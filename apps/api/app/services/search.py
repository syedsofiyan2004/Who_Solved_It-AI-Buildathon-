import csv
from datetime import UTC, datetime
from time import perf_counter
from uuid import UUID

from sqlalchemy import and_, bindparam, func, literal, or_, select
from sqlalchemy.orm import Session

from app.models.auth import AppRole, User
from app.models.repository import (
    Challenge,
    ChallengeTechnology,
    ContentStatus,
    Department,
    EmployeeProfile,
    PgVector,
    SearchQuery,
    Solution,
    SolutionEmbedding,
    Team,
    Technology,
)
from app.schemas.repository import SearchRequest, SearchResult
from app.services.embeddings import EmbeddingAdapter
from app.services.repository import can_view_challenge

SEMANTIC_MATCH_REASON_MINIMUM = 0.60
SEARCH_SIGNAL_WEIGHTS = {
    "semantic": 0.40,
    "fts": 0.25,
    "exact_error": 0.20,
    "technology": 0.05,
    "verification": 0.05,
    "recency": 0.02,
}


def _technology_names(value: object) -> list[str]:
    """Normalize psycopg array results without leaking PostgreSQL literals to the API."""
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("{") and text.endswith("}"):
            text = text[1:-1]
        return [item.strip() for item in next(csv.reader([text]), []) if item.strip()]
    if isinstance(value, (list, tuple)):
        raw_items = [str(item) for item in value]
        # psycopg can return an untyped array aggregate as the individual
        # characters of its PostgreSQL literal, for example ['{', 'OIDC', '}']
        # or ['{', 'O', 'I', 'D', 'C', '}']. Normalize that shape recursively.
        # Preserve whitespace characters while reconstructing that literal.
        if len(raw_items) >= 2 and raw_items[0] == "{" and raw_items[-1] == "}":
            return _technology_names("".join(raw_items))
        return [item for item in raw_items if item.strip()]
    return [str(value)]


def _initials(display_name: str) -> str:
    parts = [part for part in display_name.replace("-", " ").split() if part]
    return "".join(part[0].upper() for part in parts[:2]) or "?"


def _profile_context(db: Session, profiles: list[EmployeeProfile]) -> dict[UUID, tuple[str | None, str | None]]:
    team_ids = {profile.team_id for profile in profiles if profile.team_id is not None}
    department_ids = {profile.department_id for profile in profiles if profile.department_id is not None}
    teams = {
        team.id: team.name
        for team in db.scalars(select(Team).where(Team.id.in_(team_ids))).all()
    } if team_ids else {}
    departments = {
        department.id: department.name
        for department in db.scalars(select(Department).where(Department.id.in_(department_ids))).all()
    } if department_ids else {}
    return {
        profile.user_id: (teams.get(profile.team_id), departments.get(profile.department_id))
        for profile in profiles
    }


def _solver_payload(profile: EmployeeProfile, context: dict[UUID, tuple[str | None, str | None]]) -> dict:
    team, department = context.get(profile.user_id, (None, None))
    return {
        "user_id": profile.user_id,
        "display_name": profile.display_name,
        "job_title": profile.job_title,
        "team": team,
        "department": department,
        "avatar_key": profile.avatar_key,
        "initials": _initials(profile.display_name),
        "contact_email": profile.contact_email,
        "contact_handle": profile.contact_handle,
    }


def _match_reasons(*, semantic: float, has_keyword: bool, exact: bool, technology_filter: bool) -> list[str]:
    """Return stable, user-facing explanations for the retrieval signals used."""
    reasons: list[str] = []
    if exact:
        reasons.append("Exact error message contains the query")
    if has_keyword:
        reasons.append("Query terms match the documented issue")
    if technology_filter:
        reasons.append("Matches the selected technology")
    if semantic >= SEMANTIC_MATCH_REASON_MINIMUM:
        reasons.append("Similar technical context")
    return reasons[:3]


def _bounded_signal(value: float) -> float:
    return max(0.0, min(1.0, value))


def _validate_signal_weights() -> None:
    total = sum(SEARCH_SIGNAL_WEIGHTS.values())
    if total <= 0 or total > 1:
        raise ValueError("Search ranking signal weights must have a total in the range (0, 1].")
    if any(weight < 0 for weight in SEARCH_SIGNAL_WEIGHTS.values()):
        raise ValueError("Search ranking signal weights must not be negative.")


def _hybrid_score(
    *,
    semantic: float,
    fts: float,
    exact_error: float,
    technology: float,
    verification: float,
    recency: float,
    has_semantic: bool,
    has_keyword: bool,
    has_technology_filter: bool,
) -> float:
    """Apply documented search signals once, reweighting only available channels."""
    _validate_signal_weights()
    channels = [
        (_bounded_signal(semantic), SEARCH_SIGNAL_WEIGHTS["semantic"], has_semantic),
        (_bounded_signal(fts), SEARCH_SIGNAL_WEIGHTS["fts"], has_keyword),
        (_bounded_signal(exact_error), SEARCH_SIGNAL_WEIGHTS["exact_error"], has_keyword),
        (_bounded_signal(technology), SEARCH_SIGNAL_WEIGHTS["technology"], has_technology_filter),
        (_bounded_signal(verification), SEARCH_SIGNAL_WEIGHTS["verification"], True),
        (_bounded_signal(recency), SEARCH_SIGNAL_WEIGHTS["recency"], True),
    ]
    active_weight = sum(weight for _, weight, available in channels if available)
    if active_weight <= 0:
        return 0.0
    return sum(value * weight for value, weight, available in channels if available) / active_weight


def _finalize_ranked_results(
    results: list[SearchResult], *, newest: bool, threshold: float
) -> list[SearchResult]:
    """Deduplicate, apply the one result/no-answer threshold, and sort stably."""
    deduplicated: dict[UUID, SearchResult] = {}
    for result in results:
        existing = deduplicated.get(result.solution_id)
        if existing is None or result.score > existing.score:
            deduplicated[result.solution_id] = result
    eligible = [result for result in deduplicated.values() if result.score >= threshold]
    if newest:
        eligible.sort(key=lambda item: (item.updated_at, str(item.solution_id)), reverse=True)
    else:
        eligible.sort(
            key=lambda item: (item.score, item.solved_at or item.updated_at.date(), str(item.solution_id)),
            reverse=True,
        )
    return eligible


def _search_outcome(results: list[SearchResult]) -> tuple[float | None, bool]:
    """The single threshold has already filtered results, so no result is no-answer."""
    return (results[0].score, False) if results else (None, True)


def _excerpt(value: str, limit: int = 280) -> str:
    normalized = " ".join(value.split())
    return normalized if len(normalized) <= limit else f"{normalized[: limit - 1].rstrip()}…"


def execute_keyword_search(db: Session, *, user: User, payload: SearchRequest) -> tuple[list[SearchResult], int, int]:
    """Run PostgreSQL FTS and exact-error matching; semantic/RAG work is deliberately absent."""
    started = perf_counter()
    ts_query = func.websearch_to_tsquery("english", payload.query)
    normalized_query = payload.query.lower()
    exact_contains = func.strpos(func.lower(func.coalesce(Challenge.exact_error_message, "")), normalized_query) > 0
    rank = func.ts_rank_cd(Challenge.search_document, ts_query)
    statement = (
        select(Challenge, Solution, EmployeeProfile, rank.label("rank"), exact_contains.label("exact"))
        .join(Solution, and_(Solution.challenge_id == Challenge.id, Solution.deleted_at.is_(None)))
        .join(EmployeeProfile, and_(EmployeeProfile.user_id == Challenge.owner_user_id, EmployeeProfile.deleted_at.is_(None)))
        .where(
            Challenge.deleted_at.is_(None),
            or_(Challenge.search_document.op("@@")(ts_query), exact_contains),
        )
    )
    if payload.filters.verified_only:
        statement = statement.where(Challenge.status == ContentStatus.VERIFIED, Solution.status == ContentStatus.VERIFIED)
    if payload.filters.department_id is not None:
        statement = statement.where(Challenge.department_id == payload.filters.department_id)
    if payload.filters.team_id is not None:
        statement = statement.where(Challenge.team_id == payload.filters.team_id)
    if payload.filters.visibility is not None:
        statement = statement.where(Challenge.visibility == payload.filters.visibility)
    if payload.filters.technology_ids:
        statement = statement.where(
            Challenge.id.in_(
                select(ChallengeTechnology.challenge_id).where(
                    ChallengeTechnology.technology_id.in_(payload.filters.technology_ids)
                )
            )
        )

    rows = db.execute(statement).all()
    authorized = [row for row in rows if can_view_challenge(db, user, row.Challenge)]
    technology_rows = db.execute(
        select(ChallengeTechnology.challenge_id, func.array_agg(Technology.name))
        .join(Technology, Technology.id == ChallengeTechnology.technology_id)
        .where(ChallengeTechnology.challenge_id.in_([row.Challenge.id for row in authorized]))
        .group_by(ChallengeTechnology.challenge_id)
    ).all() if authorized else []
    technology_names = {challenge_id: _technology_names(names) for challenge_id, names in technology_rows}
    profile_context = _profile_context(db, [row.EmployeeProfile for row in authorized])

    def score(row) -> float:
        return float(row.rank or 0)

    if payload.sort.value == "newest":
        authorized.sort(key=lambda row: row.Challenge.updated_at, reverse=True)
    else:
        authorized.sort(key=lambda row: (score(row), row.Challenge.updated_at), reverse=True)
    total = len(authorized)
    start = (payload.page - 1) * payload.page_size
    results = []
    for row in authorized[start : start + payload.page_size]:
        challenge, solution, profile = row.Challenge, row.Solution, row.EmployeeProfile
        reasons = ["Exact error match"] if row.exact else ["Keyword match"]
        results.append(SearchResult(
            challenge_id=challenge.id,
            solution_id=solution.id,
            title=challenge.title,
            problem_excerpt=_excerpt(challenge.problem_description),
            root_cause_excerpt=_excerpt(solution.root_cause),
            resolution_steps=solution.resolution_steps[:3],
            exact_error_message=challenge.exact_error_message,
            status=challenge.status,
            visibility=challenge.visibility,
            solved_at=solution.solved_at,
            updated_at=challenge.updated_at,
            technologies=technology_names.get(challenge.id, []),
            solver=_solver_payload(profile, profile_context),
            match_reasons=reasons,
            score=round(score(row), 4),
        ))
    return results, total, int((perf_counter() - started) * 1000)


def create_search_log(
    db: Session,
    *,
    user_id: UUID,
    payload: SearchRequest,
    results: list[SearchResult],
    total: int,
    latency_ms: int,
    confidence: float | None = None,
    no_answer: bool = False,
    bedrock_generation_used: bool = False,
    outcome: str | None = None,
) -> SearchQuery:
    outcome = outcome or ("no_answer" if no_answer else "hybrid_results")
    log = SearchQuery(
        requested_by_user_id=user_id,
        query_text=payload.query,
        filters=payload.filters.model_dump(mode="json"),
        result_count=total,
        top_solution_id=results[0].solution_id if results else None,
        confidence=confidence,
        outcome=outcome,
        latency_ms=latency_ms,
        bedrock_generation_used=bedrock_generation_used,
    )
    db.add(log)
    return log


def can_read_search_log(user: User, log: SearchQuery) -> bool:
    return user.role == AppRole.ADMINISTRATOR or user.id == log.requested_by_user_id


def execute_hybrid_search(
    db: Session,
    *,
    user: User,
    payload: SearchRequest,
    adapter: EmbeddingAdapter,
    threshold: float,
) -> tuple[list[SearchResult], int, int, float | None, bool, list[UUID]]:
    """Merge authorized vector, FTS, and exact-error candidates.

    A keyword candidate remains eligible when a verified record is awaiting its
    embedding. That preserves the approved keyword fallback while embedding
    jobs catch up after a review or content edit.
    """
    started = perf_counter()
    query_vector = adapter.embed(payload.query, input_type="query")
    candidate_payload = payload.model_copy(update={"page": 1, "page_size": 20})
    keyword_results, _, _ = execute_keyword_search(db, user=user, payload=candidate_payload)
    vector_score = (
        literal(1.0)
        - SolutionEmbedding.embedding.op("<=>")(
            bindparam("query_vector", query_vector, type_=PgVector())
        )
    ).label("vector_score")
    statement = (
        select(Challenge, Solution, EmployeeProfile, vector_score)
        .join(Solution, and_(Solution.challenge_id == Challenge.id, Solution.deleted_at.is_(None)))
        .join(
            EmployeeProfile,
            and_(
                EmployeeProfile.user_id == Challenge.owner_user_id,
                EmployeeProfile.deleted_at.is_(None),
            ),
        )
        .join(
            SolutionEmbedding,
            and_(
                SolutionEmbedding.solution_id == Solution.id,
                SolutionEmbedding.embedding_model == adapter.model_id,
            ),
        )
        .where(Challenge.deleted_at.is_(None))
    )
    if payload.filters.verified_only:
        statement = statement.where(Challenge.status == ContentStatus.VERIFIED, Solution.status == ContentStatus.VERIFIED)
    if payload.filters.department_id is not None:
        statement = statement.where(Challenge.department_id == payload.filters.department_id)
    if payload.filters.team_id is not None:
        statement = statement.where(Challenge.team_id == payload.filters.team_id)
    if payload.filters.visibility is not None:
        statement = statement.where(Challenge.visibility == payload.filters.visibility)
    if payload.filters.technology_ids:
        statement = statement.where(
            Challenge.id.in_(
                select(ChallengeTechnology.challenge_id).where(
                    ChallengeTechnology.technology_id.in_(payload.filters.technology_ids)
                )
            )
        )
    vector_rows = [
        row
        for row in db.execute(statement.order_by(vector_score.desc()).limit(100)).all()
        if can_view_challenge(db, user, row.Challenge)
    ]

    # Candidate map: solution_id -> (challenge, solution, profile, semantic score | None).
    candidates = {
        row.Solution.id: (row.Challenge, row.Solution, row.EmployeeProfile, float(row.vector_score or 0.0))
        for row in vector_rows
    }
    missing_keyword_ids = [result.solution_id for result in keyword_results if result.solution_id not in candidates]
    if missing_keyword_ids:
        keyword_only_rows = db.execute(
            select(Challenge, Solution, EmployeeProfile)
            .join(Solution, and_(Solution.challenge_id == Challenge.id, Solution.deleted_at.is_(None)))
            .join(
                EmployeeProfile,
                and_(
                    EmployeeProfile.user_id == Challenge.owner_user_id,
                    EmployeeProfile.deleted_at.is_(None),
                ),
            )
            .where(Solution.id.in_(missing_keyword_ids))
        ).all()
        for row in keyword_only_rows:
            candidates[row.Solution.id] = (row.Challenge, row.Solution, row.EmployeeProfile, None)

    challenge_ids = [challenge.id for challenge, _, _, _ in candidates.values()]
    technology_rows = (
        db.execute(
            select(ChallengeTechnology.challenge_id, func.array_agg(Technology.name))
            .join(Technology, Technology.id == ChallengeTechnology.technology_id)
            .where(ChallengeTechnology.challenge_id.in_(challenge_ids))
            .group_by(ChallengeTechnology.challenge_id)
        ).all()
        if challenge_ids
        else []
    )
    technologies = {challenge_id: _technology_names(names) for challenge_id, names in technology_rows}
    profile_context = _profile_context(
        db,
        [profile for _, _, profile, _ in candidates.values()],
    )
    keyword_by_solution = {result.solution_id: result for result in keyword_results}
    max_keyword = max((result.score for result in keyword_results), default=1.0) or 1.0
    merged: list[SearchResult] = []
    for challenge, solution, profile, raw_semantic in candidates.values():
        keyword = keyword_by_solution.get(solution.id)
        semantic = _bounded_signal(raw_semantic) if raw_semantic is not None else 0.0
        fts = min(1.0, keyword.score / max_keyword) if keyword else 0.0
        exact = 1.0 if keyword and "Exact error match" in keyword.match_reasons else 0.0
        technology = 1.0 if payload.filters.technology_ids else 0.0
        verification = 1.0 if challenge.status == ContentStatus.VERIFIED else 0.0
        age_days = max(0, (datetime.now(UTC) - challenge.updated_at).days)
        recency = max(0.0, 1.0 - age_days / 3650)
        score = _hybrid_score(
            semantic=semantic,
            fts=fts,
            exact_error=exact,
            technology=technology,
            verification=verification,
            recency=recency,
            has_semantic=raw_semantic is not None,
            has_keyword=keyword is not None,
            has_technology_filter=bool(payload.filters.technology_ids),
        )
        reasons = _match_reasons(
            semantic=semantic,
            has_keyword=keyword is not None,
            exact=bool(keyword and "Exact error match" in keyword.match_reasons),
            technology_filter=bool(payload.filters.technology_ids),
        )
        merged.append(
            SearchResult(
                challenge_id=challenge.id,
                solution_id=solution.id,
                title=challenge.title,
                problem_excerpt=_excerpt(challenge.problem_description),
                root_cause_excerpt=_excerpt(solution.root_cause),
                resolution_steps=solution.resolution_steps[:3],
                exact_error_message=challenge.exact_error_message,
                status=challenge.status,
                visibility=challenge.visibility,
                solved_at=solution.solved_at,
                updated_at=challenge.updated_at,
                technologies=technologies.get(challenge.id, []),
                solver=_solver_payload(profile, profile_context),
                match_reasons=reasons,
                score=round(score, 4),
            )
        )
    merged = _finalize_ranked_results(
        merged,
        newest=payload.sort.value == "newest",
        threshold=threshold,
    )
    confidence, no_answer = _search_outcome(merged)
    total = len(merged)
    start = (payload.page - 1) * payload.page_size
    return (
        merged[start : start + payload.page_size],
        total,
        int((perf_counter() - started) * 1000),
        confidence,
        no_answer,
        [item.solution_id for item in merged],
    )

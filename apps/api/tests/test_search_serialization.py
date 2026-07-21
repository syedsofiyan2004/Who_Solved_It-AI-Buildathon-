from datetime import UTC, date, datetime
from uuid import uuid4

from app.models.repository import ContentStatus, VisibilityLevel
from app.schemas.repository import SearchResult
from app.services.search import (
    _finalize_ranked_results,
    _match_reasons,
    _search_outcome,
    _technology_names,
)


def _result(*, score: float, solved_day: int, solution_id=None) -> SearchResult:
    return SearchResult(
        challenge_id=uuid4(),
        solution_id=solution_id or uuid4(),
        title="Fictional result",
        problem_excerpt="Problem",
        root_cause_excerpt="Cause",
        resolution_steps=["Resolve"],
        exact_error_message=None,
        status=ContentStatus.VERIFIED,
        visibility=VisibilityLevel.COMPANY,
        solved_at=date(2026, 1, solved_day),
        updated_at=datetime(2026, 1, solved_day, tzinfo=UTC),
        technologies=["Docker"],
        solver={"user_id": uuid4(), "display_name": "Fictional", "job_title": "Engineer"},
        match_reasons=["Query terms match the documented issue"],
        score=score,
    )


def test_technology_aggregate_is_serialized_as_complete_names():
    assert _technology_names("{OIDC}") == ["OIDC"]
    assert _technology_names("{Docker,PostgreSQL}") == ["Docker", "PostgreSQL"]
    assert _technology_names(["OIDC", "GitHub Actions"]) == ["OIDC", "GitHub Actions"]
    assert _technology_names(list("{Kubernetes}")) == ["Kubernetes"]


def test_match_reasons_are_signal_derived_and_limited():
    assert _match_reasons(semantic=0.84, has_keyword=True, exact=True, technology_filter=True) == [
        "Exact error message contains the query",
        "Query terms match the documented issue",
        "Matches the selected technology",
    ]
    assert _match_reasons(semantic=0.84, has_keyword=False, exact=False, technology_filter=False) == [
        "Similar technical context"
    ]
    assert _match_reasons(semantic=0.59, has_keyword=False, exact=False, technology_filter=False) == []


def test_ranking_excludes_ineligible_results_deduplicates_and_paginates_after_filtering():
    duplicate_id = uuid4()
    ranked = _finalize_ranked_results(
        [
            _result(score=0.44, solved_day=1),
            _result(score=0.72, solved_day=2, solution_id=duplicate_id),
            _result(score=0.81, solved_day=3, solution_id=duplicate_id),
            _result(score=0.65, solved_day=4),
        ],
        newest=False,
        threshold=0.45,
    )

    assert [item.score for item in ranked] == [0.81, 0.65]
    assert len(ranked) == 2
    assert ranked[1:2][0].score == 0.65


def test_one_threshold_controls_eligible_results_and_no_answer():
    eligible = _finalize_ranked_results([_result(score=0.45, solved_day=1)], newest=False, threshold=0.45)
    ineligible = _finalize_ranked_results([_result(score=0.449, solved_day=1)], newest=False, threshold=0.45)

    assert _search_outcome(eligible) == (0.45, False)
    assert _search_outcome(ineligible) == (None, True)

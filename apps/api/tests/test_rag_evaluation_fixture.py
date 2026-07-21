import json
from pathlib import Path


FIXTURE = Path(__file__).parent / "fixtures" / "rag_evaluation.jsonl"
REQUIRED_KEYS = {
    "query",
    "expected_solution_id",
    "expected_solver_id",
    "expected_technology_ids",
    "expected_top_five_ids",
    "expected_no_answer",
    "caller_scope",
    "expected_permission_behavior",
    "expected_citation_ids",
}


def test_rag_evaluation_fixture_is_valid_and_covers_the_seeded_corpus():
    rows = [json.loads(line) for line in FIXTURE.read_text(encoding="utf-8").splitlines() if line]
    assert rows
    assert all(REQUIRED_KEYS <= row.keys() for row in rows)
    assert all(isinstance(row["expected_no_answer"], bool) for row in rows)

    included_solution_ids = {
        solution_id
        for row in rows
        if row["expected_permission_behavior"] == "included"
        for solution_id in row["expected_top_five_ids"]
    }
    assert len(included_solution_ids) == 36
    assert sum(row["expected_no_answer"] for row in rows) >= 2

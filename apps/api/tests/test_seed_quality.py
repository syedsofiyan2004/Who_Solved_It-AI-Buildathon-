from scripts import check_seed_quality


def test_seed_quality_gate_passes_for_current_synthetic_corpus(capsys):
    assert check_seed_quality.main() == 0

    output = capsys.readouterr().out
    assert "generated_solutions=" in output
    assert "duplicate_blueprint_keys=0" in output
    assert "unknown_technology_references=0" in output

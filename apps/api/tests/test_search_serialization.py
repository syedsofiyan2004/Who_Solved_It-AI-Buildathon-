from app.services.search import _technology_names


def test_technology_aggregate_is_serialized_as_complete_names():
    assert _technology_names("{OIDC}") == ["OIDC"]
    assert _technology_names("{Docker,PostgreSQL}") == ["Docker", "PostgreSQL"]
    assert _technology_names(["OIDC", "GitHub Actions"]) == ["OIDC", "GitHub Actions"]

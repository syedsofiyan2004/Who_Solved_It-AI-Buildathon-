import zipfile
from pathlib import Path

from scripts.package_source import create_source_archive
from scripts.scan_secrets import scan_repository


def test_secret_scanner_reports_only_affected_paths_for_safe_fictional_values(tmp_path: Path):
    key = "AK" + "IA" + ("A" * 16)
    session_key = "AS" + "IA" + ("B" * 16)
    github_line = "gh" + "p_" + ("c" * 24)
    private_key = "-----BEGIN " + "PRIVATE KEY-----"
    assignment = "api" + "_key=" + "fictional-value"
    jwt_assignment = "jwt" + "_secret=" + "fictional-value"
    url_line = "database" + "_url=postgresql://user:fictional-password@db/example"
    (tmp_path / "secrets.txt").write_text(
        "\n".join([key, session_key, github_line, private_key, assignment, jwt_assignment, url_line]),
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text("api_key=ignored-local-value", encoding="utf-8")

    findings = scan_repository(tmp_path)

    assert findings == [Path("secrets.txt")]
    assert all("fictional-value" not in str(path) for path in findings)


def test_source_packaging_excludes_local_and_generated_content(tmp_path: Path):
    (tmp_path / "app.py").write_text("print('safe')", encoding="utf-8")
    (tmp_path / ".env").write_text("api_key=local-only", encoding="utf-8")
    for directory in ("node_modules", "dist", "uploads", ".venv", ".cache"):
        path = tmp_path / directory
        path.mkdir()
        (path / "generated.txt").write_text("excluded", encoding="utf-8")
    output = tmp_path / "export.zip"

    create_source_archive(tmp_path, output)

    with zipfile.ZipFile(output) as archive:
        assert archive.namelist() == ["app.py"]

"""Verify that a shareable source archive has no local files or credentials."""

import argparse
import zipfile
from pathlib import Path

try:  # Supports both `python scripts/...` and package imports in tests.
    from scripts.scan_secrets import SECRET_PATTERNS, _contains_assignment_secret
except ModuleNotFoundError:  # pragma: no cover - exercised by direct CLI use.
    from scan_secrets import SECRET_PATTERNS, _contains_assignment_secret


FORBIDDEN_FILENAMES = {".env", "vite.config.js", "vite.config.d.ts", "tailwind.config.js", "tailwind.config.d.ts"}
FORBIDDEN_DIRECTORIES = {
    ".git", ".venv", ".cache", "__pycache__", "coverage", "dist", "htmlcov", "node_modules",
    ".pytest_cache", ".ruff_cache", "uploads", "artifacts",
}


def verify_source_archive(path: Path) -> list[str]:
    """Return affected archive paths only; never return matched credential text."""
    findings: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            member_path = Path(member.filename)
            if member.is_dir():
                continue
            if member_path.name in FORBIDDEN_FILENAMES or member_path.suffix == ".tsbuildinfo" or any(part in FORBIDDEN_DIRECTORIES for part in member_path.parts):
                findings.append(member.filename)
                continue
            try:
                content = archive.read(member).decode("utf-8")
            except UnicodeDecodeError:
                continue
            if any(pattern.search(content) for pattern in SECRET_PATTERNS) or _contains_assignment_secret(content):
                findings.append(member.filename)
    return sorted(set(findings))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", default="artifacts/knowledge-platform-source.zip")
    args = parser.parse_args()
    findings = verify_source_archive(Path(args.archive))
    if findings:
        print("Archive verification failed for: " + ", ".join(findings))
        return 1
    print("Archive verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

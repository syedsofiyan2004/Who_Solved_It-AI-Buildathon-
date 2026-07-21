"""Fail safely when credential-like content appears in exportable repository files."""

import re
import sys
from pathlib import Path


EXCLUDED_DIRECTORIES = {
    ".git", ".venv", ".cache", "__pycache__", "coverage", "dist", "htmlcov", "node_modules",
    ".pytest_cache", ".ruff_cache", "uploads",
}
EXCLUDED_FILENAMES = {".env"}
SECRET_PATTERNS = (
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
)
ASSIGNMENT_PATTERN = re.compile(
    r"(?im)^\s*(?:export\s+)?[\"']?(?P<name>aws_access_key_id|aws_secret_access_key|"
    r"aws_session_token|(?:github_)?token|api[_-]?key|(?:jwt_)?secret)[\"']?\s*[:=]\s*"
    r"[\"']?(?P<value>[^\s\"'#]+)"
)
DATABASE_URL_PATTERN = re.compile(
    r"(?im)^\s*[\"']?database_url[\"']?\s*[:=]\s*[\"']?"
    r"(?P<value>postgres(?:ql)?(?:\+[a-z0-9_]+)?://[^\s\"']+)"
)
PLACEHOLDER_PATTERN = re.compile(
    r"(?ix)^(?:|\$?\{[^}]+\}|\$[A-Z_][A-Z0-9_]*|\$\([^)]*\)|<[^>]+>|replace[-_].*|example|sample|dummy|fake|fictional|"
    r"change[-_]?me|password|local_password|[a-z_]*placeholder[a-z_]*)$"
)


def _is_placeholder(value: str) -> bool:
    return bool(PLACEHOLDER_PATTERN.fullmatch(value.strip().strip("'\"")))


def _contains_assignment_secret(text: str) -> bool:
    for match in ASSIGNMENT_PATTERN.finditer(text):
        value = match.group("value")
        if value.startswith(("jwt.", "settings.", "credentials.")):
            continue
        if value.rstrip(",") not in {"str", "int", "float", "bool", "Field"} and not _is_placeholder(value):
            return True
    for match in DATABASE_URL_PATTERN.finditer(text):
        value = match.group("value")
        password = value.split("://", 1)[1].split("@", 1)[0].split(":", 1)
        if len(password) == 2 and not _is_placeholder(password[1]):
            return True
    return False


def scan_repository(root: Path) -> list[Path]:
    """Return affected relative paths only; never include matched content."""
    findings: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.name in EXCLUDED_FILENAMES or any(
            part in EXCLUDED_DIRECTORIES for part in path.parts
        ):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(pattern.search(text) for pattern in SECRET_PATTERNS) or _contains_assignment_secret(text):
            findings.append(path.relative_to(root))
    return sorted(findings)


def main() -> int:
    findings = scan_repository(Path.cwd())
    if findings:
        print("Credential-like content found in: " + ", ".join(map(str, findings)))
        return 1
    print("Secret scan passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

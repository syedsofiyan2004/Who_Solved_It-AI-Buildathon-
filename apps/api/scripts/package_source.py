"""Create a shareable source archive without local configuration or generated files."""

import argparse
import zipfile
from pathlib import Path


EXCLUDED_DIRECTORIES = {
    ".git", ".venv", ".cache", "__pycache__", "coverage", "dist", "htmlcov", "node_modules",
    ".pytest_cache", ".ruff_cache", "uploads", "artifacts",
}
EXCLUDED_FILENAMES = {".env"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def exportable_paths(root: Path, output: Path) -> list[Path]:
    paths: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.resolve() == output.resolve():
            continue
        if path.name in EXCLUDED_FILENAMES or path.suffix in EXCLUDED_SUFFIXES:
            continue
        if any(part in EXCLUDED_DIRECTORIES for part in path.parts):
            continue
        paths.append(path)
    return sorted(paths)


def create_source_archive(root: Path, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in exportable_paths(root, output):
            archive.write(path, path.relative_to(root))
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/knowledge-platform-source.zip")
    args = parser.parse_args()
    root = Path.cwd()
    output = (root / args.output).resolve()
    create_source_archive(root, output)
    print(f"Created source archive: {output.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

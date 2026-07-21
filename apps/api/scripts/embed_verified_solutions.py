import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.database.session import SessionLocal
from app.services.embeddings import BedrockEmbeddingAdapter, EmbeddingUnavailable, reembed_verified_solutions


def main() -> None:
    try:
        adapter = BedrockEmbeddingAdapter(get_settings())
    except EmbeddingUnavailable as exc:
        print(f"Embedding run not started: {exc}")
        raise SystemExit(2)
    with SessionLocal() as db:
        created, skipped, failed = reembed_verified_solutions(db, adapter=adapter)
        db.commit()
    print(f"Embedding run complete. Created: {created}; unchanged: {skipped}; failed: {failed}.")


if __name__ == "__main__":
    main()

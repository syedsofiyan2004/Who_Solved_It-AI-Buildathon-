import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.database.session import SessionLocal
from app.services.embeddings import (
    EmbeddingUnavailable,
    create_embedding_adapter,
    reembed_verified_solutions,
)


def main() -> None:
    try:
        adapter = create_embedding_adapter(get_settings())
    except EmbeddingUnavailable as exc:
        raise SystemExit(str(exc)) from exc
    with SessionLocal() as db:
        created, skipped, failed = reembed_verified_solutions(db, adapter=adapter)
        db.commit()
    print(f"Embedding refresh complete for {adapter.model_id}: created={created}, skipped={skipped}, failed={failed}.")


if __name__ == "__main__":
    main()

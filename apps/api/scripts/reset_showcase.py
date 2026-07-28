"""Reset all local showcase records while preserving the migrated schema.

This destructive command is intentionally restricted to APP_ENV=development
and requires an explicit --yes flag. It is useful when replacing an older seed
corpus with the final Minfy Resolve employee and incident dataset.
"""

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.core.config import get_settings
from app.database.session import SessionLocal
from app.models import auth as _auth_models  # noqa: F401
from app.models import repository as _repository_models  # noqa: F401
from app.models.base import Base


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="Confirm destructive local data reset.")
    args = parser.parse_args()

    settings = get_settings()
    if settings.app_env != "development":
        print("Showcase reset is allowed only when APP_ENV=development.")
        return 1
    if not args.yes:
        print("Refusing to reset data without --yes.")
        return 1

    table_names = sorted(Base.metadata.tables)
    if not table_names:
        print("No application tables were registered.")
        return 1
    quoted = ", ".join(f'"{name}"' for name in table_names)
    with SessionLocal() as db:
        db.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"))
        db.commit()

    print(f"Reset {len(table_names)} local application tables. Run scripts/seed_dev.py next.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

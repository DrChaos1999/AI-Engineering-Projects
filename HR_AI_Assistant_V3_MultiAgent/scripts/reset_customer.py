from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import DATABASE_PATH  # noqa: E402
from database.database import create_database, delete_session_by_access_hash  # noqa: E402
from services.access_control import hash_access_code  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        raise SystemExit("Usage: python scripts/reset_customer.py CUSTOMER_ACCESS_CODE")
    code = sys.argv[1].strip()
    create_database(DATABASE_PATH)
    delete_session_by_access_hash(hash_access_code(code))
    print("Customer allocation reset.")


if __name__ == "__main__":
    main()

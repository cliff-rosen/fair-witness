"""One-off: create the `fairwitness` schema on the configured DB host.

Run with admin/master DB creds in .env:
    venv\\Scripts\\python.exe scripts\\create_db.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pymysql  # noqa: E402

from config.settings import settings  # noqa: E402


def main() -> None:
    conn = pymysql.connect(
        host=settings.DB_HOST,
        port=int(settings.DB_PORT),
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{settings.DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            conn.commit()
            cur.execute("SHOW DATABASES LIKE %s", (settings.DB_NAME,))
            present = cur.fetchone() is not None
        print(f"DB '{settings.DB_NAME}' present: {present}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

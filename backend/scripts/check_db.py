"""Quick connectivity + schema check against the configured `fairwitness` DB.

    venv\\Scripts\\python.exe scripts\\check_db.py
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
        database=settings.DB_NAME,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION()")
            (version,) = cur.fetchone()
            cur.execute("SHOW TABLES")
            tables = [r[0] for r in cur.fetchall()]
        print(f"Connected to {settings.DB_HOST}/{settings.DB_NAME} (server {version})")
        print(f"Tables: {tables or '(none yet — start the app to create them)'}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

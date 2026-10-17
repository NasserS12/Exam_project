import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

BASE_DIR = Path(__file__).parent


def get_connection():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


def run_sql_file(conn, filename):
    sql = (BASE_DIR / filename).read_text(encoding="utf-8")
    conn.execute(sql)


def init_db(reset=False):
    with get_connection() as conn:
        if reset:
            run_sql_file(conn, "reset.sql")
        run_sql_file(conn, "schema.sql")
        count = conn.execute("SELECT COUNT(*) AS n FROM chapters").fetchone()["n"]
        if count == 0:
            run_sql_file(conn, "seed.sql")


if __name__ == "__main__":
    init_db()
    print("Database initialized.")

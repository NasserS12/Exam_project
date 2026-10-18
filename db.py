import os
from pathlib import Path

import psycopg
from psycopg import sql
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


def setup_app_role(conn):
    user = os.environ["APP_DB_USER"]
    password = os.environ["APP_DB_PASSWORD"]
    database = os.environ["POSTGRES_DB"]
    role = sql.Identifier(user)

    exists = conn.execute(
        "SELECT 1 FROM pg_roles WHERE rolname = %s", (user,)
    ).fetchone()
    action = "ALTER" if exists else "CREATE"
    conn.execute(
        sql.SQL(action + " ROLE {} WITH LOGIN PASSWORD {}").format(
            role, sql.Literal(password)
        )
    )

    conn.execute(
        sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
            sql.Identifier(database), role
        )
    )
    conn.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(role))
    conn.execute(sql.SQL("GRANT SELECT ON chapters, questions TO {}").format(role))
    conn.execute(sql.SQL("GRANT SELECT, INSERT ON users, results TO {}").format(role))


if __name__ == "__main__":
    init_db()
    with get_connection() as conn:
        setup_app_role(conn)
    print("Database initialized.")

import json
import os
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "content"


def get_connection():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


def run_sql_file(conn, filename):
    sql_text = (BASE_DIR / filename).read_text(encoding="utf-8")
    conn.execute(sql_text)


class ContentError(ValueError):
    """A content file has a question the app cannot use."""


def validate_question(question, source):
    """Reject a question before it reaches the database."""
    text = question.get("question")
    options = question.get("options")
    answer = question.get("answer")
    where = f"{source}: {str(text)[:40]!r}"

    if not isinstance(text, str) or not text.strip():
        raise ContentError(f"{where}: question text is empty")
    if not isinstance(question.get("chapter"), int):
        raise ContentError(f"{where}: chapter must be a number")
    if not isinstance(question.get("chapter_title"), str):
        raise ContentError(f"{where}: chapter_title is missing")
    if not isinstance(options, list) or not 2 <= len(options) <= 4:
        raise ContentError(f"{where}: needs 2 to 4 options")
    if not all(isinstance(o, str) and o.strip() for o in options):
        raise ContentError(f"{where}: every option must be text")
    if len(set(options)) != len(options):
        raise ContentError(f"{where}: options must be different")
    if not isinstance(answer, int) or not 0 <= answer < len(options):
        raise ContentError(f"{where}: answer must point to one of the options")


def load_subject(conn, folder):
    info = json.loads((folder / "info.json").read_text(encoding="utf-8"))
    questions = json.loads((folder / "questions.json").read_text(encoding="utf-8"))
    for question in questions:
        validate_question(question, folder.name)

    conn.execute(
        "INSERT INTO subjects (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
        (info["name"],),
    )
    subject_id = conn.execute(
        "SELECT id FROM subjects WHERE name = %s", (info["name"],)
    ).fetchone()["id"]

    chapter_ids = {}
    for question in questions:
        number = question["chapter"]
        if number not in chapter_ids:
            chapter_ids[number] = conn.execute(
                "INSERT INTO chapters (subject_id, name, position) VALUES (%s, %s, %s) "
                "ON CONFLICT (subject_id, name) DO UPDATE SET position = EXCLUDED.position "
                "RETURNING id",
                (subject_id, question["chapter_title"], number),
            ).fetchone()["id"]

        options = question["options"] + [None] * (4 - len(question["options"]))
        conn.execute(
            "INSERT INTO questions "
            "(chapter_id, text, option_1, option_2, option_3, option_4, answer, source_page) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (chapter_id, text) DO UPDATE SET "
            "option_1 = EXCLUDED.option_1, option_2 = EXCLUDED.option_2, "
            "option_3 = EXCLUDED.option_3, option_4 = EXCLUDED.option_4, "
            "answer = EXCLUDED.answer, source_page = EXCLUDED.source_page",
            (
                chapter_ids[number],
                question["question"],
                *options,
                question["options"][question["answer"]],
                question.get("pdf_page"),
            ),
        )


def load_content(conn, content_dir=CONTENT_DIR):
    for folder in sorted(p for p in Path(content_dir).iterdir() if p.is_dir()):
        load_subject(conn, folder)


def init_db(reset=False, content_dir=CONTENT_DIR):
    with get_connection() as conn:
        if reset:
            run_sql_file(conn, "reset.sql")
        run_sql_file(conn, "schema.sql")
        load_content(conn, content_dir)


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
    conn.execute(
        sql.SQL("GRANT SELECT ON subjects, chapters, questions TO {}").format(role)
    )
    conn.execute(sql.SQL("GRANT SELECT, INSERT ON users, results TO {}").format(role))


if __name__ == "__main__":
    init_db()
    with get_connection() as conn:
        setup_app_role(conn)
    print("Database initialized.")

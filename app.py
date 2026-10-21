import os
import re
from functools import wraps

import psycopg
from flask import Flask, abort, redirect, render_template, request, session
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_connection

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE") == "1"
csrf = CSRFProtect(app)

USERNAME_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,29}")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return view(*args, **kwargs)

    return wrapped


def split_title(name):
    """'الفصل الأول: مقدمة' -> ('الفصل الأول', 'مقدمة')."""
    label, sep, title = name.partition(": ")
    return (label, title) if sep else ("", name)


@app.route("/")
@login_required
def home():
    conn = get_connection()
    subjects = conn.execute(
        "SELECT subjects.id, subjects.name, "
        "COUNT(DISTINCT chapters.id) AS chapters, COUNT(questions.id) AS questions "
        "FROM subjects "
        "LEFT JOIN chapters ON chapters.subject_id = subjects.id "
        "LEFT JOIN questions ON questions.chapter_id = chapters.id "
        "GROUP BY subjects.id ORDER BY subjects.id"
    ).fetchall()
    conn.close()
    return render_template("home.html", subjects=subjects)


@app.route("/about")
def about():
    conn = get_connection()
    subjects = conn.execute("SELECT name FROM subjects ORDER BY id").fetchall()
    conn.close()
    return render_template("about.html", subjects=subjects)


@app.route("/chapters")
def chapters():
    return redirect("/")


@app.route("/subjects/<int:subject_id>")
@login_required
def subject(subject_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT id, name FROM subjects WHERE id = %s", (subject_id,)
    ).fetchone()
    if row is None:
        conn.close()
        abort(404)
    rows = conn.execute(
        "SELECT chapters.id, chapters.name, COUNT(questions.id) AS questions "
        "FROM chapters LEFT JOIN questions ON questions.chapter_id = chapters.id "
        "WHERE chapters.subject_id = %s "
        "GROUP BY chapters.id ORDER BY chapters.position, chapters.id",
        (subject_id,),
    ).fetchall()
    conn.close()

    chapter_list = []
    for chapter in rows:
        label, title = split_title(chapter["name"])
        chapter_list.append(
            {
                "id": chapter["id"],
                "label": label,
                "title": title,
                "questions": chapter["questions"],
            }
        )
    return render_template("subject.html", subject=row, chapters=chapter_list)


@app.route("/chapters/<int:chapter_id>", methods=["GET", "POST"])
@login_required
def chapter_quiz(chapter_id):
    conn = get_connection()
    chapter = conn.execute(
        "SELECT chapters.id, chapters.name, chapters.subject_id, "
        "subjects.name AS subject_name "
        "FROM chapters LEFT JOIN subjects ON subjects.id = chapters.subject_id "
        "WHERE chapters.id = %s",
        (chapter_id,),
    ).fetchone()
    if chapter is None:
        conn.close()
        abort(404)
    rows = conn.execute(
        "SELECT id, text, option_1, option_2, option_3, option_4, answer, source_page "
        "FROM questions WHERE chapter_id = %s ORDER BY id",
        (chapter_id,),
    ).fetchall()
    conn.close()

    questions = []
    answers = {}
    for row in rows:
        questions.append(
            {
                "id": row["id"],
                "text": row["text"],
                "options": [
                    option
                    for option in (
                        row["option_1"],
                        row["option_2"],
                        row["option_3"],
                        row["option_4"],
                    )
                    if option is not None
                ],
                "source_page": row["source_page"],
            }
        )
        answers[row["id"]] = row["answer"]

    results = None
    error = None
    score = None
    total = None
    saved = None
    if request.method == "POST":
        results = {}
        for question in questions:
            selected = request.form.get(f"q{question['id']}")
            if selected not in question["options"]:
                error = "جاوب على كل الأسئلة من الخيارات"
                return render_template(
                    "chapter_quiz.html",
                    chapter=chapter,
                    questions=questions,
                    results=None,
                    error=error,
                ), 400
            results[question["id"]] = selected == answers[question["id"]]
        score = sum(results.values())
        total = len(results)
        user_id = session.get("user_id")
        saved = user_id is not None
        if saved:
            conn = get_connection()
            conn.execute(
                "INSERT INTO results (user_id, chapter_id, score, total) "
                "VALUES (%s, %s, %s, %s)",
                (user_id, chapter_id, score, total),
            )
            conn.commit()
            conn.close()

    return render_template(
        "chapter_quiz.html",
        chapter=chapter,
        questions=questions,
        results=results,
        answers=answers if results is not None else None,
        error=error,
        score=score,
        total=total,
        saved=saved,
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if not USERNAME_PATTERN.fullmatch(username):
            error = "اسم المستخدم لازم يبدأ بحرف إنجليزي، ومن 3 إلى 30 حرف، حروف وأرقام و _ بس"
            return render_template("register.html", error=error), 400

        if len(password) < 8 or not password.strip():
            error = "كلمة المرور لازم تكون 8 حروف على الأقل"
            return render_template("register.html", error=error), 400

        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, generate_password_hash(password)),
            )
            conn.commit()
        except psycopg.IntegrityError:
            error = "اسم المستخدم مستخدم، اختر اسم ثاني"
            return render_template("register.html", error=error), 400
        finally:
            conn.close()

        return render_template("register.html", success=True)
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        conn = get_connection()
        user = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = %s",
            (username,),
        ).fetchone()
        conn.close()

        if user is None or not check_password_hash(user["password_hash"], password):
            error = "اسم المستخدم أو كلمة المرور غير صحيحة"
            return render_template("login.html", error=error), 401

        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return redirect("/")

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/")


@app.route("/results")
@login_required
def results_page():
    user_id = session.get("user_id")

    conn = get_connection()
    rows = conn.execute(
        "SELECT subjects.name AS subject, chapters.name, "
        "results.score, results.total, results.created_at "
        "FROM results "
        "JOIN chapters ON chapters.id = results.chapter_id "
        "LEFT JOIN subjects ON subjects.id = chapters.subject_id "
        "WHERE results.user_id = %s "
        "ORDER BY results.created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return render_template("results.html", results=rows)

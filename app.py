import os
import re
import sqlite3

from flask import Flask, abort, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_connection

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

USERNAME_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,29}")


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    conn = get_connection()
    chapters = conn.execute("SELECT name FROM chapters").fetchall()
    conn.close()
    return render_template("about.html", chapters=chapters)


@app.route("/chapters")
def chapters():
    conn = get_connection()
    rows = conn.execute("SELECT id, name FROM chapters ORDER BY id").fetchall()
    conn.close()
    return render_template("chapters.html", chapters=rows)


@app.route("/chapters/<int:chapter_id>", methods=["GET", "POST"])
def chapter_quiz(chapter_id):
    conn = get_connection()
    chapter = conn.execute(
        "SELECT id, name FROM chapters WHERE id = ?", (chapter_id,)
    ).fetchone()
    if chapter is None:
        conn.close()
        abort(404)
    rows = conn.execute(
        "SELECT id, text, option_1, option_2, option_3, option_4, answer "
        "FROM questions WHERE chapter_id = ? ORDER BY id",
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
                    row["option_1"],
                    row["option_2"],
                    row["option_3"],
                    row["option_4"],
                ],
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
                "VALUES (?, ?, ?, ?)",
                (user_id, chapter_id, score, total),
            )
            conn.commit()
            conn.close()

    return render_template(
        "chapter_quiz.html",
        chapter=chapter,
        questions=questions,
        results=results,
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
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
            conn.commit()
        except sqlite3.IntegrityError:
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
            "SELECT id, username, password_hash FROM users WHERE username = ?",
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
def results_page():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect("/login")

    conn = get_connection()
    rows = conn.execute(
        "SELECT chapters.name, results.score, results.total, results.created_at "
        "FROM results "
        "JOIN chapters ON chapters.id = results.chapter_id "
        "WHERE results.user_id = ? "
        "ORDER BY results.created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return render_template("results.html", results=rows)

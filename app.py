import re
import sqlite3

from flask import Flask, abort, render_template, request
from werkzeug.security import generate_password_hash

from db import get_connection

app = Flask(__name__)
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
    return render_template(
        "chapter_quiz.html",
        chapter=chapter,
        questions=questions,
        results=results,
        error=error,
        score=score,
        total=total,
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

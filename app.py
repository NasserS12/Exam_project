from flask import Flask, abort, render_template, request

from db import get_connection

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("home.html")


def get_question(question_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM questions WHERE id = ?", (question_id,)
    ).fetchone()
    conn.close()
    options = [row["option_1"], row["option_2"], row["option_3"], row["option_4"]]
    return row["text"], options, row["answer"]


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

    return render_template(
        "chapter_quiz.html",
        chapter=chapter,
        questions=questions,
        results=results,
        error=error,
    )


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    text, options, answer = get_question(1)
    question = {"text": text, "options": options}
    result = None
    error = None
    if request.method == "POST":
        selected = request.form.get("answer")
        if selected not in options:
            error = "اختر إجابة من الخيارات"
            return render_template(
                "quiz.html", question=question, result=result, error=error
            ), 400
        result = selected == answer
    return render_template("quiz.html", question=question, result=result, error=error)

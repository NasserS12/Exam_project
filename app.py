from flask import Flask, render_template, request

from db import get_connection

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("home.html")


def get_question(question_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
    conn.close()
    options = [row["option_1"], row["option_2"], row["option_3"], row["option_4"]]
    return row["text"], options, row["answer"]


@app.route("/about")
def about():
    conn = get_connection()
    chapters = conn.execute("SELECT name FROM chapters").fetchall()
    conn.close()
    return render_template("about.html", chapters=chapters)


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

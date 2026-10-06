from flask import Flask, render_template, request

app = Flask(__name__)

CHAPTERS = ["الفصل الأول", "الفصل الثاني", "الفصل الثالث"]

QUESTION = {
    "text": "وش المنفذ الافتراضي لـ SSH؟",
    "options": ["21", "22", "80", "443"],
    "answer": "22",
}


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about.html", chapters=CHAPTERS)


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    result = None
    error = None
    if request.method == "POST":
        selected = request.form.get("answer")
        if selected not in QUESTION["options"]:
            error = "اختر إجابة من الخيارات"
            return render_template(
                "quiz.html", question=QUESTION, result=result, error=error
            ), 400
        result = selected == QUESTION["answer"]
    return render_template("quiz.html", question=QUESTION, result=result, error=error)

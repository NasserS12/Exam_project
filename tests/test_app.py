import json
import os
from pathlib import Path

import pytest

import db
from app import app

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://test:test@127.0.0.1:5433/test"
)
TEST_CONTENT = Path(__file__).parent / "content"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    db.init_db(reset=True, content_dir=TEST_CONTENT)
    app.config["SECRET_KEY"] = "test-secret-key"
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", False)
    return app.test_client()


@pytest.fixture
def logged_in(client):
    register_user(client)
    login_user(client)


def register_user(client, username="nasser", password="mypassword123"):
    return client.post("/register", data={"username": username, "password": password})


def test_csrf_blocks_forged_request(client, monkeypatch):
    register_user(client)
    login_user(client)

    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", True)
    response = client.post("/chapters/1", data={"q1": "21", "q2": "80"})
    assert response.status_code == 400

    conn = db.get_connection()
    count = conn.execute("SELECT COUNT(*) AS n FROM results").fetchone()["n"]
    conn.close()
    assert count == 0


def test_login_success_shows_username(client):
    register_user(client)
    response = client.post(
        "/login",
        data={"username": "nasser", "password": "mypassword123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "مرحباً nasser" in response.get_data(as_text=True)


def test_logout_clears_session(client):
    register_user(client)
    client.post("/login", data={"username": "nasser", "password": "mypassword123"})
    response = client.post("/logout", follow_redirects=True)
    assert "مرحباً nasser" not in response.get_data(as_text=True)
    assert 'href="/login"' in response.get_data(as_text=True)


def test_tampered_session_is_ignored(client):
    client.set_cookie("session", "fake-session-value")
    response = client.get("/")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "ذاكر موادك" in page
    assert "مرحباً" not in page


def test_login_wrong_password(client):
    register_user(client)
    response = client.post(
        "/login", data={"username": "nasser", "password": "Wornspass"}
    )
    assert response.status_code == 401
    assert "اسم المستخدم أو كلمة المرور غير صحيحة" in response.get_data(as_text=True)


def test_login_unknown_username(client):
    response = client.post(
        "/login", data={"username": "nobody", "password": "mypassword123"}
    )
    assert response.status_code == 401
    assert "اسم المستخدم أو كلمة المرور غير صحيحة" in response.get_data(as_text=True)


def test_logout_requires_post(client):
    response = client.get("/logout")
    assert response.status_code == 405


def test_home_returns_200(client, logged_in):
    response = client.get("/")
    assert response.status_code == 200
    assert "اختر الفصل وابدأ الاختبار" in response.get_data(as_text=True)


def test_unknown_route_returns_404(client):
    response = client.get("/test")
    assert response.status_code == 404


def test_about_returns_200(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert "منصة اختبارات لمراجعة المواد" in response.get_data(as_text=True)
    assert "Test subject" in response.get_data(as_text=True)


def test_subject_page_lists_chapters(client, logged_in):
    response = client.get("/subjects/1")
    assert response.status_code == 200
    assert "اختر الفصل اللي تبي تذاكره" in response.get_data(as_text=True)
    assert "Cryptography" in response.get_data(as_text=True)


def test_missing_subject_returns_404(client, logged_in):
    response = client.get("/subjects/999")
    assert response.status_code == 404


def test_old_chapters_page_redirects_home(client):
    response = client.get("/chapters")
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_home_links_to_subject(client, logged_in):
    response = client.get("/")
    assert response.status_code == 200
    assert 'href="/subjects/1"' in response.get_data(as_text=True)


def test_chapter_page_shows_questions(client, logged_in):
    response = client.get("/chapters/1")
    assert response.status_code == 200
    assert "وش المنفذ الافتراضي" in response.get_data(as_text=True)


def test_missing_chapter_returns_404(client, logged_in):
    response = client.get("/chapters/999")
    assert response.status_code == 404


def test_subject_page_links_to_chapter(client, logged_in):
    response = client.get("/subjects/1")
    assert response.status_code == 200
    assert 'href="/chapters/1"' in response.get_data(as_text=True)


def test_chapter_quiz_one_wrong_answer(client, logged_in):
    response = client.post("/chapters/1", data={"q1": "21", "q2": "443"})
    assert response.status_code == 200
    assert "إجابة خاطئة" in response.get_data(as_text=True)
    assert "إجابة صحيحة" in response.get_data(as_text=True)
    assert "نتيجتك: 1 من 2" in response.get_data(as_text=True)


def test_chapter_quiz_all_answers_correct(client, logged_in):
    response = client.post("/chapters/1", data={"q1": "22", "q2": "443"})
    assert response.status_code == 200
    assert "إجابة صحيحة" in response.get_data(as_text=True)
    assert "إجابة خاطئة" not in response.get_data(as_text=True)
    assert "نتيجتك: 2 من 2" in response.get_data(as_text=True)


def test_chapter_quiz_missing_answer(client, logged_in):
    response = client.post("/chapters/1", data={"q1": "22"})
    assert response.status_code == 400
    assert "جاوب على كل الأسئلة من الخيارات" in response.get_data(as_text=True)


def test_chapter_quiz_invalid_answer(client, logged_in):
    response = client.post("/chapters/1", data={"q1": "22222222", "q2": "443"})
    assert response.status_code == 400
    assert "جاوب على كل الأسئلة من الخيارات" in response.get_data(as_text=True)


def test_chapter_quiz_all_answers_wrong_shows_zero(client, logged_in):
    response = client.post("/chapters/1", data={"q1": "21", "q2": "80"})
    assert response.status_code == 200
    assert "نتيجتك: 0 من 2" in response.get_data(as_text=True)
    assert "إجابة صحيحة" not in response.get_data(as_text=True)


def test_register_stores_password_hash(client):
    response = client.post(
        "/register", data={"username": "nasser", "password": "mypassword123"}
    )
    assert response.status_code == 200
    assert "تم إنشاء الحساب بنجاح" in response.get_data(as_text=True)

    conn = db.get_connection()
    user = conn.execute(
        "SELECT password_hash FROM users WHERE username = %s", ("nasser",)
    ).fetchone()
    conn.close()

    assert user is not None
    assert user["password_hash"] != "mypassword123"
    assert user["password_hash"].startswith("scrypt:")


def test_register_duplicate_username(client):
    data = {"username": "nasser", "password": "mypassword123"}
    client.post("/register", data=data)
    response = client.post("/register", data=data)
    assert response.status_code == 400
    assert "اسم المستخدم مستخدم" in response.get_data(as_text=True)


def test_register_username_with_space(client):
    response = client.post(
        "/register", data={"username": "nas ser", "password": "mypassword123"}
    )
    assert response.status_code == 400
    assert "اسم المستخدم لازم يبدأ بحرف" in response.get_data(as_text=True)


def test_register_username_starts_with_digit(client):
    response = client.post(
        "/register", data={"username": "1nasser", "password": "mypassword123"}
    )
    assert response.status_code == 400
    assert "اسم المستخدم لازم يبدأ بحرف" in response.get_data(as_text=True)


def test_register_short_password(client):
    response = client.post(
        "/register", data={"username": "nasser", "password": "short"}
    )
    assert response.status_code == 400
    assert "كلمة المرور لازم تكون 8 حروف" in response.get_data(as_text=True)


def test_register_password_only_spaces(client):
    response = client.post(
        "/register", data={"username": "nasser", "password": "          "}
    )
    assert response.status_code == 400
    assert "كلمة المرور لازم تكون 8 حروف" in response.get_data(as_text=True)


def test_login_page_links_to_register(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert 'href="/register"' in response.get_data(as_text=True)


def login_user(client, username="nasser", password="mypassword123"):
    return client.post("/login", data={"username": username, "password": password})


def test_result_saved_for_logged_in_user(client):
    register_user(client)
    login_user(client)
    response = client.post("/chapters/1", data={"q1": "22", "q2": "443"})
    assert "تم حفظ نتيجتك" in response.get_data(as_text=True)

    response = client.get("/results")
    assert response.status_code == 200
    assert "Networking" in response.get_data(as_text=True)
    assert "2 من 2" in response.get_data(as_text=True)


def test_anonymous_user_cannot_submit_quiz(client):
    response = client.post("/chapters/1", data={"q1": "22", "q2": "443"})
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"

    conn = db.get_connection()
    count = conn.execute("SELECT COUNT(*) AS n FROM results").fetchone()["n"]
    conn.close()
    assert count == 0

    conn = db.get_connection()
    count = conn.execute("SELECT COUNT(*) AS n FROM results").fetchone()["n"]
    conn.close()
    assert count == 0


def test_user_cannot_see_other_users_results(client):
    register_user(client, "alice")
    login_user(client, "alice")
    client.post("/chapters/1", data={"q1": "22", "q2": "443"})
    client.post("/logout")

    register_user(client, "bob")
    login_user(client, "bob")
    response = client.get("/results")

    assert response.status_code == 200
    assert "ما حليت أي اختبار للحين" in response.get_data(as_text=True)
    assert "2 من 2" not in response.get_data(as_text=True)


def test_results_requires_login(client):
    response = client.get("/results")
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_old_quiz_page_removed(client):
    response = client.get("/quiz")
    assert response.status_code == 404


def test_answers_hidden_until_submitted(client):
    response = client.get("/chapters/1")
    assert "الصح:" not in response.get_data(as_text=True)


def test_wrong_answer_shows_correct_one(client, logged_in):
    response = client.post("/chapters/1", data={"q1": "21", "q2": "443"})
    page = response.get_data(as_text=True)
    assert "الصح: <strong>22</strong>" in page
    assert "صفحة 1 في الكتاب" in page


def test_true_false_question(client, logged_in):
    page = client.get("/chapters/2").get_data(as_text=True)
    assert page.count('type="radio"') == 2

    response = client.post("/chapters/2", data={"q3": "صح"})
    assert "نتيجتك: 1 من 1" in response.get_data(as_text=True)


def test_loading_content_twice_adds_nothing(client):
    db.init_db(content_dir=TEST_CONTENT)

    conn = db.get_connection()
    count = conn.execute("SELECT COUNT(*) AS n FROM questions").fetchone()["n"]
    conn.close()
    assert count == 3


def good_question():
    return {
        "chapter": 1,
        "chapter_title": "Chapter",
        "question": "Q?",
        "options": ["a", "b", "c", "d"],
        "answer": 0,
    }


@pytest.mark.parametrize(
    "change",
    [
        {"question": ""},
        {"options": ["only one"]},
        {"options": ["a", "b", "c", "d", "e"]},
        {"options": ["a", "a", "c", "d"]},
        {"answer": 4},
        {"answer": "0"},
        {"chapter": "1"},
    ],
)
def test_bad_question_is_rejected(change):
    question = {**good_question(), **change}
    with pytest.raises(ValueError):
        db.validate_question(question, "test")


def test_real_content_is_valid():
    folders = [p for p in db.CONTENT_DIR.iterdir() if p.is_dir()]
    assert folders
    for folder in folders:
        info = json.loads((folder / "info.json").read_text(encoding="utf-8"))
        assert info["name"].strip()
        questions = json.loads((folder / "questions.json").read_text(encoding="utf-8"))
        for question in questions:
            db.validate_question(question, folder.name)


@pytest.mark.parametrize("url", ["/subjects/1", "/chapters/1", "/results"])
def test_protected_pages_need_login(client, url):
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers["Location"] == "/login"


def test_security_headers_on_every_page(client):
    response = client.get("/login")
    headers = response.headers
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-Content-Type-Options"] == "nosniff"


def test_home_shows_progress_and_last_result(client, logged_in):
    client.post("/chapters/1", data={"q1": "22", "q2": "80"})
    page = client.get("/").get_data(as_text=True)
    assert "خلصت 1 من 2 فصول" in page
    assert "1/2" in page


def test_subject_page_shows_best_score(client, logged_in):
    client.post("/chapters/1", data={"q1": "22", "q2": "80"})
    client.post("/chapters/1", data={"q1": "21", "q2": "80"})
    page = client.get("/subjects/1").get_data(as_text=True)
    assert "أفضل نتيجة 1/2" in page


def test_visitor_sees_landing_page(client):
    page = client.get("/").get_data(as_text=True)
    assert "ذاكر موادك" in page
    assert 'href="/register"' in page
    assert "Test subject" not in page

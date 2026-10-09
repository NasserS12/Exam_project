import pytest

import db
from app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    app.config["SECRET_KEY"] = "test-secret-key"
    return app.test_client()


def register_user(client, username="nasser", password="mypassword123"):
    return client.post("/register", data={"username": username, "password": password})


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
    assert response.status_code == 200
    assert 'href="/login"' in response.get_data(as_text=True)


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


def test_home_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "اختر الفصل وابدأ الاختبار" in response.get_data(as_text=True)


def test_unknown_route_returns_404(client):
    response = client.get("/test")
    assert response.status_code == 404


def test_about_returns_200(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert "المنصة تقدر ترفع فيها ملفات" in response.get_data(as_text=True)
    assert "Networking" in response.get_data(as_text=True)


def test_chapters_page(client):
    response = client.get("/chapters")
    assert response.status_code == 200
    assert "اختر الفصل اللي تبي تذاكره" in response.get_data(as_text=True)
    assert "Cryptography" in response.get_data(as_text=True)


def test_home_links_to_chapters(client):
    response = client.get("/")
    assert response.status_code == 200
    assert 'href="/chapters"' in response.get_data(as_text=True)


def test_chapter_page_shows_questions(client):
    response = client.get("/chapters/1")
    assert response.status_code == 200
    assert "وش المنفذ الافتراضي" in response.get_data(as_text=True)


def test_missing_chapter_returns_404(client):
    response = client.get("/chapters/999")
    assert response.status_code == 404


def test_chapters_page_links_to_chapter(client):
    response = client.get("/chapters")
    assert response.status_code == 200
    assert 'href="/chapters/1"' in response.get_data(as_text=True)


def test_chapter_quiz_one_wrong_answer(client):
    response = client.post("/chapters/1", data={"q1": "21", "q2": "443"})
    assert response.status_code == 200
    assert "إجابة خاطئة" in response.get_data(as_text=True)
    assert "إجابة صحيحة" in response.get_data(as_text=True)
    assert "نتيجتك: 1 من 2" in response.get_data(as_text=True)


def test_chapter_quiz_all_answers_correct(client):
    response = client.post("/chapters/1", data={"q1": "22", "q2": "443"})
    assert response.status_code == 200
    assert "إجابة صحيحة" in response.get_data(as_text=True)
    assert "إجابة خاطئة" not in response.get_data(as_text=True)
    assert "نتيجتك: 2 من 2" in response.get_data(as_text=True)


def test_chapter_quiz_missing_answer(client):
    response = client.post("/chapters/1", data={"q1": "22"})
    assert response.status_code == 400
    assert "جاوب على كل الأسئلة من الخيارات" in response.get_data(as_text=True)


def test_chapter_quiz_invalid_answer(client):
    response = client.post("/chapters/1", data={"q1": "22222222", "q2": "443"})
    assert response.status_code == 400
    assert "جاوب على كل الأسئلة من الخيارات" in response.get_data(as_text=True)


def test_chapter_quiz_all_answers_wrong_shows_zero(client):
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
        "SELECT password_hash FROM users WHERE username = ?", ("nasser",)
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


def test_home_links_to_register(client):
    response = client.get("/")
    assert response.status_code == 200
    assert 'href="/register"' in response.get_data(as_text=True)


def test_old_quiz_page_removed(client):
    response = client.get("/quiz")
    assert response.status_code == 404

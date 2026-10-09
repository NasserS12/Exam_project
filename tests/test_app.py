import pytest

import db
from app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    return app.test_client()


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


def test_chapter_quiz_all_answers_correct(client):
    response = client.post("/chapters/1", data={"q1": "22", "q2": "443"})
    assert response.status_code == 200
    assert "إجابة صحيحة" in response.get_data(as_text=True)
    assert "إجابة خاطئة" not in response.get_data(as_text=True)


def test_chapter_quiz_missing_answer(client):
    response = client.post("/chapters/1", data={"q1": "22"})
    assert response.status_code == 400
    assert "جاوب على كل الأسئلة من الخيارات" in response.get_data(as_text=True)


def test_chapter_quiz_invalid_answer(client):
    response = client.post("/chapters/1", data={"q1": "22222222", "q2": "443"})
    assert response.status_code == 400
    assert "جاوب على كل الأسئلة من الخيارات" in response.get_data(as_text=True)


def test_old_quiz_page_removed(client):
    response = client.get("/quiz")
    assert response.status_code == 404

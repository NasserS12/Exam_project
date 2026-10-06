import pytest

from app import app


@pytest.fixture
def client():
    return app.test_client()


def test_home_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "اختر الفصل وابدأ الاختبار" in response.get_data(as_text=True)


def test_error_return_404(client):
    response = client.get("/test")
    assert response.status_code == 404


def test_about_returns_200(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert "المنصة تقدر ترفع فيها ملفات" in response.get_data(as_text=True)


def test_quiz_correct_answer(client):
    response = client.post("/quiz", data={"answer": "22"})
    assert response.status_code == 200
    assert "إجابة صحيحة" in response.get_data(as_text=True)


def test_quiz_without_answer(client):
    response = client.post("/quiz", data={})
    assert response.status_code == 400
    assert "اختر إجابة من الخيارات" in response.get_data(as_text=True)


def test_quiz_invalid_answer(client):
    response = client.post("/quiz", data={"answer": "999"})
    assert response.status_code == 400
    assert "اختر إجابة من الخيارات" in response.get_data(as_text=True)


def test_quiz_wrong_answer(client):
    response = client.post("/quiz", data={"answer": "80"})
    assert response.status_code == 200
    assert "إجابة خاطئة" in response.get_data(as_text=True)

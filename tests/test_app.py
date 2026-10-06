from app import app


def test_home_returns_200():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert "منصة الاختبارات" in response.get_data(as_text=True)

def test_error_return_404():
    client = app.test_client()
    response = client.get("/test")
    assert response.status_code == 404

def test_about_returns_200():
    client = app.test_client()
    response = client.get("/about")
    assert response.status_code == 200
    assert "المنصة تقدر ترفع فيها ملفات" in response.get_data(as_text=True)
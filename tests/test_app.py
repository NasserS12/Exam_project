from app import app


def test_home_returns_200():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200

def test_error_return_404():
    client = app.test_client()
    response = client.get("/test")
    assert response.status_code == 404
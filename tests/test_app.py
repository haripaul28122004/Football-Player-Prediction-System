import app as flask_app


def test_home_returns_http_200():
    client = flask_app.app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "Flask CI/CD Assignment"


def test_health_returns_http_200():
    client = flask_app.app.test_client()
    response = client.get("/health")

    assert response.status_code == 200


def test_health_returns_ok_status():
    client = flask_app.app.test_client()
    response = client.get("/health")

    assert response.get_json() == {"status": "ok"}

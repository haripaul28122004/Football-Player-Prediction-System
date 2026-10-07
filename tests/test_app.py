import os
import sqlite3

# Generate an in-memory key for tests; never read, print, or commit the local .env key.
os.environ.setdefault("FLASK_SECRET_KEY", os.urandom(32).hex())

import app as football_app


import pytest


@pytest.fixture
def client_and_database(tmp_path, monkeypatch):
    database_path = tmp_path / "test_database.db"
    monkeypatch.setattr(football_app, "DATABASE_PATH", database_path)
    football_app.initialize_database()
    football_app.app.config.update(TESTING=True)

    with football_app.app.test_client() as client:
        yield client, database_path


def csrf_token(client):
    client.get("/register")
    with client.session_transaction() as session_data:
        return session_data["csrf_token"]


def test_existing_home_and_prediction_pages_still_load(client_and_database):
    client, _ = client_and_database

    assert client.get("/").status_code == 200
    assert client.get("/prediction").status_code == 200


def test_registration_stores_only_hash_and_salt(client_and_database):
    client, database_path = client_and_database
    token = csrf_token(client)

    response = client.post(
        "/register",
        data={
            "csrf_token": token,
            "username": "sample_user",
            "password": "Football123",
            "confirm_password": "Football123",
        },
    )

    assert response.status_code == 302
    with sqlite3.connect(database_path) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(users)")]
        user = connection.execute(
            "SELECT username, password_hash, salt FROM users WHERE username = ?",
            ("sample_user",),
        ).fetchone()

    assert columns == ["username", "password_hash", "salt"]
    assert user is not None
    assert user[1] != "Football123"
    assert len(user[1]) == 64
    assert len(user[2]) == 32


def test_weak_password_is_rejected(client_and_database):
    client, _ = client_and_database
    token = csrf_token(client)

    response = client.post(
        "/register",
        data={
            "csrf_token": token,
            "username": "sample_user",
            "password": "weak",
            "confirm_password": "weak",
        },
    )

    assert response.status_code == 200
    assert b"at least 8 characters" in response.data


def test_login_and_logout_manage_session(client_and_database):
    client, _ = client_and_database
    token = csrf_token(client)
    client.post(
        "/register",
        data={
            "csrf_token": token,
            "username": "sample_user",
            "password": "Football123",
            "confirm_password": "Football123",
        },
    )

    token = csrf_token(client)
    login_response = client.post(
        "/login",
        data={"csrf_token": token, "username": "sample_user", "password": "Football123"},
    )

    assert login_response.status_code == 302
    client.get("/prediction")
    with client.session_transaction() as session_data:
        assert session_data["username"] == "sample_user"
        token = session_data["csrf_token"]

    logout_response = client.post("/logout", data={"csrf_token": token})

    assert logout_response.status_code == 302
    with client.session_transaction() as session_data:
        assert "username" not in session_data


def test_wrong_password_is_rejected(client_and_database):
    client, _ = client_and_database
    token = csrf_token(client)
    client.post(
        "/register",
        data={
            "csrf_token": token,
            "username": "sample_user",
            "password": "Football123",
            "confirm_password": "Football123",
        },
    )

    token = csrf_token(client)
    response = client.post(
        "/login",
        data={"csrf_token": token, "username": "sample_user", "password": "WrongPass123"},
    )

    assert response.status_code == 200
    assert b"Username or password is incorrect" in response.data

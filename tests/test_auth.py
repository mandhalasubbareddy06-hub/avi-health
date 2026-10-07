import sqlite3

import app as app_module


def test_database_and_authentication_flow(tmp_path):
    database = tmp_path / "avi-health.db"
    app_module.DATABASE_PATH = str(database)
    app_module.init_db()

    client = app_module.app.test_client()

    response = client.post(
        "/register",
        data={
            "mail": "user@example.com",
            "password": "StrongPassword123!",
            "confirm_password": "StrongPassword123!",
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")

    with sqlite3.connect(database) as connection:
        rows = connection.execute("SELECT mail, password_hash FROM users").fetchall()
    assert rows[0][0] == "user@example.com"
    assert rows[0][1] != "StrongPassword123!"

    duplicate = client.post(
        "/register",
        data={
            "mail": "USER@example.com",
            "password": "AnotherPassword123!",
            "confirm_password": "AnotherPassword123!",
        },
    )
    assert duplicate.status_code == 400
    assert b"already registered" in duplicate.data.lower()

    response = client.post(
        "/login",
        data={"mail": "user@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401

    response = client.post(
        "/login",
        data={"mail": "user@example.com", "password": "StrongPassword123!"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")

    response = client.get("/")
    assert response.status_code == 200
    assert b"Your health story" in response.data

    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"Good morning, User." in response.data

    response = client.get("/logout")
    assert response.status_code == 302
    assert client.get("/dashboard").status_code == 302


def test_dashboard_is_protected_and_serves_product_assets(tmp_path):
    database = tmp_path / "avi-health.db"
    app_module.DATABASE_PATH = str(database)
    app_module.init_db()
    client = app_module.app.test_client()

    assert client.get("/health").get_json() == {"status": "ok"}
    assert client.get("/").status_code == 200
    assert b"Your health story" in client.get("/").data

    client.post(
        "/register",
        data={
            "mail": "user@example.com",
            "password": "StrongPassword123!",
            "confirm_password": "StrongPassword123!",
        },
    )
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"Good morning, User." in response.data
    assert client.get("/static/dashboard-product.css").status_code == 200
    assert client.get("/static/landing.css").status_code == 200
    assert client.get("/static/app.js").status_code == 200


def test_authenticated_health_records_are_isolated_by_user(tmp_path):
    database = tmp_path / "avi-health.db"
    app_module.DATABASE_PATH = str(database)
    app_module.init_db()
    client = app_module.app.test_client()

    client.post(
        "/register",
        data={"mail": "user@example.com", "password": "StrongPassword123!", "confirm_password": "StrongPassword123!"},
    )
    client.post(
        "/register",
        data={"mail": "other@example.com", "password": "StrongPassword123!", "confirm_password": "StrongPassword123!"},
    )

    response = client.post(
        "/records",
        data={"title": "Blood pressure", "category": "Tracking", "details": "120/80"},
    )
    assert response.status_code == 201
    record = response.get_json()["record"]
    record_id = record["id"]

    response = client.get("/records/api")
    assert response.status_code == 200
    assert response.get_json()["records"][0]["title"] == "Blood pressure"

    response = client.patch(
        f"/records/{record_id}",
        data={"details": "122/82"},
    )
    assert response.status_code == 200
    assert response.get_json()["record"]["details"] == "122/82"

    response = client.delete(f"/records/{record_id}")
    assert response.status_code == 204
    assert client.get("/records/api").get_json()["records"] == []

    other_client = app_module.app.test_client()
    other_client.post(
        "/login",
        data={"mail": "other@example.com", "password": "StrongPassword123!"},
    )
    assert other_client.get("/records/api").get_json()["records"] == []

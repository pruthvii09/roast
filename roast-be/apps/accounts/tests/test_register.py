import pytest

pytestmark = pytest.mark.django_db


def test_register_happy_path(api_client):
    response = api_client.post(
        "/api/v1/auth/register/",
        {"email": "new@example.com", "password": "Str0ngPassw0rd!", "display_name": "New User"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "new@example.com"
    assert "password" not in body["data"]


def test_register_duplicate_email_rejected(api_client, user_factory):
    user_factory(email="dupe@example.com")
    response = api_client.post(
        "/api/v1/auth/register/",
        {"email": "dupe@example.com", "password": "Str0ngPassw0rd!"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_register_weak_password_rejected(api_client):
    response = api_client.post(
        "/api/v1/auth/register/",
        {"email": "weak@example.com", "password": "123"},
    )
    assert response.status_code == 400


def test_register_missing_fields_rejected(api_client):
    response = api_client.post("/api/v1/auth/register/", {})
    assert response.status_code == 400

import pytest

pytestmark = pytest.mark.django_db


def test_login_with_correct_credentials(api_client, user_factory):
    user_factory(email="login@example.com", password="Str0ngPassw0rd!")
    response = api_client.post(
        "/api/v1/auth/login/", {"email": "login@example.com", "password": "Str0ngPassw0rd!"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access" in body["data"]
    assert "refresh" in body["data"]


def test_login_with_wrong_password_rejected(api_client, user_factory):
    user_factory(email="login2@example.com", password="Str0ngPassw0rd!")
    response = api_client.post(
        "/api/v1/auth/login/", {"email": "login2@example.com", "password": "wrong"}
    )
    assert response.status_code == 401


def test_login_inactive_user_rejected(api_client, user_factory):
    user = user_factory(email="inactive@example.com", password="Str0ngPassw0rd!")
    user.is_active = False
    user.save(update_fields=["is_active"])
    response = api_client.post(
        "/api/v1/auth/login/", {"email": "inactive@example.com", "password": "Str0ngPassw0rd!"}
    )
    assert response.status_code == 401


def test_refresh_returns_new_access_token(api_client, user_factory):
    user_factory(email="refresh@example.com", password="Str0ngPassw0rd!")
    login = api_client.post(
        "/api/v1/auth/login/", {"email": "refresh@example.com", "password": "Str0ngPassw0rd!"}
    )
    refresh_token = login.json()["data"]["refresh"]
    response = api_client.post("/api/v1/auth/refresh/", {"refresh": refresh_token})
    assert response.status_code == 200
    assert "access" in response.json()["data"]


def test_logout_blacklists_refresh_token(api_client, user_factory):
    user_factory(email="logout@example.com", password="Str0ngPassw0rd!")
    login = api_client.post(
        "/api/v1/auth/login/", {"email": "logout@example.com", "password": "Str0ngPassw0rd!"}
    )
    data = login.json()["data"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {data['access']}")

    logout_response = api_client.post("/api/v1/auth/logout/", {"refresh": data["refresh"]})
    assert logout_response.status_code == 204

    api_client.credentials()
    reuse_response = api_client.post("/api/v1/auth/refresh/", {"refresh": data["refresh"]})
    assert reuse_response.status_code == 401


def test_logout_requires_authentication(api_client, user_factory):
    user_factory(email="logout2@example.com", password="Str0ngPassw0rd!")
    login = api_client.post(
        "/api/v1/auth/login/", {"email": "logout2@example.com", "password": "Str0ngPassw0rd!"}
    )
    refresh_token = login.json()["data"]["refresh"]
    response = api_client.post("/api/v1/auth/logout/", {"refresh": refresh_token})
    assert response.status_code == 401

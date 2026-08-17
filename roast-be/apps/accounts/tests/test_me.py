import pytest

pytestmark = pytest.mark.django_db


def test_get_me_returns_own_profile(authenticated_client, user):
    response = authenticated_client.get("/api/v1/auth/me/")
    assert response.status_code == 200
    assert response.json()["data"]["email"] == user.email


def test_get_me_requires_authentication(api_client):
    response = api_client.get("/api/v1/auth/me/")
    assert response.status_code == 401


def test_patch_me_updates_display_name(authenticated_client, user):
    response = authenticated_client.patch("/api/v1/auth/me/", {"display_name": "New Name"})
    assert response.status_code == 200
    assert response.json()["data"]["display_name"] == "New Name"
    user.refresh_from_db()
    assert user.display_name == "New Name"


def test_patch_me_ignores_email_change(authenticated_client, user):
    original_email = user.email
    response = authenticated_client.patch("/api/v1/auth/me/", {"email": "changed@example.com"})
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.email == original_email


def test_patch_me_updates_avatar_url(authenticated_client, user):
    response = authenticated_client.patch(
        "/api/v1/auth/me/", {"avatar_url": "https://example.com/avatar.png"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["avatar_url"] == "https://example.com/avatar.png"
    user.refresh_from_db()
    assert user.avatar_url == "https://example.com/avatar.png"


def test_patch_me_rejects_invalid_avatar_url(authenticated_client):
    response = authenticated_client.patch("/api/v1/auth/me/", {"avatar_url": "not-a-url"})
    assert response.status_code == 400


def test_me_response_never_includes_password(authenticated_client):
    response = authenticated_client.get("/api/v1/auth/me/")
    assert "password" not in response.json()["data"]

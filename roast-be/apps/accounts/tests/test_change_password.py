import pytest
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = pytest.mark.django_db

DEFAULT_PASSWORD = "Str0ngPassw0rd!"
NEW_PASSWORD = "N3wStrongPassw0rd!"


def _client_with_tokens(api_client_cls, user):
    client = api_client_cls()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client, str(refresh)


class TestChangePassword:
    def test_success_updates_password(self, api_client, user):
        client, _ = _client_with_tokens(type(api_client), user)

        response = client.post(
            "/api/v1/auth/change-password/",
            {"old_password": DEFAULT_PASSWORD, "new_password": NEW_PASSWORD},
        )

        assert response.status_code == 200
        assert response.json()["success"] is True
        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD)

    def test_wrong_old_password_rejected(self, api_client, user):
        client, _ = _client_with_tokens(type(api_client), user)

        response = client.post(
            "/api/v1/auth/change-password/",
            {"old_password": "TotallyWrong!", "new_password": NEW_PASSWORD},
        )

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        user.refresh_from_db()
        assert user.check_password(DEFAULT_PASSWORD)

    def test_weak_new_password_rejected(self, api_client, user):
        client, _ = _client_with_tokens(type(api_client), user)

        response = client.post(
            "/api/v1/auth/change-password/",
            {"old_password": DEFAULT_PASSWORD, "new_password": "123"},
        )

        assert response.status_code == 400

    def test_new_password_same_as_old_rejected(self, api_client, user):
        client, _ = _client_with_tokens(type(api_client), user)

        response = client.post(
            "/api/v1/auth/change-password/",
            {"old_password": DEFAULT_PASSWORD, "new_password": DEFAULT_PASSWORD},
        )

        assert response.status_code == 400

    def test_missing_fields_rejected(self, api_client, user):
        client, _ = _client_with_tokens(type(api_client), user)

        response = client.post("/api/v1/auth/change-password/", {})

        assert response.status_code == 400

    def test_requires_authentication(self, api_client):
        response = api_client.post(
            "/api/v1/auth/change-password/",
            {"old_password": DEFAULT_PASSWORD, "new_password": NEW_PASSWORD},
        )
        assert response.status_code == 401

    def test_invalidates_all_outstanding_refresh_tokens(self, api_client, user):
        client, refresh_str = _client_with_tokens(type(api_client), user)
        # A second, independent session for the same user (e.g. another device).
        _, other_refresh_str = _client_with_tokens(type(api_client), user)

        response = client.post(
            "/api/v1/auth/change-password/",
            {"old_password": DEFAULT_PASSWORD, "new_password": NEW_PASSWORD},
        )
        assert response.status_code == 200

        anon_client = type(api_client)()
        refresh_attempt = anon_client.post("/api/v1/auth/refresh/", {"refresh": refresh_str})
        other_refresh_attempt = anon_client.post(
            "/api/v1/auth/refresh/", {"refresh": other_refresh_str}
        )

        assert refresh_attempt.status_code == 401
        assert other_refresh_attempt.status_code == 401

    def test_can_login_with_new_password_after_change(self, api_client, user):
        client, _ = _client_with_tokens(type(api_client), user)
        client.post(
            "/api/v1/auth/change-password/",
            {"old_password": DEFAULT_PASSWORD, "new_password": NEW_PASSWORD},
        )

        response = api_client.post(
            "/api/v1/auth/login/", {"email": user.email, "password": NEW_PASSWORD}
        )
        assert response.status_code == 200

    def test_cannot_login_with_old_password_after_change(self, api_client, user):
        client, _ = _client_with_tokens(type(api_client), user)
        client.post(
            "/api/v1/auth/change-password/",
            {"old_password": DEFAULT_PASSWORD, "new_password": NEW_PASSWORD},
        )

        response = api_client.post(
            "/api/v1/auth/login/", {"email": user.email, "password": DEFAULT_PASSWORD}
        )
        assert response.status_code == 401

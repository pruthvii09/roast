import pytest
from rest_framework.throttling import SimpleRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = pytest.mark.django_db


def _set_rate(monkeypatch, scope, rate):
    # ScopedRateThrottle.THROTTLE_RATES is a single dict object bound once
    # at import time from settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
    # — overriding settings.REST_FRAMEWORK at runtime does NOT re-bind it,
    # so tests must patch the shared dict directly (with automatic
    # teardown via monkeypatch.setitem) rather than use the `settings`
    # fixture here.
    monkeypatch.setitem(SimpleRateThrottle.THROTTLE_RATES, scope, rate)


class TestAuthThrottling:
    def test_login_is_throttled_after_rate_exceeded(self, api_client, user_factory, monkeypatch):
        _set_rate(monkeypatch, "auth-login", "1/min")
        user_factory(email="throttle-login@example.com", password="Str0ngPassw0rd!")
        payload = {"email": "throttle-login@example.com", "password": "Str0ngPassw0rd!"}

        first = api_client.post("/api/v1/auth/login/", payload)
        assert first.status_code == 200

        second = api_client.post("/api/v1/auth/login/", payload)
        assert second.status_code == 429

    def test_register_is_throttled_after_rate_exceeded(self, api_client, monkeypatch):
        _set_rate(monkeypatch, "auth-register", "1/hour")

        first = api_client.post(
            "/api/v1/auth/register/",
            {"email": "one@example.com", "password": "Str0ngPassw0rd!"},
        )
        assert first.status_code == 201

        second = api_client.post(
            "/api/v1/auth/register/",
            {"email": "two@example.com", "password": "Str0ngPassw0rd!"},
        )
        assert second.status_code == 429

    def test_change_password_is_throttled_after_rate_exceeded(self, api_client, user, monkeypatch):
        _set_rate(monkeypatch, "auth-password-change", "1/hour")
        client = type(api_client)()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        first = client.post(
            "/api/v1/auth/change-password/",
            {"old_password": "wrong-but-still-counts", "new_password": "N3wStrongPassw0rd!"},
        )
        assert first.status_code == 400  # wrong old_password, but quota is now consumed

        second = client.post(
            "/api/v1/auth/change-password/",
            {"old_password": "Str0ngPassw0rd!", "new_password": "N3wStrongPassw0rd!"},
        )
        assert second.status_code == 429

    def test_throttling_is_scoped_per_endpoint(self, api_client, user_factory, monkeypatch):
        # Exhausting the login quota must not affect an unrelated endpoint
        # (register) that has its own independent scope/rate.
        _set_rate(monkeypatch, "auth-login", "1/min")
        user_factory(email="scoped@example.com", password="Str0ngPassw0rd!")
        payload = {"email": "scoped@example.com", "password": "Str0ngPassw0rd!"}

        api_client.post("/api/v1/auth/login/", payload)
        throttled = api_client.post("/api/v1/auth/login/", payload)
        assert throttled.status_code == 429

        register_response = api_client.post(
            "/api/v1/auth/register/",
            {"email": "unrelated@example.com", "password": "Str0ngPassw0rd!"},
        )
        assert register_response.status_code == 201

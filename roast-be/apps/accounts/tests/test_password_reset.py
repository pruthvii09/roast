import pytest
from django.utils import timezone

from apps.accounts.models import EmailOTP, OTPPurpose
from apps.accounts.services import _hash_otp

pytestmark = pytest.mark.django_db


def _seed_otp(user, code="123456"):
    return EmailOTP.objects.create(
        user=user,
        purpose=OTPPurpose.PASSWORD_RESET,
        code_hash=_hash_otp(code),
        expires_at=timezone.now() + timezone.timedelta(minutes=10),
    )


class TestRequestPasswordResetView:
    def test_returns_200_for_existing_account(self, api_client, user):
        response = api_client.post("/api/v1/auth/password-reset/request/", {"email": user.email})
        assert response.status_code == 200
        assert EmailOTP.objects.filter(user=user, purpose=OTPPurpose.PASSWORD_RESET).exists()

    def test_returns_200_for_unknown_email_too(self, api_client):
        response = api_client.post(
            "/api/v1/auth/password-reset/request/", {"email": "nobody@example.com"}
        )
        assert response.status_code == 200


class TestConfirmPasswordResetView:
    def test_correct_code_resets_password(self, api_client, user):
        _seed_otp(user)
        response = api_client.post(
            "/api/v1/auth/password-reset/confirm/",
            {"email": user.email, "code": "123456", "new_password": "N3wStr0ngPass!"},
        )
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.check_password("N3wStr0ngPass!") is True

    def test_can_login_with_new_password_after_reset(self, api_client, user):
        _seed_otp(user)
        api_client.post(
            "/api/v1/auth/password-reset/confirm/",
            {"email": user.email, "code": "123456", "new_password": "N3wStr0ngPass!"},
        )
        response = api_client.post(
            "/api/v1/auth/login/", {"email": user.email, "password": "N3wStr0ngPass!"}
        )
        assert response.status_code == 200

    def test_wrong_code_rejected(self, api_client, user):
        _seed_otp(user)
        old_password_hash = user.password
        response = api_client.post(
            "/api/v1/auth/password-reset/confirm/",
            {"email": user.email, "code": "000000", "new_password": "N3wStr0ngPass!"},
        )
        assert response.status_code == 400
        user.refresh_from_db()
        assert user.password == old_password_hash

    def test_weak_new_password_rejected(self, api_client, user):
        _seed_otp(user)
        response = api_client.post(
            "/api/v1/auth/password-reset/confirm/",
            {"email": user.email, "code": "123456", "new_password": "123"},
        )
        assert response.status_code == 400

    def test_unknown_email_rejected_generically(self, api_client):
        response = api_client.post(
            "/api/v1/auth/password-reset/confirm/",
            {"email": "nobody@example.com", "code": "123456", "new_password": "N3wStr0ngPass!"},
        )
        assert response.status_code == 400

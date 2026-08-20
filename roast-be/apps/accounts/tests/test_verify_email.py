import pytest
from django.utils import timezone

from apps.accounts.models import EmailOTP, OTPPurpose
from apps.accounts.services import _hash_otp

pytestmark = pytest.mark.django_db


def _seed_otp(user, purpose, code="123456"):
    return EmailOTP.objects.create(
        user=user,
        purpose=purpose,
        code_hash=_hash_otp(code),
        expires_at=timezone.now() + timezone.timedelta(minutes=10),
    )


class TestVerifyEmailView:
    def test_correct_code_verifies_and_returns_tokens(self, api_client, user_factory):
        user = user_factory(email="verify-me@example.com", email_verified=False)
        _seed_otp(user, OTPPurpose.EMAIL_VERIFICATION)

        response = api_client.post(
            "/api/v1/auth/verify-email/", {"email": "verify-me@example.com", "code": "123456"}
        )

        assert response.status_code == 200
        body = response.json()["data"]
        assert "access" in body
        assert "refresh" in body
        user.refresh_from_db()
        assert user.email_verified is True

    def test_wrong_code_rejected(self, api_client, user_factory):
        user = user_factory(email="verify-wrong@example.com", email_verified=False)
        _seed_otp(user, OTPPurpose.EMAIL_VERIFICATION)

        response = api_client.post(
            "/api/v1/auth/verify-email/", {"email": "verify-wrong@example.com", "code": "000000"}
        )

        assert response.status_code == 400
        user.refresh_from_db()
        assert user.email_verified is False

    def test_unknown_email_rejected_generically(self, api_client):
        response = api_client.post(
            "/api/v1/auth/verify-email/", {"email": "nope@example.com", "code": "123456"}
        )
        assert response.status_code == 400


class TestResendVerificationEmailView:
    def test_returns_200_for_unverified_account(self, api_client, user_factory):
        user_factory(email="resend-me@example.com", email_verified=False)
        response = api_client.post(
            "/api/v1/auth/verify-email/resend/", {"email": "resend-me@example.com"}
        )
        assert response.status_code == 200

    def test_returns_200_for_unknown_email_too(self, api_client):
        response = api_client.post(
            "/api/v1/auth/verify-email/resend/", {"email": "nobody@example.com"}
        )
        assert response.status_code == 200

    def test_does_not_resend_for_already_verified_account(self, api_client, user_factory):
        user = user_factory(email="already-verified@example.com", email_verified=True)
        response = api_client.post(
            "/api/v1/auth/verify-email/resend/", {"email": "already-verified@example.com"}
        )
        assert response.status_code == 200
        otp_exists = EmailOTP.objects.filter(
            user=user, purpose=OTPPurpose.EMAIL_VERIFICATION
        ).exists()
        assert not otp_exists

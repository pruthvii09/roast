import pytest
from django.utils import timezone

from apps.accounts.models import EmailOTP, OTPPurpose
from apps.accounts.services import (
    _hash_otp,
    confirm_email_verification,
    generate_and_send_otp,
    reset_password_with_otp,
    verify_otp,
)

pytestmark = pytest.mark.django_db


def _latest_otp_code(user, purpose):
    """Tests can't know the real random code (it only ever exists in the
    Celery dispatch args, which don't fire inside a rolled-back test
    transaction — see generate_and_send_otp's on_commit dispatch) — so
    reconstruct it isn't possible; instead these tests create the
    EmailOTP row directly with a known code where they need one."""
    return EmailOTP.objects.filter(user=user, purpose=purpose).order_by("-created_at").first()


class TestGenerateAndSendOtp:
    def test_creates_unconsumed_otp_row(self, user):
        generate_and_send_otp(user=user, purpose=OTPPurpose.EMAIL_VERIFICATION)
        otp = _latest_otp_code(user, OTPPurpose.EMAIL_VERIFICATION)
        assert otp is not None
        assert otp.consumed_at is None
        assert otp.attempts == 0
        assert otp.expires_at > timezone.now()

    def test_older_unconsumed_codes_are_left_in_place(self, user):
        generate_and_send_otp(user=user, purpose=OTPPurpose.EMAIL_VERIFICATION)
        generate_and_send_otp(user=user, purpose=OTPPurpose.EMAIL_VERIFICATION)
        assert (
            EmailOTP.objects.filter(
                user=user, purpose=OTPPurpose.EMAIL_VERIFICATION, consumed_at__isnull=True
            ).count()
            == 2
        )


class TestVerifyOtp:
    def _make_otp(self, user, purpose=OTPPurpose.EMAIL_VERIFICATION, code="123456", **kwargs):
        defaults = {
            "expires_at": timezone.now() + timezone.timedelta(minutes=10),
        }
        defaults.update(kwargs)
        return EmailOTP.objects.create(
            user=user, purpose=purpose, code_hash=_hash_otp(code), **defaults
        )

    def test_correct_code_succeeds_and_consumes(self, user):
        otp = self._make_otp(user)
        assert verify_otp(user=user, code="123456", purpose=OTPPurpose.EMAIL_VERIFICATION) is True
        otp.refresh_from_db()
        assert otp.consumed_at is not None

    def test_wrong_code_fails_and_increments_attempts(self, user):
        otp = self._make_otp(user)
        assert verify_otp(user=user, code="000000", purpose=OTPPurpose.EMAIL_VERIFICATION) is False
        otp.refresh_from_db()
        assert otp.attempts == 1
        assert otp.consumed_at is None

    def test_locks_out_after_max_attempts(self, user, settings):
        settings.OTP_MAX_ATTEMPTS = 3
        self._make_otp(user, attempts=3)
        # Even the RIGHT code fails once attempts has hit the cap.
        assert verify_otp(user=user, code="123456", purpose=OTPPurpose.EMAIL_VERIFICATION) is False

    def test_expired_code_fails(self, user):
        self._make_otp(user, expires_at=timezone.now() - timezone.timedelta(minutes=1))
        assert verify_otp(user=user, code="123456", purpose=OTPPurpose.EMAIL_VERIFICATION) is False

    def test_already_consumed_code_cannot_be_reused(self, user):
        self._make_otp(user, consumed_at=timezone.now())
        assert verify_otp(user=user, code="123456", purpose=OTPPurpose.EMAIL_VERIFICATION) is False

    def test_wrong_purpose_does_not_match(self, user):
        self._make_otp(user, purpose=OTPPurpose.EMAIL_VERIFICATION)
        assert verify_otp(user=user, code="123456", purpose=OTPPurpose.PASSWORD_RESET) is False

    def test_no_otp_at_all_fails(self, user):
        assert verify_otp(user=user, code="123456", purpose=OTPPurpose.EMAIL_VERIFICATION) is False


class TestConfirmEmailVerification:
    def test_sets_email_verified_on_success(self, user_factory):
        user = user_factory(email_verified=False)
        EmailOTP.objects.create(
            user=user,
            purpose=OTPPurpose.EMAIL_VERIFICATION,
            code_hash=_hash_otp("654321"),
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )
        assert confirm_email_verification(user=user, code="654321") is True
        user.refresh_from_db()
        assert user.email_verified is True

    def test_wrong_code_does_not_verify(self, user_factory):
        user = user_factory(email_verified=False)
        EmailOTP.objects.create(
            user=user,
            purpose=OTPPurpose.EMAIL_VERIFICATION,
            code_hash=_hash_otp("654321"),
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )
        assert confirm_email_verification(user=user, code="000000") is False
        user.refresh_from_db()
        assert user.email_verified is False


class TestResetPasswordWithOtp:
    def test_sets_new_password_and_blacklists_sessions(self, user):
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        OutstandingToken.objects.get(jti=refresh["jti"])  # sanity: token was tracked

        EmailOTP.objects.create(
            user=user,
            purpose=OTPPurpose.PASSWORD_RESET,
            code_hash=_hash_otp("111222"),
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )

        result = reset_password_with_otp(user=user, code="111222", new_password="N3wStr0ngPass!")
        assert result is True
        user.refresh_from_db()
        assert user.check_password("N3wStr0ngPass!") is True
        assert BlacklistedToken.objects.filter(token__jti=refresh["jti"]).exists()

    def test_wrong_code_does_not_change_password(self, user):
        EmailOTP.objects.create(
            user=user,
            purpose=OTPPurpose.PASSWORD_RESET,
            code_hash=_hash_otp("111222"),
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )
        old_password_hash = user.password
        result = reset_password_with_otp(user=user, code="000000", new_password="N3wStr0ngPass!")
        assert result is False
        user.refresh_from_db()
        assert user.password == old_password_hash

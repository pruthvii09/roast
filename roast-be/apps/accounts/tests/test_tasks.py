import uuid
from unittest.mock import patch

import pytest

from apps.accounts.models import OTPPurpose
from apps.accounts.tasks import send_otp_email_task

pytestmark = pytest.mark.django_db


class TestSendOtpEmailTask:
    def test_sends_to_user_with_expected_subject_and_code(self, user):
        with patch("apps.accounts.tasks.send_email") as mock_send:
            send_otp_email_task(str(user.id), "123456", OTPPurpose.EMAIL_VERIFICATION)

        mock_send.assert_called_once()
        kwargs = mock_send.call_args.kwargs
        assert kwargs["to"] == user.email
        assert "Verify your email" in kwargs["subject"]
        assert "1 2 3 4 5 6" in kwargs["html"]  # rendered letter-spaced, see render_otp_email

    def test_password_reset_purpose_uses_different_subject(self, user):
        with patch("apps.accounts.tasks.send_email") as mock_send:
            send_otp_email_task(str(user.id), "654321", OTPPurpose.PASSWORD_RESET)

        kwargs = mock_send.call_args.kwargs
        assert "Reset your password" in kwargs["subject"]

    def test_missing_user_is_a_noop(self):
        with patch("apps.accounts.tasks.send_email") as mock_send:
            send_otp_email_task(str(uuid.uuid4()), "123456", OTPPurpose.EMAIL_VERIFICATION)
        mock_send.assert_not_called()

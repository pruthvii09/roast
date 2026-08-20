from unittest.mock import MagicMock, patch

import pytest

from apps.notifications.emails import get_resend_client, send_email


@pytest.fixture(autouse=True)
def _clear_client_cache():
    get_resend_client.cache_clear()
    yield
    get_resend_client.cache_clear()


class TestGetResendClient:
    def test_sets_api_key_from_settings(self, settings):
        settings.RESEND_API_KEY = "re_test_123"
        client = get_resend_client()
        assert client.api_key == "re_test_123"


class TestSendEmail:
    def test_calls_emails_send_with_expected_params(self, settings):
        settings.DEFAULT_FROM_EMAIL = "noreply@test.com"
        fake_client = MagicMock()
        with patch("apps.notifications.emails.get_resend_client", return_value=fake_client):
            send_email(to="user@example.com", subject="Hi", html="<p>hi</p>")

        fake_client.Emails.send.assert_called_once_with(
            {
                "from": "noreply@test.com",
                "to": "user@example.com",
                "subject": "Hi",
                "html": "<p>hi</p>",
            }
        )

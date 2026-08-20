from unittest.mock import patch

from apps.notifications.tasks import send_email_task


class TestSendEmailTask:
    def test_delegates_to_send_email(self):
        with patch("apps.notifications.tasks.send_email") as mock_send:
            send_email_task(to="a@b.com", subject="s", html="<p>h</p>")
        mock_send.assert_called_once_with(to="a@b.com", subject="s", html="<p>h</p>")

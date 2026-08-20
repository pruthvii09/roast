"""
The single wrapper around Resend for the whole project. Nothing outside
this module should ever import `resend` directly or touch
`resend.api_key` — every caller (apps.accounts.tasks,
apps.notifications.tasks, and anything added later) just calls
send_email(...).
"""

from functools import lru_cache

from django.conf import settings


@lru_cache(maxsize=1)
def get_resend_client():
    import resend

    resend.api_key = settings.RESEND_API_KEY
    return resend


def send_email(to: str, subject: str, html: str):
    client = get_resend_client()
    return client.Emails.send(
        {
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": to,
            "subject": subject,
            "html": html,
        }
    )

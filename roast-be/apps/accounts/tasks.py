import logging

from celery import shared_task

from apps.notifications.emails import send_email

from .emails import get_subject, render_otp_email
from .models import User

logger = logging.getLogger(__name__)


@shared_task(name="apps.accounts.send_otp_email")
def send_otp_email_task(user_id: str, code: str, purpose: str) -> None:
    """
    Calls apps.notifications.emails.send_email directly rather than
    dispatching through apps.notifications.tasks.send_email_task — this
    task is already the async boundary, so a second Celery hop would add
    nothing.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.info("OTP email skipped: user %s no longer exists.", user_id)
        return

    subject = get_subject(purpose=purpose)
    html = render_otp_email(code=code, purpose=purpose)
    send_email(to=user.email, subject=subject, html=html)

from celery import shared_task

from .emails import send_email


@shared_task(name="apps.notifications.send_email")
def send_email_task(to: str, subject: str, html: str) -> None:
    """
    Generic async dispatcher for callers with no task of their own to run
    inside. apps.accounts.tasks doesn't use this — its tasks are already
    Celery tasks themselves, so they call send_email() directly instead
    of hopping through another task.
    """
    send_email(to=to, subject=subject, html=html)

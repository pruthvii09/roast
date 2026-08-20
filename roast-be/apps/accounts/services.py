import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from apps.common.storage import get_storage
from apps.submissions.models import SubmissionAsset

from .models import EmailOTP, OTPPurpose, User

_OTP_LENGTH = 6


def change_password(*, user: User, new_password: str) -> None:
    """
    Sets a new password and blacklists every outstanding refresh token for
    the user, forcing every other session to log in again with the new
    password. Wrapped in one transaction so a failure partway through
    doesn't leave the password changed with old sessions still valid (or
    vice versa).

    The short-lived access token used to make *this* request is left
    alone — simplejwt does not track/blacklist access tokens, only
    refresh tokens — it will simply expire on its own soon per
    ACCESS_TOKEN_LIFETIME.
    """
    with transaction.atomic():
        user.set_password(new_password)
        user.save(update_fields=["password"])
        _blacklist_all_outstanding_tokens_for_user(user)


def _blacklist_all_outstanding_tokens_for_user(user: User) -> None:
    outstanding = OutstandingToken.objects.filter(user=user).exclude(blacklistedtoken__isnull=False)
    BlacklistedToken.objects.bulk_create(
        [BlacklistedToken(token=token) for token in outstanding],
        ignore_conflicts=True,
    )


def delete_user_account(*, user: User, requesting_user: User) -> None:
    """
    Permanently and irreversibly deletes a user's account and every row
    that depends on it — the "right to erasure" counterpart to
    apps.submissions.services.delete_submission, generalized from one
    submission to an entire account.

    Storage bytes for every owned SubmissionAsset are purged *before* the
    DB delete — same reasoning as delete_submission: once the asset row
    is gone (via cascade, below), so is its storage_key, and there'd be
    nothing left telling us what to purge. Everything else is handled by
    Django's existing CASCADE chains with zero extra code:
    Submission.owner, RoastRun.submission, RoastRun.owner,
    ExtractionTask.submission, RoastSection.roast, RoastFinding.roast,
    and AIRequest.roast are all on_delete=CASCADE, so deleting the User
    row cascades through every submission, asset row, roast run,
    section, finding, extraction task, and AI-request audit row in one
    statement. simplejwt's own OutstandingToken/BlacklistedToken rows use
    on_delete=SET_NULL (their default) and are left behind with a null
    user rather than deleted — acceptable: they hold no PII beyond a
    token that's already meaningless once the account backing it is gone.
    """
    if user.id != requesting_user.id:
        raise PermissionDenied("You do not have permission to delete this account.")

    storage = get_storage()
    asset_keys = list(
        SubmissionAsset.objects.filter(submission__owner=user).values_list("storage_key", flat=True)
    )
    for storage_key in asset_keys:
        storage.delete(storage_key)

    with transaction.atomic():
        user.delete()


def _hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def generate_and_send_otp(*, user: User, purpose: str) -> None:
    """
    Creates an EmailOTP row and dispatches the send after commit — same
    "don't fire a side effect for a row the transaction might still roll
    back" reasoning as apps.roasts.services._dispatch_roast_processing.
    Older unconsumed codes for this (user, purpose) are left in place
    (harmless — verify_otp only ever checks the newest one) rather than
    deleted, so a slow/duplicate resend can never invalidate a code
    still in flight to the user's inbox.
    """
    code = f"{secrets.randbelow(10**_OTP_LENGTH):0{_OTP_LENGTH}d}"
    EmailOTP.objects.create(
        user=user,
        purpose=purpose,
        code_hash=_hash_otp(code),
        expires_at=timezone.now() + timedelta(minutes=settings.OTP_TTL_MINUTES),
    )

    def _dispatch():
        from .tasks import send_otp_email_task  # local import: tasks.py imports this module

        send_otp_email_task.delay(str(user.id), code, purpose)

    transaction.on_commit(_dispatch)


def verify_otp(*, user: User, code: str, purpose: str) -> bool:
    """
    The single place an OTP is checked and consumed for either purpose.
    Only the most recently created unconsumed row for (user, purpose) is
    ever eligible — see generate_and_send_otp's docstring for why older
    ones are left around rather than deleted.
    """
    otp = (
        EmailOTP.objects.filter(user=user, purpose=purpose, consumed_at__isnull=True)
        .order_by("-created_at")
        .first()
    )
    if otp is None:
        return False
    if otp.expires_at < timezone.now():
        return False
    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        return False
    if otp.code_hash != _hash_otp(code):
        otp.attempts += 1
        otp.save(update_fields=["attempts"])
        return False

    otp.consumed_at = timezone.now()
    otp.save(update_fields=["consumed_at"])
    return True


def confirm_email_verification(*, user: User, code: str) -> bool:
    if not verify_otp(user=user, code=code, purpose=OTPPurpose.EMAIL_VERIFICATION):
        return False
    user.email_verified = True
    user.save(update_fields=["email_verified"])
    return True


def reset_password_with_otp(*, user: User, code: str, new_password: str) -> bool:
    """
    On success, blacklists every outstanding refresh token for the user —
    reuses the same helper change_password() already uses, so a password
    reset forces every other session to log in again too.
    """
    if not verify_otp(user=user, code=code, purpose=OTPPurpose.PASSWORD_RESET):
        return False
    with transaction.atomic():
        user.set_password(new_password)
        user.save(update_fields=["password"])
        _blacklist_all_outstanding_tokens_for_user(user)
    return True

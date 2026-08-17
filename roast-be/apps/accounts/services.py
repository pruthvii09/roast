from django.core.exceptions import PermissionDenied
from django.db import transaction
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from apps.common.storage import get_storage
from apps.submissions.models import SubmissionAsset

from .models import User


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

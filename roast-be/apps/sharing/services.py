from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from apps.accounts.models import User
from apps.roasts.models import RoastRun, RoastStatus

from .exceptions import RoastNotShareableError
from .models import Reaction, ReactionType, ShareLink
from .selectors import get_active_share_link_by_token


def create_or_get_share_link(*, roast: RoastRun, requesting_user: User) -> tuple[ShareLink, bool]:
    """
    Only a completed RoastRun is shareable — nothing to show otherwise.
    Idempotent: the DB partial unique constraint (roast, revoked_at IS
    NULL) means a duplicate "create" request while an active link
    already exists hits IntegrityError, caught here and resolved by
    returning the existing active link instead — enforced atomically by
    Postgres, mirroring apps.roasts.services.create_roast_run's
    idempotent-create pattern. Returns (link, created).
    """
    # Defensive re-check even though the view already scoped the roast
    # lookup to this owner (apps.roasts.services docstring convention).
    if roast.owner_id != requesting_user.id:
        raise PermissionDenied("You do not have permission to share this roast.")
    if roast.status != RoastStatus.COMPLETED:
        raise RoastNotShareableError("Only a completed roast can be shared.")

    try:
        with transaction.atomic():
            share_link = ShareLink.objects.create(roast=roast, owner=requesting_user)
    except IntegrityError:
        existing = (
            ShareLink.objects.filter(roast=roast, revoked_at__isnull=True)
            .order_by("-created_at")
            .first()
        )
        if existing is None:
            raise
        return existing, False
    return share_link, True


def revoke_share_link(*, share_link: ShareLink, requesting_user: User) -> ShareLink:
    if share_link.owner_id != requesting_user.id:
        raise PermissionDenied("You do not have permission to revoke this share link.")
    if share_link.revoked_at is None:  # idempotent — a repeat revoke doesn't move the timestamp
        share_link.revoked_at = timezone.now()
        share_link.save(update_fields=["revoked_at", "updated_at"])
    return share_link


def get_reaction_totals(*, share_link: ShareLink) -> dict[str, int]:
    totals = dict.fromkeys(ReactionType.values, 0)
    totals.update(
        Reaction.objects.filter(share_link=share_link).values_list("reaction_type", "count")
    )
    return totals


def get_public_roast_payload(*, token: str) -> tuple[RoastRun, dict[str, int]]:
    """
    Fire-and-forget view_count increment — a single UPDATE, no need to
    wrap it in the same transaction as the read that follows.
    """
    share_link = get_active_share_link_by_token(token=token)
    ShareLink.objects.filter(pk=share_link.pk).update(view_count=F("view_count") + 1)
    return share_link.roast, get_reaction_totals(share_link=share_link)


def _increment_reaction(*, share_link: ShareLink, reaction_type: str) -> None:
    updated = Reaction.objects.filter(share_link=share_link, reaction_type=reaction_type).update(
        count=F("count") + 1
    )
    if updated:
        return
    try:
        Reaction.objects.create(share_link=share_link, reaction_type=reaction_type, count=1)
    except IntegrityError:
        # Lost a create race to another concurrent first-reaction of the
        # same type — the row exists now, so fall back to incrementing it.
        Reaction.objects.filter(share_link=share_link, reaction_type=reaction_type).update(
            count=F("count") + 1
        )


def record_reaction(*, token: str, reaction_type: str) -> dict[str, int]:
    share_link = get_active_share_link_by_token(token=token)  # same 404 gate as the public GET
    _increment_reaction(share_link=share_link, reaction_type=reaction_type)
    return get_reaction_totals(share_link=share_link)

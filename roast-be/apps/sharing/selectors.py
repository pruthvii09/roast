from uuid import UUID

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from apps.roasts.models import RoastRun
from apps.roasts.selectors import get_owned_roast_runs

from .models import ShareLink


def get_owned_roast_run_or_404(*, owner: User, roast_id: UUID) -> RoastRun:
    return get_object_or_404(get_owned_roast_runs(owner=owner), pk=roast_id)


def get_share_links_for_roast(*, roast: RoastRun) -> QuerySet:
    return ShareLink.objects.filter(roast=roast).order_by("-created_at")


def get_owned_share_links(*, owner: User) -> QuerySet:
    # Deliberately NOT filtered by roast__submission__deleted_at — a link
    # must stay listable/revocable by its owner even after the underlying
    # submission is soft-deleted (see services.get_public_roast_payload's
    # docstring for the contrast with the public-facing selector below).
    return ShareLink.objects.filter(owner=owner).order_by("-created_at")


def get_owned_share_link_or_404(*, owner: User, share_link_id: UUID) -> ShareLink:
    return get_object_or_404(get_owned_share_links(owner=owner), pk=share_link_id)


def get_active_share_link_by_token(*, token: str) -> ShareLink:
    """
    The single 404 gate used by both the public GET and the public
    reaction POST — a token that never existed, one that was revoked,
    and one whose roast's submission was later soft-deleted all resolve
    identically to Http404 here, so none of those cases is ever
    distinguishable from the outside.
    """
    qs = (
        ShareLink.objects.select_related("roast", "roast__submission")
        .prefetch_related("roast__sections", "roast__findings")
        .filter(token=token, revoked_at__isnull=True, roast__submission__deleted_at__isnull=True)
    )
    return get_object_or_404(qs)

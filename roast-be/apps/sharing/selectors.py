from uuid import UUID

from django.db.models import QuerySet, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from apps.roasts.models import RoastRun, RoastStatus
from apps.roasts.selectors import get_owned_roast_runs
from apps.submissions.models import SubmissionVisibility

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


def get_wall_of_fame_roasts(*, ordering: str = "top") -> QuerySet:
    """
    Public, opt-in gallery feed: active share links for completed roasts
    whose owner has explicitly set the underlying Submission's
    `visibility` to PUBLIC — see that field's docstring
    (apps.submissions.models.Submission), which anticipates exactly this
    "future public share surface". Never auto-lists on popularity alone.

    `ordering="new"` sorts by recency; anything else (default "top")
    ranks by total reaction count, tiebroken by view_count then recency.
    """
    qs = (
        ShareLink.objects.filter(
            revoked_at__isnull=True,
            roast__status=RoastStatus.COMPLETED,
            roast__submission__visibility=SubmissionVisibility.PUBLIC,
            roast__submission__deleted_at__isnull=True,
        )
        .select_related("roast", "roast__submission")
        .annotate(total_reactions=Coalesce(Sum("reactions__count"), 0))
    )
    if ordering == "new":
        return qs.order_by("-created_at")
    return qs.order_by("-total_reactions", "-view_count", "-created_at")

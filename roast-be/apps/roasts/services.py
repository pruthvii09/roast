import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import Throttled

from apps.accounts.models import User
from apps.referrals.selectors import get_active_referral_bonus
from apps.submissions.models import Submission, SubmissionStatus

from .exceptions import SubmissionNotRoastableError
from .models import IN_FLIGHT_STATUSES, RoastRun, RoastStatus

logger = logging.getLogger(__name__)

# Submissions in these statuses cannot be (re-)roasted, regardless of type.
NOT_ROASTABLE_STATUSES = [SubmissionStatus.DELETED, SubmissionStatus.FAILED]


def _validate_submission_is_roastable(submission: Submission) -> None:
    if submission.status in NOT_ROASTABLE_STATUSES:
        raise SubmissionNotRoastableError(
            f"Submission status {submission.status!r} cannot be roasted."
        )
    # Every submission type now goes through apps.extraction's async
    # pipeline (queued at creation time) before there's any extracted
    # text to roast — `draft`/`processing` means that hasn't finished
    # yet, so reject rather than roasting an empty/absent document.
    if submission.status != SubmissionStatus.READY:
        raise SubmissionNotRoastableError(
            f"Submission is not ready for roasting yet (status={submission.status!r})."
        )


@dataclass
class RoastQuotaStatus:
    limit: int
    used: int
    remaining: int
    resets_at: datetime | None  # None means nothing is currently in-window
    bonus_amount: int
    bonus_expires_at: datetime | None


def _quota_window_start() -> datetime:
    return timezone.now() - timedelta(days=settings.ROAST_QUOTA_WINDOW_DAYS)


def _effective_weekly_limit(*, owner: User) -> tuple[int, int, datetime | None]:
    """
    Returns (limit, bonus_amount, bonus_expires_at). Used by BOTH
    get_roast_quota_status (display) and _enforce_weekly_quota
    (enforcement) — they must never compute this independently, or the
    quota a client sees could diverge from what's actually allowed.
    """
    bonus = get_active_referral_bonus(user=owner)
    bonus_amount = bonus.amount if bonus else 0
    bonus_expires_at = bonus.expires_at if bonus else None
    return settings.ROAST_WEEKLY_QUOTA + bonus_amount, bonus_amount, bonus_expires_at


def get_roast_quota_status(*, owner: User) -> RoastQuotaStatus:
    """
    Read-only view of the same window/count logic _enforce_weekly_quota
    uses, for the GET /roasts/quota/ endpoint — deliberately NOT locking
    the owner row (nothing is being created), so this is safe to call as
    often as a client likes without contending with in-flight creates.
    """
    in_window = RoastRun.objects.filter(owner=owner, created_at__gte=_quota_window_start())
    used = in_window.count()
    oldest = in_window.order_by("created_at").first()
    resets_at = (
        oldest.created_at + timedelta(days=settings.ROAST_QUOTA_WINDOW_DAYS) if oldest else None
    )
    limit, bonus_amount, bonus_expires_at = _effective_weekly_limit(owner=owner)
    return RoastQuotaStatus(
        limit=limit,
        used=used,
        remaining=max(0, limit - used),
        resets_at=resets_at,
        bonus_amount=bonus_amount,
        bonus_expires_at=bonus_expires_at,
    )


def _enforce_weekly_quota(*, locked_owner: User) -> None:
    """
    Must be called with `locked_owner` already select_for_update()'d
    inside the caller's transaction — see create_roast_run. Locking the
    owner's User row (not a global lock) serializes concurrent
    roast-creation requests from that SAME user only; different users
    never contend with each other. Without this lock, N simultaneous
    requests from one user could all read "under quota" and all proceed,
    since a plain COUNT has no way to block a concurrent INSERT.

    Counts every roast-creation attempt in the window, including ones
    that later failed — a deliberate choice (not just successful roasts)
    so the limit can't be dodged by triggering cheap failures, and
    because a failed attempt still consumed a real AI provider call in
    most failure modes.
    """
    window_start = _quota_window_start()
    in_window = RoastRun.objects.filter(owner=locked_owner, created_at__gte=window_start)
    used = in_window.count()
    limit, _, _ = _effective_weekly_limit(owner=locked_owner)
    if used < limit:
        return

    oldest = in_window.order_by("created_at").first()
    resets_at = oldest.created_at + timedelta(days=settings.ROAST_QUOTA_WINDOW_DAYS)
    wait_seconds = max(0.0, (resets_at - timezone.now()).total_seconds())
    raise Throttled(
        wait=wait_seconds,
        detail=(
            f"Weekly roast limit reached ({limit} per "
            f"{settings.ROAST_QUOTA_WINDOW_DAYS} days). Try again later."
        ),
    )


def create_roast_run(
    *, submission: Submission, language: str, intensity: str
) -> tuple[RoastRun, bool]:
    """
    Validates the submission is roastable and the owner is within their
    weekly roast quota, then creates a queued RoastRun and dispatches
    asynchronous processing — never calls an AI provider directly (that
    only happens inside the Celery task).

    Idempotent where practical: (submission, language, intensity) has a
    partial unique DB constraint covering queued/processing rows (see
    RoastRun.Meta.constraints), so a duplicate request racing an
    in-flight identical run hits an IntegrityError here, which we catch
    and resolve by returning the existing in-flight run instead —
    enforced atomically by Postgres, not just an application-level
    check-then-create that could race. Returns (roast_run, created) —
    created=False when an existing in-flight run was returned instead.

    A request for the same (submission, language, intensity) after a
    prior run has already completed/failed is NOT deduplicated — that's
    a legitimate "roast me again" request, not an accidental duplicate
    (still subject to the weekly quota like any other create).
    """
    _validate_submission_is_roastable(submission)

    try:
        with transaction.atomic():
            # Locked first, before the quota count, so concurrent
            # requests from this user serialize here rather than racing
            # each other past the check — see _enforce_weekly_quota.
            locked_owner = User.objects.select_for_update().get(id=submission.owner_id)
            _enforce_weekly_quota(locked_owner=locked_owner)
            roast_run = RoastRun.objects.create(
                submission=submission,
                owner=locked_owner,
                language=language,
                intensity=intensity,
                status=RoastStatus.QUEUED,
                engine_version=settings.ROAST_ENGINE_VERSION,
            )
    except IntegrityError:
        existing = (
            RoastRun.objects.filter(
                submission=submission,
                language=language,
                intensity=intensity,
                status__in=IN_FLIGHT_STATUSES,
            )
            .order_by("-created_at")
            .first()
        )
        if existing is None:
            raise  # constraint violated for some other reason — don't swallow it
        return existing, False

    transaction.on_commit(lambda: _dispatch_roast_processing(roast_run.id))
    return roast_run, True


def _dispatch_roast_processing(roast_run_id) -> None:
    """
    Runs after the RoastRun row has committed. If the broker is
    unreachable (or dispatch fails for any other reason), the row must
    not be left stuck `queued` forever — that would both mislead the
    client (a 500 for what was actually a successful create) and
    permanently block the idempotency guard for this
    submission/language/intensity, since a `queued` row with no task
    behind it looks exactly like a legitimately in-flight one. Marking
    it `failed` here keeps status honest and lets the client retry.
    """
    from .tasks import process_roast_run  # local import: tasks.py imports this module

    try:
        # retry=False: fail fast on a broker outage rather than blocking
        # this request for Celery's default multi-second publish-retry
        # policy — better to mark the run failed quickly than hang the
        # HTTP response waiting on infra that may not come back soon.
        process_roast_run.apply_async(args=[str(roast_run_id)], retry=False)
    except Exception:
        logger.exception("Failed to dispatch roast processing for %s", roast_run_id)
        mark_roast_run_failed(
            roast_run_id=roast_run_id,
            error_message="Failed to dispatch background processing. Please try again.",
        )


def mark_roast_run_failed(*, roast_run_id: str, error_message: str) -> None:
    RoastRun.objects.filter(id=roast_run_id).update(
        status=RoastStatus.FAILED,
        error_message=error_message,
        completed_at=timezone.now(),
    )


def delete_roast_run(*, roast_run: RoastRun, requesting_user: User) -> None:
    if roast_run.owner_id != requesting_user.id:
        raise PermissionDenied("You do not have permission to delete this roast run.")
    roast_run.delete()

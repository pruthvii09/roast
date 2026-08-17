import logging
from datetime import timedelta

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.utils import timezone

from .models import IN_FLIGHT_STATUSES, RoastRun, RoastStatus
from .services import mark_roast_run_failed

logger = logging.getLogger(__name__)


@shared_task(
    name="apps.roasts.process_roast_run",
    soft_time_limit=settings.ROAST_TASK_SOFT_TIME_LIMIT_SECONDS,
    time_limit=settings.ROAST_TASK_TIME_LIMIT_SECONDS,
)
def process_roast_run(roast_run_id: str) -> None:
    """
    Idempotent: atomically claims the run by flipping queued -> processing
    via a conditional UPDATE that only affects a row still `queued`. If
    zero rows are affected, another worker already claimed it (or it was
    deleted, or already processed) — Celery's at-least-once delivery
    means this task can run more than once for the same id, and this
    guard is what makes a re-run a safe no-op instead of double
    processing.

    Stays a thin claim-and-dispatch wrapper: the actual load-submission /
    build-prompt / call-provider / validate / persist pipeline lives in
    apps.ai.services.roasting.process_roast, which never talks to an AI
    provider except through the provider-agnostic apps.ai.providers
    interface (never a vendor SDK directly) — and never from a view.

    soft_time_limit/time_limit bound how long a single run may take —
    protection against the task hanging for any reason the in-process AI
    retry/backoff logic doesn't already bound. A row that gets stuck here
    anyway (e.g. the worker itself is killed) is caught later by
    reconcile_stuck_roast_runs below, not by this task retrying itself —
    see the CELERY_TASK_ACKS_LATE comment in config/settings/base.py for
    why a Celery-level self.retry() here would silently no-op instead of
    actually retrying (the claim above would find 0 rows once already
    `processing`).
    """
    claimed = RoastRun.objects.filter(id=roast_run_id, status=RoastStatus.QUEUED).update(
        status=RoastStatus.PROCESSING, started_at=timezone.now()
    )
    if not claimed:
        logger.info("Roast run %s already claimed/processed/missing; skipping.", roast_run_id)
        return

    try:
        roast_run = RoastRun.objects.select_related("submission").get(id=roast_run_id)
    except RoastRun.DoesNotExist:
        logger.info("Roast run %s deleted before processing could start.", roast_run_id)
        return

    from apps.ai.services.roasting import process_roast  # avoids an app-loading-order cycle

    try:
        process_roast(roast_run)
    except SoftTimeLimitExceeded:
        logger.warning("Roast run %s exceeded its time limit.", roast_run_id)
        mark_roast_run_failed(
            roast_run_id=roast_run_id,
            error_message="Roast generation timed out before it could complete.",
        )
    except Exception:
        # process_roast already handles every expected failure mode
        # internally (marks the run failed with a specific message) —
        # this is a last-resort net for anything truly unexpected.
        logger.exception("Unexpected error processing roast run %s", roast_run_id)
        mark_roast_run_failed(
            roast_run_id=roast_run_id,
            error_message="An unexpected error occurred while generating this roast.",
        )


@shared_task(name="apps.roasts.reconcile_stuck_roast_runs")
def reconcile_stuck_roast_runs() -> None:
    """
    Beat-scheduled sweep (config/settings/base.py: CELERY_BEAT_SCHEDULE).
    The claim-and-process pattern above intentionally cannot recover a
    run whose task died after claiming it (see process_roast_run's
    docstring) — this is the actual backstop: any run still
    queued/processing with no update in ROAST_STUCK_THRESHOLD_MINUTES is
    almost certainly abandoned (a legitimately in-flight run updates
    `updated_at` well before that, bounded by ROAST_TASK_TIME_LIMIT_SECONDS),
    so mark it failed rather than leave it stuck forever.
    """
    threshold = timezone.now() - timedelta(minutes=settings.ROAST_STUCK_THRESHOLD_MINUTES)
    stuck = RoastRun.objects.filter(status__in=IN_FLIGHT_STATUSES, updated_at__lt=threshold)
    for roast_run_id in list(stuck.values_list("id", flat=True)):
        mark_roast_run_failed(
            roast_run_id=roast_run_id,
            error_message="Processing was interrupted and did not complete in time.",
        )
        logger.warning("Reconciled stuck roast run %s (marked failed).", roast_run_id)

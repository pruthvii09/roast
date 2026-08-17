import logging
from datetime import timedelta

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.utils import timezone

from .models import IN_FLIGHT_STATUSES, ExtractionStatus, ExtractionTask
from .services import mark_extraction_failed, process_extraction

logger = logging.getLogger(__name__)


@shared_task(
    name="apps.extraction.extract_submission",
    soft_time_limit=settings.EXTRACTION_TASK_SOFT_TIME_LIMIT_SECONDS,
    time_limit=settings.EXTRACTION_TASK_TIME_LIMIT_SECONDS,
)
def extract_submission_task(extraction_task_id: str) -> None:
    """
    Idempotent, same pattern as apps.roasts.tasks.process_roast_run:
    atomically claims the task by flipping queued -> processing via a
    conditional UPDATE that only affects a row still `queued`. Zero rows
    affected means another worker already claimed it (or it was deleted,
    or already processed) — Celery's at-least-once delivery means this
    task can run more than once for the same id, and this guard is what
    makes a re-run a safe no-op.

    soft_time_limit/time_limit bound how long a single extraction may
    run — protection against a pathological file hanging a worker
    indefinitely. SoftTimeLimitExceeded is caught here and recorded as a
    normal (if distinctly-worded) extraction failure, not an unhandled
    worker crash.
    """
    claimed = ExtractionTask.objects.filter(
        id=extraction_task_id, status=ExtractionStatus.QUEUED
    ).update(status=ExtractionStatus.PROCESSING, started_at=timezone.now())
    if not claimed:
        logger.info(
            "Extraction task %s already claimed/processed/missing; skipping.", extraction_task_id
        )
        return

    try:
        extraction_task = ExtractionTask.objects.select_related("submission").get(
            id=extraction_task_id
        )
    except ExtractionTask.DoesNotExist:
        logger.info("Extraction task %s deleted before processing could start.", extraction_task_id)
        return

    try:
        process_extraction(extraction_task)
    except SoftTimeLimitExceeded:
        logger.warning("Extraction task %s exceeded its time limit.", extraction_task_id)
        mark_extraction_failed(
            extraction_task_id=extraction_task_id,
            error_message="Extraction timed out before it could complete.",
        )
    except Exception:
        # process_extraction already handles every expected failure mode
        # internally (marks the task+submission failed with a specific
        # message) — this is a last-resort net for anything truly
        # unexpected, mirroring apps.roasts.tasks.process_roast_run.
        logger.exception("Unexpected error during extraction for task %s", extraction_task_id)
        mark_extraction_failed(
            extraction_task_id=extraction_task_id,
            error_message="An unexpected error occurred while processing this document.",
        )


@shared_task(name="apps.extraction.reconcile_stuck_extraction_tasks")
def reconcile_stuck_extraction_tasks() -> None:
    """
    Beat-scheduled sweep (config/settings/base.py: CELERY_BEAT_SCHEDULE) —
    the extraction-pipeline counterpart of
    apps.roasts.tasks.reconcile_stuck_roast_runs; see that task's
    docstring for why the claim pattern can't self-recover from a task
    that died after claiming its row. Any ExtractionTask still
    queued/processing with no update in
    EXTRACTION_STUCK_THRESHOLD_MINUTES is treated as abandoned.
    """
    threshold = timezone.now() - timedelta(minutes=settings.EXTRACTION_STUCK_THRESHOLD_MINUTES)
    stuck = ExtractionTask.objects.filter(status__in=IN_FLIGHT_STATUSES, updated_at__lt=threshold)
    for extraction_task_id in list(stuck.values_list("id", flat=True)):
        mark_extraction_failed(
            extraction_task_id=extraction_task_id,
            error_message="Processing was interrupted and did not complete in time.",
        )
        logger.warning("Reconciled stuck extraction task %s (marked failed).", extraction_task_id)

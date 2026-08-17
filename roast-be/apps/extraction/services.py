import logging

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.submissions.models import SubmissionStatus

from .exceptions import ExtractionError
from .models import ExtractionStatus, ExtractionTask
from .processors import get_processor

logger = logging.getLogger(__name__)

# Policy: extraction never logs submission.extracted_text, raw file
# bytes, or filenames — only submission/task ids, status, and exception
# *class* (error messages stored on the model may include a parser's own
# diagnostic string, e.g. "EOF marker not found", which is safe; they
# never include document content).


def queue_extraction(*, submission, asset=None) -> ExtractionTask:
    """
    Creates the queued ExtractionTask row. The caller
    (apps.submissions.services.create_submission, for every submission
    type) must call this from inside the same transaction.atomic() block
    that creates the Submission (+ SubmissionAsset, for resumes), then
    dispatch via dispatch_extraction_processing() after that transaction
    commits — mirrors apps.roasts.services.create_roast_run's
    create-then-on_commit-dispatch split.
    """
    return ExtractionTask.objects.create(submission=submission, asset=asset)


def dispatch_extraction_processing(extraction_task_id) -> None:
    """
    Runs after the ExtractionTask row has committed. If the broker is
    unreachable, the row must not be left stuck `queued` forever (that
    would leave the owning Submission stuck `processing` forever too,
    with no task ever going to claim it) — mark it failed immediately so
    the client sees a clear state instead of silence.
    """
    from .tasks import extract_submission_task  # local import: tasks.py imports this module

    try:
        # retry=False: fail fast on a broker outage rather than blocking
        # the request for Celery's default publish-retry backoff — see
        # apps.roasts.services._dispatch_roast_processing for the same
        # reasoning.
        extract_submission_task.apply_async(args=[str(extraction_task_id)], retry=False)
    except Exception:
        logger.exception("Failed to dispatch extraction processing for task %s", extraction_task_id)
        mark_extraction_failed(
            extraction_task_id=extraction_task_id,
            error_message="Failed to dispatch background processing. Please try again.",
        )


def _validate_extracted_text(text: str) -> str:
    """
    Explicit validation stage, kept separate from any single processor's
    own checks: the uniform place every processor's output passes
    through before being trusted, regardless of what that processor
    already validated internally.
    """
    if not text or not text.strip():
        raise ExtractionError("Extraction produced no usable text content.")
    return text


def process_extraction(extraction_task: ExtractionTask) -> None:
    """
    The core pipeline for one ExtractionTask: resolve the right
    processor (apps.extraction.processors.get_processor, keyed by
    submission_type) -> process -> validate -> store. On success,
    atomically marks the ExtractionTask completed and the Submission
    ready. On any ExtractionError — corrupt/unsupported file, invalid or
    unsafe URL, remote fetch failure, empty result — atomically marks
    both failed with a clear message. Never partially updates: the
    Submission only ever reaches `ready` alongside a populated
    `extracted_text`.
    """
    submission = extraction_task.submission

    try:
        asset = extraction_task.asset
        if asset is not None and asset.size_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
            # Defense-in-depth: the primary size gate is upload-time
            # validate_file_size(); this guards against a future
            # direct-to-storage upload path bypassing that check.
            raise ExtractionError("Asset exceeds the maximum allowed size for extraction.")

        processor = get_processor(submission)
        result = processor.process(submission)
        text = _validate_extracted_text(result.text)
    except ExtractionError as exc:
        _mark_task_and_submission_failed(
            extraction_task=extraction_task, submission=submission, error_message=str(exc)
        )
        return

    with transaction.atomic():
        submission.extracted_text = text
        submission.metadata = result.metadata
        submission.status = SubmissionStatus.READY
        submission.error_message = ""
        submission.save(
            update_fields=["extracted_text", "metadata", "status", "error_message", "updated_at"]
        )

        extraction_task.status = ExtractionStatus.COMPLETED
        extraction_task.processor_name = processor.processor_name
        extraction_task.char_count = len(text)
        extraction_task.completed_at = timezone.now()
        extraction_task.save(
            update_fields=["status", "processor_name", "char_count", "completed_at", "updated_at"]
        )


def _mark_task_and_submission_failed(*, extraction_task, submission, error_message: str) -> None:
    with transaction.atomic():
        extraction_task.status = ExtractionStatus.FAILED
        extraction_task.error_message = error_message
        extraction_task.completed_at = timezone.now()
        extraction_task.save(
            update_fields=["status", "error_message", "completed_at", "updated_at"]
        )

        submission.status = SubmissionStatus.FAILED
        submission.error_message = error_message
        submission.save(update_fields=["status", "error_message", "updated_at"])


def mark_extraction_failed(*, extraction_task_id, error_message: str) -> None:
    """
    Used by apps.extraction.tasks when the failure happens outside
    process_extraction's own try/except (dispatch failure, task timeout,
    or a truly unexpected error) — looks the task up fresh rather than
    assuming a live instance is available.
    """
    try:
        extraction_task = ExtractionTask.objects.select_related("submission").get(
            id=extraction_task_id
        )
    except ExtractionTask.DoesNotExist:
        logger.info("Extraction task %s no longer exists; cannot mark failed.", extraction_task_id)
        return

    _mark_task_and_submission_failed(
        extraction_task=extraction_task,
        submission=extraction_task.submission,
        error_message=error_message,
    )

from django.db import models

from apps.common.models import TimeStampedUUIDModel


class ExtractionStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


IN_FLIGHT_STATUSES = [ExtractionStatus.QUEUED, ExtractionStatus.PROCESSING]


class ExtractionTask(TimeStampedUUIDModel):
    """
    One attempt at turning a Submission's source material (a resume's
    SubmissionAsset, or a website/GitHub source_url) into plain text.
    Mirrors RoastRun's claim-and-process shape (see
    apps.roasts.tasks.process_roast_run): created `queued`, atomically
    claimed to `processing` by the Celery task, and terminates at
    `completed`/`failed`.

    This is the audit/task-tracking row — `Submission.status` and
    `Submission.error_message` are the aggregate outcome most API
    consumers actually read (see apps.extraction.services.process_extraction,
    which updates both together). `char_count` is recorded purely for
    observability; the extracted text itself is never stored here, only
    on the Submission. `processor_name` records which
    apps.extraction.processors.SubmissionProcessor subclass handled this
    task (e.g. "resume", "website", "github").

    `asset` is nullable (SET_NULL) rather than CASCADE: SubmissionAsset
    rows are hard-deleted independently of their Submission (see
    apps.submissions.services.delete_submission), and this task row
    should remain as a historical record of what was attempted even if
    the asset it read has since been purged. It is also nullable
    because website/GitHub extraction tasks have no asset at all.
    """

    submission = models.ForeignKey(
        "submissions.Submission", on_delete=models.CASCADE, related_name="extraction_tasks"
    )
    asset = models.ForeignKey(
        "submissions.SubmissionAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="extraction_tasks",
    )
    status = models.CharField(
        max_length=20, choices=ExtractionStatus.choices, default=ExtractionStatus.QUEUED
    )
    processor_name = models.CharField(max_length=50, blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")
    char_count = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "extraction_extractiontask"
        indexes = [
            models.Index(fields=["submission", "created_at"], name="extract_sub_created_idx"),
            models.Index(fields=["submission", "status"], name="extract_sub_status_idx"),
            # Supports the Beat reconciliation sweep
            # (apps.extraction.tasks.reconcile_stuck_extraction_tasks),
            # which finds queued/processing rows stale past a threshold.
            models.Index(fields=["status", "updated_at"], name="extract_status_updated_idx"),
        ]

    def __str__(self):
        return f"ExtractionTask({self.submission_id}, {self.status})"

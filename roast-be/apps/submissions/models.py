from django.db import models

from apps.common.models import SoftDeleteModel, TimeStampedUUIDModel


class SubmissionType(models.TextChoices):
    RESUME = "resume", "Resume"
    WEBSITE = "website", "Website"
    GITHUB = "github", "GitHub Profile"
    # Future: LINKEDIN, COVER_LETTER, OTHER. Adding a new choice here is a
    # Python-level change only (this is a plain CharField) — no migration
    # needed for the column itself. Do NOT add a DB CheckConstraint that
    # enumerates these values, or every new type would need a migration.


class SubmissionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PROCESSING = "processing", "Processing"
    READY = "ready", "Ready"
    FAILED = "failed", "Failed"
    DELETED = "deleted", "Deleted"


class SubmissionVisibility(models.TextChoices):
    PRIVATE = "private", "Private"
    LINK = "link", "Link"
    PUBLIC = "public", "Public"


URL_REQUIRED_TYPES = [SubmissionType.WEBSITE, SubmissionType.GITHUB]


class Submission(TimeStampedUUIDModel, SoftDeleteModel):
    """
    The source material a user submitted (resume file, website URL, or
    GitHub URL). Never stores language/intensity/roast output — those
    belong to a RoastRun (a later phase), since one Submission can be
    roasted multiple times with different settings.

    Soft-deleted (not hard-deleted): this is a lightweight metadata row
    that future RoastRun/ShareLink/Feedback rows will reference, so
    keeping it around (invisible to the owner) preserves referential
    integrity for roast history. See SubmissionAsset for why the
    *sensitive* file content is handled differently.

    `status` models the source-material processing lifecycle
    (draft -> processing -> ready/failed, or deleted). Every submission
    is created in `processing`. For every submission type,
    apps.extraction's async pipeline (queued right after creation — see
    apps.submissions.services.create_submission, routed by
    apps.extraction.processors.get_processor) populates `extracted_text`
    (and `metadata`, for processors that produce structured extras) and
    transitions the submission to `ready`, or to `failed` with
    `error_message` set (see apps.extraction.services). `deleted` is set
    alongside `deleted_at` when a submission is deleted, rather than
    being a status a user can set directly.

    `visibility` is separate from `status`: it records whether a future
    public/link-based share surface (the sharing app) may expose this
    submission's *roast output* — it does not by itself grant access to
    these owner-scoped CRUD endpoints, which always require ownership
    regardless of visibility. See services.create_submission /
    views.SubmissionViewSet for where that's enforced.
    """

    owner = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="submissions")
    submission_type = models.CharField(max_length=20, choices=SubmissionType.choices)
    title = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20, choices=SubmissionStatus.choices, default=SubmissionStatus.PROCESSING
    )
    visibility = models.CharField(
        max_length=20, choices=SubmissionVisibility.choices, default=SubmissionVisibility.PRIVATE
    )
    source_url = models.URLField(max_length=2048, null=True, blank=True)
    extracted_text = models.TextField(blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "submissions_submission"
        indexes = [
            models.Index(fields=["owner", "created_at"], name="sub_owner_created_idx"),
            models.Index(fields=["owner", "submission_type"], name="sub_owner_type_idx"),
            models.Index(fields=["owner", "status"], name="sub_owner_status_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                name="source_url_required_for_url_types",
                condition=(
                    ~models.Q(submission_type__in=URL_REQUIRED_TYPES)
                    | models.Q(source_url__isnull=False)
                ),
            ),
        ]

    def __str__(self):
        return f"{self.submission_type}:{self.id}"


class SubmissionAsset(TimeStampedUUIDModel):
    """
    Points at the sensitive file bytes for a resume submission. Hard
    deleted, immediately, and only after its backing bytes are purged
    from storage (see services.delete_submission) — this row exists
    solely to reference private file content, so there is no reason to
    keep a pointer around once that content is gone.
    """

    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="assets")
    storage_key = models.CharField(max_length=512, unique=True)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=127)
    size_bytes = models.PositiveBigIntegerField()
    checksum = models.CharField(max_length=64)

    class Meta:
        db_table = "submissions_submissionasset"
        indexes = [
            models.Index(fields=["submission"], name="asset_submission_idx"),
        ]

    def __str__(self):
        return f"{self.original_filename} ({self.submission_id})"

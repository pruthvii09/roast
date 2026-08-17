from django.db import models

from apps.common.models import TimeStampedUUIDModel


class RoastLanguage(models.TextChoices):
    EN = "en", "English"
    HI = "hi", "Hindi"
    HINGLISH = "hinglish", "Hinglish"


class RoastIntensity(models.TextChoices):
    GENTLE = "gentle", "Gentle"
    SARCASTIC = "sarcastic", "Sarcastic"
    BRUTAL = "brutal", "Brutal"
    NUCLEAR = "nuclear", "Nuclear"


class RoastStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


IN_FLIGHT_STATUSES = [RoastStatus.QUEUED, RoastStatus.PROCESSING]


class RoastSeverity(models.TextChoices):
    INFO = "info", "Info"
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class RoastRun(TimeStampedUUIDModel):
    """
    One AI roast execution against a Submission. A Submission may have
    many RoastRuns (e.g. re-roasted later with a different
    language/intensity) — this row never mutates the Submission's own
    source material, it only records one attempt at roasting it.

    No soft delete: DELETE hard-deletes the row (and cascades to its
    RoastSections/RoastFindings), unlike Submission. Nothing references
    a RoastRun as a parent yet in a way that would need the row to
    survive deletion, so there's no reason for a tombstone here.

    Idempotency: the (submission, language, intensity) + in-flight-status
    partial unique constraint below means a duplicate create request
    while an identical run is still queued/processing returns the
    existing run instead of racing to create a second one — see
    services.create_roast_run. Concurrent-safe (enforced by Postgres),
    not just an application-level check.

    `owner` is a denormalized copy of `submission.owner`, set once at
    creation and never changed — it exists purely so a per-user query
    (e.g. "how many roasts has this user requested in the last 7 days?",
    see services.create_roast_run's weekly quota check) doesn't need a
    join through Submission with no supporting index. `on_delete=CASCADE`
    here is redundant with the CASCADE already reached via
    `submission.owner` (deleting a user already cascades through their
    submissions to their roast runs) — kept for consistency/directness,
    not because it does anything the other cascade path wouldn't.
    """

    submission = models.ForeignKey(
        "submissions.Submission", on_delete=models.CASCADE, related_name="roast_runs"
    )
    owner = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="roast_runs")
    language = models.CharField(max_length=20, choices=RoastLanguage.choices)
    intensity = models.CharField(max_length=20, choices=RoastIntensity.choices)
    status = models.CharField(
        max_length=20, choices=RoastStatus.choices, default=RoastStatus.QUEUED
    )
    engine_version = models.CharField(max_length=50)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default="")

    # Populated from the AI's validated structured response on success
    # (see apps.ai.services.roasting) — blank/null until then.
    summary = models.TextField(blank=True, default="")
    final_verdict = models.TextField(blank=True, default="")
    score = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = "roasts_roastrun"
        indexes = [
            models.Index(fields=["submission", "created_at"], name="roast_sub_created_idx"),
            models.Index(fields=["submission", "status"], name="roast_sub_status_idx"),
            models.Index(fields=["owner", "created_at"], name="roast_owner_created_idx"),
            models.Index(fields=["status", "updated_at"], name="roast_status_updated_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "language", "intensity"],
                condition=models.Q(status__in=IN_FLIGHT_STATUSES),
                name="unique_inflight_roast_per_submission_lang_intensity",
            ),
            models.CheckConstraint(
                name="roastrun_score_within_range",
                condition=models.Q(score__isnull=True) | models.Q(score__gte=0, score__lte=100),
            ),
        ]

    def __str__(self):
        return f"RoastRun({self.submission_id}, {self.language}, {self.intensity}, {self.status})"


class RoastSection(TimeStampedUUIDModel):
    """A titled block of the roast output (e.g. "summary", "strengths")."""

    roast = models.ForeignKey(RoastRun, on_delete=models.CASCADE, related_name="sections")
    key = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    content = models.TextField()
    position = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "roasts_roastsection"
        indexes = [
            models.Index(fields=["roast", "position"], name="section_roast_position_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["roast", "key"], name="unique_section_key_per_roast"),
        ]
        ordering = ["position"]

    def __str__(self):
        return f"{self.key} ({self.roast_id})"


class RoastFinding(TimeStampedUUIDModel):
    """
    One individual, orderable finding within a roast: a specific
    roast-worthy observation plus the constructive feedback behind it.

    `roast_text` (not `roast`) holds the sarcastic zinger text itself —
    named to avoid colliding with the `roast` FK to RoastRun on this
    same model.
    """

    roast = models.ForeignKey(RoastRun, on_delete=models.CASCADE, related_name="findings")
    category = models.CharField(max_length=50)
    severity = models.CharField(max_length=20, choices=RoastSeverity.choices)
    title = models.CharField(max_length=255)
    roast_text = models.TextField()
    actual_feedback = models.TextField()
    position = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "roasts_roastfinding"
        indexes = [
            models.Index(fields=["roast", "position"], name="finding_roast_position_idx"),
            models.Index(fields=["roast", "severity"], name="finding_roast_severity_idx"),
        ]
        ordering = ["position"]

    def __str__(self):
        return f"{self.category}:{self.severity} ({self.roast_id})"

from django.db import models

from apps.common.models import TimeStampedUUIDModel
from apps.roasts.models import RoastLanguage


class PromptVersion(TimeStampedUUIDModel):
    """
    A versioned system prompt template for a given (name, language). Only
    one version per (name, language) may be `is_active` at a time — the
    partial unique constraint below enforces that atomically, so
    activating a new version requires explicitly deactivating the old one
    rather than risking two "active" versions racing.

    Intensity is NOT modeled here — per spec, it's a separate runtime
    prompt variable substituted into `system_prompt` at generation time
    (see apps.ai.prompts.renderer), not a distinct PromptVersion row.
    """

    name = models.CharField(max_length=100)
    language = models.CharField(max_length=20, choices=RoastLanguage.choices)
    version = models.CharField(max_length=20)
    system_prompt = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "ai_promptversion"
        indexes = [
            models.Index(fields=["name", "language", "is_active"], name="prompt_name_lang_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "language", "version"], name="unique_prompt_name_lang_version"
            ),
            models.UniqueConstraint(
                fields=["name", "language"],
                condition=models.Q(is_active=True),
                name="unique_active_prompt_per_name_language",
            ),
        ]

    def __str__(self):
        return f"{self.name}:{self.language}:{self.version}"


class AIRequest(TimeStampedUUIDModel):
    """
    Audit record of one actual call to an AI provider — one row per
    attempt, including failed/retried attempts, so the full retry
    history for a RoastRun is reconstructable. Never stores prompt text
    or the raw AI response body: only metadata (provider, model, token
    counts, latency, cost, success/error). See services.roasting for
    where these are created.
    """

    roast = models.ForeignKey(
        "roasts.RoastRun", on_delete=models.CASCADE, related_name="ai_requests"
    )
    provider = models.CharField(max_length=50)
    model = models.CharField(max_length=100)
    prompt_version = models.ForeignKey(
        PromptVersion, on_delete=models.PROTECT, related_name="ai_requests"
    )
    input_tokens = models.PositiveIntegerField(null=True, blank=True)
    output_tokens = models.PositiveIntegerField(null=True, blank=True)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    success = models.BooleanField(default=False)
    error = models.TextField(blank=True, default="")

    class Meta:
        db_table = "ai_airequest"
        indexes = [
            models.Index(fields=["roast", "created_at"], name="airequest_roast_created_idx"),
        ]

    def __str__(self):
        outcome = "ok" if self.success else "failed"
        return f"AIRequest({self.roast_id}, {self.provider}/{self.model}, {outcome})"

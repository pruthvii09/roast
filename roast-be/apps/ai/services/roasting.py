import logging
import time

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from pydantic import ValidationError

from apps.roasts.models import RoastFinding, RoastRun, RoastSection, RoastStatus
from apps.roasts.services import mark_roast_run_failed

from ..exceptions import (
    AIGenerationFailedError,
    AIProviderError,
    PromptVersionNotConfiguredError,
    SubmissionExtractionError,
)
from ..models import AIRequest, PromptVersion
from ..prompts.renderer import render_system_prompt, render_user_prompt
from ..prompts.schema import RoastResponseSchema
from ..prompts.templates import PROMPT_NAME_ROAST_GENERATION
from ..providers import get_ai_provider
from .extraction import ensure_extracted_text

logger = logging.getLogger(__name__)

_ERROR_MESSAGE_MAX_LENGTH = 2000


def get_active_prompt_version(*, language: str) -> PromptVersion:
    try:
        return PromptVersion.objects.get(
            name=PROMPT_NAME_ROAST_GENERATION, language=language, is_active=True
        )
    except PromptVersion.DoesNotExist:
        raise PromptVersionNotConfiguredError(
            f"No active prompt version configured for language {language!r}."
        ) from None


def process_roast(roast_run: RoastRun) -> None:
    """
    The full "processing" workflow for a queued RoastRun: load
    submission -> build prompt -> AI provider (bounded, exponential
    retries covering both transient provider failures and
    malformed/invalid structured output) -> validate structured output
    -> save sections/findings -> completed. On any unrecoverable
    failure, marks the run `failed` with a clear message — never
    raises out to the caller, so apps.roasts.tasks.process_roast_run
    stays a thin claim-and-dispatch wrapper.

    Never partially saves: RoastSection/RoastFinding rows are only
    written after the full response has already passed strict schema
    validation, inside one transaction alongside marking the run
    completed (see _persist_validated_roast).
    """
    submission = roast_run.submission

    try:
        prompt_version = get_active_prompt_version(language=roast_run.language)
    except PromptVersionNotConfiguredError as exc:
        mark_roast_run_failed(roast_run_id=roast_run.id, error_message=str(exc))
        return

    try:
        extracted_text = ensure_extracted_text(submission)
    except SubmissionExtractionError as exc:
        mark_roast_run_failed(roast_run_id=roast_run.id, error_message=str(exc))
        return

    system_prompt = render_system_prompt(
        prompt_version=prompt_version,
        intensity=roast_run.intensity,
        submission_type=submission.submission_type,
    )
    user_prompt = render_user_prompt(submission=submission, extracted_text=extracted_text)

    try:
        parsed, generation = _generate_with_retries(
            roast_run=roast_run,
            prompt_version=prompt_version,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
    except AIGenerationFailedError as exc:
        mark_roast_run_failed(roast_run_id=roast_run.id, error_message=str(exc))
        return

    _persist_validated_roast(roast_run=roast_run, parsed=parsed, engine_version=generation.model)


def _generate_with_retries(*, roast_run, prompt_version, system_prompt, user_prompt):
    """
    Up to settings.AI_MAX_ATTEMPTS attempts, exponential backoff between
    them, retrying on BOTH transient provider errors (timeout,
    connection error) and malformed/invalid structured output — a bad
    JSON response is just as retryable as a network blip. Records one
    AIRequest per attempt (success or failure), so the full retry
    history is auditable. Raises AIGenerationFailedError only after
    every attempt is exhausted.

    The raw per-attempt error detail (which, for AIProviderError, embeds
    the vendor SDK's own exception text) is kept in `last_error` for the
    AIRequest audit row (apps.ai — admin-only, never exposed via API)
    and the server-side warning log below — but AIGenerationFailedError
    itself is always raised with a generic, safe message: it's what
    ultimately becomes RoastRun.error_message, which IS exposed via the
    roast detail/status API, and vendor internals (rate-limit account
    details, model/deployment names, etc.) have no business reaching a
    client through it.
    """
    provider = get_ai_provider()
    last_error = "AI generation failed for an unknown reason."

    for attempt in range(1, settings.AI_MAX_ATTEMPTS + 1):
        try:
            generation = provider.generate_roast(
                system_prompt=system_prompt, user_prompt=user_prompt
            )
        except AIProviderError as exc:
            last_error = _truncate(str(exc))
            _record_ai_request(
                roast_run=roast_run,
                provider=provider,
                prompt_version=prompt_version,
                model=provider.model_name,
                generation=None,
                success=False,
                error=last_error,
            )
        else:
            try:
                parsed = RoastResponseSchema.model_validate_json(generation.raw_text)
            except ValidationError as exc:
                last_error = _truncate(f"AI response failed schema validation: {exc}")
                _record_ai_request(
                    roast_run=roast_run,
                    provider=provider,
                    prompt_version=prompt_version,
                    model=generation.model,
                    generation=generation,
                    success=False,
                    error=last_error,
                )
            else:
                _record_ai_request(
                    roast_run=roast_run,
                    provider=provider,
                    prompt_version=prompt_version,
                    model=generation.model,
                    generation=generation,
                    success=True,
                    error="",
                )
                return parsed, generation

        if attempt < settings.AI_MAX_ATTEMPTS:
            delay = settings.AI_RETRY_BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                "Roast generation attempt %s/%s failed for run %s; retrying in %.1fs. detail=%s",
                attempt,
                settings.AI_MAX_ATTEMPTS,
                roast_run.id,
                delay,
                last_error,
            )
            time.sleep(delay)

    logger.error(
        "Roast generation exhausted all %s attempts for run %s. last_detail=%s",
        settings.AI_MAX_ATTEMPTS,
        roast_run.id,
        last_error,
    )
    raise AIGenerationFailedError(
        "AI generation failed after multiple attempts. Please try again later."
    )


def _record_ai_request(
    *, roast_run, provider, prompt_version, model, generation, success, error
) -> None:
    """
    One audit row per actual provider call attempt. Never stores prompt
    text or the raw AI response body — only call metadata — per the
    "never log/store private user content" policy.
    """
    AIRequest.objects.create(
        roast=roast_run,
        provider=provider.provider_name,
        model=model,
        prompt_version=prompt_version,
        input_tokens=generation.input_tokens if generation else None,
        output_tokens=generation.output_tokens if generation else None,
        latency_ms=generation.latency_ms if generation else None,
        cost=generation.cost if generation else None,
        success=success,
        error=error,
    )


def _persist_validated_roast(
    *, roast_run: RoastRun, parsed: RoastResponseSchema, engine_version: str
) -> None:
    with transaction.atomic():
        RoastSection.objects.bulk_create(
            RoastSection(
                roast=roast_run,
                key=section.key,
                title=section.title,
                content=section.content,
                position=index,
            )
            for index, section in enumerate(parsed.sections)
        )
        RoastFinding.objects.bulk_create(
            RoastFinding(
                roast=roast_run,
                category=finding.category,
                severity=finding.severity,
                title=finding.title,
                roast_text=finding.roast_text,
                actual_feedback=finding.actual_feedback,
                position=index,
            )
            for index, finding in enumerate(parsed.findings)
        )
        roast_run.summary = parsed.summary
        roast_run.final_verdict = parsed.final_verdict
        roast_run.score = parsed.score
        roast_run.status = RoastStatus.COMPLETED
        roast_run.completed_at = timezone.now()
        roast_run.engine_version = engine_version
        roast_run.save(
            update_fields=[
                "summary",
                "final_verdict",
                "score",
                "status",
                "completed_at",
                "engine_version",
            ]
        )


def _truncate(message: str, limit: int = _ERROR_MESSAGE_MAX_LENGTH) -> str:
    return message if len(message) <= limit else message[: limit - 3] + "..."

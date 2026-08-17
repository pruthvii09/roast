class AIProviderError(Exception):
    """
    Raised by an AIProvider implementation when roast generation fails
    (vendor API error, connection error, no provider configured yet,
    etc). Callers (apps.ai.services.roasting) catch this and either
    retry (bounded, exponential) or mark the RoastRun `failed` with the
    message, never let it crash the task.
    """


class AIProviderTimeoutError(AIProviderError):
    """The provider call exceeded its configured timeout."""


class PromptVersionNotConfiguredError(Exception):
    """No active PromptVersion exists for the requested (name, language)."""


class AIGenerationFailedError(Exception):
    """Every retry attempt was exhausted without producing a valid roast."""


class SubmissionExtractionError(Exception):
    """Source text could not be extracted from a submission (e.g. corrupt/unsupported file)."""

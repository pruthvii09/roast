from apps.ai.exceptions import AIProviderError

from .base import AIGenerationResult, AIProvider


class NotImplementedAIProvider(AIProvider):
    """
    Default provider when AI_PROVIDER=stub (or unset) — no vendor is
    configured. Always raises AIProviderError — callers must treat that
    as an expected, handled outcome (mark the RoastRun `failed` with a
    clear message), not a bug to fix here. Useful for running the full
    async pipeline in dev/CI without an API key.
    """

    provider_name = "stub"

    @property
    def model_name(self) -> str:
        return "none"

    def generate_roast(
        self, *, system_prompt: str, user_prompt: str, timeout: float | None = None
    ) -> AIGenerationResult:
        raise AIProviderError(
            "No AI provider is configured (AI_PROVIDER=stub) — set AI_PROVIDER=openai "
            "and OPENAI_API_KEY to enable real roast generation."
        )

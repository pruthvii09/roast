import abc
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class AIGenerationResult:
    """
    Raw output of one successful provider call — deliberately generic
    (no roast-domain concepts here at all): just the text the model
    returned plus call metadata. Parsing/validating that text against
    the roast JSON schema is apps.ai.services.roasting's job, not the
    provider's — this is what keeps the provider interface swappable
    without any roast-specific assumptions baked into it.
    """

    raw_text: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    cost: Decimal | None


class AIProvider(abc.ABC):
    """
    Provider-agnostic interface for turning a (system prompt, user
    prompt) pair into raw model output. apps.ai.services.roasting
    depends only on this interface, never on a vendor SDK directly —
    that's the whole point: swapping providers (OpenAI today, something
    else tomorrow) is one new subclass + one new entry in
    apps.ai.providers.get_ai_provider()'s factory map, no changes to the
    roasting service, the Celery task, or anything downstream.
    """

    #: Short machine-readable name recorded on every AIRequest —
    #: overridden by each subclass (e.g. "openai", "stub").
    provider_name: str = "unknown"

    @abc.abstractmethod
    def generate_roast(
        self, *, system_prompt: str, user_prompt: str, timeout: float | None = None
    ) -> AIGenerationResult:
        """
        Returns the raw model output for the given prompts. Raises
        AIProviderTimeoutError on timeout, AIProviderError for any other
        failure (auth, rate limit, connection, vendor 5xx, etc) — never
        lets a vendor-specific exception type escape this method.
        """

    @property
    def model_name(self) -> str:
        """The *configured* model name, even before any call succeeds —
        used to label failed AIRequest rows that never got a response."""
        raise NotImplementedError

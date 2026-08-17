import time
from decimal import Decimal

from django.conf import settings
from openai import APIConnectionError, APIError, APIStatusError, APITimeoutError, OpenAI

from apps.ai.exceptions import AIProviderError, AIProviderTimeoutError

from .base import AIGenerationResult, AIProvider


class OpenAIProvider(AIProvider):
    """
    Real OpenAI-backed implementation. Uses Chat Completions with JSON
    mode (response_format={"type": "json_object"}) as a first line of
    defense so the model is constrained to emit a JSON object at the API
    level — apps.ai.services.roasting still independently validates the
    result against the strict Pydantic schema afterward (JSON mode only
    guarantees syntactically valid JSON, not our schema's shape).
    """

    provider_name = "openai"

    def __init__(self):
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self._model = settings.AI_OPENAI_MODEL

    @property
    def model_name(self) -> str:
        return self._model

    def generate_roast(
        self, *, system_prompt: str, user_prompt: str, timeout: float | None = None
    ) -> AIGenerationResult:
        start = time.monotonic()
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=settings.AI_OPENAI_TEMPERATURE,
                max_tokens=settings.AI_OPENAI_MAX_OUTPUT_TOKENS,
                timeout=timeout or settings.AI_REQUEST_TIMEOUT_SECONDS,
            )
        except APITimeoutError as exc:
            raise AIProviderTimeoutError("OpenAI request timed out.") from exc
        except (APIConnectionError, APIStatusError, APIError) as exc:
            # Deliberately does not include prompt/response content —
            # only the vendor's own error message/status.
            raise AIProviderError(f"OpenAI request failed: {exc}") from exc

        latency_ms = int((time.monotonic() - start) * 1000)
        choice = response.choices[0]
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        return AIGenerationResult(
            raw_text=choice.message.content or "",
            model=response.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost=self._estimate_cost(input_tokens, output_tokens),
        )

    @staticmethod
    def _estimate_cost(input_tokens: int, output_tokens: int) -> Decimal:
        input_price = Decimal(str(settings.AI_OPENAI_INPUT_PRICE_PER_1K))
        output_price = Decimal(str(settings.AI_OPENAI_OUTPUT_PRICE_PER_1K))
        input_cost = Decimal(input_tokens) / 1000 * input_price
        output_cost = Decimal(output_tokens) / 1000 * output_price
        return input_cost + output_cost

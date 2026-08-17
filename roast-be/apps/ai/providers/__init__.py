from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .base import AIGenerationResult, AIProvider
from .stub import NotImplementedAIProvider

__all__ = ["AIGenerationResult", "AIProvider", "get_ai_provider"]

_PROVIDERS = {
    "stub": NotImplementedAIProvider,
}


def _openai_provider_cls():
    # Local import: avoids requiring the openai SDK/API key just to run
    # with AI_PROVIDER=stub (the default for dev/CI).
    from .openai import OpenAIProvider

    return OpenAIProvider


def get_ai_provider() -> AIProvider:
    """
    Settings-driven factory (mirrors apps.common.storage.get_storage()):
    swapping providers is one new AIProvider subclass + one new entry
    here + an env var change — no call-site changes anywhere that calls
    get_ai_provider().
    """
    provider_name = settings.AI_PROVIDER
    if provider_name == "openai":
        return _openai_provider_cls()()
    try:
        provider_cls = _PROVIDERS[provider_name]
    except KeyError:
        raise ImproperlyConfigured(f"Unknown AI_PROVIDER: {provider_name!r}") from None
    return provider_cls()

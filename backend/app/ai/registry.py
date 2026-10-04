from .adapters import AnthropicProvider, GeminiProvider, GrokProvider, OpenAIProvider
from .base import AIProvider

PROVIDERS = {p.name: p() for p in (OpenAIProvider, AnthropicProvider, GeminiProvider, GrokProvider)}


def get_provider(name: str) -> AIProvider:
    return PROVIDERS[name]

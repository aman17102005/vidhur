"""One small adapter per provider. Each makes a single HTTPS call with the user's key and keeps nothing."""
import os

import httpx

from .base import AIProvider, AIProviderError, safe_status_error

_TIMEOUT = httpx.Timeout(45.0, connect=10.0)


async def _post(url: str, headers: dict, body: dict) -> dict:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=False) as client:
            r = await client.post(url, headers=headers, json=body)
    except httpx.TimeoutException:
        raise AIProviderError("The AI provider took too long to respond.")
    except httpx.HTTPError:
        raise AIProviderError("Could not reach the AI provider.")
    if r.status_code >= 400:
        raise safe_status_error(r.status_code)
    try:
        return r.json()
    except ValueError:
        raise AIProviderError("The AI provider sent an unreadable response.")


class _OpenAICompatible(AIProvider):
    url: str

    async def explain(self, *, api_key, model, system, user):
        data = await _post(
            self.url,
            {"Authorization": f"Bearer {api_key}"},
            {"model": model, "max_tokens": 400, "temperature": 0.2,
             "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
        )
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError):
            raise AIProviderError("The AI provider sent an unexpected response.")


class OpenAIProvider(_OpenAICompatible):
    name = "openai"
    default_model = os.getenv("VIDHUR_MODEL_OPENAI", "gpt-4o-mini")
    url = "https://api.openai.com/v1/chat/completions"


class GrokProvider(_OpenAICompatible):
    name = "grok"
    default_model = os.getenv("VIDHUR_MODEL_GROK", "grok-3-mini")
    url = "https://api.x.ai/v1/chat/completions"


class AnthropicProvider(AIProvider):
    name = "anthropic"
    default_model = os.getenv("VIDHUR_MODEL_ANTHROPIC", "claude-haiku-4-5-20251001")

    async def explain(self, *, api_key, model, system, user):
        data = await _post(
            "https://api.anthropic.com/v1/messages",
            {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            {"model": model, "max_tokens": 400, "system": system, "messages": [{"role": "user", "content": user}]},
        )
        try:
            return "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text").strip()
        except (KeyError, TypeError, AttributeError):
            raise AIProviderError("The AI provider sent an unexpected response.")


class GeminiProvider(AIProvider):
    name = "gemini"
    default_model = os.getenv("VIDHUR_MODEL_GEMINI", "gemini-2.5-flash")

    async def explain(self, *, api_key, model, system, user):
        # Key goes in a header, never in the URL, so it cannot end up in any URL log.
        data = await _post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            {"x-goog-api-key": api_key},
            {"systemInstruction": {"parts": [{"text": system}]},
             "contents": [{"role": "user", "parts": [{"text": user}]}],
             "generationConfig": {"maxOutputTokens": 600, "temperature": 0.2}},
        )
        try:
            return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"]).strip()
        except (KeyError, IndexError, TypeError, AttributeError):
            raise AIProviderError("The AI provider sent an unexpected response (it may have blocked the content).")

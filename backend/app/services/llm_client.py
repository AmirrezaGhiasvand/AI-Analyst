"""
LLM client.

Provides one function agents call regardless of which provider is
active — they don't need to know or care whether a response came from
a local Ollama model or OpenRouter. Both providers speak the OpenAI
chat-completions API shape, so a single client class handles both by
just pointing at a different base_url.
"""

from typing import cast

from app.core.config import settings
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam


class LLMClient:
    def __init__(self, provider: str | None = None):
        self.provider = provider or settings.llm_provider

        if self.provider == "ollama":
            # Ollama requires SOME api_key value to satisfy the OpenAI
            # client's validation, even though it doesn't check it.
            self._client = OpenAI(base_url=settings.ollama_base_url, api_key="ollama")
            self.model = settings.ollama_model
        elif self.provider == "openrouter":
            if not settings.openrouter_api_key:
                raise ValueError(
                    "OPENROUTER_API_KEY is not set. Add it to your .env file."
                )
            if not settings.openrouter_model:
                raise ValueError(
                    "OPENROUTER_MODEL is not set — OpenRouter's free model "
                    "lineup changes often, so this has no default. Check "
                    "https://openrouter.ai/models?fmt=table&max_price=0 "
                    "and set OPENROUTER_MODEL in your .env."
                )
            self._client = OpenAI(
                base_url=settings.openrouter_base_url,
                api_key=settings.openrouter_api_key,
            )
            self.model = settings.openrouter_model
        else:
            raise ValueError(f"Unknown LLM provider: '{self.provider}'")

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
        """
        messages: list of {"role": "user"|"assistant"|"system", "content": "..."}
        Returns the assistant's reply text.

        Deliberately typed as our own plain list[dict[str, str]] rather
        than OpenAI's stricter ChatCompletionMessageParam — that's how
        every agent naturally builds message lists, and forcing the
        stricter type through every call site just pushes type-checker
        friction into unrelated files. The cast below converts at the
        one place it actually matters: the SDK call itself.

        temperature defaults low (0.2) rather than a typical chat default
        (~0.7-1.0) — this app's agents are meant to reason precisely about
        real data, not write creatively. Lower temperature means more
        consistent, less "inventive" outputs, which matters when an agent
        is deciding whether to run code or naming a column that must
        exactly match the real schema.
        """
        response = self._client.chat.completions.create(
            model=self.model,
            messages=cast(list[ChatCompletionMessageParam], messages),
            temperature=temperature,
        )
        return response.choices[0].message.content or ""


def get_llm_client() -> LLMClient:
    """Factory using whatever provider is configured in settings."""
    return LLMClient()

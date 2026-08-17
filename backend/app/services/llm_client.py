from typing import cast

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from app.core.config import settings


class LLMClient:
    def __init__(self, provider: str | None = None):
        self.provider = provider or settings.llm_provider

        if self.provider == "ollama":
            self._client = OpenAI(base_url=settings.ollama_base_url, api_key="ollama")
            self.model = settings.ollama_model
        elif self.provider == "openrouter":
            if not settings.openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY is not set. Add it to your .env file.")
            if not settings.openrouter_model:
                raise ValueError("OPENROUTER_MODEL is not set.")
            self._client = OpenAI(
                base_url=settings.openrouter_base_url, api_key=settings.openrouter_api_key
            )
            self.model = settings.openrouter_model
        else:
            raise ValueError(f"Unknown LLM provider: '{self.provider}'")

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=cast(list[ChatCompletionMessageParam], messages),
            temperature=temperature,
        )
        return response.choices[0].message.content or ""


def get_llm_client() -> LLMClient:
    return LLMClient()
"""
Manual one-off test for the LLM client. Not part of the app — run this
once to confirm your Ollama/OpenRouter setup actually works, then delete
this file. (Claude's sandbox can't reach Ollama or OpenRouter, so this
step has to be verified on your machine.)

Run with: uv run python test_llm.py
"""

from app.services.llm_client import get_llm_client

client = get_llm_client()
print(f"Using provider: {client.provider}, model: {client.model}")

reply = client.chat(
    [{"role": "user", "content": "Say 'hello world' and nothing else."}]
)
print("Response:", reply)

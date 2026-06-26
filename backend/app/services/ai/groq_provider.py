import time
import httpx
from app.services.ai.provider import AIProvider, AIResponse, PromptType

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


class GroqProvider(AIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def complete(
        self,
        messages: list[dict],
        prompt_type: PromptType,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AIResponse:
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(
                GROQ_API_URL,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": GROQ_MODEL, "messages": messages, "temperature": temperature, "max_tokens": max_tokens},
            )
            r.raise_for_status()
            data = r.json()

        content = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        latency = int((time.monotonic() - start) * 1000)
        return AIResponse(content=content, tokens_used=tokens, provider="groq", latency_ms=latency)


def get_ai_provider(api_key: str) -> AIProvider:
    return GroqProvider(api_key=api_key)

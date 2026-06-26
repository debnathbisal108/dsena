from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

PromptType = Literal[
    "initial_response", "evaluate_lead", "write_followup",
    "score_lead", "handle_objection", "propose_meeting",
]


@dataclass
class AIResponse:
    content: str
    tokens_used: int
    provider: str
    latency_ms: int = 0


class AIProvider(ABC):
    @abstractmethod
    async def complete(self, messages: list[dict], prompt_type: PromptType, temperature: float = 0.7, max_tokens: int = 1000) -> AIResponse: ...

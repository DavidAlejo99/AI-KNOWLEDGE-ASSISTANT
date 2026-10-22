from dataclasses import dataclass
from typing import Protocol


class LLMProviderError(Exception):
    """Error controlado cuando el proveedor LLM falla."""


@dataclass(frozen=True)
class LLMResult:
    content: str
    model: str


class LLMProvider(Protocol):
    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        top_p: float = 1.0,
        max_tokens: int = 300,
    ) -> LLMResult:
        ...

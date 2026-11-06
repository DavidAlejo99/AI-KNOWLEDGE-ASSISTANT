from dataclasses import dataclass, field
from typing import Any, Protocol


class LLMProviderError(Exception):
    """Error controlado cuando el proveedor LLM falla."""


@dataclass(frozen=True)
class LLMResult:
    content: str
    model: str


@dataclass(frozen=True)
class LLMToolResponse:
    """Respuesta del LLM cuando se le ofrecen herramientas."""

    content: str | None
    model: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


class LLMProvider(Protocol):
    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        top_p: float = 1.0,
        max_tokens: int = 300,
    ) -> LLMResult:
        ...


class ToolCallingProvider(Protocol):
    async def complete_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        temperature: float = 0.3,
        top_p: float = 1.0,
        max_tokens: int = 300,
    ) -> LLMToolResponse:
        ...

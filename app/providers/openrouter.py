import logging
from typing import Any

import httpx

from app.providers.base import LLMProviderError, LLMResult, LLMToolResponse


logger = logging.getLogger(__name__)


class OpenRouterProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        timeout: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.transport = transport

    async def _request(
        self,
        messages: list[dict[str, Any]],
        temperature: float,
        top_p: float,
        max_tokens: int,
        tools: list[dict[str, Any]] | None = None,
    ) -> tuple[dict[str, Any], str]:
        """Envía la petición a OpenRouter y devuelve (mensaje, modelo servido)."""
        if not self.api_key:
            raise LLMProviderError("No se configuró OPENROUTER_API_KEY")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if tools is not None:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

        except httpx.TimeoutException as exc:
            raise LLMProviderError("Tiempo de espera agotado") from exc

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            logger.warning("OpenRouter HTTP %s: %s", status, exc.response.text[:300])
            raise LLMProviderError(f"OpenRouter respondió HTTP {status}") from exc

        except (httpx.RequestError, ValueError) as exc:
            raise LLMProviderError("Error de comunicación con el proveedor") from exc

        try:
            message = data["choices"][0]["message"]
            if not isinstance(message, dict):
                raise TypeError("Mensaje inválido")
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("Formato de respuesta LLM inválido") from exc

        return message, data.get("model", self.model)

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        top_p: float = 1.0,
        max_tokens: int = 300,
    ) -> LLMResult:
        message, model = await self._request(messages, temperature, top_p, max_tokens)

        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError("Formato de respuesta LLM inválido")

        return LLMResult(content=content, model=model)

    async def complete_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        temperature: float = 0.3,
        top_p: float = 1.0,
        max_tokens: int = 300,
    ) -> LLMToolResponse:
        message, model = await self._request(
            messages, temperature, top_p, max_tokens, tools=tools
        )

        tool_calls = message.get("tool_calls") or []
        if not isinstance(tool_calls, list):
            raise LLMProviderError("Formato de tool_calls inválido")

        return LLMToolResponse(
            content=message.get("content"),
            model=model,
            tool_calls=tool_calls,
        )

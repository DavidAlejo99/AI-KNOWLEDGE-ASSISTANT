import httpx
import pytest

from app.providers.base import LLMProviderError
from app.providers.openrouter import OpenRouterProvider


MESSAGES = [{"role": "user", "content": "Hola"}]


def make_provider(handler, api_key: str = "test-key") -> OpenRouterProvider:
    return OpenRouterProvider(
        api_key=api_key,
        model="test-model",
        base_url="https://openrouter.test/api/v1",
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.asyncio
async def test_returns_content_and_model() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "model": "served-model",
                "choices": [{"message": {"content": "Hola, soy el modelo"}}],
            },
        )

    result = await make_provider(handler).generate(MESSAGES)

    assert result.content == "Hola, soy el modelo"
    assert result.model == "served-model"


@pytest.mark.asyncio
async def test_timeout_raises_controlled_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout", request=request)

    with pytest.raises(LLMProviderError, match="Tiempo de espera"):
        await make_provider(handler).generate(MESSAGES)


@pytest.mark.asyncio
async def test_http_429_raises_controlled_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": "rate limit"})

    with pytest.raises(LLMProviderError, match="429"):
        await make_provider(handler).generate(MESSAGES)


@pytest.mark.asyncio
async def test_response_without_choices_raises_controlled_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "abc"})

    with pytest.raises(LLMProviderError, match="Formato"):
        await make_provider(handler).generate(MESSAGES)


@pytest.mark.asyncio
async def test_missing_api_key_raises_controlled_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200)

    with pytest.raises(LLMProviderError, match="OPENROUTER_API_KEY"):
        await make_provider(handler, api_key="").generate(MESSAGES)

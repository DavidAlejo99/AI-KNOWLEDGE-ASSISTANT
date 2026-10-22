import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes.chat import get_assistant_service
from app.main import app
from app.services.assistant_service import AssistantService
from tests.fakes import FakeLLMProvider


def use_fake_provider(provider: FakeLLMProvider) -> None:
    app.dependency_overrides[get_assistant_service] = lambda: AssistantService(provider)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


async def post_chat(body: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/api/v1/chat", json=body)


@pytest.mark.asyncio
async def test_health() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_info() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/info")

    assert response.status_code == 200
    assert response.json()["llm_enabled"] is True


@pytest.mark.asyncio
async def test_chat_ok() -> None:
    use_fake_provider(FakeLLMProvider(answer="Una API REST es..."))

    response = await post_chat({"question": "¿Qué es una API REST?"})

    assert response.status_code == 200
    assert response.json() == {"answer": "Una API REST es...", "model": "fake-model"}


@pytest.mark.asyncio
async def test_chat_rejects_short_question() -> None:
    provider = FakeLLMProvider()
    use_fake_provider(provider)

    response = await post_chat({"question": "A"})

    assert response.status_code == 422
    assert provider.last_messages == []


@pytest.mark.asyncio
async def test_chat_rejects_too_long_question() -> None:
    use_fake_provider(FakeLLMProvider())

    response = await post_chat({"question": "a" * 2001})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_rejects_negative_temperature() -> None:
    provider = FakeLLMProvider()
    use_fake_provider(provider)

    response = await post_chat({"question": "¿Qué es FastAPI?", "temperature": -1})

    assert response.status_code == 422
    assert provider.last_messages == []


@pytest.mark.asyncio
async def test_chat_returns_502_when_provider_fails() -> None:
    use_fake_provider(FakeLLMProvider(fail=True))

    response = await post_chat({"question": "¿Qué es FastAPI?"})

    assert response.status_code == 502

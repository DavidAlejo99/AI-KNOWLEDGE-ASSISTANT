import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes.agent import get_agent_service
from app.main import app
from app.providers.base import LLMToolResponse
from app.services.agent_service import AgentService
from tests.fakes import FakeToolCallingProvider, tool_call


def use_fake(provider: FakeToolCallingProvider) -> None:
    app.dependency_overrides[get_agent_service] = lambda: AgentService(provider)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


async def post_agent(body: dict):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post("/api/v1/agent/chat", json=body)


@pytest.mark.asyncio
async def test_agent_endpoint_returns_answer_and_tools_used() -> None:
    use_fake(FakeToolCallingProvider([
        LLMToolResponse(
            content=None,
            model="fake-model",
            tool_calls=[tool_call("call_1", "calculate_study_hours", '{"hours_per_day": 2, "days": 5}')],
        ),
        LLMToolResponse(content="Estudiarás 10 horas.", model="fake-model"),
    ]))

    response = await post_agent({"question": "Si estudio 2 horas por 5 días, ¿cuántas son?"})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Estudiarás 10 horas.",
        "model": "fake-model",
        "tools_used": ["calculate_study_hours"],
    }


@pytest.mark.asyncio
async def test_agent_rejects_too_many_steps() -> None:
    provider = FakeToolCallingProvider([])
    use_fake(provider)

    response = await post_agent({"question": "¿Qué es RAG?", "max_steps": 6})

    assert response.status_code == 422
    assert provider.calls == []


@pytest.mark.asyncio
async def test_agent_returns_502_when_provider_fails() -> None:
    use_fake(FakeToolCallingProvider([], fail=True))

    response = await post_agent({"question": "¿Qué es RAG?"})

    assert response.status_code == 502

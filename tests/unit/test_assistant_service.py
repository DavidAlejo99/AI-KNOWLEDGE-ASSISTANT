import pytest

from app.services.assistant_service import SYSTEM_PROMPT, AssistantService
from tests.fakes import FakeLLMProvider


@pytest.mark.asyncio
async def test_service_builds_system_and_user_messages() -> None:
    provider = FakeLLMProvider(answer="FastAPI es un framework")
    service = AssistantService(provider)

    result = await service.ask("¿Qué es FastAPI?", temperature=0.5)

    assert result.content == "FastAPI es un framework"
    assert provider.last_messages[0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert provider.last_messages[1] == {"role": "user", "content": "¿Qué es FastAPI?"}
    assert provider.last_params["temperature"] == 0.5

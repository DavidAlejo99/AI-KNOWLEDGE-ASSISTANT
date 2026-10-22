import pytest

from app.services.assistance_service import BootstrapAssistantService


@pytest.mark.asyncio
async def test_returns_known_answer() -> None:
    service = BootstrapAssistantService()

    response = await service.answer("¿Qué es FastAPI?")

    assert response.provider == "bootstrap-local"
    assert "framework" in response.answer.lower()

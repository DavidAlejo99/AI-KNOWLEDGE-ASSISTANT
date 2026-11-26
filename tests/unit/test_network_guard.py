import pytest

from app.providers.openrouter import OpenRouterProvider
from tests.conftest import NetworkBlockedError


def was_blocked(exc: BaseException | None) -> bool:
    """Busca el bloqueo aunque httpx lo envuelva en otra excepción."""
    if exc is None:
        return False
    if isinstance(exc, NetworkBlockedError):
        return True
    if isinstance(exc, BaseExceptionGroup):
        return any(was_blocked(inner) for inner in exc.exceptions)
    return was_blocked(exc.__cause__ or exc.__context__)


@pytest.mark.asyncio
async def test_real_provider_cannot_reach_openrouter_during_tests() -> None:
    """Si alguna prueba usara el proveedor real por error, fallaría aquí sin gastar tokens."""
    provider = OpenRouterProvider(
        api_key="clave-de-prueba",
        model="modelo-de-prueba",
        base_url="https://openrouter.ai/api/v1",
    )

    with pytest.raises(BaseException) as info:
        await provider.generate([{"role": "user", "content": "hola"}])

    assert was_blocked(info.value)

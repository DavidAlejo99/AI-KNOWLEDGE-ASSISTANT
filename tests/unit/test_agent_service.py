import json

import pytest

from app.providers.base import LLMToolResponse
from app.services.agent_service import AgentExecutionError, AgentService
from tests.fakes import FakeToolCallingProvider, tool_call


def final(text: str) -> LLMToolResponse:
    return LLMToolResponse(content=text, model="fake-model")


def wants_tool(name: str, arguments: str) -> LLMToolResponse:
    return LLMToolResponse(
        content=None,
        model="fake-model",
        tool_calls=[tool_call("call_1", name, arguments)],
    )


@pytest.mark.asyncio
async def test_agent_uses_tool_and_answers() -> None:
    provider = FakeToolCallingProvider([
        wants_tool("calculate_study_hours", '{"hours_per_day": 2, "days": 5}'),
        final("Estudiarás 10 horas."),
    ])

    result = await AgentService(provider).ask("Si estudio 2 horas por 5 días, ¿cuántas horas son?")

    assert result.answer == "Estudiarás 10 horas."
    assert result.tools_used == ["calculate_study_hours"]
    tool_message = provider.calls[1][-1]
    assert tool_message["role"] == "tool"
    assert tool_message["tool_call_id"] == "call_1"
    assert json.loads(tool_message["content"]) == {"ok": True, "data": {"total_hours": 10.0}}


@pytest.mark.asyncio
async def test_agent_answers_without_tools() -> None:
    provider = FakeToolCallingProvider([final("Hola, ¿en qué te ayudo?")])

    result = await AgentService(provider).ask("Hola")

    assert result.tools_used == []
    assert len(provider.calls) == 1


@pytest.mark.asyncio
async def test_write_tool_without_confirmation_is_blocked() -> None:
    provider = FakeToolCallingProvider([
        wants_tool("create_study_task", '{"title": "Repasar RAG", "estimated_hours": 2}'),
        final("No pude crear la tarea: falta confirmación."),
    ])

    await AgentService(provider).ask("Crea una tarea", confirm_actions=False)

    tool_message = provider.calls[1][-1]
    assert json.loads(tool_message["content"]) == {"ok": False, "error": "confirmation_required"}


@pytest.mark.asyncio
async def test_agent_stops_at_max_steps() -> None:
    provider = FakeToolCallingProvider([
        wants_tool("lookup_ai_concept", '{"concept": "rag"}'),
        wants_tool("lookup_ai_concept", '{"concept": "rag"}'),
    ])

    with pytest.raises(AgentExecutionError, match="Límite"):
        await AgentService(provider).ask("Pregunta", max_steps=2)


@pytest.mark.asyncio
async def test_invalid_tool_call_raises_error() -> None:
    bad = LLMToolResponse(content=None, model="fake-model", tool_calls=[{"id": "", "function": {}}])
    provider = FakeToolCallingProvider([bad])

    with pytest.raises(AgentExecutionError):
        await AgentService(provider).ask("Pregunta")


@pytest.mark.asyncio
async def test_empty_final_answer_raises_error() -> None:
    provider = FakeToolCallingProvider([final("   ")])

    with pytest.raises(AgentExecutionError, match="respuesta final"):
        await AgentService(provider).ask("Pregunta")

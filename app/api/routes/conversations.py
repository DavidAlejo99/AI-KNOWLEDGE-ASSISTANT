import logging
from functools import lru_cache
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.routes.agent import get_agent_service
from app.core.config import get_settings
from app.guardrails.service import GuardrailService, GuardrailViolation, OutputGuardrailViolation
from app.memory.repository import MemoryRepository
from app.providers.base import LLMProviderError
from app.schemas.conversation import (
    ConversationCreated,
    ConversationReplyRequest,
    ConversationReplyResponse,
    ConversationSummary,
    MemoryCreate,
    MemoryItem,
    MessagesResponse,
)
from app.services.agent_service import AgentExecutionError, AgentService
from app.services.conversation_service import (
    ConversationNotFound,
    ConversationService,
    MemoryLimitReached,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/conversations",
    tags=["conversations"],
)


@lru_cache
def get_memory_repository() -> MemoryRepository:
    return MemoryRepository(get_settings().memory_db_path)


def get_conversation_service(
    repository: MemoryRepository = Depends(get_memory_repository),
    agent: AgentService = Depends(get_agent_service),
) -> ConversationService:
    return ConversationService(
        repository=repository,
        agent=agent,
        guardrails=GuardrailService(),
        max_context_messages=get_settings().max_context_messages,
    )


def not_found(exc: Exception) -> HTTPException:
    return HTTPException(status_code=404, detail=str(exc))


@router.post("", response_model=ConversationCreated, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationCreated:
    return ConversationCreated(conversation_id=service.create())


@router.get("", response_model=list[ConversationSummary])
async def list_conversations(
    service: ConversationService = Depends(get_conversation_service),
) -> list[ConversationSummary]:
    return [ConversationSummary(**item) for item in service.list_conversations()]


@router.get("/{conversation_id}/messages", response_model=MessagesResponse)
async def get_messages(
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service),
) -> MessagesResponse:
    try:
        messages = service.messages(str(conversation_id))
    except ConversationNotFound as exc:
        raise not_found(exc) from exc
    return MessagesResponse(conversation_id=conversation_id, messages=messages)


@router.post("/{conversation_id}/messages", response_model=ConversationReplyResponse)
async def send_message(
    conversation_id: UUID,
    payload: ConversationReplyRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationReplyResponse:
    try:
        result = await service.reply(
            str(conversation_id),
            payload.question,
            temperature=payload.temperature,
            top_p=payload.top_p,
            max_tokens=payload.max_tokens,
            confirm_actions=payload.confirm_actions,
            max_steps=payload.max_steps,
        )
    except ConversationNotFound as exc:
        raise not_found(exc) from exc
    except OutputGuardrailViolation as exc:
        logger.warning("Respuesta bloqueada por el guardrail de salida: %s", exc)
        raise HTTPException(status_code=502, detail="Respuesta bloqueada por guardrails") from exc
    except GuardrailViolation as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (AgentExecutionError, LLMProviderError) as exc:
        logger.warning("Fallo del agente: %s", exc)
        raise HTTPException(status_code=502, detail="No se pudo completar la inferencia") from exc

    return ConversationReplyResponse(
        conversation_id=conversation_id,
        answer=result.answer,
        model=result.model,
        tools_used=result.tools_used,
        context_messages=result.context_messages,
    )


@router.get("/{conversation_id}/memories", response_model=list[MemoryItem])
async def list_memories(
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service),
) -> list[MemoryItem]:
    try:
        return [MemoryItem(**item) for item in service.memories(str(conversation_id))]
    except ConversationNotFound as exc:
        raise not_found(exc) from exc


@router.post(
    "/{conversation_id}/memories",
    response_model=MemoryItem,
    status_code=status.HTTP_201_CREATED,
)
async def add_memory(
    conversation_id: UUID,
    payload: MemoryCreate,
    service: ConversationService = Depends(get_conversation_service),
) -> MemoryItem:
    try:
        return MemoryItem(**service.remember(str(conversation_id), payload.fact))
    except ConversationNotFound as exc:
        raise not_found(exc) from exc
    except GuardrailViolation as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except MemoryLimitReached as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/{conversation_id}/memories/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    conversation_id: UUID,
    memory_id: UUID,
    service: ConversationService = Depends(get_conversation_service),
) -> Response:
    try:
        deleted = service.forget(str(conversation_id), str(memory_id))
    except ConversationNotFound as exc:
        raise not_found(exc) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Memoria no encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service),
) -> Response:
    try:
        service.delete(str(conversation_id))
    except ConversationNotFound as exc:
        raise not_found(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)

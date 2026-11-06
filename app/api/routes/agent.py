import logging

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import get_settings
from app.providers.base import LLMProviderError
from app.providers.openrouter import OpenRouterProvider
from app.schemas.agent import AgentChatRequest, AgentChatResponse
from app.services.agent_service import AgentExecutionError, AgentService


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/agent",
    tags=["agent"],
)


def get_agent_service() -> AgentService:
    settings = get_settings()
    provider = OpenRouterProvider(
        api_key=settings.openrouter_api_key,
        model=settings.openrouter_model,
        base_url=settings.openrouter_base_url,
    )
    return AgentService(provider)


@router.post("/chat", response_model=AgentChatResponse)
async def chat_agent(
    payload: AgentChatRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentChatResponse:
    try:
        result = await service.ask(
            question=payload.question,
            temperature=payload.temperature,
            top_p=payload.top_p,
            max_tokens=payload.max_tokens,
            confirm_actions=payload.confirm_actions,
            max_steps=payload.max_steps,
        )
    except (AgentExecutionError, LLMProviderError) as exc:
        logger.warning("Fallo del agente: %s", exc)
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo completar la ejecución del agente: {exc}",
        ) from exc

    return AgentChatResponse(
        answer=result.answer,
        model=result.model,
        tools_used=result.tools_used,
    )

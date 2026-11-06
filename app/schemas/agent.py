from pydantic import Field

from app.schemas.chat import ChatRequest, ChatResponse


class AgentChatRequest(ChatRequest):
    confirm_actions: bool = Field(
        default=False,
        description="Autoriza herramientas que escriben datos (crear tareas).",
    )
    max_steps: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Número máximo de rondas con el LLM.",
    )


class AgentChatResponse(ChatResponse):
    tools_used: list[str]

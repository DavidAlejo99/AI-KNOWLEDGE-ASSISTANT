from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.agent import AgentChatRequest


class ConversationCreated(BaseModel):
    conversation_id: UUID


class ConversationSummary(ConversationCreated):
    created_at: str


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class MessagesResponse(ConversationCreated):
    messages: list[Message]


class ConversationReplyRequest(AgentChatRequest):
    """Mismos campos del agente: question, parámetros, confirm_actions y max_steps."""


class ConversationReplyResponse(ConversationCreated):
    answer: str
    model: str
    tools_used: list[str]
    context_messages: int = Field(description="Mensajes anteriores enviados al modelo como contexto.")


class MemoryCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    fact: str = Field(min_length=3, max_length=300, examples=["Prefiere ejemplos en Python"])


class MemoryItem(MemoryCreate):
    memory_id: UUID

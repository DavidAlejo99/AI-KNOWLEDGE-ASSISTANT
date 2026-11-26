from dataclasses import dataclass

from app.guardrails.service import GuardrailService
from app.memory.repository import MemoryRepository
from app.services.agent_service import AgentService


MAX_MEMORIES = 10


class ConversationNotFound(Exception):
    """La conversación no existe."""


class MemoryLimitReached(Exception):
    """La conversación ya tiene el máximo de memorias."""


@dataclass(frozen=True)
class ConversationResult:
    answer: str
    model: str
    tools_used: list[str]
    context_messages: int


class ConversationService:
    """Lógica de las conversaciones. El router solo habla con esta clase, nunca con SQLite."""

    def __init__(
        self,
        repository: MemoryRepository,
        agent: AgentService,
        guardrails: GuardrailService,
        max_context_messages: int = 8,
    ) -> None:
        self.repository = repository
        self.agent = agent
        self.guardrails = guardrails
        self.max_context_messages = max_context_messages

    def ensure_exists(self, conversation_id: str) -> None:
        if not self.repository.conversation_exists(conversation_id):
            raise ConversationNotFound("Conversación no encontrada")

    # --- Conversaciones y mensajes ------------------------------------------

    def create(self) -> str:
        return self.repository.create_conversation()

    def list_conversations(self) -> list[dict[str, str]]:
        return self.repository.list_conversations()

    def messages(self, conversation_id: str) -> list[dict[str, str]]:
        self.ensure_exists(conversation_id)
        return self.repository.list_messages(conversation_id)

    def delete(self, conversation_id: str) -> None:
        self.ensure_exists(conversation_id)
        self.repository.delete_conversation(conversation_id)

    # --- Memorias explícitas --------------------------------------------------

    def memories(self, conversation_id: str) -> list[dict[str, str]]:
        self.ensure_exists(conversation_id)
        return self.repository.list_memories(conversation_id)

    def remember(self, conversation_id: str, fact: str) -> dict[str, str]:
        self.ensure_exists(conversation_id)
        # Una memoria se reenvía al LLM en cada turno, así que también pasa por el guardrail.
        checked = self.guardrails.check_input(fact)
        if len(self.repository.list_memories(conversation_id)) >= MAX_MEMORIES:
            raise MemoryLimitReached(f"Máximo de {MAX_MEMORIES} memorias por conversación")
        return self.repository.add_memory(conversation_id, checked)

    def forget(self, conversation_id: str, memory_id: str) -> bool:
        self.ensure_exists(conversation_id)
        return self.repository.delete_memory(conversation_id, memory_id)

    # --- Turno con el agente ----------------------------------------------------

    async def reply(
        self,
        conversation_id: str,
        question: str,
        *,
        temperature: float = 0.3,
        top_p: float = 1.0,
        max_tokens: int = 300,
        confirm_actions: bool = False,
        max_steps: int = 3,
    ) -> ConversationResult:
        # 1. La conversación debe existir.
        self.ensure_exists(conversation_id)

        # 2. Guardrail de entrada: si falla, no se llama al LLM.
        safe_question = self.guardrails.check_input(question)

        # 3. Reconstruir el contexto desde SQLite: últimos N mensajes y memorias.
        history = self.repository.list_messages(conversation_id, limit=self.max_context_messages)
        facts = [item["fact"] for item in self.repository.list_memories(conversation_id)]

        # 4. El agente del Módulo III responde (puede usar herramientas).
        result = await self.agent.ask(
            safe_question,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            confirm_actions=confirm_actions,
            max_steps=max_steps,
            history=history,
            memory_facts=facts,
        )

        # 5. Guardrail de salida ANTES de guardar: lo bloqueado nunca llega a la base.
        safe_answer = self.guardrails.check_output(result.answer)

        # 6. Guardar pregunta y respuesta juntas en una sola transacción.
        self.repository.save_turn(conversation_id, safe_question, safe_answer)

        return ConversationResult(
            answer=safe_answer,
            model=result.model,
            tools_used=result.tools_used,
            context_messages=len(history),
        )

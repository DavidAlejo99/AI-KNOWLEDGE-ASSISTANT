from app.schemas.chat import ChatResponse


class BootstrapAssistantService:
    _knowledge = {
        "fastapi": (
            "FastAPI es un framework de Python para "
            "construir APIs basado en type hints y ASGI."
        ),
        "pydantic": (
            "Pydantic valida y serializa datos a partir "
            "de anotaciones de tipo de Python."
        ),
        "asyncio": (
            "AsyncIO permite escribir código concurrente "
            "con async y await para tareas orientadas a E/S."
        ),
        "httpx": (
            "HTTPX es un cliente HTTP para Python con "
            "interfaces síncrona y asíncrona."
        ),
        "pytest": (
            "pytest es un framework de pruebas para Python "
            "con descubrimiento automático, asserts y fixtures."
        ),
    }

    async def answer(self, question: str) -> ChatResponse:
        normalized_question = question.lower()

        for keyword, answer in self._knowledge.items():
            if keyword in normalized_question:
                return ChatResponse(
                    answer=answer,
                    provider="bootstrap-local",
                )

        return ChatResponse(
            answer=(
                "La API está operativa. "
                "En el siguiente módulo conectaremos "
                "el primer LLM."
            ),
            provider="bootstrap-local",
        )

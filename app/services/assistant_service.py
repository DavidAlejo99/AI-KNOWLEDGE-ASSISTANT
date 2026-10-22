from app.providers.base import LLMProvider, LLMResult


SYSTEM_PROMPT = """
Eres AI Knowledge Assistant, un asistente
educativo especializado en tecnología.

Responde en español claro.
Explica los conceptos con ejemplos sencillos.
Si no tienes suficiente información, indícalo.
No inventes referencias ni datos.
""".strip()


class AssistantService:
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    async def ask(
        self,
        question: str,
        temperature: float = 0.3,
        top_p: float = 1.0,
        max_tokens: int = 300,
    ) -> LLMResult:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]

        return await self.provider.generate(
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )

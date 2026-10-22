from app.providers.base import LLMProviderError, LLMResult


class FakeLLMProvider:
    """Proveedor falso: no consume la red ni la API key."""

    def __init__(self, answer: str = "Respuesta simulada", fail: bool = False) -> None:
        self.answer = answer
        self.fail = fail
        self.last_messages: list[dict[str, str]] = []
        self.last_params: dict = {}

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        top_p: float = 1.0,
        max_tokens: int = 300,
    ) -> LLMResult:
        self.last_messages = messages
        self.last_params = {
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }
        if self.fail:
            raise LLMProviderError("Fallo simulado")
        return LLMResult(content=self.answer, model="fake-model")

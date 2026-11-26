import re


class GuardrailViolation(Exception):
    """La entrada no pasó el control (o, en general, un guardrail bloqueó el contenido)."""


class OutputGuardrailViolation(GuardrailViolation):
    """La respuesta del modelo no pasó el control."""


class GuardrailService:
    """Controles deterministas de entrada y salida.

    Son reglas simples con expresiones regulares: no entienden el
    contexto, así que pueden bloquear preguntas legítimas (falsos
    positivos) o dejar pasar ataques escritos de otra forma (falsos
    negativos). Complementan al system prompt, no lo reemplazan.
    """

    MAX_INPUT_CHARS = 2000

    INJECTION_PATTERNS = (
        re.compile(r"\b(ignora|olvida)\s+(todas\s+)?(las\s+|tus\s+)?instrucciones\b", re.I),
        re.compile(r"\bignore\s+(all\s+)?(previous\s+)?instructions\b", re.I),
        re.compile(r"\brevela\s+(el\s+|tu\s+)?(system\s+prompt|prompt\s+del\s+sistema)\b", re.I),
        re.compile(r"\brevela\s+(la\s+|tu\s+)?(api[\s_-]?key|clave|contraseña)\b", re.I),
    )

    SECRET_PATTERNS = (
        re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
        re.compile(r"\bOPENROUTER_API_KEY\s*[:=]\s*\S+", re.I),
    )

    def check_input(self, text: str) -> str:
        value = text.strip()

        if not value:
            raise GuardrailViolation("Entrada vacía o demasiado extensa")

        if len(value) > self.MAX_INPUT_CHARS:
            raise GuardrailViolation("Entrada vacía o demasiado extensa")

        if any(pattern.search(value) for pattern in self.INJECTION_PATTERNS):
            raise GuardrailViolation("Solicitud bloqueada por la política del laboratorio")

        return value

    def check_output(self, text: str) -> str:
        if not text.strip():
            raise OutputGuardrailViolation("El modelo devolvió una respuesta vacía")

        if any(pattern.search(text) for pattern in self.SECRET_PATTERNS):
            raise OutputGuardrailViolation("La respuesta contiene un posible secreto")

        return text

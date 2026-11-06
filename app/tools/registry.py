import json
from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

from app.tools.functions import calculate_study_hours, create_study_task, lookup_ai_concept
from app.tools.schemas import ConceptArgs, HoursArgs, TaskArgs


@dataclass(frozen=True)
class Tool:
    args_model: type[BaseModel]
    function: Callable[[Any], dict]
    is_write: bool
    description: str


REGISTRY: dict[str, Tool] = {
    "lookup_ai_concept": Tool(
        ConceptArgs,
        lookup_ai_concept,
        False,
        "Consulta la definición de un concepto educativo de IA.",
    ),
    "calculate_study_hours": Tool(
        HoursArgs,
        calculate_study_hours,
        False,
        "Calcula las horas totales de estudio.",
    ),
    "create_study_task": Tool(
        TaskArgs,
        create_study_task,
        True,
        "Crea una tarea de estudio. Requiere confirmación explícita.",
    ),
}


def tool_definitions() -> list[dict[str, Any]]:
    """Describe las herramientas en el formato que entiende el LLM."""
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": tool.description,
                "parameters": tool.args_model.model_json_schema(),
            },
        }
        for name, tool in REGISTRY.items()
    ]


def execute_tool(name: str, raw_arguments: str, confirm_actions: bool) -> dict[str, Any]:
    """Valida y ejecuta una herramienta. Nunca lanza excepciones al agente."""
    tool = REGISTRY.get(name)
    if tool is None:
        return {"ok": False, "error": "unknown_tool"}

    if tool.is_write and not confirm_actions:
        return {"ok": False, "error": "confirmation_required"}

    try:
        args = tool.args_model.model_validate(json.loads(raw_arguments))
    except (json.JSONDecodeError, ValidationError, ValueError, TypeError):
        return {"ok": False, "error": "invalid_arguments"}

    return {"ok": True, "data": tool.function(args)}

import math
from uuid import uuid4

from app.tools.schemas import ConceptArgs, EffortArgs, HoursArgs, TaskArgs


CONCEPTS = {
    "rag": "RAG combina recuperación de información con generación de texto.",
    "embedding": "Un embedding representa información mediante un vector numérico.",
    "function calling": (
        "Function Calling permite al modelo solicitar "
        "la ejecución de funciones externas."
    ),
    "fastapi": (
        "FastAPI es un framework de Python para construir "
        "APIs con tipado y validación."
    ),
}

# Almacenamiento temporal del laboratorio: se pierde al reiniciar el servidor.
TASKS: list[dict] = []

# Horas de estudio estimadas por tema según la dificultad.
HOURS_PER_TOPIC = {"basico": 2, "intermedio": 4, "avanzado": 6}
LOW_EFFORT_MAX = 10
MEDIUM_EFFORT_MAX = 30


def lookup_ai_concept(args: ConceptArgs) -> dict:
    key = args.concept.strip().lower()
    definition = CONCEPTS.get(key)
    return {"found": definition is not None, "concept": key, "definition": definition}


def calculate_study_hours(args: HoursArgs) -> dict:
    return {"total_hours": round(args.hours_per_day * args.days, 2)}


def create_study_task(args: TaskArgs) -> dict:
    item = {
        "id": str(uuid4()),
        "title": args.title,
        "estimated_hours": args.estimated_hours,
    }
    TASKS.append(item)
    return {"created": True, "task": item}


def estimate_learning_effort(args: EffortArgs) -> dict:
    hours_per_topic = HOURS_PER_TOPIC[args.difficulty]
    total_hours = args.topics * hours_per_topic
    weeks = math.ceil(total_hours / args.weekly_hours)

    if total_hours <= LOW_EFFORT_MAX:
        level = "bajo"
    elif total_hours <= MEDIUM_EFFORT_MAX:
        level = "medio"
    else:
        level = "alto"

    return {
        "total_hours": total_hours,
        "weeks": weeks,
        "effort_level": level,
        "explanation": (
            f"{args.topics} temas x {hours_per_topic} h ({args.difficulty}) = {total_hours} h; "
            f"{total_hours} h / {args.weekly_hours:g} h por semana = {weeks} semana(s)."
        ),
    }

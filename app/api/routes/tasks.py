from fastapi import APIRouter

from app.schemas.task import StudyTask
from app.tools import functions


router = APIRouter(
    prefix="/api/v1/tasks",
    tags=["tasks"],
)


@router.get("", response_model=list[StudyTask])
async def list_tasks() -> list[StudyTask]:
    """Solo lectura: permite comprobar si create_study_task escribió de verdad.

    Las tareas viven en TASKS (memoria del proceso), así que se pierden al reiniciar.
    """
    return [StudyTask(**task) for task in functions.TASKS]

from pydantic import BaseModel


class StudyTask(BaseModel):
    id: str
    title: str
    estimated_hours: float

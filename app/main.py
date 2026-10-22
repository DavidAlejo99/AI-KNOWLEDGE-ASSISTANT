from fastapi import FastAPI

from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.info import router as info_router


app = FastAPI(
    title="AI Knowledge Assistant",
    description=(
        "API evolutiva para el curso "
        "de Ingeniería de Sistemas de IA."
    ),
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(info_router)
app.include_router(chat_router)

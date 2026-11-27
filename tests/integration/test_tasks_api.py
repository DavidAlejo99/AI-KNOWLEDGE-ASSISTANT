import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.tools import functions
from app.tools.registry import execute_tool


async def get_tasks() -> list[dict]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/tasks")
    assert response.status_code == 200
    return response.json()


@pytest.mark.asyncio
async def test_tasks_endpoint_shows_only_confirmed_writes() -> None:
    functions.TASKS.clear()
    args = '{"title": "Estudiar FastAPI", "estimated_hours": 2}'

    execute_tool("create_study_task", args, confirm_actions=False)
    after_denied = await get_tasks()
    created = execute_tool("create_study_task", args, confirm_actions=True)
    after_confirmed = await get_tasks()

    assert after_denied == []
    assert [task["id"] for task in after_confirmed] == [created["data"]["task"]["id"]]

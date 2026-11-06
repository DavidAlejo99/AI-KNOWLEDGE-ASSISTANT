from app.tools.registry import execute_tool, tool_definitions


def test_tool_definitions_lists_the_three_tools() -> None:
    names = [t["function"]["name"] for t in tool_definitions()]

    assert names == ["lookup_ai_concept", "calculate_study_hours", "create_study_task"]


def test_calculate_study_hours() -> None:
    result = execute_tool("calculate_study_hours", '{"hours_per_day": 2, "days": 5}', False)

    assert result == {"ok": True, "data": {"total_hours": 10.0}}


def test_lookup_known_concept() -> None:
    result = execute_tool("lookup_ai_concept", '{"concept": "RAG"}', False)

    assert result["ok"] is True
    assert result["data"]["found"] is True


def test_unknown_tool() -> None:
    assert execute_tool("borrar_todo", "{}", False) == {"ok": False, "error": "unknown_tool"}


def test_invalid_arguments_are_rejected() -> None:
    malformed = execute_tool("calculate_study_hours", "no es json", False)
    out_of_range = execute_tool("calculate_study_hours", '{"hours_per_day": 20, "days": 5}', False)
    extra_field = execute_tool("calculate_study_hours", '{"hours_per_day": 2, "days": 5, "x": 1}', False)

    for result in (malformed, out_of_range, extra_field):
        assert result == {"ok": False, "error": "invalid_arguments"}


def test_write_tool_requires_confirmation() -> None:
    args = '{"title": "Repasar RAG", "estimated_hours": 2}'

    blocked = execute_tool("create_study_task", args, confirm_actions=False)
    allowed = execute_tool("create_study_task", args, confirm_actions=True)

    assert blocked == {"ok": False, "error": "confirmation_required"}
    assert allowed["ok"] is True
    assert allowed["data"]["created"] is True

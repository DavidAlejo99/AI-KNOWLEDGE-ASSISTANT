import pytest

from app.memory.repository import MemoryRepository


@pytest.fixture
def repo(tmp_path) -> MemoryRepository:
    return MemoryRepository(str(tmp_path / "test.db"))


def test_create_conversation(repo: MemoryRepository) -> None:
    conversation_id = repo.create_conversation()

    assert repo.conversation_exists(conversation_id) is True
    assert repo.conversation_exists("no-existe") is False


def test_list_conversations(repo: MemoryRepository) -> None:
    a = repo.create_conversation()
    b = repo.create_conversation()

    ids = {item["conversation_id"] for item in repo.list_conversations()}

    assert ids == {a, b}


def test_save_turn_keeps_order(repo: MemoryRepository) -> None:
    conversation_id = repo.create_conversation()

    repo.save_turn(conversation_id, "Me llamo Alejo", "Hola, Alejo")
    repo.save_turn(conversation_id, "¿Cómo me llamo?", "Te llamas Alejo")

    assert repo.list_messages(conversation_id) == [
        {"role": "user", "content": "Me llamo Alejo"},
        {"role": "assistant", "content": "Hola, Alejo"},
        {"role": "user", "content": "¿Cómo me llamo?"},
        {"role": "assistant", "content": "Te llamas Alejo"},
    ]


def test_recent_messages_returns_only_last_n(repo: MemoryRepository) -> None:
    conversation_id = repo.create_conversation()
    for i in range(1, 4):
        repo.save_turn(conversation_id, f"pregunta {i}", f"respuesta {i}")

    recent = repo.list_messages(conversation_id, limit=2)

    assert recent == [
        {"role": "user", "content": "pregunta 3"},
        {"role": "assistant", "content": "respuesta 3"},
    ]


def test_conversations_are_isolated(repo: MemoryRepository) -> None:
    a = repo.create_conversation()
    b = repo.create_conversation()
    repo.save_turn(a, "secreto de A", "ok")
    repo.add_memory(a, "Dato de A")

    assert repo.list_messages(b) == []
    assert repo.list_memories(b) == []


def test_memories_add_list_delete(repo: MemoryRepository) -> None:
    conversation_id = repo.create_conversation()
    memory = repo.add_memory(conversation_id, "Prefiere ejemplos en Python")

    assert repo.list_memories(conversation_id) == [memory]
    assert repo.delete_memory(conversation_id, memory["memory_id"]) is True
    assert repo.list_memories(conversation_id) == []
    assert repo.delete_memory(conversation_id, memory["memory_id"]) is False


def test_memory_cannot_be_deleted_from_another_conversation(repo: MemoryRepository) -> None:
    a = repo.create_conversation()
    b = repo.create_conversation()
    memory = repo.add_memory(a, "Dato de A")

    assert repo.delete_memory(b, memory["memory_id"]) is False
    assert repo.list_memories(a) == [memory]


def test_delete_conversation_removes_messages_and_memories(repo: MemoryRepository) -> None:
    conversation_id = repo.create_conversation()
    repo.save_turn(conversation_id, "hola", "hola")
    repo.add_memory(conversation_id, "dato")

    assert repo.delete_conversation(conversation_id) is True
    assert repo.conversation_exists(conversation_id) is False
    assert repo.list_messages(conversation_id) == []
    assert repo.list_memories(conversation_id) == []


def test_data_survives_a_restart(tmp_path) -> None:
    db_path = str(tmp_path / "persistente.db")
    first = MemoryRepository(db_path)
    conversation_id = first.create_conversation()
    first.save_turn(conversation_id, "Me llamo Alejo", "Hola, Alejo")

    # Una instancia nueva sobre el mismo archivo simula reiniciar FastAPI.
    after_restart = MemoryRepository(db_path)

    assert after_restart.conversation_exists(conversation_id) is True
    assert after_restart.list_messages(conversation_id)[0]["content"] == "Me llamo Alejo"

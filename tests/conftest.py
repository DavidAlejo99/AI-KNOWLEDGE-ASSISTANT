import socket

import pytest


class NetworkBlockedError(RuntimeError):
    """Una prueba intentó salir a la red."""


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    """Ninguna prueba puede resolver DNS ni abrir conexiones.

    Así se garantiza que las pruebas no gastan tokens ni llaman a OpenRouter.
    """

    def blocked(*args, **kwargs):
        raise NetworkBlockedError("Llamada de red bloqueada durante las pruebas")

    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)

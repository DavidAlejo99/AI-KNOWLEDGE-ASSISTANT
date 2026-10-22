# AI Knowledge Assistant

API asíncrona construida con FastAPI. Es el primer incremento funcional (Módulo 0) del asistente de conocimiento empresarial. En esta etapa **no** se integra ningún LLM: las respuestas las genera un servicio local de bootstrap.

## Tecnologías

Python 3.12+, FastAPI, Pydantic, AsyncIO, HTTPX, pytest y pytest-asyncio.

## Requisitos

- Python 3.12 o superior
- Git

## Instalación

```bash
git clone https://github.com/DavidAlejo99/AI-KNOWLEDGE-ASSISTANT.git
cd AI-KNOWLEDGE-ASSISTANT
python3 -m venv .venv
```

## Activar el entorno virtual

macOS / Linux:

```bash
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

## Instalar dependencias

```bash
pip install -e ".[dev]"
```

## Ejecutar la API

```bash
fastapi dev
```

- API: http://127.0.0.1:8000
- Documentación Swagger: http://127.0.0.1:8000/docs

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado del servicio |
| GET | `/api/v1/info` | Información básica del proyecto |
| POST | `/api/v1/chat` | Recibe una pregunta y retorna una respuesta |

Ejemplo de request a `/api/v1/chat`:

```json
{
  "question": "¿Qué es FastAPI?"
}
```

Respuesta:

```json
{
  "answer": "FastAPI es un framework de Python para construir APIs basado en type hints y ASGI.",
  "provider": "bootstrap-local"
}
```

La pregunta debe tener entre 3 y 2000 caracteres; de lo contrario la API responde **HTTP 422**.

## Ejecutar las pruebas

```bash
python -m pytest -q
```

## Scripts de demostración

```bash
python scripts/asyncio_demo.py
python scripts/httpx_demo.py
```

`httpx_demo.py` necesita la API en ejecución (`fastapi dev`) en otra terminal.

## Estructura

```
app/
├── main.py
├── api/routes/     # health, info, chat
├── schemas/        # modelos Pydantic
└── services/       # lógica del asistente
scripts/            # demos de AsyncIO y HTTPX
tests/
├── unit/
└── integration/
```

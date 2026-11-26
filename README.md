# AI Knowledge Assistant

API asíncrona construida con FastAPI que evoluciona por módulos: primero una base validada y probada (Módulo 0), luego la conexión con un LLM real a través de OpenRouter (Módulo I), un agente capaz de usar herramientas (Módulo III) y finalmente conversaciones con memoria persistente en SQLite y guardrails (Módulo 4).

## Tecnologías

Python 3.12+, FastAPI, Pydantic, AsyncIO, HTTPX, SQLite (`sqlite3`), python-dotenv, pytest y pytest-asyncio. Proveedor de modelos: [OpenRouter](https://openrouter.ai).

## Ramas

| Rama | Contenido |
|------|-----------|
| `main` | Módulo 0: API bootstrap (`/health`, `/api/v1/info`, `/api/v1/chat` sin LLM) |
| `feature/module-1-llm-integration` | Módulo I: chat con LLM real, manejo de errores y experimentos |
| `feature/module-3-tool-calling` | Módulo III: agente con herramientas (tool calling) |
| `feature/module-4-memory-guardrails` | Módulo 4: conversaciones con memoria en SQLite y guardrails |

## Requisitos

- Python 3.12 o superior
- Git
- Una API key de OpenRouter (se crea en https://openrouter.ai/settings/keys)

## Instalación

```bash
git clone https://github.com/DavidAlejo99/AI-KNOWLEDGE-ASSISTANT.git
cd AI-KNOWLEDGE-ASSISTANT
git checkout feature/module-4-memory-guardrails
python3 -m venv .venv
```

Activar el entorno virtual:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Instalar dependencias:

```bash
pip install -e ".[dev]"
```

## Configuración

Copia la plantilla y escribe tu API key en `.env`:

```bash
cp .env.example .env
```

```
OPENROUTER_API_KEY=tu-key
OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
MEMORY_DB_PATH=data/conversations.db
MAX_CONTEXT_MESSAGES=8
```

`MEMORY_DB_PATH` es el archivo SQLite donde se guardan las conversaciones (se crea solo) y `MAX_CONTEXT_MESSAGES` es cuántos mensajes recientes se reenvían al modelo en cada turno. La carpeta `data/` también está en `.gitignore`.

El archivo `.env` está en `.gitignore` y nunca debe subirse al repositorio. Para el agente, el modelo debe soportar herramientas (`tools` en sus parámetros soportados).

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
| POST | `/api/v1/chat` | Pregunta directa al LLM |
| POST | `/api/v1/agent/chat` | Agente que puede usar herramientas |
| POST · GET | `/api/v1/conversations` | Crear o listar conversaciones |
| POST | `/api/v1/conversations/{id}/messages` | Turno con memoria y guardrails |
| GET | `/api/v1/conversations/{id}/messages` | Historial guardado |
| POST · GET | `/api/v1/conversations/{id}/memories` | Agregar (máximo 10) o listar memorias |
| DELETE | `/api/v1/conversations/{id}/memories/{memory_id}` | Borrar una memoria |
| DELETE | `/api/v1/conversations/{id}` | Borrar la conversación con sus mensajes y memorias |

### POST /api/v1/chat

```json
{
  "question": "¿Qué es una API REST?",
  "temperature": 0.3,
  "top_p": 1.0,
  "max_tokens": 300
}
```

Respuesta: `{"answer": "...", "model": "modelo que respondió"}`.

### POST /api/v1/agent/chat

Acepta los mismos campos del chat, más `confirm_actions` (por defecto `false`) y `max_steps` (1 a 5, por defecto 3).

```json
{
  "question": "Si estudio 2 horas diarias durante 5 días, ¿cuántas horas estudiaré?"
}
```

Respuesta:

```json
{
  "answer": "Estudiarás un total de 10 horas.",
  "model": "nvidia/nemotron-3-ultra-550b-a55b:free",
  "tools_used": ["calculate_study_hours"]
}
```

Herramientas disponibles:

| Herramienta | Qué hace | ¿Escribe datos? |
|-------------|----------|-----------------|
| `lookup_ai_concept` | Consulta la definición de un concepto de IA | No |
| `calculate_study_hours` | Calcula horas totales de estudio | No |
| `create_study_task` | Crea una tarea de estudio (en memoria) | Sí: requiere `"confirm_actions": true` |
| `estimate_learning_effort` | Estima horas, semanas y nivel de esfuerzo según dificultad, temas y horas por semana | No |

### Conversaciones con memoria (Módulo 4)

1. `POST /api/v1/conversations` devuelve un `conversation_id`.
2. `POST /api/v1/conversations/{id}/messages` acepta los mismos campos del agente y responde con `conversation_id`, `answer`, `model`, `tools_used` y `context_messages` (cuántos mensajes anteriores se enviaron como contexto).

En cada turno, `ConversationService`:

1. Revisa que la conversación exista (404).
2. Aplica el guardrail de entrada (422 si detecta prompt injection, entrada vacía o demasiado larga). Si falla, no se llama al LLM.
3. Reconstruye el contexto desde SQLite: memorias de la conversación y los últimos `MAX_CONTEXT_MESSAGES` mensajes.
4. Ejecuta el agente con herramientas.
5. Aplica el guardrail de salida (502 si la respuesta está vacía o contiene un posible secreto).
6. Solo si todo pasó, guarda la pregunta y la respuesta juntas en una transacción.

Los mensajes `system` y `tool` no se guardan; se reconstruyen en cada llamada.

### Códigos de respuesta

| Código | Significado |
|--------|-------------|
| 200 | Respuesta correcta |
| 201 / 204 | Recurso creado / eliminado |
| 404 | La conversación o la memoria no existe |
| 409 | La conversación ya tiene 10 memorias |
| 422 | Bloqueado por el guardrail de entrada, `conversation_id` que no es un UUID o datos inválidos (por ejemplo, pregunta de menos de 3 caracteres o `temperature` negativa). El LLM no se invoca |
| 502 | Falla del proveedor (timeout, 429, respuesta vacía), el agente no pudo terminar o el guardrail de salida bloqueó la respuesta (no se guarda) |

## Ejecutar las pruebas

```bash
python -m pytest -q
```

Las pruebas usan proveedores falsos (`tests/fakes.py`), `httpx.MockTransport` y bases SQLite temporales. Además, `tests/conftest.py` bloquea el DNS y las conexiones de red en todas las pruebas, así que ninguna puede gastar tokens ni llamar a OpenRouter.

## Scripts

```bash
python scripts/asyncio_demo.py        # ejecución secuencial vs. concurrente
python scripts/httpx_demo.py          # cliente asíncrono (requiere fastapi dev)
python scripts/run_experiments.py exp1 --model nvidia/nemotron-3-ultra-550b-a55b:free
```

`run_experiments.py` ejecuta los experimentos del laboratorio del Módulo I y guarda la bitácora en `experiments/`.

## Estructura

```
app/
├── main.py
├── api/routes/     # health, info, chat, agent, conversations
├── core/           # configuración (.env)
├── guardrails/     # controles de entrada y salida
├── memory/         # repositorio SQLite (conversaciones, mensajes, memorias)
├── providers/      # contrato del proveedor y adaptador OpenRouter
├── schemas/        # modelos Pydantic
├── services/       # asistente, agente y conversación
└── tools/          # herramientas del agente y su registro
data/               # base SQLite local (no se sube)
docs/diagramas/     # diagramas en Excalidraw
experiments/        # bitácora y respuestas del laboratorio del Módulo I
scripts/
tests/
├── unit/
└── integration/
```

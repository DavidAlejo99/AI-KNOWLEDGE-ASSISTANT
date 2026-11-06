# AI Knowledge Assistant

API asíncrona construida con FastAPI que evoluciona por módulos: primero una base validada y probada (Módulo 0), luego la conexión con un LLM real a través de OpenRouter (Módulo I) y finalmente un agente capaz de usar herramientas (Módulo III).

## Tecnologías

Python 3.12+, FastAPI, Pydantic, AsyncIO, HTTPX, python-dotenv, pytest y pytest-asyncio. Proveedor de modelos: [OpenRouter](https://openrouter.ai).

## Ramas

| Rama | Contenido |
|------|-----------|
| `main` | Módulo 0: API bootstrap (`/health`, `/api/v1/info`, `/api/v1/chat` sin LLM) |
| `feature/module-1-llm-integration` | Módulo I: chat con LLM real, manejo de errores y experimentos |
| `feature/module-3-tool-calling` | Módulo III: agente con herramientas (tool calling) |

## Requisitos

- Python 3.12 o superior
- Git
- Una API key de OpenRouter (se crea en https://openrouter.ai/settings/keys)

## Instalación

```bash
git clone https://github.com/DavidAlejo99/AI-KNOWLEDGE-ASSISTANT.git
cd AI-KNOWLEDGE-ASSISTANT
git checkout feature/module-3-tool-calling
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
```

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

### Códigos de respuesta

| Código | Significado |
|--------|-------------|
| 200 | Respuesta correcta |
| 422 | Datos inválidos (por ejemplo, pregunta de menos de 3 caracteres o `temperature` negativa). El LLM no se invoca |
| 502 | Falla del proveedor (timeout, 429, respuesta vacía) o el agente no pudo terminar |

## Ejecutar las pruebas

```bash
python -m pytest -q
```

Las pruebas usan proveedores falsos (`tests/fakes.py`) y `httpx.MockTransport`, así que no consumen la red ni la API key.

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
├── api/routes/     # health, info, chat, agent
├── core/           # configuración (.env)
├── providers/      # contrato del proveedor y adaptador OpenRouter
├── schemas/        # modelos Pydantic
├── services/       # asistente y agente
└── tools/          # herramientas del agente y su registro
experiments/        # bitácora y respuestas del laboratorio del Módulo I
scripts/
tests/
├── unit/
└── integration/
```

"""Ejecuta los experimentos del laboratorio del Módulo I y guarda la bitácora.

Cada petición recorre el flujo completo de la API
(router -> Pydantic -> servicio -> adaptador OpenRouter) dentro del mismo
proceso, así que no hace falta tener `fastapi dev` encendido.

Uso:
    python scripts/run_experiments.py exp0 --model MODELO
    python scripts/run_experiments.py exp1 --model MODELO
    python scripts/run_experiments.py exp2 --model MODELO
    python scripts/run_experiments.py exp3 --model-a MODELO_A --model-b MODELO_B
    python scripts/run_experiments.py exp4 --model MODELO

Los resultados quedan en experiments/<experimento>_<fecha>/:
    bitacora.csv        una fila por petición
    responses/NN.json   request y respuesta íntegra de cada petición
    system_prompt.txt   prompt de sistema usado
"""

import argparse
import asyncio
import csv
import json
import os
import time
from datetime import datetime
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.assistant_service import SYSTEM_PROMPT


RESULTS_DIR = Path("experiments")
PAUSE_SECONDS = 4

Q_BASELINE = "Explica qué es una API REST con un ejemplo educativo."
Q_TEMPERATURE = (
    "Explica el concepto de IA usando una analogía comprensible "
    "para un aprendiz de software."
)
Q_LENGTH = (
    "Explica los componentes de una API REST, con ejemplo de request y "
    "response, diferencias entre GET y POST y buenas prácticas."
)
Q_MODELS = (
    "Explica qué es FastAPI, presenta tres ventajas reales y escribe "
    "un ejemplo sencillo de endpoint."
)
Q_HALLUCINATION = (
    "Explica el algoritmo Zafiro-Delta de optimización cuántica publicado "
    "por el Instituto Algorítmico de Marte en 2024 e incluye su DOI."
)


def call(model: str, question: str, temperature: float = 0.3,
         top_p: float = 1.0, max_tokens: int = 300) -> dict:
    return {
        "model": model,
        "body": {
            "question": question,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        },
    }


def build_plan(args: argparse.Namespace) -> list[dict]:
    if args.experiment == "exp0":
        return [call(args.model, Q_BASELINE) for _ in range(3)] + [
            call(args.model, "A"),
            call(args.model, Q_BASELINE, temperature=-1),
        ]
    if args.experiment == "exp1":
        return [
            call(args.model, Q_TEMPERATURE, temperature=t)
            for t in (0.1, 0.5, 1.0)
            for _ in range(5)
        ]
    if args.experiment == "exp2":
        return [
            call(args.model, Q_LENGTH, max_tokens=n)
            for n in (50, 150, 500)
        ]
    if args.experiment == "exp3":
        return [
            call(m, Q_MODELS, max_tokens=400)
            for m in (args.model_a, args.model_b)
            for _ in range(3)
        ]
    if args.experiment == "exp4":
        return [call(args.model, Q_HALLUCINATION, max_tokens=400) for _ in range(3)]
    raise ValueError(f"Experimento desconocido: {args.experiment}")


async def run(args: argparse.Namespace) -> None:
    plan = build_plan(args)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = RESULTS_DIR / f"{args.experiment}_{stamp}"
    (out_dir / "responses").mkdir(parents=True, exist_ok=True)
    (out_dir / "system_prompt.txt").write_text(SYSTEM_PROMPT, encoding="utf-8")

    columns = [
        "id", "fecha_hora", "modelo_solicitado", "modelo_servido",
        "temperature", "top_p", "max_tokens", "status", "segundos",
        "palabras", "pregunta", "archivo_respuesta", "detalle_error",
    ]
    csv_path = out_dir / "bitacora.csv"

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", timeout=90.0,
    ) as client:
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()

            for i, item in enumerate(plan, start=1):
                os.environ["OPENROUTER_MODEL"] = item["model"]
                body = item["body"]
                started_at = datetime.now().isoformat(timespec="seconds")

                start = time.perf_counter()
                response = await client.post("/api/v1/chat", json=body)
                seconds = round(time.perf_counter() - start, 2)

                data = response.json()
                answer = data.get("answer", "") if response.status_code == 200 else ""
                error = "" if response.status_code == 200 else json.dumps(
                    data.get("detail"), ensure_ascii=False
                )

                file_name = f"responses/{i:02d}.json"
                (out_dir / file_name).write_text(
                    json.dumps(
                        {
                            "id": i,
                            "fecha_hora": started_at,
                            "modelo_solicitado": item["model"],
                            "request": body,
                            "status": response.status_code,
                            "segundos": seconds,
                            "response": data,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )

                writer.writerow({
                    "id": i,
                    "fecha_hora": started_at,
                    "modelo_solicitado": item["model"],
                    "modelo_servido": data.get("model", ""),
                    "temperature": body["temperature"],
                    "top_p": body["top_p"],
                    "max_tokens": body["max_tokens"],
                    "status": response.status_code,
                    "segundos": seconds,
                    "palabras": len(answer.split()),
                    "pregunta": body["question"],
                    "archivo_respuesta": file_name,
                    "detalle_error": error,
                })
                f.flush()

                print(
                    f"[{i}/{len(plan)}] {response.status_code} "
                    f"{seconds}s T={body['temperature']} "
                    f"max={body['max_tokens']} {data.get('model', '')}"
                )

                if response.status_code != 422 and i < len(plan):
                    await asyncio.sleep(PAUSE_SECONDS)

    print(f"\nBitácora guardada en: {csv_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Experimentos del Módulo I")
    parser.add_argument("experiment", choices=["exp0", "exp1", "exp2", "exp3", "exp4"])
    parser.add_argument("--model", default=os.getenv("OPENROUTER_MODEL", "openrouter/free"))
    parser.add_argument("--model-a")
    parser.add_argument("--model-b")
    args = parser.parse_args()

    if args.experiment == "exp3" and not (args.model_a and args.model_b):
        parser.error("exp3 necesita --model-a y --model-b")

    asyncio.run(run(args))


if __name__ == "__main__":
    main()

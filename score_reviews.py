from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter

INPUT_CSV_PATH = Path(r"C:\Users\herrerahe\Downloads\CodeInterpreter.csv")
OUTPUT_CSV_PATH = Path(__file__).with_name("output_reviews.csv")
OUTPUT_REPORT_PATH = Path(__file__).with_name("reporte_producto.txt")

REQUIRED_COLUMNS = {"review", "calificacion"}
FALLBACK_SCORE = 3.0
MAX_SCORE_ATTEMPTS = 2
ALLOWED_SCORES = {value / 2 for value in range(2, 11)}


def require_environment_variable(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"No se encontro {name}. Copia .env.example como .env y agrega tu clave."
        )
    return value


def response_to_text(response: Any) -> str:
    content = getattr(response, "content", response)

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text") or block.get("content")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts).strip()

    return str(content).strip()


def create_model() -> ChatOpenRouter:
    require_environment_variable("OPENROUTER_API_KEY")
    return ChatOpenRouter(
        model="cohere/north-mini-code:free",
        temperature=0.5,
        max_retries=2,
    )


def parse_score(text: str) -> float | None:
    match = re.search(r"\d+(?:\.\d+)?", text)
    if not match:
        return None

    try:
        score = float(match.group(0))
    except ValueError:
        return None

    if score in ALLOWED_SCORES:
        return score
    return None


def score_review(model: ChatOpenRouter, review: str) -> tuple[float, bool]:
    system_prompt = (
        "Eres un analista de sentimiento. Devuelve solo un numero entre 1.0 y 5.0 "
        "en incrementos de 0.5. No agregues texto adicional."
    )

    user_prompt = (
        "Analiza el comentario y asigna puntuacion:\n"
        "1.0-2.0: malo\n"
        "2.5-3.5: neutral\n"
        "4.0-5.0: bueno\n\n"
        "Ejemplos:\n"
        "- Bueno: Me encanto, funciona rapido y se siente de buena calidad.\n"
        "- Neutral: Esta bien por el precio, aunque no tiene nada especial.\n"
        "- Malo: Muy decepcionante, esperaba mucho mas por ese precio.\n\n"
        f"Comentario: {review}\n\n"
        "Responde solo con un valor valido (1.0, 1.5, ..., 5.0)."
    )

    for _ in range(MAX_SCORE_ATTEMPTS):
        response = model.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        score_text = response_to_text(response)
        score = parse_score(score_text)
        if score is not None:
            return score, False

    return FALLBACK_SCORE, True


def build_global_report(
    model: ChatOpenRouter,
    global_average: float,
    processed_rows: int,
    fallback_rows: int,
) -> str:
    prompt = (
        "Genera un reporte breve en espanol sobre la satisfaccion global de un producto. "
        "Incluye interpretacion del resultado y una recomendacion concreta.\n\n"
        f"Promedio global: {global_average:.2f} / 5.00\n"
        f"Reviews procesadas: {processed_rows}\n"
        f"Reviews con fallback de puntuacion LLM: {fallback_rows}\n"
    )

    response = model.invoke(
        [
            {"role": "system", "content": "Eres un analista de experiencia de cliente."},
            {"role": "user", "content": prompt},
        ]
    )
    report = response_to_text(response)
    return report or "No se pudo generar reporte."


def read_input_rows() -> list[dict[str, str]]:
    if not INPUT_CSV_PATH.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {INPUT_CSV_PATH}")

    with INPUT_CSV_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - fieldnames
        if missing:
            missing_columns = ", ".join(sorted(missing))
            raise ValueError(f"Faltan columnas obligatorias en el CSV: {missing_columns}")

        rows: list[dict[str, str]] = []
        for row in reader:
            rows.append(row)

    return rows


def process_rows(model: ChatOpenRouter, rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int, int]:
    output_rows: list[dict[str, str]] = []
    skipped_rows = 0
    fallback_rows = 0

    for row in rows:
        review = (row.get("review") or "").strip()
        raw_calificacion = (row.get("calificacion") or "").strip()

        if not review or not raw_calificacion:
            skipped_rows += 1
            continue

        try:
            calificacion = float(raw_calificacion)
        except ValueError:
            skipped_rows += 1
            continue

        llm_score, used_fallback = score_review(model, review)
        if used_fallback:
            fallback_rows += 1

        promedio = (llm_score + calificacion) / 2

        output_rows.append(
            {
                "review": review,
                "calificacion": f"{calificacion:.2f}",
                "LLM": f"{llm_score:.1f}",
                "promedio": f"{promedio:.2f}",
            }
        )

    return output_rows, skipped_rows, fallback_rows


def write_output_csv(rows: list[dict[str, str]]) -> None:
    with OUTPUT_CSV_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["review", "calificacion", "LLM", "promedio"])
        writer.writeheader()
        writer.writerows(rows)


def write_report(report: str) -> None:
    with OUTPUT_REPORT_PATH.open("w", encoding="utf-8") as file:
        file.write(report.strip() + "\n")


def main() -> None:
    load_dotenv()
    model = create_model()

    rows = read_input_rows()
    processed_rows, skipped_rows, fallback_rows = process_rows(model, rows)

    if not processed_rows:
        raise RuntimeError("No hay filas validas para procesar.")

    global_average = sum(float(row["promedio"]) for row in processed_rows) / len(processed_rows)
    report = build_global_report(model, global_average, len(processed_rows), fallback_rows)

    write_output_csv(processed_rows)
    write_report(report)

    print("Proceso completado.")
    print(f"Entrada: {INPUT_CSV_PATH}")
    print(f"Filas totales: {len(rows)}")
    print(f"Filas procesadas: {len(processed_rows)}")
    print(f"Filas omitidas: {skipped_rows}")
    print(f"Filas con fallback LLM: {fallback_rows}")
    print(f"Promedio global del producto: {global_average:.2f}/5.00")
    print(f"CSV de salida: {OUTPUT_CSV_PATH}")
    print(f"Reporte TXT: {OUTPUT_REPORT_PATH}")


if __name__ == "__main__":
    main()

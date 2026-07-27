"""Chatbot con dos capas: Planeador y Ejecutor."""

from __future__ import annotations

import os
import time
import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter


EXIT_COMMANDS = {"salir", "exit", "quit"}
MAX_HISTORY_TURNS = 10
DEFAULT_MODEL = "openrouter/free"

DEFAULT_SYSTEM_ROLE = ""
SYSTEM_PROMPT_FILE = "system_prompt.txt"
PROMPTS_DIR = "prompts"

# Roles disponibles para ejecutor (sin Arquitecto)
ROLE_KEYWORDS = {
    "Python": {
        "keywords": {"python", "pandas", "dataframe", "numpy", "script", "código", "programación", "función", "clase"},
        "model": "poolside/laguna-m1:free",
        "prompt_file": "prompt_pandas.md"
    },
    "SQL": {
        "keywords": {"sql", "postgres", "postgresql", "database", "query", "consulta", "tabla", "schema", "ddl", "dml"},
        "model": "cohere/north-mini-code:free",
        "prompt_file": "metaprompt_postgresql.md"
    },
    "LLM": {
        "keywords": {"llm", "ia", "ai", "gpt", "modelo", "prompt", "rag", "embeddings", "vector", "generativo", "langchain"},
        "model": "nvidia/nemotron-3-ultra-550b-a55b:free",
        "prompt_file": "prompt_analisis_llm.md"
    }
}

# Modelo para planeador (Arquitecto)
PLANNER_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
PLANNER_PROMPT_FILE = "system_prompt.md"


def load_system_instructions(file_name: str = SYSTEM_PROMPT_FILE) -> str:
    """Load system instructions from a text file located next to this script."""
    file_path = Path(__file__).with_name(file_name)

    try:
        return file_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def load_prompt_file(file_name: str) -> str:
    """Load prompt from prompts directory."""
    file_path = Path(__file__).parent / PROMPTS_DIR / file_name
    
    try:
        return file_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def get_prompt_for_role(role: str) -> str:
    """Get the system prompt for a role."""
    if role in ROLE_KEYWORDS:
        prompt_file = ROLE_KEYWORDS[role]["prompt_file"]
        prompt = load_prompt_file(prompt_file)
        if prompt:
            return prompt
    
    # Default prompt
    return load_system_instructions()


def get_planner_prompt() -> str:
    """Get the planner (Arquitecto) prompt."""
    prompt = load_prompt_file(PLANNER_PROMPT_FILE)
    if prompt:
        return prompt
    return load_system_instructions()


def get_model_for_role(role: str) -> str:
    """Get the model for a role."""
    if role in ROLE_KEYWORDS:
        return ROLE_KEYWORDS[role]["model"]
    return DEFAULT_MODEL


def require_environment_variable(name: str) -> str:
    """Return a required environment variable or raise a clear error."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"No se encontró {name}. "
            "Copia .env.example como .env y agrega tu clave."
        )
    return value


def response_to_text(response: Any) -> str:
    """Convert a LangChain response into plain text."""
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


def trim_history(
    messages: list[dict[str, str]],
    max_turns: int = MAX_HISTORY_TURNS,
) -> list[dict[str, str]]:
    """Keep the system prompt and the most recent chat turns."""
    system_message = messages[:1]
    recent_messages = messages[-(max_turns * 2):]
    return system_message + recent_messages


def create_model(model_name: str) -> ChatOpenRouter:
    """Create the OpenRouter model configured from environment variables."""
    require_environment_variable("OPENROUTER_API_KEY")

    return ChatOpenRouter(
        model=model_name,
        temperature=0.5,
        max_retries=2,
    )


def extract_plan_from_response(response_text: str) -> dict:
    """Extract plan structure from planner response."""
    # Try to extract JSON from response
    try:
        # Look for JSON block
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
            plan = json.loads(json_str)
            return plan
        elif "{" in response_text and "}" in response_text:
            # Try parsing entire response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_str = response_text[json_start:json_end]
            plan = json.loads(json_str)
            return plan
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Fallback: create plan from response text
    return {
        "es_viable": True,
        "rol_asignado": "LLM",
        "plan_ejecucion": response_text,
        "pasos": [response_text],
        "contexto_importante": ""
    }


def planner_phase() -> dict | None:
    """
    FASE PLANEAMIENTO: Interactúa con usuario y genera plan.
    
    Retorna:
        dict con estructura del plan o None si usuario cancela
    """
    load_dotenv()
    
    planner_model = create_model(PLANNER_MODEL)
    planner_prompt = get_planner_prompt()
    
    planner_prompt = f"""{planner_prompt}

## INSTRUCCIONES ESPECIALES PARA MODO PLANEADOR

Eres un Planeador (Arquitecto) cuyo objetivo es:
1. Entender qué necesita el usuario
2. Hacer preguntas de clarificación si es necesario
3. Determinar si es viable resolver la solicitud
4. Asignar el rol correcto (Python, SQL, o LLM)
5. Generar un plan estructurado de ejecución

Roles disponibles:
- Python: Para manipulación de datos, scripts, pandas
- SQL: Para consultas de base de datos, diseño de esquemas
- LLM: Para análisis de contenido, IA, prompts

Responde SIEMPRE en este formato JSON cuando termines de planear:
```json
{{
  "es_viable": true/false,
  "razon_si_no_viable": "Explicación breve si no es viable",
  "rol_asignado": "Python|SQL|LLM",
  "plan_ejecucion": "Descripción detallada del plan",
  "pasos": ["paso 1", "paso 2", ...],
  "contexto_importante": "Información relevante para el ejecutor"
}}
```

Si necesitas aclarar algo, pregunta al usuario naturalmente antes del JSON final."""

    messages: list[dict[str, str]] = [
        {"role": "system", "content": planner_prompt}
    ]

    print("\n" + "="*70)
    print("[FASE PLANEAMIENTO] - Analizando tu solicitud")
    print("="*70 + "\n")

    while True:
        try:
            user_input = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[PLANEADOR] Hasta luego.")
            return None

        if not user_input:
            continue

        if user_input.lower() in EXIT_COMMANDS:
            print("[PLANEADOR] Hasta luego.")
            return None

        messages.append({"role": "user", "content": user_input})

        try:
            response = planner_model.invoke(messages)
            bot_text = response_to_text(response)

            if not bot_text:
                bot_text = "No se recibió contenido del modelo."

            print(f"\n[Planeador]: {bot_text}\n")
            messages.append({"role": "assistant", "content": bot_text})
            messages = trim_history(messages)

            # Check if plan is ready (contains JSON)
            if "```json" in bot_text or ("es_viable" in bot_text and "rol_asignado" in bot_text):
                plan = extract_plan_from_response(bot_text)
                
                if plan.get("es_viable") == False:
                    print(f"\n[PLANEADOR] ❌ No es viable: {plan.get('razon_si_no_viable', 'Sin detalles')}")
                    print("[PLANEADOR] Por favor, reformula tu solicitud o intenta con algo diferente.\n")
                    messages = messages[:-2]  # Remover último mensaje del usuario
                else:
                    print(f"\n[PLANEADOR] ✓ Plan generado. Rol asignado: {plan.get('rol_asignado')}")
                    return plan

            time.sleep(1)

        except Exception as error:
            error_text = str(error)
            print(f"\n[ERROR Planeador]: {error_text}\n")

            if "Insufficient credits" in error_text:
                print("Tu cuenta de OpenRouter no tiene créditos habilitados.\n")

            if messages and messages[-1].get("role") == "user":
                messages.pop()


def executor_phase(plan: dict) -> None:
    """
    FASE EJECUCIÓN: Ejecuta el plan con el rol asignado.
    
    Args:
        plan: Diccionario con estructura del plan
    """
    load_dotenv()
    
    role_asignado = plan.get("rol_asignado", "LLM")
    modelo_ejecutor = get_model_for_role(role_asignado)
    executor_model = create_model(modelo_ejecutor)
    executor_prompt = get_prompt_for_role(role_asignado)

    # Preparar prompt inicial para ejecutor con el plan
    plan_context = f"""Plan de Ejecución:
{plan.get('plan_ejecucion', '')}

Pasos a seguir:
{chr(10).join(f"- {paso}" for paso in plan.get('pasos', []))}

Contexto importante:
{plan.get('contexto_importante', 'N/A')}"""

    executor_prompt = f"""{executor_prompt}

## CONTEXTO DEL PLAN
{plan_context}

Tu tarea es ejecutar este plan paso a paso, interactuando con el usuario según sea necesario."""

    messages: list[dict[str, str]] = [
        {"role": "system", "content": executor_prompt},
        {"role": "assistant", "content": f"Entendido. Voy a ejecutar el plan asignado.\n\nPlan:\n{plan_context}"}
    ]

    print("\n" + "="*70)
    print(f"[FASE EJECUCIÓN] - Usando rol: {role_asignado}")
    print(f"Modelo: {modelo_ejecutor}")
    print("="*70 + "\n")

    print(f"[Ejecutor]: Entendido. Voy a ejecutar el plan asignado.\n\nPlan:\n{plan_context}\n")

    turn_count = 0
    
    while True:
        try:
            user_input = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[Ejecutor] Hasta luego.")
            break

        if not user_input:
            continue

        if user_input.lower() in EXIT_COMMANDS:
            print("[Ejecutor] Hasta luego.")
            break

        turn_count += 1
        messages.append({"role": "user", "content": user_input})

        try:
            response = executor_model.invoke(messages)
            bot_text = response_to_text(response)

            if not bot_text:
                bot_text = "No se recibió contenido del modelo."

            print(f"\n[{role_asignado}]: {bot_text}\n")
            messages.append({"role": "assistant", "content": bot_text})
            messages = trim_history(messages)

            time.sleep(1)

        except Exception as error:
            error_text = str(error)
            print(f"\n[ERROR Ejecutor]: {error_text}\n")

            if "Insufficient credits" in error_text:
                print("Tu cuenta de OpenRouter no tiene créditos habilitados.\n")

            if "unavailable for free" in error_text.lower():
                print(f"El modelo {modelo_ejecutor} no está disponible en tier free.\n")

            if messages and messages[-1].get("role") == "user":
                messages.pop()


def main() -> None:
    """Sistema de dos capas: Planeador → Ejecutor."""
    load_dotenv()
    
    print("\n" + "="*70)
    print("CHATBOT CON PLANEADOR Y EJECUTOR")
    print("="*70)
    print("Escribe 'salir' en cualquier momento para terminar.\n")

    while True:
        # FASE PLANEAMIENTO
        plan = planner_phase()
        
        if plan is None:
            break
        
        # FASE EJECUCIÓN
        executor_phase(plan)
        
        # Preguntar si continuar
        print("\n" + "="*70)
        try:
            continuar = input("¿Deseas hacer otra solicitud? (s/n): ").strip().lower()
            if continuar not in {"s", "si", "yes", "y"}:
                print("Hasta luego.")
                break
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break


if __name__ == "__main__":
    main()

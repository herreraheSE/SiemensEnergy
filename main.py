from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_openrouter import ChatOpenRouter


EXIT_COMMANDS = {"salir", "exit", "quit"}
MAX_HISTORY_TURNS = 10
DEFAULT_MODEL = "openrouter/free"
FREE_MODELS_ENV = "OPENROUTER_FREE_MODELS"

DEFAULT_SYSTEM_ROLE = ""
SYSTEM_PROMPT_FILE = "system_prompt.txt"
PROMPTS_DIR = "prompts"

# Palabras clave por tema
TOPIC_KEYWORDS = {
    "postgresql": {
        "keywords": {"sql", "postgres", "postgresql", "database", "tabla", "query", "consulta", "ddl", "dml", "schema"},
        "prompt_file": "metaprompt_postgresql.md"
    },
    "llm": {
        "keywords": {"llm", "ia", "ai", "gpt", "modelo", "prompt", "rag", "embeddings", "vector", "generativo"},
        "prompt_file": "prompt_analisis_llm.md"
    },
    "pandas": {
        "keywords": {"pandas", "python", "dataframe", "csv", "data", "numpy", "excel", "series", "df"},
        "prompt_file": "prompt_pandas.md"
    }
}


def load_system_instructions(file_name: str = SYSTEM_PROMPT_FILE) -> str:
    """Load system instructions from a text file located next to this script."""
    file_path = Path(__file__).with_name(file_name)

    try:
        return file_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def detect_topic(user_input: str) -> str | None:
    """Detect the topic based on keywords in user input."""
    text_lower = user_input.lower()
    
    for topic, config in TOPIC_KEYWORDS.items():
        if any(keyword in text_lower for keyword in config["keywords"]):
            return topic
    
    return None


def load_prompt_file(file_name: str) -> str:
    """Load prompt from prompts directory."""
    file_path = Path(__file__).parent / PROMPTS_DIR / file_name
    
    try:
        return file_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def get_system_prompt_for_topic(topic: str | None) -> str:
    """Get the system prompt for the detected topic."""
    if topic and topic in TOPIC_KEYWORDS:
        prompt_file = TOPIC_KEYWORDS[topic]["prompt_file"]
        prompt = load_prompt_file(prompt_file)
        if prompt:
            return prompt
    
    # Default prompt
    return load_system_instructions()


def build_system_prompt(role: str, instructions: str) -> str:
    """Build a system prompt with a variable role and fixed instructions."""
    return f"{role.strip()}\n\n{instructions.strip()}".strip()


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


def get_model_candidates() -> list[str]:
    """Build a de-duplicated model candidate list from environment variables."""
    configured_model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    fallback_raw = os.getenv(FREE_MODELS_ENV, "")
    fallback_models = [m.strip() for m in fallback_raw.split(",") if m.strip()]

    candidates: list[str] = []
    for model_name in [configured_model, *fallback_models]:
        if model_name not in candidates:
            candidates.append(model_name)

    return candidates


def create_model(model_name: str) -> ChatOpenRouter:
    """Create the OpenRouter model configured from environment variables."""
    require_environment_variable("OPENROUTER_API_KEY")

    return ChatOpenRouter(
        model=model_name,
        temperature=0.5,
        max_retries=2,
    )


def main() -> None:
    """Run the terminal chatbot with dynamic system prompts based on topic."""
    load_dotenv()
    model_candidates = get_model_candidates()
    active_model_index = 0
    model_name = model_candidates[active_model_index]
    model = create_model(model_name)

    role = os.getenv("SYSTEM_ROLE", DEFAULT_SYSTEM_ROLE).strip() or DEFAULT_SYSTEM_ROLE
    default_instructions = load_system_instructions()
    
    # Initial system prompt (generic)
    current_topic: str | None = None
    system_prompt = build_system_prompt(role, default_instructions)

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt}
    ]

    print(
        "Mi primer Chatbot vía OpenRouter.\n"
        f"Modelo: {model_name}\n"
        "Escribe 'salir' para terminar.\n"
        "El sistema detectará automáticamente si preguntas sobre SQL, IA/LLM, Pandas o desarrollo general.\n"
    )

    while True:
        try:
            user_input = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break

        if not user_input:
            continue

        if user_input.lower() in EXIT_COMMANDS:
            print("Hasta luego.")
            break

        # Detect topic from user input
        detected_topic = detect_topic(user_input)
        
        # Update system prompt if topic changed
        if detected_topic != current_topic:
            current_topic = detected_topic
            new_system_prompt = get_system_prompt_for_topic(detected_topic)
            system_prompt = build_system_prompt(role, new_system_prompt)
            
            # Update system message in conversation
            messages[0] = {"role": "system", "content": system_prompt}
            
            if detected_topic:
                print(f"[Sistema detectó: {detected_topic.upper()}]\n")

        messages.append({"role": "user", "content": user_input})

        try:
            response = model.invoke(messages)
            bot_text = response_to_text(response)

            if not bot_text:
                bot_text = "No se recibió contenido del modelo."

            print(f"Bot: {bot_text}\n")
            messages.append({"role": "assistant", "content": bot_text})
            messages = trim_history(messages)

            time.sleep(2)

        except Exception as error:
            error_text = str(error)

            if "unavailable for free" in error_text.lower():
                recovered = False

                for next_index in range(active_model_index + 1, len(model_candidates)):
                    next_model_name = model_candidates[next_index]

                    try:
                        model = create_model(next_model_name)
                        response = model.invoke(messages)
                        bot_text = response_to_text(response) or "No se recibió contenido del modelo."

                        print(
                            "El modelo actual no está disponible en free. "
                            f"Cambiando automáticamente a: {next_model_name}\n"
                        )
                        print(f"Bot: {bot_text}\n")

                        messages.append({"role": "assistant", "content": bot_text})
                        messages = trim_history(messages)
                        active_model_index = next_index
                        model_name = next_model_name
                        recovered = True
                        time.sleep(2)
                        break
                    except Exception:
                        continue

                if recovered:
                    continue

            print(f"Error al consultar OpenRouter: {error_text}\n")

            if "Insufficient credits" in error_text:
                print(
                    "Tu cuenta de OpenRouter no tiene créditos habilitados para esta API key.\n"
                    "Verifica que la key pertenezca a la cuenta correcta o revisa la política actual de uso free en OpenRouter.\n"
                )

            if "unavailable for free" in error_text.lower():
                print(
                    "Ese modelo dejó de estar disponible en tier free.\n"
                    f"Configura OPENROUTER_MODEL o {FREE_MODELS_ENV} en tu .env con modelos gratuitos alternativos.\n"
                    "Ejemplo: OPENROUTER_FREE_MODELS=modelo1:free,modelo2:free\n"
                )

            if messages and messages[-1].get("role") == "user":
                messages.pop()


if __name__ == "__main__":
    main()

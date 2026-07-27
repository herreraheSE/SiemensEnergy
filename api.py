"""
FastAPI server for ChatDev Assistant with WebSocket support.
Integrates planner_phase() and executor_phase() from main.py.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt
import json
import os
import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

# Import core functions from main.py
from main import (
    planner_phase as sync_planner_phase,
    executor_phase as sync_executor_phase,
    get_planner_prompt,
    get_prompt_for_role,
    get_model_for_role,
    create_model,
    response_to_text,
    trim_history,
    extract_plan_from_response,
    ROLE_KEYWORDS,
    PLANNER_MODEL,
    MAX_HISTORY_TURNS,
)

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production-min-32-bytes")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DATABASE_FILE = "chat_history.db"

# Initialize FastAPI app
app = FastAPI(title="ChatDev API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    token: str
    token_type: str = "bearer"

# Database functions
def init_database():
    """Initialize chat history database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT,
            phase TEXT,
            model TEXT,
            role_assigned TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
    """)
    
    conn.commit()
    conn.close()

def save_message(
    session_id: str, 
    role: str, 
    content: str, 
    phase: Optional[str] = None, 
    model: Optional[str] = None,
    role_assigned: Optional[str] = None
):
    """Save message to database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    msg_id = str(datetime.now().timestamp())
    cursor.execute("""
        INSERT INTO messages (id, session_id, role, content, phase, model, role_assigned)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (msg_id, session_id, role, content, phase, model, role_assigned))
    
    conn.commit()
    conn.close()

# JWT functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> str:
    """Verify JWT token and return email."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return email
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# API Routes
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_database()
    load_dotenv()

@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login endpoint - accepts any email/password for demo.
    In production, verify against actual user database.
    """
    # Demo: Accept any credentials
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.email},
        expires_delta=access_token_expires
    )
    return {"token": access_token}

@app.post("/auth/token", response_model=TokenResponse)
async def refresh_token(token: str):
    """Refresh JWT token."""
    email = verify_token(token)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": email},
        expires_delta=access_token_expires
    )
    return {"token": access_token}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Async/WebSocket versions of planner and executor
async def async_planner_phase(
    websocket: WebSocket,
    session_id: str,
    email: str,
    messages: list[dict[str, str]],
) -> tuple[dict | None, list[dict[str, str]]]:
    """
    Async version of planner_phase for WebSocket.
    Handles conversation with user until plan is generated.
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

    messages = [
        {"role": "system", "content": planner_prompt}
    ]

    # Notificar fase de planeamiento
    await websocket.send_text(json.dumps({
        "type": "phase_change",
        "payload": {
            "phase": "planeamiento",
            "role": "Planner",
            "model": PLANNER_MODEL
        }
    }))

    # Enviar mensaje de bienvenida
    welcome_msg = "¡Hola! Soy ChatDev, tu asistente de desarrollo AI.\n\n¿Qué necesitas que haga? Puedo:\n• Crear scripts Python\n• Diseñar queries SQL\n• Analizar y procesar datos\n• Resolver problemas de programación\n\nDescribe tu solicitud:"
    
    await websocket.send_text(json.dumps({
        "type": "message",
        "payload": {
            "role": "planner",
            "content": welcome_msg,
            "phase": "planeamiento",
            "model": PLANNER_MODEL
        }
    }))

    while True:
        # Esperar mensaje del usuario
        user_input = None
        try:
            data = await websocket.receive_text()
            message_obj = json.loads(data)
            user_input = message_obj.get("payload", {}).get("content", "").strip()
        except Exception as e:
            print(f"Error recibiendo mensaje: {e}")
            return None, messages

        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})
        save_message(session_id, "user", user_input, phase="planeamiento")

        try:
            # Invocar modelo planeador
            response = planner_model.invoke(messages)
            bot_text = response_to_text(response)

            if not bot_text:
                bot_text = "No se recibió contenido del modelo."

            # Guardar respuesta del planeador
            save_message(
                session_id, 
                "planner", 
                bot_text, 
                phase="planeamiento",
                model=PLANNER_MODEL
            )

            # Enviar respuesta del planeador al frontend
            await websocket.send_text(json.dumps({
                "type": "message",
                "payload": {
                    "role": "planner",
                    "content": bot_text,
                    "phase": "planeamiento",
                    "model": PLANNER_MODEL
                }
            }))

            messages.append({"role": "assistant", "content": bot_text})
            messages = trim_history(messages)

            # Verificar si el plan está listo
            if "```json" in bot_text or ("es_viable" in bot_text and "rol_asignado" in bot_text):
                plan = extract_plan_from_response(bot_text)
                
                if plan.get("es_viable") == False:
                    # Plan no es viable, continuar conversación
                    error_msg = f"❌ No es viable: {plan.get('razon_si_no_viable', 'Sin detalles')}"
                    await websocket.send_text(json.dumps({
                        "type": "message",
                        "payload": {
                            "role": "planner",
                            "content": error_msg,
                            "phase": "planeamiento",
                            "model": PLANNER_MODEL
                        }
                    }))
                    messages = messages[:-2]  # Remover último mensaje
                else:
                    # Plan válido, retornar
                    plan_msg = f"✓ Plan generado. Rol asignado: {plan.get('rol_asignado')}"
                    await websocket.send_text(json.dumps({
                        "type": "plan",
                        "payload": {
                            "plan": plan,
                            "content": plan_msg
                        }
                    }))
                    return plan, messages

            await asyncio.sleep(0.5)

        except Exception as error:
            error_text = str(error)
            print(f"Error en planeador: {error_text}")
            
            if "Insufficient credits" in error_text:
                error_text = "Tu cuenta de OpenRouter no tiene créditos habilitados."

            await websocket.send_text(json.dumps({
                "type": "error",
                "payload": {"message": error_text}
            }))

            if messages and messages[-1].get("role") == "user":
                messages.pop()

            await asyncio.sleep(1)


async def async_executor_phase(
    websocket: WebSocket,
    session_id: str,
    plan: dict,
    messages: list[dict[str, str]],
) -> None:
    """
    Async version of executor_phase for WebSocket.
    Executes the plan and handles conversation with user.
    """
    load_dotenv()
    
    role_asignado = plan.get("rol_asignado", "LLM")
    modelo_ejecutor = get_model_for_role(role_asignado)
    executor_model = create_model(modelo_ejecutor)
    executor_prompt = get_prompt_for_role(role_asignado)

    # Preparar contexto del plan
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

    messages = [
        {"role": "system", "content": executor_prompt},
        {
            "role": "assistant", 
            "content": f"Entendido. Voy a ejecutar el plan asignado.\n\nPlan:\n{plan_context}"
        }
    ]

    # Notificar fase de ejecución
    await websocket.send_text(json.dumps({
        "type": "phase_change",
        "payload": {
            "phase": "ejecucion",
            "role": role_asignado,
            "model": modelo_ejecutor
        }
    }))

    # Enviar mensaje inicial del ejecutor
    initial_message = f"Entendido. Voy a ejecutar el plan asignado.\n\nPlan:\n{plan_context}"
    await websocket.send_text(json.dumps({
        "type": "message",
        "payload": {
            "role": "executor",
            "content": initial_message,
            "phase": "ejecucion",
            "model": modelo_ejecutor,
            "role_assigned": role_asignado
        }
    }))

    save_message(
        session_id,
        "executor",
        initial_message,
        phase="ejecucion",
        model=modelo_ejecutor,
        role_assigned=role_asignado
    )

    while True:
        try:
            # Esperar mensaje del usuario
            data = await websocket.receive_text()
            message_obj = json.loads(data)
            user_input = message_obj.get("payload", {}).get("content", "").strip()

            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input})
            save_message(
                session_id,
                "user",
                user_input,
                phase="ejecucion"
            )

            # Invocar modelo ejecutor
            response = executor_model.invoke(messages)
            bot_text = response_to_text(response)

            if not bot_text:
                bot_text = "No se recibió contenido del modelo."

            # Guardar y enviar respuesta del ejecutor
            save_message(
                session_id,
                "executor",
                bot_text,
                phase="ejecucion",
                model=modelo_ejecutor,
                role_assigned=role_asignado
            )

            await websocket.send_text(json.dumps({
                "type": "message",
                "payload": {
                    "role": "executor",
                    "content": bot_text,
                    "phase": "ejecucion",
                    "model": modelo_ejecutor,
                    "role_assigned": role_asignado
                }
            }))

            messages.append({"role": "assistant", "content": bot_text})
            messages = trim_history(messages)

            await asyncio.sleep(0.5)

        except WebSocketDisconnect:
            print(f"WebSocket desconectado para sesión {session_id}")
            break
        except Exception as error:
            error_text = str(error)
            print(f"Error en ejecutor: {error_text}")

            if "Insufficient credits" in error_text:
                error_text = "Tu cuenta de OpenRouter no tiene créditos habilitados."

            if "unavailable for free" in error_text.lower():
                error_text = f"El modelo {modelo_ejecutor} no está disponible en tier free."

            await websocket.send_text(json.dumps({
                "type": "error",
                "payload": {"message": error_text}
            }))

            if messages and messages[-1].get("role") == "user":
                messages.pop()

            await asyncio.sleep(1)


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for real-time chat with two-phase architecture.
    Requires JWT token as query parameter.
    
    Flow:
    1. Connect with valid JWT token
    2. Planner phase: User describes task, planner generates plan
    3. Executor phase: Executor implements the plan
    """
    # Verify token
    try:
        email = verify_token(token)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    
    # Create session
    session_id = str(time.time())
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (id, email) VALUES (?, ?)",
        (session_id, email)
    )
    conn.commit()
    conn.close()

    print(f"✓ Sesión iniciada: {session_id} ({email})")

    try:
        while True:
            # FASE PLANEAMIENTO
            print(f"📍 Iniciando fase planeamiento para {session_id}")
            plan, messages = await async_planner_phase(
                websocket,
                session_id,
                email,
                []
            )
            
            if plan is None:
                break
            
            # FASE EJECUCIÓN
            await async_executor_phase(
                websocket,
                session_id,
                plan,
                messages
            )
            
            # Preguntar si continuar
            await websocket.send_text(json.dumps({
                "type": "continue_prompt",
                "payload": {"message": "¿Deseas hacer otra solicitud?"}
            }))

    except WebSocketDisconnect:
        print(f"✗ Sesión terminada: {session_id}")
    except Exception as e:
        print(f"Error en WebSocket: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "payload": {"message": str(e)}
            }))
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

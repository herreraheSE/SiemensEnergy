# ChatDev - Full Stack Architecture

## 📋 Descripción General

ChatDev es un asistente de desarrollo AI con arquitectura de dos capas:
1. **Planner (Arquitecto)**: Analiza solicitudes y genera planes
2. **Executor (Especialista)**: Ejecuta el plan con el modelo apropiado

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────┐
│                React Web Frontend                    │
│              (Vite + React + TailwindCSS)            │
│         • Chat Interface                             │
│         • Real-time WebSocket Communication          │
│         • JWT Authentication                         │
│         • Dark/Light Theme                           │
│         • Chat History Export                        │
└──────────────┬──────────────────────────────────────┘
               │ WSS (WebSocket Secure)
               │ JWT Token Validation
               │
┌──────────────▼──────────────────────────────────────┐
│           FastAPI Backend (Python)                   │
│            • JWT Token Generation                    │
│            • WebSocket Server                        │
│            • Chat History (SQLite)                   │
│            • CORS Middleware                         │
└──────────────┬──────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────┐
│        ChatDev Core Logic (main.py)                  │
│  • Planner Phase: nvidia/nemotron-3-ultra-550b      │
│  • Python Executor: poolside/laguna-m1              │
│  • SQL Executor: cohere/north-mini-code             │
│  • LLM Executor: nvidia/nemotron-3-ultra-550b       │
└──────────────┬──────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────┐
│      OpenRouter LLM API (Free Tier)                  │
│    https://openrouter.ai/api/v1/chat/completions   │
└────────────────────────────────────────────────────┘
```

## 📁 Estructura del Proyecto

```
SiemensEnergy/
├── main.py                  # Core logic (Planner + Executor)
├── api.py                   # FastAPI server (NEW)
├── db_utils.py             # Database utilities
├── init_db.py              # Database initialization
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
├── system_prompt.txt       # Architect prompt
│
├── prompts/                # Role-specific prompts
│   ├── system_prompt.md    # Planner (Architect)
│   ├── prompt_pandas.md    # Python Executor
│   ├── metaprompt_postgresql.md  # SQL Executor
│   └── prompt_analisis_llm.md    # LLM Executor
│
├── chatdev/                # React Frontend (NEW)
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── App.jsx
│   │   │   ├── LoginView.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   ├── ChatView.jsx
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── PhaseIndicator.jsx
│   │   │   └── ThemeToggle.jsx
│   │   ├── stores/         # Zustand state management
│   │   │   └── store.js
│   │   ├── utils/          # Utilities
│   │   │   └── wsService.js
│   │   ├── main.jsx
│   │   └── index.css
│   ├── public/             # Static assets
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── eslint.config.js
│   ├── .env.example
│   ├── .gitignore
│   ├── README.md
│   └── index.html
│
└── run_windows.cmd         # Setup script (Windows)
```

## 🚀 Quick Start

### Requisitos
- Python 3.14
- Node.js 16+
- OpenRouter API Key (free tier)

### 1. Setup Backend

```bash
# Crear archivo .env
copy .env.example .env
# Editar .env con tu OPENROUTER_API_KEY

# Instalar dependencias Python
pip install -r requirements.txt

# Inicializar base de datos
python init_db.py

# Ejecutar servidor FastAPI
python api.py
# Accesible en: http://localhost:8000
```

### 2. Setup Frontend

```bash
cd chatdev

# Instalar dependencias Node
npm install

# Crear archivo .env
copy .env.example .env.local

# Ejecutar servidor de desarrollo Vite
npm run dev
# Accesible en: http://localhost:5173
```

### 3. Usar ChatDev

1. Abrir http://localhost:5173 en el navegador
2. Login con cualquier email/contraseña (demo)
3. Crear nuevo chat
4. Escribir solicitudes
5. Ver [PLANEAMIENTO] → [EJECUCIÓN] en tiempo real
6. Exportar conversación

## 🔐 Autenticación

### JWT Flow
```
1. Frontend: POST /auth/login con email/password
   └─> Backend genera JWT token (30 min expiry)

2. Frontend: WebSocket /ws?token=<JWT_TOKEN>
   └─> Backend valida JWT en conexión

3. Frontend: Usa token para todas las operaciones
   └─> Refresca si expira (POST /auth/token)
```

### Environment Variables

**Backend (.env)**
```
OPENROUTER_API_KEY=sk-or-...
SECRET_KEY=your-secret-key-change-this
```

**Frontend (.env.local)**
```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/api/ws
```

## 📊 Base de Datos

### Schema SQLite

**sessions**
```
id          TEXT PRIMARY KEY
created_at  TIMESTAMP
updated_at  TIMESTAMP
```

**messages**
```
id          TEXT PRIMARY KEY
session_id  TEXT (FK → sessions.id)
role        TEXT ('user', 'planner', 'executor')
content     TEXT
phase       TEXT ('planeamiento', 'ejecucion')
model       TEXT (model name)
timestamp   TIMESTAMP
```

## 🔄 Flujo de Ejecución

### Paso 1: User Request
```json
{
  "type": "user_message",
  "payload": {
    "chatId": "123456",
    "content": "Crea un script Python que lea un CSV y calcule estadísticas"
  }
}
```

### Paso 2: Planner Phase
```python
# Backend llama planner_phase()
plan = {
  "es_viable": true,
  "rol_asignado": "Python",
  "plan_ejecucion": "Usar pandas para leer CSV...",
  "pasos": ["Cargar archivo", "Calcular stats", "Mostrar resultados"],
  "contexto_importante": "..."
}
```

Frontend recibe:
```json
{
  "type": "phase_change",
  "payload": {
    "phase": "planeamiento",
    "role": "Python",
    "model": "poolside/laguna-m1"
  }
}
```

### Paso 3: Executor Phase
```python
# Backend llama executor_phase(plan)
# Usa modelo Python para ejecutar plan
response = ChatOpenRouter.invoke([
  {"role": "system", "content": "Eres un experto en Python..."},
  {"role": "user", "content": "Plan: ..."}
])
```

Frontend recibe:
```json
{
  "type": "message",
  "payload": {
    "type": "executor",
    "content": "# Script Python\n```python\nimport pandas as pd...",
    "phase": "ejecucion",
    "model": "poolside/laguna-m1",
    "role": "Python"
  }
}
```

## 🎨 UI Features

### Chat Interface
- ✅ User/AI message bubbles
- ✅ Phase indicators [PLANEAMIENTO]/[EJECUCIÓN]
- ✅ Model and role information
- ✅ Timestamps (relative)
- ✅ Expandable JSON plan viewer
- ✅ Loading animations

### Sidebar
- ✅ New chat button
- ✅ Chat list with timestamps
- ✅ Delete chat
- ✅ Load chat history
- ✅ Logout button

### Features
- ✅ Dark/Light mode toggle
- ✅ Export to text file
- ✅ Real-time WebSocket updates
- ✅ Responsive design (mobile-friendly)
- ✅ JWT token refresh
- ✅ Connection status indicator

## 📝 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/login | Login and get JWT token |
| POST | /auth/token | Refresh JWT token |
| GET | /health | Health check |
| WS | /ws | WebSocket chat endpoint |

## 🧪 Testing

### Backend
```bash
# Test con curl (obtener token)
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'

# Health check
curl http://localhost:8000/health
```

### Frontend
```bash
# Ejecutar en modo desarrollo
npm run dev

# Build para producción
npm run build

# Preview de build
npm run preview
```

## 🐛 Troubleshooting

### WebSocket Connection Failed
- ✓ Verificar que backend está en puerto 8000
- ✓ Verificar JWT token es válido
- ✓ Verificar CORS está habilitado

### Messages No Appear
- ✓ Abrir DevTools → Network → WS
- ✓ Verificar que llegan mensajes al WebSocket
- ✓ Verificar que el store de Zustand actualiza

### API Key Not Working
- ✓ Verificar .env contiene OPENROUTER_API_KEY
- ✓ Verificar que la key es válida en openrouter.ai
- ✓ Verificar que no tiene caracteres extra (espacios, comillas)

## 📚 Recursos

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Vite Docs](https://vitejs.dev/)
- [React Docs](https://react.dev/)
- [TailwindCSS Docs](https://tailwindcss.com/)
- [Zustand Docs](https://github.com/pmndrs/zustand)
- [OpenRouter API](https://openrouter.ai/api/v1)

## 📄 Licencia

Este proyecto es parte del curso de IA de Siemens Energy.

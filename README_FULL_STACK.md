# ChatDev - Full Stack Application

Asistente de IA con arquitectura de dos capas (Planeador + Ejecutor) con interfaz web moderna.

## ⚡ Inicio Rápido

### Requisitos Previos
- Python 3.14+
- Node.js 16+
- OpenRouter API Key (gratis en https://openrouter.ai)

### 1️⃣ Setup Backend

```bash
# Crear archivo .env desde plantilla
copy .env.example .env

# Editar .env y agregar tu OPENROUTER_API_KEY
# OPENROUTER_API_KEY=sk-or-...

# Instalar dependencias Python
pip install -r requirements.txt
```

### 2️⃣ Setup Frontend

```bash
cd chatdev

# Instalar dependencias Node
npm install

# Crear archivo .env.local (opcional)
copy .env.example .env.local
```

### 3️⃣ Ejecutar la Aplicación

**Opción 1: Script automático (Windows)**
```bash
# En la raíz del proyecto
start_dev.cmd
```

**Opción 2: Manual en 2 terminales**

Terminal 1 (Backend):
```bash
python api.py
# Estará en: http://localhost:8000
```

Terminal 2 (Frontend):
```bash
cd chatdev
npm run dev
# Estará en: http://localhost:5173
```

## 🌐 Acceso

- **Frontend:** http://localhost:5173
- **Backend:** http://localhost:8000
- **Docs API:** http://localhost:8000/docs

## 🔑 Autenticación

1. Abre http://localhost:5173
2. Ingresa cualquier email y contraseña (demo)
3. El sistema genera un JWT token automáticamente
4. WebSocket se conecta de forma segura con el token

## 💬 Cómo Usar

1. **Crear Chat:** Click en "Nuevo Chat"
2. **Escribir Solicitud:** Describe qué necesitas (Python, SQL, análisis, etc)
3. **Planeamiento:** El Arquitecto analiza y genera un plan
4. **Ejecución:** El Especialista (Python/SQL/LLM) ejecuta el plan
5. **Exportar:** Descarga la conversación como archivo .txt

## 📊 Arquitectura

### Backend (FastAPI)
- `api.py` - Servidor WebSocket + JWT + SQLite
- Importa funciones de `main.py`
- Endpoints:
  - `POST /auth/login` - Autenticación
  - `POST /auth/token` - Refresh token
  - `GET /health` - Health check
  - `WS /ws` - WebSocket chat

### Frontend (React + Vite)
- **chatdev/src/components/:**
  - `LoginView.jsx` - Formulario de login
  - `ChatView.jsx` - Interfaz principal
  - `Sidebar.jsx` - Historial de chats
  - `MessageBubble.jsx` - Mensajes con fases
  - `PhaseIndicator.jsx` - Indicador [PLANEAMIENTO]/[EJECUCIÓN]
  - `ThemeToggle.jsx` - Modo oscuro/claro

- **chatdev/src/stores/:**
  - `store.js` - Zustand global state

- **chatdev/src/utils/:**
  - `wsService.js` - WebSocket client

### Core (Python)
- `main.py` - Lógica Planner + Executor
- `db_utils.py` - Utilidades de base de datos
- `init_db.py` - Inicialización de BD

## 🔄 Flujo de Ejecución

```
1. Usuario inicia sesión
   └─> JWT token generado

2. Crea nuevo chat
   └─> Sesión creada en BD

3. Escribe solicitud
   └─> Mensaje enviado por WebSocket

4. FASE PLANEAMIENTO
   ├─> Planner analiza solicitud
   ├─> Puede hacer preguntas de clarificación
   └─> Genera plan JSON con rol asignado

5. FASE EJECUCIÓN
   ├─> Especialista recibe plan
   ├─> Ejecuta paso a paso
   ├─> Conversa con usuario si es necesario
   └─> Itera hasta completar

6. Nuevo ciclo o logout
```

## 📁 Base de Datos

Almacenada en `chat_history.db` (SQLite)

**Tablas:**
- `sessions`: chat_id, email, timestamps
- `messages`: message_id, session_id, role, content, phase, model, timestamp

**Ejemplo de consulta:**
```sql
SELECT role, content, phase, model 
FROM messages 
WHERE session_id = '...' 
ORDER BY timestamp;
```

## 🎨 Características UI

- ✅ Chat en tiempo real (WebSocket)
- ✅ Indicadores de fase [PLANEAMIENTO]/[EJECUCIÓN]
- ✅ Información de modelo y rol
- ✅ Visor JSON del plan (expandible)
- ✅ Modo oscuro/claro (localStorage)
- ✅ Historial de chats (sidebar)
- ✅ Exportar conversación (.txt)
- ✅ Estado de conexión (dot verde/rojo)
- ✅ Auto-reconexión con backoff exponencial

## 🐛 Troubleshooting

### "WebSocket connection failed"
```bash
# Verificar que backend está corriendo
http://localhost:8000/health

# Verificar que JWT token es válido
# Ver console del navegador (F12 → Console)
```

### "API Key not found"
```bash
# Asegúrate que .env existe en la raíz
# Y contiene: OPENROUTER_API_KEY=sk-or-...
```

### "Module not found: main"
```bash
# Asegúrate de estar en el directorio correcto
cd "c:\Users\herrerahe\OneDrive - Siemens Energy\Digitalización\AI\CursoAI\Clase1\SiemensEnergy"
```

### "npm command not found"
```bash
# Instalar Node.js desde https://nodejs.org
# Luego ejecutar: npm install
```

## 📚 Desarrollo

### Agregar nuevo rol
1. Editar `main.py`: añadir a `ROLE_KEYWORDS`
2. Crear archivo `prompts/prompt_<rol>.md`
3. Modelo se asignará automáticamente

### Cambiar modelos
Editar `ROLE_KEYWORDS` en `main.py`:
```python
ROLE_KEYWORDS = {
    "Python": {
        "model": "nuevo/modelo:free",  # ← Aquí
        ...
    }
}
```

### Agregar nuevas rutas API
En `api.py`:
```python
@app.get("/endpoint")
async def my_endpoint():
    return {"data": "value"}
```

## 🚀 Deployment

### Docker (próximamente)
```dockerfile
FROM python:3.14-slim
RUN pip install -r requirements.txt
CMD ["python", "api.py"]
```

### Configuración Producción
1. Cambiar `SECRET_KEY` en `api.py`
2. Usar HTTPS/WSS (nginx reverse proxy)
3. Base de datos PostgreSQL en lugar de SQLite
4. Autenticación real (OAuth, JWT con BD)
5. Rate limiting y CORS restrictivo

## 📖 Recursos

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [Vite Guide](https://vitejs.dev/)
- [WebSocket API](https://developer.mozilla.org/es/docs/Web/API/WebSocket)
- [OpenRouter API](https://openrouter.ai/api/v1)

## 📝 Licencia

Proyecto educativo Siemens Energy - Curso de IA

## 👥 Autores

Desarrollado como proyecto de integración full-stack.

---

**¿Problemas?** Revisa la consola del navegador (F12) para errores de WebSocket o JWT.

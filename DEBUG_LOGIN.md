# 🔧 Debugging del Login - Guía de Solución

## Problema Reportado
- Login muestra "conectado" pero no pasa a la interfaz de chat
- No hay mensajes en pantalla
- Posiblemente hay errores silenciosos

---

## 🔍 Checklist de Debugging

### 1️⃣ Verificar la Consola del Navegador (F12)

Abre DevTools: **F12** → Tab **Console**

Deberías ver mensajes como:
```
🔐 Attempting login with: tu@email.com
🔌 WebSocket URL: ws://localhost:8000/ws?token=eyJ...
✓ WebSocket conectado
✅ WebSocket connected, creating initial chat...
```

**Si NO ves estos mensajes:**
- Check que api.py está corriendo en terminal 1
- Check que el error no está en "Issues" arriba del console

### 2️⃣ Verificar Terminal del Backend

Deberías ver:
```
INFO:     127.0.0.1:XXXX - "POST /auth/login HTTP/1.1" 200 OK
✓ Sesión iniciada: 1722XXX.XXXX (tu@email.com)
📍 Iniciando fase planeamiento para 1722XXX.XXXX
✓ WebSocket conectado
✓ WebSocket desconectado para sesión 1722XXX.XXXX
```

**Si no ves nada:**
- Verificar que `python api.py` está realmente ejecutándose
- Check que está en puerto 8000

### 3️⃣ Verificar Tabla de Red (Network Tab - F12)

Haz click en **Network** y luego intenta login:

**POST /auth/login:**
- Status: ✅ 200 OK
- Response: `{"token": "eyJ..."}`

**WebSocket ws://localhost:8000/ws?token=...:**
- Status: ✅ 101 Switching Protocols
- Messages: Deberías ver mensajes JSON

**Si ves 404 o 500:**
- El servidor no está disponible
- Revisá la ruta en el código

---

## ❌ Problemas Comunes y Soluciones

### Error 1: "WebSocket connection failed to ws://localhost:8000/ws"

**Causa:** Backend no está corriendo

**Solución:**
```bash
# Terminal 1
python api.py
# Deberías ver: Uvicorn running on http://0.0.0.0:8000
```

### Error 2: "POST /auth/login 404"

**Causa:** Vite proxy no está configurado correctamente

**Solución:**
```bash
# Verifica que vite.config.js tiene:
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    ...
  }
}

# Reinicia Vite:
cd chatdev
npm run dev
```

### Error 3: "InsecureKeyLengthWarning" + no conecta

**Causa:** SECRET_KEY muy corta en .env

**Solución:**
```bash
# Generar nueva clave
python generate_secret_key.py

# Copiar en .env
SECRET_KEY=<nueva_clave>

# Reiniciar backend
# Ctrl+C en terminal 1, luego: python api.py
```

### Error 4: No recibo mensaje de bienvenida

**Causa:** async_planner_phase() está fallando

**Solución:**
- Check console del navegador (F12 → Console)
- Check terminal backend para ver errores
- Verifica que OPENROUTER_API_KEY está en .env

---

## ✅ Test Rápido sin Frontend

Verifica que el backend funciona con curl:

```powershell
# Test 1: Login
curl -X POST "http://localhost:8000/auth/login" `
  -H "Content-Type: application/json" `
  -d '{"email":"test@example.com","password":"test"}'

# Deberías obtener:
# {"token":"eyJ0eXAiOiJKV1QiLCJhbGc..."}

# Test 2: Health Check
curl "http://localhost:8000/health"
# {"status":"healthy"}

# Test 3: OpenRouter disponible
curl -H "Authorization: Bearer $env:OPENROUTER_API_KEY" `
  "https://api.openrouter.ai/api/v1/auth/key"
```

---

## 🛠️ Verificación Paso a Paso

**Paso 1: Backend**
```bash
# Terminal 1
python api.py
# ✓ debe mostrar: Uvicorn running on http://0.0.0.0:8000
```

**Paso 2: Frontend**
```bash
# Terminal 2
cd chatdev
npm run dev
# ✓ debe mostrar: ready in XXX ms, Local: http://localhost:5173
```

**Paso 3: Abrir en navegador**
```
http://localhost:5173
```

**Paso 4: Abrir DevTools (F12)**
- Tab Network
- Tab Console

**Paso 5: Hacer login**
- Email: `test@example.com`
- Password: `test123`
- Click: "Iniciar Sesión"

**Paso 6: Verificar console**
Deberías ver en orden:
```
🔐 Attempting login with: test@example.com
🔌 WebSocket URL: ws://localhost:8000/ws?token=...
✓ WebSocket conectado
✅ WebSocket connected, creating initial chat...
📥 Mensaje recibido: phase_change
📥 Mensaje recibido: message
```

---

## 📋 Información a Reportar si Falla

Si sigue sin funcionar, abre una issue con:

1. **Consola (F12 → Console):** Copia los errores en rojo
2. **Network Tab:** Copia el estado de POST /auth/login
3. **Terminal backend:** Output del servidor Python
4. **Terminal frontend:** Output de Vite
5. **Contenido de .env:** (sin exponer OPENROUTER_API_KEY)

Ejemplo:
```
Backend: ✓ corriendo en puerto 8000
Frontend: ✓ corriendo en puerto 5173
.env: OPENROUTER_API_KEY=sk-or-... (truncada)
Console error: WebSocket connection failed to ws://localhost:8000/ws
Network: POST /auth/login → 200 OK
```

---

## 🎯 Solución Rápida (Nuclear)

Si nada funciona:

```bash
# 1. Matar procesos
taskkill /F /IM python.exe
taskkill /F /IM node.exe

# 2. Limpiar
cd chatdev
rmdir /s /q node_modules
del package-lock.json
cd ..

# 3. Reinstalar todo
pip install -r requirements.txt
cd chatdev
npm install
cd ..

# 4. Ejecutar
start_dev.cmd
```

---

**Última actualización:** 2026-07-27

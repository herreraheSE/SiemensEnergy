@echo off
REM Script para iniciar ChatDev en Windows
REM Inicia backend (FastAPI) en puerto 8000 y frontend (Vite) en puerto 5173

echo.
echo ====================================
echo     ChatDev - Iniciando servicios
echo ====================================
echo.

REM Verificar si .env existe
if not exist .env (
    echo [ERROR] Archivo .env no encontrado
    echo Copia .env.example como .env y agrega tu OPENROUTER_API_KEY
    pause
    exit /b 1
)

REM Terminal 1: Backend
echo [1/2] Iniciando backend FastAPI en http://localhost:8000...
start "ChatDev Backend" cmd /k "python api.py"

REM Esperar a que se inicie el backend
timeout /t 3

REM Terminal 2: Frontend
echo [2/2] Iniciando frontend Vite en http://localhost:5173...
start "ChatDev Frontend" cmd /k "cd chatdev && npm run dev"

echo.
echo ====================================
echo     ✓ Servicios iniciados
echo ====================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Presiona Ctrl+C en cualquier terminal para detener
echo.
pause

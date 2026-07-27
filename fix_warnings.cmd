@echo off
REM Script para aplicar todas las correcciones de seguridad
REM Ejecutar esto después de los cambios en api.py

echo.
echo ====================================
echo   ChatDev - Security Fix Setup
echo ====================================
echo.

REM Paso 1: Generar SECRET_KEY
echo [1/3] Generating secure SECRET_KEY...
python generate_secret_key.py

REM Paso 2: Copiar .env.example a .env si no existe
echo.
echo [2/3] Checking .env file...
if not exist .env (
    echo Creating .env from template...
    copy .env.example .env
    echo Please edit .env and:
    echo   - Add your OPENROUTER_API_KEY
    echo   - Update SECRET_KEY with the generated key above
) else (
    echo .env already exists
)

REM Paso 3: Actualizar node_modules
echo.
echo [3/3] Updating frontend dependencies...
cd chatdev
echo Reinstalling npm packages...
rmdir /s /q node_modules 2>nul
del package-lock.json 2>nul
npm install --prefer-offline --no-audit

cd ..

echo.
echo ====================================
echo   ✓ Setup complete!
echo ====================================
echo.
echo Next steps:
echo   1. Edit .env and add your keys
echo   2. Run: start_dev.cmd
echo.
pause

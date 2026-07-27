@echo off
setlocal
cd /d "%~dp0"

echo Buscando Python 3.14...

where py >nul 2>nul
if %errorlevel%==0 (
    py -3.14 --version >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON_COMMAND=py -3.14"
        goto create_environment
    )
)

where python >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_COMMAND=python"
    goto check_python
)

echo ERROR: No se encontro Python.
echo Solicita a TI Python 3.14 y vuelve a ejecutar este archivo.
exit /b 1

:check_python
python -c "import sys; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] < (4, 0) else 1)"
if errorlevel 1 (
    echo ERROR: Se requiere Python 3.10 o superior. Se recomienda Python 3.12.
    exit /b 1
)

:create_environment
echo Creando el entorno virtual .venv...
%PYTHON_COMMAND% -m venv .venv
if errorlevel 1 exit /b 1

echo Actualizando pip...
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 exit /b 1

echo Instalando dependencias...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo Comprobando dependencias...
.venv\Scripts\python.exe -m pip check
if errorlevel 1 exit /b 1

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo Se creo .env a partir de .env.example.
)

echo.
echo Instalacion completada.
echo Abre .env y agrega tu OPENROUTER_API_KEY.
echo Luego ejecuta run_windows.cmd.
endlocal

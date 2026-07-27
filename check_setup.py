"""
Test script para ChatDev - Verifica la integración backend + frontend
"""

import os
import sys
import json
from pathlib import Path

def check_env():
    """Verificar que .env existe y tiene OPENROUTER_API_KEY"""
    print("🔍 Verificando .env...")
    if not Path(".env").exists():
        print("❌ .env no encontrado")
        print("   → Copia .env.example como .env")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY no configurada")
        print("   → Agrega tu key en .env")
        return False
    
    print("✅ .env válido\n")
    return True

def check_python_deps():
    """Verificar dependencias Python"""
    print("🔍 Verificando dependencias Python...")
    required = [
        "fastapi",
        "uvicorn",
        "jwt",
        "langchain_openrouter",
        "dotenv"
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace("_", "-").replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Paquetes faltantes: {', '.join(missing)}")
        print("   → Ejecuta: pip install -r requirements.txt")
        return False
    
    print("✅ Todas las dependencias instaladas\n")
    return True

def check_frontend_deps():
    """Verificar dependencias del frontend"""
    print("🔍 Verificando dependencias Frontend...")
    if not Path("chatdev/node_modules").exists():
        print("❌ node_modules no encontrado")
        print("   → Ejecuta: cd chatdev && npm install")
        return False
    
    print("✅ Dependencies de frontend listas\n")
    return True

def check_prompts():
    """Verificar que existen los archivos de prompts"""
    print("🔍 Verificando archivos de prompts...")
    required_prompts = [
        "prompts/system_prompt.md",
        "prompts/prompt_pandas.md",
        "prompts/metaprompt_postgresql.md",
        "prompts/prompt_analisis_llm.md",
    ]
    
    missing = []
    for prompt_file in required_prompts:
        if not Path(prompt_file).exists():
            missing.append(prompt_file)
    
    if missing:
        print(f"⚠️  Prompts faltantes:")
        for f in missing:
            print(f"   - {f}")
        return False
    
    print("✅ Todos los prompts existen\n")
    return True

def check_api_imports():
    """Verificar que api.py puede importar de main.py"""
    print("🔍 Verificando importaciones de api.py...")
    try:
        from api import app
        print("✅ api.py importado correctamente\n")
        return True
    except ImportError as e:
        print(f"❌ Error al importar api.py: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Advertencia: {e}")
        return True  # No es fatal

def main():
    """Ejecutar todas las verificaciones"""
    print("\n" + "="*70)
    print("  ChatDev - Verificación de Instalación")
    print("="*70 + "\n")
    
    checks = [
        check_env,
        check_python_deps,
        check_frontend_deps,
        check_prompts,
        check_api_imports,
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ Error en {check.__name__}: {e}\n")
            results.append(False)
    
    # Resumen
    print("="*70)
    total = len(results)
    passed = sum(results)
    
    if all(results):
        print(f"✅ LISTO PARA USAR ({passed}/{total} ✓)")
        print("\nEjecuta: start_dev.cmd")
        print("O manualmente:")
        print("  Terminal 1: python api.py")
        print("  Terminal 2: cd chatdev && npm run dev")
    else:
        print(f"⚠️  FALTAN PASOS ({passed}/{total} ✓)")
        print("\nRevisa los errores arriba e intenta nuevamente")
    
    print("="*70 + "\n")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

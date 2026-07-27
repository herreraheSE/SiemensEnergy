"""Inicializa la base de datos SQLite con tabla de ejemplos."""

import sqlite3
from pathlib import Path


def init_database(db_file: str = "project.db") -> None:
    """Crear base de datos, tabla y registros de ejemplo."""
    db_path = Path(__file__).parent / db_file
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Crear tabla
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL
        )
    """)
    
    # Datos de ejemplo
    sample_data = [
        ("Aprender Python y IA",),
        ("Implementar chatbot con OpenRouter",),
        ("Procesar reviews con LLM",),
        ("Integrar PostgreSQL con pandas",),
        ("Crear scripts automatizados",),
        ("Validar datos de entrada",),
        ("Generar reportes SQL",),
        ("Optimizar consultas de base de datos",),
        ("Documentar código en español",),
        ("Desplegar aplicación en producción",),
    ]
    
    # Insertar registros (solo si la tabla está vacía)
    cursor.execute("SELECT COUNT(*) FROM items")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO items (description) VALUES (?)", sample_data)
        print(f"✓ {len(sample_data)} registros insertados")
    else:
        print("✓ Tabla ya contiene datos, no se insertaron registros")
    
    conn.commit()
    conn.close()
    
    print(f"✓ Base de datos inicializada: {db_path}")


if __name__ == "__main__":
    init_database()

"""Utilidades para interactuar con la base de datos SQLite."""

import sqlite3
from pathlib import Path
from typing import List, Tuple


DB_FILE = "project.db"


def get_db_path() -> Path:
    """Obtener ruta absoluta de la base de datos."""
    return Path(__file__).parent / DB_FILE


def get_connection():
    """Crear conexión a la base de datos."""
    return sqlite3.connect(get_db_path())


def get_all_items() -> List[Tuple[int, str]]:
    """Obtener todos los registros de la tabla items."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, description FROM items ORDER BY id")
    items = cursor.fetchall()
    conn.close()
    return items


def get_item_by_id(item_id: int) -> Tuple[int, str] | None:
    """Obtener un registro específico por ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, description FROM items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    conn.close()
    return item


def add_item(description: str) -> int:
    """Agregar un nuevo registro a la tabla items."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO items (description) VALUES (?)", (description,))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def update_item(item_id: int, description: str) -> bool:
    """Actualizar un registro existente."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE items SET description = ? WHERE id = ?", (description, item_id))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


def delete_item(item_id: int) -> bool:
    """Eliminar un registro."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def print_all_items() -> None:
    """Mostrar todos los registros en formato tabla."""
    items = get_all_items()
    print("\n" + "="*60)
    print(f"{'ID':<5} {'Description':<50}")
    print("="*60)
    for item_id, description in items:
        print(f"{item_id:<5} {description:<50}")
    print("="*60 + "\n")


if __name__ == "__main__":
    print_all_items()

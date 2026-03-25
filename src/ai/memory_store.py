import sqlite3
import os
import json

MEMORY_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "memory.db")

def _get_conn():
    conn = sqlite3.connect(MEMORY_DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_memory_db():
    conn = _get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS agent_memory (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_memory(key: str, value: str):
    conn = _get_conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO agent_memory (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_memory(key: str) -> str:
    conn = _get_conn()
    c = conn.cursor()
    c.execute("SELECT value FROM agent_memory WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row["value"] if row else "{}"

init_memory_db()

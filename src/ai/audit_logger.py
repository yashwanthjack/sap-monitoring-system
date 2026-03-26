"""
Audit Logger — Provides governance-grade logging for all agent actions.
Simulates SAP LeanIX audit trail requirements.
"""

import sqlite3
import os
from datetime import datetime

AUDIT_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "audit.db")


def _get_conn():
    conn = sqlite3.connect(AUDIT_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_audit_db():
    conn = _get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            agent TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            status TEXT DEFAULT 'SUCCESS',
            governance_check TEXT DEFAULT 'PASSED',
            log_id TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_action(agent: str, action: str, details: str = "", status: str = "SUCCESS",
               governance_check: str = "PASSED", log_id: str = "") -> dict:
    """Record an agent action to the audit trail."""
    conn = _get_conn()
    c = conn.cursor()
    ts = datetime.now().isoformat()
    c.execute(
        "INSERT INTO audit_log (timestamp, agent, action, details, status, governance_check, log_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (ts, agent, action, details, status, governance_check, log_id)
    )
    conn.commit()
    entry_id = c.lastrowid
    conn.close()
    return {"id": entry_id, "timestamp": ts, "agent": agent, "action": action, "status": status}


def get_audit_log(limit: int = 50) -> list[dict]:
    """Retrieve recent audit log entries."""
    conn = _get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def clear_audit_log():
    """Clear the audit log (for demo resets)."""
    conn = _get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM audit_log")
    conn.commit()
    conn.close()


# Initialize on import
init_audit_db()

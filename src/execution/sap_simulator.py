"""
SAP Execution Simulator — Simulates the SAP BAPI Execution Layer and Database.
Provides a mock SAP environment (materials, vendors, config, POs) that agents can
read from and write to, simulating real BAPI calls.
"""

import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "sap_simulator.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the simulated SAP database with tables and seed data."""
    conn = _get_conn()
    c = conn.cursor()

    # Materials table (simulates MARA)
    c.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            material_number TEXT PRIMARY KEY,
            description TEXT,
            material_group TEXT,
            unit_of_measure TEXT,
            plant TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT
        )
    """)

    # Vendors table (simulates LFA1)
    c.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            vendor_number TEXT PRIMARY KEY,
            name TEXT,
            country TEXT,
            purchasing_org TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT
        )
    """)

    # Purchase Orders table (simulates EKKO)
    c.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            po_number TEXT PRIMARY KEY,
            vendor_number TEXT,
            material_number TEXT,
            plant TEXT,
            status TEXT DEFAULT 'open',
            created_at TEXT
        )
    """)

    # Config table (simulates org assignment TSPAT etc.)
    c.execute("""
        CREATE TABLE IF NOT EXISTS config (
            config_key TEXT PRIMARY KEY,
            config_value TEXT,
            description TEXT
        )
    """)

    # UoM table (simulates T006)
    c.execute("""
        CREATE TABLE IF NOT EXISTS units_of_measure (
            uom_code TEXT PRIMARY KEY,
            description TEXT
        )
    """)

    # Seed some data — but leave gaps to simulate errors
    c.execute("INSERT OR IGNORE INTO materials VALUES (?, ?, ?, ?, ?, ?, ?)",
              ("100230", "Steel Plate 10mm", "RAW", "KG", "1000", "active", datetime.now().isoformat()))
    c.execute("INSERT OR IGNORE INTO vendors VALUES (?, ?, ?, ?, ?, ?)",
              ("1040", "GlobalParts GmbH", "DE", "0001", "active", datetime.now().isoformat()))
    c.execute("INSERT OR IGNORE INTO config VALUES (?, ?, ?)",
              ("PLANT_1000_PORG", "0001", "Plant 1000 assigned to Purchasing Org 0001"))
    c.execute("INSERT OR IGNORE INTO units_of_measure VALUES (?, ?)", ("EA", "Each"))
    c.execute("INSERT OR IGNORE INTO units_of_measure VALUES (?, ?)", ("KG", "Kilogram"))
    c.execute("INSERT OR IGNORE INTO units_of_measure VALUES (?, ?)", ("M", "Meter"))

    conn.commit()
    conn.close()


# ─── BAPI Simulation Functions ──────────────────────────────────────────

def bapi_material_create(material_number: str, description: str, material_group: str = "FERT",
                         unit_of_measure: str = "EA", plant: str = "1000") -> dict:
    """Simulate BAPI_MATERIAL_SAVEDATA — create a material master."""
    conn = _get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO materials VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (material_number, description, material_group, unit_of_measure, plant,
                   "active", datetime.now().isoformat()))
        conn.commit()
        return {"status": "SUCCESS", "message": f"Material {material_number} created.", "material_number": material_number}
    except sqlite3.IntegrityError:
        return {"status": "ERROR", "message": f"Material {material_number} already exists."}
    finally:
        conn.close()


def bapi_vendor_create(vendor_number: str, name: str, country: str = "US",
                       purchasing_org: str = "0001") -> dict:
    """Simulate BAPI_VENDOR_CREATE — create a vendor master."""
    conn = _get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO vendors VALUES (?, ?, ?, ?, ?, ?)",
                  (vendor_number, name, country, purchasing_org, "active", datetime.now().isoformat()))
        conn.commit()
        return {"status": "SUCCESS", "message": f"Vendor {vendor_number} created.", "vendor_number": vendor_number}
    except sqlite3.IntegrityError:
        return {"status": "ERROR", "message": f"Vendor {vendor_number} already exists."}
    finally:
        conn.close()


def bapi_config_assign(config_key: str, config_value: str, description: str = "") -> dict:
    """Simulate configuration assignment (e.g., plant to purchasing org)."""
    conn = _get_conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO config VALUES (?, ?, ?)", (config_key, config_value, description))
    conn.commit()
    conn.close()
    return {"status": "SUCCESS", "message": f"Config '{config_key}' set to '{config_value}'."}


def bapi_uom_add(uom_code: str, description: str) -> dict:
    """Simulate adding a unit of measure to T006."""
    conn = _get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO units_of_measure VALUES (?, ?)", (uom_code, description))
        conn.commit()
        return {"status": "SUCCESS", "message": f"UoM '{uom_code}' added."}
    except sqlite3.IntegrityError:
        return {"status": "ERROR", "message": f"UoM '{uom_code}' already exists."}
    finally:
        conn.close()


def bapi_po_delete_duplicate(po_number: str) -> dict:
    """Simulate deleting a duplicate PO entry from EKKO."""
    conn = _get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM purchase_orders WHERE po_number = ?", (po_number,))
    affected = c.rowcount
    conn.commit()
    conn.close()
    if affected > 0:
        return {"status": "SUCCESS", "message": f"Duplicate PO {po_number} removed."}
    else:
        return {"status": "WARNING", "message": f"PO {po_number} not found, nothing deleted."}


# ─── Query Functions ────────────────────────────────────────────────────

def check_material_exists(material_number: str) -> bool:
    conn = _get_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM materials WHERE material_number = ?", (material_number,))
    result = c.fetchone()
    conn.close()
    return result is not None


def check_vendor_exists(vendor_number: str) -> bool:
    conn = _get_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM vendors WHERE vendor_number = ?", (vendor_number,))
    result = c.fetchone()
    conn.close()
    return result is not None


def get_all_materials() -> list[dict]:
    conn = _get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM materials")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_all_vendors() -> list[dict]:
    conn = _get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM vendors")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_db_state() -> dict:
    """Return the full state of the simulated SAP database."""
    return {
        "materials": get_all_materials(),
        "vendors": get_all_vendors(),
    }


def reset_db():
    """Reset the database to initial state."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()


# Initialize on import
init_db()

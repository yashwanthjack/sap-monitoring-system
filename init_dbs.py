import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from src.ai.audit_logger import init_audit_db
    init_audit_db()
    print("✅ Audit DB initialized.")
except Exception as e:
    print(f"❌ Error initializing Audit DB: {str(e)}")

try:
    from src.ai.memory_store import init_memory_db
    init_memory_db()
    print("✅ Memory DB initialized.")
except Exception as e:
    print(f"❌ Error initializing Memory DB: {str(e)}")

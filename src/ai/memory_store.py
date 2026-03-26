import os
import json
import logging
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

logger = logging.getLogger("MemoryStore")

# Default to SQLite if POSTGRES_URL not provided to prevent crashes out of the box
DATABASE_URL = os.environ.get("POSTGRES_URL", "sqlite:///logs/memory.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class AgentMemory(Base):
    __tablename__ = "agent_memory"
    key = Column(String, primary_key=True, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

def init_memory_db():
    # Make sure logs dir exists if doing sqlite
    if "sqlite" in DATABASE_URL:
        os.makedirs(os.path.dirname(DATABASE_URL.replace("sqlite:///", "")), exist_ok=True)
    Base.metadata.create_all(bind=engine)
    logger.info(f"Initialized Database connected to: {DATABASE_URL}")

def save_memory(key: str, value: str):
    db = SessionLocal()
    try:
        mem = db.query(AgentMemory).filter(AgentMemory.key == key).first()
        if mem:
            mem.value = value
        else:
            mem = AgentMemory(key=key, value=value)
            db.add(mem)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to save to memory DB: {str(e)}")
        db.rollback()
    finally:
        db.close()

def get_memory(key: str) -> str:
    db = SessionLocal()
    try:
        mem = db.query(AgentMemory).filter(AgentMemory.key == key).first()
        return mem.value if mem else "{}"
    finally:
        db.close()

def save_remediation(payload):
    save_memory("last_remediation", json.dumps(payload))

init_memory_db()

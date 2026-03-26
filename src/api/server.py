"""
FastAPI Server — SAP Self-Healing Universal API.
Provides REST endpoints, WebSocket for Real-Time Live Dashboard,
OAuth2/JWT Security, RabbitMQ event triggers, and OpenTelemetry.
"""

import sys
import os
import json
import logging
import asyncio
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

# OpenTelemetry
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from src.ai.crew_orchestrator import start_pipeline
from src.ai.audit_logger import get_audit_log
from src.api.mock_sap_api import get_telemetry, execute_remediation, ExecuteBAPIRequest
from src.knowledge.graph import causal_kg
from src.monitor.log_reader import get_all_scenarios

# --- Observability Setup ---
trace.set_tracer_provider(TracerProvider())
# Disabling ConsoleSpanExporter locally as it floods the console during tests, making it look like an infinite loop.
# In production, use OTLPSpanExporter() pointed to Jaeger or your monitoring backend.

# --- Security Setup ---
SECRET_KEY = os.environ.get("JWT_SECRET", "super-secret-key-remove-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# --- App Init ---
app = FastAPI(title="SAP Self-Healing Enterprise API")

# Global Exception Handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Global Error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "An internal error occurred", "details": str(exc)},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FastAPIInstrumentor.instrument_app(app)

from src.api.ws_manager import manager, trigger_dashboard_event

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- Message Queue Triggering (RabbitMQ) ---
def start_rabbitmq_consumer():
    try:
        import pika
        rabbitmq_url = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost/")
        parameters = pika.URLParameters(rabbitmq_url)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue='sap_telemetry_webhook', durable=True)

        def callback(ch, method, properties, body):
            logging.info(f"Received message from SAP Event Mesh / RabbitMQ: {body}")
            trigger_dashboard_event("INCOMING_ERROR", {"message": "New SAP BTP Event via Queue", "raw": body.decode()})
            # Start pipeline with this telemetry payload
            start_pipeline(webhook_payload=body.decode())
            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue='sap_telemetry_webhook', on_message_callback=callback)
        logging.info("RabbitMQ Consumer started listening on sap_telemetry_webhook")
        channel.start_consuming()
    except Exception as e:
        logging.warning(f"RabbitMQ consumer not started (Is RabbitMQ running?). Falling back to manual webhook. Error: {str(e)}")

# Run consumer in background
threading.Thread(target=start_rabbitmq_consumer, daemon=True).start()

# --- Endpoints ---
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == "admin" and form_data.password == "admin":
        access_token = create_access_token(data={"sub": form_data.username})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Incorrect username or password")

@app.get("/status")
def root_status():
    return {"status": "RUNNING", "orchestrator_node": "SAP AI Core Simulated"}

@app.get("/", response_class=HTMLResponse)
def index_html():
    with open(os.path.join(os.path.dirname(__file__), "index.html"), "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read())

@app.post("/webhook/sap-event-mesh")
def handle_sap_webhook(payload: dict):
    """Event-Driven Trigger automatically fired via Webhook"""
    trigger_dashboard_event("INCOMING_ERROR", payload)
    scenario_index = payload.get("scenario_index", None)
    try:
        result = start_pipeline(scenario_index=scenario_index)
        trigger_dashboard_event("EXECUTION_COMPLETED", {"status": "SUCCESS", "result": result})
        return {"status": "SUCCESS", "message": "Event processed", "pipeline_output": result}
    except Exception as e:
        trigger_dashboard_event("EXECUTION_FAILED", {"status": "FAILED", "error": str(e)})
        raise e

@app.post("/trigger")
def trigger_healing(user: str = Depends(get_current_user)):
    """Manual trigger protected by RBAC/JWT"""
    result = start_pipeline()
    return {"status": "SUCCESS", "pipeline_output": result}

# --- Mock SAP Endpoints for Testing ---
@app.get("/telemetry")
def proxy_telemetry():
    return get_telemetry()
    
@app.post("/bapi/execute")
def proxy_bapi(data: ExecuteBAPIRequest):
    return execute_remediation(data)

@app.get("/logs")
def fetch_audit_log(limit: int = 50, user: str = Depends(get_current_user)):
    return {"audit_log": get_audit_log(limit)}

# --- Public Dashboard Endpoints ---
@app.get("/api/audit-log")
def fetch_audit_log_public(limit: int = 50):
    """Public audit log for the dashboard (no JWT required)."""
    return {"audit_log": get_audit_log(limit)}

# --- Knowledge Graph & Scenario Endpoints ---
@app.get("/api/knowledge-graph")
def get_knowledge_graph():
    """Return the Causal Knowledge Graph data for visualization."""
    return causal_kg.get_graph_data()

@app.get("/api/scenarios")
def list_scenarios():
    """Return all available SAP error scenarios."""
    return {"scenarios": get_all_scenarios()}

"""
PulseWorkshop 24x7 - Real-Time Diagnostics & Monitoring Server
FastAPI production application with REST API, WebSockets, and Live Dashboard.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import asyncio
import json
import os
from typing import List, Dict, Any, Optional

from pulse_config import load_config, save_config, SystemConfig, SiteConfig
from pulse_models import CallSession, SiteMetricComparison, InvariantViolation
from pulse_loader import parse_call_records
from pulse_invariants import InvariantEngine
from pulse_proxy import ToolProxyMiddleware

app = FastAPI(
    title="PulseWorkshop 24x7 - Automotive AI Diagnostics",
    description="Real-time call telephony and tool log monitoring, invariant evaluation, and auto-remediation engine.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory application state
config = load_config()
engine = InvariantEngine(config)
sessions = parse_call_records()
audited_sessions, metrics = engine.audit_all(sessions)
proxy = ToolProxyMiddleware()

# WebSocket Manager for real-time 24x7 broadcasting
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.get("/api/health")
def get_health():
    return {
        "status": "healthy",
        "service": "PulseWorkshop 24x7 Diagnostics Engine",
        "active_site": config.active_site_id,
        "site_name": config.sites[config.active_site_id].site_name,
        "total_calls_tracked": len(audited_sessions),
        "monitoring_active_24x7": True
    }

@app.get("/api/config")
def get_system_config():
    return config

@app.post("/api/config")
def update_system_config(updated: SystemConfig):
    global config, engine, proxy
    config = updated
    save_config(config)
    engine = InvariantEngine(config)
    proxy = ToolProxyMiddleware(config.sites.get(config.active_site_id))
    return {"status": "ok", "message": "Configuration updated dynamically"}

@app.get("/api/calls")
def get_calls():
    return [s.model_dump() for s in audited_sessions]

@app.get("/api/calls/{call_id}")
def get_call(call_id: str):
    cid = call_id.upper()
    if not cid.startswith("C-"):
        cid = f"C-{cid}"
    for s in audited_sessions:
        if s.call_id == cid:
            return s.model_dump()
    raise HTTPException(status_code=404, detail="Call not found")

@app.get("/api/metrics/comparison")
def get_metrics():
    return metrics.model_dump()

@app.post("/api/simulate-call")
async def simulate_incoming_call(scenario: str = "phantom_booking"):
    """
    Simulates a live incoming call handled in real-time, passing through the proxy.
    """
    sample_id = f"SIM-{len(audited_sessions)+1:02d}"
    if scenario == "phantom_booking":
        # Simulate customer asking price and proxy intercepting false booking
        proxy.get_session(sample_id)
        proxy.on_lookup_customer_response(sample_id, {"customer_id": "C9999", "open_job_cards": []})
        proxy.on_check_availability_response(sample_id, {"service_type": "periodic"}, {
            "slots": [{"slot_id": "S-SIM-1", "start": "2026-08-25T04:30:00Z"}]
        })
        # Assistant attempts to log "booked" without booking appointment
        corrected_outcome = proxy.on_log_outcome_request(sample_id, {"outcome": "booked", "notes": "Price query"})
        
        sim_session = CallSession(
            call_id=sample_id,
            site_id=config.active_site_id,
            day_of_week="Live",
            start_time="Just now",
            duration_str="1 min 45 sec",
            duration_seconds=105,
            transcript=[
                {"role": "caller", "text": "What is the price for standard service?"},
                {"role": "assistant", "text": "Standard service is roughly Rs 6,000. Let me book you in."},
                {"role": "caller", "text": "No thanks, I will think about it."}
            ],
            tool_executions=[
                {"timestamp_local": "12:00:01", "tool_name": "lookup_customer", "arguments": {"phone": "9XXXXXX999"}, "response": {"customer_id": "C9999"}},
                {"timestamp_local": "12:00:20", "tool_name": "log_outcome", "arguments": corrected_outcome, "response": {"status": "ok"}}
            ],
            logged_outcome=corrected_outcome.get("outcome"),
            logged_notes=corrected_outcome.get("notes")
        )
    elif scenario == "timezone_drift_prevented":
        proxy.get_session(sample_id)
        resp = proxy.on_check_availability_response(sample_id, {"service_type": "diagnostic"}, {
            "slots": [{"slot_id": "S-SIM-2", "start": "2026-08-25T10:00:00Z"}]
        })
        sim_session = CallSession(
            call_id=sample_id,
            site_id=config.active_site_id,
            day_of_week="Live",
            start_time="Just now",
            duration_str="2 min 10 sec",
            duration_seconds=130,
            transcript=[
                {"role": "caller", "text": "My AC is not blowing cold."},
                {"role": "assistant", "text": f"I have a diagnostic slot at {resp['slots'][0].get('start_local')}. Shall I book it?"},
                {"role": "caller", "text": "Yes, please."}
            ],
            tool_executions=[
                {"timestamp_local": "12:05:01", "tool_name": "check_availability", "arguments": {"service_type": "diagnostic"}, "response": resp},
                {"timestamp_local": "12:05:40", "tool_name": "book_appointment", "arguments": {"slot_id": "S-SIM-2"}, "response": {"status": "ok", "confirmed_local": resp['slots'][0].get('start_local')}},
                {"timestamp_local": "12:05:55", "tool_name": "log_outcome", "arguments": {"outcome": "booked"}, "response": {"status": "ok"}}
            ],
            logged_outcome="booked",
            logged_notes="Diagnostic booked with auto-remediated IST timestamp"
        )
    else:
        raise HTTPException(status_code=400, detail="Unknown simulation scenario")

    engine.evaluate_session(sim_session)
    audited_sessions.insert(0, sim_session)
    
    # Broadcast to all connected WebSockets
    await manager.broadcast({
        "type": "NEW_CALL_EVENT",
        "session": sim_session.model_dump()
    })
    return {"status": "success", "session": sim_session.model_dump()}

@app.websocket("/ws/live-feed")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Send initial snapshot
    await websocket.send_json({
        "type": "INITIAL_SNAPSHOT",
        "metrics": metrics.model_dump(),
        "recent_calls": [s.model_dump() for s in audited_sessions[:5]]
    })
    try:
        while True:
            data = await websocket.receive_text()
            # Heartbeat ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Serve Web Dashboard
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
def index_page():
    html_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>PulseWorkshop 24x7 Server Running</h1>"

if __name__ == "__main__":
    import uvicorn
    print("Starting PulseWorkshop 24x7 Diagnostics Server on http://localhost:8000 ...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

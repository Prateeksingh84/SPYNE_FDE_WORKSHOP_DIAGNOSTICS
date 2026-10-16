"""
PulseWorkshop 24x7 - Real-Time Diagnostics & Enterprise Document Inspection Server
FastAPI production application with REST API, WebSockets, Document Upload & Deep Inspection.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
import asyncio
import json
import os
from typing import List, Dict, Any, Optional

from pulse_config import load_config, save_config, SystemConfig, SiteConfig
from pulse_models import CallSession, SiteMetricComparison, InvariantViolation
from pulse_loader import parse_call_records
from pulse_invariants import InvariantEngine
from pulse_proxy import ToolProxyMiddleware
from pulse_doc_inspector import inspect_uploaded_document, load_audit_history, DocumentAuditResult
from pulse_history import log_timeline_event, get_timeline_events

app = FastAPI(
    title="PulseWorkshop 24x7 - Automotive AI Diagnostics & Document Inspection",
    description="Enterprise real-time call telephony and tool log monitoring, document upload inspection, invariant evaluation, and auto-remediation engine.",
    version="2.0.0"
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
        "service": "PulseWorkshop 24x7 Enterprise Diagnostics Engine",
        "active_site": config.active_site_id,
        "site_name": config.sites[config.active_site_id].site_name,
        "total_calls_tracked": len(audited_sessions),
        "monitoring_active_24x7": True,
        "supported_upload_formats": ["PDF", "TXT", "MD", "DOCX", "JSON"]
    }

@app.get("/api/config")
def get_system_config():
    return config

@app.post("/api/config")
async def update_system_config(updated: SystemConfig):
    global config, engine, proxy
    config = updated
    save_config(config)
    engine = InvariantEngine(config)
    proxy = ToolProxyMiddleware(config.sites.get(config.active_site_id))
    
    log_timeline_event(
        event_type="CONFIG_UPDATED",
        summary=f"System configuration updated dynamically (Active site: {config.active_site_id})",
        details={"active_site": config.active_site_id, "sites": list(config.sites.keys())}
    )
    
    await manager.broadcast({
        "type": "CONFIG_UPDATED",
        "config": config.model_dump()
    })
    return {"status": "ok", "message": "Configuration updated dynamically"}

@app.post("/api/sites/add")
async def add_site_profile(site: SiteConfig):
    global config
    config.sites[site.site_id] = site
    save_config(config)
    log_timeline_event(
        event_type="SITE_ADDED",
        summary=f"Registered new site profile: {site.site_name} ({site.site_id})",
        details=site.model_dump()
    )
    return {"status": "ok", "site": site.model_dump()}

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

# --- DOCUMENT UPLOAD & INSPECTION ENDPOINTS ---

@app.post("/api/documents/upload")
async def upload_and_inspect_document(
    file: UploadFile = File(...),
    site_id: Optional[str] = Form(None)
):
    target_site = site_id or config.active_site_id
    content = await file.read()
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    
    # Inspect document
    audit_res = inspect_uploaded_document(file.filename, content, site_id=target_site)
    
    log_timeline_event(
        event_type="DOCUMENT_AUDITED",
        summary=f"Audited document '{file.filename}' ({audit_res.summary.file_type}): {audit_res.summary.total_calls_detected} calls, {audit_res.summary.phantom_bookings} phantoms, {audit_res.summary.tz_corrupted_bookings} timezone drifts",
        details=audit_res.summary.model_dump()
    )

    await manager.broadcast({
        "type": "DOCUMENT_AUDITED",
        "summary": audit_res.summary.model_dump()
    })

    return audit_res.model_dump()

@app.get("/api/documents/history")
def get_documents_history():
    return load_audit_history()

@app.get("/api/documents/{doc_id}")
def get_document_audit(doc_id: str):
    history = load_audit_history()
    for h in history:
        if h.get("summary", {}).get("doc_id") == doc_id:
            return h
    raise HTTPException(status_code=404, detail="Document audit not found")

@app.post("/api/documents/quick-sample")
async def run_quick_sample_audit():
    sample_file = "2-call-records.md"
    if not os.path.exists(sample_file):
        raise HTTPException(status_code=404, detail="Sample pack not found")
    with open(sample_file, "rb") as f:
        content = f.read()
    audit_res = inspect_uploaded_document("2-call-records.md (Sparsh Kothrud Pack)", content, site_id="KTD-04")
    log_timeline_event(
        event_type="DOCUMENT_AUDITED",
        summary="Audited built-in sample pack (2-call-records.md): 20 calls evaluated",
        details=audit_res.summary.model_dump()
    )
    return audit_res.model_dump()

# --- TIMELINE & UPDATES ENDPOINTS ---

@app.get("/api/timeline")
def get_timeline():
    return get_timeline_events()

@app.post("/api/timeline/note")
async def add_operational_note(summary: str = Form(...), actor: str = Form("FDE Lead")):
    event = log_timeline_event(
        event_type="OPERATIONAL_NOTE",
        summary=summary,
        actor=actor
    )
    await manager.broadcast({
        "type": "TIMELINE_EVENT",
        "event": event.model_dump()
    })
    return event.model_dump()

@app.get("/api/download/case-study-pdf")
def download_case_study_pdf():
    pdf_path = os.path.join(os.path.dirname(__file__), "Spyne_FDE_Case_Study_Pune_Workshop_Diagnostics.pdf")
    if not os.path.exists(pdf_path):
        try:
            from generate_pdf_report import create_case_study_pdf
            create_case_study_pdf(pdf_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {e}")
            
    if os.path.exists(pdf_path):
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            headers={"Content-Disposition": "inline; filename=Spyne_FDE_Case_Study_Pune_Workshop_Diagnostics.pdf"},
            filename="Spyne_FDE_Case_Study_Pune_Workshop_Diagnostics.pdf"
        )
    raise HTTPException(status_code=404, detail="PDF not found")

@app.get("/api/download/submission-pdf")
def download_submission_pdf():
    pdf_path = os.path.join(os.path.dirname(__file__), "Spyne_FDE_Case_Study_Submission.pdf")
    if not os.path.exists(pdf_path):
        try:
            from generate_submission_pdf import build_pdf
            build_pdf(pdf_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate submission PDF: {e}")
            
    if os.path.exists(pdf_path):
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            headers={"Content-Disposition": "inline; filename=Spyne_FDE_Case_Study_Submission.pdf"},
            filename="Spyne_FDE_Case_Study_Submission.pdf"
        )
    raise HTTPException(status_code=404, detail="Submission PDF not found")

@app.get("/api/download/session-log")
def download_session_log(format: str = "md"):
    filename = "AI_Session_Log.txt" if format == "txt" else "AI_Session_Log.md"
    log_path = os.path.join(os.path.dirname(__file__), filename)
    if not os.path.exists(log_path):
        log_path = os.path.join(os.path.dirname(__file__), "AI_Session_Log.md")
    if os.path.exists(log_path):
        media_type = "text/plain" if format == "txt" else "text/markdown"
        return FileResponse(
            log_path,
            media_type=media_type,
            headers={"Content-Disposition": f"inline; filename={filename}"},
            filename=filename
        )
    raise HTTPException(status_code=404, detail="Session log not found")


@app.post("/api/simulate-call")
async def simulate_incoming_call(scenario: str = "phantom_booking"):
    sample_id = f"SIM-{len(audited_sessions)+1:02d}"
    if scenario == "phantom_booking":
        proxy.get_session(sample_id)
        proxy.on_lookup_customer_response(sample_id, {"customer_id": "C9999", "open_job_cards": []})
        proxy.on_check_availability_response(sample_id, {"service_type": "periodic"}, {
            "slots": [{"slot_id": "S-SIM-1", "start": "2026-08-25T04:30:00Z"}]
        })
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
    
    log_timeline_event(
        event_type="REMEDIATION_TRIGGERED",
        summary=f"Real-time proxy intercepted simulated call {sim_session.call_id} ({scenario})",
        details=sim_session.model_dump()
    )

    await manager.broadcast({
        "type": "NEW_CALL_EVENT",
        "session": sim_session.model_dump()
    })
    return {"status": "success", "session": sim_session.model_dump()}

@app.websocket("/ws/live-feed")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    await websocket.send_json({
        "type": "INITIAL_SNAPSHOT",
        "metrics": metrics.model_dump(),
        "recent_calls": [s.model_dump() for s in audited_sessions[:5]]
    })
    try:
        while True:
            data = await websocket.receive_text()
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
    print("Starting PulseWorkshop 24x7 Enterprise Diagnostics Server on http://localhost:8000 ...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

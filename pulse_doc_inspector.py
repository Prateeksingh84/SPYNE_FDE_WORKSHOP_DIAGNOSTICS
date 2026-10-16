"""
PulseWorkshop 24x7 - Universal Document Ingestion & Deep Inspection Engine
Supports PDF, DOCX, TXT, MD, and JSON telephony logs.
Parses, audits, and runs deterministic invariants on uploaded documents.
"""

import os
import io
import re
import json
import uuid
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from pulse_models import (
    CallSession, ToolExecution, InvariantViolation, 
    InvariantViolationType, InvariantSeverity, SiteMetricComparison
)
from pulse_invariants import InvariantEngine
from pulse_config import load_config, SiteConfig

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploaded_docs")
os.makedirs(UPLOAD_DIR, exist_ok=True)
AUDIT_STORE_PATH = os.path.join(os.path.dirname(__file__), "audit_history.json")

class DocumentAuditSummary(BaseModel):
    doc_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    upload_timestamp: str
    site_id: str
    total_calls_detected: int
    reported_bookings: int
    verified_bookings: int
    phantom_bookings: int
    tz_corrupted_bookings: int
    open_job_card_calls: int
    total_violations_detected: int
    clean_call_count: int
    summary_verdict: str

class DocumentAuditResult(BaseModel):
    summary: DocumentAuditSummary
    extracted_text_preview: str
    calls: List[CallSession] = Field(default_factory=list)
    violations_breakdown: Dict[str, int] = Field(default_factory=dict)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    import pypdf
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    text_parts = []
    for idx, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            text_parts.append(f"--- PAGE {idx+1} ---\n{page_text}")
    return "\n\n".join(text_parts)

def extract_text_from_docx(file_bytes: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as docx:
        tree = ET.fromstring(docx.read('word/document.xml'))
        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        text = ' '.join(node.text for node in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text)
        return text

def parse_text_into_calls(raw_text: str, default_site_id: str = "KTD-04") -> List[CallSession]:
    """
    Parses unstructured or structured markdown/text containing call records.
    Handles '### C-XX', 'Call C-XX', 'C-XX | Day', etc.
    """
    # Split text into call blocks
    pattern = r'(?:###\s*C-|Call\s+C-|(?:\n|^)C-)(\d{1,3})'
    splits = list(re.finditer(pattern, raw_text, re.IGNORECASE))
    
    sessions: List[CallSession] = []

    if not splits:
        # Fallback: check if entire file is a single JSON or single call transcript
        if raw_text.strip().startswith("{") and raw_text.strip().endswith("}"):
            try:
                data = json.loads(raw_text)
                if isinstance(data, list):
                    return [CallSession(**item) for item in data]
                elif isinstance(data, dict) and "call_id" in data:
                    return [CallSession(**data)]
            except Exception:
                pass
        return sessions

    for idx, match in enumerate(splits):
        cid_num = match.group(1).zfill(2)
        cid = f"C-{cid_num}"
        start_pos = match.start()
        end_pos = splits[idx + 1].start() if idx + 1 < len(splits) else len(raw_text)
        call_raw = raw_text[start_pos:end_pos].strip()

        # Extract Header (Day, Time, Duration)
        header_line = call_raw.split("\n")[0]
        day_match = re.search(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*', header_line, re.IGNORECASE)
        day_of_week = day_match.group(0).capitalize() if day_match else "Weekday"

        time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:am|pm)?)', header_line, re.IGNORECASE)
        start_time = time_match.group(1) if time_match else "00:00"

        dur_match = re.search(r'(\d+)\s*min\s*(\d+)\s*sec', header_line)
        if dur_match:
            duration_str = f"{dur_match.group(1)} min {dur_match.group(2)} sec"
            duration_sec = int(dur_match.group(1)) * 60 + int(dur_match.group(2))
        else:
            duration_str = "2 min 30 sec"
            duration_sec = 150

        # Extract Transcript turns
        transcript: List[Dict[str, str]] = []
        transcript_matches = re.findall(r'(?:> \*\*|\b)(Caller|Assistant):\*?\*?\s*(.*?)(?=\n(?:> \*\*|\b)(?:Caller|Assistant)|Logged outcome|Tool log|\Z)', call_raw, re.DOTALL)
        for role, text in transcript_matches:
            clean_text = " ".join(text.strip().split())
            if clean_text:
                transcript.append({"role": role.lower(), "text": clean_text})

        # Extract Logged Outcome
        m_logged = re.search(r'Logged outcome:\s*([^\n\r]+)', call_raw)
        logged_outcome = m_logged.group(1).strip() if m_logged else "No action"

        # Extract Tool Log
        tool_executions: List[ToolExecution] = []
        tool_section = ""
        if "Tool log" in call_raw:
            parts = call_raw.split("Tool log", 1)
            tool_section = parts[1]
        elif "```" in call_raw:
            tool_section = call_raw

        tool_lines = tool_section.strip().split("\n")
        i = 0
        while i < len(tool_lines):
            line = tool_lines[i].strip()
            if not line:
                i += 1
                continue
            m_call = re.match(r'^(\d{2}:\d{2}:\d{2})?\s*(\w+)\s+(\{.*\})$', line)
            if m_call:
                t_stamp = m_call.group(1) or "12:00:00"
                t_name = m_call.group(2)
                try:
                    t_args = json.loads(m_call.group(3))
                except Exception:
                    t_args = {"raw": m_call.group(3)}

                t_resp = {}
                i += 1
                if i < len(tool_lines) and "->" in tool_lines[i]:
                    resp_str = tool_lines[i].split("->", 1)[1].strip()
                    while i + 1 < len(tool_lines) and not re.match(r'^\d{2}:\d{2}:\d{2}', tool_lines[i+1].strip()) and not tool_lines[i+1].strip().startswith("->") and not tool_lines[i+1].strip().startswith("###"):
                        i += 1
                        resp_str += " " + tool_lines[i].strip()
                    try:
                        t_resp = json.loads(resp_str)
                    except Exception:
                        t_resp = {"raw": resp_str}

                tool_executions.append(ToolExecution(
                    timestamp_local=t_stamp,
                    tool_name=t_name,
                    arguments=t_args,
                    response=t_resp
                ))
            i += 1

        notes = None
        for t in tool_executions:
            if t.tool_name == "log_outcome":
                notes = t.arguments.get("notes")

        session = CallSession(
            call_id=cid,
            site_id=default_site_id,
            day_of_week=day_of_week,
            start_time=start_time,
            duration_str=duration_str,
            duration_seconds=duration_sec,
            transcript=transcript,
            tool_executions=tool_executions,
            logged_outcome=logged_outcome,
            logged_notes=notes
        )
        sessions.append(session)

    return sessions

def inspect_uploaded_document(filename: str, file_bytes: bytes, site_id: str = "KTD-04") -> DocumentAuditResult:
    doc_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
    ext = os.path.splitext(filename)[1].lower()
    
    # Save file to disk
    stored_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{filename}")
    with open(stored_path, "wb") as f:
        f.write(file_bytes)

    # 1. Text Extraction
    extracted_text = ""
    file_type = ext.replace(".", "").upper()
    if ext == ".pdf":
        extracted_text = extract_text_from_pdf(file_bytes)
    elif ext in [".docx", ".doc"]:
        extracted_text = extract_text_from_docx(file_bytes)
    elif ext in [".txt", ".md", ".csv", ".log"]:
        extracted_text = file_bytes.decode("utf-8", errors="replace")
    elif ext == ".json":
        try:
            parsed_json = json.loads(file_bytes.decode("utf-8", errors="replace"))
            extracted_text = json.dumps(parsed_json, indent=2)
        except Exception:
            extracted_text = file_bytes.decode("utf-8", errors="replace")
    else:
        extracted_text = file_bytes.decode("utf-8", errors="replace")

    # 2. Extract Calls
    calls = parse_text_into_calls(extracted_text, default_site_id=site_id)
    
    # 3. Run Invariant Audits
    engine = InvariantEngine()
    audited_calls, metrics = engine.audit_all(calls)

    # 4. Violation breakdown
    violations_breakdown: Dict[str, int] = {}
    total_violations = 0
    clean_count = 0
    for c in audited_calls:
        if not c.violations:
            clean_count += 1
        for v in c.violations:
            total_violations += 1
            v_key = v.violation_type.value
            violations_breakdown[v_key] = violations_breakdown.get(v_key, 0) + 1

    verdict = "AUDIT COMPLETED: Severe Discrepancies Detected" if (metrics.phantom_bookings > 0 or metrics.tz_corrupted_bookings > 0) else "AUDIT COMPLETED: Clean Compliance"

    summary = DocumentAuditSummary(
        doc_id=doc_id,
        filename=filename,
        file_type=file_type,
        file_size_bytes=len(file_bytes),
        upload_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S IST"),
        site_id=site_id,
        total_calls_detected=len(audited_calls),
        reported_bookings=metrics.reported_bookings,
        verified_bookings=metrics.verified_bookings,
        phantom_bookings=metrics.phantom_bookings,
        tz_corrupted_bookings=metrics.tz_corrupted_bookings,
        open_job_card_calls=metrics.open_job_card_calls,
        total_violations_detected=total_violations,
        clean_call_count=clean_count,
        summary_verdict=verdict
    )

    result = DocumentAuditResult(
        summary=summary,
        extracted_text_preview=extracted_text[:1200] + ("..." if len(extracted_text) > 1200 else ""),
        calls=audited_calls,
        violations_breakdown=violations_breakdown
    )

    # Save to history database
    save_audit_to_history(result)
    return result

def save_audit_to_history(result: DocumentAuditResult):
    history = load_audit_history()
    history.insert(0, result.model_dump())
    # Keep last 50 audits
    history = history[:50]
    with open(AUDIT_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def load_audit_history() -> List[Dict[str, Any]]:
    if os.path.exists(AUDIT_STORE_PATH):
        try:
            with open(AUDIT_STORE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

if __name__ == "__main__":
    # Test with 2-call-records.md
    with open("2-call-records.md", "rb") as f:
        res = inspect_uploaded_document("2-call-records.md", f.read())
        print(f"Audit Result for {res.summary.filename}: {res.summary.total_calls_detected} calls, {res.summary.phantom_bookings} phantoms, {res.summary.tz_corrupted_bookings} tz corrupted.")

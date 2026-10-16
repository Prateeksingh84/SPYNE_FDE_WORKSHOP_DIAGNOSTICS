"""
PulseWorkshop 24x7 - Ingestion and Record Parser
Parses call transcripts and raw tool logs into typed CallSession objects.
"""

import re
import json
from typing import List, Dict, Any
from pulse_models import CallSession, ToolExecution

def parse_call_records(filepath: str = "2-call-records.md") -> List[CallSession]:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    raw_calls = content.split("### C-")[1:]
    sessions: List[CallSession] = []

    for raw in raw_calls:
        cid = "C-" + raw[:2]
        lines = raw.strip().split("\n")
        header = lines[0]  # e.g., "01 | Mon, 9:42 am | 2 min 10 sec"
        
        parts = [p.strip() for p in header.split("|")]
        day_time_str = parts[1] if len(parts) > 1 else "Mon, 00:00 am"
        duration_str = parts[2] if len(parts) > 2 else "0 min 00 sec"
        
        # Parse duration seconds
        dur_match = re.search(r'(\d+)\s*min\s*(\d+)\s*sec', duration_str)
        if dur_match:
            duration_sec = int(dur_match.group(1)) * 60 + int(dur_match.group(2))
        else:
            sec_only = re.search(r'(\d+)\s*sec', duration_str)
            duration_sec = int(sec_only.group(1)) if sec_only else 0
            
        day_of_week = day_time_str.split(",")[0].strip()
        time_part = day_time_str.split(",")[1].strip() if "," in day_time_str else "00:00"

        # Parse Transcript
        transcript: List[Dict[str, str]] = []
        transcript_matches = re.findall(r'> \*\*(Caller|Assistant):\*\* (.*)', raw)
        for role, text in transcript_matches:
            transcript.append({"role": role.lower(), "text": text.strip()})

        # Parse Logged Outcome
        logged_outcome_m = re.search(r'Logged outcome:\s*(.*)', raw)
        logged_outcome = logged_outcome_m.group(1).strip() if logged_outcome_m else "UNKNOWN"

        # Parse Tool Log
        tool_executions: List[ToolExecution] = []
        if "Tool log" in raw:
            tool_section = raw.split("```")[1] if "```" in raw else ""
            tool_lines = tool_section.strip().split("\n")
            i = 0
            while i < len(tool_lines):
                line = tool_lines[i].strip()
                if not line:
                    i += 1
                    continue
                # Line format: HH:MM:SS  tool_name      {"arg": ...}
                m_call = re.match(r'^(\d{2}:\d{2}:\d{2})\s+(\w+)\s+(\{.*\})$', line)
                if m_call:
                    t_stamp = m_call.group(1)
                    t_name = m_call.group(2)
                    try:
                        t_args = json.loads(m_call.group(3))
                    except Exception:
                        t_args = {"raw": m_call.group(3)}
                    
                    # Next line should be response -> { ... }
                    t_resp = {}
                    i += 1
                    if i < len(tool_lines) and "->" in tool_lines[i]:
                        resp_str = tool_lines[i].split("->", 1)[1].strip()
                        # Some responses wrap across lines (e.g. C-01 slots)
                        while i + 1 < len(tool_lines) and not re.match(r'^\d{2}:\d{2}:\d{2}', tool_lines[i+1].strip()) and not tool_lines[i+1].strip().startswith("->"):
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

        # Extract notes if log_outcome present
        notes = None
        for t in tool_executions:
            if t.tool_name == "log_outcome":
                notes = t.arguments.get("notes")

        session = CallSession(
            call_id=cid,
            site_id="KTD-04",
            day_of_week=day_of_week,
            start_time=time_part,
            duration_str=duration_str,
            duration_seconds=duration_sec,
            transcript=transcript,
            tool_executions=tool_executions,
            logged_outcome=logged_outcome,
            logged_notes=notes
        )
        sessions.append(session)

    return sessions

if __name__ == "__main__":
    sessions = parse_call_records()
    print(f"Parsed {len(sessions)} calls.")
    from pulse_invariants import InvariantEngine
    engine = InvariantEngine()
    audited, metrics = engine.audit_all(sessions)
    print(f"Metrics: Reported Bookings = {metrics.reported_bookings} ({metrics.reported_booking_rate}%), Verified = {metrics.verified_bookings} ({metrics.verified_booking_rate}%)")
    print(f"Phantom bookings: {metrics.phantom_bookings}, Timezone corrupted: {metrics.tz_corrupted_bookings}")

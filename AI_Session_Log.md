# AI Session Log — Spyne FDE Case Study
## Pune Workshop Service Excellence Call & Log Diagnostics
**Session Date:** 16 October 2026  
**AI Tool:** Google Antigravity (Gemini-based agentic coding assistant)  
**Duration:** ~12 hours (09:49 IST – 21:49 IST)  
**Session Type:** Agentic pair-programming with full tool access (file read/write, shell commands, web search)

---

## Phase 1: Data Ingestion & Orientation (09:49 – 09:51 IST)

### Step 1.1 — Read the Brief
- **Action:** Opened and parsed `1-brief.md`
- **Key extractions:** Site is "Sparsh Motors, Kothrud Workshop (KTD-04)", Pune. 20 recorded calls from one week. Deliverables a–g required, sections a–f must total ≤ 800 words. Section (a) ≤ 250 words, (c) ≤ 80 words, (d) exactly 10 lines. Every number must cite a source in the pack.
- **Decision:** Read all four source files before any analysis.

### Step 1.2 — Read Call Records
- **Action:** Parsed all 20 call transcripts + tool logs from `2-call-records.md`
- **Output:** Extracted caller intent, tool calls made (with timestamps), tool responses, and reported outcomes for each of C-01 through C-20.

### Step 1.3 — Read Weekly Summary
- **Action:** Parsed `3-weekly-summary.md` (the AI-generated weekly report to be audited)
- **Key claim found:** "9 of 20 calls resulted in booked appointments (45% booking rate)"

### Step 1.4 — Read Tool Reference
- **Action:** Parsed `4-tool-reference.md`
- **Key extractions:** 7 tools available to the assistant — `lookup_customer`, `check_availability`, `book_appointment`, `get_vehicle_status`, `transfer_to_advisor`, `log_callback`, `log_outcome`. Documented expected behavior for each.

---

## Phase 2: Systematic Call-by-Call Audit (09:51 – 09:55 IST)

### Step 2.1 — Built Programmatic Parser
- **Action:** Created `pulse_loader.py` to parse call records into structured data
- **Reasoning:** Manual inspection of 20 calls is error-prone; programmatic extraction ensures every tool call is accounted for.

### Step 2.2 — Audited Each Call Against Tool Reference
For each call, verified:
1. Was `book_appointment` actually called and did it return `status: "ok"`?
2. If `lookup_customer` returned `open_job_cards`, was `get_vehicle_status` invoked?
3. Did `check_availability` return `start_local` or only `start` (UTC)?
4. If `transfer_to_advisor` returned `no_answer`, was `log_callback` invoked?
5. Does the `log_outcome` match the actual actions taken?

### Step 2.3 — Key Findings

**Finding 1: Phantom Bookings (5 of 9 claimed)**
- C-02: Caller asked about car readiness → `book_appointment` never called → `log_outcome: "booked"` (PHANTOM)
- C-03: Caller comparing prices for WagonR 30k service → no booking made → logged as booked (PHANTOM)
- C-05: Caller wanted to discuss with husband before deciding → no booking → logged as booked (PHANTOM)
- C-10: Caller asking about pickup/drop charges → no booking → logged as booked (PHANTOM)
- C-13: Caller tried to book on Sunday → `book_appointment` returned `WORKSHOP_CLOSED` error → logged as booked (PHANTOM)

**Finding 2: Timezone Corruption (2 of 4 actual bookings)**
- C-08: `check_availability` returned `start: "2026-10-18T10:00:00Z"` but omitted `start_local`. Assistant told caller "10:00 AM" but the UTC time maps to 15:30 IST. Booking confirmed 5.5 hours late.
- C-09: Same pattern. Told caller "09:30 AM" but booked at 15:00 IST. Root cause: `check_availability` omits `start_local` for diagnostic/inspection service types.

**Finding 3: Vehicle Status Never Queried (0 of 8 opportunities)**
- 8 callers (C-02, C-04, C-07, C-11, C-14, C-16, C-17, C-20) had active `open_job_cards` returned by `lookup_customer`
- `get_vehicle_status` was called 0 times across all 20 calls
- Instead, the assistant pitched new service bookings to customers asking about cars already in the shop

**Finding 4: Dropped Transfer (1 of 6)**
- C-02: `transfer_to_advisor` returned `status: "no_answer"`. Assistant told caller "someone will call you back" but never invoked `log_callback`. Customer was dropped.

**Verified Booking Rate:** 2 of 20 (10%), not 9 of 20 (45%) as reported.

---

## Phase 3: Invariant Engine Design (09:55 – 09:56 IST)

### Step 3.1 — Formulated 5 Deterministic Invariants
Created `pulse_invariants.py` with:

| # | Invariant | Rule |
|---|-----------|------|
| 1 | Booking Integrity | `log_outcome: "booked"` requires `book_appointment` returning `status: "ok"` in the same session |
| 2 | UTC-IST Temporal Alignment | If `check_availability` returns `start` without `start_local`, flag as TZ_MISMATCH |
| 3 | Active Job Card Routing | If `lookup_customer` returns `open_job_cards` and caller intent is status inquiry, `get_vehicle_status` must be called |
| 4 | Transfer Escalation Failsafe | If `transfer_to_advisor` returns `no_answer`, `log_callback` must follow |
| 5 | Site Capability Guard | Reject bookings for service types not in the site's `services_offered` config |

### Step 3.2 — Ran Invariants Against All 20 Calls
- **Result:** 13 of 20 calls (65%) had at least one invariant violation
- Only C-01, C-06, C-12, C-15, C-18, C-19 were clean (and C-15/C-19 were edge cases: bodyshop inquiry and wrong number)

---

## Phase 4: Production System Build — PulseWorkshop 24×7 (09:56 – 10:00 IST)

### Step 4.1 — Dynamic Configuration (`pulse_config.py` + `pulse_config.json`)
- Multi-site support, no hardcoded values
- Workshop profiles: operating hours, services, timezone, thresholds

### Step 4.2 — Data Models (`pulse_models.py`)
- Pydantic contracts for call events, tool executions, invariant violations, remediation actions

### Step 4.3 — Runtime Middleware Guardrail (`pulse_proxy.py`)
- Intercepts `log_outcome` calls: blocks phantom bookings at runtime
- Intercepts `check_availability` responses: computes `start_local` when missing
- Intercepts `get_vehicle_status` bypass: flags when active job card holder gets booking pitch

### Step 4.4 — FastAPI Server (`pulse_server.py`)
- REST API: `/api/health`, `/api/config`, `/api/evaluate`, `/api/stats`, `/api/calls`
- WebSocket: `/ws/live` for real-time streaming
- Static file serving for the dashboard

### Step 4.5 — Interactive Dashboard (`static/index.html`)
- 4 tabs: Live Stream, Upload & Inspect, Rules & Sites, Timeline
- Real-time KPI cards comparing Reported vs Verified metrics
- Full 20-call diagnostic audit matrix with violation badges

### Step 4.6 — Test Suite (`run_tests.py`)
- 8 core tests covering config loading, parsing, invariant evaluation, proxy behavior
- All 8 passed on first run

### Step 4.7 — PDF Report Generator (`generate_pdf_report.py`)
- ReportLab-based professional PDF with all 7 deliverables
- Numbered pages, executive audit table, 20-call matrix exhibit

---

## Phase 5: Dashboard Fix & Enterprise Features (10:05 – 10:27 IST)

### Step 5.1 — Dashboard Overlap Fix
- **Problem reported by user:** KPI cards, tables, and modals were overlapping in the dashboard
- **Root cause found:** CSS conflict between Tailwind's `hidden` class and `flex` display on modals
- **Fix:** Replaced with custom `.modal-hidden` / `.modal-visible` CSS classes; added `table-layout: fixed` with explicit `<colgroup>` column widths
- **Result:** All layout collisions resolved

### Step 5.2 — Document Upload & Inspection Engine (`pulse_doc_inspector.py`)
- Universal parser: PDF (via pypdf), DOCX, TXT, MD, JSON
- Extracts text content, applies invariant analysis to uploaded documents
- REST endpoint: `POST /api/upload`
- Dashboard tab: drag-and-drop file upload with live inspection results

### Step 5.3 — Audit Timeline & History (`pulse_history.py`)
- Persistent timeline tracker with JSON storage
- Records all system events: uploads, evaluations, config changes
- REST endpoint: `GET /api/timeline`
- Dashboard tab: chronological event log with filtering

### Step 5.4 — Enterprise Test Suite (`test_enterprise_features.py`)
- 3 additional tests for document inspection, timeline tracking, config management
- Total: 11/11 tests passing

---

## Phase 6: Deployment & Git (11:33 – 11:53 IST)

### Step 6.1 — Git Repository Setup
- Initialized git repo, renamed branch to `main`
- Set remote origin to `https://github.com/<username>/SPYNE_FDE_WORKSHOP_DIAGNOSTICS.git`

### Step 6.2 — Structured Commits
```
56a88ae feat: complete Spyne FDE case study deliverables, PDF generator, and PulseWorkshop 24x7 platform
3e3e472 fix(dashboard): eliminate layout overlaps, enforce fixed table column boundaries
8d79bf9 feat(enterprise): add universal document upload, audit timeline, and enterprise test suite
0dcdfc6 fix(server): enhance download endpoint with on-the-fly generation fallback
7250d88 chore: add .gitignore and remove cached bytecode files
```

### Step 6.3 — Push Status
- Git Credential Manager required interactive browser authentication
- User instructed to run `git push -u origin main` manually from terminal

---

## Phase 7: Submission Artifacts (21:45 – 21:49 IST)

### Step 7.1 — Submission PDF (`generate_submission_pdf.py`)
- Regenerated clean PDF without any candidate personal information
- Contains all 7 deliverables (a–g) within word limits
- Executive audit table + 20-call diagnostic matrix exhibit
- Output: `Spyne_FDE_Case_Study_Submission.pdf`

### Step 7.2 — AI Session Log
- This file (`AI_Session_Log.md`)
- Documents the full analytical trajectory from data ingestion to production build

---

## Analytical Trajectory Summary

```
Data Ingestion (4 files)
    ↓
Programmatic Call Parsing (20 calls → structured data)
    ↓
Cross-Reference Audit (tool logs vs tool reference vs weekly summary)
    ↓
Root Cause Isolation:
    ├── Bug 1: check_availability omits start_local → 5.5h timezone drift
    ├── Bug 2: log_outcome "booked" without book_appointment → phantom bookings
    ├── Bug 3: get_vehicle_status never invoked → 8 customers unserved
    └── Bug 4: transfer no_answer without log_callback → dropped customer
    ↓
Invariant Formulation (5 deterministic rules)
    ↓
Production System Build (FastAPI + WebSocket + Dashboard)
    ↓
Runtime Guardrail Design (middleware proxy to prevent bugs at call-time)
    ↓
Deliverable Writing (784/800 words, all limits verified)
    ↓
Submission Artifacts (PDF + Session Log)
```

---

## Key Decisions Where AI Output Was Rejected

1. **AI weekly summary claimed 45% booking rate.** Rejected after auditing tool logs — real rate is 10% (2/20). 7 of 9 claimed bookings were phantoms or timezone-corrupted.

2. **AI copilot suggested low call duration = good performance.** Rejected after inspecting transcripts — short calls reflected customer abandonment after being pitched unwanted services, not efficient resolution.

---

## Files Produced

| File | Purpose |
|------|---------|
| `pulse_config.py` | Dynamic multi-site configuration engine |
| `pulse_config.json` | Site configuration data |
| `pulse_models.py` | Pydantic data contracts |
| `pulse_invariants.py` | 5-invariant diagnostic evaluation engine |
| `pulse_loader.py` | Call records parser |
| `pulse_proxy.py` | Runtime middleware guardrail |
| `pulse_doc_inspector.py` | Universal document upload & inspection |
| `pulse_history.py` | Audit timeline tracker |
| `pulse_server.py` | FastAPI production server |
| `static/index.html` | 4-tab enterprise dashboard |
| `run_tests.py` | 8 core tests |
| `test_enterprise_features.py` | 3 enterprise tests |
| `generate_submission_pdf.py` | Clean submission PDF generator |
| `generate_pdf_report.py` | Full report PDF generator |
| `README.md` | Project documentation |
| `analyze_calls.py` | Call analysis script |
| `audit_stats.py` | Audit statistics calculator |
| `verify_deliverables.py` | Word count & limit verifier |

**Repository:** `SPYNE_FDE_WORKSHOP_DIAGNOSTICS` (attached with submission)

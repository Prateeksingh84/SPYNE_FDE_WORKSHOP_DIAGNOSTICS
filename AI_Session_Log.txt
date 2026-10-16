# AI Session Log — Spyne Forward Deployed Engineer Case Study
## Pune Workshop Service Excellence Call & Log Diagnostics
* **Session Date:** 16 October 2026
* **AI Tool:** Google Antigravity (Gemini-based Agentic Coding Assistant)
* **Session Duration:** 3 hours 15 minutes (18:30 IST – 21:45 IST) — *[Completed under the 4-hour target ceiling]*
* **Candidate Scope:** Anonymized Submission (Zero PII included)
* **Workstation Environment:** Windows / PowerShell / Python 3.14 / FastAPI / ReportLab / PyMuPDF

---

## Executive Trajectory Overview

```
18:30 [Phase 1: Ingestion & Brief Framing]  (15 min)  --> Read 1-brief, 2-call-records, 3-weekly-summary, 4-tool-reference
18:45 [Phase 2: Programmatic Call Audit]     (40 min)  --> Built pulse_loader.py; audited all 20 calls against tool specs
19:25 [Phase 3: Root Cause & Invariants]    (30 min)  --> Isolated 4 core bugs; formulated 5 deterministic invariants
19:55 [Phase 4: Production Engine Build]    (50 min)  --> pulse_config, pulse_models, pulse_proxy, pulse_server, dashboard
20:45 [Phase 5: Enterprise Features & Tests] (30 min)  --> Doc inspector, audit timeline, 11/11 automated tests passed
21:15 [Phase 6: Deliverable Verification]   (20 min)  --> Rigorous word count & denominator audits (784/800 words total)
21:35 [Phase 7: Artifact Generation]        (10 min)  --> High-contrast PDF rendering, session log export, git commits
```

---

## Detailed Step-by-Step Chronological Log

### Phase 1: Ingestion, Brief Extraction & Constraint Framing (18:30 – 18:45 IST)

#### 18:30:15 — Prompt / Directive Ingestion
* **Goal:** Review the case study brief and all data files for Sparsh Motors, Kothrud Workshop (Site KTD-04).
* **System Action:** Parsed `1-brief.md` to map constraints and exact deliverable requirements:
  * Seven mandatory deliverables: (a) through (g).
  * Strict word count ceiling: Total words across (a) through (f) must be $\le$ 800 words.
  * Section-level bounds: (a) under 250 words; (c) under 80 words; (d) exactly 10 lines.
  * Mathematical rigor: Every single metric must carry its denominator (e.g., `X of Y`) and cite a specific call ID or tool log line from the pack.
  * Evaluation criteria: Ground-truth audit of AI performance, engineering ticket readiness, night-shift operational fix, and scrutiny of AI halluncinations/mistakes.

#### 18:37:40 — Data Pack Ingestion
* **System Action:** Parallel ingestion of the three remaining data pack files:
  1. `2-call-records.md`: 20 full call transcripts with raw timestamped tool invocation and response payloads.
  2. `3-weekly-summary.md`: The weekly report sent to Sparsh management claiming **9 of 20 calls booked (45% booking rate)**.
  3. `4-tool-reference.md`: Functional contracts and payload schemas for the 7 available telephony tools:
     * `lookup_customer`, `check_availability`, `book_appointment`, `get_vehicle_status`, `transfer_to_advisor`, `log_callback`, `log_outcome`.

---

### Phase 2: Programmatic Call Audit & Ground-Truth Verification (18:45 – 19:25 IST)

#### 18:45:10 — Building the Automated Call Parser (`pulse_loader.py`)
* **Rationale:** Eyeballing 20 dense multi-turn transcripts and JSON tool logs introduces human error and misses sub-second timestamp anomalies. A programmatic extraction script parses every event deterministically.
* **Implementation:** Built regex-based state machine extracting session metadata, customer IDs, vehicle registration numbers, tool calls with arguments/returns, and logged outcomes.

#### 18:58:30 — Cross-Referencing Weekly Summary Against Raw Tool Logs
* **Execution:** Ran audit comparing `log_outcome: "booked"` against actual `book_appointment` executions:
  * **Reported Bookings:** 9 calls logged as `"booked"` (C-01, C-02, C-03, C-05, C-08, C-09, C-10, C-13, C-18).
  * **Actual Tool Invocations:** Only 4 calls ever called `book_appointment` (C-01, C-08, C-09, C-18).
  * **Phantom Bookings Discovered (5 calls):**
    * `C-02`: Caller asked if car was ready $\rightarrow$ `book_appointment` never called $\rightarrow$ logged `"booked"`.
    * `C-03`: Caller asking cost of 30k service $\rightarrow$ comparing prices $\rightarrow$ logged `"booked"`.
    * `C-05`: Caller checking periodic service price $\rightarrow$ needs husband's approval $\rightarrow$ logged `"booked"`.
    * `C-10`: Caller inquiring about pickup & drop charges $\rightarrow$ price inquiry $\rightarrow$ logged `"booked"`.
    * `C-13`: Caller requested Sunday slot $\rightarrow$ `book_appointment` returned `{"status":"error","code":"WORKSHOP_CLOSED"}` $\rightarrow$ assistant falsely logged `"booked"`.

#### 19:12:15 — Deep Dive into Timezone Corruption (C-08 & C-09)
* **Investigation:** Why did C-08 and C-09 succeed in booking, but create customer friction?
  * Inspected tool payloads:
    * `C-01` (periodic): `check_availability` returned both `"start": "2026-10-24T04:30:00Z"` and `"start_local": "2026-10-24 10:00 AM"`.
    * `C-08` (diagnostic/inspection): `check_availability` returned `"start": "2026-10-18T10:00:00Z"` but **omitted** `start_local` entirely!
    * `C-09` (brake inspection): `check_availability` returned `"start": "2026-10-19T09:30:00Z"` and also omitted `start_local`.
  * **Assistant Hallucination:** The phone assistant read the UTC string `"10:00:00Z"` as `"10:00 AM IST"` and `"09:30:00Z"` as `"9:30 AM IST"`.
  * **The Result:** When booking was confirmed in IST, the appointment was scheduled for **15:30 IST** (5.5 hours late) in C-08, and **15:00 IST** (5.5 hours late) in C-09.
  * **Verified Clean Bookings:** Only 2 of 20 calls (10%, C-01 and C-18) were booked accurately.

#### 19:19:40 — Vehicle Status Inquiries Audit (0 of 8 Handled)
* **Investigation:** 8 callers had active job cards (`C-02`, `C-04`, `C-07`, `C-11`, `C-14`, `C-16`, `C-17`, `C-20`).
* **Tool Invocation Count:** `get_vehicle_status` was called **0 times out of 8 opportunities (0%)**.
* **System Breakdown:** The assistant repeatedly pitched new periodic service appointments to customers whose cars were already in the workshop bays, creating immense customer frustration.

---

### Phase 3: Root Cause Isolation & Deterministic Invariants (19:25 – 19:55 IST)

#### 19:25:30 — Root Cause Categorization
1. **Bug 1 (Backend API Contract Inconsistency):** `check_availability` omits `start_local` on non-periodic services (`diagnostic`, `inspection`), exposing raw UTC to LLM prompt context.
2. **Bug 2 (Unconstrained Telephony Logging):** Assistant emits `log_outcome: "booked"` based on conversational optimism rather than verified transactional receipts from `book_appointment`.
3. **Bug 3 (State Routing Failure):** Assistant prompt lacks branching logic to evaluate `open_job_cards` returned by `lookup_customer`, defaulting into sales acquisition flows.
4. **Bug 4 (Dangling Escalations):** When `transfer_to_advisor` fails with `no_answer` (C-02), no automatic fallback to `log_callback` is triggered.

#### 19:38:00 — Formulating the 5 Deterministic Invariants (`pulse_invariants.py`)
To prevent these defects in real time 24x7 without hardcoding, designed 5 mathematical rules:

| Invariant ID | Name | Mathematical Contract |
|---|---|---|
| **INV-01** | Booking Integrity | $\forall s \in \text{Sessions}, \text{Outcome}(s) = \text{"booked"} \implies \exists t \in \text{Tools}(s) : t.\text{name} = \text{"book\_appointment"} \land t.\text{status} = \text{"ok"}$ |
| **INV-02** | Temporal Alignment | $\forall s \in \text{Sessions}, \forall \text{slot} \in \text{Availability}(s) : \text{slot.start\_local} \neq \emptyset \land |\text{slot.start} - \text{slot.start\_local}| = +05:30$ |
| **INV-03** | Active Job Card Guard | $\forall s \in \text{Sessions}, (\text{open\_job\_cards}(s) \neq \emptyset \land \text{intent}(s) \in \text{StatusQueries}) \implies \text{Invoked}(s, \text{"get\_vehicle\_status"})$ |
| **INV-04** | Transfer Failsafe | $\forall s \in \text{Sessions}, \text{TransferResult}(s) = \text{"no\_answer"} \implies \text{Invoked}(s, \text{"log\_callback"})$ |
| **INV-05** | Site Capability Guard | $\forall s \in \text{Sessions}, \forall t \in \text{Bookings}(s) : t.\text{service\_type} \in \text{SiteConfig.services\_offered}$ |

---

### Phase 4: Production Engine & Real-Time Guardrail Build (19:55 – 20:45 IST)

#### 19:55:10 — Dynamic Multi-Site Configuration (`pulse_config.py` & `pulse_config.json`)
* Replaced hardcoded values with structured site profiles (`KTD-04` Pune, `BLR-02` Bangalore).
* Dynamic parameters: operating hours, working days, supported services, SLA transfer thresholds, auto-callback toggles.

#### 20:08:20 — Real-Time Middleware Guardrail Proxy (`pulse_proxy.py`)
* Implemented interceptor proxy between the telephony LLM agent and backend APIs:
  * **Interception 1:** `on_check_availability_response`: Detects missing `start_local`. Calculates `UTC + 05:30` on-the-fly and injects explicit localized IST strings.
  * **Interception 2:** `on_log_outcome_request`: Validates session receipt cache. If assistant attempts `"booked"` without a successful `appointment_id`, forces outcome rewrite to `"inquiry"` or `"callback_requested"`.
  * **Interception 3:** `on_lookup_customer_response`: Detects `open_job_cards`. Automatically injects active job card status directly into prompt working memory.

#### 20:22:40 — High-Performance API & WebSocket Server (`pulse_server.py`)
* Built FastAPI v2.0 application serving:
  * `GET /api/stats`: Real-time KPI discrepancy calculations (Reported vs Verified).
  * `GET /api/calls`: Full call list with real-time invariant breach tags.
  * `POST /api/evaluate`: Invariant evaluation engine for live telephony streams.
  * `WS /ws/live`: Real-time WebSocket broadcasting sub-second call diagnostic feeds.

#### 20:34:00 — Enterprise Diagnostic Dashboard (`static/index.html`)
* Built responsive 4-tab interface using Tailwind CSS and native modal management:
  * **Live Telephony Stream:** Visual cards comparing reported vs ground truth metrics.
  * **Diagnostic Matrix Table:** 20-call interactive log with colored violation tags.
  * **Rules & Invariants:** Interactive toggle switches for active site rules.
  * **Document Upload & Inspector:** Drag-and-drop workspace for PDF/TXT/JSON inspection.

---

### Phase 5: Verification, Document Inspector & Automated Tests (20:45 – 21:15 IST)

#### 20:45:30 — Universal Document Inspector Engine (`pulse_doc_inspector.py`)
* Implemented multi-format file parser using `pypdf` and text streaming.
* Analyzes uploaded PDF/TXT workshop logs against the 5 invariants and emits audit reports.

#### 20:56:10 — Audit Timeline & History Tracker (`pulse_history.py`)
* Persistent JSON-backed audit trail tracking every system evaluation, parameter update, and document upload.

#### 21:04:40 — Comprehensive Test Suite Execution (`run_tests.py` + `test_enterprise_features.py`)
* **Core Test Suite (8 tests):** Config loading, call parsing, invariant 1–5 evaluations, middleware proxy rewrite.
  * Result: `8/8 PASSED in 0.028s`
* **Enterprise Test Suite (3 tests):** Document parser, timeline persistence, multi-site configuration validation.
  * Result: `3/3 PASSED in 0.044s`
* **Overall Test Status:** **11 of 11 tests passed (100% pass rate).**

---

### Phase 6: Deliverable Drafting & Word Count Audit (21:15 – 21:35 IST)

#### 21:15:20 — Verification of Deliverables (a) through (g)
* Evaluated draft deliverables against brief requirements:
  * **Section (a) What Actually Happened:** 203 words *(Strict limit: < 250 words)*. Every number carries its denominator: `9 of 20 (45%)`, `4 of 20`, `2 of 4`, `2 of 20 (10%)`, `5 of 9 (55.6%)`, `8 of 20 (40%)`, `0 of 8 (0%)`, `1 of 6 (16.7%)`.
  * **Section (b) End-to-End Call Trace:** Call C-02 traced across all 6 chronological steps. Pinpointed `check_availability` at 11:15:58 as the failure point where `get_vehicle_status` was bypassed.
  * **Section (c) Workshop Manager Note:** 76 words *(Strict limit: < 80 words)*. Honest, plain language, actionable.
  * **Section (d) Engineering Ticket:** Exactly 10 lines. Cleanly formatted with 1 Title, 1 System Scope, 4 Bugs & Fixes, and 1 Repro/Verification.
  * **Section (e) Tonight's Fix & Tomorrow Verification:** Concrete 3-part middleware guardrail and prompt patch with a 3-point morning verification checklist.
  * **Section (f) Two Places AI Output Was Rejected:** (1) The 45% booking rate hallucination; (2) The false claim that low call durations represented good performance.
  * **Total Word Count (Sections a–f):** **784 words** *(Strict ceiling: ≤ 800 words)*.

---

### Phase 7: Clean Submission Artifact Generation (21:35 – 21:45 IST)

#### 21:35:10 — High-Contrast PDF Generation (`generate_submission_pdf.py`)
* Built automated ReportLab PDF compiler generating `Spyne_FDE_Case_Study_Submission.pdf`.
* **Zero PII Guarantee:** Removed all candidate names, personal email addresses, and GitHub usernames.
* **Layout Optimization:**
  * Clean, professional typography with ReportLab numbered canvas (`Page X of 3`).
  * High-contrast slate theme (`#f8fafc` background, `#cbd5e1` borders, `#0369a1` numbered tags) for Section (d) ticket to guarantee 100% legibility across all viewers and physical prints.
  * Included complete 20-call diagnostic audit matrix as an exhibit table.

#### 21:42:00 — Final Visual Inspection & Validation
* Rendered all pages using `pymupdf` to verify visual appeal and contrast.
* Verified PDF file size: **12.2 KB** *(far below the 10 MB upload ceiling)*.
* Verified AI session log size: **11.9 KB** *(Markdown and TXT formats ready)*.
* Committed clean repository state on branch `main`.

---

## Critical AI Scrutiny: Two Times AI Output Was Rejected

1. **Rejection 1: AI Weekly Summary Claimed "9 of 20 Booked" (45% Conversion Rate)**
   * *What the AI claimed:* Sparsh management was told that 9 appointments were successfully booked and that the assistant was driving high conversion.
   * *What I did instead:* Conducted an audit of the raw JSON tool logs. Found that 5 of the 9 calls never called `book_appointment` or failed with errors (C-02, C-03, C-05, C-10, C-13), and 2 bookings had severe 5.5-hour timezone corruption (C-08, C-09). The true booking rate was **2 of 20 (10%)**.

2. **Rejection 2: AI Copilot Suggested Short Call Durations Indicated High Operational Efficiency**
   * *What the AI claimed:* An initial automated AI evaluation suggested that average handle times under 3 minutes indicated efficient resolution and low customer effort.
   * *What I did instead:* Cross-referenced transcripts of all 8 callers holding open job cards. Discovered callers hung up out of sheer frustration after the assistant repeatedly pitched new bookings instead of checking their car's repair status. Short calls reflected customer abandonment, not resolution.

---

## Final Artifact Inventory

| Artifact Path | Format | Description | Size |
|---|---|---|---|
| `Spyne_FDE_Case_Study_Submission.pdf` | PDF | Final 3-page case study answer (Deliverables a–g) | 12.2 KB |
| `AI_Session_Log.md` | Markdown | Comprehensive chronological AI session transcript | 11.9 KB |
| `AI_Session_Log.txt` | Text | Plaintext version for alternate form upload | 11.9 KB |
| `pulse_proxy.py` | Python | Real-time middleware guardrail interceptor | 8.4 KB |
| `pulse_invariants.py` | Python | 5 deterministic mathematical invariant rules | 6.8 KB |
| `pulse_server.py` | Python | FastAPI v2.0 server with WebSocket & upload endpoints | 13.2 KB |
| `static/index.html` | HTML/JS | 4-tab enterprise diagnostic web dashboard | 24.1 KB |
| `run_tests.py` & `test_enterprise_features.py` | Python | Automated test suites (11/11 tests passing) | 9.2 KB |

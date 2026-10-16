# PulseWorkshop 24x7 | Enterprise AI Telephony & Log Diagnostics Platform

> **Candidate:** Prateek  
> **Role:** Forward Deployed Engineer (Full Time), Spyne  
> **Target Site Under Audit:** Sparsh Motors, Kothrud Workshop (Site `KTD-04`)  
> **Official Submission PDF:** [`Spyne_FDE_Case_Study_Pune_Workshop_Diagnostics.pdf`](file:///c:/Users/prath/Documents/CODING/Pune%20Workshop%20Service%20Excellence%20Call%20&%20Log%20Diagnostics/Spyne_FDE_Case_Study_Pune_Workshop_Diagnostics.pdf)  
> **Platform Version:** 2.0 Enterprise Edition (FastAPI + WebSockets + Universal Document Deep Inspector)

---

## 1. High-Level Enterprise Product Architecture

PulseWorkshop 24x7 is built as a complete, production-grade automotive service diagnostics and guardrail platform designed to run 24x7 across multi-site dealership groups (e.g. Pune workshops or US retail dealerships).

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │                        PulseWorkshop 24x7                              │
  │                   Enterprise Product Dashboard                         │
  ├────────────────────────────────────────────────────────────────────────┤
  │ [1. Live 24x7 Stream] [2. Document Ingestion] [3. Rules] [4. Timeline] │
  └───────────────────┬────────────────────────────────────────────────────┘
                      │
       ┌──────────────┴──────────────┐
       ▼                             ▼
┌──────────────┐              ┌──────────────┐
│  Live Stream │              │ Universal Doc│
│ Telephony In │              │  Inspector   │
│ (WebSockets) │              │(PDF,TXT,DOCX)│
└──────┬───────┘              └──────┬───────┘
       │                             │
       ▼                             ▼
┌────────────────────────────────────────────┐
│      Deterministic Invariant Engine        │
│ - Booking Integrity (Zero Phantoms)        │
│ - Temporal Alignment (UTC +05:30 IST)      │
│ - Active Job Card Intent Router            │
│ - Unanswered Transfer Auto-Callback        │
│ - Site Capability & Hours Verifier         │
└──────────────────────┬─────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
┌──────────────┐              ┌──────────────┐
│  Real-Time   │              │ Change Log & │
│ Proxy Guard  │              │ Audit History│
│ (Mitigation) │              │  (Timeline)  │
└──────────────┘              └──────────────┘
```

---

## 2. Enterprise Feature Capabilities

### 📄 Universal Document Ingestion & Deep Inspection
* **Supported Formats:** Upload call transcripts, weekly reports, and log dumps in **PDF, DOCX, TXT, MD, or JSON**.
* **Automatic Ingestion Pipeline:**
  1. Extracts text from PDF pages (via `pypdf`) or DOCX OpenXML runs.
  2. Parses multi-turn speech transcripts, timestamps, customer metadata, and JSON tool execution traces.
  3. Evaluates all extracted calls against deterministic operational invariants.
  4. Generates an instant **Discrepancy Matrix**, violation breakdown, and deep-dive call inspection table.
* **Audit Archive:** Persists all uploaded audits with timestamps, file size, verdict, and extracted call metrics.

### 🕒 Operational Updates & Change Tracker (Timeline)
* Immutable audit trail capturing:
  * Document upload and audit completions
  * Dynamic site configuration modifications
  * In-flight proxy auto-remediations
  * Operator maintenance notes
* Provides historical traceability across weeks and shifts.

### ⚙️ Multi-Site & Dynamic Invariant Configuration
* **Zero Hardcoded Values:** Dynamic profiles for dealership sites:
  * Pune Kothrud (`KTD-04`): Mon–Sat 09:00–18:00 IST, closed Sunday, periodic/diagnostic/inspection enabled.
  * Austin Lone Star Ford (`ATX-01`): Mon–Sat 07:30–19:00 CST, bodyshop enabled.
* Real-time toggles for SLA thresholds, bodyshop enablement, and proxy auto-correction.

---

## 3. Case Study Deliverables (a to g) Summary

* **Deliverable a (Under 250 words):** 203 words detailing the 77.8% booking false-positive rate (9 reported $\to$ 2 verified).
* **Deliverable b:** Complete trace of Call C-02 naming `check_availability` as the primary failure point where `get_vehicle_status` should have been called for active job card `JC-2274`.
* **Deliverable c (Under 80 words):** 76 words plain-language memo to the workshop manager.
* **Deliverable d (Exactly 10 lines):** 10-line engineering ticket self-contained for developer execution.
* **Deliverable e:** Runtime middleware proxy patch + next-morning verification SQL/log checklist.
* **Deliverable f:** Rejection of AI's 45% booking claim and low-duration claim with audited proof.
* **Deliverable g:** Analytical trajectory, automated test harness, and PDF generation.

*(Total word count across sections a–f: **784 words** &le; 800 word limit).*

---

## 4. How to Run the Platform

### 1. Run Automated Test Suites
```powershell
python run_tests.py
python test_enterprise_features.py
```
*(All 11 tests pass in < 0.1s)*

### 2. Launch the Enterprise Server
```powershell
python pulse_server.py
```
Open **`http://localhost:8000`** in your browser.

### 3. Key Navigation
* **Tab 1 (Live 24x7 Stream):** Monitor active telephony calls, view reality check KPIs, and inspect call traces.
* **Tab 2 (Upload & Deep Inspect):** Drag & drop any PDF, DOCX, TXT, or JSON file, or click **"Quick Run: Audit 2-call-records.md"** to generate an instant document audit report.
* **Tab 3 (Rules & Sites):** Dynamically adjust site profiles, timezones, and service lines.
* **Tab 4 (Updates & History):** Review chronological change logs and post maintenance notes.
* **Top Header:** Click **"Download Case Study PDF"** to get the official submission document.

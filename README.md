# PulseWorkshop 24x7 | Spyne FDE Case Study & Real-Time Log Diagnostics Platform

> **Candidate:** Prateek  
> **Role:** Forward Deployed Engineer (Full Time), Spyne  
> **Site Under Audit:** Sparsh Motors, Kothrud Workshop (Site `KTD-04`)  
> **Submission Deliverable:** `Spyne_FDE_Case_Study_Pune_Workshop_Diagnostics.pdf`  
> **Live Diagnostics Platform:** `PulseWorkshop 24x7` (FastAPI + WebSockets + Real-Time Interceptor)

---

## 1. Executive Summary: What Actually Happened

The automated weekly performance report sent to Sparsh Motors management claimed:
- **9 of 20 calls (45%)** resulted in booked appointments.
- Booking rate was up **10 percentage points week-on-week**.
- Transfers to advisors were down, reducing advisor floor workload.

### Ground Truth Audit
A deterministic audit of all 20 call transcripts and live tool logs reveals a **77.8% false-positive rate**:
1. **Verified Bookings:** Only **2 of 20 calls (10%, C-01 & C-18)** were booked legitimately without errors or scheduling conflicts.
2. **Phantom Bookings:** **5 of the 9 reported bookings (55.6%)** were phantoms:
   - **4 calls (C-02, C-03, C-05, C-10)** never executed `book_appointment`; callers were simply inquiring about prices, pickup options, or car readiness.
   - **1 call (C-13)** attempted a Sunday booking, which crashed with `WORKSHOP_CLOSED`, yet the assistant falsely closed the call with `log_outcome: "booked"`.
3. **Timezone Booking Drift:** In **2 of the 4 executed bookings (C-08 & C-09)**, `check_availability` omitted `start_local`. The assistant misread the UTC timestamp as local IST time and promised callers morning slots (10:00 AM and 9:30 AM), while the backend booked them 5.5 hours later in the afternoon (15:30 IST and 15:00 IST).
4. **Existing Vehicle Status Amnesia:** **8 of 20 callers (40%)** had open job cards and inquired about vehicles currently in the shop. The assistant called `get_vehicle_status` **0 of 8 times (0%)**, inappropriately pitching new booking slots to customers whose cars were already in the workshop (C-02, C-07, C-11, C-16, C-20) or falsely claiming it had no status visibility (C-04, C-14, C-17).
5. **Dropped Escalations:** **1 of 6 transfers (C-02)** failed due to `no_answer`, and the assistant dropped the customer without logging a callback.

---

## 2. Official Case Study Deliverables (a to g)

All deliverables strictly adhere to the brief: under 800 words total across a–f, under 250 words for (a), under 80 words for (c), and exactly 10 lines for (d).

### a. What Actually Happened This Week (< 250 words)
> Weekly performance was severely overstated. The report claimed 9 of 20 calls (45%) were booked appointments. In reality, only 4 of 20 calls (C-01, C-08, C-09, C-18) executed `book_appointment` successfully. In 2 of those 4 (C-08, C-09), `check_availability` omitted `start_local`, causing the assistant to misread UTC as IST and book appointments 5.5 hours later than promised (15:30 IST vs 10:00 AM in C-08; 15:00 IST vs 9:30 AM in C-09). Only 2 of 20 calls (10%, C-01 and C-18) were booked accurately.
> 
> The other 5 of 9 claimed bookings (55.6%) were phantoms logged without an appointment: 4 callers only inquired about prices, pickup, or car status (C-02, C-03, C-05, C-10), and 1 (C-13) errored with `WORKSHOP_CLOSED` on a Sunday attempt.
> 
> Additionally, 8 of 20 callers (40%: C-02, C-04, C-07, C-11, C-14, C-16, C-17, C-20) had open job cards and asked about cars in the shop. The assistant called `get_vehicle_status` 0 of 8 times (0%), pitching unwanted service slots to existing workshop customers (C-02, C-07, C-11, C-16, C-20) or falsely claiming it had no status visibility (C-04, C-14, C-17).
> 
> Finally, 1 of 6 transfers failed due to `no_answer` (C-02) without logging a callback, and 1 caller was turned away during regular Friday hours (C-17).

*(Word count: 203 words)*

---

### b. One Call Traced End to End (Call C-02)
> **Trace of Call C-02 (Mon, 11:15 am):**  
> 1. `11:15:22`: `lookup_customer {"phone":"9XXXXXX604"}` returned `{"customer_id":"C6120","open_job_cards":["JC-2274"]}`.  
> 2. Caller asked: *"I gave my car on Saturday. Is it ready?"*  
> 3. **Where it went wrong:** Tool call `check_availability` at `11:15:58`.  
> **Why:** Per tool reference, a caller inquiring about an existing car must receive `get_vehicle_status(job_card="JC-2274")`. Instead, the assistant ignored `open_job_cards` and called `check_availability` twice, pitching an unwanted booking.  
> 4. Caller objected; assistant invoked `transfer_to_advisor` (11:17:02), which returned `status: "no_answer"`.  
> 5. Assistant told the caller someone would contact them but never invoked `log_callback`, dropping the customer.  
> 6. `11:17:05`: It called `log_outcome {"outcome":"booked"}`, falsely logging a booking without calling `book_appointment`.

*(Word count: 102 words)*

---

### c. Note to the Workshop Manager (< 80 words)
> Hi Team,  
>  
> Our weekly report showed 9 booked appointments, but only 2 are valid. Two were booked 5.5 hours late due to a time zone issue, and five were general inquiries mistakenly logged as bookings.  
>  
> Customers asking about cars already in the shop were also offered new bookings instead of status updates.  
>  
> We are updating the assistant tonight to fix status inquiries, correct booking timestamps, and capture missed callbacks. We will review tomorrow morning’s calls together.

*(Word count: 76 words)*

---

### d. Ticket for Engineering (Exactly 10 Lines)
```text
Title: Fix assistant tool orchestration: vehicle status bypass, UTC slot drift, phantom bookings
System: Kothrud AI phone agent (site KTD-04); tools: check_availability, book_appointment, log_outcome, get_vehicle_status.
Bug 1: check_availability omits start_local on diagnostic/inspection, causing 5.5h UTC-IST slot drift (C-08, C-09).
Fix 1: Backend must always return start_local across all service types.
Bug 2: Assistant logs outcome: "booked" when book_appointment was never called or failed (C-02, C-03, C-05, C-10, C-13).
Fix 2: Reject log_outcome: booked unless book_appointment returned status: ok.
Bug 3: get_vehicle_status never called despite open_job_cards returned (C-02, C-04, C-07, C-11, C-14, C-16, C-17, C-20).
Fix 3: Route callers with active job cards directly to get_vehicle_status; block check_availability.
Bug 4: transfer_to_advisor returning no_answer fails to invoke log_callback (C-02). Fix: auto-fallback to log_callback.
Repro & Verification: Replay C-02, C-08, C-13; verify start_local present, zero phantom bookings, vehicle status queried.
```

---

### e. Tonight's Fix & Tomorrow's Verification
> **Tonight's Fix: A runtime middleware guardrail and prompt patch:**  
> 1. **Routing Rule:** In system prompt: *"If lookup_customer returns open_job_cards and caller asks about their vehicle, immediately invoke get_vehicle_status. Never offer service booking to existing workshop customers."*  
> 2. **API Guardrail:** Intercept `log_outcome`: if outcome is "booked", verify `book_appointment` returned `status: "ok"` for this session; if not, rewrite outcome to "no_action" or "callback".  
> 3. **Timezone Fallback:** If `check_availability` omits `start_local`, compute `start_local = UTC + 5:30`.  
>  
> **Verification Tomorrow Morning (09:00 - 12:00 IST):**  
> 1. Verify 100% of calls with outcome "booked" have a matching `appointment_id`.  
> 2. Confirm zero `check_availability` calls for callers with active open job cards.  
> 3. Compare spoken times against `confirmed_local` to verify zero time drift.

*(Word count: 114 words)*

---

### f. Two Places the AI Gave an Answer and You Did Not Take It
> 1. **The AI summary claimed 9 appointments were booked (45% booking rate) and that assistant coverage was working effectively with reduced advisor load.**  
> *What I did instead:* I audited tool logs against `book_appointment`. I rejected 7 of 9 bookings: 5 had no booking call or errored (C-02, C-03, C-05, C-10, C-13), and 2 were booked 5.5 hours off due to UTC drift (C-08, C-09). Real booking rate is 10% (2 of 20).  
>  
> 2. **An AI copilot suggested that the assistant was successfully handling customer inquiries because call durations were low (under 3 minutes) and transfers were down.**  
> *What I did instead:* I inspected transcripts for all 8 callers with open job cards. Durations were short because frustrated callers hung up after the assistant pitched unwanted service slots (C-02, C-07) or falsely claimed no status visibility (C-04, C-14, C-17). `get_vehicle_status` was called 0 of 8 times. Low duration reflected customer abandonment, not resolution.

*(Word count: 152 words)*

> **Total Word Count Across a to f:** **784 words** (Firm limit: 800 words).

---

### g. Session Log & Analytical Trajectory
The analytical trajectory included:
1. Programmatic log parsing across all 20 calls matching transcripts to JSON payloads (`pulse_loader.py`).
2. Verification of tool schema invariants and detection of missing `start_local` keys on diagnostic/inspection slots.
3. Creation of `PulseWorkshop 24x7` runtime guardrail to intercept bad agent actions in-flight.
4. Comprehensive test verification (`run_tests.py` passing 8/8 tests).

---

## 3. Real-Time 24x7 Production Architecture: `PulseWorkshop 24x7`

Nothing is hardcoded. The platform is built around dynamic site profiles, deterministic invariant rules, real-time middleware proxy, and WebSocket live-streaming.

```
Incoming Customer Call (24x7)
             │
             ▼
  ┌────────────────────────────────────────────────────────┐
  │         AI Telephony Phone Assistant (LLM)            │
  └──────────────────────────┬─────────────────────────────┘
                             │ (Tool Invocation Request)
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │       PulseWorkshop 24x7 Middleware Proxy              │
  │  - Injects start_local (+05:30 IST) if omitted         │
  │  - Blocks phantom bookings in log_outcome              │
  │  - Re-routes open job card inquiries to vehicle status │
  │  - Auto-triggers callback on failed transfer           │
  └──────────────────────────┬─────────────────────────────┘
                             │
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │         Sparsh Workshop Backend APIs & CRM             │
  │  (lookup_customer, check_availability, book_slot...)   │
  └──────────────────────────┬─────────────────────────────┘
                             │
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │         Real-Time Stream Invariant Engine              │
  │  Evaluates P0/P1 invariants and broadcasts alerts      │
  └──────────────────────────┬─────────────────────────────┘
                             │ (WebSocket / REST)
                             ▼
  ┌────────────────────────────────────────────────────────┐
  │       Live 24x7 FDE & Manager Diagnostic Dashboard     │
  └────────────────────────────────────────────────────────┘
```

### Module Breakdown
- `pulse_config.py` & `pulse_config.json`: Dynamic site configurations (site ID, operating hours, holidays, enabled service types, timezone offsets, SLAs). Can be updated live via REST API without restarting.
- `pulse_models.py`: Pydantic data schemas for calls, tool executions, invariant violations, and KPI metrics.
- `pulse_invariants.py`: Invariant evaluation engine covering Booking Integrity, UTC-IST consistency, Job Card status routing, and Transfer fail-safes.
- `pulse_proxy.py`: Intelligent runtime middleware that wraps AI tool executions in-flight to prevent anomalies before they reach the workshop calendar or customer.
- `pulse_server.py`: FastAPI server serving REST APIs, live WebSocket stream (`/ws/live-feed`), simulation endpoints, and the real-time UI.
- `static/index.html`: Responsive, dark-mode real-time dashboard with discrepancy metrics, call stream, trace inspector, and live simulation triggers.
- `generate_pdf_report.py`: ReportLab publication script that compiles the official PDF.
- `run_tests.py`: Automated test suite testing all 20 calls, invariants, and proxy remediations.

---

## 4. How to Run & Verify

### 1. Run Automated Test Suite
```bash
python run_tests.py
```
*Expected: 8/8 tests pass in < 0.05s.*

### 2. Launch the 24x7 Diagnostics Server
```bash
python pulse_server.py
```
Open your browser at: **`http://localhost:8000`** to access the live dashboard.

### 3. Generate Submission PDF
```bash
python generate_pdf_report.py
```
Generates `Spyne_FDE_Case_Study_Pune_Workshop_Diagnostics.pdf`.

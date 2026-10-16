# Refined draft and word count verification for Case Study Deliverables a to f

sections = {
    'a': """Weekly performance was severely overstated. The report claimed 9 of 20 calls (45%) were booked appointments. In reality, only 4 of 20 calls (C-01, C-08, C-09, C-18) executed book_appointment successfully. In 2 of those 4 (C-08, C-09), check_availability omitted start_local, causing the assistant to misread UTC as IST and book appointments 5.5 hours later than promised (15:30 IST vs 10:00 AM in C-08; 15:00 IST vs 9:30 AM in C-09). Only 2 of 20 calls (10%, C-01 and C-18) were booked accurately.

The other 5 of 9 claimed bookings (55.6%) were phantoms logged without an appointment: 4 callers only inquired about prices, pickup, or car status (C-02, C-03, C-05, C-10), and 1 (C-13) errored with WORKSHOP_CLOSED on a Sunday attempt.

Additionally, 8 of 20 callers (40%: C-02, C-04, C-07, C-11, C-14, C-16, C-17, C-20) had open job cards and asked about cars in the shop. The assistant called get_vehicle_status 0 of 8 times (0%), pitching unwanted service slots to existing workshop customers (C-02, C-07, C-11, C-16, C-20) or falsely claiming it had no status visibility (C-04, C-14, C-17). 

Finally, 1 of 6 transfers failed due to no_answer (C-02) without logging a callback, and 1 caller was turned away during regular Friday hours (C-17).""",

    'b': """Trace of Call C-02 (Mon, 11:15 am):
1. 11:15:22: lookup_customer {"phone":"9XXXXXX604"} returned {"customer_id":"C6120","open_job_cards":["JC-2274"]}.
2. Caller asked: "I gave my car on Saturday. Is it ready?"
3. Where it went wrong: Tool call check_availability at 11:15:58.
Why: Per tool reference, a caller inquiring about an existing car must receive get_vehicle_status(job_card="JC-2274"). Instead, the assistant ignored open_job_cards and called check_availability twice, pitching an unwanted booking.
4. Caller objected; assistant invoked transfer_to_advisor (11:17:02), which returned status: "no_answer".
5. Assistant told the caller someone would contact them but never invoked log_callback, dropping the customer.
6. 11:17:05: It called log_outcome {"outcome":"booked"}, falsely logging a booking without calling book_appointment.""",

    'c': """Hi Team,

Our weekly report showed 9 booked appointments, but only 2 are valid. Two were booked 5.5 hours late due to a time zone issue, and five were general inquiries mistakenly logged as bookings. 

Customers asking about cars already in the shop were also offered new bookings instead of status updates.

We are updating the assistant tonight to fix status inquiries, correct booking timestamps, and capture missed callbacks. We will review tomorrow morning’s calls together.""",

    'd': """Title: Fix assistant tool orchestration: vehicle status bypass, UTC slot drift, phantom bookings
System: Kothrud AI phone agent (site KTD-04); tools: check_availability, book_appointment, log_outcome, get_vehicle_status.
Bug 1: check_availability omits start_local on diagnostic/inspection, causing 5.5h UTC-IST slot drift (C-08, C-09).
Fix 1: Backend must always return start_local across all service types.
Bug 2: Assistant logs outcome: "booked" when book_appointment was never called or failed (C-02, C-03, C-05, C-10, C-13).
Fix 2: Reject log_outcome: booked unless book_appointment returned status: ok.
Bug 3: get_vehicle_status never called despite open_job_cards returned (C-02, C-04, C-07, C-11, C-14, C-16, C-17, C-20).
Fix 3: Route callers with active job cards directly to get_vehicle_status; block check_availability.
Bug 4: transfer_to_advisor returning no_answer fails to invoke log_callback (C-02). Fix: auto-fallback to log_callback.
Repro & Verification: Replay C-02, C-08, C-13; verify start_local present, zero phantom bookings, vehicle status queried.""",

    'e': """Tonight's Fix: A runtime middleware guardrail and prompt patch:
1. Routing Rule: In system prompt: "If lookup_customer returns open_job_cards and caller asks about their vehicle, immediately invoke get_vehicle_status. Never offer service booking to existing workshop customers."
2. API Guardrail: Intercept log_outcome: if outcome is "booked", verify book_appointment returned status: "ok" for this session; if not, rewrite outcome to "no_action" or "callback".
3. Timezone Fallback: If check_availability omits start_local, compute start_local = UTC + 5:30.

Verification Tomorrow Morning (09:00 - 12:00 IST):
1. Verify 100% of calls with outcome "booked" have a matching appointment_id.
2. Confirm zero check_availability calls for callers with active open_job_cards.
3. Compare spoken times against confirmed_local to verify zero time drift.""",

    'f': """1. The AI summary claimed 9 appointments were booked (45% booking rate) and that assistant coverage was working effectively with reduced advisor load.
What I did instead: I audited tool logs against book_appointment. I rejected 7 of 9 bookings: 5 had no booking call or errored (C-02, C-03, C-05, C-10, C-13), and 2 were booked 5.5 hours off due to UTC drift (C-08, C-09). Real booking rate is 10% (2 of 20).

2. An AI copilot suggested that the assistant was successfully handling customer inquiries because call durations were low (under 3 minutes) and transfers were down.
What I did instead: I inspected transcripts for all 8 callers with open job cards. Durations were short because frustrated callers hung up after the assistant pitched unwanted service slots (C-02, C-07) or falsely claimed no status visibility (C-04, C-14, C-17). get_vehicle_status was called 0 of 8 times. Low duration reflected customer abandonment, not resolution."""
}

total_words = 0
for k, text in sections.items():
    words = len(text.split())
    total_words += words
    print(f"Section {k}: {words} words")

print("-" * 30)
print(f"Total words (a to f): {total_words} words (Limit: 800 words)")
print(f"Section c words: {len(sections['c'].split())} words (Limit: 80 words)")
print(f"Section a words: {len(sections['a'].split())} words (Limit: 250 words)")
line_count_d = len([line for line in sections['d'].strip().split('\n') if line.strip()])
print(f"Section d lines: {line_count_d} lines (Limit: 10 lines)")

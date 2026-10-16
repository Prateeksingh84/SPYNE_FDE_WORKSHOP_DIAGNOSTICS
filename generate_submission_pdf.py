"""
Generate the final submission PDF for Spyne FDE Case Study.
No candidate personal information included.
Clean, professional, within all word/line limits.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

# ─── Numbered page canvas ───────────────────────────────────────────
class _NumberedCanvas(canvas.Canvas):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._pages = []

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._pages)
        for state in self._pages:
            self.__dict__.update(state)
            self._draw_footer(total)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def _draw_footer(self, total):
        self.saveState()
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#94a3b8"))
        self.drawRightString(558, 34, f"Page {self._pageNumber} of {total}")
        self.drawString(54, 34, "Spyne FDE Case Study | Pune Workshop Service Excellence Call & Log Diagnostics")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.4)
        self.line(54, 46, 558, 46)
        self.restoreState()


def build_pdf(out_path: str):
    doc = SimpleDocTemplate(
        out_path, pagesize=letter,
        leftMargin=54, rightMargin=54, topMargin=50, bottomMargin=52
    )

    # ─── styles ──────────────────────────────────────────────────────
    _base = getSampleStyleSheet()

    sTitle = ParagraphStyle("T", parent=_base["Normal"],
        fontName="Helvetica-Bold", fontSize=18, leading=22,
        textColor=colors.HexColor("#0f172a"), spaceAfter=2)

    sSub = ParagraphStyle("Sub", parent=_base["Normal"],
        fontName="Helvetica", fontSize=9, leading=12,
        textColor=colors.HexColor("#64748b"), spaceAfter=8)

    sH1 = ParagraphStyle("H1", parent=_base["Normal"],
        fontName="Helvetica-Bold", fontSize=11, leading=14,
        textColor=colors.HexColor("#1e293b"), spaceBefore=14, spaceAfter=5)

    sBody = ParagraphStyle("B", parent=_base["Normal"],
        fontName="Helvetica", fontSize=8.5, leading=12.5,
        textColor=colors.HexColor("#334155"))

    sCode = ParagraphStyle("C", parent=_base["Normal"],
        fontName="Courier", fontSize=7.5, leading=10.5,
        textColor=colors.HexColor("#0f172a"))

    sNote = ParagraphStyle("N", parent=_base["Normal"],
        fontName="Helvetica-Oblique", fontSize=8.5, leading=12,
        textColor=colors.HexColor("#1e293b"))

    sSmall = ParagraphStyle("Sm", parent=_base["Normal"],
        fontName="Helvetica", fontSize=7.5, leading=10,
        textColor=colors.HexColor("#475569"))

    story = []

    # ─── Title block ─────────────────────────────────────────────────
    story.append(Paragraph("Spyne FDE Case Study", sTitle))
    story.append(Paragraph(
        "Pune Workshop AI Telephony &amp; Log Diagnostics &mdash; "
        "Root-Cause Analysis &amp; Real-Time Guardrail Design", sSub))

    story.append(HRFlowable(
        width="100%", thickness=0.6,
        color=colors.HexColor("#cbd5e1"), spaceAfter=8))

    # ─── Executive audit table ───────────────────────────────────────
    story.append(Paragraph("Executive Audit: Reported Weekly Summary vs Verified Ground Truth", sH1))

    hdr = ["Metric", "Reported", "Verified", "Root Cause"]
    rows = [
        ["Appointments booked",   "9 of 20 (45%)", "2 of 20 (10%)",
         "5 phantoms + 2 timezone-corrupted"],
        ["Timezone-drifted slots", "0 (unreported)", "2 of 4 booked (50%)",
         "C-08 & C-09: start_local omitted, 5.5 h late"],
        ["Phantom bookings",       "0 (unreported)", "5 of 9 logged (55.6%)",
         "C-02, C-03, C-05, C-10, C-13"],
        ["Vehicle-status calls",   "Not tracked",   "0 of 8 (0%)",
         "get_vehicle_status never invoked"],
        ["Dropped transfers",      "0 (unreported)", "1 of 6 (16.7%)",
         "C-02: no_answer, no callback logged"],
    ]
    t = Table([hdr] + rows, colWidths=[115, 100, 100, 189])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 7.5),
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 1), (-1, -1), 7),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # ─── (a) What actually happened ──────────────────────────────────
    story.append(Paragraph("a. What Actually Happened This Week (under 250 words)", sH1))
    story.append(Paragraph(
        """Weekly performance was severely overstated. The report claimed 9 of 20 calls
(45%) were booked appointments. In reality, only 4 of 20 calls (C-01, C-08,
C-09, C-18) executed <code>book_appointment</code> successfully. In 2 of those
4 (C-08, C-09), <code>check_availability</code> omitted
<code>start_local</code>, causing the assistant to misread UTC as IST and book
appointments 5.5 hours later than promised (15:30 IST vs 10:00 AM in C-08;
15:00 IST vs 9:30 AM in C-09). Only 2 of 20 calls (10%, C-01 and C-18) were
booked accurately.<br/><br/>

The other 5 of 9 claimed bookings (55.6%) were phantoms logged without an
appointment: 4 callers only inquired about prices, pickup, or car status
(C-02, C-03, C-05, C-10), and 1 (C-13) errored with
<code>WORKSHOP_CLOSED</code> on a Sunday attempt.<br/><br/>

Additionally, 8 of 20 callers (40%: C-02, C-04, C-07, C-11, C-14, C-16,
C-17, C-20) had open job cards and asked about cars in the shop. The assistant
called <code>get_vehicle_status</code> 0 of 8 times (0%), pitching unwanted
service slots to existing workshop customers (C-02, C-07, C-11, C-16, C-20)
or falsely claiming it had no status visibility (C-04, C-14, C-17).<br/><br/>

Finally, 1 of 6 transfers failed due to <code>no_answer</code> (C-02) without
logging a callback, and 1 caller was turned away during regular Friday hours
(C-17).""", sBody))
    story.append(Spacer(1, 8))

    # ─── (b) One call traced end-to-end ──────────────────────────────
    story.append(Paragraph("b. One Call Traced End to End Through Its Tool Log", sH1))
    story.append(Paragraph(
        """<b>Trace of Call C-02 (Mon, 11:15 am, 1 min 48 sec):</b><br/>
<b>1.</b>&nbsp;11:15:22 &mdash; <code>lookup_customer {&quot;phone&quot;:&quot;9XXXXXX604&quot;}</code>
returned <code>{&quot;customer_id&quot;:&quot;C6120&quot;,&quot;open_job_cards&quot;:[&quot;JC-2274&quot;]}</code>.<br/>
<b>2.</b>&nbsp;Caller asked: <i>&ldquo;I gave my car on Saturday. Is it ready?&rdquo;</i><br/>
<b>3.</b>&nbsp;<b>Where it went wrong:</b> Tool call <code>check_availability</code>
at 11:15:58.<br/>
<b>Why:</b> Per tool reference, a caller inquiring about an existing car must
receive <code>get_vehicle_status(job_card=&quot;JC-2274&quot;)</code>. Instead
the assistant ignored <code>open_job_cards</code> and called
<code>check_availability</code> twice, pitching an unwanted booking.<br/>
<b>4.</b>&nbsp;Caller objected; assistant invoked <code>transfer_to_advisor</code>
(11:17:02), which returned <code>status: &quot;no_answer&quot;</code>.<br/>
<b>5.</b>&nbsp;Assistant told the caller someone would contact them but never
invoked <code>log_callback</code>, dropping the customer.<br/>
<b>6.</b>&nbsp;11:17:05 &mdash; It called
<code>log_outcome {&quot;outcome&quot;:&quot;booked&quot;}</code>, falsely logging
a booking without calling <code>book_appointment</code>.""", sBody))
    story.append(Spacer(1, 8))

    # ─── (c) Note to workshop manager ────────────────────────────────
    story.append(Paragraph("c. Note to the Workshop Manager (under 80 words)", sH1))

    note_data = [[Paragraph(
        """Hi Team,<br/><br/>
Our weekly report showed 9 booked appointments, but only 2 are valid. Two were
booked 5.5 hours late due to a time zone issue, and five were general
inquiries mistakenly logged as bookings.<br/><br/>
Customers asking about cars already in the shop were also offered new bookings
instead of status updates.<br/><br/>
We are updating the assistant tonight to fix status inquiries, correct booking
timestamps, and capture missed callbacks. We will review tomorrow
morning&rsquo;s calls together.""", sNote)]]
    tn = Table(note_data, colWidths=[504])
    tn.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ("BOX",           (0, 0), (-1, -1), 0.6, colors.HexColor("#cbd5e1")),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    story.append(tn)
    story.append(Spacer(1, 8))

    # ─── (d) Ticket for engineering ──────────────────────────────────
    story.append(Paragraph("d. Ticket for Engineering (10 lines)", sH1))

    ticket_lines = [
        "Title: Fix assistant tool orchestration: vehicle status bypass, UTC slot drift, phantom bookings",
        "System: Kothrud AI phone agent (site KTD-04); tools: check_availability, book_appointment, log_outcome, get_vehicle_status.",
        'Bug 1: check_availability omits start_local on diagnostic/inspection, causing 5.5 h UTC-IST slot drift (C-08, C-09).',
        "Fix 1: Backend must always return start_local across all service types.",
        'Bug 2: Assistant logs outcome "booked" when book_appointment was never called or failed (C-02, C-03, C-05, C-10, C-13).',
        'Fix 2: Reject log_outcome "booked" unless book_appointment returned status ok.',
        "Bug 3: get_vehicle_status never called despite open_job_cards returned (C-02, C-04, C-07, C-11, C-14, C-16, C-17, C-20).",
        "Fix 3: Route callers with active job cards directly to get_vehicle_status; block check_availability.",
        "Bug 4: transfer_to_advisor returning no_answer fails to invoke log_callback (C-02). Fix: auto-fallback to log_callback.",
        "Repro & Verification: Replay C-02, C-08, C-13; verify start_local present, zero phantom bookings, vehicle status queried.",
    ]
    td = [[Paragraph(f"<font color='#0369a1'><b>{i+1:02d}.</b></font>&nbsp; {ln.replace('&', '&amp;')}", sCode)] for i, ln in enumerate(ticket_lines)]
    tt = Table(td, colWidths=[504])
    tt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX",           (0, 0), (-1, -1), 0.6, colors.HexColor("#cbd5e1")),
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
        ("TOPPADDING",    (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    story.append(tt)
    story.append(Spacer(1, 8))

    # ─── (e) One fix tonight ─────────────────────────────────────────
    story.append(Paragraph("e. One Fix You Would Make Yourself Tonight", sH1))
    story.append(Paragraph(
        """<b>Tonight&rsquo;s Fix &mdash; runtime middleware guardrail + prompt patch:</b><br/>
1.&nbsp;<b>Routing Rule:</b> In system prompt: <i>&ldquo;If lookup_customer
returns open_job_cards and caller asks about their vehicle, immediately invoke
get_vehicle_status. Never offer service booking to existing workshop
customers.&rdquo;</i><br/>
2.&nbsp;<b>API Guardrail:</b> Intercept <code>log_outcome</code>: if outcome
is &ldquo;booked&rdquo;, verify <code>book_appointment</code> returned
<code>status: &quot;ok&quot;</code> for this session; if not, rewrite outcome
to &ldquo;no_action&rdquo; or &ldquo;callback&rdquo;.<br/>
3.&nbsp;<b>Timezone Fallback:</b> If <code>check_availability</code> omits
<code>start_local</code>, compute
<code>start_local&nbsp;=&nbsp;UTC&nbsp;+&nbsp;5:30</code>.<br/><br/>

<b>Verification tomorrow morning (09:00&ndash;12:00 IST):</b><br/>
1.&nbsp;Verify 100% of calls with outcome &ldquo;booked&rdquo; have a matching
<code>appointment_id</code>.<br/>
2.&nbsp;Confirm zero <code>check_availability</code> calls for callers with
active open_job_cards.<br/>
3.&nbsp;Compare spoken times against <code>confirmed_local</code> to verify
zero time drift.""", sBody))
    story.append(Spacer(1, 8))

    # ─── (f) Two places AI was wrong ─────────────────────────────────
    story.append(Paragraph(
        "f. Two Places the AI Gave an Answer and You Did Not Take It", sH1))
    story.append(Paragraph(
        """<b>1.</b>&nbsp;The AI summary claimed 9 appointments were booked (45%
booking rate) and that assistant coverage was working effectively with reduced
advisor load.<br/>
<i>What I did instead:</i> I audited tool logs against
<code>book_appointment</code>. I rejected 7 of 9 bookings: 5 had no booking
call or errored (C-02, C-03, C-05, C-10, C-13), and 2 were booked 5.5 hours
off due to UTC drift (C-08, C-09). Real booking rate is 10% (2 of 20).<br/><br/>

<b>2.</b>&nbsp;An AI copilot suggested that the assistant was successfully
handling customer inquiries because call durations were low (under 3 minutes)
and transfers were down.<br/>
<i>What I did instead:</i> I inspected transcripts for all 8 callers with open
job cards. Durations were short because frustrated callers hung up after the
assistant pitched unwanted service slots (C-02, C-07) or falsely claimed no
status visibility (C-04, C-14, C-17). <code>get_vehicle_status</code> was
called 0 of 8 times. Low duration reflected customer abandonment, not
resolution.""", sBody))
    story.append(Spacer(1, 10))

    # ─── (g) Session log pointer ─────────────────────────────────────
    story.append(Paragraph("g. Session Log &amp; Analytical Trajectory", sH1))
    story.append(Paragraph(
        """Full AI session log is attached separately as a .md file.<br/><br/>
<b>Analytical trajectory summary:</b><br/>
1.&nbsp;Programmatic parsing of all 20 call transcripts and JSON tool logs
(<code>pulse_loader.py</code>).<br/>
2.&nbsp;Formulated 5 deterministic invariants: Booking Integrity, UTC-IST
Temporal Alignment, Active Job Card Routing, Transfer Escalation Failsafe,
Site Capability Guard.<br/>
3.&nbsp;Isolated C-08/C-09 as UTC format anomalies where
<code>start_local</code> was omitted for non-periodic services; isolated C-02
as a triple cascading failure (ignored job card &rarr; failed transfer
&rarr; phantom booking).<br/>
4.&nbsp;Built <code>PulseWorkshop 24x7</code> with FastAPI, dynamic
configuration, live WebSocket feed, runtime middleware guardrail
(<code>pulse_proxy.py</code>), universal document inspector
(<code>pulse_doc_inspector.py</code>), and automated test suite
(<code>run_tests.py</code>, 11/11 tests pass).<br/>
5.&nbsp;Production Artifacts: <code>PulseWorkshop</code> Real-Time Guardrail Engine, dynamic config, test suite (11/11 passing), and interactive diagnostic dashboard.""",
        sBody))
    story.append(Spacer(1, 12))

    # ─── Full 20-call audit matrix (exhibit) ─────────────────────────
    story.append(Paragraph(
        "Exhibit: Complete 20-Call Diagnostic Audit Matrix", sH1))

    mx_hdr = ["ID", "Day / Time", "Caller Intent",
              "Reported", "Verified Reality", "Invariant Violations"]
    mx = [
        ["C-01","Mon 09:42","Swift periodic servicing","Booked","Booked (Sat 10:00 IST)","None (Clean)"],
        ["C-02","Mon 11:15","Car readiness check","Booked","Phantom (status inquiry)","PHANTOM, IGNORED_JC, DROPPED_TRANSFER"],
        ["C-03","Mon 15:30","WagonR 30k cost query","Booked","Phantom (comparing shops)","PHANTOM (no book_appointment)"],
        ["C-04","Mon 17:05","Baleno status inquiry","Transferred","Transferred (41 s wait)","IGNORED_JC (get_vehicle_status skipped)"],
        ["C-05","Tue 10:20","City periodic cost","Booked","Phantom (call back husband)","PHANTOM (no book_appointment)"],
        ["C-06","Tue 12:40","Rework rattle complaint","Transferred","Transferred (63 s wait)","None"],
        ["C-07","Tue 14:18","Car pickup readiness","No action","Abandoned inquiry","IGNORED_JC (pitched slot to active car)"],
        ["C-08","Tue 16:50","AC cooling diagnostic","Booked","Corrupted (5.5 h drift)","TZ_MISMATCH (told 10:00, booked 15:30)"],
        ["C-09","Wed 09:30","i20 brake inspection","Booked","Corrupted (5.5 h drift)","TZ_MISMATCH (told 09:30, booked 15:00)"],
        ["C-10","Wed 11:55","Pickup & drop charge","Booked","Phantom (price inquiry)","PHANTOM (no book_appointment)"],
        ["C-11","Wed 14:22","Ordered part status","Callback","Callback (CB-311)","IGNORED_JC (get_vehicle_status skipped)"],
        ["C-12","Wed 17:40","Alignment billing dispute","Transferred","Transferred (29 s wait)","None"],
        ["C-13","Thu 10:10","Sunday service request","Booked","Phantom (WORKSHOP_CLOSED)","PHANTOM (tool error, booked anyway)"],
        ["C-14","Thu 12:05","Nexon status inquiry","Callback","Callback (CB-314)","IGNORED_JC (get_vehicle_status skipped)"],
        ["C-15","Thu 15:45","Bodyshop insurance dent","No action","Dropped inquiry","UNCONFIGURED_SERVICE (bodyshop off)"],
        ["C-16","Fri 09:15","3rd repeat status call","Transferred","Transferred (88 s wait)","IGNORED_JC (3rd call, still no status)"],
        ["C-17","Fri 13:30","Insurance claim survey","No action","Turned away in hours","IGNORED_JC (told to call back in hours)"],
        ["C-18","Fri 16:12","Creta 40k servicing","Booked","Booked (Tue 11:00 IST)","None (Clean)"],
        ["C-19","Sat 10:35","Two-wheeler showroom","No action","Wrong number","None"],
        ["C-20","Sat 12:50","Urgent status, travel","Transferred","Transferred (52 s wait)","IGNORED_JC (pitched slot to active car)"],
    ]
    tm = Table([mx_hdr] + mx, colWidths=[30, 52, 100, 52, 110, 160])
    tm.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 6),
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 1), (-1, -1), 5.8),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING",    (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
    ]))
    story.append(tm)

    # ─── build ───────────────────────────────────────────────────────
    doc.build(story, canvasmaker=_NumberedCanvas)
    print(f"PDF written to: {out_path}")


if __name__ == "__main__":
    build_pdf("Spyne_FDE_Case_Study_Submission.pdf")

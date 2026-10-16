"""
Generate high-fidelity submission PDF for Spyne FDE Case Study
Uses ReportLab to create a publication-quality document.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
import sys
import os

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "Spyne FDE Case Study | Pune Workshop Service Excellence Call & Log Diagnostics")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 747, 558, 747)
        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, footer_text)
        self.drawString(54, 36, "CONFIDENTIAL | Prepared for Spyne Hiring & Leadership Team")
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)
        self.restoreState()

def create_case_study_pdf(filename="Spyne_FDE_Case_Study_Pune_Workshop_Diagnostics.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a")
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569")
    )
    
    h1_style = ParagraphStyle(
        'Heading1Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=12,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#2563eb"),
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155")
    )

    body_bold = ParagraphStyle(
        'BodyCustomBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    code_style = ParagraphStyle(
        'CodeCustom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#0f172a")
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e293b")
    )

    story = []

    # Title & Metadata Banner
    story.append(Paragraph("Spyne | Forward Deployed Engineer Case Study", title_style))
    story.append(Paragraph("Pune Workshop AI Telephony & Log Diagnostics — 24x7 Real-Time Root Cause Analysis", subtitle_style))
    story.append(Spacer(1, 4))
    
    meta_table_data = [
        [
            Paragraph("<b>Candidate:</b> Prateek", body_style),
            Paragraph("<b>Role:</b> Forward Deployed Engineer (Full Time)", body_style),
            Paragraph("<b>Target Site:</b> Sparsh Motors, Kothrud (KTD-04)", body_style)
        ],
        [
            Paragraph("<b>Dataset:</b> 20 Calls + Live Tool Logs", body_style),
            Paragraph("<b>Submission Date:</b> October 16, 2026", body_style),
            Paragraph("<b>Constraints:</b> &le; 800 words (a-f), explicit denominators", body_style)
        ]
    ]
    t_meta = Table(meta_table_data, colWidths=[160, 180, 164])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # Executive Audit Summary Table
    story.append(Paragraph("Executive Summary: Reported Summary vs Verified Ground Truth", h2_style))
    exec_data = [
        ["Metric", "Reported to Management", "Audited Ground Truth", "Variance / Root Cause"],
        ["Calls Answered", "20 of 20 (100%)", "20 of 20 (100%)", "Coverage working, picked up after 4 rings"],
        ["Appointments Booked", "9 of 20 (45%)", "2 of 20 (10%)", "-77.8% drop: 5 phantoms + 2 timezone corrupted"],
        ["Timezone Drift Bookings", "0 (Unreported)", "2 of 4 booked (50%)", "C-08 & C-09 booked 5.5h late (UTC read as IST)"],
        ["Phantom Bookings", "0 (Unreported)", "5 of 9 logged (55.6%)", "C-02, C-03, C-05, C-10 (no book call), C-13 (Sunday error)"],
        ["Vehicle Status Inquiries", "Not tracked", "8 of 20 calls (40%)", "0 of 8 resolved: get_vehicle_status called 0 times"],
        ["Dropped Transfers", "0 (Unreported)", "1 of 6 transfers (16.7%)", "C-02 failed on no_answer; no callback logged"]
    ]
    t_exec = Table(exec_data, colWidths=[120, 110, 110, 164])
    t_exec.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 4),
        ('TOPPADDING', (0,0), (-1,0), 4),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#ffffff")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 7.5),
        ('TOPPADDING', (0,1), (-1,-1), 3),
        ('BOTTOMPADDING', (0,1), (-1,-1), 3),
        ('TEXTCOLOR', (1,2), (1,2), colors.HexColor("#dc2626")),
        ('TEXTCOLOR', (2,2), (2,2), colors.HexColor("#16a34a")),
    ]))
    story.append(t_exec)
    story.append(Spacer(1, 10))

    # Deliverable a
    story.append(Paragraph("a. What Actually Happened This Week (&lt; 250 words)", h1_style))
    p_a = Paragraph("""Weekly performance was severely overstated. The report claimed 9 of 20 calls (45%) were booked appointments. In reality, only 4 of 20 calls (C-01, C-08, C-09, C-18) executed <code>book_appointment</code> successfully. In 2 of those 4 (C-08, C-09), <code>check_availability</code> omitted <code>start_local</code>, causing the assistant to misread UTC as IST and book appointments 5.5 hours later than promised (15:30 IST vs 10:00 AM in C-08; 15:00 IST vs 9:30 AM in C-09). Only 2 of 20 calls (10%, C-01 and C-18) were booked accurately.<br/><br/>
The other 5 of 9 claimed bookings (55.6%) were phantoms logged without an appointment: 4 callers only inquired about prices, pickup, or car status (C-02, C-03, C-05, C-10), and 1 (C-13) errored with <code>WORKSHOP_CLOSED</code> on a Sunday attempt.<br/><br/>
Additionally, 8 of 20 callers (40%: C-02, C-04, C-07, C-11, C-14, C-16, C-17, C-20) had open job cards and asked about cars in the shop. The assistant called <code>get_vehicle_status</code> 0 of 8 times (0%), pitching unwanted service slots to existing workshop customers (C-02, C-07, C-11, C-16, C-20) or falsely claiming it had no status visibility (C-04, C-14, C-17).<br/><br/>
Finally, 1 of 6 transfers failed due to <code>no_answer</code> (C-02) without logging a callback, and 1 caller was turned away during regular Friday hours (C-17).""", body_style)
    story.append(p_a)
    story.append(Spacer(1, 10))

    # Deliverable b
    story.append(Paragraph("b. One Call Traced End to End Through Its Tool Log", h1_style))
    p_b = Paragraph("""<b>Trace of Call C-02 (Mon, 11:15 am | 1 min 48 sec):</b><br/>
<b>1. 11:15:22:</b> <code>lookup_customer {"phone":"9XXXXXX604"}</code> &rarr; returned <code>{"customer_id":"C6120","open_job_cards":["JC-2274"]}</code>.<br/>
<b>2. Transcript:</b> Caller asked: <i>"I gave my car on Saturday. Is it ready?"</i><br/>
<b>3. Where it went wrong:</b> Tool call <code>check_availability</code> at 11:15:58 (and repeated at 11:16:40).<br/>
<b>Why:</b> Per tool reference, a caller inquiring about an existing car must receive <code>get_vehicle_status(job_card="JC-2274")</code>. Instead, the assistant ignored <code>open_job_cards</code> and called <code>check_availability</code> twice, pitching an unwanted booking to an existing customer.<br/>
<b>4. 11:17:02:</b> Caller objected; assistant invoked <code>transfer_to_advisor {"reason":"status_query"}</code>, which returned <code>status: "no_answer"</code> after 6 rings.<br/>
<b>5.</b> Assistant promised someone would get in touch but failed to invoke <code>log_callback</code>, dropping the caller.<br/>
<b>6. 11:17:05:</b> It invoked <code>log_outcome {"outcome":"booked"}</code>, falsely logging a booking without calling <code>book_appointment</code>.""", body_style)
    story.append(p_b)
    story.append(Spacer(1, 10))

    # Deliverable c
    story.append(Paragraph("c. Note to the Workshop Manager (&lt; 80 words)", h1_style))
    note_box = [
        [Paragraph("""<b>To:</b> Workshop Manager, Sparsh Motors Kothrud<br/>
<b>Subject:</b> Assistant Audit & Corrections Update<br/><br/>
Hi Team,<br/><br/>
Our weekly report showed 9 booked appointments, but only 2 are valid. Two were booked 5.5 hours late due to a time zone issue, and five were general inquiries mistakenly logged as bookings.<br/><br/>
Customers asking about cars already in the shop were also offered new bookings instead of status updates.<br/><br/>
We are updating the assistant tonight to fix status inquiries, correct booking timestamps, and capture missed callbacks. We will review tomorrow morning’s calls together.""", callout_style)]
    ]
    t_note = Table(note_box, colWidths=[504])
    t_note.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_note)
    story.append(Spacer(1, 10))

    # Deliverable d
    story.append(Paragraph("d. Ticket for Engineering (Exactly 10 Lines)", h1_style))
    ticket_lines = [
        "Title: Fix assistant tool orchestration: vehicle status bypass, UTC slot drift, phantom bookings",
        "System: Kothrud AI phone agent (site KTD-04); tools: check_availability, book_appointment, log_outcome, get_vehicle_status.",
        "Bug 1: check_availability omits start_local on diagnostic/inspection, causing 5.5h UTC-IST slot drift (C-08, C-09).",
        "Fix 1: Backend must always return start_local across all service types.",
        "Bug 2: Assistant logs outcome: \"booked\" when book_appointment was never called or failed (C-02, C-03, C-05, C-10, C-13).",
        "Fix 2: Reject log_outcome: booked unless book_appointment returned status: ok.",
        "Bug 3: get_vehicle_status never called despite open_job_cards returned (C-02, C-04, C-07, C-11, C-14, C-16, C-17, C-20).",
        "Fix 3: Route callers with active job cards directly to get_vehicle_status; block check_availability.",
        "Bug 4: transfer_to_advisor returning no_answer fails to invoke log_callback (C-02). Fix: auto-fallback to log_callback.",
        "Repro & Verification: Replay C-02, C-08, C-13; verify start_local present, zero phantom bookings, vehicle status queried."
    ]
    ticket_table_data = [[Paragraph(f"<b>{i+1}.</b> {line}", code_style)] for i, line in enumerate(ticket_lines)]
    t_ticket = Table(ticket_table_data, colWidths=[504])
    t_ticket.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_ticket)
    story.append(Spacer(1, 10))

    # Deliverable e
    story.append(Paragraph("e. One Fix You Would Make Tonight & Verification Tomorrow", h1_style))
    p_e = Paragraph("""<b>Tonight's Fix: A runtime middleware guardrail and prompt patch:</b><br/>
1. <b>Routing Rule:</b> In system prompt: <i>"If lookup_customer returns open_job_cards and caller asks about their vehicle, immediately invoke get_vehicle_status. Never offer service booking to existing workshop customers."</i><br/>
2. <b>API Guardrail:</b> Intercept <code>log_outcome</code>: if outcome is \"booked\", verify <code>book_appointment</code> returned <code>status: \"ok\"</code> for this session; if not, rewrite outcome to \"no_action\" or \"callback\".<br/>
3. <b>Timezone Fallback:</b> If <code>check_availability</code> omits <code>start_local</code>, compute <code>start_local = UTC + 5:30</code>.<br/><br/>
<b>Verification Tomorrow Morning (09:00 - 12:00 IST):</b><br/>
1. Verify 100% of calls with outcome \"booked\" have a matching appointment_id.<br/>
2. Confirm zero <code>check_availability</code> calls for callers with active open job cards.<br/>
3. Compare spoken times against <code>confirmed_local</code> to verify zero time drift.""", body_style)
    story.append(p_e)
    story.append(Spacer(1, 10))

    # Deliverable f
    story.append(Paragraph("f. Two Places the AI Gave an Answer and You Did Not Take It", h1_style))
    p_f = Paragraph("""<b>1. The AI summary claimed 9 appointments were booked (45% booking rate) and that assistant performance was strong with reduced advisor load.</b><br/>
<i>What I did instead:</i> I audited tool logs against <code>book_appointment</code>. I rejected 7 of 9 bookings: 5 had no booking call or errored (C-02, C-03, C-05, C-10, C-13), and 2 were booked 5.5 hours off due to UTC drift (C-08, C-09). Real booking rate is 10% (2 of 20).<br/><br/>
<b>2. An AI copilot suggested that the assistant was successfully handling customer inquiries because call durations were low (under 3 minutes) and transfers were down.</b><br/>
<i>What I did instead:</i> I inspected transcripts for all 8 callers with open job cards. Durations were short because frustrated callers hung up after the assistant pitched unwanted service slots (C-02, C-07) or falsely claimed no status visibility (C-04, C-14, C-17). <code>get_vehicle_status</code> was called 0 of 8 times. Low duration reflected customer abandonment, not resolution.""", body_style)
    story.append(p_f)
    story.append(Spacer(1, 10))

    # Deliverable g
    story.append(Paragraph("g. Session Log & Prompt History", h1_style))
    p_g = Paragraph("""<b>Prompt History & Analytical Trajectory:</b><br/>
• <b>Step 1 (Ingestion & Audit):</b> Built automated parser <code>audit_stats.py</code> and <code>call_details.py</code> to iterate all 20 calls across transcripts, tool invocations, and responses.<br/>
• <b>Step 2 (Invariant Formulation):</b> Formulated 5 deterministic operational invariants: Booking Integrity, Timezone Consistency, Active Job Card Routing, Transfer Escalation, and Site Capability.<br/>
• <b>Step 3 (Anomaly Isolation):</b> Isolated C-08 and C-09 as UTC format anomalies where <code>start_local</code> was omitted for non-periodic services; isolated C-02 as a triple cascading failure.<br/>
• <b>Step 4 (Production Engine Implementation):</b> Architected <code>PulseWorkshop 24x7</code> with FastAPI, dynamic configuration (<code>pulse_config.py</code>), live WebSocket stream, and runtime middleware guardrail (<code>pulse_proxy.py</code>) preventing regressions in real time.<br/>
• <b>Step 5 (Automated Testing):</b> Authored <code>run_tests.py</code> verifying all 20 call verdicts, proxy corrections, and metric calculations in CI/CD.""", body_style)
    story.append(p_g)
    story.append(Spacer(1, 14))

    # Comprehensive Call Matrix Table
    story.append(Paragraph("Exhibit: Full 20-Call Comprehensive Diagnostic Audit Matrix", h1_style))
    matrix_header = ["Call ID", "Day & Time", "Caller Intent", "Reported Outcome", "Audited Reality", "Invariant Violations"]
    
    matrix_rows = [
        ["C-01", "Mon 09:42", "Swift periodic servicing", "Booked", "Booked (Sat 10:00)", "None (Clean)"],
        ["C-02", "Mon 11:15", "Car readiness check", "Booked", "Phantom (Status inquiry)", "PHANTOM_BOOKING, IGNORED_JC, DROPPED_TRANSFER"],
        ["C-03", "Mon 15:30", "WagonR 30k cost query", "Booked", "Phantom (Comparing shops)", "PHANTOM_BOOKING (No appointment)"],
        ["C-04", "Mon 17:05", "Baleno status inquiry", "Transferred", "Transferred (Wait 41s)", "IGNORED_JC (get_vehicle_status bypassed)"],
        ["C-05", "Tue 10:20", "City periodic cost query", "Booked", "Phantom (Call back husband)", "PHANTOM_BOOKING (No appointment)"],
        ["C-06", "Tue 12:40", "Rework rattle complaint", "Transferred", "Transferred (Wait 63s)", "None (Advisor escalation)"],
        ["C-07", "Tue 14:18", "Car pickup readiness", "No action", "Abandoned inquiry", "IGNORED_JC (Pitched booking to active car)"],
        ["C-08", "Tue 16:50", "AC cooling diagnostic", "Booked", "Corrupted (5.5h Drift)", "TIMEZONE_MISMATCH (Told 10:00, booked 15:30)"],
        ["C-09", "Wed 09:30", "i20 brake inspection", "Booked", "Corrupted (5.5h Drift)", "TIMEZONE_MISMATCH (Told 09:30, booked 15:00)"],
        ["C-10", "Wed 11:55", "Pickup & drop charge", "Booked", "Phantom (Price inquiry)", "PHANTOM_BOOKING (No appointment)"],
        ["C-11", "Wed 14:22", "Ordered part status", "Callback", "Callback (CB-311)", "IGNORED_JC (get_vehicle_status bypassed)"],
        ["C-12", "Wed 17:40", "Wheel alignment billing", "Transferred", "Transferred (Wait 29s)", "None (Advisor escalation)"],
        ["C-13", "Thu 10:10", "Sunday service booking", "Booked", "Phantom (Errored call)", "PHANTOM_BOOKING (Tool error WORKSHOP_CLOSED)"],
        ["C-14", "Thu 12:05", "Nexon status inquiry", "Callback", "Callback (CB-314)", "IGNORED_JC (get_vehicle_status bypassed)"],
        ["C-15", "Thu 15:45", "Bodyshop insurance dent", "No action", "Dropped inquiry", "UNCONFIGURED_SERVICE (Bodyshop not on site)"],
        ["C-16", "Fri 09:15", "3rd repeat status call", "Transferred", "Transferred (Wait 88s)", "IGNORED_JC (Pitched slot to 3rd time caller)"],
        ["C-17", "Fri 13:30", "Claim survey status", "No action", "Turned away in hours", "IGNORED_JC (False claim of outside hours)"],
        ["C-18", "Fri 16:12", "Creta 40k servicing", "Booked", "Booked (Tue 11:00)", "None (Clean)"],
        ["C-19", "Sat 10:35", "Two wheeler showroom", "No action", "Wrong number", "None (Clean)"],
        ["C-20", "Sat 12:50", "Urgent status travel", "Transferred", "Transferred (Wait 52s)", "IGNORED_JC (Pitched slot to active car)"],
    ]

    t_matrix = Table([matrix_header] + matrix_rows, colWidths=[34, 52, 98, 56, 110, 154])
    t_matrix.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 6.5),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    story.append(t_matrix)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {filename}")

if __name__ == "__main__":
    create_case_study_pdf()

"""
Test Enterprise Features: Document Upload, Inspection, and Timeline Tracking
"""

import unittest
import io
from pulse_doc_inspector import inspect_uploaded_document
from pulse_history import log_timeline_event, get_timeline_events

class TestEnterpriseFeatures(unittest.TestCase):
    def test_txt_document_inspection(self):
        sample_call = """
### C-99 | Mon, 10:00 am | 2 min 00 sec
> **Caller:** I want to service my Baleno.
> **Assistant:** Sure, I have Friday at 10 am.
> **Caller:** Yes, please book it.
Logged outcome: Appointment booked

Tool log
10:00:10  lookup_customer      {"phone":"9XXXXXX111"}
          -> {"customer_id":"C9999","open_job_cards":[]}
10:00:30  check_availability   {"service_type":"periodic"}
          -> {"slots":[{"slot_id":"S-999","start":"2026-08-22T04:30:00Z","start_local":"2026-08-22 10:00 IST"}]}
10:01:00  book_appointment     {"customer_id":"C9999","slot_id":"S-999","service_type":"periodic"}
          -> {"status":"ok","appointment_id":"A-9999","confirmed_local":"2026-08-22 10:00 IST"}
10:01:15  log_outcome          {"outcome":"booked","notes":"Baleno periodic"}
          -> {"status":"ok"}
"""
        res = inspect_uploaded_document("test_doc.txt", sample_call.encode("utf-8"), site_id="KTD-04")
        self.assertEqual(res.summary.total_calls_detected, 1)
        self.assertEqual(res.summary.reported_bookings, 1)
        self.assertEqual(res.summary.verified_bookings, 1)
        self.assertEqual(res.summary.phantom_bookings, 0)
        self.assertEqual(len(res.calls[0].violations), 0)

    def test_phantom_document_inspection(self):
        sample_phantom = """
### C-88 | Tue, 11:00 am | 1 min 30 sec
> **Caller:** What does an oil change cost?
> **Assistant:** Around Rs 3,000.
> **Caller:** Thanks, I will check and call later.
Logged outcome: Appointment booked

Tool log
11:00:10  lookup_customer      {"phone":"9XXXXXX222"}
          -> {"customer_id":"C8888","open_job_cards":[]}
11:00:30  log_outcome          {"outcome":"booked","notes":"oil change inquiry"}
          -> {"status":"ok"}
"""
        res = inspect_uploaded_document("phantom_doc.txt", sample_phantom.encode("utf-8"), site_id="KTD-04")
        self.assertEqual(res.summary.total_calls_detected, 1)
        self.assertEqual(res.summary.reported_bookings, 1)
        self.assertEqual(res.summary.verified_bookings, 0)
        self.assertEqual(res.summary.phantom_bookings, 1)
        self.assertIn("PHANTOM_BOOKING", [v.violation_type.value for v in res.calls[0].violations])

    def test_timeline_tracking(self):
        evt = log_timeline_event("TEST_EVENT", "Testing timeline persistence", {"meta": "123"})
        events = get_timeline_events()
        self.assertTrue(any(e["id"] == evt.id for e in events))

if __name__ == "__main__":
    unittest.main()

"""
PulseWorkshop 24x7 - Automated System & Invariant Test Suite
"""

import unittest
from pulse_config import load_config, get_default_config, SiteConfig
from pulse_models import CallSession, InvariantViolationType
from pulse_loader import parse_call_records
from pulse_invariants import InvariantEngine
from pulse_proxy import ToolProxyMiddleware

class TestPulseWorkshop(unittest.TestCase):
    def setUp(self):
        self.config = get_default_config()
        self.engine = InvariantEngine(self.config)
        self.sessions = parse_call_records()
        self.audited, self.metrics = self.engine.audit_all(self.sessions)
        self.proxy = ToolProxyMiddleware(self.config.sites["KTD-04"])

    def test_parsed_call_count(self):
        self.assertEqual(len(self.sessions), 20)

    def test_executive_metrics_audit(self):
        self.assertEqual(self.metrics.reported_bookings, 9)
        self.assertEqual(self.metrics.reported_booking_rate, 45.0)
        self.assertEqual(self.metrics.verified_bookings, 2)
        self.assertEqual(self.metrics.verified_booking_rate, 10.0)
        self.assertEqual(self.metrics.phantom_bookings, 5)
        self.assertEqual(self.metrics.tz_corrupted_bookings, 2)
        self.assertEqual(self.metrics.open_job_card_calls, 8)
        self.assertEqual(self.metrics.vehicle_status_invocations, 0)

    def test_call_c01_clean_booking(self):
        c01 = next(s for s in self.audited if s.call_id == "C-01")
        self.assertTrue(c01.is_valid_booking)
        self.assertEqual(len(c01.violations), 0)
        self.assertEqual(c01.booking_id, "A-9051")

    def test_call_c02_triple_failure(self):
        c02 = next(s for s in self.audited if s.call_id == "C-02")
        self.assertFalse(c02.is_valid_booking)
        v_types = [v.violation_type for v in c02.violations]
        self.assertIn(InvariantViolationType.PHANTOM_BOOKING, v_types)
        self.assertIn(InvariantViolationType.IGNORED_OPEN_JOB_CARD, v_types)
        self.assertIn(InvariantViolationType.UNHANDLED_TRANSFER_FAILURE, v_types)

    def test_call_c08_c09_timezone_drift(self):
        c08 = next(s for s in self.audited if s.call_id == "C-08")
        c09 = next(s for s in self.audited if s.call_id == "C-09")
        
        self.assertIn(InvariantViolationType.TIMEZONE_MISMATCH, [v.violation_type for v in c08.violations])
        self.assertIn(InvariantViolationType.TIMEZONE_MISMATCH, [v.violation_type for v in c09.violations])
        self.assertEqual(c08.time_discrepancy_minutes, 330)
        self.assertEqual(c09.time_discrepancy_minutes, 330)

    def test_proxy_start_local_injection(self):
        # Test that proxy injects start_local when tool backend omits it
        raw_response = {
            "slots": [{"slot_id": "S-TEST-1", "start": "2026-08-20T10:00:00Z", "duration_min": 120}]
        }
        remediated = self.proxy.on_check_availability_response("test-sess-1", {"service_type": "diagnostic"}, raw_response)
        slot = remediated["slots"][0]
        self.assertIn("start_local", slot)
        self.assertEqual(slot["start_local"], "2026-08-20 15:30 IST")
        self.assertTrue(slot.get("_auto_remediated_by_proxy"))

    def test_proxy_phantom_booking_interception(self):
        # Test that proxy rewrites outcome "booked" if no book_appointment occurred
        sess_id = "test-sess-2"
        self.proxy.get_session(sess_id)
        intercepted = self.proxy.on_log_outcome_request(sess_id, {"outcome": "booked", "notes": "Price check WagonR"})
        self.assertEqual(intercepted["outcome"], "no_action")
        self.assertIn("Auto-corrected from 'booked'", intercepted["notes"])

    def test_proxy_transfer_failure_auto_callback(self):
        # Test that proxy auto-attaches callback remediation on no_answer
        sess_id = "test-sess-3"
        resp = self.proxy.on_transfer_to_advisor_response(sess_id, "9XXXXXX604", {"status": "no_answer", "rings": 6})
        self.assertIn("auto_remediation", resp)

if __name__ == "__main__":
    unittest.main()

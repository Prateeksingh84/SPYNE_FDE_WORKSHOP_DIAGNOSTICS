"""
PulseWorkshop 24x7 - Data Contracts and Event Models
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class InvariantSeverity(str, Enum):
    P0_CRITICAL = "P0_CRITICAL"
    P1_HIGH = "P1_HIGH"
    P2_MEDIUM = "P2_MEDIUM"
    INFO = "INFO"

class InvariantViolationType(str, Enum):
    PHANTOM_BOOKING = "PHANTOM_BOOKING"
    TIMEZONE_MISMATCH = "TIMEZONE_MISMATCH"
    MISSING_START_LOCAL = "MISSING_START_LOCAL"
    IGNORED_OPEN_JOB_CARD = "IGNORED_OPEN_JOB_CARD"
    UNHANDLED_TRANSFER_FAILURE = "UNHANDLED_TRANSFER_FAILURE"
    OPERATION_OUTSIDE_HOURS = "OPERATION_OUTSIDE_HOURS"
    UNCONFIGURED_SERVICE_TYPE = "UNCONFIGURED_SERVICE_TYPE"
    HALLUCINATED_SLOT = "HALLUCINATED_SLOT"

class ToolExecution(BaseModel):
    timestamp_local: str
    tool_name: str
    arguments: Dict[str, Any]
    response: Dict[str, Any]
    duration_ms: Optional[int] = 0

class InvariantViolation(BaseModel):
    call_id: str
    violation_type: InvariantViolationType
    severity: InvariantSeverity
    tool_name: Optional[str] = None
    timestamp: str
    summary: str
    detail: str
    remediation_applied: Optional[str] = None

class CallSession(BaseModel):
    call_id: str
    site_id: str
    day_of_week: str
    start_time: str
    duration_str: str
    duration_seconds: int
    transcript: List[Dict[str, str]] = Field(default_factory=list) # [{"role": "caller"|"assistant", "text": "..."}]
    tool_executions: List[ToolExecution] = Field(default_factory=list)
    logged_outcome: Optional[str] = None
    logged_notes: Optional[str] = None
    
    # Audit enrichment fields
    customer_id: Optional[str] = None
    open_job_cards: List[str] = Field(default_factory=list)
    has_vehicle_inquiry: bool = False
    verified_outcome: Optional[str] = None
    is_valid_booking: bool = False
    booking_id: Optional[str] = None
    agreed_time_spoken: Optional[str] = None
    system_booked_time: Optional[str] = None
    time_discrepancy_minutes: Optional[int] = None
    violations: List[InvariantViolation] = Field(default_factory=list)

class SiteMetricComparison(BaseModel):
    site_id: str
    total_calls: int
    reported_bookings: int
    reported_booking_rate: float
    verified_bookings: int
    verified_booking_rate: float
    phantom_bookings: int
    tz_corrupted_bookings: int
    open_job_card_calls: int
    vehicle_status_invocations: int
    unhandled_transfers: int
    clean_resolution_rate: float

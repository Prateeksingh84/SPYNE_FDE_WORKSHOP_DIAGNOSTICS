# Assistant tool reference

Sparsh Motors, site KTD-04, Kothrud. Open Monday to Saturday, 09:00 to 18:00
IST. Closed Sunday.

The assistant calls these tools during a live call. It knows nothing the tools
do not hand back to it.

## Time

Log timestamps are workshop local time, IST, which runs 5 hours 30 minutes ahead
of UTC.

`check_availability` returns each slot twice. `start` is the instant in UTC.
`start_local` is the same instant in workshop time. Say `start_local` to the
caller and pass `slot_id` to `book_appointment`.

## The tools

| Tool | When it runs | Parameters | Returns |
|---|---|---|---|
| lookup_customer | First, on every call | phone | customer_id, open_job_cards (job card IDs), calls_last_7d, last_visit |
| get_vehicle_status | Caller asks about a car already in the workshop | job_card | stage, eta_local, parts_pending |
| check_availability | Caller wants a slot | date_from, days, service_type | slots array of slot_id, start, start_local, duration_min |
| book_appointment | Caller has agreed a date and a time | customer_id, slot_id, service_type, vehicle | status ok, appointment_id, confirmed_local. Or an error |
| transfer_to_advisor | The assistant cannot answer | reason | status connected, no_answer or busy |
| log_callback | Nobody is free and the caller wants a call back | phone, note, deadline_local | status, callback_id |
| log_outcome | Last call of every call | outcome, notes | status |

## Values

service_type is one of periodic, diagnostic, inspection, bodyshop. bodyshop is
enabled per site.

outcome is one of booked, transferred, callback, no_action.

An error return carries `error` and `detail` instead of `status`. Common ones are
NOT_FOUND, WORKSHOP_CLOSED, SLOT_NOT_AVAILABLE and UNKNOWN_SERVICE_TYPE.

## How the assistant is meant to behave

log_outcome booked goes in only after book_appointment returns status ok.

transfer_to_advisor returning no_answer means nobody picked up. The caller needs
a log_callback in that case.

An error return is a failure. The assistant carries on as if the step did not
happen.

A caller asking about a car that is already in the workshop gets
get_vehicle_status, not a slot offer.

---

*Synthetic. Built for this exercise.*

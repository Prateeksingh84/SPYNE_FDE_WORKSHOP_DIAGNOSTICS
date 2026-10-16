import re

with open('2-call-records.md', 'r', encoding='utf-8') as f:
    text = f.read()

calls = text.split('### C-')[1:]

print(f"Total calls: {len(calls)}")

stats = {
    'total': len(calls),
    'logged_outcomes': {},
    'true_booked': 0,
    'tz_corrupted_booked': 0,
    'fake_booked': 0,
    'has_open_jc': 0,
    'get_veh_status_called': 0,
    'transfer_attempted': 0,
    'transfer_connected': 0,
    'transfer_no_answer': 0,
    'callbacks_logged': 0,
    'caller_inquiring_existing_car': 0,
}

for c in calls:
    cid = 'C-' + c[:2]
    m_logged = re.search(r'Logged outcome:\s*(.*)', c)
    logged = m_logged.group(1).strip() if m_logged else 'UNKNOWN'
    stats['logged_outcomes'][logged] = stats['logged_outcomes'].get(logged, 0) + 1
    
    # tool log
    tool_log = c.split('Tool log')[1] if 'Tool log' in c else ''
    
    # Check open job card
    open_jc = False
    m_jc = re.search(r'"open_job_cards":\[(.*?)\]', tool_log)
    if m_jc and m_jc.group(1).strip():
        stats['has_open_jc'] += 1
        open_jc = True
        
    if 'get_vehicle_status' in tool_log:
        stats['get_veh_status_called'] += 1
        
    if 'transfer_to_advisor' in tool_log:
        stats['transfer_attempted'] += 1
        if '"status":"connected"' in tool_log:
            stats['transfer_connected'] += 1
        elif '"status":"no_answer"' in tool_log:
            stats['transfer_no_answer'] += 1
            
    if 'log_callback' in tool_log:
        stats['callbacks_logged'] += 1
        
    if 'book_appointment' in tool_log:
        if 'status":"ok"' in tool_log:
            # check if tz corrupted
            if cid in ['C-08', 'C-09']:
                stats['tz_corrupted_booked'] += 1
            else:
                stats['true_booked'] += 1
        else:
            stats['fake_booked'] += 1
    else:
        if logged == 'Appointment booked':
            stats['fake_booked'] += 1

print("Stats summary:")
for k, v in stats.items():
    print(f"  {k}: {v}")

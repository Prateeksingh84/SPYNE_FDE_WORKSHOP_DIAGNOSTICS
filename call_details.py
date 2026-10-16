import re

with open('2-call-records.md', 'r', encoding='utf-8') as f:
    text = f.read()

calls = text.split('### C-')[1:]

details = []
for c in calls:
    cid = 'C-' + c[:2]
    first_line = c.split('\n')[0]
    
    # logged outcome
    m_logged = re.search(r'Logged outcome:\s*(.*)', c)
    logged = m_logged.group(1).strip() if m_logged else ''
    
    # open job cards
    m_jc = re.search(r'lookup_customer.*?->\s*\{.*?"open_job_cards":\[(.*?)\]', c, re.DOTALL)
    jc = m_jc.group(1).strip() if m_jc else ''
    
    # book appointment
    m_book = re.search(r'book_appointment\s+(\{.*?\})\s+->\s+(\{.*?\})', c)
    book_status = 'None'
    book_confirmed = ''
    if m_book:
        res = m_book.group(2)
        if '"status":"ok"' in res:
            book_status = 'OK'
            m_conf = re.search(r'"confirmed_local":"(.*?)"', res)
            if m_conf:
                book_confirmed = m_conf.group(1)
        elif 'error' in res:
            book_status = 'ERROR'
            book_confirmed = res
            
    # check availability
    slots_found = re.findall(r'check_availability\s+(\{.*?\})\s+->\s+(\{.*?\})', c)
    has_start_local = any('start_local' in s[1] for s in slots_found) if slots_found else None
    
    # transfer to advisor
    m_trans = re.search(r'transfer_to_advisor\s+(\{.*?\})\s+->\s+(\{.*?\})', c)
    trans_status = ''
    if m_trans:
        res = m_trans.group(2)
        m_st = re.search(r'"status":"(.*?)"', res)
        if m_st:
            trans_status = m_st.group(1)
            
    # callback
    has_cb = 'log_callback' in c
    
    # caller intent
    caller_lines = [l for l in c.split('\n') if l.startswith('> **Caller:**')]
    caller_text = ' '.join(caller_lines)
    
    details.append({
        'cid': cid,
        'info': first_line,
        'logged': logged,
        'jc': jc,
        'book_status': book_status,
        'book_confirmed': book_confirmed,
        'has_start_local': has_start_local,
        'trans_status': trans_status,
        'has_cb': has_cb,
        'caller_summary': caller_lines[0] if caller_lines else ''
    })

for d in details:
    print(f"{d['cid']} | Logged: {d['logged']:<22} | Book: {d['book_status']:<5} {d['book_confirmed']:<25} | JC: {d['jc']:<10} | Trans: {d['trans_status']:<10} | CB: {str(d['has_cb']):<5}")
    print(f"     Caller: {d['caller_summary'][:90]}")

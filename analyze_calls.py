import re
import json

with open('2-call-records.md', 'r', encoding='utf-8') as f:
    text = f.read()

calls = text.split('### C-')
print(f"Total call sections: {len(calls)-1}")

results = []

for c in calls[1:]:
    cid = 'C-' + c[:2]
    header = c.split('\n')[0]
    
    # check logged outcome
    m_logged = re.search(r'Logged outcome:\s*(.*)', c)
    logged = m_logged.group(1).strip() if m_logged else 'UNKNOWN'
    
    # check book_appointment in tool log
    has_book_call = 'book_appointment' in c
    book_ok = False
    book_err = False
    confirmed_local = None
    if has_book_call:
        m_book = re.search(r'book_appointment\s+(\{.*?\})\s+->\s+(\{.*?\})', c)
        if m_book:
            book_req = m_book.group(1)
            book_res = m_book.group(2)
            if '"status":"ok"' in book_res:
                book_ok = True
                m_conf = re.search(r'"confirmed_local":"(.*?)"', book_res)
                if m_conf:
                    confirmed_local = m_conf.group(1)
            else:
                book_err = True

    # check transfer_to_advisor
    has_transfer = 'transfer_to_advisor' in c
    transfer_status = None
    if has_transfer:
        m_trans = re.search(r'transfer_to_advisor\s+(\{.*?\})\s+->\s+(\{.*?\})', c)
        if m_trans:
            m_st = re.search(r'"status":"(.*?)"', m_trans.group(2))
            if m_st:
                transfer_status = m_st.group(1)
                
    # check log_callback
    has_callback = 'log_callback' in c

    # check open_job_cards
    has_open_jc = False
    m_jc = re.search(r'"open_job_cards":\[(.*?)\]', c)
    if m_jc and m_jc.group(1).strip():
        has_open_jc = m_jc.group(1).strip()
        
    # check get_vehicle_status
    has_get_veh = 'get_vehicle_status' in c

    results.append({
        'cid': cid,
        'header': header,
        'logged': logged,
        'has_book_call': has_book_call,
        'book_ok': book_ok,
        'book_err': book_err,
        'confirmed_local': confirmed_local,
        'transfer_status': transfer_status,
        'has_callback': has_callback,
        'open_jc': has_open_jc,
        'has_get_veh': has_get_veh
    })

print(f"{'CID':<5} | {'Logged Outcome':<22} | {'Book':<5} | {'BookOk':<6} | {'Confirmed Local':<22} | {'Transfer':<10} | {'CB':<5} | {'Open JC':<10} | {'GetVeh'}")
print("-" * 105)
for r in results:
    print(f"{r['cid']:<5} | {r['logged']:<22} | {str(r['has_book_call']):<5} | {str(r['book_ok']):<6} | {str(r['confirmed_local']):<22} | {str(r['transfer_status']):<10} | {str(r['has_callback']):<5} | {str(r['open_jc']):<10} | {r['has_get_veh']}")

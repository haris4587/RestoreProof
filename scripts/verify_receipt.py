"""Verify an exported receipt hash and optional append-only event chain offline.
This proves internal consistency; anchor the final event hash to an on-chain read.
"""
import argparse
import hashlib
import json
from pathlib import Path

def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)

def digest(x):
    return hashlib.sha256(canonical(x).encode()).hexdigest()

def verify(receipt, events=None):
    r=dict(receipt)
    h=r.pop('decision_hash')
    if digest(r)!=h: raise ValueError('Receipt hash mismatch')
    if events is not None:
        previous='0'*64
        found=False
        for event in events:
            row=dict(event);eh=row.pop('event_hash')
            if row['plan_id']!=r['plan_id']: raise ValueError('Export only this plan\'s events in sequence order')
            if row['previous_hash']!=previous or digest(row)!=eh: raise ValueError('Broken event chain')
            if row['action']=='ASSESS' and row['payload']['attempt']==r['attempt']:
                if row['payload']['decision_hash']!=h or row['previous_hash']!=r['previous_event_hash']:
                    raise ValueError('Receipt not bound to history')
                found=True
            previous=eh
        if not found: raise ValueError('No assessment event for this receipt')
    return h

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('receipt');p.add_argument('--events');a=p.parse_args()
    print('Verified:',verify(json.loads(Path(a.receipt).read_text()),json.loads(Path(a.events).read_text()) if a.events else None))

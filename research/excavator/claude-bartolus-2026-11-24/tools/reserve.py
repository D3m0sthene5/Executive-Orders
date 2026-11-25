"""Papinian: reserve exact orders for one lane agent in CLAIM_KIT_LOCK.json (clerical; uses kit.py's own guard).
usage: python reserve.py AGENT TAG EO:N [EO:N ...]   (run from the repository root, without -I)"""
import sys, json
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, 'jobs/claim-kit')
import kit
agent, tag, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
repo = Path('.').resolve()
taken = []
with kit.reservations(repo) as locks:
    for iid in ids:
        cur = locks['orders'].get(iid)
        if cur and cur.get('agent') != agent:
            taken.append((iid, cur.get('agent'))); continue
        locks['orders'][iid] = {'agent': agent, 'family': tag, 'dossier_sha256': None,
                                'reserved_on': datetime.now(timezone.utc).isoformat()}
print(json.dumps({'reserved': len(ids) - len(taken), 'refused': taken}))

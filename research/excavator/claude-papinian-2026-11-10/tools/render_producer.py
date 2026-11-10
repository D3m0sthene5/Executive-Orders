"""Render one Papinian producer prompt (coordinator tool, no legal judgment).
usage: python -I render_producer.py BATCH ROUTE AGENT [NOTE_FILE] -> SCR/prompts/producer-BATCH.txt
Splits assigned from dispatch-blocked members using the packet's DISPATCH_CHECK.json (or newest dispatch-v*.json)."""
import glob, json, sys
from pathlib import Path
REPO = Path('C:/Users/danie/eo-wt/papinian'); SCR = Path('C:/Users/danie/AppData/Local/Temp/papinian')
T = Path(__file__).resolve().parent / 'prompts'
b, route, agent = sys.argv[1:4]
P = REPO / 'research/excavator/claude-papinian-2026-11-10' / b / 'packet'
recs = sorted(glob.glob(str(P / 'dispatch-v*.json'))) or [str(P / 'DISPATCH_CHECK.json')]
d = json.load(open(recs[-1], encoding='utf-8'))
ok, blocked = d['dispatchable_ids'], d['source_blocked_ids']
miss = {}
for t in d.get('source_recovery_tasks', []):
    for r in t.get('affected_references', []):
        if r.get('required'):
            miss.setdefault(r['instrument_id'], set()).add(f"{r['evidence_id']} ({'/'.join(t.get('check_statuses', []))})")
note = 'All members passed the dispatch check.' if not blocked else (
    'DISPATCH-BLOCKED (not assigned; do not research; write only their assessment row from the view, and leave their decisions.csv rows as prepared): '
    + '; '.join(f"{i}: mandatory source not held: {', '.join(sorted(miss.get(i, ['see DISPATCH_CHECK.json'])))}" for i in blocked))
t = (T / 'producer.txt').read_text(encoding='utf-8')
t = t.replace('ROUTENAME', route).replace('ROUTEBRIEF', (T / f'route_{route}.txt').read_text(encoding='utf-8').strip())
t = t.replace('PACKETPATH', P.relative_to(REPO).as_posix()).replace('ASSIGNEDLIST', ', '.join(ok) or 'none')
t = t.replace('DISPATCHNOTE', note).replace('SCRATCH', f'C:/Users/danie/AppData/Local/Temp/papinian/work/{b}/').replace('AGENTNAME', agent)
if len(sys.argv) > 4:
    t += '\n\nCOORDINATOR NOTE FOR THIS BATCH:\n' + Path(sys.argv[4]).read_text(encoding='utf-8')
out = SCR / 'prompts' / f'producer-{b}.txt'; out.write_text(t, encoding='utf-8')
print(b, 'assigned', len(ok), 'blocked', blocked, len(t), 'chars ->', out)

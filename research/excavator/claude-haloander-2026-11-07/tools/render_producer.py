"""Render one producer prompt for a Haloander packet (coordinator tool, no legal judgment).
usage: python3 -I render_producer.py PACKET [EXTRA_NOTE_FILE] -> /tmp/claude-0/dorotheus-wave/prompts/producer-PACKET.txt
Uses the newest dispatch-v*.json receipt to split assigned from dispatch-blocked members, and for undecided packets
adds a mechanical precheck of each member's frozen original grade and held ending/current records."""
import glob, json, sys
from pathlib import Path
REPO = Path('/home/user/Executive-Orders'); E = Path('/tmp/claude-0/-home-user-Executive-Orders/b948d1cb-92e5-5ecb-8cbe-fc3fb7b3e2c6/scratchpad/necker'); T = Path(__file__).resolve().parent / 'prompts'
b = sys.argv[1]
W = REPO / 'research/excavator/claude-haloander-2026-11-07'
P = W / b / 'packet'
rec = sorted(glob.glob(str(P / 'dispatch-v*.json')))[-1]
d = json.load(open(rec))
ok, blocked = d['dispatchable_ids'], d['source_blocked_ids']
miss = {}
for t in d.get('source_recovery_tasks', []):
    for r in t.get('affected_references', []):
        if r.get('required'):
            miss.setdefault(r['instrument_id'], set()).add(f"{r['evidence_id']} ({'/'.join(t.get('check_statuses', []))}; sha256 {t.get('expected_sha256','')[:16]}; {' '.join(t.get('native_wanted',{}).get('urls',[])[:1])})")
note = 'All members passed the dispatch check.' if not blocked else (
    'DISPATCH-BLOCKED (not assigned; do not research; write only their assessment row from the view, and leave their decisions.csv rows as prepared): '
    + '; '.join(f"{i}: mandatory source not held: {', '.join(sorted(miss.get(i, ['see DISPATCH_CHECK.json'])))}" for i in blocked))
und = (P / 'undecided').exists()
route = (T / ('route_undecided.txt' if und else 'route_decided.txt')).read_text()
if und:
    lines = ['COORDINATOR PRECHECK (mechanical, from the frozen evidence; you still verify):']
    for ev in sorted(glob.glob(str(P / 'undecided/*/EVIDENCE.json'))):
        e = json.load(open(ev)); dz = e['base_dossier']; o = dz['evidence'].get(dz.get('original_source_id'), {})
        ids = list(dz.get('evidence', {}))
        h = e['history_packet']['history']
        lines.append(f"- {e['instrument_id']}: original {dz.get('original_source_id')} acceptable_as_original={o.get('acceptable_as_original')} requires_page_check={o.get('requires_page_check')}; "
                     f"ending-type records {sum(i.startswith(('ACT:','TERM:','ACTOR_TEXT:')) for i in ids)}, CURRENT records {sum(i.startswith('CURRENT:') for i in ids)}; history observations {len(h.get('observation_ids',[]))}, flags {h.get('flags')}")
    route = route.replace('PRECHECK', '\n'.join(lines))
extra = Path(sys.argv[2]).read_text() if len(sys.argv) > 2 else ''
t = (T / 'producer.txt').read_text()
t = t.replace('ROUTENAME', 'undecided' if und else ('decided (YES probe)' if b.startswith('y') else 'decided'))
t = t.replace('ROUTEBRIEF', route).replace('PACKETPATH', str(P)).replace('ASSIGNEDLIST', ', '.join(ok) or 'none')
t = t.replace('DISPATCHNOTE', note).replace('SCRATCH', f'/tmp/claude-0/haloander-work/{b}/')
t = t.replace('EXTRAEDIT', 'and the STATUS_DECISION.json files under undecided/' if und else '')
if extra: t += '\n\nCOORDINATOR NOTE FOR THIS ATTEMPT:\n' + extra
(E / 'prompts' / f'producer-{b}.txt').write_text(t)
print(b, 'assigned', len(ok), 'blocked', blocked, 'undecided' if und else 'decided', len(t), 'chars')

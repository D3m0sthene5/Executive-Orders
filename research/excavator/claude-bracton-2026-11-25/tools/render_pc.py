"""Bracton PC lanes: render one producer prompt for this machine (coordinator tool, no legal judgment).
usage (from the repository root): python -X utf8 research/excavator/claude-bracton-2026-11-25/tools/render_pc.py pNN SCRATCH_ROOT
Writes SCRATCH_ROOT/prompts/producer-pNN.txt from producer.txt and route_correction.txt (same brief as the cloud lanes),
with this machine's repository path and `python` in place of `python3`."""
import glob, json, sys
from pathlib import Path
REPO = Path('.').resolve(); W = 'research/excavator/claude-bracton-2026-11-25'; T = REPO / W / 'tools'
b, scr = sys.argv[1], Path(sys.argv[2]); P = REPO / W / b / 'packet'
d = json.load(open(sorted(glob.glob(str(P / 'dispatch-v*.json'))) [-1] if glob.glob(str(P / 'dispatch-v*.json')) else P / 'DISPATCH_CHECK.json', encoding='utf-8'))
ok, blocked = d['dispatchable_ids'], d['source_blocked_ids']
note = 'All members passed the dispatch check.' if not blocked else ('DISPATCH-BLOCKED (not assigned; do not research; write only their assessment row from the view, and leave their decisions.csv rows as prepared): ' + ', '.join(blocked))
t = (T / 'producer.txt').read_text(encoding='utf-8')
t = t.replace('ROUTENAME', 'correction').replace('ROUTEBRIEF', (T / 'route_correction.txt').read_text(encoding='utf-8').strip())
t = t.replace('PACKETPATH', f'{W}/{b}/packet').replace('ASSIGNEDLIST', ', '.join(ok) or 'none').replace('DISPATCHNOTE', note)
t = t.replace('SCRATCH', (scr / 'work' / b).as_posix() + '/').replace('AGENTNAME', 'claude')
t = t.replace('/home/claude/d3m0sthene5/executive-orders', REPO.as_posix()).replace('claude-bartolus-2026-11-24', 'claude-bracton-2026-11-25')
t = t.replace('python3 ', 'python ').replace('Python is `python3`', 'Python is `python`')
out = scr / 'prompts' / f'producer-{b}.txt'; out.parent.mkdir(parents=True, exist_ok=True); (scr / 'work' / b).mkdir(parents=True, exist_ok=True)
out.write_text(t, encoding='utf-8'); print(b, 'assigned', len(ok), 'blocked', len(blocked), '->', out)

"""Bracton PC lanes: prepare one correction packet (coordinator tool, no legal judgment; cross-platform).
usage (from the repository root): python -X utf8 research/excavator/claude-bracton-2026-11-25/tools/prep_pc.py pNN
Reads ids/pNN.txt; runs kit.py prepare (agent claude, action production.one_step_away, replacement proposal),
cruden lookups and one Geddes view per order; log in <wave>/pNN/PREP_LOG.txt."""
import subprocess, sys
from pathlib import Path
W = Path('research/excavator/claude-bracton-2026-11-25'); b = sys.argv[1]
ids = (W / 'ids' / f'{b}.txt').read_text(encoding='utf-8').split()
R = W / b; R.mkdir(parents=True, exist_ok=True)
log = open(R / 'PREP_LOG.txt', 'w', encoding='utf-8'); py = sys.executable
def run(cmd):
    log.write('$ ' + ' '.join(cmd) + '\n'); log.flush()
    r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT); log.write(f'exit {r.returncode}\n'); return r.returncode
if run([py, '-X', 'utf8', 'jobs/claim-kit/kit.py', 'prepare', *ids, '--agent', 'claude', '--action', 'production.one_step_away',
        '--replacement-proposal', '--write', str(R / 'packet')]) != 0:
    print(b, 'PREPARE FAILED; see', R / 'PREP_LOG.txt'); sys.exit(2)
run([py, '-X', 'utf8', '-I', 'research/excavator/claude-nira-sweep-2026-10-29/cruden.py', 'lookups', str(R / 'packet')])
(R / 'packet' / 'views').mkdir(exist_ok=True)
for i in ids:
    n = i.split(':', 1)[1].replace(':', '_')
    run([py, '-X', 'utf8', '-I', 'jobs/geddes/geddes.py', 'view', str(R / 'packet' / 'PACKET.json'), i, '--write', str(R / 'packet' / 'views' / f'EO_{n}.json')])
print(b, 'prepared', len(ids), 'orders')

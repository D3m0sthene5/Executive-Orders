"""Bracton PC lanes: prepare one correction packet (coordinator tool, no legal judgment; cross-platform).
usage (from the repository root): python -X utf8 research/excavator/claude-bracton-2026-11-25/tools/prep_pc.py pNN [--held]
Reads ids/pNN.txt; runs kit.py prepare (agent claude, action production.one_step_away, replacement proposal),
cruden lookups and one Geddes view per order; log in <wave>/pNN/PREP_LOG.txt.

kit prepare exits 0 when every member is dispatchable, 1 when it wrote the packet but some members are
source-blocked (PREPARE.json and DISPATCH_CHECK.json name them), and 2 when it refused or failed (no packet).
An exit of 1 is a usable packet: prepare lookups and views for every member, and assign only the dispatchable
ones. Any other failure, or an exit of 1 without a fresh PREPARE.json, stops.

--held passes --held-supplement: held registry sources the dossiers do not cite are sealed into packet-held
(source_supplement), and lookups, views and the printed dispatch list use that packet."""
import json, subprocess, sys
from pathlib import Path


def prepare_outcome(code, packet):
    """('ok'|'partly_blocked'|'all_blocked'|'failed', PREPARE.json metrics or None) for a kit prepare exit code."""
    metrics = None
    try:
        metrics = json.loads((packet / 'PREPARE.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        pass
    check = (metrics or {}).get('dispatch_check') if isinstance(metrics, dict) else None
    if not isinstance(check, dict):
        return 'failed', metrics
    if code == 0 and check.get('ok'):
        return 'ok', metrics
    if code == 1 and not check.get('ok'):
        return ('partly_blocked' if check.get('dispatchable_ids') else 'all_blocked'), metrics
    return 'failed', metrics


def main(b, held=False):
    W = Path('research/excavator/claude-bracton-2026-11-25')
    ids = (W / 'ids' / f'{b}.txt').read_text(encoding='utf-8').split()
    R = W / b; R.mkdir(parents=True, exist_ok=True); packet = R / 'packet'
    if packet.exists():
        print(b, 'packet already exists; kit prepare never overwrites:', packet); return 2
    log = open(R / 'PREP_LOG.txt', 'w', encoding='utf-8'); py = sys.executable

    def run(cmd):
        log.write('$ ' + ' '.join(cmd) + '\n'); log.flush()
        r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT); log.write(f'exit {r.returncode}\n'); log.flush()
        return r.returncode

    code = run([py, '-X', 'utf8', 'jobs/claim-kit/kit.py', 'prepare', *ids, '--agent', 'claude', '--action',
                'production.one_step_away', '--replacement-proposal', '--write', str(packet)]
               + (['--held-supplement'] if held else []))
    state, metrics = prepare_outcome(code, packet)
    supplemented = packet.with_name(packet.name + '-held')
    if held and state != 'failed' and supplemented.is_dir():
        state, metrics = prepare_outcome(code, supplemented)
        packet = supplemented
    if state == 'failed':
        print(b, 'PREPARE FAILED (exit', code, '); see', R / 'PREP_LOG.txt'); return 2
    run([py, '-X', 'utf8', '-I', 'research/excavator/claude-nira-sweep-2026-10-29/cruden.py', 'lookups', str(packet)])
    (packet / 'views').mkdir(exist_ok=True)
    for i in ids:
        n = i.split(':', 1)[1].replace(':', '_')
        run([py, '-X', 'utf8', '-I', 'jobs/geddes/geddes.py', 'view', str(packet / 'PACKET.json'), i, '--write',
             str(packet / 'views' / f'EO_{n}.json')])
    check = metrics['dispatch_check']
    prescreen = (metrics.get('prescreen') or {}).get('flagged_ids') or []
    print(b, 'prepared', len(ids), 'orders in', packet, ';', state, '- dispatchable:', ' '.join(check.get('dispatchable_ids') or []) or 'none',
          '- source-blocked:', ' '.join(check.get('source_blocked_ids') or []) or 'none',
          '- prescreen flags (advisory):', ' '.join(prescreen) or 'none')
    return 0 if state != 'all_blocked' else 3


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], '--held' in sys.argv[2:]))

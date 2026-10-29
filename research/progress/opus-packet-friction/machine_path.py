"""Time the whole native machine path for one batch on one tree (engineering receipt).

prepare -> declarations (+ extra declared excerpts) -> source-supplement prepare -> view x2 ->
apply (the producer's exact sheets; only dossier_sha256 remapped to this tree's packet) -> batch-check
(actual claim-checker). Each step is its own process, timed by io_run.py. Run it on two trees that hold
identical inputs but different code to compare machine cost; model work is not included.

Usage: python3 machine_path.py TREE LABEL SHEETS_PACKET EXTRA_DECLARATIONS.json OUT.json ID [ID ...]
SHEETS_PACKET is the reviewed producer packet (its decisions.csv/clauses.csv/RATIONALES.json and
PACKET.json fingerprints are the remap source). EXTRA_DECLARATIONS.json holds source entries appended to
the shared NIRA declarations (or [] for none).
"""
import csv
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
NRA = 'research/excavator/claude-nira-sweep-2026-10-29'


def run(tree, script, *args):
    p = subprocess.run([sys.executable, '-B', str(HERE / 'io_run.py'), str(tree / script), *map(str, args)],
                       cwd=tree, capture_output=True, text=True)
    stats = next((json.loads(l[7:]) for l in p.stderr.splitlines() if l.startswith('IO_RUN ')), {})
    if p.returncode:
        raise RuntimeError(script + ' failed: ' + p.stderr[-800:])
    return stats


def main(tree, label, sheets, extra, out, ids):
    tree = Path(tree).resolve(); sheets = Path(sheets).resolve()
    rel = f'research/excavator/machine-{label}'
    packet = tree / rel / 'packet'; supp = packet / 'supp'
    steps = {}
    steps['prepare'] = run(tree, 'jobs/claim-kit/kit.py', '--repo', tree, 'prepare', *ids, '--agent', 'claude', '--write', packet)
    steps['declarations'] = run(tree, NRA + '/make_declarations.py', packet, packet / 'SUPPLEMENT_DECLARATIONS.json')
    decl = json.loads((packet / 'SUPPLEMENT_DECLARATIONS.json').read_bytes())
    decl['sources'].extend(json.loads(Path(extra).read_bytes()))
    (packet / 'SUPPLEMENT_DECLARATIONS.json').write_text(json.dumps(decl, indent=1, ensure_ascii=False) + '\n')
    steps['supplement'] = run(tree, 'jobs/claim-kit/source_supplement.py', '--repo', tree, 'prepare', '--parent', packet,
                              '--sources', packet / 'SUPPLEMENT_DECLARATIONS.json', '--agent', 'claude', '--write', supp)
    steps['view'] = run(tree, 'jobs/claim-kit/kit.py', '--repo', tree, 'view', supp)
    steps['view_order'] = run(tree, 'jobs/claim-kit/kit.py', '--repo', tree, 'view', supp, '--order', ids[0])
    sys.path.insert(0, str(tree / 'jobs/claim-kit'))
    import batch
    _, mine = batch.load_packet(supp, tree, check_sources=False)
    _, theirs = batch.load_packet(sheets, tree, check_sources=False)
    remap = {theirs[i]['fingerprint']: mine[i]['fingerprint'] for i in mine}
    with (sheets / 'decisions.csv').open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f)); fields = list(rows[0])
    for r in rows:
        r['dossier_sha256'] = remap[r['dossier_sha256']]
    with (supp / 'decisions.csv').open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n'); w.writeheader(); w.writerows(rows)
    for name in ('clauses.csv', 'RATIONALES.json'):
        target = supp / name
        if target.exists():
            target.unlink()
        target.write_bytes((sheets / name).read_bytes())
    steps['apply'] = run(tree, 'jobs/claim-kit/kit.py', '--repo', tree, 'apply', supp, '--write', supp / 'applied')
    steps['batch_check'] = run(tree, 'jobs/claim-kit/kit.py', '--repo', tree, 'batch-check', supp, supp / 'applied')
    fresh = [json.loads(l) for l in (supp / 'applied/CLAIMS.proposed.jsonl').read_text().splitlines() if l.strip()]
    reviewed = [json.loads(l) for l in (sheets / 'applied-v1/CLAIMS.proposed.jsonl').read_text().splitlines() if l.strip()]
    def strip(c):
        c = json.loads(json.dumps(c)); c['claim_kit'].pop('dossier_sha256', None); return c
    check = json.loads((supp / 'applied/CHECK_SUMMARY.json').read_bytes())
    result = {'label': label, 'tree': tree.name, 'ids': ids, 'steps': steps,
              'machine_seconds': round(sum(s.get('seconds', 0) for s in steps.values()), 2),
              'claims_equal_except_dossier_sha256': [strip(a) == strip(b) for a, b in zip(fresh, reviewed)],
              'claims_count': [len(fresh), len(reviewed)],
              'batch_check': {k: check.get(k) for k in ('strict_claim_pass', 'strict_claim_fail', 'outcomes_including_blocked', 'actual_claim_checker')}}
    Path(out).write_text(json.dumps(result, indent=1) + '\n')
    print(json.dumps({k: result[k] for k in ('label', 'machine_seconds', 'claims_count')}),
          {k: v.get('seconds') for k, v in steps.items()})


if __name__ == '__main__':
    a = sys.argv[1:]
    main(a[0], a[1], a[2], a[3], a[4], a[5:])

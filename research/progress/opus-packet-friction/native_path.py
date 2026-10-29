"""Apply the real NRA t5 producer sheets to a freshly prepared supplemented packet, then batch-check.

The sheets are the producer's own decisions/clauses/rationales. Only the dossier_sha256 column is
rewritten, mechanically, from the production packet fingerprint to the fresh packet's fingerprint
for the same instrument (a code change re-versions every packet). The resulting claims are compared
with the production applied-v1 claims field by field: they may differ only in
claim_kit.dossier_sha256. Nothing is reviewed, published or decided.

Usage: python3 native_path.py TREE PACKET_FOLDER OUT.json [--actual-checker]
"""
import csv
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
NRA = 'research/excavator/claude-nira-sweep-2026-10-29/t5/packet/supp'


def run(tree, *args):
    command = [sys.executable, '-B', str(HERE / 'io_run.py'), str(tree / 'jobs/claim-kit/kit.py'), '--repo', str(tree), *map(str, args)]
    done = subprocess.run(command, cwd=tree, capture_output=True, text=True)
    stats = next((json.loads(l[7:]) for l in done.stderr.splitlines() if l.startswith('IO_RUN ')), {})
    return {'ok': done.returncode == 0, 'error': None if not done.returncode else done.stderr[-600:], **stats}


def main(tree, folder, out, actual=False):
    tree = Path(tree).resolve(); folder = Path(folder).resolve(); production = tree / NRA
    old = json.loads((production / 'PACKET.json').read_bytes())
    sys.path.insert(0, str(tree / 'jobs/claim-kit'))
    import batch
    _, old_dossiers = batch.load_packet(production, tree, check_sources=False)
    _, new_dossiers = batch.load_packet(folder, tree, check_sources=False)
    remap = {old_dossiers[i]['fingerprint']: new_dossiers[i]['fingerprint'] for i in new_dossiers}
    with (production / 'decisions.csv').open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f)); fields = list(rows[0])
    for r in rows:
        r['dossier_sha256'] = remap[r['dossier_sha256']]
    for name in ('decisions.csv',):
        with (folder / name).open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n'); w.writeheader(); w.writerows(rows)
    for name in ('clauses.csv', 'RATIONALES.json'):
        (folder / name).write_bytes((production / name).read_bytes())
    result = {'packet': folder.relative_to(tree).as_posix()}
    result['apply'] = run(tree, 'apply', folder, '--write', folder / 'applied-native')
    check_args = ['batch-check', folder, folder / 'applied-native']
    result['batch_check'] = run(tree, *check_args) if actual else None
    if not actual:
        sys.path.insert(0, str(tree / 'jobs/claim-kit'))
        result['batch_check_inline'] = batch.check(tree, folder, folder / 'applied-native', actual=False)
    fresh = [json.loads(l) for l in (folder / 'applied-native/CLAIMS.proposed.jsonl').read_text().splitlines() if l.strip()]
    prod = [json.loads(l) for l in (production / 'applied-v1/CLAIMS.proposed.jsonl').read_text().splitlines() if l.strip()]
    def strip(c):
        c = json.loads(json.dumps(c)); c['claim_kit'].pop('dossier_sha256', None); return c
    result['claims'] = {'fresh': len(fresh), 'production': len(prod),
        'ids_equal': [c['instrument_id'] for c in fresh] == [c['instrument_id'] for c in prod],
        'equal_except_dossier_sha256': [strip(a) == strip(b) for a, b in zip(fresh, prod)],
        'dossier_sha256_remapped_exactly': all(remap.get(b['claim_kit']['dossier_sha256']) == a['claim_kit']['dossier_sha256']
                                               for a, b in zip(fresh, prod))}
    audit = json.loads((folder / 'applied-native/AUDIT.json').read_bytes())
    prod_audit = json.loads((production / 'applied-v1/AUDIT.json').read_bytes())
    result['outcomes_equal'] = [(a['instrument_id'], a['outcome'], a['errors']) for a in audit] == \
                               [(a['instrument_id'], a['outcome'], a['errors']) for a in prod_audit]
    Path(out).write_text(json.dumps(result, indent=1, default=str) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'batch_check_inline'}, default=str)[:2000])


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], '--actual-checker' in sys.argv)

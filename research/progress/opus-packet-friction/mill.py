"""MILL: method-of-difference replay for claim-kit packets (after J. S. Mill's canon of difference).

Prepare real packets in an isolated replay tree, then change exactly one input at a time and
record whether the native `kit.py view` still accepts the packet, how long it took and how many
bytes the process read. Each change is reverted before the next. Unrelated changes should leave a
packet valid; relevant ones must still invalidate it.

The replay tree is a hardlinked copy whose files are read-only: every edit here unlinks first and
writes a new file, so the shared inode of the pristine checkout is never altered. Engineering
evidence only; it never publishes, reviews or decides anything.

Usage: python3 mill.py TREE LABEL OUT.json [--batches supp,undecided]
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
NRA = 'research/excavator/claude-nira-sweep-2026-10-29'
# Undecided members of saved Codex continuous packets b05/b06, reserved by one agent; the replay
# prepares as that reservation holder in the isolated tree only.
UNDECIDED = ['EO:10673', 'EO:10740', 'EO:10772', 'EO:10785']
UNDECIDED_AGENT = 'codex-continuous-prior-b04'
IO_RUN = HERE / 'io_run.py'


class Tree:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.undo = []

    def p(self, rel):
        return self.root / rel

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True, text=True).stdout

    def write(self, rel, raw):
        path = self.p(rel)
        old = path.read_bytes() if path.exists() else None
        if path.exists():
            path.unlink()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        self.undo.append(('restore', rel, old))

    def delete(self, rel):
        path = self.p(rel)
        old = path.read_bytes()
        path.unlink()
        self.undo.append(('restore', rel, old))

    def track(self, *rels):
        self.git('add', '-f', '--', *rels)
        self.undo.append(('untrack', rels, None))

    def revert(self):
        while self.undo:
            kind, rel, old = self.undo.pop()
            if kind == 'untrack':
                self.git('rm', '-q', '--cached', '--', *rel)
                continue
            path = self.p(rel)
            if path.exists():
                path.unlink()
            if old is not None:
                path.write_bytes(old)
                os.chmod(path, 0o444)


def kit(tree, *args):
    """Run one native kit command in its own process; return result, seconds and I/O counters."""
    command = [sys.executable, '-B', str(IO_RUN), str(tree.root / 'jobs/claim-kit/kit.py'), '--repo', str(tree.root), *map(str, args)]
    run = subprocess.run(command, cwd=tree.root, capture_output=True, text=True)
    stats = {}
    for line in run.stderr.splitlines():
        if line.startswith('IO_RUN '):
            stats = json.loads(line[7:])
    error = None
    if run.returncode:
        tail = [l for l in run.stderr.splitlines() if l.strip() and not l.startswith('IO_RUN ')]
        error = tail[-1][:300] if tail else 'exit %d' % run.returncode
    return {'ok': run.returncode == 0, 'error': error, **stats}, run.stdout


def supplement(tree, *args):
    command = [sys.executable, '-B', str(IO_RUN), str(tree.root / 'jobs/claim-kit/source_supplement.py'), '--repo', str(tree.root), *map(str, args)]
    run = subprocess.run(command, cwd=tree.root, capture_output=True, text=True)
    stats = {}
    for line in run.stderr.splitlines():
        if line.startswith('IO_RUN '):
            stats = json.loads(line[7:])
    if run.returncode:
        raise RuntimeError(run.stderr[-2000:])
    return stats


def packet_ids(folder):
    return sorted(json.loads((folder / 'PACKET.json').read_bytes())['input_pins'])


def prepare_supp(tree, dest, label):
    """24 NRA t5 orders (now owned, so a replacement proposal) plus the batch's real declarations."""
    ids = packet_ids(tree.p(NRA + '/t5/packet'))
    base = dest / 'packet'
    receipts = {}
    receipts['prepare'], _ = kit(tree, 'prepare', *ids, '--agent', 'claude', '--replacement-proposal', '--write', base)
    if not receipts['prepare']['ok']:
        raise RuntimeError(receipts['prepare'])
    receipts['supplement'] = supplement(tree, 'prepare', '--parent', base,
        '--sources', tree.p(NRA + '/t5/packet/SUPPLEMENT_DECLARATIONS.json'), '--agent', 'claude', '--write', base / 'supp')
    return base / 'supp', ids, receipts


def prepare_undecided(tree, dest, label):
    receipts = {}
    receipts['prepare'], _ = kit(tree, 'prepare', *UNDECIDED, '--agent', UNDECIDED_AGENT, '--write', dest / 'packet')
    if not receipts['prepare']['ok']:
        raise RuntimeError(receipts['prepare'])
    return dest / 'packet', list(UNDECIDED), receipts


def first_claim_line(tree, iid=None, exclude_ids=()):
    for path in sorted(tree.p('research/readiness/claims').glob('*.jsonl')):
        for line in path.read_bytes().splitlines():
            if line.strip():
                c = json.loads(line)
                if (iid is None and c['instrument_id'] not in exclude_ids) or c['instrument_id'] == iid:
                    return line, c
    return None, None


def perturbations(tree, folder, ids):
    """(name, expected, apply). expected: 'valid' (independent) or 'invalid' (relevant)."""
    rel_folder = folder.relative_to(tree.root).as_posix()
    packet = json.loads((folder / 'PACKET.json').read_bytes())
    t6 = NRA + '/t6/packet/supp'
    unrelated_package = {n: tree.p(t6 + '/' + n).read_bytes() for n in ('RATIONALES.json', 'decisions.csv', 'clauses.csv')}
    other_ids = set(packet_ids(tree.p(t6)))
    assert not other_ids & set(ids)

    def package(where, files):
        rels = []
        for name, raw in files.items():
            tree.write(where + '/' + name, raw); rels.append(where + '/' + name)
        tree.track(*rels)

    def relevant_sheets():
        iid = ids[0]
        decisions = ('instrument_id,research_rationale\n%s,@rationale:mill\n' % iid).encode()
        return {'RATIONALES.json': b'{"mill": "A shared rationale written for a requested instrument."}\n',
                'decisions.csv': decisions, 'clauses.csv': b'instrument_id,reason\n'}

    def own_package():
        # The producer's filled sheets of the real t5 batch, committed while the packet is in flight.
        rels = []
        for name in ('RATIONALES.json', 'decisions.csv', 'clauses.csv'):
            src = tree.p(NRA + '/t5/packet/supp/' + name).read_bytes() if 'nira' in rel_folder or True else b''
            tree.write(rel_folder + '/' + name, src); rels.append(rel_folder + '/' + name)
        tree.track(*rels)

    def many_packages():
        for n in range(12):
            package('research/excavator/mill-unrelated/pkg%02d' % n, unrelated_package)

    def unrelated_claims_file():
        line, _ = first_claim_line(tree, exclude_ids=set(ids))
        tree.write('research/readiness/claims/zz-mill-unrelated.jsonl', line + b'\n')

    def unrelated_completion_receipt():
        src = tree.p(t6 + '/complete-v2')
        for path in sorted(src.rglob('*')):
            if path.is_file() and path.name in ('TRACKER_CLAIMS.jsonl', 'TALLY.json', 'INPUTS.json', 'PUBLICATION.json'):
                tree.write('research/excavator/mill-unrelated/complete-v9/' + path.relative_to(src).as_posix(), path.read_bytes())

    def unrelated_fragment_provider():
        tree.write('jobs/mill-provider/output/FRAGMENTS.mill.jsonl',
                   b'{"kind": "original_representation", "instrument_id": "EO:999999", "data": {"sha256": "' + b'0' * 64 + b'"}}\n')

    def relevant_claim():
        line, claim = first_claim_line(tree, iid=ids[0])
        if line is None:
            line, claim = first_claim_line(tree)
            claim = dict(claim, instrument_id=ids[0]); line = json.dumps(claim, sort_keys=True, separators=(',', ':')).encode()
        tree.write('research/readiness/claims/zz-mill-relevant.jsonl', line + b'\n')

    def competing_version():
        line, claim = first_claim_line(tree, iid=ids[0])
        if claim is None:
            _, claim = first_claim_line(tree)
        claim = dict(claim, instrument_id=ids[0], research_rationale='A competing producer version (mill fixture).')
        tree.write('research/excavator/mill-relevant/applied-v1/CLAIMS.proposed.jsonl', json.dumps(claim).encode() + b'\n')

    def review_record():
        tree.write('research/excavator/mill-relevant/REVIEW.json', json.dumps({
            'schema': 'mill-fixture-review/v1', 'reviewer': 'mill-fixture', 'instrument_id': ids[0],
            'claim_sha256': '1' * 64, 'verdict': 'rejected'}).encode())

    def attestation():
        tree.write('research/readiness/component_attestations/zz-mill.jsonl', json.dumps({
            'schema': 'eo-component-attestation/v1', 'attestation_id': 'MILL', 'instrument_id': ids[0]}).encode() + b'\n')

    def held_text_edit():
        rel = sorted(packet['held_text_file_pins'])[0]
        tree.write(rel, tree.p(rel).read_bytes() + b' ')

    def owner_ruling():
        tree.write('research/readiness/owner_rulings/2026-10-30-mill-fixture.md', b'# Fixture ruling for replay only\n')

    def protocol_edit():
        tree.write('jobs/claim-kit/BATCH.md', tree.p('jobs/claim-kit/BATCH.md').read_bytes() + b'\n')

    def bound_research_edit():
        pins = [p for p in packet['prior_research']['input_file_pins']
                if p.startswith('research/') and not p.startswith('research/readiness/')]
        tree.write(pins[0], tree.p(pins[0]).read_bytes() + b'\n')

    def bound_research_delete():
        pins = [p for p in packet['prior_research']['input_file_pins']
                if p.startswith('research/') and not p.startswith('research/readiness/') and tree.p(p).exists()]
        tree.delete(pins[-1])

    def declaration_edit():
        rel = NRA + '/t5/packet/SUPPLEMENT_DECLARATIONS.json'
        tree.write(rel, tree.p(rel).read_bytes() + b'\n')

    def relevant_fragment_registration():
        # Register the first supplemented excerpt's held text as a graded working text.
        dossier_sources = [json.dumps(s) for s in packet['sources'].values()]
        text = next(json.loads(s) for s in dossier_sources if 'text_path' in json.loads(s))
        row = {'kind': 'original_representation', 'instrument_id': ids[0], 'produced_by': 'mill-fixture',
               'data': {'sha256': text.get('sha256') or '2' * 64, 'text_path': text['text_path'],
                        'text_sha256': text.get('text_sha256'), 'grade': 'compiled_transcription',
                        'acceptable_as_original': False, 'url': text.get('url')}}
        tree.write('jobs/mill-provider/output/FRAGMENTS.mill.jsonl', json.dumps(row).encode() + b'\n')

    cases = [
        ('U1 unrelated package tracked', 'valid', lambda: package('research/excavator/mill-unrelated/pkg', unrelated_package)),
        ('U2 own packet sheets tracked', 'valid', own_package),
        ('U3 12 more unrelated packages (>100 tracked)', 'valid', many_packages),
        ('U4 unrelated canonical claims file', 'valid', unrelated_claims_file),
        ('U5 unrelated completion receipt folder', 'valid', unrelated_completion_receipt),
        ('U6 unrelated fragment provider file', 'valid', unrelated_fragment_provider),
        ('R1 relevant package tracked', 'invalid', lambda: package('research/excavator/mill-relevant/pkg', relevant_sheets())),
        ('R2 new canonical claim for a member', 'invalid', relevant_claim),
        ('R3 competing version of a member claim', 'invalid', competing_version),
        ('R4 review record for a member', 'invalid', review_record),
        ('R5 component attestation for a member', 'invalid', attestation),
        ('R6 held source text edited', 'invalid', held_text_edit),
        ('R7 owner ruling added', 'invalid', owner_ruling),
        ('R8 protocol file edited', 'invalid', protocol_edit),
        ('R9 bound prior-research file corrected', 'invalid', bound_research_edit),
        ('R10 bound prior-research file removed', 'invalid', bound_research_delete),
    ]
    if (folder / 'SOURCE_SUPPLEMENT.json').exists():
        cases += [('R11 supplement declarations edited', 'invalid', declaration_edit),
                  ('R12 member source registered as working text', 'invalid', relevant_fragment_registration)]
    return cases


def run(tree_path, label, out, batches):
    tree = Tree(tree_path)
    dest_root = tree.p('research/excavator/mill-' + label)
    if dest_root.exists():
        raise SystemExit('destination exists: ' + str(dest_root))
    result = {'label': label, 'tree': str(tree.root), 'head': tree.git('rev-parse', 'HEAD').strip(), 'batches': {}}
    for name in batches:
        prep = prepare_supp if name == 'supp' else prepare_undecided
        folder, ids, receipts = prep(tree, dest_root / name, label)
        batch = {'packet': folder.relative_to(tree.root).as_posix(), 'ids': ids, 'prepare': receipts}
        for k in ('first_view', 'second_view'):
            batch[k], _ = kit(tree, 'view', folder)
        batch['view_order'], _ = kit(tree, 'view', folder, '--order', ids[0])
        batch['cases'] = []
        for case, expected, apply in perturbations(tree, folder, ids):
            try:
                apply()
                outcome, _ = kit(tree, 'view', folder)
            finally:
                tree.revert()
            observed = 'valid' if outcome['ok'] else 'invalid'
            batch['cases'].append({'case': case, 'expected': expected, 'observed': observed,
                                   'as_expected': observed == expected, **outcome})
            print(label, name, case, observed, outcome.get('error') or '', flush=True)
        batch['after_revert'], _ = kit(tree, 'view', folder)
        result['batches'][name] = batch
    Path(out).write_text(json.dumps(result, indent=1) + '\n')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('tree'); ap.add_argument('label'); ap.add_argument('out')
    ap.add_argument('--batches', default='supp,undecided')
    a = ap.parse_args()
    run(a.tree, a.label, a.out, a.batches.split(','))

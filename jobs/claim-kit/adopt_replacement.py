"""Novellae: file owner-adopted replacement proposals as canonical claims of record.

Named for Justinian's Novellae Constitutiones, the new laws that replaced parts of his own Code once it was in
force. The claim kit's completion publishes a reviewed claim that would replace another owner's claim only as an
isolated `replacement_proposal` outside research/readiness (completion.py, "explicit replacement proposal
required"); it never files one canonically, because the replaced claim belongs to someone else. The owner's
answer to a Kean ask is what lets it count. This tool carries out that answer and nothing more:

1. It refuses unless a Kean decision with the given id exists, an answered Kean ask names that decision, and every
   adopted order's number appears in that ask's question; an owner-ruling file under
   research/readiness/owner_rulings/ must name the decision.
2. For each completion directory it rechecks the kit's own receipts: PUBLICATION.json says replacement_proposal,
   owner acceptance required, written, no status adoption required and 0 human certifications; the proposal file
   has the published sha256; TALLY.json shows every planted control caught and each adopted claim's exact version
   eligible, whole_case and upheld by source review; INPUTS.json pinned the file holding the replaced claim of
   record at the bytes it has now (so the review saw the claim being replaced).
3. For each claim: the order has a canonical claim of record now (otherwise it is not a replacement), the claim's
   status equals the provisional ledger status (a contest needs the status-adoption route instead), the Stage 19
   gate passes with no errors, no unresolved source-audit hold names this version, and the new file name sorts
   after the replaced claim's file name (completion.py's filename-sort rule), so the native readers (batch.owners,
   the tracker and the checker keep the last version) take the new claim.
4. With --write, under the kit's publication lock, it creates one new canonical claims file whose lines are
   byte-identical to the reviewed proposal lines, verifies that every adopted order's claim of record is now the
   new line, and writes an adoption receipt that records the decision, the ask, the ruling, each proposal line and
   each replaced claim. Existing claim files are never changed (the publication audit allows appends only).

Human certification is unchanged at 0. Without --write it prints the plan and writes nothing.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batch  # noqa: E402
import completion  # noqa: E402

SCHEMA = 'eo-claim-kit-replacement-adoption/v1'
CLAIMS_DIR = 'research/readiness/claims'
RULINGS_DIR = 'research/readiness/owner_rulings'
LEDGER = 'research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv'
HOLDS = 'research/readiness/SOURCE_AUDIT_HOLDS.jsonl'
GATE = 'research/stage19/code/claim_gate.py'
DECISIONS = 'jobs/kean/register/decisions.jsonl'
ASKS = 'jobs/kean/register/asks.jsonl'
require = completion.require


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def rel(repo, path):
    return Path(path).resolve().relative_to(repo).as_posix()


def latest(path):
    """Kean register rows, newest revision of each id."""
    rows = {}
    for line in path.read_text('utf-8').splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get('rev', 0) >= rows.get(row['id'], {}).get('rev', -1):
                rows[row['id']] = row
    return rows


def owner_approval(repo, decision_id, ruling):
    decision = latest(repo / DECISIONS).get(decision_id)
    require(decision is not None, 'Kean decision not found: ' + decision_id)
    asks = [a for a in latest(repo / ASKS).values() if a.get('decision') == decision_id and a.get('status') == 'answered']
    require(asks, 'no answered Kean ask names decision ' + decision_id)
    numbers = set()
    for ask in asks:
        numbers.update(re.findall(r'\b\d{1,5}[A-Z]?\b', ask['question']))
    ruling_path = batch.safe(repo, ruling)
    require(ruling_path.is_file() and ruling_path.parent == repo / RULINGS_DIR, 'owner ruling file required under ' + RULINGS_DIR)
    ruling_raw = ruling_path.read_bytes()
    require(decision_id.encode() in ruling_raw, 'owner ruling file does not name ' + decision_id)
    return decision, asks, numbers, {'path': rel(repo, ruling_path), 'sha256': sha(ruling_raw)}


def load_json(path):
    return completion.read_json(path.read_bytes())


def completion_claims(repo, folder):
    """The proposal lines of one completion, each with the receipts that make it eligible."""
    folder = batch.safe(repo, folder)
    publication_raw = (folder / 'PUBLICATION.json').read_bytes()
    publication = completion.read_json(publication_raw)
    require(publication.get('mode') == 'replacement_proposal', 'not a replacement proposal publication: ' + rel(repo, folder))
    require(publication.get('owner_acceptance_required') is True and publication.get('written') is True,
            'publication not written for owner acceptance: ' + rel(repo, folder))
    require(publication.get('independent_human_certifications') == 0, 'unexpected human certification count')
    require(not publication.get('status_adoption_required'),
            'status-overlay proposals need the status-adoption route (ADOPTION_ROWS, population contract): ' + rel(repo, folder))
    proposal = batch.safe(repo, publication['path'])
    raw = proposal.read_bytes()
    require(sha(raw) == publication['sha256'], 'proposal bytes differ from the published sha256: ' + publication['path'])
    tally_raw = (folder / 'TALLY.json').read_bytes()
    tally = completion.read_json(tally_raw)
    require(tally.get('plants_placed', 0) >= 1 and tally.get('plants_caught') == tally['plants_placed'] and
            all(c.get('caught') is True for c in tally.get('controls', [])), 'planted controls not all caught: ' + rel(repo, folder))
    require(tally.get('independent_human_certifications') == 0, 'unexpected human certification count')
    inputs_raw = (folder / 'INPUTS.json').read_bytes()
    pins = completion.read_json(inputs_raw).get('dependency_sha256', {})
    receipts = {'completion': rel(repo, folder),
                'publication': {'path': rel(repo, folder / 'PUBLICATION.json'), 'sha256': sha(publication_raw)},
                'tally': {'path': rel(repo, folder / 'TALLY.json'), 'sha256': sha(tally_raw)},
                'inputs': {'path': rel(repo, folder / 'INPUTS.json'), 'sha256': sha(inputs_raw)}}
    lines = raw.splitlines(keepends=True)
    require(lines and all(line.endswith(b'\n') for line in lines), 'proposal must be newline-terminated JSONL')
    out = []
    for number, line in enumerate(lines, 1):
        require(line.strip(), 'blank line in proposal: ' + publication['path'])
        claim = completion.read_json(line)
        iid, claim_sha = claim.get('instrument_id'), completion.claim_sha(claim)
        rows = [r for r in tally.get('outcomes', []) if r.get('instrument_id') == iid]
        require(len(rows) == 1 and rows[0].get('outcome') == 'eligible' and rows[0].get('claim_sha256') == claim_sha and
                rows[0].get('publication_kind') == 'whole_case' and rows[0].get('source_review_upheld') is True and
                iid in tally.get('eligible', []), 'completion does not show this exact version eligible and upheld: ' + str(iid))
        out.append({'instrument_id': iid, 'claim_sha256': claim_sha, 'claim': claim, 'raw': line, 'pins': pins,
                    'proposal': {'path': publication['path'], 'sha256': publication['sha256'], 'line': number},
                    **receipts})
    return out


def load_gate(repo):
    spec = importlib.util.spec_from_file_location('adopt_replacement_claim_gate', repo / GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def held(repo):
    path = repo / HOLDS
    result = set()
    if path.exists():
        for line in path.read_text('utf-8').splitlines():
            if line.strip():
                hold = json.loads(line)
                if hold.get('state') == 'unresolved':
                    result.add((hold.get('instrument_id'), hold.get('claim_sha256')))
    return result


def plan(repo, decision_id, ruling, folders, target):
    repo = Path(repo).resolve()
    decision, asks, numbers, ruling_ref = owner_approval(repo, decision_id, ruling)
    target_path = batch.safe(repo, target)
    require(target_path.parent == repo / CLAIMS_DIR and target_path.suffix == '.jsonl', 'target must be a top-level ' + CLAIMS_DIR + ' *.jsonl file')
    require(not target_path.exists(), 'target already exists: ' + target)
    claims = [c for folder in folders for c in completion_claims(repo, folder)]
    require(claims, 'no proposal lines selected')
    ids = [c['instrument_id'] for c in claims]
    require(len(set(ids)) == len(ids), 'an order appears in more than one selected proposal line')
    existing = batch.owners(repo)
    with (repo / LEDGER).open(encoding='utf-8', newline='') as stream:
        ledger = {r['instrument_id']: r['provisional_substantive_status'] for r in csv.DictReader(stream)}
    gate, holds = load_gate(repo), held(repo)
    for c in claims:
        iid = c['instrument_id']
        require(iid.split(':', 1)[-1] in numbers, 'order not named in the owner-answered ask: ' + iid)
        prior = existing.get(iid)
        require(prior is not None, 'no claim of record to replace (use own filing or status adoption): ' + iid)
        prior_path = Path(prior['path'])
        require(prior_path.parent.as_posix() == CLAIMS_DIR, 'claim of record is not a canonical claims file: ' + prior['path'])
        require(target_path.name > prior_path.name, 'adopted replacement would be shadowed by an existing claim filename: '
                + iid + ' in ' + prior['path'])
        require(c['pins'].get(prior['path']) == sha((repo / prior['path']).read_bytes()),
                'claim of record changed since the completion pinned it; re-run completion: ' + iid + ' in ' + prior['path'])
        require(c['claim_sha256'] != prior['claim_sha256'], 'proposal equals the claim of record: ' + iid)
        status = ledger.get(iid)
        require(status, 'order has no provisional ledger status (status adoption route required): ' + iid)
        require(c['claim'].get('whole_order_status') == status, 'claim status contests the ledger (needs a status decision): ' + iid)
        errors = gate.validate_claim(c['claim'], expected_status=status)
        require(not errors, 'Stage 19 gate errors for ' + iid + ': ' + '; '.join(map(str, errors)))
        require((iid, c['claim_sha256']) not in holds, 'unresolved source-audit hold on this version: ' + iid)
        c['replaces'] = {'owner': prior['owner'], 'path': prior['path'], 'line': prior['line'], 'claim_sha256': prior['claim_sha256'],
                         'ledger_status': status}
    raw = b''.join(c['raw'] for c in claims)
    receipt = {
        'schema': SCHEMA, 'decision': decision_id, 'decision_rev': decision.get('rev', 0), 'decision_date': decision.get('date'),
        'asks': sorted(a['id'] for a in asks), 'ruling': ruling_ref,
        'publication': {'path': rel(repo, target_path), 'sha256': sha(raw), 'claims': len(claims),
                        'byte_identical_to_reviewed_proposals': True},
        'claims': [{'instrument_id': c['instrument_id'], 'claim_sha256': c['claim_sha256'], 'line': n,
                    'proposal': c['proposal'], 'completion': c['completion'], 'publication_receipt': c['publication'],
                    'tally': c['tally'], 'inputs': c['inputs'], 'replaces': c['replaces']}
                   for n, c in enumerate(claims, 1)],
        'independent_human_certifications': 0,
        'note': 'Owner adoption of AI-reviewed replacement proposals as claims of record. The replaced claims stay in '
                'their files; the new file sorts after them, so readers that keep the last version take these. '
                'Human certification is unchanged (0).'}
    return receipt, raw, target_path


def adopt(repo, decision_id, ruling, folders, target, receipt_path, write=False):
    repo = Path(repo).resolve()
    receipt_file = batch.safe(repo, receipt_path)
    require(receipt_file.suffix == '.json' and not receipt_file.is_relative_to(repo / CLAIMS_DIR), 'receipt must be a .json file outside the claims folder')
    require(not receipt_file.exists(), 'receipt already exists: ' + receipt_path)
    if not write:
        receipt, _, _ = plan(repo, decision_id, ruling, folders, target)
        return dict(receipt, written=False)
    lock = completion.PublicationLock(repo, receipt_file.parent)
    lock.acquire()
    try:
        receipt, raw, target_path = plan(repo, decision_id, ruling, folders, target)
        with target_path.open('xb') as stream:
            stream.write(raw)
        try:
            now = batch.owners(repo)
            for row in receipt['claims']:
                record = now.get(row['instrument_id'], {})
                require(record.get('path') == receipt['publication']['path'] and record.get('line') == row['line'] and
                        record.get('claim_sha256') == row['claim_sha256'], 'adopted claim is not the claim of record: ' + row['instrument_id'])
        except BaseException:
            target_path.unlink()
            raise
        receipt['written'] = True
        receipt_file.parent.mkdir(parents=True, exist_ok=True)
        with receipt_file.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
        return receipt
    finally:
        lock.release()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--repo', default='.')
    ap.add_argument('--decision', required=True, help='Kean decision id of the owner adoption')
    ap.add_argument('--ruling', required=True, help='owner-ruling file under ' + RULINGS_DIR + ' naming the decision')
    ap.add_argument('--completion', action='append', required=True, help='completion result directory (repeatable)')
    ap.add_argument('--target', required=True, help='new canonical claims file, sorting after every replaced file')
    ap.add_argument('--receipt', required=True, help='adoption receipt (.json) to create')
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args(argv)
    try:
        result = adopt(a.repo, a.decision, a.ruling, a.completion, a.target, a.receipt, a.write)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, indent=2))
        return 1
    print(json.dumps(dict(result, ok=True), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())

"""Replay worker for the Maudslay conveyor: answers each worker session with the Lind stage-0 pilot's SAVED real
outputs instead of a model, so the conveyor can be exercised end to end on the real claim kit at zero model cost.

It reuses fakes/fake_worker.py's event stream and replaces only the three role functions:
- producer: copies the Lind producer's row, clause rows, rationales and STATUS_DECISION.json for the order;
- status reviewer: copies the Lind status reviewer's decision, rationale and checked evidence into each sheet
  (the sheet's own reviewer name and hashes are kept);
- blind reviewer: copies the Lind arm's verdict and defects for a claim with the same sha256. A claim Lind never
  reviewed is the conveyor's own planted control and is rejected with a date defect. That is a replay assumption:
  both Lind arms caught their control. For after-reveal mode, the Lind arm's verdict on the genuine claim is used.

This measures coordination and integration, not research quality: the legal content is exactly the pilot's.
"""
import csv
import importlib.util
import json
import re
from pathlib import Path

REPO = Path('/home/user/executive-orders')
LIND = REPO / 'research/excavator/claude-lind-2026-11-12'
spec = importlib.util.spec_from_file_location('fake_worker', REPO / 'jobs/maudslay-conveyor/fakes/fake_worker.py')
fw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fw)


def lind_packet(iid):
    for p in ('p1', 'p2'):
        d = LIND / p / 'packet'
        if any(r['instrument_id'] == iid for r in csv.DictReader(open(d / 'decisions.csv', encoding='utf-8'))):
            return d
    raise ValueError('order not in the Lind pilot: ' + iid)


def produce(prompt, sc):
    iid, work = fw.field(prompt, 'ORDER'), Path(fw.field(prompt, 'SHEET FOLDER'))
    src = lind_packet(iid)
    df, dr = fw.rows(work / 'decisions.csv')
    cf, cr = fw.rows(work / 'clauses.csv')
    lrow = next(r for r in csv.DictReader(open(src / 'decisions.csv', encoding='utf-8')) if r['instrument_id'] == iid)
    lcl = [r for r in csv.DictReader(open(src / 'clauses.csv', encoding='utf-8')) if r.get('instrument_id') == iid]
    r = dr[0]
    for k in df:
        if k in lrow and k not in ('dossier_sha256',):
            r[k] = lrow[k]
    if lcl:
        # Lind's clause rows exactly: a producer may replace the template's whole-order scope with slices, so a
        # template scope Lind did not keep is dropped (keeping it blank made kit apply fail on EO 9447).
        cr = [{k: c.get(k, '') for k in cf} for c in lcl]
    fw.write_csv(work / 'decisions.csv', df, dr)
    fw.write_csv(work / 'clauses.csv', cf, cr)
    rat = json.loads((src / 'RATIONALES.json').read_text(encoding='utf-8') or '{}')
    slug = iid.replace(':', '_')
    (work / 'RATIONALES.json').write_text(json.dumps({k: v for k, v in rat.items() if slug in k} or rat), encoding='utf-8')
    a = [json.loads(l) for l in open(src / 'ASSESSMENT.jsonl', encoding='utf-8') if json.loads(l)['id'] == iid]
    (work / 'ASSESSMENT.json').write_text(json.dumps(a[0] if a else {'id': iid}), encoding='utf-8')
    (work / 'REPORT.md').write_text(f'replay of the Lind stage-0 producer for {iid}\n', encoding='utf-8')
    dec_path = fw.field(prompt, 'STATUS DECISION')
    lsd = src / 'undecided' / slug / 'STATUS_DECISION.json'
    if dec_path and lsd.exists():
        saved = json.loads(lsd.read_text(encoding='utf-8'))
        if saved.get('approved'):
            Path(dec_path).write_text(json.dumps(saved, indent=1), encoding='utf-8')
    return iid, 0, [f"cat {fw.field(prompt, 'VIEW')}"]


def status_review(prompt, sc):
    name = fw.field(prompt, 'STATUS REVIEWER NAME')
    for line in re.findall(r'^MEMBER: (.+)$', prompt, re.M):
        parts = dict(x.split(': ', 1) for x in line.split(' | ')[1:])
        iid = line.split(' | ')[0].strip()
        sheet = Path(parts['SHEET'])
        rv = json.loads(sheet.read_text(encoding='utf-8'))
        saved = LIND / 'overlay' / iid.replace(':', '_') / 'review-v1' / 'STATUS_REVIEW.json'
        if saved.exists():
            s = json.loads(saved.read_text(encoding='utf-8'))
            for k in ('decision', 'rationale', 'checked_evidence_ids', 'independence_confirmed', 'source_checks_confirmed'):
                rv[k] = s.get(k)
        sheet.write_text(json.dumps(rv, indent=1), encoding='utf-8')
    return name, 0, []


def review(prompt, sc):
    src, out, name, mode = (fw.field(prompt, 'CLAIMS TO REVIEW'), fw.field(prompt, 'WRITE REVIEWS TO'),
                            fw.field(prompt, 'REVIEWER NAME'), fw.field(prompt, 'MODE'))
    arm = name.rsplit('-', 1)[1]
    saved = {}
    for f in ('BLIND_REVIEW_' + arm + '.jsonl', 'AFTER_REVEAL_' + arm + '.jsonl'):
        p = LIND / 'reviews' / f
        if p.exists():
            for l in open(p, encoding='utf-8'):
                r = json.loads(l)
                saved[r['claim_sha256']] = r
    recs = []
    for line in Path(src).read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        c = json.loads(line)
        sha = fw.canon(c)
        s = saved.get(sha)
        if s is None:
            v, d = 'rejected', [{'field': 'whole_order_end.date', 'problem': 'replay: claim not in the Lind record, '
                                 'treated as the conveyor\'s planted control (both Lind arms caught theirs)'}]
        else:
            v = s['verdict']
            if mode == 'after_reveal' and v == 'upheld':
                v = 'upheld_after_reveal'
            d = s.get('defects', [])
        recs.append({'instrument_id': c['instrument_id'], 'claim_sha256': sha, 'verdict': v, 'defects': d,
                     'reasons': 'replay of the Lind stage-0 arm ' + arm, 'scope': 'whole_case'})
    Path(out).write_text(''.join(json.dumps(r) + '\n' for r in recs), encoding='utf-8')
    return name, 0, []


fw.produce, fw.status_review, fw.review = produce, status_review, review

if __name__ == '__main__':
    fw.main()

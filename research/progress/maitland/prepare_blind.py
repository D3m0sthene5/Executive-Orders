"""Prepare one frozen temporal-record challenge, using Mountweazel hash conventions.

Run before source review. Keys are written outside the repository/reviewer inputs;
no canonical claims or approvals are changed. This bounded adapter does not extend
Mountweazel's Stage19 mutation schema or claim its historic calibration transfers.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import secrets
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'jobs/mountweazel'))
from mountweazel import sha


def main():
    source = ROOT/'research/progress/maitland/source-production/CANDIDATES.json'
    dest = ROOT/'research/progress/maitland/blind-review-input'
    key_path = Path('/tmp/maitland-control-key.json')
    if dest.exists() or key_path.exists():
        raise ValueError('Frozen challenge exists; no reroll/overwrite')
    bundle = json.loads(source.read_text())
    records = deepcopy(bundle['provisions']+bundle['transitions'])
    by = {r.get('provision_id', r.get('transition_id')): r for r in records}
    keys = []
    def mutate(rid, field, value, defect_code, locus_terms, rationale):
        rec = by[rid]
        original = deepcopy(rec)
        before = rec[field]
        rec[field] = value
        keys.append({'record_id': rid, 'field': field, 'before': before, 'after': value,
                     'genuine_sha256': sha(original), 'planted_sha256': sha(rec),
                     'defect_code': defect_code, 'locus_terms': locus_terms,
                     'affected_scope_id': rec.get('affected_provision_id', rid),
                     'rationale': rationale, 'genuine_record': original})
    mutate('T:14189:030-reinstate-13934-chapeau', 'restore_version_id',
           'P:13934:sec3c-chapeau::v0', 'D6', ['EO:13978', 'restore_version_id'],
           'Pre-revocation form includes the earlier EO13978 amendment, not the original chapeau.')
    mutate('T:10973:0605-supersede-food-for-peace-sec111', 'effective_date',
           '1961-11-03', 'D7', ['EO:10973', '1961-09-30', 'effective_date'],
           'Section607 expressly supplies September30 effective time, distinct from November3 signing.')
    renumber = 'T:11963:020-renumber-food-for-peace'
    mutate(renumber, 'new_label', 'Section 6: Director of the Food-for-Peace Program',
           'D4', ['EO:11963', 'new_label', 'Section 5'],
           'The reviewed norm moves from section6 to section5; the separately revoked old section5 is another provision.')
    seed = secrets.token_hex(24)
    random.Random(seed).shuffle(records)
    dest.mkdir(parents=True)
    payload = {'schema':'eo-temporal-blind-record-set/v1','producer':bundle['producer'],
               'records':records,'notice':'Review each exact record against cited held sources. No whole-order, original-authentication or human-certification finding is requested.'}
    raw = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()
    (dest/'RECORDS.json').write_bytes(raw)
    freeze = {'schema':'eo-temporal-blind-freeze/v1','records':len(records),
              'input_file_sha256':hashlib.sha256(raw).hexdigest(),
              'producer_candidate_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
              'record_sha256':sorted(sha(r) for r in records),
              'model_usage':None,'no_rerolls':True}
    (dest/'FREEZE.json').write_text(json.dumps(freeze,indent=2)+'\n')
    key_path.write_text(json.dumps({'seed':seed,'controls':keys,'freeze':freeze},indent=2)+'\n')
    print(json.dumps({'records':len(records),'input_sha256':freeze['input_file_sha256'],'key_outside_repository':True}))


if __name__ == '__main__':
    main()

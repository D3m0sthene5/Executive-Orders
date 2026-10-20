"""Controlled hypothetical pairs. Generated items and answer keys stay outside the repo.

The packet expressly supplies fictional rules. Expected labels concern missing evidence
or those stipulated rules, never an adjudication of disputed executive-order law.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LABELS = {
    'delivery_supported': 'Dated evidence supports delivery of the specified report.',
    'performance_gap': 'Actual performance or delivery is not demonstrated.',
    'recurring_duty_unresolved': 'A first report does not finish the stipulated recurring duty; rescission evidence is absent.',
    'earlier_event_day_8': 'The supplied operative rescission first ends the stipulated duty on day 8.',
    'earlier_event_gap': 'A material earlier rescission is referenced but its date or scope cannot be established.',
    'saved_b_continues': 'The supplied savings provision expressly continues duty B.',
    'savings_scope_gap': 'Missing material savings terms prevent a complete scope conclusion.'}


def sha(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def definitions():
    # Bounded, explicit counterfactual rules remove contested-law assumptions.
    return [
        ('layout', 'The fictional rule ends this one report duty upon recorded delivery. Receipt: delivery on day 8.',
         'The fictional rule ends this one report duty upon recorded delivery.\n\nReceipt:\n delivery on day 8.',
         ['delivery_supported'], ['delivery_supported'], 'invariant'),
        ('deadline', 'A report is due on day 10. No receipt or other performance evidence is supplied.',
         'A report is due on day 10. Receipt establishes delivery on day 8.',
         ['performance_gap'], ['delivery_supported'], 'material'),
        ('performance', 'By its express fictional terms the single duty ends upon delivery. Receipt records delivery on day 8.',
         'By its express fictional terms the single duty ends upon delivery. The receipt has been removed.',
         ['delivery_supported'], ['performance_gap'], 'material'),
        ('recurring', 'The fictional terms require a new report every year until express rescission. The first report was delivered on day 8. No rescission evidence is supplied.',
         'The fictional terms require only one report and expressly end the duty on delivery. The report was delivered on day 8.',
         ['recurring_duty_unresolved'], ['delivery_supported'], 'material'),
        ('earlier_event', 'The fictional rule ends this duty on express rescission. A valid rescission effective day 8 and a redundant rescission on day 20 are supplied.',
         'The fictional rule ends this duty on express rescission. A document says the day 20 rescission repeats an earlier rescission, but the earlier instrument and date have been removed.',
         ['earlier_event_day_8'], ['earlier_event_gap'], 'material'),
        ('savings', 'A fictional instrument rescinds duties A and B on day 20 except B, which continues under the express savings clause.',
         'A fictional instrument rescinds duties A and B on day 20. A reference to a savings annex remains but that annex has been removed.',
         ['saved_b_continues'], ['savings_scope_gap'], 'material')]


def prepare(dest, seed='valla-pairs-1'):
    dest = Path(dest).resolve()
    if dest.is_relative_to(REPO) or dest.exists():
        raise ValueError('new destination outside repository required')
    dest.mkdir(parents=True); batch = []; keys = []; rng = random.Random(seed)
    for name, a, b, ea, eb, relation in definitions():
        pair = []
        for text, expected in ((a, ea), (b, eb)):
            ident = hashlib.sha256((seed + name + text).encode()).hexdigest()[:20]
            item = {'schema': 'SEEDED-reasoning-practice/v1', 'instrument_id': 'SEEDED:' + ident,
                    'SEEDED': True, 'item_id': ident, 'hypothetical': text,
                    'instruction': 'Apply only the stipulated fictional rule. Return item_id, findings (a list selected from the common answer_labels), and reason. Missing material must be acknowledged.',
                    'answer_labels': LABELS}
            batch.append(item); pair.append(ident)
            keys.append({'item_id': ident, 'expected': expected, 'pair': name, 'relation': relation})
    rng.shuffle(batch)
    (dest / 'batch.json').write_text(json.dumps(batch, indent=2) + '\n')
    key = {'schema': 'mountweazel-paired-key/v1', 'items': keys,
           'batch_sha256': sha(batch), 'blinding_technically_enforced': False,
           'blinding_note': 'Key permissions do not isolate a reviewer running under the same account. This generator and operator know the key.',
           'method': 'Explicit fictional conditions plus claim-kit evidence-gap rules; no disputed legal interpretation.',
           'method_sha256': hashlib.sha256((REPO / 'jobs/claim-kit/BATCH.md').read_bytes()).hexdigest()}
    key['seal'] = sha(key)
    (dest / 'KEY.json').write_text(json.dumps(key, indent=2) + '\n'); os.chmod(dest / 'KEY.json', 0o600)
    return {'items': len(batch), 'pairs': len(definitions()), 'blinding_technically_enforced': False}


def score(key_path, batch_path, verdicts):
    key = json.loads(Path(key_path).read_bytes()); seal = key.pop('seal')
    if sha(key) != seal or sha(json.loads(Path(batch_path).read_bytes())) != key['batch_sha256']:
        raise ValueError('key or batch changed')
    if key['method_sha256'] != hashlib.sha256((REPO / 'jobs/claim-kit/BATCH.md').read_bytes()).hexdigest():
        raise ValueError('method changed; prepare a new reviewed pair version')
    rows = json.loads(Path(verdicts).read_bytes()); by_id = {r['item_id']: r for r in rows}
    expected_ids = {k['item_id'] for k in key['items']}
    if len(rows) != len(by_id) or set(by_id) != expected_ids:
        raise ValueError('one verdict per item required; missing/extra/duplicates refused')
    results = []
    for k in key['items']:
        r = by_id[k['item_id']]
        findings = r.get('findings')
        good = (isinstance(findings, list) and sorted(findings) == sorted(k['expected'])
                and isinstance(r.get('reason'), str) and len(r['reason'].strip()) >= 20)
        results.append({'item_id': k['item_id'], 'pair': k['pair'], 'relation': k['relation'], 'passed': good})
    pairs = {k[0]: all(r['passed'] for r in results if r['pair'] == k[0]) for k in definitions()}
    return {'schema': 'mountweazel-paired-score/v1', 'items': results, 'pairs': pairs,
            'items_passed': sum(r['passed'] for r in results), 'blinding_technically_enforced': False,
            'legal_accuracy_estimated': False, 'reviewer_run_required': True}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('prepare'); a.add_argument('--out', type=Path, required=True); a.add_argument('--seed', default='valla-pairs-1')
    a = s.add_parser('score'); a.add_argument('--key', required=True); a.add_argument('--batch', required=True)
    a.add_argument('--verdicts', required=True); a.add_argument('--out', type=Path, required=True)
    a = p.parse_args(argv)
    result = prepare(a.out, a.seed) if a.cmd == 'prepare' else score(a.key, a.batch, a.verdicts)
    if a.cmd == 'score':
        if a.out.resolve().is_relative_to(REPO):
            raise ValueError('item-level scores must remain outside repository')
        a.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('items', 'pairs')}))
    return 0

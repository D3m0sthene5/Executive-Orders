"""H13 replay: are the held later orders the NRA t5 producer could not cite now in a regenerated packet?

Prepares EO 6254 and EO 6438 in an isolated replay tree, records whether any evidence record names
EO 6730 or EO 6620-B, then declares the two held American Presidency Project excerpts (plus the
batch's S.J. Res. 113 excerpt) through the native source-supplement interface and checks that the
supplemented evidence IDs resolve through the assembler's ordinary reference route. Preparation only:
no mechanism, date, ending or legal effect is decided here.

Usage: python3 h13_replay.py TREE OUT.json
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

NRA = 'research/excavator/claude-nira-sweep-2026-10-29'
TEXTS = 'jobs/app-executive-orders/output/texts/'
CASES = [
    {'target': 'EO:6254', 'alias': 'EO6730', 'actor_id': 'EO:6730',
     'file': 'executive-order-6730-revised-code-fair-competition-the-iron-and-steel-industry.txt',
     'url': 'https://www.presidency.ucsb.edu/documents/executive-order-6730-revised-code-fair-competition-the-iron-and-steel-industry',
     'anchor': 'it hereby is approved, said revised Code', 'until': 'shall continue in full force and effect.',
     'reason': 'Held later order approving a revised Iron and Steel code; preparation excerpt only.'},
    {'target': 'EO:6438', 'alias': 'EO6620B', 'actor_id': 'EO:6620-B',
     'file': 'executive-order-6620-b-code-fair-competition-for-the-hotel-industry-modification-executive.txt',
     'url': 'https://www.presidency.ucsb.edu/documents/executive-order-6620-b-code-fair-competition-for-the-hotel-industry-modification-executive',
     'anchor': 'do modify my order of November 17, 1933', 'until': 'numbered two (2) and three (3).',
     'reason': 'Held later order modifying the Hotel code approval; preparation excerpt only.'},
]


def kit(tree, *args, script='jobs/claim-kit/kit.py'):
    run = subprocess.run([sys.executable, '-B', str(tree / script), '--repo', str(tree), *map(str, args)],
                         cwd=tree, capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError(run.stderr[-1500:])
    return run.stdout


def mentions(dossier, needles):
    hits = []
    for eid, e in dossier.get('evidence', {}).items():
        # Record metadata only (actor, source, ids): a number inside quoted text is not a record for it.
        blob = json.dumps({k: v for k, v in e.items() if k != 'text'})
        if any(n in blob for n in needles):
            hits.append(eid)
    return hits


def main(tree, out):
    tree = Path(tree).resolve(); dest = tree / 'research/excavator/h13-replay'
    sys.path.insert(0, str(tree / 'jobs/claim-kit'))
    import batch
    import assemble
    ids = [c['target'] for c in CASES]
    kit(tree, 'prepare', *ids, '--agent', 'claude', '--write', dest / 'packet')
    _, dossiers = batch.load_packet(dest / 'packet', tree)
    before = {c['target']: mentions(dossiers[c['target']], ['6730', '6620-B', '6620B']) for c in CASES}
    nra = json.loads((tree / NRA / 't5/packet/SUPPLEMENT_DECLARATIONS.json').read_bytes())
    sources = [dict(e, instrument_ids=[i for i in e['instrument_ids'] if i in ids]) for e in nra['sources']
               if e['alias'] == 'SJRES113']
    for c in CASES:
        rel = TEXTS + c['file']; raw = (tree / rel).read_bytes(); text = raw.decode('utf-8')
        start = text.index(c['anchor']); end = text.index(c['until'], start) + len(c['until'])
        sha = hashlib.sha256(raw).hexdigest()
        # The held artifact is the registered transcription itself; registered() substitutes the
        # registry's capture hash and grade, which the declaring agent cannot choose.
        sources.append({'alias': c['alias'], 'instrument_ids': [c['target']], 'actor_id': c['actor_id'],
                        'reason': c['reason'], 'char_start': start, 'char_end': end,
                        'source': {'url': c['url'], 'sha256': sha, 'text_path': rel, 'text_sha256': sha,
                                   'page_or_item': 'American Presidency Project transcription', 'local_path': rel}})
    declarations = dest / 'SUPPLEMENT_DECLARATIONS.json'
    declarations.write_text(json.dumps({'schema': 'eo-source-excerpt-declarations/v1', 'sources': sources}, indent=1))
    kit(tree, 'prepare', '--parent', dest / 'packet', '--sources', declarations, '--agent', 'claude',
        '--write', dest / 'packet/supp', script='jobs/claim-kit/source_supplement.py')
    _, supplemented = batch.load_packet(dest / 'packet/supp', tree)
    result = {'packet_before_supplement_mentions': before, 'cases': []}
    for c in CASES:
        evidence = supplemented[c['target']]['evidence']; eid = 'SUPPLEMENT:' + c['alias']
        errors = []
        ref = assemble._reference(eid, evidence, errors) if eid in evidence else None
        rec = evidence.get(eid, {})
        result['cases'].append({'target': c['target'], 'evidence_id': eid, 'present': eid in evidence,
            'reference_errors': errors, 'source_grade': (rec.get('source') or {}).get('grade'),
            'acceptable_as_original': (rec.get('source') or {}).get('acceptable_as_original'),
            'excerpt': rec.get('text'), 'reference': ref})
    view = kit(tree, 'view', dest / 'packet/supp', '--order', CASES[0]['target'])
    result['view_lists_supplement'] = 'SUPPLEMENT:EO6730' in view
    Path(out).write_text(json.dumps(result, indent=1) + '\n'); print(json.dumps(result, indent=1)[:3000])


if __name__ == '__main__':
    main(*sys.argv[1:3])

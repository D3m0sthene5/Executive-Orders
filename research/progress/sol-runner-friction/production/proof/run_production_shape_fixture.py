"""Bounded synthetic payloads in actual production path/reference/import shapes.

The certificate created here is for this isolated synthetic fixture only. It
never changes or supplies a production certificate. Production code/import files
are byte copies; declared payload/custody shapes and induced failure are fixtures.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
import run_matched_checkout as proof

ROOT = Path(__file__).resolve().parents[5]
NAME = proof.NAME


def put(root, rel, value):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(value if isinstance(value, bytes) else value.encode())


def native_consumer_probe(root):
    script = r"""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,'jobs/readiness-tracker')
import tracker
repo=Path.cwd().resolve()
claim=json.loads((repo/'research/readiness/claims/fixture.jsonl').read_text())
ref=claim['original_representation']
reads=[]
stage='index'
def audit(event,args):
    if event!='open' or not isinstance(args[0],(str,bytes)):
        return
    try:
        p=Path(args[0]).resolve().relative_to(repo).as_posix()
    except (ValueError,TypeError):
        return
    if p.endswith('FRAGMENTS.jsonl') or p in (ref['text_path'],ref['raw_path']):
        reads.append({'stage':stage,'path':p})
sys.addaudithook(audit)
index=tracker.W.Index(repo)
candidates=index.match(ref)
assert len(candidates)==1,candidates
assert candidates[0]['declaration_path']=='jobs/provider/output/FRAGMENTS.jsonl'
stage='policy'
errors,dependent=tracker.W.policy(claim,repo,index)
assert errors==['working_text:disclosure_required'],errors
assert dependent==[ref],dependent
assert any(r['stage']=='policy' and r['path']==ref['text_path'] for r in reads),reads
stage='source_span'
span={'source':ref,'char_start':ref['char_start'],'char_end':ref['char_end'],'text':ref['quote']}
span_errors=tracker.F.MODEL.source_span(repo,span,require_bytes=True)
assert span_errors==[],span_errors
assert all(any(r['stage']=='source_span' and r['path']==p for r in reads) for p in [ref['text_path'],ref['raw_path']])
stage='verify'
body=(repo/ref['text_path']).read_bytes()
assert body==b'bounded transcription text\n'
print(json.dumps({'indexed_candidates':len(candidates),'policy_errors':errors,
    'dependent_refs':len(dependent),'source_span_errors':span_errors,
    'expected_body_sha256':hashlib.sha256(body).hexdigest(),'reads':reads,
    'scope':'fixture byte/identity/quote checks only; mandatory disclosure hold retained'}))
"""
    return json.loads(proof.cmd(root, sys.executable, '-B', '-c', script))


def main(target):
    proof.SCRATCH.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='production-shape-', dir=proof.SCRATCH) as tmp:
        source = Path(tmp) / 'source'
        source.mkdir()
        pinned_code = []
        for rel in ['.github/scripts', 'jobs/_lib']:
            shutil.copytree(ROOT / rel, source / rel, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for rel in ['.github/workflows/run-jobs.yml', 'jobs/readiness-tracker/tracker.py',
                    'jobs/claim-kit/working_text.py', 'jobs/claim-kit/factual_events.py', 'jobs/norton/model.py']:
            put(source, rel, (ROOT / rel).read_bytes())
            pinned_code.append({'path': rel, 'sha256': hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()})
        put(source, 'README.md', 'root file retained\n')
        put(source, 'HANDOFF/README.md', 'fixture handoff\n')
        put(source, f'jobs/{NAME}/README.md', 'fixture bounded tracker\n')
        put(source, f'jobs/{NAME}/job.py', "from pathlib import Path\nimport os,sys\nPath(os.environ['OUTPUT_DIR'],'CANDIDATE.txt').write_text('failed candidate')\nsys.exit(9)\n")
        put(source, f'jobs/{NAME}/needs.txt', 'research/readiness\nresearch/stage15/CENSUS\nresearch/valla\n')
        put(source, f'jobs/{NAME}/inputs.txt', 'jobs/*/output/SOURCES.jsonl\njobs/*/output/FRAGMENTS*.jsonl\njobs/*/output/texts/**\njobs/claim-kit/working_text.py\njobs/claim-kit/factual_events.py\njobs/norton/model.py\n')
        put(source, f'jobs/{NAME}/after.txt', 'source-ladder\nclaim-checker\n')
        put(source, f'jobs/{NAME}/output/STATUS.json', json.dumps({'result': 'succeeded', 'started_utc': '2026-01-01T00:00:00Z', 'finished_utc': '2026-01-01T00:00:01Z'}))
        put(source, f'jobs/{NAME}/output/PRIOR.txt', 'retained successful tracker generation\n')
        text = b'bounded transcription text\n'
        raw = b'bounded held original bytes\n'
        text_path = 'jobs/provider/output/texts/EO-FIXTURE.txt'
        raw_path = 'research/valla/held/EO-FIXTURE.pdf'
        review_path = 'research/readiness/reviews/EO-FIXTURE.json'
        put(source, text_path, text)
        put(source, raw_path, raw)
        put(source, review_path, json.dumps({'result': 'fixture_only', 'sha256': hashlib.sha256(text).hexdigest()}))
        ref = {'instrument_id': 'EO:90001', 'grade': 'compiled_transcription',
               'acceptable_as_original': False, 'complete_text': True,
               'text_path': text_path, 'raw_path': raw_path, 'review_path': review_path,
               'sha256': hashlib.sha256(raw).hexdigest(),
               'text_sha256': hashlib.sha256(text).hexdigest(),
               'url': 'https://example.invalid/fixture', 'page_or_item': 'fixture p. 1',
               'char_start': 0, 'char_end': len(text.decode()), 'quote': text.decode()}
        fragment = {'instrument_id': ref['instrument_id'], 'kind': 'original_representation',
                    'produced_by': 'provider', 'data': dict(ref)}
        put(source, 'jobs/provider/job.py', "print('fixture provider')\n")
        put(source, 'jobs/provider/output/FRAGMENTS.jsonl', json.dumps(fragment) + '\n')
        put(source, 'jobs/provider/output/SOURCES.jsonl', json.dumps({'url': 'https://example.invalid/fixture', 'local_path': raw_path, 'sha256': hashlib.sha256(raw).hexdigest(), 'capture_record': 'jobs/provider/output/CAPTURES.jsonl'}) + '\n')
        put(source, 'jobs/provider/output/CAPTURES.jsonl', json.dumps({'local_path': raw_path, 'sha256': hashlib.sha256(raw).hexdigest(), 'fixture_only': True}) + '\n')
        # Custody capture is intentionally a needs root in this fixture.
        put(source, f'jobs/{NAME}/needs.txt', (source / f'jobs/{NAME}/needs.txt').read_text() + 'jobs/provider/output/CAPTURES.jsonl\n')
        for name in ['source-ladder', 'claim-checker']:
            put(source, f'jobs/{name}/job.py', "print('fixture predecessor')\n")
            put(source, f'jobs/{name}/output/STATUS.json', json.dumps({'result': 'succeeded'}))
        put(source, 'jobs/source-ladder/output/SOURCES.jsonl', json.dumps(ref) + '\n')
        put(source, 'jobs/claim-checker/output/PER_CLAIM.json', json.dumps({'fixture_only': True, 'sources': [ref]}))
        put(source, 'research/readiness/claims/fixture.jsonl', json.dumps({'instrument_id': ref['instrument_id'], 'original_representation': ref}) + '\n')
        put(source, 'research/stage15/CENSUS/fixture.csv', 'instrument_id\nEO-FIXTURE\n')
        put(source, 'jobs/distractor/job.py', "print('unselected')\n")
        put(source, 'jobs/distractor/output/UNRELATED.bin', b'x' * (2 * 1024 * 1024))
        proof.git(source, 'init', '-q')
        proof.git(source, 'config', 'user.name', 'Fixture')
        proof.git(source, 'config', 'user.email', 'fixture@example.invalid')
        proof.git(source, 'add', '.')
        proof.git(source, 'commit', '-qm', 'Production-shaped bounded fixture')
        m = proof.module(source, 'materialize_job_inputs')
        with proof.cwd(source):
            signature = m.narrow_signature(NAME)
        helper = source / '.github/scripts/materialize_job_inputs.py'
        helper.write_text(helper.read_text().replace('NARROW_SIGNATURES = {',
            f'NARROW_SIGNATURES = {{\n    "{NAME}": "{signature}",'))
        proof.git(source, 'add', '.github/scripts/materialize_job_inputs.py')
        proof.git(source, 'commit', '-qm', 'Fixture-only certificate')
        result = proof.run(source, target, fixture_failure=True, scope_label='bounded synthetic production-shape fixture', native_probe=native_consumer_probe)
        result.update({'scope': 'bounded synthetic payloads; actual working-text Index/policy and NORTON source_span reads in both arms',
            'production_source_pin': proof.git(ROOT, 'rev-parse', 'HEAD').decode().strip(),
            'actual_native_code_hashes': pinned_code,
            'fixture_certificate_only': True, 'scientific_job_executed': False,
            'required_reference_shapes': ['provider FRAGMENTS.data -> text_path/raw_path/review_path',
                'provider SOURCES -> local_path and CAPTURES custody', 'claim source_refs',
                'after.txt predecessor generations', 'selected previous successful output']})
        target.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
        print(json.dumps({k: result[k] for k in ['scope', 'old', 'repaired', 'failure_after_prior_success', 'working_changes']}, indent=2))


if __name__ == '__main__':
    target = Path(__file__).with_name('PRODUCTION_SHAPE_FIXTURE.json')
    main(target)

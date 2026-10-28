"""Deterministic v2 -> v3 representation repair; no lifecycle conclusions inferred."""
import copy
import hashlib
import importlib.util
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[4]
BASE = pathlib.Path(__file__).resolve().parent
INPUT = BASE / 'CLAIMS.partial.proposed-v2.jsonl'
OUTPUT = BASE / 'CLAIMS.partial.proposed-v3.jsonl'
EXPECTED_INPUT_SHA = 'c78eca80f0229e82f34f9328154dda5959a408bec78c01e81f6789b52c48cb23'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')

def relative(p):
    return p.relative_to(REPO).as_posix()

def ref(p):
    return {'path': relative(p), 'sha256': sha(p.read_bytes())}

def save(p, obj):
    assert not p.exists(), f'Preserve prior version: {p}'
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

assert sha(INPUT.read_bytes()) == EXPECTED_INPUT_SHA
before = json.loads(INPUT.read_bytes())
after = copy.deepcopy(before)
changes = []

# This source supports only the formal-revocation component of the existing
# open rationale. It does not establish any residual classification.
assert after['savings_residuals']['source'] is None
assert after['savings_residuals']['state'] is None
revocation = [e for e in after['operative_clauses'][0]['later_events'] if e.get('actor') == 'EO:12379']
assert len(revocation) == 1
after['savings_residuals']['source'] = copy.deepcopy(revocation[0]['source'])
changes.append({'pointer': '/savings_residuals/source', 'operation': 'copy_existing_cited_source',
                'copied_from': '/operative_clauses/0/later_events/' + str(after['operative_clauses'][0]['later_events'].index(revocation[0])) + '/source',
                'support_scope': 'EO12379 section12 proves formal revocation of EO11022 as amended. It supports that component of the existing open savings rationale only. No inference of first cessation or final savings classification; source document, existing separate full-order review and supporting statute references retain their existing roles.'})

SOURCE_KEYS = {'original_representation', 'original_source', 'source'}
def fix_source(source, pointer):
    assert isinstance(source, dict), pointer
    raw = (REPO / source['text_path']).read_bytes()
    assert sha(raw) == source['text_sha256'], pointer
    text = raw.decode('utf-8')  # retain stored newline/codepoint offsets
    if all(k in source for k in ('quote', 'char_start', 'char_end')):
        assert text[source['char_start']:source['char_end']] == source['quote'], pointer
        return
    assert not any(k in source for k in ('quote', 'char_start', 'char_end')), pointer
    if pointer == '/original_representation':
        anchor = 'Executive Order 11022\n'
        assert text.count(anchor) == 1
        start = text.index(anchor)
        end = len(text.rstrip())
        assert text[start:end].endswith('[F.R. Doc. 62-4831; Filed, May 15, 1962 ; 3:58 p.m.]')
        for clause in after['operative_clauses']:
            assert clause['original_operative_text'] in text[start:end]
        method = 'Complete original from unique EO11022 heading through the filing line, excluding generated provenance/page metadata.'
        part_spans = []
    else:
        parts = source['quoted_parts']
        assert parts and all(isinstance(p, str) and p for p in parts), pointer
        part_spans = []
        for number, part in enumerate(parts):
            assert text.count(part) == 1, (pointer, number, 'part absent or ambiguous')
            a = text.index(part)
            part_spans.append({'index': number, 'char_start': a, 'char_end': a + len(part), 'part_sha256': sha(part.encode('utf-8'))})
        start = min(p['char_start'] for p in part_spans)
        end = max(p['char_end'] for p in part_spans)
        method = 'Smallest exact contiguous held-text span enclosing all unchanged uniquely located quoted_parts; intervening held text retained verbatim.'
    source.update(quote=text[start:end], char_start=start, char_end=end)
    changes.append({'pointer': pointer, 'operation': 'add_exact_quote_and_offsets',
                    'text_path': source['text_path'], 'text_sha256': source['text_sha256'],
                    'raw_sha256': source['sha256'], 'char_start': start, 'char_end': end,
                    'quote_sha256': sha(source['quote'].encode('utf-8')), 'quoted_part_spans': part_spans, 'method': method})

def walk(value, pointer=''):
    if isinstance(value, dict):
        for key, child in value.items():
            p = pointer + '/' + key.replace('~', '~0').replace('/', '~1')
            if key in SOURCE_KEYS:
                fix_source(child, p)
            else:
                walk(child, p)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            walk(child, pointer + '/' + str(i))
walk(after)

# Prove that undoing only the declared representation additions recovers every
# prior field exactly, including all quoted_parts and all legal gaps.
reverted = copy.deepcopy(after)
def at(obj, pointer):
    for part in pointer.strip('/').split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj
for change in changes:
    if change['operation'] == 'add_exact_quote_and_offsets':
        source = at(reverted, change['pointer'])
        for key in ('quote', 'char_start', 'char_end'):
            del source[key]
reverted['savings_residuals']['source'] = None
assert reverted == before, 'Unexpected substantive/provenance change'
assert after['savings_residuals']['state'] is None
sys.path.insert(0, str(REPO / 'jobs/claim-kit'))
from assemble import check_claim, _gate
expected = json.loads((BASE / 'PROPOSAL-v2.json').read_bytes())['expected_gate_errors']
gates = _gate(REPO).validate_claim(after, expected_status=after['whole_order_status'])
strict = check_claim(after, REPO, None)
assert gates == expected, ('changed gate errors', gates)
assert strict == expected, ('strict errors beyond approved gaps', strict)
assert not OUTPUT.exists()
OUTPUT.write_text(json.dumps(after, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')

report = {'schema': 'astra-b01-source-span-correction/v3', 'script': ref(pathlib.Path(__file__).resolve()),
          'input': ref(INPUT), 'input_claim_sha256': sha(canonical(before)),
          'output': ref(OUTPUT), 'output_claim_sha256': sha(canonical(after)),
          'changes': changes, 'changed_source_objects': len(changes),
          'prior_fields_exactly_recovered_by_removing_declared_additions': reverted == before,
          'existing_quoted_parts_unchanged': True, 'substantive_findings_changed': False,
          'state_and_first_end_fields_changed': False, 'sources_acquired': 0,
          'strict_check_function': 'jobs/claim-kit/assemble.py:check_claim',
          'strict_check_code': ref(REPO / 'jobs/claim-kit/assemble.py'),
          'strict_errors': strict, 'gate_errors': gates, 'non_gate_strict_errors': [],
          'savings_state': after['savings_residuals']['state'],
          'prior_failed_completion': ref(BASE / 'complete-v1/EXCEPTIONS.json'),
          'review': 'No producer legal approval. New exact-v3 independent after-reveal review required.'}
save(BASE / 'SOURCE_SPAN_CORRECTION-v3.json', report)
proposal = json.loads((BASE / 'PROPOSAL-v2.json').read_bytes())
proposal.update(claim_path=relative(OUTPUT), claim_file_sha256=sha(OUTPUT.read_bytes()),
                claim_sha256=sha(canonical(after)), supersedes_for_review='PROPOSAL-v2.json',
                producer_completed_utc=None, producer_completed_note='Claim substantive producer timestamp remains unchanged; v3 is deterministic representation correction. Execution receipt recorded separately.',
                strict_check_receipt=ref(BASE / 'SOURCE_SPAN_CORRECTION-v3.json'))
save(BASE / 'PROPOSAL-v3.json', proposal)
print(json.dumps({'claim': ref(OUTPUT), 'claim_sha256': sha(canonical(after)), 'correction': ref(BASE / 'SOURCE_SPAN_CORRECTION-v3.json'), 'objects_changed': len(changes), 'strict_errors': strict}, indent=2))

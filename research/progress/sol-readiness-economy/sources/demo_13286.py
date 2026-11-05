"""Bounded held-source delivery demonstration; never applies or files claims.

Run from the repository root with an unused output directory:
python3 research/progress/sol-readiness-economy/sources/demo_13286.py \
  --repo . --write research/progress/sol-readiness-economy/sources/native-v1
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time


TARGETS = {'EO:12312': 61, 'EO:12830': 28, 'EO:12985': 20, 'EO:12793': 31}
RAW = ('jobs/astra-source-retention/output/pdf/'
       '0f74e21c46effda67c9a2824675469df809b09a321495030fa551594859554b5.pdf')
ACTOR = 'jobs/claim-kit/output/actor-texts/EO_13286.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')


def section(text, number, following):
    start = list(re.finditer(r'^Sec\. ' + str(number) + r'\.', text, re.M))
    stop = list(re.finditer(r'^Sec\. ' + str(following) + r'\.', text, re.M))
    if len(start) != 1 or len(stop) != 1 or start[0].start() >= stop[0].start():
        raise ValueError('unique ordered section boundaries required: ' + str(number))
    return start[0].start(), stop[0].start()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--write', required=True)
    args = parser.parse_args()
    started = time.monotonic()
    repo = Path(args.repo).resolve()
    dest = Path(args.write).resolve()
    if dest.exists() or not dest.is_relative_to(repo / 'research/progress/sol-readiness-economy/sources'):
        raise ValueError('unused Session A source-artifact destination required')
    cache = tempfile.TemporaryDirectory(prefix='eo-readiness-source-demo-')
    os.environ['CLAIM_KIT_CACHE_DIR'] = cache.name
    sys.path.insert(0, str(repo / 'jobs/claim-kit'))
    import batch as B
    import assemble as A
    import dispatch as D
    import source_supplement as S
    lock_file = repo / 'research/readiness/CLAIM_KIT_LOCK.json'
    if not lock_file.is_file():
        raise ValueError('current reservation file must be explicitly materialized before this demo')
    locks = json.loads(lock_file.read_bytes()).get('orders', {})
    reserved = {iid: locks[iid] for iid in TARGETS if iid in locks}
    if reserved:
        raise ValueError('reserved assignments excluded from demonstration: ' + ', '.join(reserved))
    actor = json.loads((repo / ACTOR).read_bytes())
    source = actor['source']
    if actor['instrument_id'] != 'EO:13286':
        raise ValueError('wrong held actor identity')
    text_path = repo / source['text_path']
    if sha(repo / RAW) != source['sha256'] or sha(text_path) != source['text_sha256']:
        raise ValueError('held EO13286 original or extract hash mismatch')
    text = text_path.read_bytes().decode('utf-8')
    dossier_paths = {iid: repo / 'jobs/claim-kit/output/dossiers' / (B.filename(iid) + '.json') for iid in TARGETS}
    for iid, path in dossier_paths.items():
        dossier = json.loads(path.read_bytes())
        if dossier.get('fingerprint') != B.canonical_sha(dossier):
            raise ValueError('changed retained dossier: ' + iid)
        ref = dossier['evidence'][dossier['original_source_id']]['source']
        if sha(repo / ref['text_path']) != ref['text_sha256']:
            raise ValueError('required original text does not match retained dossier: ' + iid)
    entries = []
    applicability = {}
    for iid, number in TARGETS.items():
        start, end = section(text, number, number + 1)
        page = list(re.finditer(r'^=== PDF page (\d+) of 15 ===', text[:start], re.M))
        page_label = page[-1].group(1) if page else '1'
        inherited = ' indirect parent EO11448; application to EO12312 remains unresolved' if iid == 'EO:12312' else ''
        reason = ('Held EO13286 section ' + str(number) + inherited
                  + '; examine amendment scope, earlier endings and surviving commands independently.')
        entries.append({'alias': 'EO13286-section-' + str(number), 'instrument_ids': [iid],
                        'actor_id': 'EO:13286', 'reason': reason,
                        'source': {k: source[k] for k in ('url', 'sha256', 'text_path', 'text_sha256')}
                                  | {'local_path': RAW, 'page_or_item': 'EO13286 section ' + str(number) + ', PDF page ' + page_label},
                        'char_start': start, 'char_end': end})
        applicability[iid] = {'selected_section': number, 'reason': reason,
                              'legal_application': 'unreviewed',
                              'current_law_and_other_amendment_coverage': 'unresolved',
                              'original_replacement_and_quotation_obligations': 'retained'}
    savings_start, _ = section(text, 89, 90)
    signature = text.find('\nW\nTHE WHITE HOUSE,', savings_start)
    if signature < 0:
        raise ValueError('EO13286 savings/effective-date ending boundary not found')
    entries.append({'alias': 'EO13286-savings-effective', 'instrument_ids': list(TARGETS),
                    'actor_id': 'EO:13286',
                    'reason': 'Common EO13286 sections 89-93 context only; independently examine savings, preserved authority and effective date for every target.',
                    'source': {k: source[k] for k in ('url', 'sha256', 'text_path', 'text_sha256')}
                              | {'local_path': RAW, 'page_or_item': 'EO13286 sections 89-93, PDF pages 14-15'},
                    'char_start': savings_start, 'char_end': signature})
    declaration_path = dest / 'SOURCE_DECLARATIONS.json'
    dump(declaration_path, {'schema': S.SCHEMA, 'sources': entries})
    agent = 'sol-readiness-economy-source-delivery-demo'
    parent = dest / 'parent'
    supplemented = dest / 'supplemented'
    # This uses native ownership/reservation checks and retains all unresolved
    # member decisions. It cannot publish or adopt a replacement proposal.
    parent_metrics = B.prepare(repo, repo / 'jobs/claim-kit/output', parent,
                               list(TARGETS), agent, dossier_paths=dossier_paths,
                               replacement_proposal=True)
    prepare_receipt = S.prepare(repo, parent, declaration_path, agent, supplemented)
    verify_receipt = S.verify(repo, supplemented)
    packet, dossiers = B.load_packet(supplemented, repo)
    views = B.views(repo, supplemented, list(TARGETS))
    dump(dest / 'MEMBER_VIEWS.json', views)
    dispatch = D.check(repo, supplemented)
    dump(dest / 'FINAL_DISPATCH.json', dispatch)
    probe_arms = {'delivered_official_excerpts': [], 'inherited_mirror_excerpt': []}
    for iid, dossier in dossiers.items():
        records = A._records(dossier)
        for arm, selected_ids in [
                ('delivered_official_excerpts', [eid for eid in records if eid.startswith('SUPPLEMENT:')]),
                ('inherited_mirror_excerpt', ['ACT:' + iid + '>EO:13286'])]:
            errors = []
            refs = [A._reference(eid, records, errors) for eid in selected_ids]
            if errors:
                raise ValueError('cannot construct exact source-selection probe: ' + repr(errors))
            probe_arms[arm].append({'schema': 'eo-engineering-source-selection-probe/v1',
                                    'instrument_id': iid,
                                    'claim_kit': {'dossier_sha256': dossier['fingerprint']},
                                    'sources': refs,
                                    'notice': 'ENGINEERING source-selection probe only; not an assembled claim, legal finding or review.'})
    selected_receipts = {}
    selected_results = {}
    for arm, probes in probe_arms.items():
        result = D.check_selected(repo, supplemented, probes)
        selected_results[arm] = result
        selected_receipts[arm] = D.selected_summary(result)
    # Both arms run against the same pre-write context. These are engineering
    # probes, not filed claims or new selected-version research assertions.
    dump(supplemented / 'ENGINEERING_SOURCE_PROBES.json', {
        'schema': 'eo-readiness-source-selection-engineering-probes/v1',
        'not_assembled_claims': True, 'legal_approval': False, 'arms': probe_arms})
    for arm, result in selected_results.items():
        # Keep source diagnostics inside the packet's own work and do not label
        # them as selected-version manifests for later prior-research discovery.
        dump(supplemented / ('ENGINEERING_GUARD_' + arm.upper() + '.json'), result)
    delivered = {}
    for iid, dossier in dossiers.items():
        rows = {eid: e for eid, e in dossier['evidence'].items() if eid.startswith('SUPPLEMENT:')}
        for eid, evidence in rows.items():
            if evidence['source']['sha256'] != source['sha256']:
                raise ValueError('selected official raw source was replaced: ' + iid + '/' + eid)
            if text[evidence['char_start']:evidence['char_end']] != evidence['text']:
                raise ValueError('delivered source span changed: ' + iid + '/' + eid)
            if eid not in views[iid]:
                raise ValueError('native member view omitted supplemental evidence: ' + iid + '/' + eid)
        delivered[iid] = {'evidence_ids': sorted(rows),
                          'source_sha256': sorted({e['source']['sha256'] for e in rows.values()}),
                          'source_custody': [r for m in dispatch['members'] if m['instrument_id'] == iid
                                              for r in m['sources'] if r['evidence_id'] in rows],
                          **applicability[iid]}
    receipt = {'schema': 'eo-readiness-economy-held-source-demo/v1',
               'targets': list(TARGETS), 'unique_raw_sources': 1,
               'native_parent_prepare': parent_metrics,
               'native_supplement_prepare': prepare_receipt,
               'native_supplement_verify': verify_receipt,
               'delivered': delivered,
               'native_final_dispatch': D.summary(dispatch),
               'engineering_source_selection_only': selected_receipts,
               'pins': {rel: sha(repo / rel) for rel in [RAW, source['text_path'], ACTOR,
                    'research/readiness/CLAIM_KIT_LOCK.json',
                    'jobs/claim-kit/batch.py', 'jobs/claim-kit/dispatch.py',
                    'jobs/claim-kit/source_supplement.py', 'jobs/claim-kit/current_evidence.py']},
               'packet_sha256': sha(supplemented / 'PACKET.json'),
               'declarations_sha256': sha(declaration_path),
               'demonstration_script': {'path': Path(__file__).resolve().relative_to(repo).as_posix(),
                                        'sha256': sha(Path(__file__).resolve())},
               'dossier_input_pins': {iid: sha(path) for iid, path in dossier_paths.items()},
               'wall_seconds': time.monotonic() - started,
               'cache_isolation': 'Unique temporary directory for this process; never a shared production cache.',
               'model_tokens': None, 'cash': None, 'network_requests': 0,
               'legal_approval': False, 'human_certification': False,
               'new_ready_dossiers_claimed': 0,
               'limitations': ['Source delivery and exact spans only; per-target legal application remains unreviewed.',
                              'EO12312 link is indirect through EO11448 and not established by supplement preparation.',
                              'Sparse materialized prior-work coverage is explicit in the native packet; unmaterialized work is not inferred absent.',
                              'Optional source gaps and original-replacement/quotation duties remain visible.']}
    dump(dest / 'RECEIPT.json', receipt)
    print(json.dumps({'receipt': str((dest / 'RECEIPT.json').relative_to(repo)),
                      'targets': list(TARGETS), 'unique_raw_sources': 1,
                      'supplement_verify': verify_receipt,
                      'dispatch_state': dispatch['state'],
                      'wall_seconds': receipt['wall_seconds'], 'new_ready_dossiers_claimed': 0}, indent=2))


if __name__ == '__main__':
    main()

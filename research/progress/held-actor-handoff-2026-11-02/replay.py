"""Bounded exact-byte declaration for four Erasmus held-actor packet gaps.

This only prepares an input to source_supplement.py. It neither identifies the
instrument conclusively nor asserts occurrence, effective date or legal effect.
"""
import argparse
import hashlib
import json
from pathlib import Path


ROOT = 'research/excavator/counterexample-first-2026-10-26/packet/producers/EO_8126/'
SOURCES = [
    dict(alias='plo1704-fr1958-p14', instrument_ids=['EO:8129', 'EO:8163'],
         actor_id='PLO:1704',
         reason='Read the held Federal Register column and check the actor, extent and dated effect independently.',
         source=dict(url='https://www.govinfo.gov/content/pkg/FR-1958-08-09/pdf/FR-1958-08-09.pdf',
                     sha256='008e6b7585335a78b228ef1c4657ad75221cad40c82197c7d7be074e75db83e8',
                     local_path='jobs/astra-source-retention/output/pdf/008e6b7585335a78b228ef1c4657ad75221cad40c82197c7d7be074e75db83e8.pdf',
                     text_path=ROOT+'PLO1704-page14-pypdf.txt',
                     text_sha256='d3d6e792a4a4ef94d8328217d641cbb83129c7d1b512c3608ea80608856fd019',
                     page_or_item='23 FR 6110, PDF page 14; unreviewed extraction'),
         char_start=2422, char_end=3889,
         expected_start='[Public Land Order 1704]', expected_end='8 :45 a. m.J\n'),
    dict(alias='proc2416-stat54', instrument_ids=['EO:8163'], actor_id='Proclamation:2416',
         reason='Read the held Statutes at Large pages and check designation, scope and dated effect independently.',
         source=dict(url='https://www.govinfo.gov/content/pkg/STATUTE-54/pdf/STATUTE-54-Pg2717.pdf',
                     sha256='15e01816ebc165ff00f747861704bae240f51f4f7578f1c14f53a942e5fa96de',
                     local_path='jobs/astra-source-retention/output/pdf/15e01816ebc165ff00f747861704bae240f51f4f7578f1c14f53a942e5fa96de.pdf',
                     text_path=ROOT+'Proc2416-full.txt',
                     text_sha256='c6f1f8fbe442b1ef66786277e4d72c5f950577db8c508f0498f29b3a611aa343',
                     page_or_item='54 Stat. 2717–2726; unreviewed extraction'),
         char_start=562, char_end=17226,
         expected_start='[No. 2416]', expected_end='Acting Secretary of State.'),
    dict(alias='eo10804-fr1959', instrument_ids=['EO:9949'], actor_id='EO:10804',
         reason='Read the held later order and check its identity, scope and dated effect independently.',
         source=dict(url='https://www.govinfo.gov/content/pkg/FR-1959-02-14/pdf/FR-1959-02-14.pdf',
                     sha256='f337a3b16522261cc147d92721a7fdea67ee17bfb1d9d155d45667455b09adaa',
                     local_path='jobs/astra-source-retention/output/pdf/f337a3b16522261cc147d92721a7fdea67ee17bfb1d9d155d45667455b09adaa.pdf',
                     text_path='jobs/fr-originals/data/full_run/texts/EO_10804.txt',
                     text_sha256='8e2760ae3954b6e6e8563659cc58fd9fcc4445826e9c0d10106c2e95be9b2ee2',
                     page_or_item='24 FR 1147, PDF page 1; extracted text requires page check'),
         char_start=0, char_end=5765,
         expected_start='Instrument: EO:10804', expected_end=None),
    dict(alias='eo11029-fr1962', instrument_ids=['EO:11026'], actor_id='EO:11029',
         reason='Read the held later order and check its identity, scope and dated effect independently.',
         source=dict(url='https://www.govinfo.gov/content/pkg/FR-1962-06-15/pdf/FR-1962-06-15.pdf',
                     sha256='7dfadd0c42279cf10b8e842c13ebdcd9a860d90b37da0862d2e5b421d33bab1f',
                     local_path='jobs/astra-source-retention/output/pdf/7dfadd0c42279cf10b8e842c13ebdcd9a860d90b37da0862d2e5b421d33bab1f.pdf',
                     text_path='jobs/fr-originals/data/full_run/texts/EO_11029.txt',
                     text_sha256='7f46daae72119e10a9c906f3505bd51966eaa3b5c15876a70fa96cd19cbf62db',
                     page_or_item='27 FR 5699, PDF page 3; extracted text requires page check'),
         char_start=0, char_end=2702,
         expected_start='Instrument: EO:11029', expected_end=None),
]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def declarations(repo):
    ready, blocked = [], []
    for item in SOURCES:
        source = item['source']
        absent = [key for key in ('local_path', 'text_path') if not (repo/source[key]).is_file()]
        if absent:
            blocked.append({'alias': item['alias'], 'instrument_ids': item['instrument_ids'],
                            'missing': absent, 'paths': {key: source[key] for key in absent}})
            continue
        for hash_key, path_key in [('sha256', 'local_path'), ('text_sha256', 'text_path')]:
            if sha(repo/source[path_key]) != source[hash_key]:
                raise ValueError('Changed held source: '+source[path_key])
        text = (repo/source['text_path']).read_bytes().decode('utf-8')
        start, end = item['char_start'], item['char_end']
        excerpt = text[start:end]
        if not excerpt.startswith(item['expected_start']) or not excerpt or (
                item['expected_end'] is not None and not excerpt.endswith(item['expected_end'])):
            raise ValueError('Changed excerpt span: '+item['alias'])
        ready.append({k: item[k] for k in ('alias', 'instrument_ids', 'actor_id', 'reason',
                                           'source', 'char_start', 'char_end')})
    return {'schema': 'eo-source-excerpt-declarations/v1', 'sources': ready}, blocked


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', type=Path, default=Path('.'))
    p.add_argument('--write', type=Path, required=True,
                   help='New JSON declaration path under research/; inspect it before native prepare')
    a = p.parse_args()
    repo, dest = a.repo.resolve(), a.write.resolve()
    if not dest.is_relative_to(repo/'research') or dest.exists():
        p.error('fresh research declaration path required')
    declaration, blocked = declarations(repo)
    if not declaration['sources']:
        raise ValueError('No exact raw and text pair held for these four cases')
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(declaration, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps({'declaration': dest.relative_to(repo).as_posix(),
                      'source_ids': ['SUPPLEMENT:'+x['alias'] for x in declaration['sources']],
                      'blocked': blocked, 'legal_approval': False,
                      'next': 'Inspect the exact sources and use source_supplement.py prepare on a fresh parent packet.'}, indent=2))


if __name__ == '__main__':
    main()

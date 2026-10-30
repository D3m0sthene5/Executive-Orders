#!/usr/bin/env python3
"""Profile retained Cruden without modifying its packet or native source.

The output destination alone is redirected. Native Cruden's load_members still
loads the selected retained packet with its original check_sources=False policy.
Separately attempt default load_packet(check_sources=True); refusal is preserved.
"""
import argparse
import cProfile
import datetime
import hashlib
import importlib.util
import json
import pstats
import sys
import time
import traceback
from pathlib import Path


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def io():
    return {k: int(v) for line in Path('/proc/self/io').read_text().splitlines()
            for k, v in [line.split(': ')]}


def main():
    harness_started = time.perf_counter()
    start_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    ap = argparse.ArgumentParser()
    ap.add_argument('repo', type=Path)
    ap.add_argument('packet', type=Path)
    ap.add_argument('out', type=Path)
    ap.add_argument('--full-validation', action='store_true', help='Attempt the expensive full native gate separately')
    ap.add_argument('--limit-texts', type=int, help='Explicit microprofile only; first N sorted text files')
    ap.add_argument('--cruden-source', type=Path, help='Use an exact retained legacy or repaired module')
    ap.add_argument('--reference', type=Path, help='Compare exact LOOKUPS JSON and Markdown bytes')
    ap.add_argument('--no-profile', action='store_true', help='Unprofiled timing arm; same callable and output')
    args = ap.parse_args()
    repo, packet, out = (p.resolve() for p in (args.repo, args.packet, args.out))
    out.mkdir(parents=True, exist_ok=False)
    source = (args.cruden_source.resolve() if args.cruden_source else
              repo / 'research/excavator/claude-nira-sweep-2026-10-29/cruden.py')
    spec = importlib.util.spec_from_file_location('cruden_profile_target', source)
    cruden = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cruden)
    cruden.REPO = repo  # Exact source snapshots can live outside their original folder.
    sys.path.insert(0, str(repo / 'jobs/claim-kit'))
    import batch
    pins = [source, repo/'jobs/claim-kit/batch.py', packet/'PACKET.json',
            repo/'jobs/domesday-register/output/REGISTER.csv',
            repo/'jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv',
            repo/'jobs/app-executive-orders/output/MIRROR_DOCUMENTS.jsonl',
            repo/'jobs/app-executive-orders/output/DOCUMENTS.jsonl']
    helper = source.parent/'cruden_cache.py'
    if helper.exists():
        pins.append(helper)
    inputs = [{'path': str(p.relative_to(repo)), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in pins]
    texts = list(cruden.held_texts())
    if args.limit_texts is not None:
        texts = texts[:args.limit_texts]
        cruden.held_texts = lambda: iter(texts)
    manifest = [{'path': str(p.relative_to(repo)), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in texts]
    manifest_bytes = (json.dumps(manifest, indent=1)+'\n').encode()
    canonical_manifest = Path(__file__).resolve().parent/'TEXT_MANIFEST.json'
    if not canonical_manifest.exists():
        canonical_manifest.write_bytes(manifest_bytes)
    manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
    summary = {'schema': 'cruden-profile/v1', 'inputs': inputs,
               'start_utc': start_utc,
               'microprofile_limit': args.limit_texts,
               'text_manifest_sha256': manifest_digest,
               'canonical_text_manifest': str(canonical_manifest.relative_to(repo)),
               'canonical_manifest_equal': canonical_manifest.read_bytes()==manifest_bytes,
               'profile_enabled': not args.no_profile,
               'text_count': len(texts), 'text_bytes': sum(x['bytes'] for x in manifest),
               'model': 'OpenAI Codex; exact runtime model name not exposed to worker', 'tokens': None,
               'notice': 'Engineering profile only. No legal or readiness determination.'}
    t = time.perf_counter()
    try:
        if args.full_validation:
            batch.load_packet(packet, repo)
            summary['default_packet_validation'] = {'accepted': True}
        else:
            summary['default_packet_validation'] = {'attempted': False}
    except Exception as e:
        summary['default_packet_validation'] = {'accepted': False, 'exception': type(e).__name__, 'error': str(e)}
    summary['default_packet_validation']['wall_seconds'] = time.perf_counter()-t
    (out/'START.json').write_text(json.dumps(summary, indent=2)+'\n')
    summary['setup_seconds'] = time.perf_counter()-harness_started
    print('starting original Cruden callable', flush=True)
    # Redirect ONLY where output is written. Original native loader is called
    # with the real retained packet; no fabricated dossier or validator bypass.
    original_load = cruden.load_members
    cruden.load_members = lambda unused_output_dir: original_load(packet)
    if hasattr(cruden, 'input_manifest'):
        original_input_manifest = cruden.input_manifest
        cruden.input_manifest = lambda unused_output_dir: original_input_manifest(packet)
    profile = cProfile.Profile()
    before = io()
    t = time.perf_counter()
    try:
        if args.no_profile:
            cruden.lookups(out)
        else:
            profile.runcall(cruden.lookups, out)
        summary['cruden'] = {'completed': True}
    except Exception as e:
        summary['cruden'] = {'completed': False, 'exception': type(e).__name__, 'error': str(e), 'traceback': traceback.format_exc()}
    summary['cruden']['wall_seconds'] = time.perf_counter()-t
    summary['cruden']['io_delta'] = {k: v-before[k] for k,v in io().items()}
    if hasattr(cruden, 'LAST_DETAILS') and cruden.LAST_DETAILS:
        details = cruden.LAST_DETAILS
        summary['implementation_details'] = {k: v for k,v in details.items() if k not in ('members','own_and_page_texts')}
        summary['implementation_details']['corpus'] = {k:v for k,v in details['corpus'].items() if k!='sources'}
        cache_path = Path(details['corpus']['cache_path'])
        summary['cache_bytes'] = cache_path.stat().st_size if cache_path.exists() else None
    if not args.no_profile:
        profile.dump_stats(str(out/'PROFILE.pstats'))
        stats = pstats.Stats(profile)
        stats.sort_stats('tottime')
        with (out/'PROFILE.txt').open('w') as stream:
            stats.stream = stream
            stats.print_stats(35)
    summary['outputs'] = [{'path': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p)}
                          for p in [out/'LOOKUPS.json',out/'LOOKUPS.md',out/'LOOKUPS.details.json'] if p.exists()]
    if args.reference:
        summary['reference_equivalence'] = {name: (args.reference/name).read_bytes()==(out/name).read_bytes()
                                            for name in ('LOOKUPS.json','LOOKUPS.md')}
    if (out/'LOOKUPS.json').exists():
        members = json.loads((out/'LOOKUPS.json').read_text())['members']
        summary['member_count'] = len(members)
        summary['number_citations'] = sum(len(e['number_citations']) for e in members.values())
        summary['code_mentions'] = sum(len(e['code_mentions']) for e in members.values())
        prior = packet/'LOOKUPS.json'
        if prior.exists():
            summary['retained_lookup_sha256'] = sha(prior)
            summary['equal_retained_lookup_bytes'] = prior.read_bytes()==(out/'LOOKUPS.json').read_bytes()
    summary['harness_wall_seconds'] = time.perf_counter()-harness_started
    summary['end_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (out/'RESULT.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('inputs','outputs','implementation_details')}, indent=2))


if __name__ == '__main__':
    main()

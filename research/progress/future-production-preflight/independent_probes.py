#!/usr/bin/env python3
"""Reconstructed replay of seven independent dispatch-review probes.

The original probes ran from an inline Python command. This reusable script was
subsequently reconstructed from that command and rerun; it is not represented as
the historical execution file. All mutable corpus inputs are temporary native
integration fixtures. Only the requested --output review receipt is persisted.

Usage: python3 -B eo-dispatch-independent-probes.py --repo /path/to/checkout
ROOT may supply the checkout when --repo is omitted.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=os.environ.get('ROOT'))
    parser.add_argument('--output', type=Path,
                        default=Path('/tmp/eo-dispatch-independent-replay.json'))
    args = parser.parse_args()
    if args.repo is None:
        parser.error('--repo or ROOT is required')
    repo = args.repo.resolve()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(repo / 'jobs/claim-kit'))
    import test_dispatch as T
    import dispatch
    import batch

    started = time.monotonic()
    checks = []

    def passed(name):
        checks.append({'name': name, 'passed': True})

    fixture = T.DispatchTests()
    fixture.setUp()
    try:
        folder = fixture.packet(missing=('EO:1',))
        try:
            dispatch.check(fixture.repo, folder, ['EO:2', 'EO:2'])
        except ValueError as exc:
            assert 'distinct' in str(exc)
        else:
            raise AssertionError('duplicate selection accepted')
        passed('duplicate_member_selection_refused')

        packet_path = folder / 'PACKET.json'
        original = packet_path.read_bytes()
        doc = json.loads(original)
        doc.pop('fingerprint')
        doc['dossiers']['EO:2']['original_source_id'] = None
        doc['fingerprint'] = batch.digest(batch.canon(doc).encode())
        batch.dump(packet_path, doc)
        try:
            try:
                dispatch.check(fixture.repo, folder, ['EO:2'])
            except ValueError as exc:
                assert 'dossier fingerprint mismatch' in str(exc)
            else:
                raise AssertionError('rehashed packet hid changed dossier')
        finally:
            packet_path.write_bytes(original)
        passed('rehashed_packet_cannot_hide_changed_dossier')

        nested = folder / 'escape'
        nested.symlink_to(fixture.repo, target_is_directory=True)
        assert fixture.cli('dispatch-check', folder, '--write', nested / 'receipt.json')[0] == 2
        assert not (fixture.repo / 'receipt.json').exists()
        passed('symlink_receipt_escape_refused')

        rule = fixture.repo / 'research/readiness/owner_rulings/selected-other.md'
        rule.parent.mkdir(parents=True, exist_ok=True)
        rule.write_text('# EO:1\nNew relevant source examination required.\n')
        try:
            try:
                dispatch.check(fixture.repo, folder, ['EO:2'])
            except ValueError as exc:
                assert 'changed prior research' in str(exc)
            else:
                raise AssertionError('subset bypassed whole seal')
        finally:
            rule.unlink()
        passed('subset_does_not_bypass_whole_packet_freshness')
    finally:
        fixture.doCleanups()

    fixture = T.DispatchTests()
    fixture.setUp()
    try:
        import urllib.request
        fixture.retain()
        fixture.run_build()
        folder = fixture.repo / 'research/network-probe/packet'
        with patch.object(urllib.request, 'urlopen', side_effect=AssertionError('network request')):
            result = batch.prepare(fixture.repo, fixture.out, folder, ['EO:1', 'EO:2'], 'producer')
            assert result['dispatch_check']['ok']
        passed('ordinary_prepare_does_not_open_network')

        def snapshot():
            return {str(p.relative_to(fixture.repo)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in fixture.repo.rglob('*') if p.is_file()}

        before = snapshot()
        result = dispatch.check(fixture.repo, folder, ['EO:1'])
        assert before == snapshot()
        assert result['checked_ids'] == ['EO:1']
        assert not result['scientific_approval']
        passed('selected_member_check_read_only_and_no_approval')

        checker = dispatch.actual_checker()
        ref = {'url': 'https://www.govinfo.gov/custody-probe.pdf', 'sha256': 'a' * 64}
        index = checker.S.HeldIndex()
        index.add(checker.S.HeldCopy('fixture', 'a' * 64,
                                    url=ref['url'], custody='record_only'))
        context = SimpleNamespace(index=index, reader=checker.S.TextReader(),
                                  gpo_matched={}, cache_dir=None, archive_captures={})
        checker._VERIFY['left'] = 400
        rows = []
        with patch.object(checker, 'verify_by_download', side_effect=AssertionError('live fallback')), \
             patch.object(checker, 'verify_by_archive', side_effect=AssertionError('archive fallback')):
            checker.check_source(ref, 'source', context, rows, allow_download=False)
        assert rows[0]['status'] == 'custody_record_only'
        passed('offline_custody_never_enters_live_or_archive_fallback')
    finally:
        fixture.doCleanups()

    paths = ['jobs/claim-kit/dispatch.py', 'jobs/claim-kit/batch.py',
             'jobs/claim-kit/kit.py', 'jobs/claim-kit/test_dispatch.py',
             'jobs/claim-checker/checker.py']
    report = {
        'schema': 'eo-independent-engineering-review/v1',
        'execution_kind': 'newly_reconstructed_replay',
        'reviewer': 'dispatch_audit', 'model_family': 'OpenAI',
        'model': 'inherited; exact identifier unavailable',
        'input_sha256': {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in paths},
        'checks': checks, 'probes_passed': len(checks), 'findings': [],
        'verdict': 'approve', 'wall_seconds': round(time.monotonic() - started, 6),
        'model_tokens': None,
        'limitations': [
            'Reconstructed replay; the historical original ran from an inline Python command.',
            'Synthetic real-native integration fixtures; no claim that the current corpus is complete or production-ready.',
            'Whole-corpus custody-index overhead not benchmarked.',
            'Receipt is a point-in-time check; rerun immediately before dispatch.',
            'No different-model-family scientific review or legal judgment performed.',
        ],
    }
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'probes_passed': len(checks), 'wall_seconds': report['wall_seconds'],
                      'report': str(args.output), 'verdict': report['verdict'],
                      'execution_kind': report['execution_kind']}))


if __name__ == '__main__':
    main()

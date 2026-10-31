"""Connect explicit ordinary completion history to the existing NEYMAN importer.

Run after normal production; no research dispatch, source fetch, canonical write
or savings calculation. The supplied history is never claimed to be exhaustive.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

from production_receipts import Reader, import_production, require, tally


def build(repo, history, finals, base_commit, dest, research_attempts=(), effort_receipts=(),
          current=None, checkpoints=(), questions=()):
    reader = Reader(repo)
    require(re.fullmatch(r'[0-9a-f]{40}', base_commit), 'exact production base commit required')
    dest = reader.path(dest)
    allowed = reader.root / 'research/neyman/production-diagnostics'
    require(dest.is_relative_to(allowed) and dest != allowed and not dest.exists(),
            'fresh NEYMAN production-diagnostic destination required')
    finals = list(dict.fromkeys(finals))
    require(len(finals) <= 20 and len(research_attempts) <= 100 and len(effort_receipts) <= 100,
            'bounded completion/attempt/effort selection required')
    require(len(checkpoints) <= 100 and len(questions) <= 100, 'bounded diagnostic context required')
    history_ref = reader.ref(history)
    index = reader.value(history_ref)
    invocations = index.get('invocations')
    require(isinstance(invocations, list) and 1 <= len(invocations) <= 200,
            'explicit nonempty completion history required (at most 200)')
    refs = [{'path': r['path'], 'sha256': r['sha256']} for r in invocations]
    if current is not None:
        current = reader.path(current).relative_to(reader.root).as_posix()
        refs.append(reader.ref(current + '/TALLY.json'))
    require(len(refs) <= 200, 'at most 200 supplied/current completion receipts required')
    attempts = [tally(reader, ref) for ref in refs]
    history_hashes = {a['receipt']['sha256'] for a in attempts}
    observed = {r['instrument_id'] for a in attempts for r in a['outcomes']}
    selection = {}
    for folder in finals:
        folder = reader.path(folder).relative_to(reader.root).as_posix()
        final_ref = reader.ref(folder + '/TALLY.json')
        require(final_ref['sha256'] in history_hashes, 'final completion absent from explicit history')
        final = tally(reader, final_ref)
        for row in final['outcomes']:
            if row['outcome'] != 'eligible':
                continue
            iid = row['instrument_id']
            require(iid not in selection, 'multiple final selections for ' + iid)
            selection[iid] = {'instrument_id': iid, 'claim_sha256': row['claim_sha256'],
                              'publication_kind': row['publication_kind'], 'completion': folder}
    research_refs = [reader.ref(path) for path in research_attempts]
    for ref in research_refs:
        attempt = reader.value(ref)
        require(attempt.get('schema') == 'neyman.research-attempt/1', 'existing research-attempt receipt required')
        iid = attempt['instrument_id']
        selection.setdefault(iid, {'instrument_id': iid})
    missing = sorted(observed - set(selection))
    require(not missing, 'unfinished members need explicit research-attempt receipts; refusing to drop: ' + ', '.join(missing))
    require(selection, 'no selected production members')
    effort_refs = [reader.ref(path) for path in effort_receipts]
    checkpoint_refs = [reader.ref(path) for path in checkpoints]
    question_refs = [reader.ref(path) for path in questions]
    # Preserve the input versions read while deriving the selection.
    for path, digest in list(reader.pins.items()):
        reader.raw({'path': path, 'sha256': digest})
    dest.mkdir(parents=True, exist_ok=False)
    supplied_history = history_ref
    if current is not None:
        # The ordinary invocation's receipt only exists after completion. Keep
        # the supplied index intact, then append that exact receipt explicitly.
        combined = dest / 'COMPLETION_HISTORY.json'
        combined.write_text(json.dumps({'invocations': refs, 'supplied_history': history_ref}, indent=2) + '\n')
        history_ref = reader.ref(combined.relative_to(reader.root).as_posix())
    selected = dest / 'SELECTION.json'
    selected.write_text(json.dumps([selection[i] for i in sorted(selection)], indent=2) + '\n', encoding='utf-8')
    manifest = {'schema': 'neyman.production-import/1', 'base_commit': base_commit,
                'cohort_kind': 'ordinary_production',
                'selection': reader.ref(selected.relative_to(reader.root).as_posix()),
                'completion_index': history_ref, 'research_attempts': research_refs,
                'effort_receipts': effort_refs,
                'checkpoints': checkpoint_refs, 'questions': question_refs,
                'supplied_history': supplied_history,
                'history_coverage': 'Only explicitly supplied invocations; missing sessions are not zero-cost or absent.'}
    path = dest / 'IMPORT.json'
    path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    try:
        imported = import_production(reader, manifest)
    except (ValueError, KeyError, IndexError, TypeError, OSError) as exc:
        (dest / 'REFUSED.json').write_text(json.dumps({'error': str(exc), 'diagnosis_published': False}, indent=2) + '\n')
        raise
    receipt = {'schema': 'neyman.after-completion/1', 'input_pins': dict(sorted(reader.pins.items())),
               'observed_orders': len(imported['observations']),
               'unique_completion_invocations': len(imported['attempts']),
               'duplicate_receipt_aliases': len(imported['duplicate_receipt_aliases']),
               'total_agent_hours': None, 'net_savings': None, 'canonical_outputs_modified': False,
               'history_coverage': manifest['history_coverage']}
    (dest / 'HANDOFF.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    return path, imported


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', default='.')
    p.add_argument('--history', required=True, help='existing COMPLETION_COSTS.json with pinned invocations')
    p.add_argument('--final', action='append', default=[], help='final completion folder; repeat for multiple batches')
    p.add_argument('--research-attempt', action='append', default=[])
    p.add_argument('--effort', action='append', default=[])
    p.add_argument('--current', help='explicit just-finished completion folder to append to supplied history')
    p.add_argument('--checkpoint', action='append', default=[], help='existing source-blocked checkpoint')
    p.add_argument('--question', action='append', default=[], help='existing discriminating-question record')
    p.add_argument('--base-commit', required=True)
    p.add_argument('--write', required=True, help='new research/neyman/production-diagnostics run folder')
    a = p.parse_args(argv)
    try:
        path, _ = build(a.repo, a.history, a.final, a.base_commit, a.write, a.research_attempt, a.effort,
                        a.current, a.checkpoint, a.question)
        # Existing diagnostic implementation owns all interpretation, report and cost rules.
        import diagnose
        repo = Path(a.repo).resolve()
        return diagnose.main(['--repo', str(repo), '--manifest', path.relative_to(repo).as_posix(),
                              '--out', str(path.parent / 'diagnosis')])
    except (ValueError, KeyError, IndexError, TypeError, OSError) as exc:
        print('completion handoff refused: ' + str(exc))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

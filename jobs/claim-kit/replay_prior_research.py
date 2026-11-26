"""Replay prior-research staleness for prepared packets under the scoped-pin rules.

Owner decision D-20261125-scoped-ruling-pins: an owner-ruling file binds only the orders it
names (plus rulings marked global and the grandfathered files), and a finished batch's
completion receipts/ copies no longer bind. This read-only script recomputes each packet's
prior research with the current prior_research.py ("new rules") and with the version at a
baseline Git ref ("old rules"), and reports whether the packet would be stale.

Two modes, chosen per packet:
  exact          PACKET.json is present: compare collect() with the stored prior_research
                 exactly as batch.load_packet does, and list the pins that differ.
  reconstructed  PACKET.json was removed (it is never committed): take the preparation time
                 from PREPARE.json's mtime and the time the packet went stale from the next
                 sibling packet's PREPARE.json (the re-preparation; "now" if none), and list
                 every file each rule set binds that was last written inside that window with
                 bytes different from the last commit before preparation. A third rule set,
                 new_rules_in_force, grandfathers only the rulings already present at
                 preparation, as if the new rules had been in force then. Limits: a file bound at
                 preparation and deleted since, or rewritten again after the window, is not seen.

Usage: python3 replay_prior_research.py [--repo DIR] [--baseline-ref REF] [--json OUT] PACKET...
Nothing is written except the optional --json report.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import prior_research as new_rules  # noqa: E402


def git(repo, *args, data=None):
    return subprocess.run(['git', '-c', 'gc.auto=0', '-C', str(repo), *args], input=data,
                          capture_output=True, check=True).stdout


def load_baseline(repo, ref):
    """Import prior_research.py as it stands at `ref` (old rules) from a temporary file."""
    raw = git(repo, 'show', ref + ':jobs/claim-kit/prior_research.py')
    handle = tempfile.NamedTemporaryFile('wb', suffix='_prior_research_baseline.py', delete=False)
    handle.write(raw)
    handle.close()
    spec = importlib.util.spec_from_file_location('prior_research_baseline', handle.name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    os.unlink(handle.name)
    return module


def members(folder):
    """(dossiers, stored prior_research or None) for one packet folder."""
    packet_path = folder / 'PACKET.json'
    if packet_path.is_file():
        import batch
        packet = json.loads(packet_path.read_bytes())
        return batch.decode(packet), packet.get('prior_research')
    for name, key in (('ADMISSION.json', 'instrument_ids'), ('DISPATCH_CHECK.json', 'packet_members')):
        if (folder / name).is_file():
            ids = json.loads((folder / name).read_bytes()).get(key) or []
            if ids:
                # Pins and ruling scope depend only on the ids; clause alignment is not replayed.
                return {iid: {'instrument_id': iid} for iid in ids}, None
    raise ValueError('no PACKET.json, ADMISSION.json or DISPATCH_CHECK.json member list: %s' % folder)


def bound_files(context):
    files = dict(context['input_file_pins'])
    for ruling in context.get('current_rulings', []):
        files.setdefault(ruling['path'], ruling.get('sha256'))
    return files


def category(repo, rel, cache):
    if rel.startswith(new_rules.RULING_DIR + '/'):
        return 'owner_ruling'
    parts = rel.split('/')
    for n, part in enumerate(parts[:-1]):
        if part == new_rules.RECEIPTS and new_rules.is_completion_folder(str(repo.joinpath(*parts[:n])), cache):
            return 'completion_receipt'
    return 'other'


def changed_since(repo, rels, prepared_at, until, commit):
    """Bound files last written in (prepared_at, until] whose bytes differ from `commit` (or are new)."""
    late = sorted(rel for rel in rels if (repo / rel).is_file()
                  and prepared_at < (repo / rel).stat().st_mtime <= until)
    if not late:
        return []
    then = git(repo, 'cat-file', '--batch-check=%(objectname)',
               data=''.join(commit + ':' + rel + '\n' for rel in late).encode()).decode().splitlines()
    now = git(repo, 'hash-object', '--stdin-paths', data=''.join(rel + '\n' for rel in late).encode()).decode().split()
    return [rel for rel, old, new in zip(late, then, now) if old.split()[0] != new]


def successor_time(folder, prepared_at):
    """PREPARE.json mtime of the earliest sibling packet prepared after this one, else None."""
    later = []
    for sibling in folder.parent.iterdir():
        marker = sibling / 'PREPARE.json'
        if sibling != folder and marker.is_file() and marker.stat().st_mtime > prepared_at:
            later.append((marker.stat().st_mtime, sibling.name))
    return min(later) if later else None


def collect_with_grandfathered(repo, dossiers, folder, names):
    saved = new_rules.GRANDFATHERED_GLOBAL_RULINGS
    new_rules.GRANDFATHERED_GLOBAL_RULINGS = frozenset(names)
    try:
        return new_rules.collect(repo, dossiers, exclude=folder)
    finally:
        new_rules.GRANDFATHERED_GLOBAL_RULINGS = saved


def replay(repo, folder, baseline):
    folder = folder.resolve()
    rel_folder = folder.relative_to(repo).as_posix()
    dossiers, stored = members(folder)
    cache = {}
    report = {'packet': rel_folder, 'orders': sorted(dossiers)}
    contexts = {}
    if baseline is not None:
        contexts['old_rules'] = baseline.collect(repo, dossiers, exclude=folder)
    contexts['new_rules'] = new_rules.collect(repo, dossiers, exclude=folder)
    if stored is not None:
        report['mode'] = 'exact'
        then = bound_files(stored)
        # Old rules pinned every ruling, so the stored list is exactly the rulings present then.
        present = {r['path'].rsplit('/', 1)[-1] for r in stored.get('current_rulings', [])}
        in_force = sorted(new_rules.GRANDFATHERED_GLOBAL_RULINGS & present)
        report['grandfathered_absent_at_preparation'] = sorted(new_rules.GRANDFATHERED_GLOBAL_RULINGS - present)
        contexts['new_rules_in_force'] = collect_with_grandfathered(repo, dossiers, folder, in_force)
        for name, context in contexts.items():
            now = bound_files(context)
            diff = sorted(rel for rel in set(then) | set(now) if then.get(rel) != now.get(rel))
            report[name] = {'stale': context != stored,
                            'differing_pins': [{'path': rel, 'category': category(repo, rel, cache),
                                                'stored': then.get(rel), 'current': now.get(rel)} for rel in diff]}
        return report
    report['mode'] = 'reconstructed'
    prepared_at = (folder / 'PREPARE.json').stat().st_mtime
    commit = git(repo, 'rev-list', '-1', '--before=@%d' % int(prepared_at), 'HEAD').decode().strip()
    successor = successor_time(folder, prepared_at)
    until = successor[0] if successor else float('inf')
    report.update(prepared_at_epoch=prepared_at, commit_before_preparation=commit,
                  window_end=successor[1] if successor else 'now', window_end_epoch=successor[0] if successor else None)
    present = set(git(repo, 'ls-tree', '--name-only', commit, new_rules.RULING_DIR + '/').decode().split())
    present |= {p.relative_to(repo).as_posix() for p in (repo / new_rules.RULING_DIR).glob('*.md')
                if p.stat().st_mtime <= prepared_at}
    in_force = [n for n in new_rules.GRANDFATHERED_GLOBAL_RULINGS if new_rules.RULING_DIR + '/' + n in present]
    report['grandfathered_absent_at_preparation'] = sorted(set(new_rules.GRANDFATHERED_GLOBAL_RULINGS) - set(in_force))
    contexts['new_rules_in_force'] = collect_with_grandfathered(repo, dossiers, folder, in_force)
    for name, context in contexts.items():
        late = changed_since(repo, bound_files(context), prepared_at, until, commit)
        causes = {}
        for rel in late:
            causes.setdefault(category(repo, rel, cache), []).append(rel)
        report[name] = {'stale': bool(late), 'bound_files': len(bound_files(context)),
                        'changed_after_preparation': causes}
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--repo', default=str(HERE.parents[1]))
    parser.add_argument('--baseline-ref', default='HEAD',
                        help='Git ref whose prior_research.py gives the old rules; "none" to skip')
    parser.add_argument('--json', help='write the full report here')
    parser.add_argument('packets', nargs='+')
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    baseline = None if args.baseline_ref == 'none' else load_baseline(repo, args.baseline_ref)
    reports = []
    for packet in args.packets:
        path = Path(packet)
        report = replay(repo, path if path.is_absolute() else repo / path, baseline)
        reports.append(report)
        line = [report['packet'], report['mode'] + ('' if report['mode'] == 'exact' else ' until ' + report['window_end'])]
        for name in ('old_rules', 'new_rules', 'new_rules_in_force'):
            if name in report:
                item = report[name]
                causes = item.get('changed_after_preparation')
                if causes is None:
                    causes = {}
                    for pin in item['differing_pins']:
                        causes.setdefault(pin['category'], []).append(pin['path'])
                line.append('%s=%s%s' % (name, 'STALE' if item['stale'] else 'fresh',
                                         ''.join(' %s:%d' % (k, len(v)) for k, v in sorted(causes.items()))))
        print(' | '.join(line))
    if args.json:
        Path(args.json).write_text(json.dumps(reports, indent=1, sort_keys=True) + '\n')
    return reports


if __name__ == '__main__':
    main()

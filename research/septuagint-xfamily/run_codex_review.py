#!/usr/bin/env python3
"""Septuagint: run one OpenAI-family (Codex) blind review of a rebuilt, gated Dorotheus claim batch.

The prompt is the original Dorotheus reviewer prompt (prompts/reviewer_original.txt, the committed
research/excavator/dorotheus-sample-2026-11-06/tools/prompts/reviewer.txt) with only these changes: paths for this PC,
`py -I` for `python3 -I`, a Python one-liner for `date -u`, model_family "OpenAI", reviewer id
"septuagint-codex-<batch>-X-2026-11-06", and one appended environment paragraph. Nothing in it names a plant.

Blinding by absence: the reviewer works in <run>/work (its only writable folder). It reads <run>/inputs (the review set
and the frozen PACKET.json, nothing else) and the detached source worktree, which is sparse-checked-out so that
PLANTS.csv, REPORT.md, AFTER_REVEAL files, every BLIND_REVIEW file, every dorotheus-* folder, the ice core folder,
HANDOFF, jobs/mountweazel and research/readiness/claims do not exist in it. `audit` verifies this before launching.

usage:
  py -I run_codex_review.py BATCH --dry-run          print prompt, directory listings, audit and the codex command
  py -I run_codex_review.py BATCH                    build the run folder, launch Codex, validate the output
  py -I run_codex_review.py BATCH --validate-only    re-validate an existing output file
BATCH is a batch whose entry in GATE.json has passed: y01, y02, y03 or y05.
Standard library only.
"""
import argparse, datetime, hashlib, json, os, random, re, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULTS = {
    'private': 'C:/Users/danie/eo-septuagint-private',   # keys, rebuilt packets and plants, copies of the verdicts
    'runs': 'C:/Users/danie/eo-septuagint-review',       # what the reviewer sees: <runs>/<batch>/{inputs,work}; nothing private
    'src': 'C:/Users/danie/eo-wt/enc-septuagint-src',
    'codex': 'C:/Users/danie/AppData/Local/OpenAI/Codex/bin/0ab0e7a8f3779036/codex.exe',
    # the sandbox user cannot see the `py` launcher; Codex's own bundled Python 3.12 is readable by it
    'python': 'C:/Users/danie/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
    'model': 'gpt-6-sol', 'effort': 'medium', 'timeout': 7200,
}
SRC_COMMIT = 'a8dd983983'
ARM = 'X'
YW = 'dorotheus-yesprobe-2026-11-06'
# Paths that must not exist in the source worktree the reviewer can read (relative to it).
ABSENT_IN_SRC = ['research/excavator/dorotheus-sample-2026-11-06', 'research/excavator/' + YW,
                 'research/excavator/claude-icecore-2026-11-05', 'HANDOFF', 'jobs/mountweazel', 'research/readiness/claims',
                 'jobs/_attempts', '.github']
# File names that must not exist anywhere in the reviewer's inputs and work folders.
FORBIDDEN_NAMES = re.compile(r'(PLANTS|REPORT|DISPOSITION|ADOPTION_ROWS|CAUSES|SAMPLE)\.(csv|md|json)$|AFTER_REVEAL|BLIND_REVIEW|'
                             r'CORRECTION_REVIEW|CLAIMS\.proposed|GENUINE_CONTROLS|^decisions\.csv$|^clauses\.csv$|'
                             r'PRODUCER_REPORT|ASSESSMENT\.jsonl|LOOKUPS|KEY\.sealed|^keys$|MANIFEST\.json$', re.I)
REQUIRED = ['review_id', 'instrument_id', 'claim_sha256', 'reviewer', 'model_family', 'independent', 'separate_context',
            'review_kind', 'scope', 'verdict', 'defects', 'evidence_checked', 'reasoning', 'started_utc', 'ended_utc']
UTC = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')


def canon(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def render_prompt(batch, n_claims, run, src, py):
    """Original reviewer.txt, filled as review_prep.py filled it, then the PC changes. Returns (prompt, change_list)."""
    t = (HERE / 'prompts' / 'reviewer_original.txt').read_bytes().decode('utf-8').replace('\r\n', '\n')
    inputs, work = run / 'inputs', run / 'work'
    out = (work / f'BLIND_REVIEW_{ARM}.jsonl').as_posix()
    changes = []

    def sub(old, new, why):
        nonlocal t
        if old not in t:
            raise SystemExit(f'prompt template changed: {old!r} not found')
        t = t.replace(old, new)
        changes.append(why)
    # same fill order as review_prep.py
    sub('PACKETDIR/reviews/BLIND_REVIEW_ARM.jsonl', out, 'output path')
    sub('SETPATH', (inputs / 'REVIEW_SET.jsonl').as_posix(), 'review set path')
    sub('PACKETDIR', (inputs / 'packet').as_posix(), 'packet folder')
    sub('NCLAIMS', str(n_claims), 'claim count')
    sub('UNDECIDEDNOTE', '', 'no undecided note (decided packets)')
    sub('SCRATCH', (work / 'scratch').as_posix(), 'scratch folder')
    # reviewer identity (original: "dorotheus-blind-reviewer-BATCH-ARM-2026-11-06", model_family "Anthropic")
    sub('"dorotheus-blind-reviewer-BATCH-ARM-2026-11-06"', f'"septuagint-codex-{batch}-{ARM}-2026-11-06"', 'reviewer id')
    sub('model_family "Anthropic"', 'model_family "OpenAI"', 'model family')
    t = t.replace('BATCH', batch).replace('ARM', ARM)
    # paths and commands for this PC
    sub('/home/user/Executive-Orders', src.as_posix(), 'repository path')
    sub('python3 -I', f'{py} -I', 'python launcher')
    sub('`date -u +%FT%TZ`', f'`{py} -c "import datetime;print(datetime.datetime.now(datetime.timezone.utc).strftime(\'%Y-%m-%dT%H:%M:%SZ\'))"`',
        'timestamp command')
    t = t.rstrip('\n') + (
        f'\n\nEnvironment (this PC, not part of the method): Windows 11, PowerShell. The `py` launcher is not on your PATH; Python 3.12 is {py} '
        f'(use it as written above). Run it from the repository root {src.as_posix()} with PYTHONUTF8=1; `-I` does not put the script folder on sys.path, so a script that imports claim-kit '
        'modules must first insert the jobs/claim-kit folder into sys.path. The repository is read-only for you. Your working folder is '
        f'{work.as_posix()}; the only places you may write are {out} and the folder {(work / "scratch").as_posix()}. Where this prompt says '
        'PACKET.json, the file is ' + (inputs / 'packet' / 'PACKET.json').as_posix() + '.\n')
    changes.append('appended environment paragraph')
    return t, changes


def build_run(batch, a):
    priv, src = Path(a.private), Path(a.src)
    run = Path(a.runs) / batch
    base = priv / 'E' / 'review' / batch / 'REVIEW_SET.jsonl'
    packet = priv / 'rebuilt' / YW / batch / 'packet' / 'PACKET.json'
    for p in (base, packet):
        if not p.is_file():
            raise SystemExit(f'missing rebuilt input {p}')
    gate = json.loads((HERE / 'GATE.json').read_text(encoding='utf-8'))
    if not gate['batches'].get(batch, {}).get('passed'):
        raise SystemExit(f'batch {batch} has not passed the gate')
    claims = [json.loads(l) for l in base.read_text(encoding='utf-8').splitlines() if l.strip()]
    expect = gate['batches'][batch]['rebuilt_claims']
    if sorted(canon(c) for c in claims) != sorted(expect):
        raise SystemExit('rebuilt review set differs from GATE.json hashes; refusing to run')
    if sha_file(packet) != gate['batches'][batch]['packet_sha256_original']:
        raise SystemExit('PACKET.json differs from the original packet_sha256; refusing to run')
    if run.exists():
        if (run / 'work' / f'BLIND_REVIEW_{ARM}.jsonl').exists() and not a.dry_run and not a.force:
            raise SystemExit(f'{run} already has an output; use --force to move it aside')
        if not a.dry_run:
            shutil.move(str(run), str(run) + '.old-' + now().replace(':', ''))
    if not run.exists():
        (run / 'inputs' / 'packet').mkdir(parents=True)
        (run / 'work' / 'scratch').mkdir(parents=True)
        rows = list(claims)
        random.Random(f'dorotheus-{batch}-{ARM}').shuffle(rows)
        (run / 'inputs' / 'REVIEW_SET.jsonl').write_bytes(
            ''.join(json.dumps(c, ensure_ascii=False) + '\n' for c in rows).encode('utf-8'))
        shutil.copyfile(packet, run / 'inputs' / 'packet' / 'PACKET.json')
    return run, len(claims), [c['instrument_id'] for c in claims]


def audit(run, src):
    """Blinding by absence. Returns a list of problems (empty when clean)."""
    bad = []
    head = subprocess.run(['git', '-C', str(src), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    if not head.startswith(SRC_COMMIT):
        bad.append(f'source worktree HEAD {head[:10]} is not {SRC_COMMIT}')
    for rel in ABSENT_IN_SRC:
        if (src / rel).exists():
            bad.append(f'present in source worktree: {rel}')
    exc = src / 'research' / 'excavator'
    allowed = {'claude-nira-sweep-2026-10-29', 'claude-production-2026-10-28'}
    if exc.exists():
        for p in exc.iterdir():
            if p.name not in allowed:
                bad.append(f'unexpected research/excavator/{p.name}')
    for root in (run / 'inputs', run / 'work'):
        for dp, dn, fn in os.walk(root):
            for n in dn + fn:
                if FORBIDDEN_NAMES.search(n) and n != f'BLIND_REVIEW_{ARM}.jsonl':
                    bad.append(f'forbidden name {Path(dp, n)}')
    names = sorted(p.name for p in (run / 'inputs').rglob('*') if p.is_file())
    if names != ['PACKET.json', 'REVIEW_SET.jsonl']:
        bad.append(f'inputs hold {names}')
    return bad


def listing(run, src):
    lines = ['--- what the reviewer can read and write ---']
    for root in (run / 'inputs', run / 'work'):
        for p in sorted(root.rglob('*')):
            lines.append(('  dir  ' if p.is_dir() else f'  {p.stat().st_size:>9,} ') + p.relative_to(run).as_posix())
    lines.append(f'--- repository (read-only), top level of {src.as_posix()} ---')
    for p in sorted(src.iterdir()):
        if p.name != '.git':
            lines.append('  ' + p.name + ('/' if p.is_dir() else ''))
    jobs = sum(1 for p in (src / 'jobs').iterdir() if p.is_dir())
    exc = sorted(p.name for p in (src / 'research' / 'excavator').iterdir())
    lines.append(f'  jobs/: {jobs} job folders (no jobs/_attempts, no jobs/mountweazel); research/excavator/: {exc}')
    lines.append('  research/readiness/: ' + ', '.join(sorted(p.name for p in (src / 'research' / 'readiness').iterdir())))
    return '\n'.join(lines)


def codex_cmd(a, work, last):
    c = [a.codex, 'exec', '--skip-git-repo-check', '--ignore-user-config', '-s', 'workspace-write', '--json', '--ephemeral',
         '-C', str(work), '-m', a.model, '-c', f'model_reasoning_effort="{a.effort}"', '-c', 'windows.sandbox="elevated"',
         '-c', 'sandbox_workspace_write.network_access=false',
         '-c', 'sandbox_workspace_write.exclude_tmpdir_env_var=true',
         '-c', 'sandbox_workspace_write.exclude_slash_tmp=true',
         '-o', str(last), '-']
    return c


def sum_usage(events_path):
    tot = {}
    for l in Path(events_path).read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            e = json.loads(l)
        except ValueError:
            continue
        if e.get('type') == 'turn.completed' and isinstance(e.get('usage'), dict):
            for k, v in e['usage'].items():
                if isinstance(v, int):
                    tot[k] = tot.get(k, 0) + v
    return tot


BREACH = re.compile(r'PLANTS\.csv|REPORT\.md|AFTER_REVEAL|BLIND_REVIEW_[ABC]|dorotheus-(sample|yesprobe)|claude-icecore|'
                    r'eo-septuagint-private|Projects[/\\\\]Executive-Orders|\.git\.sealed|git\s+(log|show|cat-file|ls-tree|grep|worktree)|'
                    r'readiness[/\\\\]claims|jobs[/\\\\]mountweazel|HANDOFF|_attempts', re.I)


def scan_events(events_path):
    """Record every command in the Codex event log that touches something the reviewer was told never to open.
    The sandbox cannot stop reads outside the workspace, so this is the audit of the instruction-level rule."""
    hits = []
    for n, l in enumerate(Path(events_path).read_text(encoding='utf-8', errors='replace').splitlines(), 1):
        try:
            e = json.loads(l)
        except ValueError:
            continue
        item = e.get('item') if isinstance(e.get('item'), dict) else {}
        cmd = item.get('command') or ''
        if isinstance(cmd, list):
            cmd = ' '.join(map(str, cmd))
        if cmd and e.get('type') == 'item.started' and BREACH.search(cmd):
            hits.append({'event_line': n, 'command': cmd[:300]})
    return {'suspect_commands': len(hits), 'examples': hits[:10]}


def validate(run, batch, expected_ids, claims):
    out = run / 'work' / f'BLIND_REVIEW_{ARM}.jsonl'
    issues, rows = [], []
    if not out.is_file():
        return {'ok': False, 'issues': ['output file missing'], 'lines': 0}
    for n, l in enumerate(out.read_text(encoding='utf-8').splitlines(), 1):
        if not l.strip():
            continue
        try:
            r = json.loads(l)
        except ValueError as e:
            issues.append(f'line {n}: not JSON ({e})')
            continue
        rows.append(r)
        for k in REQUIRED:
            if k not in r:
                issues.append(f'line {n}: missing {k}')
        if r.get('reviewer') != f'septuagint-codex-{batch}-{ARM}-2026-11-06':
            issues.append(f'line {n}: reviewer {r.get("reviewer")!r}')
        if r.get('model_family') != 'OpenAI':
            issues.append(f'line {n}: model_family {r.get("model_family")!r}')
        if r.get('independent') is not True or r.get('separate_context') is not True:
            issues.append(f'line {n}: independent/separate_context not true')
        if r.get('review_kind') != 'independent_ai_source_review' or r.get('scope') != 'whole_case':
            issues.append(f'line {n}: review_kind/scope')
        if r.get('verdict') not in ('upheld', 'rejected'):
            issues.append(f'line {n}: verdict {r.get("verdict")!r}')
        d = r.get('defects')
        if not isinstance(d, list) or any(not isinstance(x, dict) or not {'field', 'claim_says', 'source_says'} <= set(x) for x in d):
            issues.append(f'line {n}: defects shape')
        elif r.get('verdict') == 'rejected' and not d:
            issues.append(f'line {n}: rejected with no defects')
        if not isinstance(r.get('evidence_checked'), list):
            issues.append(f'line {n}: evidence_checked not a list')
        for k in ('started_utc', 'ended_utc'):
            if not (isinstance(r.get(k), str) and UTC.match(r[k])):
                issues.append(f'line {n}: {k} format')
    want = {canon(c): c['instrument_id'] for c in claims}
    got = [r.get('claim_sha256') for r in rows]
    if len(rows) != len(want):
        issues.append(f'{len(rows)} lines for {len(want)} claims')
    if sorted(got) != sorted(want):
        issues.append('claim_sha256 set differs from the review set: missing '
                      + str(sorted(want[h] for h in set(want) - set(got))) + ', unknown ' + str(sorted(set(got) - set(want))))
    for r in rows:
        if want.get(r.get('claim_sha256')) not in (None, r.get('instrument_id')):
            issues.append(f'instrument_id does not match claim_sha256 for {r.get("claim_sha256", "")[:8]}')
    return {'ok': not issues, 'issues': issues, 'lines': len(rows), 'output_sha256': sha_file(out)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('batch', choices=['y01', 'y02', 'y03', 'y05'])
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--validate-only', action='store_true')
    ap.add_argument('--force', action='store_true')
    for k, v in DEFAULTS.items():
        ap.add_argument('--' + k, default=v, type=type(v))
    a = ap.parse_args()
    src = Path(a.src)
    run, n, ids = build_run(a.batch, a)
    claims = [json.loads(l) for l in (Path(a.private) / 'E' / 'review' / a.batch / 'REVIEW_SET.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    prompt, changes = render_prompt(a.batch, n, run, src, a.python)
    (run / 'PROMPT.txt').write_bytes(prompt.encode('utf-8'))
    problems = audit(run, src)
    if a.validate_only:
        print(json.dumps(validate(run, a.batch, ids, claims), indent=1))
        return 0
    if a.dry_run:
        print('=' * 20, 'PROMPT', '=' * 20)
        print(prompt)
        print('=' * 20, 'CHANGES FROM THE ORIGINAL PROMPT', '=' * 20)
        print('; '.join(changes))
        print(listing(run, src))
        print('--- blinding audit:', 'CLEAN' if not problems else problems)
        print('--- command:', ' '.join(codex_cmd(a, run / 'work', run / 'LAST_MESSAGE.txt')))
        print(f'--- {n} claims; run folder {run}; nothing launched')
        return 1 if problems else 0
    if problems:
        print('blinding audit failed:', problems)
        return 2
    events, last = run / 'EVENTS.jsonl', run / 'LAST_MESSAGE.txt'
    cmd = codex_cmd(a, run / 'work', last)
    env = dict(os.environ, PYTHONUTF8='1')
    # Seal the worktree's .git pointer for the run: it leads to the whole object database, including later commits
    # (the filed claims, PLANTS.csv). It is restored in `finally`.
    gitf, sealed = src / '.git', src / '.git.sealed-by-septuagint'
    gitf.rename(sealed)
    t0, start = time.time(), now()
    try:
        with open(events, 'wb') as ev, open(run / 'STDERR.txt', 'wb') as er:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=ev, stderr=er, env=env)
            try:
                p.communicate(prompt.encode('utf-8'), timeout=a.timeout)
                timed_out = False
            except subprocess.TimeoutExpired:
                p.kill()
                p.communicate()
                timed_out = True
    finally:
        sealed.rename(gitf)
    wall = round(time.time() - t0, 1)
    val = validate(run, a.batch, ids, claims)
    usage = sum_usage(events)
    ver = subprocess.run([a.codex, '--version'], capture_output=True, text=True).stdout.strip()
    rec = {'schema': 'septuagint-run/v1', 'batch': a.batch, 'arm': ARM, 'reviewer': f'septuagint-codex-{a.batch}-{ARM}-2026-11-06',
           'codex_version': ver, 'model': a.model, 'reasoning_effort': a.effort, 'source_commit': SRC_COMMIT,
           'prompt_sha256': hashlib.sha256(prompt.encode('utf-8')).hexdigest(), 'claims': n,
           'started_utc': start, 'ended_utc': now(), 'wall_seconds': wall, 'exit_code': p.returncode, 'timed_out': timed_out,
           'tokens_reported_by_codex': usage, 'validation': {k: val[k] for k in ('ok', 'lines', 'issues')},
           'output_sha256': val.get('output_sha256'), 'blinding_event_scan': scan_events(events),
           'verdicts_in_this_log': False}
    vdir = Path(a.private) / 'verdicts' / a.batch
    vdir.mkdir(parents=True, exist_ok=True)
    for name in (f'BLIND_REVIEW_{ARM}.jsonl',):
        if (run / 'work' / name).is_file():
            shutil.copyfile(run / 'work' / name, vdir / name)
    for name in ('EVENTS.jsonl', 'LAST_MESSAGE.txt', 'STDERR.txt', 'PROMPT.txt'):
        if (run / name).is_file():
            shutil.copyfile(run / name, vdir / name)
    (run / 'RUN_LOG.json').write_text(json.dumps(rec, indent=1) + '\n', encoding='utf-8', newline='\n')
    (HERE / 'runs' / f'{a.batch}.json').write_text(json.dumps(rec, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(rec, indent=1))
    return 0 if val['ok'] and p.returncode == 0 else 3


if __name__ == '__main__':
    sys.exit(main())

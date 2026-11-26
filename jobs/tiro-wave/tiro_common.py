"""Tiro shared pieces: the wave's configuration, the one place external commands run, and small file helpers.

Coordinator bookkeeping only: nothing here makes a legal judgment.
"""
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROMPTS = HERE / 'prompts'
DEFAULT_REPO = HERE.parents[1]
KIT = 'jobs/claim-kit/kit.py'
CRUDEN = 'research/excavator/claude-nira-sweep-2026-10-29/cruden.py'
MAKE_COMPLETION = 'research/excavator/claude-nira-sweep-2026-10-29/make_completion.py'
GEDDES = 'jobs/geddes/geddes.py'
ADOPT = 'jobs/claim-kit/adopt_replacement.py'


class TiroError(Exception):
    """A refusal: printed as one line and exit 2, never a traceback."""


class Result:
    def __init__(self, returncode, stdout='', stderr=''):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def run(cmd, cwd, env=None, timeout=None):
    """Run one external command. Every kit, cruden, geddes, make_completion and git call goes through here,
    so tests replace this one function."""
    full = dict(os.environ)
    full.update(env or {})
    p = subprocess.run([str(c) for c in cmd], cwd=str(cwd), env=full, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=timeout)
    return Result(p.returncode, p.stdout, p.stderr)


def run_to_file(cmd, cwd, path):
    """Run a command with its stdout written byte for byte to path (git blobs). Returns a Result without stdout."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as fh:
        p = subprocess.run([str(c) for c in cmd], cwd=str(cwd), stdout=fh, stderr=subprocess.PIPE)
    return Result(p.returncode, '', p.stderr.decode('utf-8', 'replace'))


def py(*args, isolated=False):
    """A Python command as the wave scripts ran it: -X utf8, and -I for scripts that allow it."""
    return [sys.executable, '-X', 'utf8'] + (['-I'] if isolated else []) + [str(a) for a in args]


def kit(*args):
    return py(KIT, *args)


def git(*args):
    return ['git', '-c', 'gc.auto=0', *args]


def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def canon(obj):
    """sha256 of the canonical claim JSON; the same rule reviewers use for claim_sha256."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def write_jsonl(path, rows):
    Path(path).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')


def read_csv(path):
    return list(csv.DictReader(io.StringIO(Path(path).read_text(encoding='utf-8'))))


def write_csv(path, rows, fieldnames):
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=fieldnames, lineterminator='\n')
    w.writeheader()
    w.writerows(rows)
    Path(path).write_text(out.getvalue(), encoding='utf-8')


def version_dirs(folder, prefix):
    """Subfolders PREFIX1, PREFIX2, ... sorted by number (applied-v10 after applied-v9)."""
    found = []
    for d in Path(folder).glob(prefix + '*'):
        m = re.fullmatch(re.escape(prefix) + r'(\d+)', d.name)
        if d.is_dir() and m:
            found.append((int(m.group(1)), d))
    return [d for _, d in sorted(found)]


def next_version(folder, prefix):
    n = 1
    while (Path(folder) / f'{prefix}{n}').exists():
        n += 1
    return Path(folder) / f'{prefix}{n}'


def render(template, values):
    """Fill {{TOKEN}} placeholders; refuse if one is left, so a template change cannot ship a raw token."""
    for k, v in values.items():
        template = template.replace('{{' + k + '}}', str(v))
    left = sorted(set(re.findall(r'\{\{[A-Z_]+\}\}', template)))
    if left:
        raise TiroError('unfilled template tokens: ' + ', '.join(left))
    return template


class Wave:
    """One wave, read from its WAVE.json. Every name the old scripts hardcoded comes from here.

    spec may be the wave name (baldus-2026-11-25), its folder (research/excavator/claude-baldus-2026-11-25) or
    the WAVE.json path. The scratch root (keys, review sets, prompts, logs, ledgers) defaults to
    /home/claude/<short name>-scr and must lie outside the repository."""

    def __init__(self, repo, spec, scratch=None):
        self.repo = Path(repo).resolve()
        p = Path(spec)
        candidates = [p, self.repo / p, p / 'WAVE.json', self.repo / p / 'WAVE.json',
                      self.repo / 'research/excavator' / f'claude-{spec}' / 'WAVE.json']
        path = next((c for c in candidates if c.name == 'WAVE.json' and c.is_file()), None)
        if path is None:
            raise TiroError(f'no WAVE.json for wave {spec!r} (tried the name, the folder and research/excavator/claude-{spec}/)')
        self.plan_path = path.resolve()
        self.plan = json.loads(self.plan_path.read_text(encoding='utf-8'))
        self.name = self.plan.get('wave') or ''
        m = re.fullmatch(r'(.+)-(\d{4}-\d{2}-\d{2})', self.name)
        if not m:
            raise TiroError(f'{self.plan_path}: "wave" must be NAME-YYYY-MM-DD, found {self.name!r}')
        self.short, self.date = m.groups()
        self.dir = self.plan_path.parent
        try:
            self.rel = self.dir.relative_to(self.repo).as_posix()
        except ValueError:
            raise TiroError(f'wave folder {self.dir} is not inside the repository {self.repo}')
        if not self.dir.name.endswith(self.name):
            raise TiroError(f'wave folder {self.dir.name} does not match the plan\'s wave name {self.name}')
        self.actions = [a['id'] for a in self.plan.get('actions', []) if isinstance(a, dict) and a.get('id')]
        self.adjudicator = f'claude-coordinator-{self.name}'
        self.scratch = Path(scratch or os.environ.get('TIRO_SCRATCH') or f'/home/claude/{self.short}-scr').resolve()
        if self.scratch == self.repo or self.repo in self.scratch.parents:
            raise TiroError(f'scratch root {self.scratch} is inside the repository; keys and review sets must stay outside it')

    # Paths -------------------------------------------------------------------------------------------------------
    def batch_dir(self, batch):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', batch or ''):
            raise TiroError(f'bad batch name {batch!r}')
        return self.dir / batch

    def packet(self, batch, name=None):
        """The batch's packet folder. With no name, the only packet* folder that holds a prepared packet; several
        are a refusal (pass --packet), because guessing 'packet' when a packet-v2 exists caused today's mistakes."""
        bdir = self.batch_dir(batch)
        if name:
            p = bdir / name
            if not p.is_dir():
                raise TiroError(f'no packet folder {self.rel}/{batch}/{name}')
            return p
        found = sorted(d for d in bdir.glob('packet*') if d.is_dir()
                       and any((d / f).exists() for f in ('PACKET.json', 'PREPARE.json', 'ADMISSION.json')))
        if len(found) == 1:
            return found[0]
        if not found:
            raise TiroError(f'no prepared packet under {self.rel}/{batch}/')
        raise TiroError(f'{self.rel}/{batch} has several packets ({", ".join(d.name for d in found)}): pass --packet')

    def relpath(self, path):
        return Path(path).resolve().relative_to(self.repo).as_posix()

    def scr(self, *parts):
        return self.scratch.joinpath(*parts)

    def key_path(self, batch):
        return self.scr('keys', f'{batch}.json')

    def action(self, requested=None):
        """The Bentham action: the one named (it must be in WAVE.json) or the plan's only action."""
        if requested:
            if requested not in self.actions:
                raise TiroError(f'action {requested} is not in {self.rel}/WAVE.json (actions: {", ".join(self.actions)})')
            return requested
        if len(self.actions) == 1:
            return self.actions[0]
        raise TiroError(f'{self.rel}/WAVE.json names {len(self.actions)} actions ({", ".join(self.actions)}): pass --action')

    def reviewer_name(self, batch, arm):
        return f'claude-blind-reviewer-{self.short}-{batch}-{arm}-{self.date}'


def packet_meta(packet):
    """agent, Bentham action and member ids of a prepared packet, from PACKET.json when it is on disk, else
    ADMISSION.json, else decisions.csv (heavy files may be skip-worktree in a lean checkout)."""
    packet = Path(packet)
    meta = {'agent': None, 'action': None, 'ids': []}
    adm = packet / 'ADMISSION.json'
    if adm.exists():
        a = json.loads(adm.read_text(encoding='utf-8'))
        meta.update(agent=a.get('agent'), action=a.get('bentham_action'), ids=list(a.get('instrument_ids') or []))
    pj = packet / 'PACKET.json'
    if pj.exists():
        p = json.loads(pj.read_bytes())
        meta['agent'] = p.get('agent') or meta['agent']
        if isinstance(p.get('dossiers'), dict) and p['dossiers']:
            meta['ids'] = list(p['dossiers'])
    if not meta['ids'] and (packet / 'decisions.csv').exists():
        meta['ids'] = [r.get('instrument_id') for r in read_csv(packet / 'decisions.csv') if r.get('instrument_id')]
    return meta


def append_log(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a', encoding='utf-8') as fh:
        fh.write(text if text.endswith('\n') or not text else text + '\n')

"""Persistent and in-process reuse of the fragment-provider Index (working_text.Index).

working_text.py is a pinned compiler file, so it is not touched. This module returns a genuine
working_text.Index. Parsing ~230 MB of FRAGMENTS*.jsonl and resolving ~30k text paths took ~7.5 s per
process; here the parsed raw original_representation rows are cached outside the repository, keyed by
the COMPLETE provider inventory (repo-relative path, byte size, sha256 of every matched file, re-globbed
and re-hashed on every use; never mtimes). The filesystem-dependent resolution (both candidate text
paths, is_file, official classification) is re-run on every use, so text files appearing or disappearing
are honored. A miss builds with working_text.Index(repo) itself, and the cache entry is stored only if
the reconstruction from the raw rows is identical to that genuine build.

CLAIM_KIT_CACHE_DIR sets the cache directory (default ~/.cache/eo-claim-kit);
CLAIM_KIT_INDEX_CACHE=0 disables both the disk cache and in-process reuse.
"""
import hashlib
import io
from contextlib import contextmanager
import json
import os
from pathlib import Path

import working_text as W

FRAGMENT_GLOBS = ('jobs/*/output/FRAGMENTS*.jsonl', 'jobs/*/data/**/FRAGMENTS*.jsonl')
CACHE_FORMAT = 'eo-fragment-index-cache/v2'
CACHE_KEEP = 3
_ROW_FIELDS = 11


def _realpath(joined, memo, resolutions):
    """os.path.realpath(joined), resolving the directory part once per distinct directory and only
    the final component per path. Any unusual shape falls back to the full realpath."""
    head, tail = os.path.split(joined)
    if not head or tail in ('', '.', '..') or '\0' in joined:
        resolved = os.path.realpath(joined)
        resolutions[joined] = resolved
        return resolved
    directory = memo.get(('dir', head))
    if directory is None:
        directory = memo[('dir', head)] = os.path.realpath(head)
    candidate = os.path.join(directory, tail)
    if os.path.islink(candidate):
        resolved = os.path.realpath(joined)
        resolutions[joined] = resolved
        return resolved
    resolutions[joined] = candidate
    return candidate


def provider_paths(repo):
    """Every fragment provider file, re-globbed on each call, in the original deterministic order."""
    repo = Path(repo).resolve()
    paths = set()
    for pattern in FRAGMENT_GLOBS:
        paths.update(repo.glob(pattern))
    return [p for p in sorted(paths) if p.parts[-3] != 'claim-kit']


def _file_digest(path):
    h = hashlib.sha256()
    size = 0
    with path.open('rb') as fh:
        while True:
            chunk = fh.read(1 << 22)
            if not chunk:
                break
            size += len(chunk)
            h.update(chunk)
    return size, h.hexdigest()


def provider_inventory(repo):
    """[(repo-relative path, byte size, sha256 of the file bytes)] of every provider file, plus the
    paths. Content hashes, never mtimes; unreadable files are skipped exactly as the parser skips them."""
    repo = Path(repo).resolve()
    paths = provider_paths(repo)

    def one(path):
        try:
            return _file_digest(path)
        except OSError:
            return None
    if len(paths) > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(8, len(paths))) as pool:
            digests = list(pool.map(one, paths))
    else:
        digests = [one(p) for p in paths]
    kept = [(p, d) for p, d in zip(paths, digests) if d is not None]
    inventory = [(p.relative_to(repo).as_posix(), d[0], d[1]) for p, d in kept]
    return [p for p, _ in kept], inventory


def inventory_key(inventory):
    blob = json.dumps([CACHE_FORMAT, [list(i) for i in inventory]], separators=(',', ':'), ensure_ascii=True)
    return hashlib.sha256(blob.encode('ascii')).hexdigest()


def _rows_digest(files):
    blob = json.dumps(files, separators=(',', ':'), ensure_ascii=True)
    return hashlib.sha256(blob.encode('ascii')).hexdigest()


def cache_dir():
    configured = os.environ.get('CLAIM_KIT_CACHE_DIR')
    return Path(configured) if configured else Path.home() / '.cache' / 'eo-claim-kit'


def cache_enabled():
    return os.environ.get('CLAIM_KIT_INDEX_CACHE', '1') != '0'


def _raw_rows(lines):
    """The expensive part: parse FRAGMENTS lines into the raw, filesystem-independent
    original_representation fields the Index needs."""
    rows = []
    for line in lines:
        try:
            row = json.loads(line)
        except (ValueError, UnicodeError):
            continue
        if not isinstance(row, dict) or row.get('kind') != 'original_representation':
            continue
        data = row.get('data') if isinstance(row.get('data'), dict) else {}
        iid = row.get('instrument_id')
        sha = data.get('sha256')
        if not isinstance(iid, str) or not W.source_sha({'sha256': sha}):
            continue
        rows.append([iid, data.get('grade') or row.get('grade'),
                     data.get('acceptable_as_original', row.get('acceptable_as_original')),
                     sha, data.get('text_sha256'), data.get('text_path'),
                     data.get('needs_page_check') is False,
                     bool(data.get('needs_page_check') or data.get('requires_page_check')),
                     data.get('complete_text'), data.get('url'), row.get('produced_by')])
    return rows


def _parse_file(path):
    """(sha256 of the exact bytes parsed, raw rows). Same line semantics as open(..., encoding='utf-8')."""
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    with io.TextIOWrapper(io.BytesIO(raw), encoding='utf-8') as fh:
        return digest, _raw_rows(fh)


def _cache_file(repo, key):
    tag = hashlib.sha256(str(repo).encode('utf-8', 'surrogateescape')).hexdigest()[:10]
    return cache_dir() / f'fragment-index-{tag}-{key}.json', f'fragment-index-{tag}-'


def _load_cache(repo, key, inventory):
    try:
        path, _ = _cache_file(repo, key)
        doc = json.loads(path.read_text(encoding='utf-8'))
        if (not isinstance(doc, dict) or doc.get('format') != CACHE_FORMAT or doc.get('key') != key
                or doc.get('inventory') != [list(i) for i in inventory]):
            return None
        files = doc.get('rows')
        if not isinstance(files, list) or len(files) != len(inventory):
            return None
        if doc.get('rows_sha256') != _rows_digest(files):
            return None
        for rows in files:
            if not isinstance(rows, list) or any(not isinstance(r, list) or len(r) != _ROW_FIELDS
                                                 or not isinstance(r[0], str) for r in rows):
                return None
        return files
    except (OSError, ValueError, UnicodeError):
        return None


def _store_cache(repo, key, inventory, files):
    try:
        path, prefix = _cache_file(repo, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        doc = {'format': CACHE_FORMAT, 'key': key, 'inventory': [list(i) for i in inventory], 'rows': files,
               'rows_sha256': _rows_digest(files)}
        tmp = path.with_name(f'.{path.name}.{os.getpid()}.tmp')
        try:
            tmp.write_text(json.dumps(doc, separators=(',', ':'), ensure_ascii=True), encoding='ascii')
            os.replace(tmp, path)
        finally:
            tmp.unlink(missing_ok=True)
        old = sorted((p for p in path.parent.glob(prefix + '*.json') if p != path),
                     key=lambda p: p.stat().st_mtime, reverse=True)
        for stale in old[max(0, CACHE_KEEP - 1):]:
            stale.unlink(missing_ok=True)
    except (OSError, ValueError, UnicodeError):
        pass


_SHARED = {}
last_status = None


def _make(repo, by_sha, official, official_by_sha):
    index = W.Index.__new__(W.Index)
    index.repo = Path(repo).resolve()
    index.by_sha, index.official, index.official_by_sha = by_sha, official, official_by_sha
    return index


def resolve(repo, paths, files):
    """Per-row filesystem resolution, identical to W.Index.__init__ but with os.path calls and per-run
    memos (Path.resolve()/relative_to dominated the original build time).
    Returns (by_sha, official, official_by_sha, witness); witness maps each text path whose existence
    was consulted to its answer and each lexical candidate to its resolved path."""
    repo = Path(repo).resolve()
    root = str(repo)
    prefix = root.rstrip(os.sep) + os.sep
    by_sha, official, official_by_sha = {}, {}, {}
    real, isfile, resolutions = {}, {}, {}

    def child(value, start):
        if not isinstance(value, str) or not value:
            raise ValueError('missing_path')
        memo = (start, value)
        got = real.get(memo)
        if got is None:
            got = real[memo] = _realpath(os.path.join(start, value), real, resolutions)
        if got != root and not got.startswith(prefix):
            raise ValueError('outside_repository')
        return got

    def is_file(p):
        got = isfile.get(p)
        if got is None:
            got = isfile[p] = os.path.isfile(p)
        return got
    for path, rows in zip(paths, files):
        base = str(path.parent)
        decl = path.relative_to(repo).as_posix()
        for (iid, grade, acceptable, sha, text_sha, raw_text_path, needs_false, requires, complete, url,
             produced_by) in rows:
            try:
                text_path = child(raw_text_path, base)
                # Some producers publish repo-relative text paths.
                if not is_file(text_path):
                    text_path = child(raw_text_path, root)
            except (ValueError, TypeError):
                continue
            rel = '.' if text_path == root else text_path[len(prefix):].replace(os.sep, '/')
            rec = {'instrument_id': iid, 'grade': grade, 'acceptable_as_original': acceptable,
                   'sha256': sha, 'text_sha256': text_sha, 'text_path': rel,
                   'declaration_path': decl, 'requires_page_check': requires,
                   'complete_text': complete, 'url': url}
            if acceptable is False:
                by_sha.setdefault(W.source_sha(rec), []).append(rec)
            elif ((acceptable is True or produced_by in W.OFFICIAL_PRODUCERS)
                  and needs_false and is_file(text_path)):
                # Candidate availability only. This neither authenticates the source nor
                # substitutes it into a claim.
                official.setdefault(iid, []).append(rec)
                official_by_sha.setdefault(W.source_sha(rec), []).append(rec)
    return by_sha, official, official_by_sha, {'isfile': isfile, 'resolutions': resolutions}


def _same(index, by_sha, official, official_by_sha):
    return (index.by_sha == by_sha and index.official == official and index.official_by_sha == official_by_sha
            and list(index.by_sha) == list(by_sha) and list(index.official) == list(official)
            and list(index.official_by_sha) == list(official_by_sha))


def build(repo):
    """(Index, status, key, witness). status: disabled | hit | miss_stored | miss_unverified."""
    repo = Path(repo).resolve()
    if not cache_enabled():
        return W.Index(repo), 'disabled', None, {}
    paths, inventory = provider_inventory(repo)
    key = inventory_key(inventory)
    files = _load_cache(repo, key, inventory)
    if files is not None:
        by_sha, official, official_by_sha, witness = resolve(repo, paths, files)
        return _make(repo, by_sha, official, official_by_sha), 'hit', key, witness
    index = W.Index(repo)  # the genuine construction
    files, verified = [], True
    for path, (_, size, sha) in zip(paths, inventory):
        try:
            digest, rows = _parse_file(path)
        except (OSError, ValueError):
            verified, digest, rows = False, None, []
        verified = verified and digest == sha
        files.append(rows)
    by_sha, official, official_by_sha, witness = resolve(repo, paths, files)
    if not verified or not _same(index, by_sha, official, official_by_sha):
        return index, 'miss_unverified', key, witness
    _store_cache(repo, key, inventory, files)
    return index, 'miss_stored', key, witness


def index(repo):
    """A genuine working_text.Index, from the persistent cache when the provider inventory matches."""
    global last_status
    result, last_status, _, _ = build(repo)
    return result


def shared(repo):
    """One Index per process, repository and exact provider inventory. Provider files are re-globbed and
    content-hashed on every call; a reused instance is also re-validated against each text-file existence
    and lexical path resolution its construction consulted."""
    global last_status
    repo = Path(repo).resolve()
    if not cache_enabled():
        return W.Index(repo)
    _, inventory = provider_inventory(repo)
    key = (str(repo), inventory_key(inventory))
    hit = _SHARED.get(key)
    if (hit is not None
            and all(os.path.isfile(p) == seen for p, seen in hit[1]['isfile'].items())
            and _resolutions_match(hit[1]['resolutions'])):
        last_status = 'process_reuse'
        return hit[0]
    result, last_status, _, witness = build(repo)
    for stale in [k for k in _SHARED if k[0] == key[0]]:
        del _SHARED[stale]
    _SHARED[key] = (result, witness)
    return result


def _resolutions_match(resolutions):
    """Re-resolve every lexical candidate, sharing directory work across the witness."""
    memo, current = {}, {}
    for path, expected in resolutions.items():
        if _realpath(path, memo, current) != expected:
            return False
    return True


@contextmanager
def policy_index(repo):
    """Let working_text.policy use one verified index instead of building one per checked claim.

    assemble.check_claim calls working_text.policy(claim, repo) without an index, so every checked
    claim rebuilt the complete provider index (about 8 s each). Inside this context the default index
    is shared(repo), which re-hashes the complete provider inventory and re-checks every consulted
    text path and its resolution on each call, so the result equals a fresh construction. assemble.py and
    working_text.py stay byte-identical (both are in the compiler fingerprint); an explicit index
    argument is never replaced, and the original function is restored on exit.
    """
    original = W.policy

    def policy(claim, repo_arg, index=None):
        return original(claim, repo_arg, index if index is not None else shared(repo_arg))
    W.policy = policy
    try:
        yield
    finally:
        W.policy = original

"""Palsgraf: recheck only the claims a change can reach (owner ruling D-20261109-impact-scoped-checks).

Named for Palsgraf v. Long Island Railroad (N.Y. 1928): liability reaches only those within the zone a
change can foreseeably affect. Here the "zone" of a claim is recorded, not guessed.

How it stays sound
------------------
While the checker checks one claim, this module records every input that claim's result was computed
from, at two levels:

* values: every lookup into the run-wide tables the checker builds before reading claims (the held-source
  index by SHA-256 and by URL, the Opus text pack, the working-text fragment index, Lachmann
  confirmations, the universe, provisional statuses, signing dates, GPO matches, archive captures);
* files: every file the check opens (PEP 578 audit hook), every directory it lists, and every path it
  stats (``os.stat``/``os.lstat``, which is how ``Path.is_file()`` and ``exists()`` look), including reads
  hidden behind the text reader's in-memory memos (``sources.TRACE`` replays them).

Each input is stored with a fingerprint (a SHA-256 of the canonical value, of the file's bytes, of the
listing, or of the stat type and size). On the next run every stored fingerprint is recomputed from the
current checkout. A claim whose line bytes and every fingerprint are unchanged has, by construction, the
same inputs, so its previous result is reused; any difference, a new or edited line, a network attempt, a
date judged against "today", or a checker error makes it rechecked.

The whole run is redone ("full") when the checker's own code or rules changed (any repository module it
imported, any file read outside the per-claim tables, Python, pypdf or a setting), when there is no usable
previous trace, when a mode outside the default production run is requested, and at least every
RECONCILE_DAYS days. A periodic full run also reconciles: every claim the selector would have reused must
come out identical, or the run stops with BLOCKED.json (a missed dependency is a soundness bug).

Nothing here changes a status, a claim, a count or a check; it only decides which claims to recompute.
"""

import collections
import contextlib
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import pathlib
import sys
import sysconfig

SCHEMA = "eo-claim-checker-trace/v1"
TRACE_FILE = "DEPENDENCY_TRACE.json.gz"
SELECTION_FILE = "SELECTION.json"
RECONCILE_DAYS = 7
SETTINGS_ENV = ("CLAIM_CHECKER_CACHE_ROOTS", "CLAIM_CHECKER_TEXT_PACK", "CLAIM_CHECKER_VERIFY_DOWNLOADS",
                "CLAIM_CHECKER_CSV_MAX_MB")


# ------------------------------------------------------------------ recording

class Recorder:
    """A stack of dependency sets. Outside a claim (empty stack) only the global phase is recorded."""

    def __init__(self):
        self.stack = []
        self.memo = {}  # memo key -> frozenset of deps captured when the memo was filled
        self.global_reads = set()
        # Only inside explicit windows (the checker's imports, gate and tracker loading) is a read outside a
        # claim a global input; any other read in the process (a test, a caller) is not.
        self.global_phase = False
        self.excluded = []  # path prefixes never recorded (stdlib, site-packages, outputs)
        self.existence_only = []  # path prefixes recorded by existence (content-addressed caches)
        self._busy = False

    # dependency keys: "f:" file bytes, "s:" stat, "l:" listing, "m:<table>\0<key>" value, "M:<table>" whole
    # table, "i:" index by sha, "u:" index by url, "v:" volatile (always recheck)
    def add(self, dep):
        for s in self.stack:
            s.add(dep)

    def volatile(self, reason):
        self.add("v:" + reason)

    def active(self):
        return bool(self.stack) and not self._busy

    @contextlib.contextmanager
    def claim(self):
        self.stack.append(set())
        try:
            yield self.stack[-1]
        finally:
            self.stack.pop()

    @contextlib.contextmanager
    def capture(self, key):
        """Collect the deps of filling a memo entry so a later hit can replay them."""
        if not self.stack:
            yield
            return
        self.stack.append(set())
        try:
            yield
        finally:
            got = self.stack.pop()
            self.memo[key] = frozenset(got) | self.memo.get(key, frozenset())
            self.add_all(got)

    def replay(self, key):
        if self.stack:
            self.add_all(self.memo.get(key, ()))

    def add_all(self, deps):
        for s in self.stack:
            s.update(deps)

    @contextlib.contextmanager
    def global_window(self):
        """Reads here are code or rules: a change to any of them forces a full run."""
        old, self.global_phase = self.global_phase, True
        try:
            yield
        finally:
            self.global_phase = old

    @contextlib.contextmanager
    def summarized(self):
        """Run-wide loaders whose every per-claim use goes through a recorded table lookup."""
        old, self.global_phase = self.global_phase, False
        try:
            yield
        finally:
            self.global_phase = old

    @contextlib.contextmanager
    def quiet(self):
        old, self._busy = self._busy, True
        try:
            yield
        finally:
            self._busy = old

    def _path(self, p):
        if isinstance(p, int):
            return None
        try:
            p = os.fsdecode(p)
        except TypeError:
            return None
        p = os.path.abspath(p)
        if any(p == e or p.startswith(e + os.sep) for e in self.excluded) or "__pycache__" in p:
            return None
        return p

    def _kind(self, p, kind):
        if kind in ("f", "s", "l") and any(p.startswith(e + os.sep) for e in self.existence_only):
            return "e"  # content-addressed cache: only whether the file is there matters
        return kind

    def on_event(self, event, args):
        if self._busy:
            return
        if event == "open":
            path, mode, flags = (tuple(args) + (None, None, None))[:3]
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or \
                (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT))
            if writing:
                return
            kind = "f"
        elif event in ("os.listdir", "os.scandir"):
            path, kind = (args[0] if args else "."), "l"
            if path is None:
                path = "."
        elif event in ("urllib.Request", "socket.connect", "socket.getaddrinfo", "subprocess.Popen",
                       "os.system", "os.exec", "os.posix_spawn", "os.spawn"):
            if self.stack:
                self.volatile(event)
            return
        else:
            return
        if not (self.stack or self.global_phase):
            return
        p = self._path(path)
        if p is None:
            return
        dep = self._kind(p, kind) + ":" + p
        if self.stack:
            self.add(dep)
        elif self.global_phase:
            self.global_reads.add(dep)

    def on_stat(self, path):
        if self._busy or not self.stack:
            return
        p = self._path(path)
        if p is not None:
            self.add(self._kind(p, "s") + ":" + p)


class _Null:
    """sources.TRACE when Palsgraf is not recording."""

    def capture(self, key):
        return contextlib.nullcontext()

    def replay(self, key):
        pass

    def volatile(self, reason):
        pass


NULL = _Null()
REC = None


def install():
    """Install the audit hook and stat recorder once per process; returns the Recorder."""
    global REC
    if REC is not None:
        return REC
    rec = Recorder()
    rec.global_phase = True  # the importing checker turns this off once its own imports are done
    for key in ("stdlib", "platstdlib", "purelib", "platlib"):
        p = sysconfig.get_paths().get(key)
        if p:
            rec.excluded.append(os.path.abspath(p))
    for p in {sys.prefix, sys.base_prefix, sys.exec_prefix}:
        rec.excluded.append(os.path.abspath(os.path.join(p, "lib")))
    rec.excluded += ["/proc", "/dev", "/sys"]
    sys.addaudithook(rec.on_event)
    real_stat, real_lstat = os.stat, os.lstat

    def stat(path, *a, **k):
        if rec.stack and not rec._busy:
            rec.on_stat(path)
        return real_stat(path, *a, **k)

    def lstat(path, *a, **k):
        if rec.stack and not rec._busy:
            rec.on_stat(path)
        return real_lstat(path, *a, **k)

    os.stat, os.lstat = stat, lstat
    REC = rec
    return rec


class Table:
    """A read-only mapping (or set) whose per-key reads are recorded as value dependencies."""

    def __init__(self, name, data, rec):
        self._name, self._data, self._rec = name, data, rec

    def _note(self, key):
        if self._rec.active():
            self._rec.add("m:" + self._name + "\0" + _key(key))

    def _all(self):
        if self._rec.active():
            self._rec.add("M:" + self._name)

    def get(self, key, default=None):
        self._note(key)
        return self._data.get(key, default)

    def __getitem__(self, key):
        self._note(key)
        return self._data[key]

    def __contains__(self, key):
        self._note(key)
        return key in self._data

    def __iter__(self):
        self._all()
        return iter(self._data)

    def __len__(self):
        self._all()
        return len(self._data)

    def keys(self):
        self._all()
        return self._data.keys()

    def items(self):
        self._all()
        return self._data.items()

    def values(self):
        self._all()
        return self._data.values()

    def __bool__(self):
        self._all()
        return bool(self._data)


def _key(key):
    return key if isinstance(key, str) else "\1" + json.dumps(key, default=str, sort_keys=True)


class TracedIndex:
    """sources.HeldIndex with recorded lookups; everything else is delegated."""

    def __init__(self, index, rec):
        self._index, self._rec = index, rec
        self.packed_texts = Table("packed", index.packed_texts, rec)

    def lookup_sha(self, sha):
        if self._rec.active():
            self._rec.add("i:" + str(sha))
        return self._index.lookup_sha(sha)

    def lookup_url(self, url):
        if self._rec.active():
            self._rec.add("u:" + str(url))
        return self._index.lookup_url(url)

    def __getattr__(self, name):
        return getattr(self._index, name)


def trace_context(ctx, rec, W):
    """Wrap a checker Context's run-wide tables so per-claim reads are recorded."""
    ctx.raw = {"universe": ctx.universe, "statuses": ctx.statuses, "signing": ctx.signing,
               "gpo": ctx.gpo_matched, "archive": ctx.archive_captures, "index": ctx.index,
               "wt_by_sha": ctx.working_text_index.by_sha, "wt_official": ctx.working_text_index.official,
               "wt_official_by_sha": ctx.working_text_index.official_by_sha,
               "confirmations": ctx.confirmations}
    ctx.universe = Table("universe", ctx.universe, rec)
    ctx.statuses = Table("statuses", ctx.statuses, rec)
    ctx.signing = Table("signing", ctx.signing, rec)
    ctx.gpo_matched = Table("gpo", ctx.gpo_matched, rec)
    ctx.archive_captures = Table("archive", ctx.archive_captures, rec)
    ctx.index = TracedIndex(ctx.index, rec)
    ctx.reader.packed = ctx.index.packed_texts
    wi = ctx.working_text_index
    wi.by_sha = Table("wt_by_sha", wi.by_sha, rec)
    wi.official = Table("wt_official", wi.official, rec)
    wi.official_by_sha = Table("wt_official_by_sha", wi.official_by_sha, rec)
    ctx.confirmations = Table("confirmations", ctx.confirmations, rec)
    ctx.raw["packed"] = ctx.index._index.packed_texts


# --------------------------------------------------------------- fingerprints

def _canon(obj):
    def default(o):
        if isinstance(o, (set, frozenset)):
            return sorted(o, key=lambda x: json.dumps(x, default=str, sort_keys=True))
        if isinstance(o, os.PathLike):
            return os.fspath(o)
        slots = getattr(type(o), "__slots__", None)
        if slots:
            return {"__type__": type(o).__name__, **{s: getattr(o, s, None) for s in slots}}
        if hasattr(o, "__dict__"):
            return {"__type__": type(o).__name__, **vars(o)}
        return repr(o)
    return json.dumps(obj, default=default, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _h(text):
    return hashlib.sha256(text.encode("utf-8", "surrogatepass") if isinstance(text, str) else text).hexdigest()[:32]


_ABSENT = object()


class Fingerprinter:
    """Current fingerprint of any recorded dependency; memoised per run."""

    def __init__(self, raw, rec):
        self.raw, self.rec, self.memo = raw, rec, {}
        self.bytes_hashed = 0

    def __call__(self, dep):
        fp = self.memo.get(dep)
        if fp is None:
            with self.rec.quiet():
                fp = self.memo[dep] = self._compute(dep)
        return fp

    def _compute(self, dep):
        kind, _, rest = dep.partition(":")
        if kind == "v":
            return "volatile"
        if kind == "f":
            try:
                h = hashlib.sha256()
                with open(rest, "rb") as fh:
                    for chunk in iter(lambda: fh.read(1 << 20), b""):
                        h.update(chunk)
                        self.bytes_hashed += len(chunk)
                return "b" + h.hexdigest()[:32]
            except IsADirectoryError:
                return "dir"
            except OSError as exc:
                return "unreadable:" + type(exc).__name__
        if kind == "e":
            return "present" if os.path.isfile(rest) else "absent"
        if kind == "s":
            try:
                st = os.lstat(rest)
            except OSError:
                return "missing"
            import stat as S
            if S.S_ISLNK(st.st_mode):
                try:
                    target = os.stat(rest)
                    return f"link:{os.readlink(rest)}:{'dir' if S.S_ISDIR(target.st_mode) else target.st_size}"
                except OSError:
                    return "link:broken"
            if S.S_ISDIR(st.st_mode):
                return "dir"
            return f"file:{st.st_size}" if S.S_ISREG(st.st_mode) else "other"
        if kind == "l":
            try:
                return "l" + _h("\n".join(sorted(os.listdir(rest))))
            except OSError as exc:
                return "unlistable:" + type(exc).__name__
        if kind == "i":
            return _h(_canon(self.raw["index"].lookup_sha(rest)))
        if kind == "u":
            return _h(_canon(self.raw["index"].lookup_url(rest)))
        if kind == "m":
            table, _, key = rest.partition("\0")
            data = self.raw.get(table)
            if data is None:
                return "no_table"
            if key.startswith("\1"):
                key = json.loads(key[1:])
                key = tuple(key) if isinstance(key, list) else key
            if isinstance(data, (set, frozenset)):
                return "in" if key in data else "out"
            val = data.get(key, _ABSENT) if hasattr(data, "get") else _ABSENT
            return "absent" if val is _ABSENT else _h(_canon(val))
        if kind == "M":
            data = self.raw.get(rest)
            return "no_table" if data is None else _h(_canon(data))
        return "unknown_kind"


def settings(repo, cache_dir):
    try:
        import pypdf
        pv = getattr(pypdf, "__version__", "yes")
    except ImportError:
        pv = None
    return {"python": sys.version, "pypdf": pv, "repo": str(repo), "cache_dir": str(cache_dir),
            "env": {k: os.environ.get(k) for k in SETTINGS_ENV}}


HOME_REPO = pathlib.Path(__file__).resolve().parent.parent.parent


def code_deps(repo, rec):
    """Global dependencies: every module loaded from the repository being checked or from the repository
    holding this checker (they differ in tests), and every file read in a global window."""
    roots = {str(pathlib.Path(repo).resolve()), str(HOME_REPO)}
    deps = set(rec.global_reads)
    for m in list(sys.modules.values()):
        f = getattr(m, "__file__", None)
        if isinstance(f, str):
            f = os.path.abspath(f)
            if any(f.startswith(r + os.sep) for r in roots):
                deps.add("f:" + f)
    return sorted(d for d in deps if d[:2] in ("f:", "s:", "l:", "e:"))


# ------------------------------------------------------------------- trace io

def line_sha(raw_line):
    return hashlib.sha256(raw_line.encode("utf-8", "surrogatepass")).hexdigest()


def load_trace(dirs):
    """(trace, path) from the first directory holding a readable trace, or (None, reason)."""
    reasons = []
    for d in dirs:
        if not d:
            continue
        p = pathlib.Path(d) / TRACE_FILE
        if not p.is_file():
            reasons.append(f"no {TRACE_FILE} in {d}")
            continue
        try:
            with gzip.open(p, "rt", encoding="utf-8") as fh:
                t = json.load(fh)
        except (OSError, ValueError, EOFError) as exc:
            reasons.append(f"{p}: unreadable ({type(exc).__name__})")
            continue
        if t.get("schema") != SCHEMA:
            reasons.append(f"{p}: schema {t.get('schema')!r}, expected {SCHEMA}")
            continue
        return t, str(p)
    return None, "; ".join(reasons) or "no previous output directory"


def write_trace(out, trace):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0, compresslevel=9) as gz:
        # Insertion order, not sorted keys: a reused claim summary must keep a full run's key order.
        gz.write(json.dumps(trace, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    (pathlib.Path(out) / TRACE_FILE).write_bytes(buf.getvalue())


def build_trace(claim_entries, fps, code, sett, last_full):
    """claim_entries: {line_sha: {"deps": [dep, ...], ...}}; deps are stored once in a table."""
    table, ids = [], {}
    claims = {}
    for sha in sorted(claim_entries):
        e = dict(claim_entries[sha])
        refs = []
        for d in sorted(set(e.pop("deps"))):
            if d not in ids:
                ids[d] = len(table)
                table.append([d, fps(d)])
            refs.append(ids[d])
        e["deps"] = refs
        claims[sha] = e
    return {"schema": SCHEMA, "settings": sett, "code": {d: fps(d) for d in code},
            "last_full": last_full, "deps": table, "claims": claims}


# --------------------------------------------------------------------- choice

def utc_now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def decide(trace, line_shas, fps, sett, *, forced_full=None, now=None):
    """Return the selection record: mode, reason, which lines to recheck and why.

    line_shas: [line_sha] in claim order. Pure apart from fps (the current fingerprints)."""
    now = now or utc_now()
    sel = {"mode": "full", "reason": None, "recheck": [], "reuse": [], "why": collections.Counter(),
           "changed_code": [], "changed_dep_kinds": collections.Counter(), "would_reuse": []}
    if trace is None:
        sel["reason"] = "no_previous_trace"
    else:
        changed = [k for k, v in sorted(trace.get("settings", {}).items()) if sett.get(k) != v]
        changed += [k for k in sett if k not in trace.get("settings", {})]
        code_changed = [d for d, fp in sorted(trace.get("code", {}).items()) if fps(d) != fp]
        sel["changed_code"] = (["setting:" + c for c in changed] + code_changed)[:50]
        last = (trace.get("last_full") or {}).get("utc")
        try:
            age = (now - dt.datetime.fromisoformat(last.replace("Z", "+00:00"))).total_seconds() / 86400
        except (AttributeError, ValueError):
            age = None
        if changed or code_changed:
            sel["reason"] = "code_or_rules_changed"
        elif not trace.get("code"):
            sel["reason"] = "previous_trace_has_no_code_record"
        else:
            table = trace.get("deps", [])
            prior = trace.get("claims", {})
            current = {}
            for sha in line_shas:
                e = prior.get(sha)
                if e is None:
                    why = "new_or_edited_line"
                elif e.get("volatile"):
                    why = "volatile:" + ",".join(e["volatile"][:3])
                else:
                    why = None
                    for i in e.get("deps", []):
                        d, fp = table[i]
                        if fps(d) != fp:
                            why = "input_changed"
                            sel["changed_dep_kinds"][d.split(":", 1)[0]] += 1
                            current.setdefault("examples", []).append(d[:200])
                            break
                if why:
                    sel["recheck"].append(sha)
                    sel["why"][why.split(":", 1)[0]] += 1
                else:
                    sel["reuse"].append(sha)
            sel["changed_examples"] = sorted(set(current.get("examples", [])))[:20]
            if forced_full:
                sel["reason"] = forced_full
                sel["would_reuse"], sel["reuse"], sel["recheck"] = sel["reuse"], [], list(line_shas)
            elif age is None or age >= RECONCILE_DAYS:
                sel["reason"] = "periodic_full_reconcile"
                sel["would_reuse"], sel["reuse"], sel["recheck"] = sel["reuse"], [], list(line_shas)
            else:
                sel["mode"] = "selective"
                sel["reason"] = "inputs_compared"
    if sel["mode"] == "full" and not sel["recheck"]:
        sel["recheck"] = list(line_shas)
    sel["why"] = dict(sel["why"])
    sel["changed_dep_kinds"] = dict(sel["changed_dep_kinds"])
    return sel


def comparable(entry):
    """The parts of a stored claim result a full rerun must reproduce exactly."""
    return {k: entry.get(k) for k in ("summary", "rows", "stats")}

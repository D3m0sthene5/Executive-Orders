"""Maudslay conveyor: run one claim-kit batch end to end so that a coordinator model only adjudicates.

Named for Henry Maudslay, whose Portsmouth block-making machines (from 1803) let a few unskilled hands do the work
of many skilled ones. The 2026-11-09/10 Codex wave spent 54% of its tokens on coordinators doing clerical steps
themselves; the Papinian lane, where small scripts did that work, spent 17%. This file is those scripts as one
resumable state machine.

    python -I jobs/maudslay-conveyor/conveyor.py run --run-dir research/excavator/RUN --batch b01 --agent NAME \
        --action BENTHAM_ACTION --n 20 --route ROUTE.txt --workers WORKERS.json --batch-usd 170 [--publish]
    python -I jobs/maudslay-conveyor/conveyor.py status research/excavator/RUN/b01
    python -I jobs/maudslay-conveyor/conveyor.py commands --workers WORKERS.json      (print worker commands)

Stages, each recorded in BATCH/LEDGER.jsonl and skipped on a re-run once done: reserve, prepare, dispatch, render,
produce, collect, check (with repair rounds), plant, review, controls, reveal, agree, complete, measure. See README.md.

Workers never run inside the repository: each gets a fresh, empty folder under the scratch root (outside the
repository), so no worker loads the repository's CLAUDE.md or AGENTS.md. Review sets, the sealed control key and
the genuine control claims also stay in the scratch root; only the post-reveal records the kit's completion needs
are written under research/.

Exit codes: 0 done; 1 failed; 2 stopped by a stop rule; 3 paused for coordinator adjudication; 4 done, but Bentham's
gate says STOP; 5 done, but the gate gave no verdict (refused or unranked).

The conveyor makes no legal judgment. It never decides an order the arms disagree on, never edits a claim, and never
certifies anything: human-certified stays 0.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import copy
import csv
import hashlib
import json
import os
import random
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PROMPTS = HERE / "prompts"

EXIT_DONE, EXIT_FAILED, EXIT_STOPPED, EXIT_PAUSED, EXIT_GATE_STOP, EXIT_NO_GATE = 0, 1, 2, 3, 4, 5
# A planted control is caught only when a word or field name in the reviewer's `defects` is one of these.
DATE_TERMS = frozenset({"date", "dates", "dated", "first_end", "whole_order_end", "signing_date", "effective_date",
                        "later_event", "later_events", "year", "years"})
OUTCOMES = ("submit", "unresolved", "blocked", "route_owner")
# Settings fixed when a batch starts; a re-run may change only budgets, concurrency, timeouts and switches.
FIXED = ("agent", "action", "n", "ids", "route", "replacement_proposal", "publication", "prompt_cap_chars",
         "review_chunk", "repair_rounds", "adjudicator", "keys_dir", "scratch_root")
MUTABLE = ("parallel", "item_usd", "item_tokens", "batch_usd", "batch_tokens", "item_timeout", "publish",
           "defer_adjudication", "batches_file", "tools", "workers")

DEFAULT_TOOLS = {
    "kit": ["{python}", "-X", "utf8", "{repo}/jobs/claim-kit/kit.py", "--repo", "{repo}"],
    "lookups": ["{python}", "-X", "utf8", "-I", "{repo}/research/excavator/claude-nira-sweep-2026-10-29/cruden.py",
                "lookups", "{packet}"],
    "view": ["{python}", "-X", "utf8", "-I", "{repo}/jobs/geddes/geddes.py", "view", "{packet}/PACKET.json", "{iid}",
             "--write", "{out}"],
    "gate": ["{python}", "-I", "{repo}/jobs/bentham/bentham.py", "gate", "--action", "{action}", "--batches",
             "{batches}"],
}

# Worker templates. Every call is a fresh session in a fresh folder outside the repository.
CLAUDE_TEMPLATE = ["claude", "-p", "--model", "{model}", "--output-format", "stream-json", "--verbose",
                   "--max-turns", "{max_turns}", "--max-budget-usd", "{item_usd}", "--permission-mode", "auto",
                   "--add-dir", "{repo}"]
CODEX_TEMPLATE = ["codex", "exec", "--json", "--ephemeral", "--skip-git-repo-check", "-C", "{cwd}", "-m", "{model}",
                  "--config", 'model_reasoning_effort="medium"',
                  "--config", "model_auto_compact_token_limit={auto_compact_tokens}",
                  "--config", "tool_output_token_limit={tool_output_tokens}",
                  "--config", 'approval_policy="never"',
                  "--config", 'sandbox_mode="workspace-write"',
                  "--config", "sandbox_workspace_write.writable_roots={writable_roots}",
                  "--config", "sandbox_workspace_write.network_access={network}",
                  "-"]
# Refused anywhere in any worker command: session reuse, and the short -c (claude --continue; use codex --config).
REFUSED_TOKENS = {"-c", "-r", "--continue", "--resume", "resume", "--last", "--fork-session", "fork"}
UNSAFE_TOKENS = {"--dangerously-bypass-approvals-and-sandbox", "--yolo", "--dangerously-skip-permissions"}
PATH_TAIL = re.compile(r"[^\s\"'`;|&<>(),]*")


class Stop(Exception):
    """A stop rule fired: the batch is not completed (exit 2)."""


class Pause(Exception):
    """Orders wait for the coordinator's adjudication (exit 3)."""


class Fail(Exception):
    """A tool or configuration error (exit 1)."""


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def canon(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def fsha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def slug(iid):
    return iid.replace(":", "_")


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def read_jsonl(path):
    out = []
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return out
    for line in text.splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as fh:
        rd = csv.DictReader(fh)
        return list(rd.fieldnames or []), list(rd)


def write_csv(path, fields, rows):
    # Same dialect as jobs/claim-kit/batch.py csv_write.
    with Path(path).open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def json_list(text):
    try:
        v = json.loads(text) if text else []
    except ValueError:
        v = [text]
    return v if isinstance(v, list) else [v]


def bash_path(p):
    s = Path(p).as_posix()
    m = re.match(r"^([A-Za-z]):/(.*)$", s)
    return f"/{m.group(1).lower()}/{m.group(2)}" if m else s


def move_aside(path, stem):
    """Rename path to the first free STEM-k beside it; an orphan process holding the folder is a clear failure."""
    path = Path(path)
    k = 1
    while (path.parent / f"{stem}-{k}").exists():
        k += 1
    try:
        os.replace(path, path.parent / f"{stem}-{k}")
    except OSError as exc:
        raise Fail(f"cannot move {path} aside ({exc}); a leftover process may still hold it. Stop it and re-run.")
    return path.parent / f"{stem}-{k}"


# ---------------------------------------------------------------------------------------------------------------
# Processes


def pid_alive(pid, launched_epoch=None):
    """True if the process exists and (on Windows) was created within two minutes of launched_epoch."""
    if not pid:
        return False
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        k = ctypes.windll.kernel32
        k.OpenProcess.restype = wintypes.HANDLE
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        h = k.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        try:
            code = wintypes.DWORD()
            if not k.GetExitCodeProcess(h, ctypes.byref(code)) or code.value != 259:  # STILL_ACTIVE
                return False
            if launched_epoch:
                ft = [wintypes.FILETIME() for _ in range(4)]
                if k.GetProcessTimes(h, *[ctypes.byref(f) for f in ft]):
                    created = ((ft[0].dwHighDateTime << 32) + ft[0].dwLowDateTime) / 1e7 - 11644473600
                    if abs(created - float(launched_epoch)) > 120:
                        return False  # the PID was reused by another process
            return True
        finally:
            k.CloseHandle(h)
    try:
        os.kill(int(pid), 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def kill_pid_tree(pid):
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True)
    else:
        try:
            os.killpg(int(pid), signal.SIGKILL)  # workers start in their own session
        except (ProcessLookupError, PermissionError):
            pass


def kill_tree(proc):
    if proc.poll() is None:
        kill_pid_tree(proc.pid)


# ---------------------------------------------------------------------------------------------------------------
# Ledger


class Ledger:
    """Append-only JSONL of stage and worker records. A key is done once a 'done' record exists for it."""

    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.Lock()
        self.rows = read_jsonl(self.path)

    def done(self, key):
        for r in reversed(self.rows):
            if r.get("key") == key and r.get("status") == "done":
                return r
        return None

    def data(self, key):
        r = self.done(key)
        return r.get("data") if r else None

    def count(self, key, status):
        return sum(1 for r in self.rows if r.get("key") == key and r.get("status") == status)

    def mark(self, key, status, **data):
        row = {"utc": now(), "key": key, "status": status, "data": data}
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("ab") as fh:
                # A torn last line (a kill mid-write) must not swallow this record.
                if fh.tell() > 0:
                    with self.path.open("rb") as rd:
                        rd.seek(-1, os.SEEK_END)
                        if rd.read(1) != b"\n":
                            fh.write(b"\n")
                fh.write((json.dumps(row, ensure_ascii=False) + "\n").encode("utf-8"))
                fh.flush()
                os.fsync(fh.fileno())
            self.rows.append(row)
        # Test hook: simulate a kill right after a given record ("KEY:STATUS"), so resume can be tested.
        if os.environ.get("MAUDSLAY_KILL_AT") == f"{key}:{status}":
            os._exit(137)
        return row

    def once(self, key, fn):
        hit = self.done(key)
        if hit is not None:
            return hit["data"]
        self.mark(key, "started")
        t0 = time.monotonic()
        try:
            data = dict(fn() or {})
        except (Fail, Stop, Pause) as exc:
            self.mark(key, "aborted", reason=str(exc))
            raise
        data.setdefault("wall_seconds", round(time.monotonic() - t0, 3))
        self.mark(key, "done", **data)
        return data

    def worker_states(self):
        """{key: (last status, merged data)} for every worker key (pool 'started', 'launched', 'done', 'aborted')."""
        out = {}
        for r in self.rows:
            d = r.get("data") if isinstance(r.get("data"), dict) else {}
            if not (d.get("pool") or d.get("worker_launch") or d.get("worker") or r["key"] in out):
                continue
            status, merged = out.get(r["key"], (None, {}))
            out[r["key"]] = (r["status"], {**merged, **d})
        return out

    def workers(self):
        """Every finished worker record (one per launched session)."""
        return [d for s, d in self.worker_states().values() if s == "done" and d.get("worker")]


# ---------------------------------------------------------------------------------------------------------------
# Worker commands


def render_args(template, mapping):
    out = []
    for tok in template:
        for k, v in mapping.items():
            tok = tok.replace("{" + k + "}", str(v))
        out.append(tok)
    left = [t for t in out if re.search(r"\{[a-z_]+\}", t)]
    if left:
        raise Fail(f"unfilled placeholder in command: {left}")
    return out


def program_family(program):
    name = Path(str(program)).name.lower()
    for ext in (".exe", ".cmd", ".bat", ".ps1"):
        if name.endswith(ext):
            name = name[: -len(ext)]
    return name if name in ("claude", "codex") else None


def validate_worker_command(argv, family):
    """Refuse any command that reuses a session, disables the sandbox, or lacks the budget and event flags."""
    toks = [str(t) for t in argv]
    if family not in ("claude", "codex"):
        raise Fail(f"worker family {family!r} is refused for now: only claude and codex commands are accepted")
    prog = program_family(toks[0])
    if prog and prog != family:
        raise Fail(f"the program {toks[0]!r} is {prog}, but the worker is declared {family}")
    bad = [t for t in toks if t in REFUSED_TOKENS or t.startswith(("--resume=", "--continue=", "--session-id"))]
    if bad:
        raise Fail(f"worker command contains refused flags {bad}: every call is a fresh session, and codex "
                   "settings use --config, not -c")
    unsafe = [t for t in toks if t in UNSAFE_TOKENS or "danger-full-access" in t]
    if unsafe:
        raise Fail(f"worker command disables the sandbox or approvals: {unsafe}")
    if any("rollout_token_budget" in t for t in toks):
        raise Fail("rollout_token_budget does not exist in the installed Codex build; remove it")
    if family == "claude":
        for flag in ("-p", "--max-turns", "--max-budget-usd", "--output-format", "--verbose"):
            if flag not in toks:
                raise Fail(f"claude worker command lacks {flag}")
        if toks[toks.index("--output-format") + 1] != "stream-json":
            raise Fail("claude workers must use --output-format stream-json (tool calls are scanned for blinding)")
        if not toks[toks.index("--max-budget-usd") + 1]:
            raise Fail("claude worker has an empty --max-budget-usd")
    else:
        for flag in ("exec", "--json", "--ephemeral", "--skip-git-repo-check"):
            if flag not in toks:
                raise Fail(f"codex worker command lacks {flag}")
        cfg = " ".join(toks[i + 1] for i, t in enumerate(toks[:-1]) if t == "--config")
        for need in ("model_auto_compact_token_limit=", "tool_output_token_limit=", 'approval_policy="never"'):
            if need not in cfg:
                raise Fail(f"codex worker command lacks --config {need}")
    return toks


# ---------------------------------------------------------------------------------------------------------------
# Usage and events


def new_usage():
    return {"session_id": None, "is_error": False, "num_turns": None, "input": 0, "cache_read": 0, "cache_write": 0,
            "output": 0, "usd": None, "result": None, "usage_seen": False, "result_seen": False, "_msgs": {}}


def add_event(u, ev):
    """Fold one event of `claude -p --output-format stream-json` or `codex exec --json` into usage u."""
    if not isinstance(ev, dict):
        return
    t = ev.get("type")
    if t == "system" and ev.get("session_id"):
        u["session_id"] = ev["session_id"]
    elif t == "assistant" and isinstance(ev.get("message"), dict):
        msg = ev["message"]
        if isinstance(msg.get("usage"), dict) and msg.get("id") and not u["result_seen"]:
            u["_msgs"][msg["id"]] = msg["usage"]  # the last usage per message id, as bentham sessions.py does
            ms = u["_msgs"].values()
            u.update(input=sum(int(m.get("input_tokens") or 0) for m in ms),
                     cache_read=sum(int(m.get("cache_read_input_tokens") or 0) for m in ms),
                     cache_write=sum(int(m.get("cache_creation_input_tokens") or 0) for m in ms),
                     output=sum(int(m.get("output_tokens") or 0) for m in ms), usage_seen=True)
    elif t == "result":
        us = ev.get("usage") or {}
        u.update(session_id=ev.get("session_id") or u["session_id"], is_error=bool(ev.get("is_error")),
                 num_turns=ev.get("num_turns"), usd=ev.get("total_cost_usd"), result=ev.get("result"),
                 result_seen=True)
        if us:
            u.update(input=int(us.get("input_tokens") or 0), cache_read=int(us.get("cache_read_input_tokens") or 0),
                     cache_write=int(us.get("cache_creation_input_tokens") or 0),
                     output=int(us.get("output_tokens") or 0), usage_seen=True)
    elif t == "thread.started":
        u["session_id"] = ev.get("thread_id") or u["session_id"]
    elif t == "turn.completed" and isinstance(ev.get("usage"), dict):
        us = ev["usage"]
        cached = int(us.get("cached_input_tokens") or 0)
        u["cache_read"] += cached
        u["input"] += max(int(us.get("input_tokens") or 0) - cached, 0)
        u["output"] += int(us.get("output_tokens") or 0)
        u["num_turns"] = (u["num_turns"] or 0) + 1
        u.update(usage_seen=True, result_seen=True)
    elif t in ("turn.failed", "error"):
        u["is_error"] = True
    elif t == "item.completed" and isinstance(ev.get("item"), dict) and ev["item"].get("type") == "agent_message":
        u["result"] = ev["item"].get("text")


def parse_usage(text):
    u = new_usage()
    for line in text.splitlines():
        try:
            add_event(u, json.loads(line))
        except ValueError:
            continue
    return u


def tokens(u):
    return int(u.get("input") or 0) + int(u.get("cache_read") or 0) + int(u.get("cache_write") or 0) + int(u.get("output") or 0)


def price(u, prices):
    if u.get("usd") is not None:
        return float(u["usd"])
    if not prices or any(not isinstance(prices.get(k), (int, float)) for k in ("input", "cached_input", "output")):
        return None
    return ((u.get("input") or 0) * prices["input"] + (u.get("cache_read") or 0) * prices["cached_input"]
            + (u.get("cache_write") or 0) * prices.get("cache_write", prices["input"])
            + (u.get("output") or 0) * prices["output"]) / 1e6


def _strings(v):
    if isinstance(v, str):
        return [v]
    if isinstance(v, dict):
        return [s for x in v.values() for s in _strings(x)]
    if isinstance(v, list):
        return [s for x in v for s in _strings(x)]
    return []


def tool_strings(ev):
    """The arguments of every tool call in one event (claude tool_use inputs; codex commands and file paths)."""
    if not isinstance(ev, dict):
        return []
    if ev.get("type") == "assistant" and isinstance(ev.get("message"), dict):
        return [s for b in ev["message"].get("content") or [] if isinstance(b, dict) and b.get("type") == "tool_use"
                for s in _strings(b.get("input"))]
    if ev.get("type") in ("item.started", "item.updated", "item.completed") and isinstance(ev.get("item"), dict):
        it = ev["item"]
        if it.get("type") in ("agent_message", "reasoning"):
            return []
        return [s for k in ("command", "path", "changes", "arguments", "query") for s in _strings(it.get(k))]
    return []


def path_forms(p):
    p = Path(p).resolve().as_posix().lower()
    return sorted({p, bash_path(p).lower()})


def scan(strings, rules):
    """Violations: a tool argument naming a forbidden path. rules: [(prefix forms, allowed tail regex|None, label)]."""
    out = []
    for s in strings:
        n = re.sub(r"/+", "/", s.replace("\\", "/").lower())
        for forms, allow, label in rules:
            for f in forms:
                start = 0
                while True:
                    i = n.find(f, start)
                    if i < 0:
                        break
                    start = i + 1
                    tail = PATH_TAIL.match(n, i + len(f)).group(0)
                    if tail and not tail.startswith("/"):
                        continue  # a longer, different name that merely starts with the prefix
                    if allow is None or not allow.match(tail.rstrip("/")):
                        out.append(f"{label}: {s[:200]}")
    return sorted(set(out))


# ---------------------------------------------------------------------------------------------------------------
# Planted controls (Cujas plant.py / Papinian review_prep.py)


def _shift(d):
    if not isinstance(d, str) or len(d) < 10 or not d[:4].isdigit():
        return d
    md = d[4:10]
    md = "-02-28" if md == "-02-29" else md
    return f"{int(d[:4]) - 3:04d}{md}{d[10:]}"


def _has_end(c):
    we = c.get("whole_order_end")
    return (isinstance(we, dict) and bool(we.get("date"))) or any(
        isinstance(x.get("first_end"), dict) and x["first_end"].get("date") for x in c.get("operative_clauses", []))


def _has_event(c):
    return any(isinstance(e, dict) and (e.get("effective_date") or e.get("date"))
               for x in c.get("operative_clauses", []) for e in x.get("later_events", []))


def plant_one(c, mode):
    p = copy.deepcopy(c)
    n = 0
    if mode == "end":
        we = p.get("whole_order_end")
        if isinstance(we, dict) and we.get("date"):
            we["date"] = _shift(we["date"]); n += 1
        for x in p.get("operative_clauses", []):
            fe = x.get("first_end")
            if isinstance(fe, dict) and fe.get("date"):
                fe["date"] = _shift(fe["date"]); n += 1
    elif mode == "event":
        for x in p.get("operative_clauses", []):
            for e in x.get("later_events", []):
                for k in ("effective_date", "date"):
                    if isinstance(e, dict) and e.get(k):
                        e[k] = _shift(e[k]); n += 1
    else:
        def walk(o):
            nonlocal n
            if isinstance(o, dict):
                for k in list(o):
                    if k == "signing_date" and isinstance(o[k], str):
                        o[k] = _shift(o[k]); n += 1
                    else:
                        walk(o[k])
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(p)
    return p, n


DEFECT = {"end": "every first_end and whole_order_end date moved back three years",
          "event": "every later_events effective date moved back three years",
          "signing": "every signing_date of the order moved back three years"}


def plant_controls(claims, salt):
    """Pick max(1, round(n/15)) claims with a secret salt and plant a date defect. Returns (review set, key)."""
    elig, mode = [c for c in claims if _has_end(c)], "end"
    if not elig:
        elig, mode = [c for c in claims if _has_event(c)], "event"
    if not elig:
        elig, mode = list(claims), "signing"
    n = max(1, round(len(claims) / 15))
    rng = random.Random(hashlib.sha256(("maudslay-controls:" + salt).encode()).hexdigest())
    picks = {c["instrument_id"] for c in rng.sample(sorted(elig, key=lambda c: c["instrument_id"]), min(n, len(elig)))}
    out, controls = [], []
    for c in claims:
        if c["instrument_id"] in picks:
            p, k = plant_one(c, mode)
            if not k:
                raise Fail(f"cannot plant a date control on {c['instrument_id']}: no date to move")
            out.append(p)
            controls.append({"instrument_id": c["instrument_id"], "planted": canon(p), "genuine": canon(c),
                             "defect": DEFECT[mode], "type": "date_shift_" + mode})
        else:
            out.append(c)
    return out, controls


def caught(rec):
    """Rule fixed in advance: the arm rejected the version, and a whole word or field name in its `defects` names a
    date. Reasons are not read, and no substring of a longer word ("mandate", "update") counts."""
    if not rec or rec.get("verdict") != "rejected":
        return False
    text = json.dumps(rec.get("defects") or [], ensure_ascii=False).lower()
    return bool(set(re.findall(r"[a-z_]+", text)) & DATE_TERMS)


# ---------------------------------------------------------------------------------------------------------------
# The batch


class Batch:
    def __init__(self, cfg, repo):
        self.cfg = cfg
        self.repo = Path(repo).resolve()
        self.dir = (self.repo / cfg["run_dir"] / cfg["batch"]).resolve()
        if not self.dir.is_relative_to(self.repo):
            raise Fail("the batch folder must be inside the repository")
        self.packet = self.dir / "packet"
        self.name = cfg["batch"]
        self.scratch = Path(cfg["scratch_root"]).resolve()
        self.keys = Path(cfg["keys_dir"]).resolve()
        for label, p in (("--scratch-root", self.scratch), ("--keys-dir", self.keys)):
            if p.is_relative_to(self.repo) or self.repo.is_relative_to(p):
                raise Fail(f"{label} must be outside the repository (workers and control material stay out of it)")
        if self.keys.is_relative_to(self.scratch / "workers"):
            raise Fail("--keys-dir must not be inside the workers' folders")
        self.ledger = Ledger(self.dir / "LEDGER.jsonl")
        self.tools = dict(DEFAULT_TOOLS)
        if cfg.get("tools"):
            self.tools.update(read_json(cfg["tools"], {}) or {})
        self.workers = load_workers(cfg["workers"])
        self.spend_lock = threading.Lock()
        self.live, self.live_lock = {}, threading.Lock()
        if cfg.get("batch_usd") is None:
            raise Fail("--batch-usd is required")
        self.check_workers()

    # -- helpers -------------------------------------------------------------------------------------------
    def rel(self, p):
        return Path(p).resolve().relative_to(self.repo).as_posix()

    def tool(self, name, args=(), log=None, **mapping):
        base = {"python": sys.executable, "repo": self.repo.as_posix(), "packet": self.packet.as_posix(),
                "action": self.cfg["action"]}
        base.update({k: (v.as_posix() if isinstance(v, Path) else v) for k, v in mapping.items()})
        argv = render_args(self.tools[name], base) + [str(a.as_posix() if isinstance(a, Path) else a) for a in args]
        logs = self.dir / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        log = log or name
        t0 = time.monotonic()
        p = subprocess.run(argv, cwd=self.repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
        (logs / f"{log}.out").write_text(p.stdout or "", encoding="utf-8")
        (logs / f"{log}.err").write_text(p.stderr or "", encoding="utf-8")
        with (logs / "TOOLS.log").open("a", encoding="utf-8") as fh:
            fh.write(f"{now()} {log} exit {p.returncode} {round(time.monotonic() - t0, 2)}s {' '.join(argv[:8])}\n")
        return p.returncode, p.stdout or ""

    def cap(self, role, kind):
        """Per-worker cap: the role's own item_usd / item_tokens in the workers file, else the batch-wide one."""
        w = self.workers.get(role) or {}
        v = w.get(f"item_{kind}")
        return v if v is not None else self.cfg.get(f"item_{kind}")

    def command(self, role, folder):
        w = self.workers[role]
        mapping = {"model": w["model"], "max_turns": w.get("max_turns", 80), "repo": self.repo.as_posix(),
                   "cwd": Path(folder).as_posix(), "item_usd": self.cap(role, "usd"),
                   "auto_compact_tokens": w.get("auto_compact_tokens", 120000),
                   "tool_output_tokens": w.get("tool_output_tokens", 6000),
                   "writable_roots": json.dumps([Path(folder).as_posix()]),
                   "network": "true" if w.get("network") else "false"}
        return validate_worker_command(render_args(w["command"], mapping), w["family"])

    def check_workers(self):
        for role, w in self.workers.items():
            if w["family"] not in ("claude", "codex"):
                raise Fail(f"{role}: worker family {w['family']!r} is refused for now (claude or codex only)")
            if self.cap(role, "usd") is None:
                raise Fail(f"{role}: needs an item dollar cap (--item-usd or item_usd in the workers file)")
            if w["family"] == "codex":
                if self.cap(role, "tokens") is None:
                    raise Fail(f"{role}: a codex worker needs an item token cap (--item-tokens or item_tokens)")
                pr = w.get("prices_usd_per_mtok") or {}
                if any(not isinstance(pr.get(k), (int, float)) for k in ("input", "cached_input", "output")):
                    raise Fail(f"{role}: a codex worker needs prices_usd_per_mtok (input, cached_input, output)")
            self.command(role, self.scratch / "workers" / "CHECK")

    def spent(self):
        """(usd, tokens) for budget checks. A running or unfinished worker counts at its item caps; a codex worker
        always counts at least its item dollar cap; a worker with unknown dollars counts at its cap."""
        usd = tok = 0.0
        for status, d in self.ledger.worker_states().values():
            role = d.get("role")
            cu, ct = float(self.cap(role, "usd") or 0), float(self.cap(role, "tokens") or 0)
            if status in ("started", "launched"):
                usd, tok = usd + cu, tok + ct
            elif status == "done":
                u = d.get("usd")
                if d.get("family") == "codex":
                    u = max(float(u or 0), cu)
                usd += cu if u is None else float(u)
                tok += d.get("tokens") or 0
        return usd, tok

    def measured_usd(self):
        return round(sum(float(w["usd"]) if w.get("usd") is not None else float(self.cap(w.get("role"), "usd") or 0)
                         for w in self.ledger.workers()), 4)

    def budget_reason(self, role):
        usd, tok = self.spent()
        cu, ct = float(self.cap(role, "usd") or 0), self.cap(role, "tokens")
        bu, bt = float(self.cfg["batch_usd"]), self.cfg.get("batch_tokens")
        if usd + cu > bu + 1e-9:
            return f"batch_budget: committed ${usd:.2f} + next {role} cap ${cu:.2f} > ${bu:.2f}"
        if bt is not None and tok + float(ct or 0) > bt:
            return f"batch_token_budget: {int(tok)} + {int(ct or 0)} > {int(bt)}"
        return None

    def rules_for(self, role, folder):
        own = re.escape(Path(folder).name.lower())
        rules = [(path_forms(self.scratch), re.compile(rf"^/workers/{own}(/.*)?$"), "outside its own folder"),
                 (path_forms(self.keys), None, "control folder")]
        if role.startswith("reviewer"):
            batch = path_forms(self.dir) + [self.rel(self.dir).lower()]
            rules.append((batch, re.compile(r"^/packet(/packet\.json)?$"), "batch material"))
        return rules

    # -- workers ------------------------------------------------------------------------------------------
    def run_worker(self, item, stage):
        key, label, role = item["key"], item["label"], item["role"]
        folder = self.scratch / "workers" / label
        k = 1
        while folder.exists():
            k += 1
            folder = self.scratch / "workers" / f"{label}.{k}"
        folder.mkdir(parents=True)
        if item.get("setup"):
            item["setup"](folder)
        prompt = item["render"](folder)
        if len(prompt) > int(self.cfg["prompt_cap_chars"]):
            raise Fail(f"{label}: prompt of {len(prompt)} chars exceeds the cap")
        (folder / "PROMPT.txt").write_text(prompt, encoding="utf-8")
        (self.dir / "prompts").mkdir(parents=True, exist_ok=True)
        (self.dir / "prompts" / f"{label}.txt").write_text(prompt, encoding="utf-8")
        argv = self.command(role, folder)
        exe = shutil.which(argv[0])
        if exe:
            argv[0] = exe
        outd = self.scratch / "out"
        outd.mkdir(parents=True, exist_ok=True)
        out_path, err_path = outd / f"{folder.name}.out", outd / f"{folder.name}.err"
        env = {k_: v for k_, v in os.environ.items() if k_ != "CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD"}
        kw = {} if os.name == "nt" else {"start_new_session": True}
        t0, started, epoch = time.monotonic(), now(), time.time()
        try:
            # The worker writes its events straight to a file, so a conveyor crash never loses a finished result.
            with open(folder / "PROMPT.txt", "rb") as stdin, open(out_path, "wb") as out, open(err_path, "wb") as err:
                proc = subprocess.Popen(argv, cwd=folder, stdin=stdin, stdout=out, stderr=err, env=env, **kw)
        except OSError as exc:
            raise Fail(f"cannot launch worker {label}: {exc}")
        with self.live_lock:
            self.live[key] = proc
        try:
            self.ledger.mark(key, "launched", worker_launch=True, label=label, role=role, stage=stage, pid=proc.pid,
                             launched_epoch=epoch, started_utc=started, folder=folder.as_posix(),
                             out=out_path.as_posix())
            text, killed = self.watch(proc, out_path, role, folder, t0)
        finally:
            with self.live_lock:
                self.live.pop(key, None)
        return self.record(label, role, stage, folder, out_path, text, proc.returncode, killed, started,
                           round(time.monotonic() - t0, 3), len(prompt), argv)

    def watch(self, proc, out_path, role, folder, t0):
        """Follow the worker's event file; kill it on a blinding violation, the item token cap or the timeout."""
        u, rules, killed, chunks, buf = new_usage(), self.rules_for(role, folder), None, [], b""
        cap_tok = self.cap(role, "tokens")
        timeout = self.workers[role].get("item_timeout", self.cfg.get("item_timeout"))
        with open(out_path, "rb") as fh:
            while True:
                data = fh.read()
                if data:
                    chunks.append(data)
                    buf += data
                    *lines, buf = buf.split(b"\n")
                    for line in lines:
                        try:
                            ev = json.loads(line)
                        except ValueError:
                            continue
                        add_event(u, ev)
                        bad = scan(tool_strings(ev), rules)
                        if bad and not killed:
                            killed = "blinding: " + bad[0]
                            kill_tree(proc)
                    if cap_tok and tokens(u) > cap_tok and not killed:
                        killed = f"item_token_cap {tokens(u)} > {cap_tok}"
                        kill_tree(proc)
                    continue
                if proc.poll() is not None:
                    break
                if timeout and time.monotonic() - t0 > float(timeout) and not killed:
                    killed = f"item_timeout {timeout}s"
                    kill_tree(proc)
                time.sleep(0.1)
        proc.wait()
        return b"".join(chunks).decode("utf-8", "replace"), killed

    def record(self, label, role, stage, folder, out_path, text, rc, killed, started, wall, prompt_chars, argv):
        w = self.workers[role]
        u = parse_usage(text)
        violations = []
        for line in text.splitlines():
            try:
                violations += scan(tool_strings(json.loads(line)), self.rules_for(role, folder))
            except ValueError:
                pass
        usd = price(u, w.get("prices_usd_per_mtok"))
        rec = {"worker": True, "label": label, "stage": stage, "role": role, "family": w["family"],
               "model": w["model"], "model_family": w.get("model_family"), "session_id": u["session_id"],
               "exit": rc, "is_error": u["is_error"], "killed": killed, "num_turns": u["num_turns"],
               "input": u["input"], "cache_read": u["cache_read"], "cache_write": u["cache_write"],
               "output": u["output"], "tokens": tokens(u), "usd": usd, "usage_reported": u["usage_seen"],
               "result_seen": u["result_seen"], "blinding_violations": sorted(set(violations)),
               "started_utc": started, "ended_utc": now(), "wall_seconds": wall, "prompt_chars": prompt_chars,
               "folder": Path(folder).as_posix(), "out": Path(out_path).as_posix(),
               "argv": [Path(argv[0]).name] + list(argv[1:]) if argv else None}
        over = []
        ct, cu = self.cap(role, "tokens"), self.cap(role, "usd")
        if ct and rec["tokens"] > ct:
            over.append(f"tokens {rec['tokens']} > {ct}")
        if cu is not None and usd is not None and usd > float(cu) * 1.0001:
            over.append(f"usd {usd:.4f} > {cu}")
        rec["over_item_cap"] = "; ".join(over) or None
        rec["ok"] = (rc in (0, None)) and not u["is_error"] and not killed and u["result_seen"] and not violations
        with self.spend_lock, (self.dir / "COSTS.log").open("a", encoding="utf-8") as fh:
            # The carnot-coordinator/worker.py cost line, read by `bentham.py usage --reported-costs`.
            fh.write(f"{label} launched {started}\n")
            if u["session_id"] and usd is not None:
                fh.write(f"{label} {u['session_id']} cost {usd} turns {u['num_turns']} ms {int((wall or 0) * 1000)}\n")
            fh.write(f"{label} {'done' if rec['ok'] else 'failed'} {rec['ended_utc']}\n")
        return rec

    def reap(self):
        """On (re)start: kill workers a dead conveyor left running, adopt finished ones, and close the rest."""
        for key, (status, d) in self.ledger.worker_states().items():
            if status not in ("started", "launched"):
                continue
            killed = None
            if status == "launched" and pid_alive(d.get("pid"), d.get("launched_epoch")):
                kill_pid_tree(d["pid"])
                for _ in range(100):
                    if not pid_alive(d["pid"], d.get("launched_epoch")):
                        break
                    time.sleep(0.1)
                killed = "orphan worker still running at resume; killed"
            text = ""
            if status == "launched" and d.get("out"):
                try:
                    text = Path(d["out"]).read_text(encoding="utf-8", errors="replace")
                except OSError:
                    text = ""
            if status == "launched" and not killed and d.get("role") in self.workers and parse_usage(text)["result_seen"]:
                rec = self.record(d["label"], d["role"], d.get("stage"), d["folder"], d["out"], text, None, None,
                                  d.get("started_utc"), None, None, None)
                rec["adopted"] = True
                self.ledger.mark(key, "done", **rec)
                continue
            role = d.get("role")
            self.ledger.mark(key, "done", worker=True, orphaned=True, ok=False, label=d.get("label"), role=role,
                             stage=d.get("stage"), family=(self.workers.get(role) or {}).get("family"),
                             model=(self.workers.get(role) or {}).get("model"), usd=None, tokens=0,
                             folder=d.get("folder"), out=d.get("out"),
                             killed=killed or "the conveyor stopped before this worker finished")

    def kill_all(self):
        with self.live_lock:
            procs = list(self.live.values())
        for p in procs:
            kill_tree(p)

    def latest(self, key):
        """(key of the newest attempt, its done record or None). Attempts after the first are KEY#2, KEY#3 ..."""
        n = 1
        while any(r.get("key") == f"{key}#{n + 1}" for r in self.ledger.rows):
            n += 1
        k = key if n == 1 else f"{key}#{n}"
        return k, self.ledger.data(k)

    def pool(self, items, stage, retry_failed=False):
        """Run worker items concurrently, capped, with the batch budget checked before every launch.

        items: [{"key", "label", "role", "id", "render": fn(folder), "setup": fn(folder)}]; returns {id: record}.
        A finished worker is not relaunched, except an orphaned one (always) or a failed one when retry_failed;
        a worker that broke blinding is never relaunched."""
        results, pending = {}, []
        for it in items:
            k, rec = self.latest(it["key"])
            if rec is not None and (rec.get("ok") or rec.get("blinding_violations")
                                    or (not rec.get("orphaned") and not retry_failed)):
                results[it["id"]] = rec
                continue
            if rec is not None:
                n = int(k.split("#")[1]) + 1 if "#" in k else 2
                k = f"{it['key']}#{n}"
            pending.append(dict(it, key=k, label=it["label"] + (f"-a{k.split('#')[1]}" if "#" in k else "")))
        stop = None
        parallel = max(1, int(self.cfg.get("parallel") or 1))
        ex = cf.ThreadPoolExecutor(max_workers=parallel)
        running = {}
        try:
            while pending or running:
                while pending and len(running) < parallel and stop is None:
                    stop = self.budget_reason(pending[0]["role"])
                    if stop:
                        break
                    it = pending.pop(0)
                    # Recorded before launch, so the next budget check already counts this worker at its cap.
                    self.ledger.mark(it["key"], "started", pool=True, label=it["label"], role=it["role"], stage=stage)
                    running[ex.submit(self.run_worker, it, stage)] = it
                if not running:
                    break
                done, _ = cf.wait(running, return_when=cf.FIRST_COMPLETED)
                for f in done:
                    it = running.pop(f)
                    try:
                        rec = f.result()
                    except Fail as exc:
                        self.ledger.mark(it["key"], "aborted", reason=str(exc))
                        raise
                    self.ledger.mark(it["key"], "done", **rec)
                    results[it["id"]] = rec
        except BaseException:
            self.kill_all()  # never leave a worker tree running behind a failed batch
            raise
        finally:
            ex.shutdown(wait=True)
        if stop:
            raise Stop(f"{stage}: {stop}; {len(pending)} worker(s) not launched")
        return results

    # -- stages -------------------------------------------------------------------------------------------
    def reserve(self):
        if self.cfg.get("ids"):
            return {"ids": list(self.cfg["ids"]), "via": "explicit --ids (no kit next reservation)"}
        saved = self.dir / "RESERVED.json"
        rows = read_json(saved)
        if not isinstance(rows, list):
            if self.ledger.count("reserve", "started") - self.ledger.count("reserve", "aborted") > 1:
                raise Fail("an earlier run may have reserved orders with kit next, but RESERVED.json is missing; "
                           "kit next is not called twice. Check research/readiness/CLAIM_KIT_LOCK.json, release or "
                           "reuse those orders, and start a new batch")
            rc, out = self.tool("kit", ["next", "--agent", self.cfg["agent"], "--action", self.cfg["action"],
                                        "--n", self.cfg["n"]], log="reserve")
            try:
                rows = json.loads(out)
            except ValueError:
                rows = None
            if isinstance(rows, list):
                write_json(saved, rows)  # atomically, before anything else can fail
            if rc or not isinstance(rows, list):
                raise Fail(f"kit next failed (exit {rc}); see {self.rel(self.dir / 'logs/reserve.err')}")
        ids = [r["instrument_id"] for r in rows]
        if not ids:
            raise Stop("reserve: kit next reserved no orders under this action")
        return {"ids": ids, "via": "kit next"}

    def prepare(self, ids):
        if self.packet.exists():
            move_aside(self.packet, "packet.incomplete")
        args = ["prepare", *ids, "--agent", self.cfg["agent"], "--action", self.cfg["action"], "--write", self.packet]
        if self.cfg.get("replacement_proposal"):
            args.append("--replacement-proposal")
        rc, _ = self.tool("kit", args, log="prepare")
        dc = read_json(self.packet / "DISPATCH_CHECK.json")
        if not (self.packet / "PACKET.json").exists() or not isinstance(dc, dict):
            raise Fail(f"kit prepare wrote no packet (exit {rc}); see {self.rel(self.dir / 'logs/prepare.err')}")
        lrc, _ = self.tool("lookups", log="lookups")
        (self.packet / "views").mkdir(exist_ok=True)
        views = {}
        for iid in ids:
            out = self.packet / "views" / f"{slug(iid)}.json"
            vrc, _ = self.tool("view", log=f"view-{slug(iid)}", iid=iid, out=out)
            views[iid] = self.rel(out) if vrc == 0 and out.exists() else None
        prep = self.dir / "prepared"
        prep.mkdir(exist_ok=True)
        for name in ("decisions.csv", "clauses.csv", "RATIONALES.json"):
            shutil.copyfile(self.packet / name, prep / name)
        return {"prepare_exit": rc, "lookups_exit": lrc, "views": views,
                "dispatchable": list(dc.get("dispatchable_ids") or []),
                "source_blocked": list(dc.get("source_blocked_ids") or [])}

    def dispatch(self, targets):
        k = 1
        while (self.packet / f"dispatch-v{k}.json").exists():
            k += 1
        receipt = self.packet / f"dispatch-v{k}.json"
        args = ["dispatch-check", self.packet] + [x for i in targets for x in ("--order", i)] + ["--write", receipt]
        rc, _ = self.tool("kit", args, log=f"dispatch-v{k}")
        d = read_json(receipt, {}) or {}
        if rc:
            raise Stop(f"dispatch: kit dispatch-check exit {rc} just before producers ({self.rel(receipt)}); "
                       "the packet or a source changed")
        return {"receipt": self.rel(receipt), "dispatchable": d.get("dispatchable_ids", targets)}

    def view_header(self, iid, view_rel):
        v = read_json(self.repo / view_rel, {}) or {}
        keep = {k: v.get(k) for k in ("instrument_id", "title", "signing_date", "whole_order_status",
                                      "view_bytes", "approx_view_tokens") if k in v}
        b = v.get("own_text_boundary")
        if isinstance(b, dict):
            keep["own_text_verified_whole_order"] = b.get("verified_whole_order")
        if isinstance(v.get("missing"), list):
            keep["missing_count"] = len(v["missing"])
        if keep.get("instrument_id") not in (None, iid):
            raise Fail(f"view for {iid} names {keep.get('instrument_id')}")
        return json.dumps(keep, ensure_ascii=False)

    def producer_prompt(self, iid, view_rel, folder, extra=""):
        t = (PROMPTS / "producer.txt").read_text(encoding="utf-8")
        route = Path(self.cfg["route"])
        route = route if route.is_absolute() else self.repo / route
        sub = {"<<REPO>>": self.repo.as_posix(), "<<REPO_BASH>>": bash_path(self.repo), "<<ORDER>>": iid,
               "<<SLUG>>": slug(iid), "<<VIEW>>": view_rel, "<<PACKET>>": self.rel(self.packet),
               "<<WORK>>": Path(folder).as_posix(), "<<AGENT>>": self.cfg["agent"], "<<ROUTE_NAME>>": route.stem,
               "<<ROUTE>>": route.read_text(encoding="utf-8").strip(),
               "<<VIEW_HEADER>>": self.view_header(iid, view_rel), "<<RUN>>": self.rel(self.dir.parent),
               "<<SCRATCH_ROOT>>": self.scratch.as_posix()}
        for k, v in sub.items():
            t = t.replace(k, v)
        return t + extra

    def render(self, targets, views):
        cap = int(self.cfg["prompt_cap_chars"])
        ok, over, sizes = [], {}, {}
        for iid in targets:
            text = self.producer_prompt(iid, views[iid], self.scratch / "workers" / f"{self.name}-produce-{slug(iid)}")
            sizes[iid] = len(text)
            if len(text) > cap:
                over[iid] = len(text)
                continue
            ok.append(iid)
        return {"rendered": ok, "over_cap": over, "cap_chars": cap, "prompt_chars": sizes}

    def seed_sheet(self, iid, folder, source=None):
        """A producer's folder: this order's prepared rows, or (for a repair) the sheet as it last stood."""
        if source:
            for name in ("decisions.csv", "clauses.csv", "RATIONALES.json", "ASSESSMENT.json", "REPORT.md"):
                if (Path(source) / name).exists():
                    shutil.copyfile(Path(source) / name, folder / name)
            return
        for name in ("decisions.csv", "clauses.csv"):
            fields, rows = read_csv(self.dir / "prepared" / name)
            write_csv(folder / name, fields, [r for r in rows if r.get("instrument_id") == iid])
        (folder / "RATIONALES.json").write_text("{}\n", encoding="utf-8")

    def produce_round(self, rnd, iids, views, folders, errors=None):
        items = []
        cap = int(self.cfg["prompt_cap_chars"])
        for iid in iids:
            def render(folder, iid=iid):
                if not errors:
                    return self.producer_prompt(iid, views[iid], folder)
                err = json.dumps(errors.get(iid, []), ensure_ascii=False)
                room = cap - len(self.producer_prompt(iid, views[iid], folder)) - 900
                if len(err) > max(room, 200):
                    err = err[:max(room, 200)] + " ...(cut)"
                extra = ((PROMPTS / "repair.txt").read_text(encoding="utf-8")
                         .replace("<<ROUND>>", str(rnd)).replace("<<ORDER>>", iid).replace("<<ERRORS>>", err))
                return self.producer_prompt(iid, views[iid], folder, "\n\n" + extra)
            tag = "produce" if rnd == 0 else f"repair{rnd}"
            items.append({"key": f"{tag}:{slug(iid)}", "label": f"{self.name}-{tag}-{slug(iid)}", "role": "producer",
                          "id": iid, "render": render,
                          "setup": lambda folder, iid=iid: self.seed_sheet(iid, folder, folders.get(iid) if rnd else None)})
        return self.pool(items, "produce" if rnd == 0 else "repair")

    @staticmethod
    def produced_map(results):
        out = {}
        for iid, rec in results.items():
            if rec.get("over_item_cap"):
                out[iid] = {"reason": f"worker over the item cap ({rec['over_item_cap']}); sheet held, not used"}
            elif rec.get("blinding_violations"):
                out[iid] = {"reason": f"worker named a forbidden path ({rec['blinding_violations'][0]}); not used"}
            elif not rec.get("ok"):
                out[iid] = {"reason": f"worker did not finish (exit {rec.get('exit')}, {rec.get('killed') or 'error'})"}
            else:
                out[iid] = {"folder": rec["folder"]}
        return out

    def validate_sheet(self, iid, folder):
        """(decision row, clause rows, rationales, assessment) from a producer folder, or raise ValueError."""
        work = Path(folder)
        pf, prows = read_csv(self.dir / "prepared" / "decisions.csv")
        cf_, _ = read_csv(self.dir / "prepared" / "clauses.csv")
        prep = next(r for r in prows if r["instrument_id"] == iid)
        f, rows = read_csv(work / "decisions.csv")
        if f != pf:
            raise ValueError("decisions.csv header changed")
        if len(rows) != 1 or rows[0].get("instrument_id") != iid:
            raise ValueError("decisions.csv must hold exactly one row, for this order")
        row = rows[0]
        if row.get("dossier_sha256") != prep.get("dossier_sha256"):
            raise ValueError("dossier_sha256 differs from the prepared row")
        if row.get("outcome") not in OUTCOMES:
            raise ValueError(f"outcome {row.get('outcome')!r} is not one of {OUTCOMES}")
        f2, crows = read_csv(work / "clauses.csv")
        if f2 != cf_:
            raise ValueError("clauses.csv header changed")
        if any(c.get("instrument_id") != iid for c in crows):
            raise ValueError("clauses.csv holds a row for another order")
        rat = read_json(work / "RATIONALES.json")
        if not isinstance(rat, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in rat.items()):
            raise ValueError("RATIONALES.json must be an object of strings")
        bad = [k for k in rat if not k.startswith(slug(iid) + ".")]
        if bad:
            raise ValueError(f"rationale keys must start with {slug(iid)}.: {bad[:3]}")
        shared = read_json(self.dir / "prepared" / "RATIONALES.json", {}) or {}
        for v in list(row.values()) + [x for c in crows for x in c.values()]:
            if isinstance(v, str) and v.startswith("@rationale:"):
                key = v.split(":", 1)[1]
                if key not in rat and key not in shared:
                    raise ValueError(f"undefined rationale {key}")
        assess = read_json(work / "ASSESSMENT.json")
        if assess is not None and (not isinstance(assess, dict) or assess.get("id") not in (None, iid)):
            raise ValueError("ASSESSMENT.json must be one object for this order")
        return row, crows, rat, assess

    def collect(self, prep, produced, demoted):
        """Rebuild the packet's sheets from the prepared copies plus every valid per-order sheet."""
        df, drows = read_csv(self.dir / "prepared" / "decisions.csv")
        cfields, crows = read_csv(self.dir / "prepared" / "clauses.csv")
        rat = read_json(self.dir / "prepared" / "RATIONALES.json", {}) or {}
        notes, sheets, assess = {}, {}, []
        blocked = set(prep["source_blocked"])
        for r in drows:
            iid = r["instrument_id"]
            note = None
            p = produced.get(iid) or {}
            if iid in blocked:
                note = "dispatch check: a mandatory source is not held; no producer was launched"
                r["outcome"] = "blocked"
            elif p.get("folder"):
                try:
                    sheets[iid] = self.validate_sheet(iid, p["folder"])
                except (ValueError, OSError, StopIteration) as exc:
                    note = f"producer sheet invalid: {exc}"
            else:
                note = p.get("reason") or "no producer sheet (not dispatched)"
            if iid in sheets:
                row, _, srat, a = sheets[iid]
                for k, v in srat.items():
                    if k in rat and rat[k] != v:
                        raise Fail(f"rationale key collision {k}")
                    rat[k] = v
                r.clear()
                r.update(row)
                if a is not None:
                    assess.append(dict(a, id=iid))
                if iid in demoted:
                    note = demoted[iid]
            if note:
                # The conveyor never submits for a producer: an order without a usable sheet stays not submitted.
                if r.get("outcome") == "submit":
                    r["outcome"] = "unresolved"
                notes[iid] = note
                r["unresolved_material_gaps"] = json.dumps(json_list(r.get("unresolved_material_gaps")) + [note],
                                                           ensure_ascii=False)
        out_c = [c for c in crows if c["instrument_id"] not in sheets]
        for r in drows:
            if r["instrument_id"] in sheets:
                out_c += sheets[r["instrument_id"]][1]
        write_csv(self.packet / "decisions.csv", df, drows)
        write_csv(self.packet / "clauses.csv", cfields, out_c)
        (self.packet / "RATIONALES.json").write_text(json.dumps(rat, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        if assess:
            write_jsonl(self.packet / "ASSESSMENT.jsonl", assess)
        submit = [r["instrument_id"] for r in drows if r.get("outcome") == "submit"]
        fp = hashlib.sha256(b"".join((self.packet / n).read_bytes()
                                     for n in ("decisions.csv", "clauses.csv", "RATIONALES.json"))).hexdigest()
        return {"submit": submit, "not_used": notes, "sheets_fingerprint": fp}

    def apply_and_check(self, fp):
        key = f"apply:{fp[:16]}"
        hit = self.ledger.data(key)
        if hit and (self.repo / hit["applied"]).exists():
            return hit

        def go():
            k = 1
            while (self.packet / f"applied-v{k}").exists():
                k += 1
            applied = self.packet / f"applied-v{k}"
            arc, _ = self.tool("kit", ["apply", self.packet, "--write", applied], log=f"apply-v{k}")
            audit = read_json(applied / "AUDIT.json")
            if not isinstance(audit, list):
                raise Fail(f"kit apply wrote no AUDIT.json (exit {arc}); see logs/apply-v{k}.err")
            fails = {r["instrument_id"]: r.get("errors") for r in audit if r.get("errors")}
            ssc = read_json(applied / "SELECTED_SOURCE_CHECK.json", {}) or {}
            for m in ssc.get("members", []) if isinstance(ssc, dict) else []:
                if m.get("blockers"):
                    fails.setdefault(m["instrument_id"], []).extend(
                        [b.get("kind", "source blocker") for b in m["blockers"]])
            claims = read_jsonl(applied / "CLAIMS.proposed.jsonl")
            crc = None
            if claims:
                # batch-check runs even when apply rejected some members, so one repair round sees every failure.
                crc, _ = self.tool("kit", ["batch-check", self.packet, applied], log=f"batch-check-v{k}")
                summ = read_json(applied / "CHECK_SUMMARY.json")
                if not isinstance(summ, dict):
                    raise Fail(f"kit batch-check wrote no CHECK_SUMMARY.json (exit {crc})")
                for f in summ.get("actionable_failures", []):
                    fails.setdefault(f.get("instrument_id"), []).extend(
                        (f.get("errors") or []) + (f.get("mechanical_failures") or []) + (f.get("unverified") or []))
                if crc and not fails:
                    raise Fail(f"kit batch-check exit {crc} without per-order failures; see logs/batch-check-v{k}.err")
            elif arc and not fails:
                raise Fail(f"kit apply exit {arc} without per-order failures; see logs/apply-v{k}.err")
            return {"applied": self.rel(applied), "apply_exit": arc, "check_exit": crc,
                    "failures": {k2: [str(e) for e in (v or [])][:20] for k2, v in fails.items()},
                    "claims": len(claims)}
        return self.ledger.once(key, go)

    # -- review -------------------------------------------------------------------------------------------
    def reviewer_name(self, arm):
        return f"maudslay-blind-reviewer-{self.name}-{arm}"

    def review_sets(self, rset, key):
        """Per arm (and chunk), a separately shuffled copy of the planted set, kept in the control folder."""
        sets = {}
        chunk = int(self.cfg.get("review_chunk") or 0)
        for arm in "AB":
            rows = list(rset)
            random.Random(f"{key['salt']}-{arm}").shuffle(rows)
            parts = [rows[i:i + chunk] for i in range(0, len(rows), chunk)] if chunk else [rows]
            for k, part in enumerate(parts):
                p = self.keys / "sets" / f"{self.name}-{arm}{k}.jsonl"
                if not p.exists():
                    write_jsonl(p, part)
                sets[f"{arm}{k}"] = p
        return sets

    def reviewer_prompt(self, arm, folder, mode):
        w = self.workers[f"reviewer_{arm}"]
        t = (PROMPTS / "reviewer.txt").read_text(encoding="utf-8")
        mode_text = (PROMPTS / ("reveal.txt" if mode == "after_reveal" else "blind.txt")).read_text(encoding="utf-8")
        folder = Path(folder)
        sub = {"<<MODE_RULES>>": mode_text.strip(), "<<REPO>>": self.repo.as_posix(), "<<REPO_BASH>>": bash_path(self.repo),
               "<<SET>>": (folder / ("GENUINE.jsonl" if mode == "after_reveal" else "REVIEW_SET.jsonl")).as_posix(),
               "<<OUT>>": (folder / ("AFTER_REVEAL.jsonl" if mode == "after_reveal" else "BLIND_REVIEW.jsonl")).as_posix(),
               "<<SCRATCH>>": (folder / "scratch").as_posix(), "<<PACKET>>": self.rel(self.packet),
               "<<BATCH>>": self.rel(self.dir), "<<SCRATCH_ROOT>>": self.scratch.as_posix(),
               "<<REVIEWER>>": self.reviewer_name(arm), "<<MODEL_FAMILY>>": w.get("model_family", ""), "<<MODE>>": mode}
        for k, v in sub.items():
            t = t.replace(k, v)
        return t

    def run_reviews(self, mode, sets):
        """One fresh session per arm (or chunk), each in its own folder holding only its prompt and its set."""
        items = []
        tag = "review" if mode == "blind" else "reveal"
        dest = "GENUINE.jsonl" if mode == "after_reveal" else "REVIEW_SET.jsonl"
        for name, src in sorted(sets.items()):
            arm = name[0]
            items.append({"key": f"{tag}:{name}", "label": f"{self.name}-{tag}-{name}", "role": f"reviewer_{arm}",
                          "id": name, "render": lambda folder, arm=arm: self.reviewer_prompt(arm, folder, mode),
                          "setup": lambda folder, src=src: shutil.copyfile(src, folder / dest)})
        res = self.pool(items, tag, retry_failed=True)
        bad = {k: r["blinding_violations"] for k, r in res.items() if r.get("blinding_violations")}
        if bad:
            raise Stop(f"{mode} review: blinding broken, arm(s) {sorted(bad)} named forbidden paths: "
                       f"{next(iter(bad.values()))[:2]}; this batch cannot be completed")
        failed = [k for k, r in res.items() if not r.get("ok")]
        if failed:
            raise Stop(f"{mode} review: worker(s) {failed} did not finish; re-run to retry them "
                       "(not scored as control misses)")
        return res

    def arm_records(self, results, fname, hashes):
        """{arm: [record]} from each reviewer's own output file, with the session identity the conveyor knows."""
        out = {"A": [], "B": []}
        for name, rec in sorted(results.items()):
            arm = name[0]
            w = self.workers[f"reviewer_{arm}"]
            for r in read_jsonl(Path(rec["folder"]) / fname):
                if not isinstance(r, dict) or r.get("claim_sha256") not in hashes or r.get("verdict") not in (
                        "upheld", "rejected", "upheld_after_reveal"):
                    continue
                # The conveyor launched this fresh, separate session, so it states the session's identity itself;
                # the verdict, defects and reasons are the reviewer's own and are never changed.
                r.update(reviewer=self.reviewer_name(arm), model_family=w.get("model_family", "unknown"),
                         independent=True, separate_context=True, review_kind="independent_ai_source_review")
                r.setdefault("scope", "whole_case")
                if not isinstance(r.get("defects"), list):
                    r["defects"] = [r["defects"]] if r.get("defects") else []
                out[arm].append(r)
        return out

    def adjudications(self, items):
        """The coordinator's decisions from CONTROL/ADJUDICATION.json, a folder no worker may name or write."""
        p = self.keys / "ADJUDICATION.json"
        if not p.exists():
            return {}
        written = self.ledger.data("adjudicate:written")
        if not written or p.stat().st_mtime <= float(written["epoch"]):
            raise Fail(f"{p} predates this batch's ADJUDICATE.json; write it after reading ADJUDICATE.json")
        raw = read_json(p)
        decisions = raw.get("decisions") if isinstance(raw, dict) else None
        if not isinstance(decisions, list):
            raise Fail(f"{p} must be {{\"decisions\": [...]}}")
        want = {i["instrument_id"]: i["claim_sha256"] for i in items if i.get("blocks_completion")}
        out = {}
        for d in decisions:
            iid = d.get("instrument_id") if isinstance(d, dict) else None
            if iid not in want:
                raise Fail(f"ADJUDICATION.json names {iid!r}, which is not awaiting adjudication")
            if d.get("claim_sha256") != want[iid]:
                raise Fail(f"ADJUDICATION.json must name the exact claim_sha256 of {iid} from ADJUDICATE.json")
            if d.get("decision") not in ("file", "block") or not str(d.get("adjudicator") or "").strip():
                raise Fail(f"ADJUDICATION.json entry for {iid} needs decision file|block and an adjudicator")
            out[iid] = d
        return out

    # -- completion manifest (port of research/excavator/claude-nira-sweep-2026-10-29/make_completion.py,
    #    with Papinian finish_pair.py's two-arm rule) -----------------------------------------------------
    def manifest(self, applied, key, agree, adjudicator, pub, files):
        ref = lambda p, line=None: dict({"path": self.rel(p), "sha256": fsha(p)}, **({"line": line} if line else {}))
        lines = lambda p: {r.get("claim_sha256"): (i, r) for i, r in enumerate(read_jsonl(p), 1)}
        cpath = applied / "CLAIMS.proposed.jsonl"
        claims, agents = {}, set()
        for i, l in enumerate(cpath.read_text(encoding="utf-8").splitlines(), 1):
            if l.strip():
                c = json.loads(l)
                claims[c["instrument_id"]] = (i, canon(c))
                agents.add((c.get("claim_kit") or {}).get("agent"))
        if len(agents) != 1:
            raise Fail(f"claims name more than one producer agent: {sorted(map(str, agents))}")
        idx = {k: lines(p) for k, p in files.items()}
        pk = ref(self.packet / "PACKET.json")
        ctrl = {k["instrument_id"]: k for k in key["controls"]}
        members = []
        _, drows = read_csv(self.packet / "decisions.csv")
        for row in drows:
            iid = row["instrument_id"]
            if row["outcome"] != "submit" or iid not in claims:
                reason = row.get("unresolved_material_gaps") or row.get("research_rationale") or row["outcome"]
                members.append({"instrument_id": iid, "outcome": "blocked", "reason": reason})
                continue
            line, sha = claims[iid]
            a = agree.get(iid, {})
            if a.get("decision") != "file":
                members.append({"instrument_id": iid, "outcome": "blocked", "reason": a.get("reason", "not upheld")})
                continue
            mode = "AFTER_REVEAL" if iid in ctrl else "BLIND_REVIEW"
            hit = idx[(mode, a["arm"])].get(sha)
            if not hit:
                raise Fail(f"no {mode} record for {iid} in arm {a['arm']}")
            m = {"instrument_id": iid, "outcome": "submit", "claim_sha256": sha, "claim": ref(cpath, line),
                 "publication_kind": "whole_case", "packet": pk}
            m["after_reveal_review" if iid in ctrl else "review"] = ref(files[(mode, a["arm"])], hit[0])
            members.append(m)
        out = self.packet / "completion"
        out.mkdir(exist_ok=True)
        controls = []
        for k in key["controls"]:
            iid = k["instrument_id"]
            sp = out / f"SEED_RECEIPT_{slug(iid)}.json"
            sp.write_text(json.dumps({"schema": "eo-claim-kit-control-seed/v1", "instrument_id": iid,
                                      "planted_claim_sha256": k["planted"], "genuine_claim_sha256": k["genuine"],
                                      "seeded_by": adjudicator}, indent=1) + "\n", encoding="utf-8")
            hit = idx[("BLIND_REVIEW", "A")][k["planted"]]
            rr = ref(files[("BLIND_REVIEW", "A")], hit[0])
            ap = out / f"CONTROL_ADJUDICATION_{slug(iid)}.json"
            ap.write_text(json.dumps({"instrument_id": iid, "planted_claim_sha256": k["planted"], "review": rr,
                                      "adjudicator": adjudicator, "caught": True, "scoring": "strict",
                                      "rationale": f"Planted version: {k['defect']}. Rule fixed in advance: both "
                                      "independent blind arms (A and B) rejected that exact planted hash and named a "
                                      "date field or the word date in their defects."}, indent=1, ensure_ascii=False)
                          + "\n", encoding="utf-8")
            controls.append({"instrument_id": iid, "planted_claim_sha256": k["planted"], "seed": ref(sp),
                             "review": rr, "adjudication": ref(ap)})
        receipts = [ref(p) for p in (files[("BLIND_REVIEW", "B")], files[("AFTER_REVEAL", "B")],
                                     self.packet / "ASSESSMENT.jsonl", self.dir / "ADJUDICATION.json")
                    if Path(p).exists()]
        pf = self.workers["producer"].get("model_family", "unknown")
        fams = {self.workers[f"reviewer_{a}"].get("model_family", "unknown").casefold() for a in "AB"}
        indep = "different_family" if pf.casefold() not in fams else "same_family_separate_context"
        man = {"schema": "eo-claim-kit-completion/v1", "agent": agents.pop(), "producer_model_family": pf,
               "independence_requirement": indep, "publication": {"mode": "own_claims", "path": pub},
               "members": members, "controls": controls, "receipts": receipts}
        if self.cfg.get("replacement_proposal"):
            man["publication"] = {"mode": "replacement_proposal", "path": pub}
        write_json(out / "COMPLETION.json", man)
        return out / "COMPLETION.json", man


def load_workers(path):
    raw = read_json(path)
    if not isinstance(raw, dict):
        raise Fail(f"workers file {path} is not a JSON object")
    out = {}
    for role in ("producer", "reviewer_A", "reviewer_B"):
        w = raw.get(role) or (raw.get("reviewer") if role.startswith("reviewer") else None)
        if not isinstance(w, dict) or not w.get("model"):
            raise Fail(f"workers file needs a {role} (or reviewer) entry with a model")
        w = dict(w)
        cmd = w.get("command", w.get("family", "claude"))
        if cmd in ("claude", "codex"):
            w["command"] = list(CLAUDE_TEMPLATE if cmd == "claude" else CODEX_TEMPLATE)
            w["family"] = w.get("family") or cmd
        elif isinstance(cmd, list) and cmd:
            w["family"] = w.get("family") or program_family(cmd[0]) or "generic"
        else:
            raise Fail(f"{role}: command must be 'claude', 'codex' or a non-empty list")
        w.setdefault("model_family", {"claude": "Anthropic", "codex": "OpenAI"}.get(w["family"], "unknown"))
        out[role] = w
    return out


# ---------------------------------------------------------------------------------------------------------------
# The state machine


def run(cfg, repo=REPO):
    b = Batch(cfg, repo)
    L = b.ledger
    L.mark("run", "started", pid=os.getpid())
    b.reap()
    adjudicate = []
    state = {"ids": [], "submitted": 0, "controls_missed": 0}
    try:
        res = L.once("reserve", b.reserve)
        ids = state["ids"] = res["ids"]
        prep = L.once("prepare", lambda: b.prepare(ids))
        views = prep["views"]
        targets = [i for i in prep["dispatchable"] if i in ids and views.get(i)]
        no_view = [i for i in prep["dispatchable"] if not views.get(i)]
        rend = L.once("render", lambda: b.render(targets, views))
        for iid, n in rend["over_cap"].items():
            adjudicate.append({"instrument_id": iid, "kind": "prompt_over_cap", "blocks_completion": False,
                               "detail": f"rendered producer prompt {n} chars > cap {rend['cap_chars']}; not dispatched"})
        go = rend["rendered"]
        if not go:
            raise Stop("render: zero orders can be dispatched (all source-blocked, viewless or over the prompt cap)")
        pending = [i for i in go if not (b.latest(f"produce:{slug(i)}")[1] or {}).get("ok")]
        if pending:
            # A fresh dispatch check right before producers launch, on every (re)start that still launches any.
            n = len({r["key"] for r in L.rows if str(r.get("key", "")).startswith("dispatch:")})
            L.once(f"dispatch:{n + 1}", lambda: b.dispatch(pending))
        results = b.produce_round(0, go, views, {})
        produced = b.produced_map(results)
        for iid, v in produced.items():
            if "item cap" in v.get("reason", ""):
                adjudicate.append({"instrument_id": iid, "kind": "over_item_cap", "blocks_completion": False,
                                   "detail": v["reason"]})
        for iid in no_view:
            produced[iid] = {"reason": "Geddes view failed; no producer launched"}
        folders = {iid: v["folder"] for iid, v in produced.items() if v.get("folder")}
        demoted = dict(L.data("demoted") or {})
        col = b.collect(prep, produced, demoted)
        state["submitted"] = len(col["submit"])
        if not col["submit"]:
            raise Stop("collect: zero orders submittable after the producers finished")
        # Mechanical checks, with fresh-session repair rounds for orders that fail them.
        rnd = 0
        while True:
            chk = b.apply_and_check(col["sheets_fingerprint"])
            if not chk["failures"]:
                if not chk["claims"]:
                    raise Stop("check: zero claims assembled")
                break
            failing = [i for i in chk["failures"] if i in col["submit"]]
            if not failing:
                raise Fail(f"mechanical failures name no submitted order: {sorted(chk['failures'])[:5]}")
            if rnd < int(cfg.get("repair_rounds") or 0):
                rnd += 1
                rr = b.produce_round(rnd, failing, views, folders, chk["failures"])
                for iid, v in b.produced_map(rr).items():
                    if v.get("folder"):
                        produced[iid] = v
                        folders[iid] = v["folder"]
                    else:
                        demoted[iid] = f"repair round {rnd}: {v['reason']}"
            else:
                for iid in failing:
                    demoted[iid] = ("mechanical checks failed after "
                                    f"{rnd} repair round(s): {'; '.join(chk['failures'][iid])[:400]}")
                L.mark("demoted", "done", **demoted)
            col = b.collect(prep, produced, demoted)
            state["submitted"] = len(col["submit"])
            if not col["submit"]:
                raise Stop("check: zero orders submittable after the mechanical checks")
        applied = b.repo / chk["applied"]
        claims = read_jsonl(applied / "CLAIMS.proposed.jsonl")
        state["submitted"] = len(claims)
        kp = b.keys / f"{b.name}.json"

        def plant():
            key = read_json(kp)
            if not key or key.get("applied") != chk["applied"]:
                salt = os.urandom(16).hex()
                rset, controls = plant_controls(claims, salt)
                key = {"batch": b.name, "applied": chk["applied"], "salt": salt, "controls": controls,
                       "sealed_utc": now()}
                write_json(kp, key)
                ctl = {k["instrument_id"] for k in controls}
                write_jsonl(b.keys / f"{b.name}.GENUINE.jsonl", [c for c in claims if c["instrument_id"] in ctl])
                write_jsonl(b.keys / f"{b.name}.REVIEW_SET.jsonl", rset)
            # Only counts and the key's hash go in the ledger, which sits in the repository.
            return {"controls": len(key["controls"]), "key_sha256": fsha(kp), "claims": len(claims)}

        pl = L.once("plant", plant)
        if fsha(kp) != pl["key_sha256"]:
            raise Fail("the sealed control key changed after planting")
        key = read_json(kp)
        rset = read_jsonl(b.keys / f"{b.name}.REVIEW_SET.jsonl")
        hashes = {canon(c) for c in rset}
        blind_res = b.run_reviews("blind", b.review_sets(rset, key))
        blind_recs = b.arm_records(blind_res, "BLIND_REVIEW.jsonl", hashes)
        blind = {a: {r["claim_sha256"]: r for r in blind_recs[a]} for a in "AB"}

        def score():
            rows = []
            for k in key["controls"]:
                ok = {a: caught(blind[a].get(k["planted"])) for a in "AB"}
                rows.append({"instrument_id": k["instrument_id"], "defect": k["defect"], "caught_A": ok["A"],
                             "caught_B": ok["B"], "caught": all(ok.values())})
            write_json(b.dir / "CONTROLS.json", {"rule": "caught only if both arms rejected the exact planted hash and "
                                                 "a whole word or field name in their defects names a date",
                                                 "controls": rows})
            return {"missed": [r["instrument_id"] for r in rows if not r["caught"]], "controls": len(rows)}

        sc = L.once("controls", score)
        if sc["missed"]:
            state["controls_missed"] = len(sc["missed"])
            raise Stop(f"controls: planted control(s) missed by at least one arm: {sc['missed']}; batch not completed")
        genuine_path = b.keys / f"{b.name}.GENUINE.jsonl"
        reveal_res = b.run_reviews("after_reveal", {"AR": genuine_path, "BR": genuine_path})
        ghash = {canon(c) for c in read_jsonl(genuine_path)}
        after_recs = b.arm_records(reveal_res, "AFTER_REVEAL.jsonl", ghash)
        after = {a: {r["claim_sha256"]: r for r in after_recs[a]} for a in "AB"}
        # Arm agreement. The conveyor files only what both arms upheld and blocks only what both rejected;
        # everything else goes to the coordinator.
        ctrl = {k["instrument_id"] for k in key["controls"]}
        agree = {}
        for c in claims:
            iid, sha = c["instrument_id"], canon(c)
            src, need = (after, "upheld_after_reveal") if iid in ctrl else (blind, "upheld")
            ra, rb = src["A"].get(sha), src["B"].get(sha)
            va, vb = (ra or {}).get("verdict"), (rb or {}).get("verdict")
            if va == need and vb == need:
                agree[iid] = {"decision": "file", "arm": "A"}
            elif va == "rejected" and vb == "rejected":
                agree[iid] = {"decision": "block", "reason": "Both independent blind arms rejected this exact version: "
                              + json.dumps({"A": ra.get("defects"), "B": rb.get("defects")}, ensure_ascii=False)}
            else:
                adjudicate.append({"instrument_id": iid, "kind": "arm_disagreement" if ra and rb else "missing_review",
                                   "blocks_completion": True, "claim_sha256": sha, "control_genuine": iid in ctrl,
                                   "need": need, "arm_A": {"verdict": va, "defects": (ra or {}).get("defects")},
                                   "arm_B": {"verdict": vb, "defects": (rb or {}).get("defects")}})
        write_json(b.dir / "ADJUDICATE.json", {
            "schema": "maudslay-adjudicate/v1", "batch": b.name, "items": adjudicate,
            "note": f"The conveyor decides none of these. Write {(b.keys / 'ADJUDICATION.json').as_posix()} as "
                    "{\"decisions\":[{\"instrument_id\",\"claim_sha256\",\"decision\":\"file|block\",\"reason\","
                    "\"adjudicator\"}]} and re-run."})
        if not L.done("adjudicate:written"):
            L.mark("adjudicate:written", "done", epoch=time.time())
        decisions = b.adjudications(adjudicate)
        held = []
        for item in [i for i in adjudicate if i.get("blocks_completion")]:
            iid, d = item["instrument_id"], decisions.get(item["instrument_id"])
            verdicts = {"A": item["arm_A"]["verdict"], "B": item["arm_B"]["verdict"]}
            if d and d["decision"] == "file":
                arm = next((a for a in "AB" if verdicts[a] == item["need"]), None)
                if not arm:
                    raise Fail(f"ADJUDICATION.json files {iid}, but no arm upheld that exact version")
                agree[iid] = {"decision": "file", "arm": arm}
            elif d:
                agree[iid] = {"decision": "block", "reason": f"Coordinator adjudication ({d['adjudicator']}): "
                              + str(d.get("reason") or "blocked")}
            elif cfg.get("defer_adjudication"):
                agree[iid] = {"decision": "block", "reason": "The two blind arms disagreed; held for the "
                              "coordinator's adjudication and not filed in this completion."}
            else:
                held.append(iid)
        if held:
            raise Pause(f"agree: {len(held)} order(s) await adjudication: {held}")
        adj = cfg.get("adjudicator") or f"{cfg['agent']}-coordinator-maudslay"

        def complete():
            # A run killed after kit complete published must adopt that publication, not fail on the existing file.
            for d in sorted(b.packet.glob("complete-v*"), key=lambda p: int(p.name.split("-v")[1])):
                pub = read_json(d / "PUBLICATION.json", {}) or {}
                if pub.get("written") is True:
                    tally = read_json(d / "TALLY.json", {}) or {}
                    return {"complete": b.rel(d), "exit": 0, "adopted": True, "exceptions": tally.get("exceptions"),
                            "eligible": len(tally.get("eligible") or []), "published": tally.get("claims_published", 0),
                            "publication": cfg["publication"]}
            # Post-reveal records the kit's completion needs: the only review files written under research/.
            rv = b.packet / "reviews"
            files = {(m, a): rv / f"{m}_{a}.jsonl" for m in ("BLIND_REVIEW", "AFTER_REVEAL") for a in "AB"}
            for a in "AB":
                write_jsonl(files[("BLIND_REVIEW", a)], blind_recs[a])
                write_jsonl(files[("AFTER_REVEAL", a)], after_recs[a])
            if decisions:
                shutil.copyfile(b.keys / "ADJUDICATION.json", b.dir / "ADJUDICATION.json")
            mpath, man = b.manifest(applied, key, agree, adj, cfg["publication"], files)
            k = 1
            while (b.packet / f"complete-v{k}").exists():
                k += 1
            dest = b.packet / f"complete-v{k}"
            rc, _ = b.tool("kit", ["complete", mpath, "--write", dest] + (["--publish"] if cfg.get("publish") else []),
                           log=f"complete-v{k}")
            tally = read_json(dest / "TALLY.json", {}) or {}
            if rc and not tally:
                raise Fail(f"kit complete exit {rc}; see logs/complete-v{k}.err")
            return {"complete": b.rel(dest), "exit": rc, "exceptions": tally.get("exceptions"),
                    "eligible": len(tally.get("eligible") or []), "published": tally.get("claims_published", 0),
                    "submit_members": sum(m["outcome"] == "submit" for m in man["members"]),
                    "publication": cfg["publication"] if cfg.get("publish") else None}

        done = L.once("complete", complete)
        if done["exit"]:
            raise Fail(f"kit complete reported {done['exceptions']} exception(s); see {done['complete']}")
        verdict = gate_line(b, cfg, state, filed=done["published"])
        write_measures(b, cfg, state, done, verdict)
        L.mark("run", "done", outcome="done", gate=(verdict or {}).get("decision"))
        decision = (verdict or {}).get("decision")
        if decision == "STOP":
            return EXIT_GATE_STOP
        return EXIT_DONE if decision in ("CONTINUE", "PILOT") else EXIT_NO_GATE
    except Stop as s:
        b.kill_all()
        L.mark("run", "stopped", reason=str(s))
        if adjudicate:
            write_json(b.dir / "ADJUDICATE.json", {"schema": "maudslay-adjudicate/v1", "batch": b.name, "items": adjudicate})
        verdict = gate_line(b, cfg, state, filed=0)
        write_measures(b, cfg, state, None, verdict, stopped=str(s))
        print(json.dumps({"batch": b.name, "state": "stopped", "reason": str(s)}))
        return EXIT_STOPPED
    except Pause as p:
        L.mark("run", "paused", reason=str(p))
        write_measures(b, cfg, state, None, None, stopped=str(p))
        print(json.dumps({"batch": b.name, "state": "paused", "reason": str(p),
                          "adjudicate": b.rel(b.dir / "ADJUDICATE.json")}))
        return EXIT_PAUSED
    except Fail as f:
        b.kill_all()
        L.mark("run", "failed", reason=str(f))
        print(json.dumps({"batch": b.name, "state": "failed", "reason": str(f)}))
        return EXIT_FAILED


def gate_line(b, cfg, state, filed):
    """Upsert this batch's line in the wave's batch file, then run Bentham's gate on it (on every stop or finish)."""
    line = {"batch": b.name, "attempted": len(state["ids"]), "submitted": state["submitted"], "filed": filed,
            "controls_missed": state["controls_missed"], "usd": b.measured_usd()}
    bf = Path(cfg["batches_file"])
    bf = bf if bf.is_absolute() else b.repo / bf
    rows = read_json(bf, [])
    rows = rows["batches"] if isinstance(rows, dict) else (rows or [])
    rows = [r for r in rows if r.get("batch") != b.name] + [line]
    write_json(bf, rows)
    rc, out = b.tool("gate", log="gate", batches=bf)
    try:
        verdict = json.loads(out)
        if not isinstance(verdict, dict) or not verdict.get("decision"):
            raise ValueError
    except ValueError:
        verdict = {"decision": None, "refused": f"gate exit {rc}: {out.strip()[:300]}"}
    b.ledger.mark(f"gate:{len([r for r in b.ledger.rows if str(r.get('key')).startswith('gate:')]) + 1}", "done",
                  line=line, verdict=verdict)
    return verdict


def write_measures(b, cfg, state, done, verdict, stopped=None):
    stages = {}
    for w in b.ledger.workers():
        s = stages.setdefault(w.get("stage") or w.get("role") or "worker",
                              {"workers": 0, "input": 0, "cache_read": 0, "cache_write": 0, "output": 0, "tokens": 0,
                               "usd": 0.0, "usd_at_cap_workers": 0, "wall_seconds": 0.0})
        s["workers"] += 1
        for k in ("input", "cache_read", "cache_write", "output", "tokens"):
            s[k] += int(w.get(k) or 0)
        if w.get("usd") is None:
            s["usd_at_cap_workers"] += 1
            s["usd"] = round(s["usd"] + float(b.cap(w.get("role"), "usd") or 0), 6)
        else:
            s["usd"] = round(s["usd"] + w["usd"], 6)
        s["wall_seconds"] = round(s["wall_seconds"] + (w.get("wall_seconds") or 0), 3)
    machine = {r["key"]: r["data"].get("wall_seconds") for r in b.ledger.rows
               if r.get("status") == "done" and isinstance(r.get("data"), dict) and not r["data"].get("worker")
               and r["data"].get("wall_seconds") is not None}
    usd = sum(s["usd"] for s in stages.values())
    filed = (done or {}).get("published", 0)
    m = {"schema": "maudslay-measures/v1", "batch": b.name, "action": cfg["action"], "agent": cfg["agent"],
         "written_utc": now(), "state": "stopped" if stopped else "done", "stop_reason": stopped,
         "stages": stages, "machine_stage_seconds": machine,
         "workers": [{k: w.get(k) for k in ("label", "role", "model", "family", "session_id", "tokens", "input",
                                            "cache_read", "cache_write", "output", "usd", "wall_seconds", "ok",
                                            "killed", "orphaned", "adopted", "over_item_cap", "prompt_chars")}
                     for w in b.ledger.workers()],
         "totals": {"usd": round(usd, 4), "tokens": sum(s["tokens"] for s in stages.values()),
                    "attempted": len(state["ids"]), "submitted": state["submitted"], "filed": filed,
                    "usd_per_filed": round(usd / filed, 4) if filed else None},
         "gate": verdict, "human_certified": 0,
         "note": "Tokens and dollars are the workers' own reported usage (claude stream-json result; codex exec "
                 "turn.completed usage priced from the workers file). A worker with unknown dollars counts at its "
                 "item cap. The coordinator's own tokens are not here."}
    write_json(b.dir / "MEASURES.json", m)
    return m


# ---------------------------------------------------------------------------------------------------------------
# CLI


def build_config(a, repo):
    run_dir = Path(a.run_dir)
    bdir = (repo / run_dir / a.batch) if not run_dir.is_absolute() else run_dir / a.batch
    saved = read_json(bdir / "CONFIG.json")
    given = {k: getattr(a, k) for k in FIXED + MUTABLE if getattr(a, k, None) is not None}
    for k in ("keys_dir", "scratch_root"):
        if k in given:
            given[k] = Path(given[k]).resolve().as_posix()
    if saved:
        for k in FIXED:
            if k in given and given[k] != saved.get(k):
                raise Fail(f"{k} is fixed for batch {a.batch} (was {saved.get(k)!r}, now {given[k]!r}); start a new batch")
        cfg = dict(saved)
        cfg.update({k: v for k, v in given.items() if k in MUTABLE})
    else:
        for need in ("agent", "action", "route", "workers", "batch_usd"):
            if given.get(need) is None:
                raise Fail(f"--{need.replace('_', '-')} is required for a new batch")
        name = Path(a.run_dir).name
        scratch = Path(given.get("scratch_root") or Path(tempfile.gettempdir()) / "maudslay" / name / a.batch).resolve()
        cfg = {"run_dir": Path(a.run_dir).as_posix(), "batch": a.batch, "n": 20, "parallel": 4,
               "prompt_cap_chars": 16000, "review_chunk": 0, "repair_rounds": 1, "item_timeout": 5400,
               "replacement_proposal": False, "publish": False, "defer_adjudication": False,
               "scratch_root": scratch.as_posix(), "keys_dir": (scratch / "control").as_posix(),
               "batches_file": (Path(a.run_dir) / "BATCHES.json").as_posix(),
               "publication": f"research/readiness/claims/{given['agent']}-{datetime.now(timezone.utc).date()}-"
                              f"{name}-{a.batch}.jsonl"}
        cfg.update(given)
    for k in ("workers", "tools"):
        if cfg.get(k):
            p = Path(cfg[k])
            cfg[k] = (p if p.is_absolute() else (repo / p)).as_posix()
    write_json(bdir / "CONFIG.json", cfg)
    return cfg


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run or resume one batch")
    r.add_argument("--repo", type=Path, default=REPO)
    r.add_argument("--run-dir", required=True, help="wave folder, relative to the repository")
    r.add_argument("--batch", required=True)
    r.add_argument("--agent")
    r.add_argument("--action", help="Bentham action id (jobs/bentham/output/PLAN.json)")
    r.add_argument("--n", type=int)
    r.add_argument("--ids", nargs="+", help="explicit orders instead of kit next")
    r.add_argument("--route", help="route brief (e.g. research/excavator/claude-papinian-2026-11-10/tools/prompts/route_yes.txt)")
    r.add_argument("--workers", help="workers JSON (see workers.example.json)")
    r.add_argument("--tools", help="JSON overriding the kit/lookups/view/gate command templates")
    r.add_argument("--replacement-proposal", action="store_true", default=None)
    r.add_argument("--publication", help="repo-relative claim file (default research/readiness/claims/AGENT-DATE-RUN-BATCH.jsonl)")
    r.add_argument("--publish", action="store_true", default=None, help="pass --publish to kit complete")
    r.add_argument("--parallel", type=int)
    r.add_argument("--item-usd", type=float, help="per-worker dollar cap (claude --max-budget-usd)")
    r.add_argument("--item-tokens", type=int, help="per-worker token cap, enforced from the worker's own usage")
    r.add_argument("--item-timeout", type=int, help="per-worker wall-clock cap, seconds")
    r.add_argument("--batch-usd", type=float, help="batch budget in dollars (required)")
    r.add_argument("--batch-tokens", type=int, help="batch budget in tokens")
    r.add_argument("--prompt-cap-chars", type=int, help="hard cap on every rendered prompt (default 16000)")
    r.add_argument("--review-chunk", type=int, help="claims per reviewer session (0 = one session per arm)")
    r.add_argument("--repair-rounds", type=int, help="fresh producer sessions for mechanical failures (default 1)")
    r.add_argument("--defer-adjudication", action="store_true", default=None,
                   help="complete now and hold disagreed orders unfiled, instead of pausing")
    r.add_argument("--adjudicator", help="name recorded on control adjudications and seed receipts")
    r.add_argument("--scratch-root", help="worker folders and control material, outside the repository "
                                          "(default TEMP/maudslay/RUN/BATCH)")
    r.add_argument("--keys-dir", help="sealed control key, review sets and ADJUDICATION.json (default SCRATCH/control)")
    r.add_argument("--batches-file", help="Bentham gate batch file (default RUN/BATCHES.json)")
    s = sub.add_parser("status", help="print one batch's ledger summary")
    s.add_argument("batch_dir", type=Path)
    c = sub.add_parser("commands", help="print the rendered worker commands without running them")
    c.add_argument("--workers", required=True)
    c.add_argument("--item-usd", type=float, default=1.0)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "status":
            rows = read_jsonl(Path(a.batch_dir) / "LEDGER.jsonl")
            last = {}
            for r_ in rows:
                last[r_["key"]] = r_["status"]
            print(json.dumps({"records": len(rows), "keys": last,
                              "run": next((r_ for r_ in reversed(rows) if r_["key"] == "run"), None)}, indent=1))
            return 0
        if a.cmd == "commands":
            for role, w in load_workers(a.workers).items():
                argv_ = render_args(w["command"], {"model": w["model"], "max_turns": w.get("max_turns", 80),
                                                  "repo": REPO.as_posix(), "cwd": "WORKER_FOLDER",
                                                  "item_usd": w.get("item_usd", a.item_usd),
                                                  "auto_compact_tokens": w.get("auto_compact_tokens", 120000),
                                                  "tool_output_tokens": w.get("tool_output_tokens", 6000),
                                                  "writable_roots": json.dumps(["WORKER_FOLDER"]),
                                                  "network": "true" if w.get("network") else "false"})
                validate_worker_command(argv_, w["family"])
                print(role, "(cwd WORKER_FOLDER)", " ".join(argv_), "< PROMPT.txt")
            return 0
        repo = a.repo.resolve()
        cfg = build_config(a, repo)
        return run(cfg, repo)
    except Fail as f:
        print(json.dumps({"state": "failed", "reason": str(f)}))
        return EXIT_FAILED


if __name__ == "__main__":
    sys.exit(main())

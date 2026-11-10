"""Maudslay conveyor: run one claim-kit batch end to end so that a coordinator model only adjudicates.

Named for Henry Maudslay, whose Portsmouth block-making machines (from 1803) let a few unskilled hands do the work
of many skilled ones. The 2026-11-09/10 Codex wave spent 54% of its tokens on coordinators doing clerical steps
themselves; the Papinian lane, where small scripts did that work, spent 17%. This file is those scripts as one
resumable state machine.

    python -I jobs/maudslay-conveyor/conveyor.py run --run-dir research/excavator/RUN --batch b01 \
        --agent NAME --action BENTHAM_ACTION --n 20 --route ROUTE.txt --workers WORKERS.json [--publish]
    python -I jobs/maudslay-conveyor/conveyor.py status research/excavator/RUN/b01
    python -I jobs/maudslay-conveyor/conveyor.py commands --workers WORKERS.json      (print rendered worker commands)

Stages, each recorded in BATCH/LEDGER.jsonl and skipped on a re-run once done: reserve (kit next), prepare (kit
prepare, cruden lookups, Geddes views), dispatch (kit dispatch-check just before producers), render (one producer
prompt per order, size-capped), produce (fresh worker sessions, concurrent, capped), collect (validate and merge the
per-order sheets), check (kit apply and batch-check, optional repair rounds), plant (sealed planted controls), review
(two independent blind arms), controls (stop on any miss), reveal (fresh after-reveal sessions on the genuine
controls), agree (arm agreement; disagreements go to ADJUDICATE.json), complete (kit complete, --publish only when
asked), measure (MEASURES.json and the Bentham gate line).

Exit codes: 0 done; 1 failed (a tool or configuration error); 2 stopped by a stop rule; 3 paused for coordinator
adjudication (write BATCH/ADJUDICATION.json and re-run); 4 done, but Bentham's gate says STOP.

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

EXIT_DONE, EXIT_FAILED, EXIT_STOPPED, EXIT_PAUSED, EXIT_GATE_STOP = 0, 1, 2, 3, 4
DATE_WORDS = ("date", "first_end", "whole_order_end", "signing", "later_event", "effective", "year")
OUTCOMES = ("submit", "unresolved", "blocked", "route_owner")
# Settings fixed when a batch starts; a re-run may change only budgets, concurrency and publication switches.
FIXED = ("agent", "action", "n", "ids", "route", "replacement_proposal", "publication", "prompt_cap_chars",
         "review_chunk", "repair_rounds", "adjudicator")
MUTABLE = ("parallel", "item_usd", "item_tokens", "batch_usd", "batch_tokens", "item_timeout", "publish",
           "defer_adjudication", "batches_file", "keys_dir", "tools", "workers")

DEFAULT_TOOLS = {
    "kit": ["{python}", "-X", "utf8", "{repo}/jobs/claim-kit/kit.py", "--repo", "{repo}"],
    "lookups": ["{python}", "-X", "utf8", "-I", "{repo}/research/excavator/claude-nira-sweep-2026-10-29/cruden.py",
                "lookups", "{packet}"],
    "view": ["{python}", "-X", "utf8", "-I", "{repo}/jobs/geddes/geddes.py", "view", "{packet}/PACKET.json", "{iid}",
             "--write", "{out}"],
    "gate": ["{python}", "-I", "{repo}/jobs/bentham/bentham.py", "gate", "--action", "{action}", "--batches",
             "{batches}"],
}

# Worker templates. Every call is a fresh session: no resume, continue or fork flag is ever accepted.
CLAUDE_TEMPLATE = ["claude", "-p", "--model", "{model}", "--output-format", "json", "--max-turns", "{max_turns}",
                   "--max-budget-usd", "{item_usd}", "--permission-mode", "auto", "--add-dir", "{repo}"]
CODEX_TEMPLATE = ["codex", "exec", "--json", "--ephemeral", "--skip-git-repo-check", "-C", "{cwd}", "-m", "{model}",
                  "-c", 'model_reasoning_effort="medium"',
                  "-c", "model_auto_compact_token_limit={auto_compact_tokens}",
                  "-c", "tool_output_token_limit={tool_output_tokens}",
                  "-c", 'approval_policy="never"',
                  "-c", 'sandbox_mode="workspace-write"',
                  "-c", "sandbox_workspace_write.writable_roots={writable_roots}",
                  "-c", "sandbox_workspace_write.network_access={network}",
                  "-"]
RESUME_TOKENS = {"resume", "--resume", "--continue", "--last", "--fork-session", "fork"}
UNSAFE_TOKENS = {"--dangerously-bypass-approvals-and-sandbox", "--yolo", "--dangerously-skip-permissions"}


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
    except (FileNotFoundError, ValueError):
        return default


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def read_jsonl(path):
    out = []
    if not Path(path).exists():
        return out
    for line in Path(path).read_text(encoding="utf-8").splitlines():
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


# ---------------------------------------------------------------------------------------------------------------
# Ledger


class Ledger:
    """Append-only JSONL of stage and item records. A key is done once a 'done' record exists for it."""

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

    def mark(self, key, status, **data):
        row = {"utc": now(), "key": key, "status": status, "data": data}
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
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
        data = fn()
        data = dict(data or {})
        data.setdefault("wall_seconds", round(time.monotonic() - t0, 3))
        self.mark(key, "done", **data)
        return data

    def workers(self):
        """Every finished worker record (one per launched session)."""
        seen = {}
        for r in self.rows:
            if r.get("status") == "done" and isinstance(r.get("data"), dict) and r["data"].get("worker"):
                seen[r["key"]] = r["data"]
        return list(seen.values())


# ---------------------------------------------------------------------------------------------------------------
# Commands


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


def validate_worker_command(argv, family):
    """Refuse any command that resumes, continues or forks a session, or that lacks the budget flags."""
    toks = [str(t) for t in argv]
    bad = [t for t in toks if t in RESUME_TOKENS or t.startswith(("--resume=", "--continue=", "--session-id"))]
    if family == "claude":
        bad += [t for t in toks if t in ("-c", "-r")]
    if bad:
        raise Fail(f"worker command would reuse a session ({bad}); every worker call must be a fresh session")
    unsafe = [t for t in toks if t in UNSAFE_TOKENS or "danger-full-access" in t]
    if unsafe:
        raise Fail(f"worker command disables the sandbox or approvals: {unsafe}")
    if any("rollout_token_budget" in t for t in toks):
        raise Fail("rollout_token_budget does not exist in the installed Codex build; remove it")
    if family == "claude":
        for flag in ("-p", "--max-turns", "--max-budget-usd", "--output-format"):
            if flag not in toks:
                raise Fail(f"claude worker command lacks {flag}")
        fmt = toks[toks.index("--output-format") + 1]
        if fmt not in ("json", "stream-json"):
            raise Fail("claude worker must report usage with --output-format json")
    elif family == "codex":
        for flag in ("exec", "--json", "--ephemeral"):
            if flag not in toks:
                raise Fail(f"codex worker command lacks {flag}")
        cfg = " ".join(toks[i + 1] for i, t in enumerate(toks[:-1]) if t == "-c")
        for need in ("model_auto_compact_token_limit=", "tool_output_token_limit=", 'approval_policy="never"'):
            if need not in cfg:
                raise Fail(f"codex worker command lacks -c {need}")
    elif family != "generic":
        raise Fail(f"unknown worker family {family!r} (claude, codex or generic)")
    return toks


def kill_tree(proc):
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()


def parse_usage(text):
    """Usage from a worker's own JSON output: a `claude -p --output-format json` result object, or `codex exec
    --json` events (turn.completed usage). Tokens: input (uncached), cache_read, cache_write, output."""
    u = {"session_id": None, "is_error": False, "num_turns": None, "input": 0, "cache_read": 0, "cache_write": 0,
         "output": 0, "usd": None, "result": None, "usage_seen": False}
    d = None
    try:
        d = json.loads(text)
    except ValueError:
        pass
    if isinstance(d, list):
        d = next((x for x in reversed(d) if isinstance(x, dict) and x.get("type") == "result"), None)
    if isinstance(d, dict) and ("usage" in d or "total_cost_usd" in d):
        us = d.get("usage") or {}
        u.update(session_id=d.get("session_id"), is_error=bool(d.get("is_error")), num_turns=d.get("num_turns"),
                 input=int(us.get("input_tokens") or 0), cache_read=int(us.get("cache_read_input_tokens") or 0),
                 cache_write=int(us.get("cache_creation_input_tokens") or 0),
                 output=int(us.get("output_tokens") or 0), usd=d.get("total_cost_usd"), result=d.get("result"),
                 usage_seen=True)
        return u
    for line in text.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        add_event(u, ev)
    return u


def add_event(u, ev):
    if not isinstance(ev, dict):
        return
    t = ev.get("type")
    if t == "thread.started":
        u["session_id"] = ev.get("thread_id") or u["session_id"]
    elif t == "turn.completed" and isinstance(ev.get("usage"), dict):
        us = ev["usage"]
        cached = int(us.get("cached_input_tokens") or 0)
        u["cache_read"] += cached
        u["input"] += max(int(us.get("input_tokens") or 0) - cached, 0)
        u["output"] += int(us.get("output_tokens") or 0)
        u["num_turns"] = (u["num_turns"] or 0) + 1
        u["usage_seen"] = True
    elif t in ("turn.failed", "error"):
        u["is_error"] = True
    elif t == "item.completed" and isinstance(ev.get("item"), dict) and ev["item"].get("type") == "agent_message":
        u["result"] = ev["item"].get("text")


def tokens(u):
    return int(u.get("input") or 0) + int(u.get("cache_read") or 0) + int(u.get("cache_write") or 0) + int(u.get("output") or 0)


def price(u, prices):
    if u.get("usd") is not None:
        return float(u["usd"])
    if not prices or any(not isinstance(prices.get(k), (int, float)) for k in ("input", "cached_input", "output")):
        return None
    return ((u.get("input") or 0) * prices.get("input", 0) + (u.get("cache_read") or 0) * prices.get("cached_input", 0)
            + (u.get("cache_write") or 0) * prices.get("cache_write", prices.get("input", 0))
            + (u.get("output") or 0) * prices.get("output", 0)) / 1e6


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
    """Papinian finish_pair.py rule, fixed in advance: rejected, and the defect text names a date."""
    if not rec or rec.get("verdict") != "rejected":
        return False
    text = json.dumps([rec.get("defects", []), rec.get("reasons", ""), rec.get("reason", "")], ensure_ascii=False).lower()
    return any(w in text for w in DATE_WORDS)


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
        # Sheets, review sets and review outputs live inside the packet folder. claim-kit's prior-research scan
        # excludes only the packet itself, so a claim or review file elsewhere under research/ would change the
        # frozen packet's prior research ("changed prior research; prepare a new version").
        self.work = self.packet / "maudslay" / "work"
        self.reviews = self.packet / "maudslay" / "review"
        self.name = cfg["batch"]
        self.ledger = Ledger(self.dir / "LEDGER.jsonl")
        keys = Path(cfg["keys_dir"]).resolve()
        if keys.is_relative_to(self.repo):
            raise Fail("--keys-dir must be outside the repository (the control key is sealed from reviewers)")
        self.keys = keys
        self.tools = dict(DEFAULT_TOOLS)
        if cfg.get("tools"):
            self.tools.update(read_json(cfg["tools"], {}) or {})
        self.workers = load_workers(cfg["workers"])
        self.spend_lock = threading.Lock()

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

    def git_dirs(self):
        out = []
        for flag in ("--git-dir", "--git-common-dir"):
            try:
                p = subprocess.run(["git", "rev-parse", flag], cwd=self.repo, capture_output=True, text=True)
                if p.returncode == 0 and p.stdout.strip():
                    d = Path(p.stdout.strip())
                    d = d if d.is_absolute() else self.repo / d
                    out.append(d.resolve().as_posix())
            except OSError:
                pass
        return sorted(set(out)) or [(self.repo / ".git").as_posix()]

    def spent(self):
        """(usd, tokens) of every worker this batch launched, counting a worker with unknown usd at the item cap."""
        usd = tok = 0.0
        for w in self.ledger.workers():
            usd += w["usd"] if w.get("usd") is not None else float(self.cap(w["role"], "usd") or 0)
            tok += w.get("tokens") or 0
        return usd, tok

    def cap(self, role, kind):
        """Per-worker cap: the role's own item_usd / item_tokens in the workers file, else the batch-wide one."""
        w = self.workers.get(role) or {}
        v = w.get(f"item_{kind}")
        return v if v is not None else self.cfg.get(f"item_{kind}")

    def budget_reason(self, running, role="producer"):
        usd, tok = self.spent()
        iu, it = self.cap(role, "usd"), self.cap(role, "tokens")
        bu, bt = self.cfg.get("batch_usd"), self.cfg.get("batch_tokens")
        if bu is not None and (usd + (running + 1) * float(iu or 0) > bu or usd >= bu):
            return f"batch_budget: spent ${usd:.2f} + {running + 1} x item cap ${float(iu or 0):.2f} > ${bu:.2f}"
        if bt is not None and (tok + (running + 1) * float(it or 0) > bt or tok >= bt):
            return f"batch_token_budget: {int(tok)} + {running + 1} x {int(it or 0)} > {int(bt)}"
        return None

    # -- workers ------------------------------------------------------------------------------------------
    def run_worker(self, label, role, prompt_text, stage="worker"):
        w = self.workers[role]
        cwd = self.dir
        prompt_file = self.dir / "prompts" / f"{label}.txt"
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text(prompt_text, encoding="utf-8")
        mapping = {"model": w["model"], "max_turns": w.get("max_turns", 80), "repo": self.repo.as_posix(),
                   "cwd": cwd.as_posix(), "prompt_file": prompt_file.as_posix(),
                   "item_usd": self.cap(role, "usd") if self.cap(role, "usd") is not None else "",
                   "auto_compact_tokens": w.get("auto_compact_tokens", 120000),
                   "tool_output_tokens": w.get("tool_output_tokens", 6000),
                   "writable_roots": json.dumps([cwd.as_posix()] + self.git_dirs()),
                   "network": "true" if w.get("network") else "false"}
        argv = render_args(w["command"], mapping)
        if w["family"] == "claude" and mapping["item_usd"] == "":
            raise Fail("a claude worker needs --item-usd or its own item_usd (passed as --max-budget-usd)")
        argv = validate_worker_command(argv, w["family"])
        exe = shutil.which(argv[0])
        if exe:
            argv[0] = exe
        wdir = self.dir / "workers"
        wdir.mkdir(parents=True, exist_ok=True)
        out_path, err_path = wdir / f"{label}.out", wdir / f"{label}.err"
        t0, started = time.monotonic(), now()
        item_tokens, timeout = self.cap(role, "tokens"), w.get("item_timeout", self.cfg.get("item_timeout"))
        killed = None
        live = {"session_id": None, "is_error": False, "num_turns": None, "input": 0, "cache_read": 0,
                "cache_write": 0, "output": 0, "usd": None, "result": None, "usage_seen": False}
        try:
            with open(prompt_file, "rb") as stdin, open(err_path, "wb") as err:
                proc = subprocess.Popen(argv, cwd=cwd, stdin=stdin, stdout=subprocess.PIPE, stderr=err)
                timer = None
                if timeout:
                    def on_timeout():
                        nonlocal killed
                        killed = killed or f"item_timeout {timeout}s"
                        kill_tree(proc)
                    timer = threading.Timer(float(timeout), on_timeout)
                    timer.start()
                chunks = []
                for raw in proc.stdout:
                    chunks.append(raw)
                    try:
                        add_event(live, json.loads(raw.decode("utf-8", "replace")))
                    except ValueError:
                        pass
                    # Per-item cap, in the loop: stop a worker whose own reported usage passes the cap.
                    if item_tokens and tokens(live) > item_tokens and not killed:
                        killed = f"item_token_cap {tokens(live)} > {item_tokens}"
                        kill_tree(proc)
                proc.stdout.close()
                rc = proc.wait()
                if timer:
                    timer.cancel()
        except OSError as exc:
            raise Fail(f"cannot launch worker {label}: {exc}")
        text = b"".join(chunks).decode("utf-8", "replace")
        out_path.write_text(text, encoding="utf-8")
        u = parse_usage(text)
        usd = price(u, w.get("prices_usd_per_mtok"))
        rec = {"worker": True, "label": label, "stage": stage, "role": role, "family": w["family"], "model": w["model"],
               "model_family": w.get("model_family"), "session_id": u["session_id"], "exit": rc,
               "is_error": u["is_error"], "killed": killed, "num_turns": u["num_turns"],
               "input": u["input"], "cache_read": u["cache_read"], "cache_write": u["cache_write"],
               "output": u["output"], "tokens": tokens(u), "usd": usd, "usage_reported": u["usage_seen"],
               "started_utc": started, "ended_utc": now(), "wall_seconds": round(time.monotonic() - t0, 3),
               "argv": [Path(argv[0]).name] + argv[1:], "prompt_chars": len(prompt_text)}
        over = []
        if item_tokens and rec["tokens"] > item_tokens:
            over.append(f"tokens {rec['tokens']} > {item_tokens}")
        iu = self.cap(role, "usd")
        if iu is not None and usd is not None and usd > float(iu) * 1.0001:
            over.append(f"usd {usd:.4f} > {iu}")
        rec["over_item_cap"] = "; ".join(over) or None
        rec["ok"] = rc == 0 and not u["is_error"] and not killed
        # One lock for the whole record: on Windows, append mode from two threads can lose a write.
        with self.spend_lock, (self.dir / "COSTS.log").open("a", encoding="utf-8") as fh:
            # The carnot-coordinator/worker.py cost line, read by `bentham.py usage --reported-costs`.
            fh.write(f"{label} launched {started}\n")
            if u["session_id"] and usd is not None:
                fh.write(f"{label} {u['session_id']} cost {usd} turns {u['num_turns']} ms {int(rec['wall_seconds'] * 1000)}\n")
            fh.write(f"{label} {'done' if rec['ok'] else 'failed'} {rec['ended_utc']}\n")
        return rec

    def latest(self, key):
        """(key of the newest attempt, its done record or None). Attempts after the first are KEY#2, KEY#3 ..."""
        n = 1
        while any(r.get("key") == f"{key}#{n + 1}" for r in self.ledger.rows):
            n += 1
        k = key if n == 1 else f"{key}#{n}"
        return k, self.ledger.data(k)

    def pool(self, items, stage, retry_failed=False):
        """Run worker items concurrently, capped, with the budget checked before every launch.

        items: [{"key", "label", "role", "prompt", "id", "before"}]; returns {id: worker record}. A finished
        worker is never relaunched, except a failed one when retry_failed (then as a new attempt key)."""
        results, pending = {}, []
        for it in items:
            k, rec = self.latest(it["key"])
            if rec is not None and (rec.get("ok") or not retry_failed):
                results[it["id"]] = rec
                continue
            if rec is not None:
                n = int(k.split("#")[1]) + 1 if "#" in k else 2
                k = f"{it['key']}#{n}"
            pending.append(dict(it, key=k, label=it["label"] + (f"-a{k.split('#')[1]}" if "#" in k else "")))
        stop = None
        parallel = max(1, int(self.cfg.get("parallel") or 1))
        with cf.ThreadPoolExecutor(max_workers=parallel) as ex:
            running = {}
            while pending or running:
                while pending and len(running) < parallel and stop is None:
                    stop = self.budget_reason(len(running), pending[0]["role"])
                    if stop:
                        break
                    it = pending.pop(0)
                    if it.get("before"):
                        it["before"]()
                    self.ledger.mark(it["key"], "started", label=it["label"], role=it["role"])
                    running[ex.submit(self.run_worker, it["label"], it["role"], it["prompt"], stage)] = it
                if not running:
                    break
                done, _ = cf.wait(running, return_when=cf.FIRST_COMPLETED)
                for f in done:
                    it = running.pop(f)
                    try:
                        rec = f.result()
                    except Fail:
                        for g in running:
                            g.cancel()
                        raise
                    self.ledger.mark(it["key"], "done", **rec)
                    results[it["id"]] = rec
                    if stop is None:
                        usd, tok = self.spent()
                        bu, bt = self.cfg.get("batch_usd"), self.cfg.get("batch_tokens")
                        if (bu is not None and usd >= bu) or (bt is not None and tok >= bt):
                            stop = f"batch_budget: spent ${usd:.2f} / {int(tok)} tokens"
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
            rc, out = self.tool("kit", ["next", "--agent", self.cfg["agent"], "--action", self.cfg["action"],
                                        "--n", self.cfg["n"]], log="reserve")
            try:
                rows = json.loads(out)
            except ValueError:
                rows = None
            if rc or not isinstance(rows, list):
                raise Fail(f"kit next failed (exit {rc}); see {self.rel(self.dir / 'logs/reserve.err')}")
            write_json(saved, rows)
        ids = [r["instrument_id"] for r in rows]
        if not ids:
            raise Stop("reserve: kit next reserved no orders under this action")
        return {"ids": ids, "via": "kit next"}

    def prepare(self, ids):
        if self.packet.exists():
            k = 1
            while (self.dir / f"packet.incomplete-{k}").exists():
                k += 1
            os.replace(self.packet, self.dir / f"packet.incomplete-{k}")
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
                "source_blocked": list(dc.get("source_blocked_ids") or []),
                "agent": (read_json(self.packet / "PACKET.json", {}) or {}).get("agent", self.cfg["agent"])}

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

    def producer_prompt(self, iid, view_rel, extra=""):
        t = (PROMPTS / "producer.txt").read_text(encoding="utf-8")
        route = Path(self.cfg["route"])
        route = route if route.is_absolute() else self.repo / route
        work = self.work / slug(iid)
        sub = {"<<REPO>>": self.repo.as_posix(), "<<REPO_BASH>>": bash_path(self.repo), "<<ORDER>>": iid,
               "<<SLUG>>": slug(iid), "<<VIEW>>": view_rel, "<<PACKET>>": self.rel(self.packet),
               "<<WORK>>": work.as_posix(), "<<AGENT>>": self.cfg["agent"], "<<ROUTE_NAME>>": route.stem,
               "<<ROUTE>>": route.read_text(encoding="utf-8").strip(),
               "<<VIEW_HEADER>>": self.view_header(iid, view_rel), "<<RUN>>": self.rel(self.dir.parent)}
        for k, v in sub.items():
            t = t.replace(k, v)
        return t + extra

    def render(self, targets, views):
        cap = int(self.cfg["prompt_cap_chars"])
        ok, over, sizes = [], {}, {}
        for iid in targets:
            text = self.producer_prompt(iid, views[iid])
            sizes[iid] = len(text)
            if len(text) > cap:
                over[iid] = len(text)
                continue
            ok.append(iid)
        return {"rendered": ok, "over_cap": over, "cap_chars": cap, "prompt_chars": sizes}

    def fresh_sheet(self, iid):
        """Give a producer this order's prepared rows; an earlier (killed) attempt's folder is kept aside."""
        work = self.work / slug(iid)
        if work.exists():
            k = 1
            while (work.parent / f"{slug(iid)}.prior-{k}").exists():
                k += 1
            os.replace(work, work.parent / f"{slug(iid)}.prior-{k}")
        work.mkdir(parents=True)
        for name in ("decisions.csv", "clauses.csv"):
            fields, rows = read_csv(self.dir / "prepared" / name)
            write_csv(work / name, fields, [r for r in rows if r.get("instrument_id") == iid])
        (work / "RATIONALES.json").write_text("{}\n", encoding="utf-8")

    def snapshot(self, iid, rnd):
        work = self.work / slug(iid)
        snap = self.work / f"{slug(iid)}.round-{rnd - 1}"
        if work.exists() and not snap.exists():
            shutil.copytree(work, snap)

    def validate_sheet(self, iid):
        """(decision row, clause rows, rationales, assessment) from work/EO_N, or raise ValueError."""
        work = self.work / slug(iid)
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
            if iid in blocked:
                note = "dispatch check: a mandatory source is not held; no producer was launched"
                r["outcome"] = "blocked"
            elif produced.get(iid) is True:
                try:
                    sheets[iid] = self.validate_sheet(iid)
                except (ValueError, OSError, StopIteration) as exc:
                    note = f"producer sheet invalid: {exc}"
            else:
                note = produced.get(iid) or "no producer sheet (not dispatched)"
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
                gaps = json_list(r.get("unresolved_material_gaps"))
                r["unresolved_material_gaps"] = json.dumps(gaps + [note], ensure_ascii=False)
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

    def produce_round(self, rnd, iids, views, errors=None):
        items = []
        for iid in iids:
            extra = ""
            if errors:
                err = json.dumps(errors.get(iid, []), ensure_ascii=False)
                room = int(self.cfg["prompt_cap_chars"]) - len(self.producer_prompt(iid, views[iid])) - 900
                if len(err) > max(room, 200):
                    err = err[:max(room, 200)] + " ...(cut)"
                extra = ((PROMPTS / "repair.txt").read_text(encoding="utf-8")
                         .replace("<<ROUND>>", str(rnd)).replace("<<ORDER>>", iid).replace("<<ERRORS>>", err))
            prompt = self.producer_prompt(iid, views[iid], "\n\n" + extra if extra else "")
            if len(prompt) > int(self.cfg["prompt_cap_chars"]):
                raise Fail(f"repair prompt for {iid} exceeds the cap")
            tag = "produce" if rnd == 0 else f"repair{rnd}"
            before = (lambda i=iid: self.fresh_sheet(i)) if rnd == 0 else (lambda i=iid, r=rnd: self.snapshot(i, r))
            items.append({"key": f"{tag}:{slug(iid)}", "label": f"{self.name}-{tag}-{slug(iid)}", "role": "producer",
                          "prompt": prompt, "id": iid, "before": before})
        return self.pool(items, "produce" if rnd == 0 else "repair")

    @staticmethod
    def produced_map(results):
        out = {}
        for iid, rec in results.items():
            if rec.get("over_item_cap"):
                out[iid] = f"worker over the item cap ({rec['over_item_cap']}); sheet held, not used"
            elif not rec.get("ok"):
                out[iid] = f"worker did not finish (exit {rec.get('exit')}, {rec.get('killed') or 'error'})"
            else:
                out[iid] = True
        return out

    def review_sets(self, claims, key):
        sets = {}
        chunk = int(self.cfg.get("review_chunk") or 0)
        rows_by_arm = {}
        for arm in "AB":
            rows = list(claims)
            random.Random(f"{key['salt']}-{arm}").shuffle(rows)
            rows_by_arm[arm] = rows
            parts = [rows[i:i + chunk] for i in range(0, len(rows), chunk)] if chunk else [rows]
            for k, part in enumerate(parts):
                d = self.reviews / f"{arm}{k}"
                write_jsonl(d / "REVIEW_SET.jsonl", part)
                sets[f"{arm}{k}"] = d
        return sets

    def reviewer_prompt(self, arm, d, mode):
        w = self.workers[f"reviewer_{arm}"]
        t = (PROMPTS / "reviewer.txt").read_text(encoding="utf-8")
        mode_text = (PROMPTS / ("reveal.txt" if mode == "after_reveal" else "blind.txt")).read_text(encoding="utf-8")
        out = d / ("AFTER_REVEAL.jsonl" if mode == "after_reveal" else "BLIND_REVIEW.jsonl")
        sub = {"<<MODE_RULES>>": mode_text.strip(), "<<REPO>>": self.repo.as_posix(), "<<REPO_BASH>>": bash_path(self.repo),
               "<<SET>>": (d / ("GENUINE.jsonl" if mode == "after_reveal" else "REVIEW_SET.jsonl")).as_posix(),
               "<<OUT>>": out.as_posix(), "<<SCRATCH>>": (d / "scratch").as_posix(),
               "<<PACKET>>": self.rel(self.packet), "<<RUN>>": self.rel(self.dir.parent),
               "<<REVIEWER>>": self.reviewer_name(arm), "<<MODEL_FAMILY>>": w.get("model_family", ""), "<<MODE>>": mode}
        for k, v in sub.items():
            t = t.replace(k, v)
        if len(t) > int(self.cfg["prompt_cap_chars"]):
            raise Fail(f"reviewer prompt exceeds the cap ({len(t)} chars)")
        return t

    def reviewer_name(self, arm):
        return f"maudslay-blind-reviewer-{self.name}-{arm}"

    def merge_reviews(self, arm, dirs, fname, hashes):
        recs, dropped = [], 0
        w = self.workers[f"reviewer_{arm}"]
        for d in dirs:
            for r in read_jsonl(d / fname):
                if not isinstance(r, dict) or r.get("claim_sha256") not in hashes or r.get("verdict") not in (
                        "upheld", "rejected", "upheld_after_reveal"):
                    dropped += 1
                    continue
                # The conveyor launched this fresh, separate session, so it states the session's identity itself;
                # the verdict, defects and reasons are the reviewer's own and are never changed.
                r.update(reviewer=self.reviewer_name(arm), model_family=w.get("model_family", "unknown"),
                         independent=True, separate_context=True, review_kind="independent_ai_source_review")
                r.setdefault("scope", "whole_case")
                if not isinstance(r.get("defects"), list):
                    r["defects"] = [r["defects"]] if r.get("defects") else []
                recs.append(r)
        path = self.packet / "reviews" / f"{fname[:-6]}_{arm}.jsonl"
        write_jsonl(path, recs)
        return {"records": len(recs), "dropped": dropped, "path": self.rel(path)}

    def run_reviews(self, mode, sets):
        items = []
        out = "AFTER_REVEAL.jsonl" if mode == "after_reveal" else "BLIND_REVIEW.jsonl"
        for name, d in sorted(sets.items()):
            arm = name[0]
            tag = "review" if mode == "blind" else "reveal"

            def aside(d=d):
                # A retried reviewer starts from an empty output file; the failed attempt's file is kept.
                if (d / out).exists():
                    k = 1
                    while (d / f"{out}.attempt-{k}").exists():
                        k += 1
                    os.replace(d / out, d / f"{out}.attempt-{k}")
            items.append({"key": f"{tag}:{name}", "label": f"{self.name}-{tag}-{name}", "role": f"reviewer_{arm}",
                          "prompt": self.reviewer_prompt(arm, d, mode), "id": name, "before": aside})
        res = self.pool(items, "review" if mode == "blind" else "reveal", retry_failed=True)
        bad = [k for k, r in res.items() if not r.get("ok")]
        if bad:
            raise Stop(f"{mode} review: worker(s) {bad} did not finish; rerun after checking them "
                       "(not scored as control misses)")
        return res

    # -- completion manifest (port of research/excavator/claude-nira-sweep-2026-10-29/make_completion.py,
    #    with Papinian finish_pair.py's two-arm rule) -----------------------------------------------------
    def manifest(self, applied, key, agree, adjudicator, pub):
        ref = lambda p, line=None: dict({"path": self.rel(p), "sha256": fsha(p)}, **({"line": line} if line else {}))
        lines = lambda p: {r.get("claim_sha256"): (i, r) for i, r in enumerate(
            (json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()), 1)} if Path(p).exists() else {}
        cpath = applied / "CLAIMS.proposed.jsonl"
        claims, agents = {}, set()
        for i, l in enumerate(cpath.read_text(encoding="utf-8").splitlines(), 1):
            if l.strip():
                c = json.loads(l)
                claims[c["instrument_id"]] = (i, canon(c))
                agents.add((c.get("claim_kit") or {}).get("agent"))
        if len(agents) != 1:
            raise Fail(f"claims name more than one producer agent: {sorted(map(str, agents))}")
        rv = self.packet / "reviews"
        files = {(m, a): rv / f"{m}_{a}.jsonl" for m in ("BLIND_REVIEW", "AFTER_REVEAL") for a in "AB"}
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
            arm = a["arm"]
            hit = idx[(mode, arm)].get(sha)
            if not hit:
                raise Fail(f"no {mode} record for {iid} in arm {arm}")
            m = {"instrument_id": iid, "outcome": "submit", "claim_sha256": sha, "claim": ref(cpath, line),
                 "publication_kind": "whole_case", "packet": pk}
            m["after_reveal_review" if iid in ctrl else "review"] = ref(files[(mode, arm)], hit[0])
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
                                      "rationale": f"Planted version: {k['defect']}. Rule fixed in advance (Papinian "
                                      "finish_pair.py): both independent blind arms (A and B) rejected that exact "
                                      "planted hash and named a date defect."}, indent=1, ensure_ascii=False) + "\n",
                          encoding="utf-8")
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


def bash_path(p):
    s = Path(p).as_posix()
    m = re.match(r"^([A-Za-z]):/(.*)$", s)
    return f"/{m.group(1).lower()}/{m.group(2)}" if m else s


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
        if cmd == "claude":
            w["command"] = list(CLAUDE_TEMPLATE)
            w["family"] = w.get("family") or "claude"
        elif cmd == "codex":
            w["command"] = list(CODEX_TEMPLATE)
            w["family"] = w.get("family") or "codex"
        elif isinstance(cmd, list):
            w.setdefault("family", "generic")
        else:
            raise Fail(f"{role}: command must be 'claude', 'codex' or a list")
        w.setdefault("model_family", {"claude": "Anthropic", "codex": "OpenAI"}.get(w["family"], "unknown"))
        out[role] = w
    return out


# ---------------------------------------------------------------------------------------------------------------
# The state machine


def run(cfg, repo=REPO):
    b = Batch(cfg, repo)
    L = b.ledger
    L.mark("run", "started", pid=os.getpid())
    adjudicate = []
    try:
        res = L.once("reserve", b.reserve)
        ids = res["ids"]
        prep = L.once("prepare", lambda: b.prepare(ids))
        prep["ids"] = ids
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
        pending = [i for i in go if not L.done(f"produce:{slug(i)}")]
        if pending:
            # A fresh dispatch check right before producers launch, on every (re)start that still launches any.
            n = len({r["key"] for r in L.rows if str(r.get("key", "")).startswith("dispatch:")})
            L.once(f"dispatch:{n + 1}", lambda: b.dispatch(pending))
        results = b.produce_round(0, go, views)
        produced = b.produced_map(results)
        for iid, v in produced.items():
            if v is not True and "item cap" in v:
                adjudicate.append({"instrument_id": iid, "kind": "over_item_cap", "blocks_completion": False,
                                   "detail": v})
        for iid in no_view:
            produced[iid] = "Geddes view failed; no producer launched"
        demoted = dict(L.data("demoted") or {})
        col = b.collect(prep, produced, demoted)
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
                rr = b.produce_round(rnd, failing, views, chk["failures"])
                for iid, v in b.produced_map(rr).items():
                    if v is not True:
                        demoted[iid] = f"repair round {rnd}: {v}"
            else:
                for iid in failing:
                    demoted[iid] = ("mechanical checks failed after "
                                    f"{rnd} repair round(s): {'; '.join(chk['failures'][iid])[:400]}")
                L.mark("demoted", "done", **demoted)
            col = b.collect(prep, produced, demoted)
            if not col["submit"]:
                raise Stop("check: zero orders submittable after the mechanical checks")
        applied = b.repo / chk["applied"]
        claims = read_jsonl(applied / "CLAIMS.proposed.jsonl")

        def plant():
            kp = b.keys / f"{b.name}.json"
            key = read_json(kp)
            if not key or key.get("applied") != chk["applied"]:
                salt = os.urandom(16).hex()
                rset, controls = plant_controls(claims, salt)
                key = {"batch": b.name, "applied": chk["applied"], "salt": salt, "controls": controls,
                       "sealed_utc": now()}
                write_json(kp, key)
                write_jsonl(b.keys / f"{b.name}.GENUINE.jsonl",
                            [c for c in claims if c["instrument_id"] in {k["instrument_id"] for k in controls}])
                write_jsonl(b.keys / f"{b.name}.REVIEW_SET.jsonl", rset)
            rset = read_jsonl(b.keys / f"{b.name}.REVIEW_SET.jsonl")
            sets = b.review_sets(rset, key)
            # Only counts and the key's hash go in the ledger, which sits in the repository beside the reviewers.
            return {"controls": len(key["controls"]), "key_sha256": fsha(kp), "claims": len(rset),
                    "sets": {k: b.rel(v) for k, v in sets.items()}}

        pl = L.once("plant", plant)
        kp = b.keys / f"{b.name}.json"
        if fsha(kp) != pl["key_sha256"]:
            raise Fail("the sealed control key changed after planting")
        key = read_json(kp)
        sets = {k: b.repo / v for k, v in pl["sets"].items()}
        rset = read_jsonl(b.keys / f"{b.name}.REVIEW_SET.jsonl")
        hashes = {canon(c) for c in rset}
        b.run_reviews("blind", sets)
        merged = L.once("merge:blind", lambda: {a: b.merge_reviews(a, [d for k, d in sets.items() if k[0] == a],
                                                                   "BLIND_REVIEW.jsonl", hashes) for a in "AB"})
        blind = {a: {r["claim_sha256"]: r for r in read_jsonl(b.repo / merged[a]["path"])} for a in "AB"}

        def score():
            rows = []
            for k in key["controls"]:
                ok = {a: caught(blind[a].get(k["planted"])) for a in "AB"}
                rows.append({"instrument_id": k["instrument_id"], "defect": k["defect"], "caught_A": ok["A"],
                             "caught_B": ok["B"], "caught": all(ok.values())})
            write_json(b.dir / "CONTROLS.json", {"rule": "caught only if both arms rejected the exact planted hash "
                                                 "and named a date defect (Papinian finish_pair.py)", "controls": rows})
            return {"missed": [r["instrument_id"] for r in rows if not r["caught"]], "controls": len(rows)}

        sc = L.once("controls", score)
        if sc["missed"]:
            gate_line(b, cfg, ids, col, filed=0, controls_missed=len(sc["missed"]))
            raise Stop(f"controls: planted control(s) missed by at least one arm: {sc['missed']}; batch not completed")
        genuine = read_jsonl(b.keys / f"{b.name}.GENUINE.jsonl")
        rsets = {}
        for arm in "AB":
            d = b.reviews / f"{arm}-reveal"
            if not (d / "GENUINE.jsonl").exists():
                write_jsonl(d / "GENUINE.jsonl", genuine)
            rsets[f"{arm}R"] = d
        b.run_reviews("after_reveal", rsets)
        ghash = {canon(c) for c in genuine}
        rm = L.once("merge:reveal", lambda: {a: b.merge_reviews(a, [rsets[f"{a}R"]], "AFTER_REVEAL.jsonl", ghash)
                                             for a in "AB"})
        after = {a: {r["claim_sha256"]: r for r in read_jsonl(b.repo / rm[a]["path"])} for a in "AB"}
        # Arm agreement. The conveyor files only what both arms upheld and blocks only what both rejected;
        # everything else goes to the coordinator.
        ctrl = {k["instrument_id"] for k in key["controls"]}
        agree, held = {}, []
        decisions = {d["instrument_id"]: d for d in (read_json(b.dir / "ADJUDICATION.json", {}) or {}).get("decisions", [])
                     if isinstance(d, dict) and d.get("instrument_id")}
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
                item = {"instrument_id": iid, "kind": "arm_disagreement" if ra and rb else "missing_review",
                        "blocks_completion": True, "claim_sha256": sha, "control_genuine": iid in ctrl,
                        "arm_A": {"verdict": va, "defects": (ra or {}).get("defects")},
                        "arm_B": {"verdict": vb, "defects": (rb or {}).get("defects")}}
                adjudicate.append(item)
                d = decisions.get(iid)
                if d and d.get("decision") == "file" and need in (va, vb):
                    agree[iid] = {"decision": "file", "arm": "A" if va == need else "B"}
                elif d and d.get("decision") == "block":
                    agree[iid] = {"decision": "block", "reason": "Coordinator adjudication (ADJUDICATION.json): "
                                  + str(d.get("reason") or "blocked")}
                elif cfg.get("defer_adjudication"):
                    agree[iid] = {"decision": "block", "reason": "The two blind arms disagreed; held for the "
                                  "coordinator's adjudication and not filed in this completion."}
                else:
                    held.append(iid)
        write_json(b.dir / "ADJUDICATE.json", {"schema": "maudslay-adjudicate/v1", "batch": b.name,
                                               "note": "The conveyor decides none of these. Write ADJUDICATION.json "
                                               "({\"decisions\":[{\"instrument_id\",\"decision\":\"file|block\","
                                               "\"reason\",\"adjudicator\"}]}) and re-run.",
                                               "items": adjudicate})
        if held:
            raise Pause(f"agree: {len(held)} order(s) await adjudication: {held}")
        adj = cfg.get("adjudicator") or f"{cfg['agent']}-coordinator-maudslay"

        def complete():
            mpath, man = b.manifest(applied, key, agree, adj, cfg["publication"])
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
        verdict = gate_line(b, cfg, ids, col, filed=done["published"], controls_missed=0)
        write_measures(b, cfg, ids, col, done, verdict)
        L.mark("run", "done", outcome="done", gate=(verdict or {}).get("decision"))
        if verdict and verdict.get("decision") == "STOP":
            return EXIT_GATE_STOP
        return EXIT_DONE
    except Stop as s:
        L.mark("run", "stopped", reason=str(s))
        write_measures(b, cfg, None, None, None, None, stopped=str(s))
        if adjudicate:
            write_json(b.dir / "ADJUDICATE.json", {"schema": "maudslay-adjudicate/v1", "batch": b.name, "items": adjudicate})
        print(json.dumps({"batch": b.name, "state": "stopped", "reason": str(s)}))
        return EXIT_STOPPED
    except Pause as p:
        L.mark("run", "paused", reason=str(p))
        write_measures(b, cfg, None, None, None, None, stopped=str(p))
        print(json.dumps({"batch": b.name, "state": "paused", "reason": str(p),
                          "adjudicate": b.rel(b.dir / "ADJUDICATE.json")}))
        return EXIT_PAUSED
    except Fail as f:
        L.mark("run", "failed", reason=str(f))
        print(json.dumps({"batch": b.name, "state": "failed", "reason": str(f)}))
        return EXIT_FAILED


def gate_line(b, cfg, ids, col, filed, controls_missed):
    """Upsert this batch's line in the wave's batch file, then run Bentham's gate on it."""
    usd, _ = b.spent()
    unknown = [w["label"] for w in b.ledger.workers() if w.get("usd") is None]
    line = {"batch": b.name, "attempted": len(ids), "submitted": len(col["submit"]) if col else 0, "filed": filed,
            "controls_missed": controls_missed, "usd": round(usd, 4)}
    bf = Path(cfg["batches_file"])
    bf = bf if bf.is_absolute() else b.repo / bf
    rows = read_json(bf, [])
    rows = rows["batches"] if isinstance(rows, dict) else (rows or [])
    rows = [r for r in rows if r.get("batch") != b.name] + [line]
    write_json(bf, rows)
    verdict = None
    if unknown:
        verdict = {"decision": None, "skipped": f"usd unknown for {len(unknown)} worker(s) (set prices_usd_per_mtok); "
                   "the gate was not run on a guessed cost"}
    else:
        rc, out = b.tool("gate", log="gate", batches=bf)
        try:
            verdict = json.loads(out)
        except ValueError:
            verdict = {"decision": None, "refused": f"gate exit {rc}: {out.strip()[:300]}"}
    b.ledger.mark(f"gate:{b.name}:{filed}:{controls_missed}", "done", line=line, verdict=verdict)
    return verdict


def write_measures(b, cfg, ids, col, done, verdict, stopped=None):
    stages = {}
    for w in b.ledger.workers():
        s = stages.setdefault(w.get("stage") or w["role"], {"workers": 0, "input": 0, "cache_read": 0, "cache_write": 0, "output": 0,
                                   "tokens": 0, "usd": 0.0, "usd_unknown_workers": 0, "wall_seconds": 0.0})
        s["workers"] += 1
        for k in ("input", "cache_read", "cache_write", "output", "tokens"):
            s[k] += int(w.get(k) or 0)
        if w.get("usd") is None:
            s["usd_unknown_workers"] += 1
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
                                            "killed", "over_item_cap", "prompt_chars")} for w in b.ledger.workers()],
         "totals": {"usd": round(usd, 4), "tokens": sum(s["tokens"] for s in stages.values()),
                    "attempted": len(ids) if ids else None, "submitted": len(col["submit"]) if col else None,
                    "filed": filed, "usd_per_filed": round(usd / filed, 4) if filed else None},
         "gate": verdict, "human_certified": 0,
         "note": "Tokens and dollars are the workers' own reported usage (claude -p total_cost_usd; codex exec "
                 "turn.completed usage priced from the workers file). The coordinator's own tokens are not here."}
    write_json(b.dir / "MEASURES.json", m)
    return m


# ---------------------------------------------------------------------------------------------------------------
# CLI


def build_config(a, repo):
    run_dir = Path(a.run_dir)
    bdir = (repo / run_dir / a.batch) if not run_dir.is_absolute() else run_dir / a.batch
    saved = read_json(bdir / "CONFIG.json")
    given = {k: getattr(a, k) for k in FIXED + MUTABLE if getattr(a, k, None) is not None}
    if saved:
        for k in FIXED:
            if k in given and given[k] != saved.get(k):
                raise Fail(f"{k} is fixed for batch {a.batch} (was {saved.get(k)!r}, now {given[k]!r}); start a new batch")
        cfg = dict(saved)
        cfg.update({k: v for k, v in given.items() if k in MUTABLE})
    else:
        for need in ("agent", "action", "route", "workers"):
            if not given.get(need):
                raise Fail(f"--{need.replace('_', '-')} is required for a new batch")
        name = Path(a.run_dir).name
        cfg = {"run_dir": Path(a.run_dir).as_posix(), "batch": a.batch, "n": 20, "parallel": 4,
               "prompt_cap_chars": 16000, "review_chunk": 0, "repair_rounds": 1, "item_timeout": 5400,
               "replacement_proposal": False, "publish": False, "defer_adjudication": False,
               "keys_dir": (Path(tempfile.gettempdir()) / "maudslay-keys" / name).as_posix(),
               "batches_file": (Path(a.run_dir) / "BATCHES.json").as_posix(),
               "publication": f"research/readiness/claims/{given['agent']}-{datetime.now(timezone.utc).date()}-"
                              f"{name}-{a.batch}.jsonl"}
        cfg.update(given)
    cfg["run_dir"] = Path(cfg["run_dir"]).as_posix()
    for k in ("route", "workers", "tools"):
        if cfg.get(k):
            p = Path(cfg[k])
            cfg[k] = (p if p.is_absolute() else (repo / p)).as_posix() if k != "route" else cfg[k]
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
    r.add_argument("--batch-usd", type=float, help="batch budget in dollars")
    r.add_argument("--batch-tokens", type=int, help="batch budget in tokens")
    r.add_argument("--prompt-cap-chars", type=int, help="hard cap on every rendered prompt (default 16000)")
    r.add_argument("--review-chunk", type=int, help="claims per reviewer session (0 = one session per arm)")
    r.add_argument("--repair-rounds", type=int, help="fresh producer sessions for mechanical failures (default 1)")
    r.add_argument("--defer-adjudication", action="store_true", default=None,
                   help="complete now and hold disagreed orders unfiled, instead of pausing")
    r.add_argument("--adjudicator", help="name recorded on control adjudications and seed receipts")
    r.add_argument("--keys-dir", help="sealed control keys, outside the repository")
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
            ws = load_workers(a.workers)
            for role, w in ws.items():
                argv_ = render_args(w["command"], {"model": w["model"], "max_turns": w.get("max_turns", 80),
                                                  "repo": REPO.as_posix(), "cwd": "BATCH_DIR", "prompt_file": "PROMPT",
                                                  "item_usd": a.item_usd,
                                                  "auto_compact_tokens": w.get("auto_compact_tokens", 120000),
                                                  "tool_output_tokens": w.get("tool_output_tokens", 6000),
                                                  "writable_roots": json.dumps(["BATCH_DIR", "GIT_DIR"]),
                                                  "network": "true" if w.get("network") else "false"})
                validate_worker_command(argv_, w["family"])
                print(role, " ".join(argv_), "< PROMPT")
            return 0
        repo = a.repo.resolve()
        cfg = build_config(a, repo)
        return run(cfg, repo)
    except Fail as f:
        print(json.dumps({"state": "failed", "reason": str(f)}))
        return EXIT_FAILED


if __name__ == "__main__":
    sys.exit(main())

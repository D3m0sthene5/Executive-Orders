#!/usr/bin/env python3
"""Sessions: sanitized per-agent token usage for every Claude Code session on this machine.

What it does
------------
Claude Code saves each session as one JSONL transcript, and each subagent it launches as another
JSONL transcript, under ``$CLAUDE_CONFIG_DIR/projects/<project>/`` and ``~/.claude/projects/<project>/``:

    <project>/<session-id>.jsonl                          the main (coordinating) agent
    <project>/<session-id>/subagents/agent-<id>.jsonl     one subagent (records have isSidechain true)
    <project>/<session-id>/subagents/agent-<id>.meta.json agentType, model alias, spawn depth

Hamilton (jobs/hamilton-token-audit/profile.py) already reads this JSONL shape. This module loads
Hamilton's own ``load`` and ``profile`` functions and uses the per-call ``usage_records`` they
produce (duplicates collapsed, streaming and final snapshots reconciled, cache-write time-to-live
classes kept apart). Nothing from Hamilton's accounting is reimplemented. Only if Hamilton refuses a
transcript (for example a malformed line or conflicting counts) does this module fall back to its
own extraction: the last ``usage`` object seen for each message id. Rows produced that way say
``fallback`` in ``hamilton_status`` and are not reconciled for conflicts.

What it writes
--------------
``AGENT_USAGE.csv`` in the column layout of
research/excavator/claude-tribonian-2026-11-04/telemetry/AGENT_USAGE.csv, plus three trailing
columns (``session_id``, ``active_seconds``, ``agent_type``). ``SUMMARY.json`` holds totals by phase,
by model family (opus, sonnet, haiku), by exact model, and by phase and family.

Rows hold only identifiers, timestamps, counts and labels. No prompt text, tool input, file
content or user message is written. Before writing, a guard collects every string from the message
content of the transcripts read (length 16 or more) and refuses to write if any appears inside the
output text.

What the numbers mean
---------------------
Token categories (fresh input, cache read, cache write, output) are separate and are never summed
together. ``wall_seconds`` is last record minus first record and includes waiting. ``active_seconds``
sums the gaps between consecutive records that are at most 300 seconds, so long waits do not count.
Neither is a measure of invoiced cost. A main transcript can span earlier work than the phase you
label it with; it is marked ``partial``. A category with no observed value stays null, not zero.
Output tokens from a transcript that never recorded a final count may be a lower bound.

Usage:
    python3 -I jobs/bentham/sessions.py --wave NAME (--phase LABEL | --phase-map FILE) --out DIR
        [--session-id ID] [--since ISO] [--claude-dir DIR ...]

``--phase-map`` is JSON mapping a key to a phase label. Keys are tried in order: an agent id, then
``session:<session id>``, then ``role:<agent type>`` (main agents have role ``coordinator``), then
``default``. Agents matching no key are labeled ``unlabeled``.
"""
import argparse
import collections
import csv
import importlib.util
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(os.environ.get("REPO_ROOT") or Path(__file__).resolve().parents[2])
HAMILTON = REPO_ROOT / "jobs" / "hamilton-token-audit" / "profile.py"
GAP_CAP_SECONDS = 300
MIN_GUARD_LEN = 16

COLUMNS = ["agent_id", "role", "phase", "batch", "model", "started_utc", "finished_utc", "wall_seconds", "calls",
           "fresh_input", "cache_read", "cache_write_5m", "cache_write_1h", "cache_write_unclassified", "output",
           "tool_uses", "bash_calls", "coverage_notes", "hamilton_status",
           "session_id", "active_seconds", "agent_type"]
CATS = ["fresh_input", "cache_read", "cache_write_5m", "cache_write_1h", "cache_write_unclassified", "output"]
MODEL_NAME = re.compile(r"^claude-[a-z0-9.-]+$")  # a model name that happens to be a whole content string is not private
SAFE_LABEL = re.compile(r"[^A-Za-z0-9_.:+-]")


class GuardError(RuntimeError):
    """Output text contains a string taken from transcript message content."""


def load_hamilton():
    spec = importlib.util.spec_from_file_location("hamilton_profile", HAMILTON)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def label(text, default="unknown"):
    return SAFE_LABEL.sub("_", str(text))[:80] or default


def parse_ts(text):
    if not text:
        return None
    try:
        d = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def family(model):
    m = re.search(r"(opus|sonnet|haiku)", model or "")
    return m.group(1) if m else "other"


# ---------------------------------------------------------------- discovery

def config_dirs(extra=()):
    dirs = [Path(d) for d in extra]
    if dirs:  # explicit directories replace the machine defaults
        return dirs
    if os.environ.get("CLAUDE_CONFIG_DIR"):
        dirs.append(Path(os.environ["CLAUDE_CONFIG_DIR"]))
    dirs.append(Path.home() / ".claude")
    seen, out = set(), []
    for d in dirs:
        r = d.resolve()
        if r not in seen:
            seen.add(r)
            out.append(d)
    return out


def first_record(path):
    with path.open(errors="replace") as f:
        for line in f:
            if line.strip():
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    return {}
                return r if isinstance(r, dict) else {}
    return {}


def discover(extra_dirs=(), session_id=None):
    """Return transcript descriptors: dicts with path, session_id, agent_id, role, kind, project."""
    found, seen = [], set()

    def add(path, session, agent_id, kind, project, meta):
        key = path.resolve()
        if key in seen:
            return
        seen.add(key)
        if session_id and not str(session).startswith(session_id):
            return
        role = "coordinator" if kind == "main" else label(meta.get("agentType") or "subagent")
        found.append({"path": path, "session_id": str(session), "agent_id": agent_id, "kind": kind,
                      "role": role, "project": project, "agent_type": None if kind == "main" else role})

    for cfg in config_dirs(extra_dirs):
        projects = cfg / "projects"
        if not projects.is_dir():
            continue
        for proj in sorted(p for p in projects.iterdir() if p.is_dir()):
            for f in sorted(proj.glob("*.jsonl")):
                head = first_record(f)
                if f.stem.startswith("agent-") or head.get("isSidechain") is True:
                    aid = head.get("agentId") or f.stem.removeprefix("agent-")
                    add(f, head.get("sessionId") or "unknown", label(aid), "subagent", proj.name, read_meta(f))
                else:
                    add(f, f.stem, "main-" + f.stem[:8], "main", proj.name, {})
            for sdir in sorted(d for d in proj.iterdir() if d.is_dir()):
                sub = sdir / "subagents"
                if not sub.is_dir():
                    continue
                for f in sorted(sub.glob("*.jsonl")):
                    aid = first_record(f).get("agentId") or f.stem.removeprefix("agent-")
                    add(f, sdir.name, label(aid), "subagent", proj.name, read_meta(f))
    return found


def read_meta(jsonl):
    p = jsonl.with_name(jsonl.stem + ".meta.json")
    try:
        d = json.loads(p.read_text())
        return d if isinstance(d, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


# ---------------------------------------------------------------- reading

def content_strings(path):
    """String leaves of message content, tool inputs and results, for the leak guard only."""
    out = set()

    def walk(x):
        if isinstance(x, str):
            if len(x.strip()) >= MIN_GUARD_LEN and not MODEL_NAME.match(x.strip()):
                out.add(x.strip())
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    for line in path.read_text(errors="replace").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(r, dict):
            continue
        msg = r.get("message")
        if isinstance(msg, dict):
            walk(msg.get("content"))
        for k in ("attachment", "toolUseResult", "wireToolInputs", "content", "summary"):
            if k in r:
                walk(r[k])
    return out


def count_tools(events):
    tools, bashes = set(), set()
    for _, kind, body in events:
        if kind != "assistant":
            continue
        c = (body.get("message") or {}).get("content")
        if isinstance(c, list):
            for b in c:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    tools.add(b.get("id"))
                    if b.get("name") == "Bash":
                        bashes.add(b.get("id"))
    return len(tools), len(bashes)


def fallback_records(events):
    """Last usage object per message id; used only when Hamilton refuses the transcript."""
    last = collections.OrderedDict()
    for ts, kind, body in events:
        msg = body.get("message") if kind == "assistant" else None
        if not isinstance(msg, dict) or not isinstance(msg.get("usage"), dict):
            continue
        u = msg["usage"]
        cc = u.get("cache_creation") or {}
        w5, w1 = cc.get("ephemeral_5m_input_tokens"), cc.get("ephemeral_1h_input_tokens")
        total = u.get("cache_creation_input_tokens")
        last[msg.get("id") or body.get("uuid") or ts] = {
            "model": msg.get("model"), "observed_at": ts,
            "tokens": {"input": u.get("input_tokens"), "read": u.get("cache_read_input_tokens"),
                       "write5m": w5, "write1h": w1, "output": u.get("output_tokens")},
            "cache_creation_tokens": total}
    return list(last.values())


def active_seconds(stamps):
    stamps = sorted(stamps)
    total = 0.0
    for a, b in zip(stamps, stamps[1:]):
        gap = (b - a).total_seconds()
        if gap <= GAP_CAP_SECONDS:
            total += gap
    return total


def add_tok(acc, key, value):
    if value is not None:
        acc[key] = acc.get(key, 0) + value


def read_agent(hp, t, since):
    """Return (row, cells). cells: one dict per model with token categories, for the summaries."""
    events = hp.load(t["path"])
    events = [e for e in events if (e[2].get("message") or {}).get("model") != "<synthetic>"]
    synthetic = len(hp.load(t["path"])) - len(events)
    if since:
        events = [e for e in events if (parse_ts(e[0]) or since) >= since]
    status = "ok"
    try:
        prof = hp.profile(events, label=t["agent_id"])
        records = prof["usage_records"]
    except (ValueError, KeyError, TypeError) as err:
        status = "fallback: Hamilton refused (%s: %s); last-usage-per-message extraction" % (
            type(err).__name__, str(err)[:80])
        records = fallback_records(events)
    stamps = [d for d in (parse_ts(e[0]) for e in events) if d]
    per_model = collections.OrderedDict()
    for r in records:
        tk = r["tokens"]
        m = r.get("model") or "unknown"
        c = per_model.setdefault(m, {"calls": 0})
        c["calls"] += 1
        add_tok(c, "fresh_input", tk.get("input"))
        add_tok(c, "cache_read", tk.get("read"))
        add_tok(c, "cache_write_5m", tk.get("write5m"))
        add_tok(c, "cache_write_1h", tk.get("write1h"))
        add_tok(c, "output", tk.get("output"))
        total = r.get("cache_creation_tokens")
        if total is not None and tk.get("write5m") is None and tk.get("write1h") is None:
            add_tok(c, "cache_write_unclassified", total)
        elif total is not None:
            add_tok(c, "cache_write_unclassified", max(total - (tk.get("write5m") or 0) - (tk.get("write1h") or 0), 0))
    notes = ["partial" if t["kind"] == "main" else "complete_interval"]
    if t["kind"] == "main":
        notes.append("main transcript can span work earlier than the labelled phase")
    if synthetic:
        notes.append("%d zero-usage client-generated '<synthetic>' message(s) excluded" % synthetic)
    if since:
        notes.append("calls before --since excluded")
    if len(per_model) > 1:
        notes.append("%d models in one transcript; row model is the most-called" % len(per_model))
    dominant = max(per_model, key=lambda m: per_model[m]["calls"]) if per_model else ""
    row = {"agent_id": t["agent_id"], "role": t["role"], "batch": "", "model": dominant,
           "started_utc": min(stamps).isoformat().replace("+00:00", "Z") if stamps else "",
           "finished_utc": max(stamps).isoformat().replace("+00:00", "Z") if stamps else "",
           "wall_seconds": round((max(stamps) - min(stamps)).total_seconds(), 3) if stamps else "",
           "calls": sum(c["calls"] for c in per_model.values()),
           "tool_uses": count_tools(events)[0], "bash_calls": count_tools(events)[1],
           "coverage_notes": "; ".join(notes), "hamilton_status": status,
           "session_id": t["session_id"], "active_seconds": round(active_seconds(stamps), 3) if stamps else "",
           "agent_type": t["agent_type"] or ""}
    for cat in CATS:
        vals = [c[cat] for c in per_model.values() if cat in c]
        row[cat] = sum(vals) if vals else ""
    return row, per_model


# ---------------------------------------------------------------- phases and summary

def phase_for(t, phase, phase_map):
    if phase:
        return label(phase)
    for key in (t["agent_id"], "session:" + t["session_id"], "role:" + t["role"], "default"):
        if key in phase_map:
            return label(phase_map[key])
    return "unlabeled"


def totals_into(acc, cell):
    acc["agents"] = acc.get("agents", 0)
    acc["calls"] = acc.get("calls", 0) + cell["calls"]
    for c in CATS:
        if c in cell:
            acc[c] = acc.get(c, 0) + cell[c]


def finish(acc):
    return {"agents": acc.get("agents", 0), "calls": acc.get("calls", 0), **{c: acc.get(c) for c in CATS}}


def summarize(wave, rows_cells, phase_source, since, session_id):
    by_phase, by_family, by_model, by_pf, overall = {}, {}, {}, {}, {}
    agents_seen = collections.defaultdict(set)
    for row, per_model in rows_cells:
        for model, cell in per_model.items():
            fam = family(model)
            for d, key in ((by_phase, row["phase"]), (by_family, fam), (by_model, model),
                           (by_pf, "%s|%s" % (row["phase"], fam)), (overall, "all")):
                acc = d.setdefault(key, {}) if d is not overall else overall
                totals_into(acc, cell)
                agents_seen[(id(d), key)].add(row["agent_id"] + "@" + row["session_id"])

    def fin(d):
        out = {}
        for k, v in sorted(d.items()):
            e = finish(v)
            e["agents"] = len(agents_seen[(id(d), k)])
            out[k] = e
        return out

    o = finish(overall)
    o["agents"] = len({r["agent_id"] + "@" + r["session_id"] for r, _ in rows_cells})
    return {
        "wave": wave,
        "generated_from": "Claude Code session transcripts via Hamilton profile.py (jobs/hamilton-token-audit); "
                          "per-call usage_records, sanitized by jobs/bentham/sessions.py",
        "phase_source": phase_source,
        "filters": {"session_id_prefix": session_id, "since": since.isoformat() if since else None},
        "token_categories_note": "fresh_input, cache_read, cache_write and output are separate, nonoverlapping "
                                 "categories and are never summed together. Null means no value observed.",
        "totals": o,
        "totals_by_phase": fin(by_phase),
        "totals_by_model_family": fin(by_family),
        "totals_by_model": fin(by_model),
        "totals_by_phase_and_family": fin(by_pf),
        "notes": ["Agents counted per grouping can overlap across groupings when one agent used several models.",
                  "Main (coordinator) transcripts are partial: they can span work earlier than the labelled phase.",
                  "Output tokens may be a lower bound where a call never recorded a final count.",
                  "Tokens are what transcripts recorded; they are not an invoice."],
    }


# ---------------------------------------------------------------- guard and write

def guard(texts, forbidden):
    for name, text in texts.items():
        for s in forbidden:
            if s in text:
                raise GuardError("refusing to write %s: it contains a string from transcript message content "
                                 "(%d characters, not shown)" % (name, len(s)))


def render(rows, summary):
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, COLUMNS, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return {"AGENT_USAGE.csv": buf.getvalue(), "SUMMARY.json": json.dumps(summary, indent=1) + "\n"}


def write_outputs(out, rows, summary, forbidden):
    texts = render(rows, summary)
    guard(texts, forbidden)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, text in texts.items():
        (out / name).write_text(text)
    return sorted(texts)


def run(wave, out, phase=None, phase_map=None, session_id=None, since=None, claude_dirs=()):
    hp = load_hamilton()
    transcripts = discover(claude_dirs, session_id)
    rows_cells, forbidden = [], set()
    for t in transcripts:
        row, per_model = read_agent(hp, t, since)
        row["phase"] = phase_for(t, phase, phase_map or {})
        row["batch"] = label(wave)
        if since and not row["calls"]:
            continue
        rows_cells.append((row, per_model))
        forbidden |= content_strings(t["path"])
    # Agent and session ids are the identifiers this tool exists to write; a parent transcript quotes them.
    forbidden -= {t["agent_id"] for t in transcripts} | {t["session_id"] for t in transcripts}
    rows_cells.sort(key=lambda rc: (rc[0]["started_utc"], rc[0]["agent_id"]))
    source = "--phase %s" % label(phase) if phase else "--phase-map"
    summary = summarize(label(wave), rows_cells, source, since, session_id)
    written = write_outputs(out, [r for r, _ in rows_cells], summary, forbidden)
    return summary, written, len(transcripts)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Sanitized per-agent token usage from Claude Code transcripts.")
    ap.add_argument("--wave", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--phase", help="one phase label for every agent")
    g.add_argument("--phase-map", help="JSON file mapping agent id, session:ID, role:TYPE or default to a phase")
    ap.add_argument("--out", required=True)
    ap.add_argument("--session-id", help="keep only sessions whose id starts with this")
    ap.add_argument("--since", help="ISO timestamp; calls before it are excluded")
    ap.add_argument("--claude-dir", action="append", default=[], help="extra Claude config directory (holds projects/)")
    a = ap.parse_args(argv)
    since = parse_ts(a.since) if a.since else None
    if a.since and since is None:
        ap.error("--since is not an ISO timestamp")
    pmap = json.loads(Path(a.phase_map).read_text()) if a.phase_map else None
    try:
        summary, written, n = run(a.wave, a.out, a.phase, pmap, a.session_id, since, a.claude_dir)
    except GuardError as err:
        print(str(err), file=sys.stderr)
        return 2
    print(json.dumps({"transcripts": n, "agents": summary["totals"]["agents"], "calls": summary["totals"]["calls"],
                      "wrote": [str(Path(a.out) / w) for w in written]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

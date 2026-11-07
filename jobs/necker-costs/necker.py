#!/usr/bin/env python3
"""Necker: dollars per worker and per claim batch, at Anthropic's API list prices.

Named for Jacques Necker, whose 1781 Compte rendu was the first public account of the French crown's finances.

What it does
------------
Bentham ranks agent work by yield per API-equivalent dollar, but its price table is fixed text in measure.py,
it prices every cache write at one rate, and the tokens-per-wave figures are not per batch. Necker prices recorded
tokens per message at the list price of the model that made the call (PRICES.json: input, output, 5-minute cache
write, 1-hour cache write, cache read), then adds the messages up per session, per worker (subagent), per model,
per day and per batch.

Three subcommands (standard library only; run with ``python3 -I``):

  transcripts PATH...   read Claude Code JSONL transcripts (files or directories; main sessions and
                        ``<session>/subagents/agent-*.jsonl``), write sanitized aggregates to --out
  telemetry   --wave W  CSV [--disposition JSON]
                        reprice a committed Bentham-format AGENT_USAGE.csv per batch (the claim waves ran in cloud
                        sessions whose transcripts are not on this PC; their token counts were committed as CSV)
  compare     CSV...    for waves Bentham already measured: raw token count, Bentham's dollars, Necker's dollars,
                        and what cache reads change
  validate    PATH...   check the price table against dollar totals the Claude Code CLI wrote into the transcripts
                        itself (``cost-state`` records) and against Herschel's ``cli_cost_usd`` (``--trace``)

What the numbers mean, and do not
---------------------------------
Every dollar figure is a list-price ESTIMATE of API-equivalent cost. It is not a bill. Under a Claude subscription
nothing is charged per token; the figure then measures relative size of work, not money owed.
A message is counted once however many transcript records repeat it (the largest value of each counter wins,
because streaming records carry partial counts). Output tokens include thinking tokens, as the API bills them.
Batch attribution uses only evidence in the transcript's own labels (see ``attribute``); everything else is reported
as unattributed, never guessed.

Privacy: outputs hold session-id hashes, agent ids, model ids, timestamps, token counts, dollars and batch labels
extracted by fixed patterns. No prompt, message text or tool input is copied. ``--out`` files are checked against
every string of 24 or more characters taken from the transcripts' message content before writing.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRICES_PATH = HERE / "PRICES.json"
CATS = ("input", "output", "cache_write_5m", "cache_write_1h", "cache_read")
MIN_GUARD_LEN = 24
MAX_BYTES = 5 * 1024 * 1024

# Bentham's table, copied (not imported) so this tool needs nothing from jobs/bentham.
BENTHAM_PRICES = {
    "sonnet": {"input": 3.0, "output": 15.0, "cache_read": 0.30, "cache_write": 3.75},
    "opus": {"input": 5.0, "output": 25.0, "cache_read": 0.50, "cache_write": 6.25},
}


# ---------------------------------------------------------------- prices

class Prices:
    def __init__(self, path=PRICES_PATH):
        self.doc = json.loads(Path(path).read_text(encoding="utf8"))
        self.models = [(re.compile(m["match"]), m) for m in self.doc["models"]]
        self.aliases = self.doc.get("aliases_for_telemetry_without_a_model_id", {})
        self.web_search = float(self.doc["rules"]["web_search_usd_per_1000"])

    def public_strings(self):
        """String values of PRICES.json (public, e.g. the pricing URL); a transcript may quote them."""
        out = set()

        def walk(x):
            if isinstance(x, str):
                out.add(x.strip())
            elif isinstance(x, dict):
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(self.doc)
        return out

    def entry(self, model):
        model = self.aliases.get(model, model) if model in ("opus", "sonnet", "haiku") else model
        for rx, m in self.models:
            if model and rx.search(model):
                return m
        return None

    def rates(self, model, usage_tokens, fast=False):
        """Per-MTok rates for one request, or None for an unknown model."""
        m = self.entry(model)
        if m is None:
            return None
        r = {c: float(m[c]) for c in ("input", "output", "cache_write_5m", "cache_write_1h", "cache_read")}
        thr = m.get("long_prompt_threshold_tokens")
        if thr and (usage_tokens.get("input", 0) + usage_tokens.get("cache_read", 0)
                    + usage_tokens.get("cache_write_5m", 0) + usage_tokens.get("cache_write_1h", 0)) > thr:
            r = {c: float(m["long_prompt"][c]) for c in r}
        if fast and m.get("fast_multiplier"):
            r = {c: v * m["fast_multiplier"] for c, v in r.items()}
        return r

    def cost(self, model, tokens, fast=False, web_searches=0):
        """Dollars for one request's tokens (a dict over CATS), or None if the model has no price."""
        r = self.rates(model, tokens, fast)
        if r is None:
            return None
        usd = sum(tokens.get(c, 0) * r[c] for c in CATS) / 1e6
        return usd + web_searches * self.web_search / 1000.0

    def breakdown(self, model, tokens, fast=False):
        r = self.rates(model, tokens, fast)
        return None if r is None else {c: tokens.get(c, 0) * r[c] / 1e6 for c in CATS}


def family(model):
    m = re.search(r"(opus|sonnet|haiku|fable|mythos)", model or "")
    return m.group(1) if m else "other"


def sha12(text):
    return hashlib.sha256(str(text).encode()).hexdigest()[:12]


def parse_ts(text):
    try:
        d = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def iso(d):
    return d.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if d else ""


# ---------------------------------------------------------------- reading transcripts

def find_transcripts(paths):
    out, seen = [], set()
    for p in paths:
        p = Path(p)
        files = [p] if p.is_file() else sorted(p.rglob("*.jsonl"))
        for f in files:
            r = f.resolve()
            if r not in seen:
                seen.add(r)
                out.append(f)
    return out


def meta_of(jsonl):
    p = jsonl.with_name(jsonl.stem + ".meta.json")
    try:
        d = json.loads(p.read_text(encoding="utf8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _int(x):
    return x if isinstance(x, int) and not isinstance(x, bool) and x >= 0 else 0


def read_file(path):
    """Return (messages, info). messages: message id -> record with the max of every counter seen."""
    msgs = collections.OrderedDict()
    info = {"first_user_text": None, "bash_text": [], "cost_states": [], "content_strings": set(),
            "records": 0, "session_id": None, "agent_id": None, "is_sidechain": False}
    with open(path, encoding="utf8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if not isinstance(r, dict):
                continue
            info["records"] += 1
            info["session_id"] = info["session_id"] or r.get("sessionId")
            info["agent_id"] = info["agent_id"] or r.get("agentId")
            info["is_sidechain"] = info["is_sidechain"] or r.get("isSidechain") is True
            t = r.get("type")
            if t == "cost-state":
                info["cost_states"].append(r)
                continue
            msg = r.get("message") if isinstance(r.get("message"), dict) else None
            if t == "user" and msg is not None:
                text = _text_of(msg.get("content"))
                if info["first_user_text"] is None and text:
                    info["first_user_text"] = text
                _collect_strings(msg.get("content"), info["content_strings"])
            if t != "assistant" or msg is None:
                continue
            _collect_strings(msg.get("content"), info["content_strings"])
            for b in msg.get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Bash":
                    cmd = (b.get("input") or {}).get("command")
                    if isinstance(cmd, str):
                        info["bash_text"].append(cmd)
            u = msg.get("usage")
            model = msg.get("model")
            if not isinstance(u, dict) or model in (None, "<synthetic>"):
                continue
            blocks = {}
            for b in msg.get("content") or []:
                n = _block_chars(b)
                if n:
                    blocks[hashlib.md5(json.dumps(b, sort_keys=True, ensure_ascii=False).encode()).hexdigest()] = n
            cc = u.get("cache_creation") if isinstance(u.get("cache_creation"), dict) else {}
            w5, w1 = _int(cc.get("ephemeral_5m_input_tokens")), _int(cc.get("ephemeral_1h_input_tokens"))
            total_w = _int(u.get("cache_creation_input_tokens"))
            cur = {"input": _int(u.get("input_tokens")), "output": _int(u.get("output_tokens")),
                   "cache_read": _int(u.get("cache_read_input_tokens")),
                   "cache_write_5m": w5, "cache_write_1h": w1, "cache_write_total": total_w,
                   "web_searches": _int((u.get("server_tool_use") or {}).get("web_search_requests")),
                   "fast": u.get("speed") == "fast", "final": bool(msg.get("stop_reason")), "blocks": blocks}
            mid = msg.get("id") or r.get("uuid")
            ts = parse_ts(r.get("timestamp"))
            prev = msgs.get(mid)
            if prev is None:
                cur.update(model=model, first_ts=ts, last_ts=ts, records=1)
                msgs[mid] = cur
            else:
                for k in ("input", "output", "cache_read", "cache_write_5m", "cache_write_1h", "cache_write_total",
                          "web_searches"):
                    prev[k] = max(prev[k], cur[k])
                prev["fast"] = prev["fast"] or cur["fast"]
                prev["final"] = prev["final"] or cur["final"]
                prev["blocks"].update(cur["blocks"])
                prev["records"] += 1
                if ts and (prev["last_ts"] is None or ts > prev["last_ts"]):
                    prev["last_ts"] = ts
                if ts and (prev["first_ts"] is None or ts < prev["first_ts"]):
                    prev["first_ts"] = ts
    return msgs, info


def _block_chars(b):
    """Characters the model wrote in one content block (text, thinking, tool name and input); signatures excluded."""
    if not isinstance(b, dict):
        return 0
    t = b.get("type")
    if t == "text":
        return len(b.get("text") or "")
    if t == "thinking":
        return len(b.get("thinking") or "")
    if t == "tool_use":
        return len(b.get("name") or "") + len(json.dumps(b.get("input"), ensure_ascii=False))
    return 0


def tokens_per_char(all_msgs):
    """Output tokens per written character, from messages whose output count is final (stop_reason recorded)."""
    out = chars = 0
    for m in all_msgs:
        c = sum(m["blocks"].values())
        if m["final"] and c >= 400 and m["output"] > 0:
            out += m["output"]
            chars += c
    return out / chars if chars else 0.0


def _text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(b.get("text", "") for b in content if isinstance(b, dict) and isinstance(b.get("text"), str))
    return ""


def _collect_strings(x, acc):
    if isinstance(x, str):
        if len(x.strip()) >= MIN_GUARD_LEN:
            acc.add(x.strip())
    elif isinstance(x, dict):
        for k, v in x.items():
            if k in ("id", "type", "name", "tool_use_id", "signature"):
                continue
            _collect_strings(v, acc)
    elif isinstance(x, list):
        for v in x:
            _collect_strings(v, acc)


def tokens_of(m):
    t = {c: m[c] for c in ("input", "output", "cache_read", "cache_write_5m", "cache_write_1h")}
    unclassified = max(m["cache_write_total"] - m["cache_write_5m"] - m["cache_write_1h"], 0)
    t["cache_write_5m"] += unclassified  # no TTL split: priced at the lower 5-minute rate
    return t, unclassified


# ---------------------------------------------------------------- attribution

LANE = re.compile(r"^Lane (\d+) (replica check|free printings|GPO page check|CSC page check|adjudication) ([a-z]\d+)(?: rerun)?\s*$")
LANE_KIND = {"replica check": "replica", "free printings": "free", "GPO page check": "gpo", "CSC page check": "csc",
             "adjudication": "adjudication"}
PRODUCE = re.compile(r"^(produce|review):([A-Za-z0-9_.-]{1,32})\s*$")
GATE_CALL = re.compile(r"bentham\.py\s+gate\s+--action\s+([A-Za-z0-9_.-]+)")
PACKET = re.compile(r"research/(?:production|excavator)/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")


def attribute(meta, first_prompt, bash_text, action_ids=()):
    """Return (label, kind, note) for one worker, or (None, None, reason).

    Evidence, strongest first; a worker is attributed only when its strongest evidence names exactly one batch:
      description  the Workflow tool's task label is exactly ``produce:<batch>`` or ``review:<batch>``, or
                   ``Lane <n> <kind> <code>`` (the description in <agent>.meta.json; only the matched ids are kept)
      gate_call    a Bash command runs ``bentham.py gate --action <ID>`` with exactly one known Bentham action id
    Weaker evidence is recorded but NOT counted as attribution (kind ``weak:...``, label kept in ``weak_label``):
    the first message names exactly one ``research/production|excavator/<name>/<segment>`` path, or exactly one
    Bentham action id. A question about a packet or an action is not the same as running it.
    """
    desc = str(meta.get("description") or "").strip()
    m = PRODUCE.match(desc)
    if m:
        return f"{m.group(2)}", "description:" + m.group(1), ""
    m = LANE.match(desc)
    if m:
        return f"lane{m.group(1)}.{LANE_KIND[m.group(2)]}.{m.group(3)}", "description:lane", ""
    paths = {"/".join(p) for p in PACKET.findall(first_prompt or "")}
    paths = {p for p in paths if not p.startswith(("...", "."))}
    packet = None
    if len(paths) == 1:
        packet = paths.pop()
    elif len(paths) > 1:
        return None, None, "first message names several packet paths"
    known = set(action_ids)
    gate_ids = {m for cmd in bash_text or [] for m in GATE_CALL.findall(cmd) if m in known}
    if len(gate_ids) == 1:
        return gate_ids.pop(), "gate_call", ""
    if len(gate_ids) > 1:
        return None, None, "several Bentham action ids gated"
    if packet:
        return packet, "weak:packet_path_mention", "named in the first message only"
    ids = {a for a in known if re.search(r"(?<![A-Za-z0-9_.-])" + re.escape(a) + r"(?![A-Za-z0-9_-])", first_prompt or "")}
    if len(ids) == 1:
        return ids.pop(), "weak:action_id_mention", "named in the first message only"
    return None, None, "no batch label in the transcript"


# ---------------------------------------------------------------- aggregation

def new_acc():
    a = {c: 0 for c in CATS}
    a.update(usd=0.0, usd_no_cache_discount=0.0, messages=0, unpriced_messages=0, unclassified_cache_write=0,
             web_searches=0, usd_by_cat={c: 0.0 for c in CATS},
             messages_output_not_final=0, output_repair_tokens=0, usd_repair=0.0)
    return a


def add(acc, tokens, usd, naive, brk, unclassified=0, web=0, repair=(0, 0.0, 0)):
    acc["output_repair_tokens"] += repair[0]
    acc["usd_repair"] += repair[1]
    acc["messages_output_not_final"] += repair[2]
    for c in CATS:
        acc[c] += tokens[c]
    acc["messages"] += 1
    acc["unclassified_cache_write"] += unclassified
    acc["web_searches"] += web
    if usd is None:
        acc["unpriced_messages"] += 1
        return
    acc["usd"] += usd
    acc["usd_no_cache_discount"] += naive
    for c in CATS:
        acc["usd_by_cat"][c] += brk[c]


def naive_usd(prices, model, tokens, fast=False):
    """What the same call costs if cache reads and writes are lumped with full-price input (the old estimate)."""
    r = prices.rates(model, tokens, fast)
    if r is None:
        return None
    lumped = tokens["input"] + tokens["cache_read"] + tokens["cache_write_5m"] + tokens["cache_write_1h"]
    return (lumped * r["input"] + tokens["output"] * r["output"]) / 1e6


def rounded(acc):
    o = {k: v for k, v in acc.items() if k != "usd_by_cat"}
    for k in ("usd", "usd_no_cache_discount", "usd_repair"):
        o[k] = round(o[k], 4)
    o["usd_by_cat"] = {c: round(v, 4) for c, v in acc["usd_by_cat"].items()}
    return o


def analyze(paths, prices, action_ids=(), until=None):
    """Read transcripts and return the aggregate structures (no private text)."""
    files = find_transcripts(paths)
    workers = {}            # (session_hash, worker_id) -> dict
    by_model, by_day, by_session = {}, {}, {}
    by_model_day, by_session_model = {}, {}
    guard, cost_states, dup_records = set(), [], 0
    loaded = [(f,) + read_file(f) for f in files]
    tpc = tokens_per_char(m for _, msgs, _ in loaded for m in msgs.values())
    for f, msgs, info in loaded:
        guard |= info["content_strings"]
        meta = meta_of(f) if (f.parent.name == "subagents" or f.stem.startswith("agent-")) else {}
        sidechain = info["is_sidechain"] or f.parent.name == "subagents" or f.stem.startswith("agent-")
        session = info["session_id"] or (f.parent.parent.name if f.parent.name == "subagents" else f.stem)
        sh = sha12(session)
        worker = (info["agent_id"] or f.stem.removeprefix("agent-")) if sidechain else "main"
        for cs in info["cost_states"]:
            cost_states.append(cs)
        if not msgs:
            continue
        label, kind, note = (None, None, "coordinator transcript: its cost is not split across batches")
        if sidechain:
            label, kind, note = attribute(meta, info["first_user_text"], info["bash_text"], action_ids)
        weak = ""
        if kind and kind.startswith("weak:"):
            weak, label = label, None
        w = workers.setdefault((sh, worker), {
            "session": sh, "worker": worker, "role": ("worker:" + str(meta.get("agentType") or "subagent")) if sidechain else "coordinator",
            "requested_model": meta.get("model") or "", "batch": label or "", "attribution": kind or "", "weak_label": weak,
            "attribution_note": note, "first": None, "last": None, "acc": new_acc(), "models": collections.Counter()})
        for mid, m in msgs.items():
            if until and m["first_ts"] and m["first_ts"] > until:
                continue
            dup_records += m["records"] - 1
            tok, uncl = tokens_of(m)
            usd = prices.cost(m["model"], tok, m["fast"], m["web_searches"])
            naive = naive_usd(prices, m["model"], tok, m["fast"])
            brk = prices.breakdown(m["model"], tok, m["fast"])
            day = (m["first_ts"] or datetime.min.replace(tzinfo=timezone.utc)).astimezone(timezone.utc).date().isoformat()
            targets = [w["acc"], by_model.setdefault(m["model"], new_acc()), by_day.setdefault(day, new_acc()),
                       by_session.setdefault(sh, new_acc()), by_model_day.setdefault((day, m["model"]), new_acc()),
                       by_session_model.setdefault((sh, m["model"]), new_acc())]
            repair = (0, 0.0, 0)
            if not m["final"]:
                est = int(round(sum(m["blocks"].values()) * tpc))
                extra = max(est - m["output"], 0)
                r = prices.rates(m["model"], tok, m["fast"])
                repair = (extra, extra * r["output"] / 1e6 if r else 0.0, 1)
            for acc in targets:
                add(acc, tok, usd, naive, brk, uncl, m["web_searches"], repair)
            w["models"][m["model"]] += 1
            for ts in (m["first_ts"], m["last_ts"]):
                if ts and (w["first"] is None or ts < w["first"]):
                    w["first"] = ts
                if ts and (w["last"] is None or ts > w["last"]):
                    w["last"] = ts
    workers = {k: w for k, w in workers.items() if w["acc"]["messages"]}
    return {"files": len(files), "workers": workers, "by_model": by_model, "by_day": by_day, "by_session": by_session,
            "by_model_day": by_model_day, "by_session_model": by_session_model, "tokens_per_char": tpc, "guard": guard, "cost_states": cost_states, "duplicate_records_collapsed": dup_records}


def attribution_summary(workers):
    total = sum(w["acc"]["usd"] for w in workers.values())
    parts = {"coordinator": 0.0, "attributed": 0.0, "unattributed_worker": 0.0}
    counts = {"coordinator": 0, "attributed": 0, "unattributed_worker": 0}
    for w in workers.values():
        k = "coordinator" if w["role"] == "coordinator" else ("attributed" if w["batch"] else "unattributed_worker")
        parts[k] += w["acc"]["usd"]
        counts[k] += 1
    worker_total = parts["attributed"] + parts["unattributed_worker"]
    by_kind = collections.Counter()
    for w in workers.values():
        if w["batch"]:
            by_kind[w["attribution"]] += w["acc"]["usd"]
    weak = sum(w["acc"]["usd"] for w in workers.values() if w.get("weak_label"))
    return {"total_usd": round(total, 2), "weak_label_usd_not_counted": round(weak, 2),
            "usd": {k: round(v, 2) for k, v in parts.items()}, "transcripts": counts,
            "attributed_share_of_all": round(parts["attributed"] / total, 4) if total else None,
            "attributed_share_of_worker_cost": round(parts["attributed"] / worker_total, 4) if worker_total else None,
            "attributed_usd_by_evidence": {k: round(v, 2) for k, v in sorted(by_kind.items())}}


def batch_table(workers):
    rows = {}
    for w in workers.values():
        if not w["batch"]:
            continue
        b = rows.setdefault(w["batch"], {"batch": w["batch"], "workers": 0, "evidence": set(), "acc": new_acc(),
                                         "first": None, "last": None, "usd_production": 0.0, "usd_review": 0.0,
                                         "usd_other": 0.0})
        b["usd_production" if w["attribution"] == "description:produce" else
          "usd_review" if w["attribution"] == "description:review" else "usd_other"] += w["acc"]["usd"]
        b["workers"] += 1
        b["evidence"].add(w["attribution"])
        for c in CATS:
            b["acc"][c] += w["acc"][c]
        for k in ("usd", "usd_no_cache_discount", "messages", "unpriced_messages", "usd_repair",
                  "messages_output_not_final"):
            b["acc"][k] += w["acc"][k]
        for k in ("first", "last"):
            if w[k] and (b[k] is None or (w[k] < b[k] if k == "first" else w[k] > b[k])):
                b[k] = w[k]
    return sorted(rows.values(), key=lambda r: (r["first"] or datetime.max.replace(tzinfo=timezone.utc), r["batch"]))


# ---------------------------------------------------------------- telemetry (Bentham-format CSV)

TEL_COLS = ("fresh_input", "cache_read", "cache_write_5m", "cache_write_1h", "cache_write_unclassified", "output")


def _n(x):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return 0


def row_tokens(r):
    return {"input": _n(r.get("fresh_input")), "output": _n(r.get("output")), "cache_read": _n(r.get("cache_read")),
            "cache_write_5m": _n(r.get("cache_write_5m")) + _n(r.get("cache_write_unclassified")),
            "cache_write_1h": _n(r.get("cache_write_1h"))}


def bentham_usd(model, tok):
    fam = "opus" if "opus" in model else "sonnet"
    p = BENTHAM_PRICES[fam]
    cw = tok["cache_write_5m"] + tok["cache_write_1h"]
    return (tok["input"] * p["input"] + tok["output"] * p["output"] + tok["cache_read"] * p["cache_read"]
            + cw * p["cache_write"]) / 1e6


def reprice_csv(path, prices):
    """Rows of a Bentham AGENT_USAGE.csv priced per agent. Batch-less rows keep an empty batch."""
    out = []
    with open(path, newline="", encoding="utf8") as f:
        for r in csv.DictReader(f):
            tok = row_tokens(r)
            model = r.get("model") or ""
            usd = prices.cost(model, tok)
            out.append({"agent_id": r.get("agent_id"), "role": r.get("role"), "phase": r.get("phase"),
                        "batch": r.get("batch") or "", "model": model, "started_utc": r.get("started_utc"),
                        "finished_utc": r.get("finished_utc"), "tokens": tok, "calls": _n(r.get("calls")),
                        "usd": usd, "usd_no_cache_discount": naive_usd(prices, model, tok),
                        "usd_bentham": bentham_usd(model, tok) if usd is not None else None,
                        "brk": prices.breakdown(model, tok)})
    return out


def load_disposition(path):
    d = json.loads(Path(path).read_text(encoding="utf8"))
    out = {}
    for b in d.get("batches", []):
        v = b.get("blind_review_verdicts") or {}
        controls = b.get("controls") or []
        out[b["batch"]] = {"attempted": b.get("attempted"), "filed": b.get("claims_filed"),
                           "submitted": (v.get("upheld") or 0) + (v.get("rejected") or 0) if v else None,
                           "controls_missed": sum(1 for c in controls if c.get("caught") is False)}
    return out


def batch_rows_from_telemetry(wave, rows, disp):
    by = collections.OrderedDict()
    for r in sorted(rows, key=lambda r: (r["started_utc"] or "", r["agent_id"])):
        if r["usd"] is None:
            continue
        b = by.setdefault(r["batch"], {"wave": wave, "batch": r["batch"], "workers": 0, "usd": 0.0, "usd_production": 0.0,
                                       "usd_review": 0.0, "usd_other": 0.0, "usd_no_cache_discount": 0.0,
                                       "usd_bentham": 0.0, "cache_read_tokens": 0, "started_utc": r["started_utc"]})
        b["workers"] += 1
        b["usd"] += r["usd"]
        b["usd_no_cache_discount"] += r["usd_no_cache_discount"]
        b["usd_bentham"] += r["usd_bentham"]
        b["cache_read_tokens"] += r["tokens"]["cache_read"]
        k = {"production": "usd_production", "review": "usd_review"}.get(r["phase"], "usd_other")
        b[k] += r["usd"]
    out = []
    for name, b in by.items():
        d = disp.get(name) if disp else None
        b["composite"] = 1 if "+" in name else 0
        b["attempted"] = d["attempted"] if d else ""
        b["submitted"] = d["submitted"] if d and d["submitted"] is not None else ""
        b["filed"] = d["filed"] if d else ""
        b["controls_missed"] = d["controls_missed"] if d else ""
        out.append(b)
    return out


# ---------------------------------------------------------------- output

BATCH_COLS = ["wave", "batch", "attempted", "submitted", "filed", "controls_missed", "usd", "workers", "usd_production",
              "usd_review", "usd_other", "usd_no_cache_discount", "usd_bentham", "cache_read_tokens", "composite",
              "started_utc", "usd_repaired", "messages_output_not_final"]
GATE_COLS = ["batch", "attempted", "submitted", "filed", "controls_missed", "usd"]


def csv_text(cols, rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, cols, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({c: (round(r[c], 4) if isinstance(r.get(c), float) else r.get(c, "")) for c in cols})
    return buf.getvalue()


class GuardError(RuntimeError):
    pass


def write_files(out, texts, guard=()):
    total = 0
    for name, text in texts.items():
        for s in guard:
            if s in text:
                raise GuardError("refusing to write %s: it contains a string from transcript message content" % name)
        total += len(text.encode())
        if len(text.encode()) > MAX_BYTES:
            raise GuardError("%s exceeds %d bytes" % (name, MAX_BYTES))
    if total > 20 * 1024 * 1024:
        raise GuardError("output over 20 MiB")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, text in texts.items():
        p = out / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf8"))
    budget = json.dumps({"files": {n: len(t.encode()) for n, t in texts.items()}, "total_bytes": total}, indent=1)
    (out / "BUDGET.json").write_bytes((budget + "\n").encode())
    return total


WORKER_COLS = ["session", "worker", "role", "model", "requested_model", "batch", "attribution", "weak_label", "started_utc",
               "finished_utc", "messages", "input", "output", "cache_write_5m", "cache_write_1h", "cache_read", "usd",
               "usd_no_cache_discount", "unpriced_messages", "messages_output_not_final", "usd_repaired"]


def cmd_transcripts(a):
    prices = Prices(a.prices)
    action_ids = json.loads(Path(a.action_ids).read_text()) if a.action_ids else []
    until = parse_ts(a.until) if a.until else None
    res = analyze(a.paths, prices, action_ids, until)
    workers = res["workers"]
    wrows = []
    for w in sorted(workers.values(), key=lambda w: (w["first"] or datetime.max.replace(tzinfo=timezone.utc), w["worker"])):
        acc = w["acc"]
        wrows.append({**{k: w[k] for k in ("session", "worker", "role", "requested_model", "batch", "attribution",
                                                      "weak_label")},
                      "model": w["models"].most_common(1)[0][0], "started_utc": iso(w["first"]),
                      "finished_utc": iso(w["last"]), "messages": acc["messages"], **{c: acc[c] for c in CATS},
                      "usd": acc["usd"], "usd_no_cache_discount": acc["usd_no_cache_discount"],
                      "unpriced_messages": acc["unpriced_messages"],
                      "messages_output_not_final": acc["messages_output_not_final"],
                      "usd_repaired": acc["usd"] + acc["usd_repair"]})
    brows = []
    for b in batch_table(workers):
        acc = b["acc"]
        brows.append({"wave": "local-transcripts", "batch": b["batch"], "workers": b["workers"], "usd": acc["usd"],
                      "usd_no_cache_discount": acc["usd_no_cache_discount"], "cache_read_tokens": acc["cache_read"],
                      "usd_repaired": acc["usd"] + acc["usd_repair"],
                      "usd_production": b["usd_production"], "usd_review": b["usd_review"], "usd_other": b["usd_other"],
                      "messages_output_not_final": acc["messages_output_not_final"], "started_utc": iso(b["first"]), "attempted": "", "submitted": "", "filed": "",
                      "controls_missed": "", "composite": 0})
    total = new_acc()
    for acc in res["by_model"].values():
        for k in ("input", "output", "cache_write_5m", "cache_write_1h", "cache_read", "usd", "usd_no_cache_discount",
                  "messages", "unpriced_messages", "usd_repair", "messages_output_not_final", "output_repair_tokens"):
            total[k] += acc[k]
        for c in CATS:
            total["usd_by_cat"][c] += acc["usd_by_cat"][c]
    unpriced = sorted(m for m, acc in res["by_model"].items() if acc["unpriced_messages"])
    summary = {
        "schema": "necker-summary/v1", "wave": a.wave, "messages_after_cutoff_excluded": a.until or None,
        "what_this_is": "API list-price ESTIMATES of cost from recorded tokens. Not bills. Under a subscription nothing "
                        "here is charged per token.",
        "prices": {"file": "PRICES.json", "source_url": prices.doc["source_url"], "retrieved": prices.doc["retrieved"]},
        "transcript_files": res["files"], "duplicate_records_collapsed": res["duplicate_records_collapsed"],
        "totals": rounded(total), "unpriced_models": unpriced,
        "by_model": {m: rounded(acc) for m, acc in sorted(res["by_model"].items())},
        "by_day": {d: rounded(acc) for d, acc in sorted(res["by_day"].items())},
        "by_day_and_model": {"%s|%s" % k: rounded(acc) for k, acc in sorted(res["by_model_day"].items())},
        "attribution": attribution_summary(workers),
        "sessions": len(res["by_session"]), "workers": sum(1 for w in workers.values() if w["role"] != "coordinator"),
        "cache_read_effect": cache_effect(total),
        "output_repair": {
            "what": "Some transcripts record a call's output token count at the start of streaming only (no stop_reason "
                    "was ever written for the message), so recorded output is a lower bound. usd_repaired adds "
                    "(characters the model wrote x measured output tokens per character on messages with a final count) "
                    "minus the recorded output, priced at the model's output rate. It is an estimate; the CLI's own "
                    "cost-state totals are the reference where they exist.",
            "tokens_per_character": round(res["tokens_per_char"], 4),
            "messages_output_not_final": total["messages_output_not_final"],
            "messages": total["messages"],
            "output_tokens_added": total["output_repair_tokens"],
            "usd_repair": round(total["usd_repair"], 2), "usd_repaired_total": round(total["usd"] + total["usd_repair"], 2)},
    }
    recon = cost_state_reconciliation(res)
    cli_by_session = recon.pop("_rows")
    summary["cost_state_reconciliation"] = recon
    sess_rows = [{"session": s, "cli_reported_usd": cli_by_session.get(s, ""),
                  "usd_repaired": acc["usd"] + acc["usd_repair"],
                  **{k: rounded(acc)[k] for k in ("messages", "input", "output", "cache_write_5m",
                                                  "cache_write_1h", "cache_read", "usd")}}
                 for s, acc in sorted(res["by_session"].items(), key=lambda kv: -kv[1]["usd"])]
    texts = {"SUMMARY.json": json.dumps(summary, indent=1) + "\n",
             "WORKER_COSTS.csv": csv_text(WORKER_COLS, wrows),
             "BATCH_COSTS.csv": csv_text(BATCH_COLS, brows),
             "SESSION_COSTS.csv": csv_text(["session", "messages", "input", "output", "cache_write_5m", "cache_write_1h",
                                            "cache_read", "usd", "cli_reported_usd", "usd_repaired"], sess_rows)}
    n = write_files(a.out, texts, res["guard"] - prices.public_strings())
    print(json.dumps({"files": res["files"], "usd_total": summary["totals"]["usd"], "bytes": n,
                      "attribution": summary["attribution"]}, indent=1))
    return 0


def cost_state_reconciliation(res):
    """Compare transcript-derived dollars with the CLI's own running total for the same sessions.

    Some transcripts record output tokens at the start of streaming only, so transcript output (and dollars) can
    understate; the CLI's ``cost-state`` record is the reference where one exists.
    """
    latest = {}
    for cs in res["cost_states"]:
        sid = sha12(cs.get("sessionId"))
        if sid not in latest or (cs.get("totalCostUSD") or 0) >= (latest[sid].get("totalCostUSD") or 0):
            latest[sid] = cs
    rep = mine = rpr = 0.0
    rows = {}
    for sid, cs in latest.items():
        if sid not in res["by_session"] or not isinstance(cs.get("totalCostUSD"), (int, float)):
            continue
        rows[sid] = cs["totalCostUSD"]
        rep += cs["totalCostUSD"]
        mine += res["by_session"][sid]["usd"]
        rpr += res["by_session"][sid]["usd"] + res["by_session"][sid]["usd_repair"]
    return {"sessions_with_cli_total": len(rows), "cli_reported_usd": round(rep, 2), "necker_same_sessions_usd": round(mine, 2),
            "necker_over_cli": round(mine / rep, 4) if rep else None,
            "necker_repaired_same_sessions_usd": round(rpr, 2),
            "necker_repaired_over_cli": round(rpr / rep, 4) if rep else None,
            "gap_usd": round(rep - mine, 2),
            "note": "cost-state totals are written during a session and may predate its last messages; where the "
                    "ratio is below 1, transcript output tokens are probably understated (streaming-start counts)",
            "_rows": rows}


def cache_effect(acc):
    """How much of the priced dollar figure is cache reads, and what a lumped estimate would have said."""
    usd = acc["usd"]
    reads = acc["usd_by_cat"]["cache_read"]
    return {"usd_priced": round(usd, 2), "usd_cache_reads": round(reads, 2),
            "cache_reads_share_of_priced_usd": round(reads / usd, 4) if usd else None,
            "usd_if_cache_reads_and_writes_were_full_price_input": round(acc["usd_no_cache_discount"], 2),
            "lumped_over_priced": round(acc["usd_no_cache_discount"] / usd, 3) if usd else None}


def cmd_telemetry(a):
    prices = Prices(a.prices)
    rows = reprice_csv(a.csv, prices)
    disp = load_disposition(a.disposition) if a.disposition else {}
    brows = batch_rows_from_telemetry(a.wave, rows, disp)
    wrows = [{"session": a.wave, "worker": r["agent_id"], "role": r["role"], "model": r["model"], "requested_model": "",
              "batch": r["batch"], "attribution": "telemetry_csv_batch_column", "started_utc": r["started_utc"],
              "finished_utc": r["finished_utc"], "messages": r["calls"], **r["tokens"], "usd": r["usd"],
              "usd_no_cache_discount": r["usd_no_cache_discount"],
              "unpriced_messages": 0 if r["usd"] is not None else 1} for r in rows]
    texts = {"BATCH_COSTS.csv": csv_text(BATCH_COLS, brows), "WORKER_COSTS.csv": csv_text(WORKER_COLS, wrows)}
    gate = [b for b in brows if not b["composite"] and b["attempted"] != "" and b["batch"] and
            not re.match(r"^(c\d+|lind-|rereview)", b["batch"])]
    gate = sorted(gate, key=lambda b: b["started_utc"] or "")
    if gate:
        texts["gate_%s.csv" % a.wave] = csv_text(GATE_COLS, gate)
    write_files(a.out, texts)
    print(json.dumps({"wave": a.wave, "agents": len(rows), "batches": len(brows), "gate_rows": len(gate),
                      "usd": round(sum(r["usd"] or 0 for r in rows), 2)}, indent=1))
    return 0


def wave_totals(rows):
    t = {"agents": len(rows), "tokens": collections.Counter(), "usd_necker": 0.0, "usd_bentham": 0.0,
         "usd_no_cache_discount": 0.0, "usd_cache_reads": 0.0, "usd_cache_writes": 0.0, "usd_input": 0.0, "usd_output": 0.0}
    for r in rows:
        if r["usd"] is None:
            continue
        for k, v in r["tokens"].items():
            t["tokens"][k] += v
        t["usd_necker"] += r["usd"]
        t["usd_bentham"] += r["usd_bentham"]
        t["usd_no_cache_discount"] += r["usd_no_cache_discount"]
        t["usd_cache_reads"] += r["brk"]["cache_read"]
        t["usd_cache_writes"] += r["brk"]["cache_write_5m"] + r["brk"]["cache_write_1h"]
        t["usd_input"] += r["brk"]["input"]
        t["usd_output"] += r["brk"]["output"]
    return t


def cmd_compare(a):
    prices = Prices(a.prices)
    result = {"what_this_is": "API-price estimates for waves Bentham already measured. Not bills; not charges under a "
                              "subscription.",
              "columns": {
                  "tokens_total": "fresh input + output + cache read + cache write, summed (a size, not a price)",
                  "usd_bentham": "Bentham measure.py table: Sonnet 3/15/0.30/3.75, Opus 5/25/0.50/6.25, both cache-write "
                                 "kinds at one rate",
                  "usd_necker": "per-model list price of the model in the row (PRICES.json), 5m and 1h writes apart",
                  "usd_lumped": "every input-side token (fresh, cache read, cache write) at the full input price, "
                                "output at the output price, current rates: the estimate that lumps cache reads with "
                                "full-price input"}, "waves": []}
    for spec in a.csv:
        wave, _, path = spec.partition("=")
        rows = reprice_csv(path, prices)
        t = wave_totals(rows)
        tok = t["tokens"]
        total_tokens = sum(tok.values())
        result["waves"].append({
            "wave": wave, "agents": t["agents"], "tokens": dict(tok), "tokens_total": total_tokens,
            "cache_read_share_of_tokens": round(tok["cache_read"] / total_tokens, 4) if total_tokens else None,
            "usd_bentham": round(t["usd_bentham"], 2), "usd_necker": round(t["usd_necker"], 2),
            "usd_lumped": round(t["usd_no_cache_discount"], 2),
            "necker_over_bentham": round(t["usd_necker"] / t["usd_bentham"], 3) if t["usd_bentham"] else None,
            "lumped_over_necker": round(t["usd_no_cache_discount"] / t["usd_necker"], 3) if t["usd_necker"] else None,
            "usd_necker_by_kind": {"fresh_input": round(t["usd_input"], 2), "output": round(t["usd_output"], 2),
                                   "cache_read": round(t["usd_cache_reads"], 2),
                                   "cache_write": round(t["usd_cache_writes"], 2)},
            "cache_read_share_of_necker_usd": round(t["usd_cache_reads"] / t["usd_necker"], 4) if t["usd_necker"] else None})
    texts = {"COMPARISON.json": json.dumps(result, indent=1) + "\n", "COMPARISON.md": comparison_md(result)}
    write_files(a.out, texts)
    print(texts["COMPARISON.md"])
    return 0


def comparison_md(res):
    L = ["# Token-count and Bentham estimates against Necker's priced estimate", "",
         "API-price estimates, not bills. Under a subscription none of these dollars is charged.", "",
         "| Wave | Agents | Total tokens | Cache reads, share of tokens | Bentham USD | Necker USD | Necker / Bentham | "
         "Lumped USD | Lumped / Necker | Cache reads, share of Necker USD |",
         "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for w in res["waves"]:
        L.append("| %s | %d | %s | %.1f%% | %s | %s | %.2f | %s | %.2f | %.1f%% |" % (
            w["wave"], w["agents"], f"{w['tokens_total']:,}", 100 * (w["cache_read_share_of_tokens"] or 0),
            f"{w['usd_bentham']:,.2f}", f"{w['usd_necker']:,.2f}", w["necker_over_bentham"] or 0,
            f"{w['usd_lumped']:,.2f}", w["lumped_over_necker"] or 0, 100 * (w["cache_read_share_of_necker_usd"] or 0)))
    L += ["", "Columns: " + " ".join("`%s` %s." % kv for kv in res["columns"].items()), ""]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- validate

def cmd_validate(a):
    prices = Prices(a.prices)
    latest = {}
    n_states = 0
    for f in find_transcripts(a.paths):
        _, info = read_file(f)
        for cs in info["cost_states"]:
            n_states += 1
            sid = cs.get("sessionId") or f.stem
            if sid not in latest or (cs.get("totalCostUSD") or 0) >= (latest[sid].get("totalCostUSD") or 0):
                latest[sid] = cs
    rows = []
    for sid, cs in sorted(latest.items()):
        for model, mu in (cs.get("modelUsage") or {}).items():
            reported = mu.get("costUSD")
            tok = {"input": _int(mu.get("inputTokens")), "output": _int(mu.get("outputTokens")),
                   "cache_read": _int(mu.get("cacheReadInputTokens")), "cache_write_5m": 0,
                   "cache_write_1h": 0}
            w = _int(mu.get("cacheCreationInputTokens"))
            c5 = prices.cost(model, {**tok, "cache_write_5m": w}, web_searches=_int(mu.get("webSearchRequests")))
            c1 = prices.cost(model, {**tok, "cache_write_1h": w}, web_searches=_int(mu.get("webSearchRequests")))
            rows.append({"session": sha12(sid), "model": model, "reported_cli_usd": reported, "necker_all_5m": c5,
                         "necker_all_1h": c1, "tokens": {**tok, "cache_creation": w}})
    ok = [r for r in rows if isinstance(r["reported_cli_usd"], (int, float)) and r["necker_all_1h"] is not None
          and r["reported_cli_usd"] > 0]
    out = {"what_this_is": "Does PRICES.json reproduce the dollar total the Claude Code CLI itself recorded? "
                           "cost-state records carry the CLI's own running cost per model; both cache-write TTL "
                           "assumptions are shown.",
           "cost_state_records": n_states, "sessions": len(latest), "model_rows": len(rows),
           "by_model": {}, "rows": [{**r, "necker_all_5m": round(r["necker_all_5m"] or 0, 4),
                                     "necker_all_1h": round(r["necker_all_1h"] or 0, 4)} for r in rows]}
    for m in sorted({r["model"] for r in ok}):
        sub = [r for r in ok if r["model"] == m]
        rep = sum(r["reported_cli_usd"] for r in sub)
        out["by_model"][m] = {"rows": len(sub), "reported_cli_usd": round(rep, 4),
                              "necker_all_1h_usd": round(sum(r["necker_all_1h"] for r in sub), 4),
                              "necker_all_5m_usd": round(sum(r["necker_all_5m"] for r in sub), 4),
                              "ratio_all_1h_over_reported": round(sum(r["necker_all_1h"] for r in sub) / rep, 5) if rep else None,
                              "max_abs_rel_error_all_1h": round(max(abs(r["necker_all_1h"] / r["reported_cli_usd"] - 1) for r in sub), 5)}
    until = parse_ts(a.until) if a.until else None
    mine = analyze(a.paths, prices, (), until)["by_session_model"]
    cmp_rows = []
    for r in rows:
        acc = mine.get((r["session"], r["model"]))
        if acc is None or not r["reported_cli_usd"]:
            continue
        cmp_rows.append({"session": r["session"], "model": r["model"], "reported_cli_usd": round(r["reported_cli_usd"], 4),
                         "necker_from_transcript_usd": round(acc["usd"], 4),
                         "necker_repaired_usd": round(acc["usd"] + acc["usd_repair"], 4),
                         "repaired_ratio": round((acc["usd"] + acc["usd_repair"]) / r["reported_cli_usd"], 4),
                         "ratio": round(acc["usd"] / r["reported_cli_usd"], 4),
                         "transcript_output_over_cli_output": round(acc["output"] / r["tokens"]["output"], 4) if r["tokens"]["output"] else None,
                         "transcript_cache_read_over_cli": round(acc["cache_read"] / r["tokens"]["cache_read"], 4) if r["tokens"]["cache_read"] else None})
    out["per_session_vs_cli"] = {
        "note": "cost-state is written at the end of a session and may predate later messages; transcript totals include "
                "subagents of the session as separate files, so a ratio below 1 can mean subagent files are missing from "
                "the PATH given, and above 1 means messages after the last cost-state record",
        "rows": cmp_rows}
    if a.trace:
        out["herschel_trace"] = validate_trace(a.trace, prices)
    texts = {"VALIDATION.json": json.dumps(out, indent=1) + "\n"}
    write_files(a.out, texts)
    print(json.dumps({k: out[k] for k in ("cost_state_records", "sessions", "model_rows", "by_model")}, indent=1))
    if a.trace:
        print(json.dumps(out["herschel_trace"]["summary"], indent=1))
    return 0


def validate_trace(path, prices):
    rows = []
    for line in Path(path).read_text(encoding="utf8").splitlines():
        if not line.strip():
            continue
        t = json.loads(line)
        tk = t.get("tokens") or {}
        tok = {"input": _n(tk.get("fresh_input")), "output": _n(tk.get("output")), "cache_read": _n(tk.get("cache_read")),
               "cache_write_5m": _n(tk.get("cache_write_5m")) + _n(tk.get("cache_write_unclassified")),
               "cache_write_1h": _n(tk.get("cache_write_1h"))}
        fam = t.get("model") or ""
        usd = prices.cost(fam, tok)
        fast = prices.cost(fam, tok, fast=True)
        rows.append({"worker": t.get("worker"), "model": fam, "cli_cost_usd": t.get("cli_cost_usd"), "necker_usd": usd,
                     "necker_if_fast_mode_usd": fast,
                     "usd_bentham": t.get("usd_bentham")})
    ok = [r for r in rows if r["cli_cost_usd"] and r["necker_usd"] is not None]
    cli = sum(r["cli_cost_usd"] for r in ok)
    nk = sum(r["necker_usd"] for r in ok)
    bn = sum(r["usd_bentham"] or 0 for r in ok)
    return {"summary": {"workers": len(ok), "cli_cost_usd": round(cli, 4), "necker_usd": round(nk, 4),
                        "usd_bentham": round(bn, 4), "necker_over_cli": round(nk / cli, 4) if cli else None,
                        "bentham_over_cli": round(bn / cli, 4) if cli else None,
                        "note": "model is the alias recorded in TRACE.jsonl, read as the current model of that family"},
            "by_model": {m: {"workers": sum(1 for r in ok if r["model"] == m),
                             "cli_cost_usd": round(sum(r["cli_cost_usd"] for r in ok if r["model"] == m), 4),
                             "necker_usd": round(sum(r["necker_usd"] for r in ok if r["model"] == m), 4),
                             "necker_if_fast_mode_usd": round(sum(r["necker_if_fast_mode_usd"] or 0 for r in ok if r["model"] == m), 4),
                             "usd_bentham": round(sum(r["usd_bentham"] or 0 for r in ok if r["model"] == m), 4)}
                         for m in sorted({r["model"] for r in ok})},
            "rows": [{**r, "necker_usd": round(r["necker_usd"], 4),
                      "necker_if_fast_mode_usd": round(r["necker_if_fast_mode_usd"] or 0, 4)} for r in ok]}


# ---------------------------------------------------------------- merge

def cmd_merge(a):
    """Concatenate the per-source BATCH_COSTS.csv / WORKER_COSTS.csv files into one pair, and record input hashes."""
    texts = {}
    for name, cols in (("BATCH_COSTS.csv", BATCH_COLS), ("WORKER_COSTS.csv", WORKER_COLS)):
        rows = []
        for d in a.dirs:  # columns are matched by name; a source without a column leaves it empty
            p = Path(d) / name
            if p.exists():
                rows += list(csv.DictReader(io.StringIO(p.read_text(encoding="utf8"))))
        texts[name] = csv_text(cols, rows)
    inputs = {}
    for f in a.inputs or []:
        inputs[Path(f).name] = {"sha256": hashlib.sha256(Path(f).read_bytes()).hexdigest(),
                                "bytes": Path(f).stat().st_size}
    texts["INPUTS.json"] = json.dumps({"inputs": inputs, "note": a.note or ""}, indent=1) + "\n"
    n = write_files(a.out, texts)
    print(json.dumps({"bytes": n, "files": sorted(texts)}))
    return 0


# ---------------------------------------------------------------- main

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--prices", default=str(PRICES_PATH))
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("transcripts")
    s.add_argument("paths", nargs="+")
    s.add_argument("--out", required=True)
    s.add_argument("--wave", default="local-transcripts")
    s.add_argument("--until", help="ISO time; messages first seen after it are left out (the live session keeps growing)")
    s.add_argument("--action-ids", help="JSON list of Bentham action ids to look for in worker prompts and Bash commands")
    s.set_defaults(fn=cmd_transcripts)
    s = sub.add_parser("telemetry")
    s.add_argument("csv")
    s.add_argument("--wave", required=True)
    s.add_argument("--disposition")
    s.add_argument("--out", required=True)
    s.set_defaults(fn=cmd_telemetry)
    s = sub.add_parser("compare")
    s.add_argument("csv", nargs="+", help="WAVE=path/to/AGENT_USAGE.csv")
    s.add_argument("--out", required=True)
    s.set_defaults(fn=cmd_compare)
    s = sub.add_parser("validate")
    s.add_argument("paths", nargs="+")
    s.add_argument("--until", help="ISO time; later messages are left out")
    s.add_argument("--trace", help="Herschel TRACE.jsonl with cli_cost_usd")
    s.add_argument("--out", required=True)
    s.set_defaults(fn=cmd_validate)
    s = sub.add_parser("merge")
    s.add_argument("dirs", nargs="+")
    s.add_argument("--out", required=True)
    s.add_argument("--inputs", nargs="*")
    s.add_argument("--note")
    s.set_defaults(fn=cmd_merge)
    a = p.parse_args(argv)
    try:
        return a.fn(a)
    except GuardError as e:
        print(str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

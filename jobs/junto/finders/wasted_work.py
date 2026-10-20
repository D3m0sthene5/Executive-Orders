"""Gallatin: the wasted-work miner, a Junto finder (finder id F-wasted_work).

Named for Albert Gallatin, Jefferson's Secretary of the Treasury, who audited the
government's spending, cut what produced nothing and paid down the debt. This finder
audits saved agent transcripts for tokens spent on work that was later blocked,
rejected, undone, superseded or thrown away, and prices it.

What it counts, per session (numbers only, never any transcript text):
  rejected_call     a tool call the user or harness refused (permission denied, blocked)
  failed_retry      a large model-written payload (script, file body) whose call failed and
                    was redone with a similar call within three calls
  superseded_write  a file body written and then overwritten or deleted before anything
                    used it (sub-kinds: overwritten, removed)
  unused_write      a file body written and never referenced again (no later tool call,
                    reply or blanket git add mentions it); the weakest signal
  task_stopped      a background command or monitor the model started and later killed
  aborted_agent     a subagent that never handed back, or whose launch call failed
  superseded_agent  the same subagent description launched twice (the earlier run is waste)
  blocked_output    producer work on rows that ended blocked: the producer's hand-back reports
                    "N of M rows blocked"; that share of its cost bought no claim (blocking is a
                    valid outcome; the saver is an early screen, not fewer blocks)
  rejected_review   producer work a reviewer subagent rejected: the reviewer's hand-back
                    reports "N of M rejected"; that share of the producer's cost is waste
  user_correction   the model's recent work before a user message that corrects it
                    (matched by a short list of cue words; only a flag leaves this script)

Pricing follows Hamilton (jobs/hamilton-token-audit/profile.py): every model call is split
into fresh input, output, the fixed setup it re-reads, and the history it re-reads. Here
the split is kept at the finest grain (call x item) so each piece is charged to at most one
waste event, in priority order, and the total can never exceed the session total.
Dollars use the session's own get_session cost_usd when the transcript is complete
(coverage of cache reads at least 90%); a partly saved session is priced at the median
dollars per unit of the complete ones and is flagged "profile_scaled".

Every figure is an upper bound on what a saver could remove: it assumes the saver prevents
all of the waste. Everything emitted is status "unverified". Estimates rank work and never
count as savings (research/plans/JUNTO_DESIGN.md).

usage (the Junto finder interface):
  python3 -I jobs/junto/finders/wasted_work.py --data DIR --out FILE --run-id R-yyyymmdd-n [--profiles DIR]
FILE ending in .json gets one JSON document (candidates, per-session figures, sanity check);
any other name gets one candidate per line (JSON Lines). FILE.run.json gets the run record.
Exit codes: 0 ok, 2 bad or empty input (or a failed sanity check), 3 privacy refusal.
"""
import argparse
import collections
import datetime
import difflib
import hashlib
import importlib.util
import json
import posixpath
import re
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
HAMILTON = HERE.parents[2] / "hamilton-token-audit" / "profile.py"

FINDER_ID = "F-wasted_work"
VERSION = "1"
MIN_USD = 0.25            # emit a candidate only when its attributed cost reaches this
COMPLETE_COVERAGE = 0.90  # saved cache reads / reported cache reads needed to price a session by its own cost
RETRY_WINDOW = 3          # a failed call counts as redone if a similar call follows within 3 calls
PAYLOAD_MIN = 150         # tokens: smaller payloads are not counted as wasted file bodies or scripts
TURN_CALL_CAP = 40        # a user correction charges at most the last 40 main-agent calls before it
STOP_AFTER_S = 1800       # an agent with no hand-back counts as aborted only if the session ran this long after it
MIN_BASENAME = 4          # shorter file names are too ambiguous to match by name

# category -> (cause key, saver key, title, proposed test)
CATS = {
    "rejected_call": ("wasted_rejected_call", "permission_preapproval",
                      "Letter of Marque: pre-approve safe commands before the model writes them",
                      "Same task twice, with and without an allowlist; measure refused calls and usd per accepted unit."),
    "failed_retry": ("wasted_failed_retry", "preflight_checks",
                     "Sentinel: check paths, tools and syntax before long scripts run",
                     "Same job with a preflight step; measure failed-then-redone calls and usd per unit."),
    "superseded_write": ("wasted_superseded_write", "fair_copy_write_once",
                         "Fair copy: outline first, write each file once, then edit",
                         "Same task with a write-once rule (outline, one write, edits only); measure files overwritten unused and usd per unit."),
    "unused_write": ("wasted_unused_write", "fair_copy_write_once",
                     "Fair copy: write only files a later step will read or commit",
                     "Same task with an output manifest listing each file's consumer; measure unreferenced files and usd per unit."),
    "task_stopped": ("wasted_task_stopped", "watchman_external_monitoring",
                     "Watchman: wait outside the large session; do not start waits it will kill",
                     "Next long merge or build with an external wake-up instead of in-session waits; measure killed tasks and usd."),
    "aborted_agent": ("wasted_aborted_agent", "agent_charter_guard",
                      "Charter: give each agent a scope, a deadline and a return check",
                      "Same agent batch with a return-check and stop rule; measure agents that never hand back and usd per unit."),
    "superseded_agent": ("wasted_superseded_agent", "agent_registry_dedupe",
                         "Register of Patents: look for an equivalent agent before launching",
                         "Same batch with a launch registry; measure repeated agent launches and usd per unit."),
    "blocked_output": ("wasted_blocked_output", "early_triage_gate",
                       "Customs House: screen rows for sources before full production",
                       "Same batch with a cheap source-availability screen before the producer runs; measure rows blocked after full work and usd per accepted unit."),
    "rejected_review": ("wasted_rejected_review", "producer_precheck",
                        "Grand Jury: cheap pre-screen of producer output before full review",
                        "Same batch with a pre-screen that routes weak items back early; measure rejected share and usd per accepted unit."),
    "user_correction": ("wasted_user_correction", "intent_echo_first",
                        "Quorum: restate the ask in one line and confirm before long work",
                        "Same prompts with a one-line restatement step; measure user corrections and usd per accepted unit."),
}
ORDER = ["rejected_call", "failed_retry", "superseded_write", "unused_write", "task_stopped",
         "aborted_agent", "superseded_agent", "blocked_output", "rejected_review", "user_correction"]

PERM_RE = re.compile(
    r"^(<tool_use_error>)?(Permission for (this|the) \w+ was denied|Blocked:|Permission to use .{0,80} has been denied|"
    r"The user doesn't want to proceed|User rejected|.{0,80}requested permissions? to use .{0,80}haven't granted)", re.S)
BG_RE = re.compile(r"moved to the background \(ID: ([\w-]+)\)")
HEREDOC_RE = re.compile(r"\b(?:cat|tee)\s+(?:-a\s+)?>?\s*(\"[^\"]+\"|'[^']+'|[^\s<>|;&]+)\s*<<", re.S)
RM_RE = re.compile(r"(?:^|[;&|\n]\s*)(?:sudo\s+)?rm\s+(?:-\w+\s+)*([^;&|\n]+)")
GIT_DISCARD_RE = re.compile(r"\bgit\s+(?:checkout\s+(?:--\s+|-f\b)|restore\b|clean\b|reset\s+--hard|stash\s+drop|"
                            r"(?:merge|rebase|cherry-pick)\s+--abort)")
GIT_BLANKET_RE = re.compile(r"\bgit\s+(?:add\s+(?:-A|--all|\.|-u)(?:\s|$)|commit\s+(?:-\w*a\w*|--all)\b)")
CORRECTION_RE = re.compile(
    r"\b(misinterpret\w*|misunderstood|misunderstand\w*|i meant|not what i (?:asked|meant|wanted)|that'?s not what|"
    r"thats not what|that'?s wrong|you(?:'| a)re wrong|undo that|revert that|you keep (?:saying|doing)|"
    r"why did you|stop (?:giving|doing|adding|it\b)|are you insane|i didn'?t ask|i never asked|don'?t do that)\b", re.I)
SYSTEM_PROMPT_PREFIX = ("<", "Another Claude session sent a message", "Stop hook feedback", "Base directory for this skill",
                        "[Image", "Caveat:")
STOP_TOKENS = {"reviewer", "producer", "independent", "review", "for", "of", "the", "and", "round", "a", "an", "to", "in"}


def load_hamilton():
    spec = importlib.util.spec_from_file_location("hamilton_profile", str(HAMILTON))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def result_text(c):
    return c if isinstance(c, str) else json.dumps(c)


def parse_ts(s):
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return 0.0


def base_of(p):
    p = (p or "").strip().strip("\"'")
    return posixpath.basename(p.rstrip("/"))


# ---------------------------------------------------------------------------------------
# Pass 1: rebuild calls, items, tool uses and results from the transcript events
# ---------------------------------------------------------------------------------------
def parse_handback(text):
    """Counts only (no text is kept). Returns a dict of numbers found in a subagent's hand-back, or None."""
    t = text.lower()
    rej_hits = [int(x) for x in re.findall(r"(\d+)\s+(?:are\s+|is\s+|were\s+)?reject\w*", t)]
    rej_hits += [int(x) for x in re.findall(r"reject\w*[ :]+(\d+)\b", t)]
    back_hits = [int(x) for x in re.findall(r"(\d+)\s+(?:\w+\s+)?(?:are\s+|is\s+|were\s+)?sent back", t)]
    acc_hits = [int(x) for x in re.findall(r"(\d+)\s+accept\w*", t)]
    corr_hits = [int(x) for x in re.findall(r"(\d+)\s+accept\w*[ _]with[ _]correction\w*", t)]
    tot_hits = [int(x) for x in re.findall(r"(\d+)\s+(?:p\d\s+|x\d+\s+)?(?:orders|proposals|records|members|rules|claims|rows|items)\b", t)]
    said = [int(x) for x in re.findall(r"reviewed\s+(?:all\s+)?(\d+)", t)]
    blocked = [int(x) for x in re.findall(r"(\d+)\s+blocked", t)]
    submitted = [int(x) for x in re.findall(r"(\d+)\s+(?:of\s+\d+\s+rows\s+)?submit", t)]
    other = [int(x) for x in re.findall(r"(\d+)\s+(?:unresolved|route_owner)", t)]
    rows_of = [int(x) for x in re.findall(r"\d+\s+of\s+(\d+)\s+rows", t)]
    out = {"is_review": bool(re.search(r"\breviewed\b|\breview of\b|_rev\b", t))}
    if rej_hits or back_hits:
        rejected = max(sum(rej_hits), max(back_hits or [0]))
        reviewed = max(said) if said else max(tot_hits or [sum(acc_hits) + rejected])
        out.update({"rejected": rejected, "corrected": sum(corr_hits), "reviewed": max(reviewed, rejected)})
    if blocked:
        total = max(rows_of or [sum(blocked) + sum(submitted) + sum(other)])
        out.update({"blocked": max(blocked), "rows": max(total, max(blocked))})
    return out if len(out) > 1 else None


def rebuild(H, events):
    calls = collections.OrderedDict()
    items = {}
    uses = {}
    results = []
    texts = []             # (event no, searchable assistant text), for "was it mentioned" checks
    prompts = []           # (event no, call count so far, is_correction)
    handbacks = {}         # agent tool_use id -> (rejected, corrected, reviewed)
    pending = []
    seq = 0
    cur_msg_items = None
    for evn, (ts, kind, body) in enumerate(events):
        cat = body.get("internal_anthropic_catchall") or {}
        msg = cat.get("message") or body.get("message")
        if not isinstance(msg, dict):
            continue
        agent = cat.get("parent_tool_use_id") or "main"
        if kind == "assistant":
            mid = msg.get("id")
            u = msg.get("usage") or {}
            if mid not in calls:
                cc = u.get("cache_creation") or {}
                w1h = cc.get("ephemeral_1h_input_tokens", 0)
                w5m = cc.get("ephemeral_5m_input_tokens", u.get("cache_creation_input_tokens", 0) - w1h)
                calls[mid] = {"idx": len(calls), "ts": parse_ts(ts), "evn": evn, "agent": agent,
                              "read": u.get("cache_read_input_tokens", 0), "write5m": max(w5m, 0), "write1h": w1h,
                              "input": u.get("input_tokens", 0), "output": u.get("output_tokens", 0),
                              "triggers": list(pending), "emitted": [], "turn": len(prompts)}
                pending = []
            call = calls[mid]
            for b in msg.get("content") or []:
                bt = b.get("type")
                if bt == "tool_use":
                    inp = b.get("input") or {}
                    name = b.get("name", "")
                    raw = json.dumps(inp)
                    seq += 1
                    items[seq] = {"tokens": len(raw) / 4, "agent": agent}
                    cmd = inp.get("command", "") if name == "Bash" else ""
                    path = inp.get("file_path", "") if name in ("Write", "Edit") else ""
                    uses[b.get("id")] = {"id": b.get("id"), "item": seq, "call": call["idx"], "agent": agent, "name": name,
                                         "label": H.tool_label(name, inp), "cmd": cmd, "path": path,
                                         "evn": evn, "payload": len(raw) / 4,
                                         "search": raw[:20000], "desc": inp.get("description", "") if name == "Agent" else "",
                                         "prompt": (inp.get("prompt") or "")[:3000] if name == "Agent" else "",
                                         "task_id": inp.get("task_id", "") if name == "TaskStop" else ""}
                    if name == "SubagentHandback":
                        hb = parse_handback(str(inp.get("message", "")))
                        if hb:
                            handbacks[agent] = hb
                        uses[b.get("id")]["handback_of"] = agent
                    call["emitted"].append(seq)
                    pending.append(seq)
                elif bt == "text":
                    tx = b.get("text") or ""
                    seq += 1
                    items[seq] = {"tokens": len(tx) / 4, "agent": agent}
                    call["emitted"].append(seq)
                    pending.append(seq)
                    texts.append((evn, tx[:20000]))
        elif kind == "user":
            content = msg.get("content")
            if isinstance(content, list):
                for b in content:
                    if b.get("type") == "tool_result":
                        tx = result_text(b.get("content"))
                        seq += 1
                        items[seq] = {"tokens": len(tx) / 4, "agent": agent}
                        results.append({"use_id": b.get("tool_use_id"), "item": seq, "agent": agent, "evn": evn,
                                        "is_error": bool(b.get("is_error")), "head": tx[:400], "text": tx[:3000]})
                        pending.append(seq)
                    elif b.get("type") == "text":
                        tx = b.get("text") or ""
                        seq += 1
                        items[seq] = {"tokens": len(tx) / 4, "agent": agent}
                        pending.append(seq)
            elif isinstance(content, str):
                seq += 1
                items[seq] = {"tokens": len(content) / 4, "agent": agent}
                pending.append(seq)
                if agent == "main" and not content.startswith(SYSTEM_PROMPT_PREFIX) and cat.get("inbound_origin") is None:
                    prompts.append({"evn": evn, "calls_before": len(calls), "correction": bool(CORRECTION_RE.search(content)),
                                    "len": len(content)})
    return list(calls.values()), items, uses, results, texts, prompts, handbacks


# ---------------------------------------------------------------------------------------
# Pass 2: price every call at the finest grain, so each piece can be charged once
# ---------------------------------------------------------------------------------------
class Ledger:
    def __init__(self, H, calls, items):
        W = H.W
        self.comps = {}                        # key -> units
        self.by_item = collections.defaultdict(list)
        self.by_call = collections.defaultdict(list)
        self.charged = set()
        last_read = collections.defaultdict(int)
        base_ctx = {}
        live = collections.defaultdict(list)
        epoch = collections.defaultdict(int)
        self.total = 0.0

        def add(key, units, call_idx, item=None):
            if units <= 0:
                return
            self.comps[key] = self.comps.get(key, 0.0) + units
            self.by_call[call_idx].append(key)
            if item is not None:
                self.by_item[item].append(key)
            self.total += units

        for c in calls:
            a = c["agent"]
            if c["read"] < 0.5 * last_read[a]:      # context compacted, or a new agent started
                live[a] = []
                base_ctx.pop(a, None)
                epoch[a] += 1
            last_read[a] = c["read"]
            c["epoch"] = epoch[a]
            trig = c["triggers"]
            live[a].extend(trig)
            fresh_in = W["input"] * c["input"] + W["write5m"] * c["write5m"] + W["write1h"] * c["write1h"]
            out_u = W["output"] * c["output"]
            ctx = c["read"] + c["write5m"] + c["write1h"] + c["input"]
            base_ctx.setdefault(a, ctx)
            base = min(base_ctx[a], c["read"])
            c["ctx_tokens"] = ctx
            i = c["idx"]
            # fresh input -> the items that triggered the call, by size
            tok = sum(items[t]["tokens"] for t in trig)
            if trig:
                for t in trig:
                    share = (items[t]["tokens"] / tok) if tok else 1.0 / len(trig)
                    add(("fresh", i, t), fresh_in * share, i, t)
            else:
                add(("fresh", i, None), fresh_in, i)
            # output -> the items the call emitted, by size
            em = c["emitted"]
            etok = sum(items[t]["tokens"] for t in em)
            if em:
                for t in em:
                    share = (items[t]["tokens"] / etok) if etok else 1.0 / len(em)
                    add(("out", i, t), out_u * share, i, t)
            else:
                add(("out", i, None), out_u, i)
            # fixed setup re-read: belongs to the call as a whole
            add(("fixed", i), W["read"] * base, i)
            # history re-read -> every live item, by size
            hist_u = W["read"] * (c["read"] - base)
            live_tok = sum(items[t]["tokens"] for t in live[a])
            if live_tok:
                for t in live[a]:
                    add(("carry", i, t), hist_u * items[t]["tokens"] / live_tok, i, t)
            else:
                add(("carry", i, None), hist_u, i)

    def charge(self, keys):
        got = 0.0
        for k in keys:
            if k not in self.charged:
                self.charged.add(k)
                got += self.comps[k]
        return got

    def charge_item(self, item):
        return self.charge(self.by_item.get(item, ()))

    def charge_call(self, call_idx):
        return self.charge(self.by_call.get(call_idx, ()))

    def uncharged_calls(self, call_idxs):
        return sum(self.comps[k] for c in call_idxs for k in self.by_call.get(c, ()) if k not in self.charged)

    def charge_amount(self, units, call_idxs):
        """Take up to `units` from the still-uncharged pieces of these calls (a piece may be split),
        so an estimated charge never re-charges cost already given to another event."""
        got = 0.0
        for c in call_idxs:
            for k in self.by_call.get(c, ()):
                if got >= units:
                    return got
                if k in self.charged:
                    continue
                take = min(self.comps[k], units - got)
                got += take
                if take >= self.comps[k]:
                    self.charged.add(k)
                else:
                    self.comps[k] -= take      # the rest stays chargeable
        return got


# ---------------------------------------------------------------------------------------
# Pass 3: find waste events and charge them, in priority order
# ---------------------------------------------------------------------------------------
class Events:
    def __init__(self):
        self.rows = collections.defaultdict(lambda: {"events": 0, "units": 0.0, "ctx": [], "subs": collections.Counter()})

    def add(self, cat, units, ctx, sub=None, n=1):
        r = self.rows[cat]
        r["events"] += n
        r["units"] += units
        if ctx is not None:
            r["ctx"].append(ctx)
        if sub:
            r["subs"][sub] += n


def find_wastes(calls, items, uses, results, texts, prompts, handbacks, ledger, events_list, meta):
    ev = Events()
    res_by_use = {r["use_id"]: r for r in results}
    use_list = sorted(uses.values(), key=lambda u: u["evn"])
    ctx_of = lambda u: calls[u["call"]]["ctx_tokens"]

    def charge_use(u, with_result=True):
        units = ledger.charge_item(u["item"])
        r = res_by_use.get(u["id"])
        if with_result and r:
            units += ledger.charge_item(r["item"])
        return units

    # 1. rejected calls ---------------------------------------------------------------
    for u in use_list:
        r = res_by_use.get(u["id"])
        if r and PERM_RE.search(r["head"]):
            ev.add("rejected_call", charge_use(u), ctx_of(u),
                   "blocked" if r["head"].startswith("<tool_use_error>Blocked") else "denied")

    # 2. failed calls with a large payload that were redone ------------------------------
    by_agent = collections.defaultdict(list)
    for u in use_list:
        by_agent[u["agent"]].append(u)
    for lst in by_agent.values():
        for pos, u in enumerate(lst):
            if u["name"] not in ("Write", "Edit", "Bash") or u["payload"] < PAYLOAD_MIN:
                continue
            r = res_by_use.get(u["id"])
            if not r or PERM_RE.search(r["head"]):
                continue
            if not (r["is_error"] or r["head"].startswith(("Exit code", "<tool_use_error>"))):
                continue
            for x in lst[pos + 1: pos + 1 + RETRY_WINDOW]:
                if x["name"] != u["name"]:
                    continue
                if u["name"] == "Bash":
                    a, b = u["cmd"][:1500], x["cmd"][:1500]
                    same = bool(a and b and difflib.SequenceMatcher(None, a, b).ratio() >= 0.8)
                else:
                    same = bool(u["path"]) and x["path"] == u["path"]
                if same:
                    ev.add("failed_retry", charge_use(u), ctx_of(u), "write" if u["name"] != "Bash" else "script")
                    break

    # 3. files written and then overwritten, deleted, or never used ----------------------
    file_events = collections.defaultdict(list)    # basename -> [(evn, kind, use or None)]
    for u in use_list:
        wrote = []
        if u["name"] == "Write" and u["path"]:
            wrote = [base_of(u["path"])]
        elif u["name"] == "Bash":
            wrote = [base_of(m) for m in HEREDOC_RE.findall(u["cmd"])]
        for b in wrote:
            if len(b) >= MIN_BASENAME:
                file_events[b].append((u["evn"], "W", u))
        if u["name"] == "Edit" and u["path"]:
            b = base_of(u["path"])
            if len(b) >= MIN_BASENAME:
                file_events[b].append((u["evn"], "E", u))
    names = sorted(file_events)
    if names:
        blanket_evns = [u["evn"] for u in use_list if u["name"] == "Bash" and GIT_BLANKET_RE.search(u["cmd"])]
        for b in names:
            wr_evns = {e[0] for e in file_events[b]}
            for u in use_list:
                if b not in u["search"] or u["evn"] in wr_evns:
                    # a call that writes the file is a write event; but if it also runs it, that is a use
                    if u["evn"] in wr_evns and u["name"] == "Bash" and u["cmd"].count(b) > len(HEREDOC_RE.findall(u["cmd"])):
                        file_events[b].append((u["evn"] + 0.5, "U", None))
                    continue
                kind = "U"
                if u["name"] == "Bash":
                    m = RM_RE.search(u["cmd"])
                    if m and b in m.group(1) and u["cmd"].count(b) == 1:
                        kind = "R"
                    elif GIT_DISCARD_RE.search(u["cmd"]):
                        kind = "R"
                file_events[b].append((u["evn"], kind, u))
            for tevn, tx in texts:
                if b in tx:
                    file_events[b].append((tevn, "U", None))
            for be in blanket_evns:
                file_events[b].append((be + 0.25, "B", None))     # blanket add: counts as a use of everything written earlier
        item_state = {}          # item -> (set of verdicts per file)
        for b in names:
            seq_ = sorted(file_events[b], key=lambda e: (e[0], e[1]))
            for k, (en, kd, u) in enumerate(seq_):
                if kd not in ("W", "E"):
                    continue
                verdict = "unused"
                for en2, kd2, u2 in seq_[k + 1:]:
                    if en2 == en:
                        continue
                    if kd2 in ("U", "E", "B"):
                        verdict = "used"
                        break
                    if kd2 == "W":
                        verdict = "overwritten"
                        break
                    if kd2 == "R":
                        verdict = "removed"
                        break
                item_state.setdefault(u["id"], (u, []))[1].append(verdict)
        for uid, (u, verdicts) in sorted(item_state.items(), key=lambda kv: kv[1][0]["evn"]):
            for v in set(verdicts):
                meta["files_" + v] += 1
            if u["payload"] < PAYLOAD_MIN or any(v == "used" for v in verdicts):
                continue
            if all(v in ("overwritten", "removed") for v in verdicts):
                cat, sub = "superseded_write", verdicts[0]
            elif all(v == "unused" for v in verdicts):
                cat, sub = "unused_write", "never_referenced"
            else:
                continue
            ev.add(cat, charge_use(u, with_result=False), ctx_of(u), sub)

    # 4. background tasks the model started and later killed ---------------------------
    started = {}
    for r in results:
        m = BG_RE.search(r["text"])
        if m and m.group(1) not in started:
            started[m.group(1)] = r
    for u in use_list:
        if u["name"] == "TaskStop" and u["task_id"] in started:
            r0 = started[u["task_id"]]
            u0 = uses.get(r0["use_id"])
            units = charge_use(u)
            if u0:
                units += charge_use(u0)
            ev.add("task_stopped", units, ctx_of(u))

    # 5. agents: aborted, superseded, rejected by a reviewer --------------------------------
    agent_uses = [u for u in use_list if u["name"] == "Agent"]
    last_ts = max((c["ts"] for c in calls), default=0.0)
    children = collections.defaultdict(list)
    for c in calls:
        children[c["agent"]].append(c["idx"])
    launched_by = {}
    for u in agent_uses:
        launched_by[u["id"]] = u["agent"]

    def agent_calls(aid):
        out, stack = [], [aid]
        while stack:
            x = stack.pop()
            out.extend(children.get(x, []))
            stack.extend(a for a, p in launched_by.items() if p == x)
        return out

    def agent_units(aid):
        return ledger.uncharged_calls(agent_calls(aid))

    def charge_agent(aid):
        total = 0.0
        for ci in agent_calls(aid):
            total += ledger.charge_call(ci)
        return total

    handed_back = {x["handback_of"] for x in use_list if x.get("handback_of")}
    for u in agent_uses:
        r = res_by_use.get(u["id"])
        aid = u["id"]
        failed = bool(r and r["is_error"])
        unreturned = False
        if not failed and aid not in handbacks and aid not in handed_back:
            cs = agent_calls(aid)
            last = max([calls[i]["ts"] for i in cs] + [calls[u["call"]]["ts"]])
            foreground = bool(r) and not r["head"].startswith("Async agent launched")
            unreturned = (not foreground) and (last_ts - last) > STOP_AFTER_S
        if failed or unreturned:
            ev.add("aborted_agent", charge_agent(aid) + charge_use(u), None, "failed_launch" if failed else "no_hand_back")
    seen_desc = {}
    for u in agent_uses:
        d = (u["desc"] or "").strip().lower()
        if len(d) < 8:
            continue
        prev = seen_desc.get(d)
        if prev is not None and difflib.SequenceMatcher(None, prev["prompt"], u["prompt"]).ratio() >= 0.9:
            ev.add("superseded_agent", charge_agent(prev["id"]) + charge_use(prev), None, "relaunched")
        seen_desc[d] = u
    # producer work that ended blocked, or that a reviewer rejected -> share of the producer's cost
    def toks(d):
        return {t for t in re.findall(r"[a-z0-9]+", (d or "").lower())} - STOP_TOKENS
    use_by_id = {u["id"]: u for u in agent_uses}
    producers = [u for u in agent_uses if "produc" in (u["desc"] or "").lower()]
    reviewer_rates = []        # units per reviewed item, for reviewers seen from launch to hand-back
    for aid, hb in sorted(handbacks.items()):
        u = use_by_id.get(aid)
        if hb.get("is_review") and u and hb.get("reviewed"):
            reviewer_rates.append(agent_units(aid) / hb["reviewed"])
    proxy = statistics.median(reviewer_rates) if reviewer_rates else None
    producer_share = {}        # producer id -> [blocked share, rejected share]
    proxy_due = []             # rejected counts with no matched producer, priced by the reviewer proxy
    for aid, hb in sorted(handbacks.items()):
        u = use_by_id.get(aid)
        if u and "blocked" in hb and "produc" in (u["desc"] or "").lower():
            producer_share.setdefault(aid, [0.0, 0.0])[0] = min(hb["blocked"] / hb["rows"], 1.0)
        if "rejected" not in hb or not hb["is_review"]:
            continue
        meta["reviewed_items"] += hb["reviewed"]
        meta["rejected_items"] += hb["rejected"]
        meta["corrected_by_reviewers"] += hb["corrected"]
        if not hb["rejected"]:
            continue
        match = None
        if u:
            rt = toks(u["desc"])
            best_n, tie = 0, False
            for p in producers:
                if p["evn"] >= u["evn"]:
                    continue
                n = len(rt & toks(p["desc"]))
                if n > best_n:
                    match, best_n, tie = p, n, False
                elif n == best_n and n:
                    tie = True
            if best_n < 2 or tie:
                match = None
        if match is not None:
            producer_share.setdefault(match["id"], [0.0, 0.0])[1] += min(hb["rejected"] / hb["reviewed"], 1.0)
            meta["rejected_priced"] += hb["rejected"]
        elif proxy:
            proxy_due.append(hb["rejected"])     # priced after producer shares are charged
        else:
            meta["rejected_unpriced"] += hb["rejected"]
    for pid, (fb, fr) in sorted(producer_share.items()):
        base_units = agent_units(pid)
        charge_agent(pid)
        scale = min(1.0, 1.0 / (fb + fr)) if fb + fr > 0 else 0.0
        if fb:
            ev.add("blocked_output", base_units * fb * scale, None, "producer_rows_blocked")
        if fr:
            ev.add("rejected_review", base_units * fr * scale, None, "producer_work_rejected")
    # proxy-priced rejections are taken from still-uncharged producer (then other subagent) calls, so
    # they can never double count cost already charged above or exceed what the session spent
    pool = [ci for p in producers for ci in agent_calls(p["id"])]
    in_pool = set(pool)
    pool += [c["idx"] for c in calls if c["agent"] != "main" and c["idx"] not in in_pool]
    for n_rej in proxy_due:
        units = ledger.charge_amount(n_rej * proxy, pool)
        ev.add("rejected_review", units, None, "proxy_from_reviewer_cost", n=n_rej)
        meta["rejected_proxy_priced"] += n_rej

    # 6. the model's recent work before a user correction -------------------------------------
    main_calls = [c for c in calls if c["agent"] == "main"]
    for p in prompts:
        if not p["correction"]:
            continue
        before = [c for c in main_calls if c["idx"] < p["calls_before"]][-TURN_CALL_CAP:]
        # stay inside the turn that the correction follows
        prev_turn = max((q["calls_before"] for q in prompts if q["calls_before"] < p["calls_before"]), default=0)
        before = [c for c in before if c["idx"] >= prev_turn]
        if not before:
            continue
        units = sum(ledger.charge_call(c["idx"]) for c in before)
        ev.add("user_correction", units, int(statistics.median(c["ctx_tokens"] for c in before)), "corrected_turn")
    return ev


# ---------------------------------------------------------------------------------------
def summarize_session(H, sid, label, n_events, events):
    calls, items, uses, results, texts, prompts, handbacks = rebuild(H, events)
    if not calls:
        return None
    ledger = Ledger(H, calls, items)
    meta = collections.Counter()
    ev = find_wastes(calls, items, uses, results, texts, prompts, handbacks, ledger, events, meta)
    charged_units = sum(r["units"] for r in ev.rows.values())
    return {"session_id": sid, "label": label, "events": n_events, "model_calls": len(calls),
            "_total_units": ledger.total, "replay_units": round(ledger.total), "_ev": ev, "_charged": charged_units,
            "_ctx_all": [c["ctx_tokens"] for c in calls], "signals": dict(meta),
            "tokens": {k: sum(c[k] for c in calls) for k in ("input", "read", "write5m", "write1h", "output")}}


def build(args):
    H = load_hamilton()
    data = Path(args.data).resolve()
    idx = {}
    if (data / "session_index.json").exists():
        for s in json.loads((data / "session_index.json").read_text()).get("sessions", []):
            idx[s["id"]] = s
    labels, manifest_complete = {}, {}
    if (data / "MANIFEST.json").exists():
        for s in json.loads((data / "MANIFEST.json").read_text()).get("sessions", []):
            labels[s["session_id"]] = s.get("label", "")
            manifest_complete[s["session_id"]] = bool(s.get("complete", True))
    sessions, n_events = [], 0
    for sd in sorted(p for p in (data / "events").iterdir() if p.is_dir()):
        events = H.load(sd)
        if not events:
            continue
        n_events += len(events)
        s = summarize_session(H, sd.name, labels.get(sd.name, ""), len(events), events)
        if not s:
            continue
        row = idx.get(sd.name) or {}
        read_idx = row.get("cache_read_tokens")
        s["coverage_cache_read"] = round(s["tokens"]["read"] / read_idx, 4) if read_idx else None
        s["complete"] = bool(manifest_complete.get(sd.name, True)
                             and (s["coverage_cache_read"] is None or s["coverage_cache_read"] >= COMPLETE_COVERAGE))
        s["session_cost_usd"] = row.get("cost_usd")
        sessions.append(s)
    if not sessions:
        return None
    rates = [s["session_cost_usd"] / s["replay_units"] for s in sessions
             if s["complete"] and s["session_cost_usd"] and s["replay_units"]]
    median_rate = statistics.median(rates) if rates else None
    for s in sessions:
        if s["complete"] and s["session_cost_usd"]:
            s["usd_per_unit"], s["usd_basis"] = s["session_cost_usd"] / s["replay_units"], "get_session.cost_usd"
        else:
            s["usd_per_unit"], s["usd_basis"] = median_rate, "profile_scaled"
        s["replay_usd"] = round(s["replay_units"] * s["usd_per_unit"], 2) if s["usd_per_unit"] else None
    return sessions, n_events, median_rate


PROFILE_NAMES = {"X1": "PROFILE_x1.json", "treemap parent": "PROFILE_treemap.json", "PRs 33 and 31": "PROFILE_prmerge.json",
                 "ProQuest": "PROFILE_proquest.json", "blocked-copy session": "PROFILE_upload_partial.json"}


def make_output(sessions, args, run_date):
    n_sessions = len(sessions)
    profile_map = {}
    if args.profiles:
        pdir = Path(args.profiles).resolve()
        for s in sessions:
            f = PROFILE_NAMES.get(s["label"])
            if f and (pdir / f).exists():
                try:
                    profile_map[s["session_id"]] = str((pdir / f).relative_to(REPO))
                except ValueError:
                    pass
    session_docs, sanity = [], []
    by_cat = {k: [] for k in ORDER}
    for s in sessions:
        rate = s["usd_per_unit"]
        usd = (lambda x, r=rate: round(x * r, 2)) if rate else (lambda x: None)
        cat_docs, tot_units = {}, 0.0
        for k in ORDER:
            r = s["_ev"].rows.get(k)
            if not r:
                cat_docs[k] = {"events": 0, "usd": 0.0, "units": 0, "share_of_replay": 0.0}
                continue
            tot_units += r["units"]
            share = round(r["units"] / s["_total_units"], 4) if s["_total_units"] else 0.0
            doc = {"events": r["events"], "usd": usd(r["units"]), "units": round(r["units"]), "share_of_replay": share}
            if r["subs"]:
                doc["kinds"] = dict(sorted(r["subs"].items()))
            cat_docs[k] = doc
            e = {"session_id": s["session_id"]}
            if s["session_id"] in profile_map:
                e["profile"] = profile_map[s["session_id"]]
            e.update({"cause_key": CATS[k][0], "usd": usd(r["units"]), "share": share, "events": r["events"],
                      "model_calls": s["model_calls"],
                      "median_context_tokens": int(statistics.median(r["ctx"] or s["_ctx_all"]))})
            by_cat[k].append((e, r["units"]))
        w_usd = usd(tot_units)
        cost = s["session_cost_usd"]
        bounds = [x for x in (cost, s["replay_usd"]) if x is not None]
        ok = bool(bounds) and w_usd is not None and w_usd <= min(bounds) + 1e-9 and tot_units <= s["_total_units"] + 1e-6
        share = round(tot_units / s["_total_units"], 4) if s["_total_units"] else 0.0
        sanity.append({"session_id": s["session_id"], "wasted_usd": w_usd, "replay_usd": s["replay_usd"],
                       "session_cost_usd": cost, "wasted_share_of_replay": share, "within_session_total": ok})
        session_docs.append({
            "session_id": s["session_id"], "label": s["label"], "complete": s["complete"],
            "coverage_cache_read": s["coverage_cache_read"], "events": s["events"], "model_calls": s["model_calls"],
            "usd_basis": s["usd_basis"], "session_cost_usd": cost, "replay_usd": s["replay_usd"],
            "wasted_usd": w_usd, "wasted_share_of_replay": share, "signals": s["signals"],
            "by_category": cat_docs})
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    all_gb = all(s["usd_basis"] == "get_session.cost_usd" for s in sessions)
    cands = []
    for k in ORDER:
        ev = by_cat[k]
        usd_total = sum(e["usd"] or 0.0 for e, _ in ev)
        if not ev or usd_total < MIN_USD:
            continue
        cause, saver, title, test = CATS[k]
        units_total = sum(u for _, u in ev)
        cands.append({
            "schema": "junto.candidate/1", "candidate_id": "", "rev": 0, "finder_id": FINDER_ID,
            "run_id": args.run_id, "saver_key": saver, "title": title, "targets": [cause],
            "evidence": [e for e, _ in sorted(ev, key=lambda x: -(x[0]["usd"] or 0))],
            "estimate": {"usd_per_session": round(usd_total / n_sessions, 2),
                         "tokens_per_session": round(units_total / n_sessions),
                         "usd_attributed_total": round(usd_total, 2),
                         "events_total": sum(e["events"] for e, _ in ev),
                         "basis": f"upper bound: wasted-work cost attributed in {n_sessions} audited sessions, divided by {n_sessions}; "
                                  "assumes the saver prevents all of it; tokens are input-price cost units; "
                                  + ("heuristic signal (cue words), low confidence" if k == "user_correction" else
                                     "heuristic signal (hand-back counts), low confidence" if k in ("rejected_review", "blocked_output") else
                                     "weak signal (not referenced again), low confidence" if k == "unused_write" else
                                     "pattern signal, medium confidence")},
            "proposed_test": test, "status": "unverified", "status_ref": None,
            "usd_basis": "get_session.cost_usd" if all_gb else "profile_scaled",
            "written_at": now, "written_by": "claude"})
    cands.sort(key=lambda c: (-c["estimate"]["usd_attributed_total"], c["saver_key"], c["targets"][0]))
    for n, c in enumerate(cands, 1):
        c["candidate_id"] = f"C-{run_date}-{n}"
    return cands, session_docs, sanity, now


# ---------------------------------------------------------------------------------------
# Redaction check (Junto design, section 5)
# ---------------------------------------------------------------------------------------
BAD = re.compile(r"(ghp_|github_pat_|sk-|xox|AKIA|Bearer |-----BEGIN|token=|key=|sig=|@[A-Za-z0-9-]+\.[A-Za-z]|https?://\S*\?|/home/|/tmp/|/root/|scratchpad)")


def redaction_failures(obj, path="", out=None):
    out = [] if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            redaction_failures(str(k), path + "/key", out)
            redaction_failures(v, path + "/" + str(k), out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            redaction_failures(v, path + f"/{i}", out)
    elif isinstance(obj, str) and (BAD.search(obj) or len(obj) > 300):
        out.append(path)
    return out


def main():
    t0 = time.time()
    ap = argparse.ArgumentParser(description="Gallatin wasted-work miner (Junto finder)")
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--profiles")
    args = ap.parse_args()
    data = Path(args.data).resolve()
    try:
        data.relative_to(REPO)
        print("refused: --data is inside the repository", file=sys.stderr)
        return 3
    except ValueError:
        pass
    if not (data / "events").is_dir():
        print("bad input: no events/ directory under --data", file=sys.stderr)
        return 2
    built = build(args)
    if built is None:
        print("bad input: no usable transcript events", file=sys.stderr)
        return 2
    sessions, n_events, median_rate = built
    m = re.match(r"R-(\d{8})-\d+$", args.run_id)
    run_date = m.group(1) if m else datetime.date.today().strftime("%Y%m%d")
    cands, session_docs, sanity, now = make_output(sessions, args, run_date)
    doc = {"schema": "junto.finder_output/1", "finder_id": FINDER_ID, "finder_version": VERSION, "run_id": args.run_id,
           "written_at": now, "written_by": "claude",
           "note": "Everything here is unverified. Estimates rank work and are never counted as savings.",
           "median_usd_per_unit_complete_sessions": median_rate,
           "sanity": {"all_within_session_total": all(x["within_session_total"] for x in sanity), "sessions": sanity},
           "sessions": session_docs, "candidates": cands}
    bad = redaction_failures(doc)
    if bad:
        print("privacy refusal: redaction check failed at " + ", ".join(bad[:5]), file=sys.stderr)
        return 3
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix == ".json":
        out.write_text(json.dumps(doc, indent=1) + "\n")
    else:
        out.write_text("".join(json.dumps(c, sort_keys=True) + "\n" for c in cands))
    digest_src = sorted((p.name, p.stat().st_size) for p in (data / "events").rglob("*") if p.is_file())
    run = {"schema": "junto.run/1", "run_id": args.run_id, "finder_id": FINDER_ID, "finder_version": VERSION,
           "wall_seconds": round(time.time() - t0, 2),
           "data_digest": hashlib.sha256(json.dumps(digest_src).encode()).hexdigest(),
           "inputs": {"profiles": 0, "sessions": len(sessions), "events": n_events},
           "candidates_emitted": [c["candidate_id"] for c in cands], "usd_spent": None, "usd_basis": "local_script"}
    Path(str(out) + ".run.json").write_text(json.dumps(run, indent=1) + "\n")
    ok = doc["sanity"]["all_within_session_total"]
    lines = [f"wasted_work: {len(sessions)} sessions, {n_events} events, {len(cands)} candidates (all unverified); sanity {'ok' if ok else 'FAILED'}"]
    for c in cands[:8]:
        e = c["estimate"]
        lines.append(f"  {c['targets'][0]} -> {c['saver_key']}: est ${e['usd_per_session']}/session, ${e['usd_attributed_total']} total, {e['events_total']} events")
    print("\n".join(lines[:20]))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())

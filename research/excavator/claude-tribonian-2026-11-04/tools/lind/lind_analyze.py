"""Lind trial analysis: paired A/B blind review, current reviewer prompt (A) vs the same prompt with
maintained mechanical receipts supplied first (B). Coordinator tool; reads private transcripts, writes only
sanitized counts (no message text).

usage: python3 -I lind_analyze.py ARMS.json OUT.json
  ARMS.json: [{"batch": "c01", "arm": "A", "agent_id": "...", "review_file": "<packet>/reviews/BLIND_REVIEW.jsonl",
               "after_reveal_file": "...", "key_file": "<scratch>/moon-keys/c01.json"}, ...]

Per arm and batch it reports: token categories (fresh input, cache read, cache write 5m/1h, output; message ids
counted once, last snapshot wins), assistant calls, tool uses by name, Bash calls, Bash/Write commands that build
hashing or quote-offset scripts (sha256/hashlib/char_start), Read calls on held text files, receipt-file reads,
wall time (first to last record), active time (sum of record gaps of at most 300 s, so a usage-limit pause is excluded), verdict counts, planted-control catch, and paired verdict agreement.
Token figures come from the transcript usage records the harness reports; they are observed counts, not an
invoice. Hamilton's supported bridge remains the authority for the run-wide profile.
"""
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

TX = Path("/root/.claude/projects/-home-claude/113ce3b2-4ba3-50df-9241-eb6576e0f367/subagents")
HASH_RE = re.compile(r"hashlib|sha256sum|sha256\(|char_start|char_end")


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def transcript(agent_id):
    usage, tools, bash, hash_scripts, text_reads, receipt_reads = {}, Counter(), 0, 0, 0, 0
    first = last = None
    prev = None
    active = 0.0
    for line in (TX / f"agent-{agent_id}.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        if r.get("timestamp"):
            t = ts(r["timestamp"])
            first = first or t
            if prev is not None and 0 <= (t - prev).total_seconds() <= 300:
                active += (t - prev).total_seconds()
            prev = t
            last = t
        if r.get("type") != "assistant":
            continue
        m = r["message"]
        if m.get("id") and m.get("usage"):
            usage[m["id"]] = m["usage"]
        for c in m.get("content", []):
            if c.get("type") != "tool_use":
                continue
            name = c.get("name", "")
            tools[name] += 1
            inp = json.dumps(c.get("input", {}))
            if name == "Bash":
                bash += 1
            if name in ("Bash", "Write") and HASH_RE.search(inp):
                hash_scripts += 1
            if name == "Read" and "/output/texts/" in inp:
                text_reads += 1
            if "MECHANICAL.json" in inp:
                receipt_reads += 1
    tok = Counter()
    for u in usage.values():
        tok["fresh_input"] += u.get("input_tokens") or 0
        tok["cache_read"] += u.get("cache_read_input_tokens") or 0
        cc = u.get("cache_creation") or {}
        tok["cache_write_5m"] += cc.get("ephemeral_5m_input_tokens") or 0
        tok["cache_write_1h"] += cc.get("ephemeral_1h_input_tokens") or 0
        tok["output"] += u.get("output_tokens") or 0
    return {"assistant_calls": len(usage), "tokens": dict(tok), "tool_uses": dict(tools), "bash_calls": bash,
            "hash_or_offset_script_calls": hash_scripts, "held_text_reads": text_reads,
            "receipt_reads": receipt_reads,
            "wall_seconds": (last - first).total_seconds() if first and last else None,
            "active_seconds_gaps_le_300s": round(active, 1),
            "started_utc": first.isoformat() if first else None, "ended_utc": last.isoformat() if last else None}


def verdicts(path):
    out = {}
    p = Path(path) if path else None
    if not p or not p.exists():
        return None
    for line in p.open(encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            out[r.get("instrument_id")] = r.get("verdict")
    return out


def main():
    arms = json.loads(Path(sys.argv[1]).read_text())
    rows = []
    for a in arms:
        row = dict(a)
        row["transcript"] = transcript(a["agent_id"])
        v = verdicts(a.get("review_file"))
        row["verdicts"] = Counter(v.values()) if v else None
        key = json.loads(Path(a["key_file"]).read_text()) if a.get("key_file") else {}
        planted = [c["instrument_id"] for c in key.get("controls", [])]
        row["controls"] = {i: (v or {}).get(i) for i in planted}
        row["_v"] = v
        rows.append(row)
    pairs = {}
    for r in rows:
        pairs.setdefault(r["batch"], {})[r["arm"]] = r
    agreement = {}
    for b, d in pairs.items():
        if "A" in d and "B" in d and d["A"]["_v"] and d["B"]["_v"]:
            ids = set(d["A"]["_v"]) | set(d["B"]["_v"])
            dis = sorted(i for i in ids if d["A"]["_v"].get(i) != d["B"]["_v"].get(i))
            agreement[b] = {"claims": len(ids), "disagreements": dis}
    for r in rows:
        r.pop("_v")
    Path(sys.argv[2]).write_text(json.dumps({"schema": "lind-trial-analysis/v1", "arms": rows,
                                             "paired_agreement": agreement}, indent=2, default=dict) + "\n")


if __name__ == "__main__":
    main()

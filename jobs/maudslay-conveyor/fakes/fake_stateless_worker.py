"""A canned stateless worker for the stateless-mode tests: stands in for
`claude -p --tools "" --system-prompt-file PREFIX --json-schema SCHEMA --output-format stream-json --verbose ...`.
It reads the user message (the suffix) on stdin and the system prompt from the --system-prompt-file argument, and
prints claude-style stream-json events with a structured_output answer. No model, no network.

Cache: when MAUDSLAY_FAKE_CACHE names a folder, the worker keeps one marker file per prefix hash there. The first
process to see a prefix reports cache_creation_input_tokens for it; later processes with the same prefix report
cache_read_input_tokens (the way the real cache behaves inside its time to live).

Env MAUDSLAY_FAKE_LOG: write LOG.<random> with {"argv", "cwd", "kind", "id", "prefix_sha256", "prefix_chars",
"suffix_chars", "round"} per call. Env MAUDSLAY_FAKE_SCENARIO: JSON with optional
  "producer": {EO: "block"|"need_more"|"need_more_twice"|"junk"|"fail"}, "end_date": "2000-01-02",
  "need_more": {"path": ..., "start": 0, "end": 40},
  "reviewer": {"A"|"B": {"miss_controls": bool, "reject": [EO]}}."""
import hashlib
import json
import os
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fake_worker import canon, planted_claim  # noqa: E402


def emit(ev):
    print(json.dumps(ev), flush=True)


def arg(name):
    a = sys.argv[1:]
    return a[a.index(name) + 1] if name in a else None


def main():
    suffix = sys.stdin.read()
    prefix = Path(arg("--system-prompt-file")).read_text(encoding="utf-8")
    sc = json.loads(Path(os.environ["MAUDSLAY_FAKE_SCENARIO"]).read_text()) if os.environ.get("MAUDSLAY_FAKE_SCENARIO") else {}
    psha = hashlib.sha256(prefix.encode("utf-8")).hexdigest()
    end = sc.get("end_date", "2000-01-02")
    second_round = "NEED_MORE ROUND" in suffix
    rc, answer, ident, kind = 0, {}, "?", "producer"
    if "=== ROLE: PRODUCER" in prefix:
        iid = re.search(r"^ORDER: (\S+)", suffix, re.M).group(1)
        ident = iid
        s = iid.replace(":", "_")
        mode = (sc.get("producer") or {}).get(iid, "submit")
        scopes = json.loads(re.search(r"^PREPARED CLAUSE ROWS \(scope_id / clause_id\): (.+)$", suffix, re.M).group(1))
        if mode == "fail":
            rc = 1
        elif mode == "junk":
            answer = {"note": "no decision here"}
        elif mode in ("need_more", "need_more_twice") and (not second_round or mode == "need_more_twice"):
            answer = {"need_more": [sc.get("need_more") or {"path": "README.md", "start": 0, "end": 10}]}
        elif mode == "block":
            answer = {"decision": {"outcome": "blocked", "unresolved_material_gaps": ["synthetic: source not held"]},
                      "rationales": {}, "assessment": {"operative_force_at_cutoff": "unknown"}}
        else:
            answer = {"decision": {"outcome": "submit", "approved": True, "original_confirmed": True,
                                   "original_pages_confirmed": True, "inventory_confirmed": True,
                                   "research_rationale": f"@rationale:{s}.main", "savings_state": "none_after_bounded_search",
                                   "search_ids": ["current-law:usc"], "conflict_resolutions": {},
                                   "unresolved_material_gaps": []},
                      "clauses": [{"scope_id": c["scope_id"], "clause_id": c["clause_id"], "state": "terminated",
                                   "effective_date": end, "effective_date_confirmed": True,
                                   "later_event_ids": [], "later_events": []} for c in scopes],
                      "rationales": {f"{s}.main": f"Synthetic stateless rationale for {iid}."},
                      "assessment": {"operative_force_at_cutoff": "no", "claimed_status": "no"}}
    else:
        kind = "reviewer"
        m = re.search(r"CLAIM TO REVIEW \(JSON, sorted keys\):\n(.*)\n\nAnswer now through", suffix, re.S)
        claim = json.loads(m.group(1))
        arm = re.search(r"^REVIEW ARM: (\S+)", suffix, re.M).group(1)
        mode = re.search(r"^MODE: (\S+)", suffix, re.M).group(1)
        cfg = (sc.get("reviewer") or {}).get(arm, {})
        ident = f"{claim['instrument_id']}:{arm}"
        if cfg.get("fail"):
            rc = 1
        elif planted_claim(claim, end) and not cfg.get("miss_controls"):
            answer = {"verdict": "rejected", "defects": [{"field": "whole_order_end.date",
                                                          "problem": "contradicts the cited source"}],
                      "reasons": "synthetic"}
        elif claim["instrument_id"] in cfg.get("reject", []):
            answer = {"verdict": "rejected", "defects": [{"field": "research_rationale", "problem": "reason mismatch"}],
                      "reasons": "synthetic"}
        else:
            answer = {"verdict": "upheld_after_reveal" if mode == "after_reveal" else "upheld", "defects": [],
                      "reasons": "synthetic"}
    sid = str(uuid.uuid4())
    ptok = -(-len(prefix) // 4)
    stok = -(-len(suffix) // 4)
    cdir = os.environ.get("MAUDSLAY_FAKE_CACHE")
    cached = False
    if cdir:
        marker = Path(cdir) / psha
        Path(cdir).mkdir(parents=True, exist_ok=True)
        cached = marker.exists()
        marker.write_text("1")
    emit({"type": "system", "subtype": "init", "session_id": sid, "model": arg("--model")})
    use1 = {"input_tokens": 3, "cache_read_input_tokens": ptok if cached else 0,
            "cache_creation_input_tokens": stok + (0 if cached else ptok), "output_tokens": 200}
    emit({"type": "assistant", "message": {"id": "m1", "model": arg("--model"), "usage": use1,
                                           "content": [{"type": "tool_use", "name": "StructuredOutput", "input": answer}]}})
    use2 = {"input_tokens": 3, "cache_read_input_tokens": ptok + stok, "cache_creation_input_tokens": 50, "output_tokens": 20}
    emit({"type": "assistant", "message": {"id": "m2", "model": arg("--model"), "usage": use2,
                                           "content": [{"type": "text", "text": "done"}]}})
    tot = {k: use1[k] + use2[k] for k in use1}
    emit({"type": "result", "session_id": sid, "total_cost_usd": 0.01, "num_turns": 2, "is_error": bool(rc),
          "result": "done", "structured_output": answer if answer else None, "usage": tot})
    if os.environ.get("MAUDSLAY_FAKE_LOG"):
        with open(f"{os.environ['MAUDSLAY_FAKE_LOG']}.{uuid.uuid4().hex}", "w", encoding="utf-8") as f:
            f.write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(), "kind": kind, "id": ident,
                                "prefix_sha256": psha, "prefix_chars": len(prefix), "suffix_chars": len(suffix),
                                "round": 2 if second_round else 1, "pid": os.getpid()}) + "\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())

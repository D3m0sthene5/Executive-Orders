"""A canned worker for test_conveyor.py: reads the rendered prompt on stdin, writes a canned sheet or review file in
its working folder, and prints claude-style (`-p --output-format stream-json`) or codex-style (`exec --json`)
events, including tool calls the conveyor scans for blinding. No model, no network.

Env MAUDSLAY_FAKE_LOG: write LOG.<random> holding {"argv", "cwd", "files", "kind", "id", "repair", "pid"} per call
(after the last event).
Env MAUDSLAY_FAKE_SCENARIO: JSON with optional
  "producer": {EO: "block"|"bad_sheet"|"fail"|"badclaim"|"checkfail"}, "repair_fails": [EO],
  "reviewer": {"A"|"B": {"miss_controls": bool, "reject": [EO], "fail": bool, "touch": [string], "reasons": str}},
  "touch": {EO: [string]} (extra producer tool-call arguments), "usd": {"producer"|"reviewer": x}, "tokens": n,
  "sleep": {EO: s}, "sleep_once": {EO: s}, "turns": n, "turn_sleep": s, "end_date": "2000-01-02",
  "canned": {EO: {"decision": {...}, "clauses": {scope: {...}}, "rationale": str}},
  "status_decision": {EO: "blank"} (an undecided order's producer leaves STATUS_DECISION.json blank),
  "status_reviewer": {"reject": [EO], "fail": bool, "touch": [string], "rename": str}.
A status-reviewer prompt (STATUS REVIEWER NAME:) fills each STATUS_REVIEW_EO_N.json sheet it lists. A blind reviewer
treats a claim carrying "fake_seal" as planted when the seal no longer matches (any typed or dated plant); otherwise as
planted when its whole_order_end date differs from end_date."""
import csv
import hashlib
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path


def field(prompt, name):
    m = re.search(rf"^{name}: (.+)$", prompt, re.M)
    return m.group(1).strip() if m else None


def canon(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def rows(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        return rd.fieldnames, list(rd)


def write_csv(p, fields, rs):
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rs)


def sleep_for(sc, ident):
    s = (sc.get("sleep") or {}).get(ident, 0)
    once = (sc.get("sleep_once") or {}).get(ident)
    if once and os.environ.get("MAUDSLAY_FAKE_SCENARIO"):
        mark = Path(os.environ["MAUDSLAY_FAKE_SCENARIO"]).parent / f"slept-{ident.replace(':', '_')}"
        if not mark.exists():
            mark.write_text("1")
            s = once
    time.sleep(s)


def fill_status_decision(prompt, sc, iid, agent):
    """An undecided order: fill the blank STATUS_DECISION.json in the producer's own folder (a status NO resting on
    the evidence's ACT: records), as a real producer would."""
    ev_path, dec_path = field(prompt, "STATUS EVIDENCE"), field(prompt, "STATUS DECISION")
    if not ev_path or not dec_path or (sc.get("status_decision") or {}).get(iid) == "blank":
        return []
    ev = json.loads(Path(ev_path).read_text(encoding="utf-8"))
    dec = json.loads(Path(dec_path).read_text(encoding="utf-8"))
    h = ev["history_packet"]["history"]
    recs = ev["base_dossier"]["evidence"]
    dec.update(agent=agent, approved=True, identity_confirmed=True, basis_review_confirmed=True,
               earlier_endings_checked=True, partial_scope_checked=True, savings_checked=True,
               observations_reviewed=list(h.get("observation_ids", [])),
               conflict_resolutions={f: "Synthetic resolution: the held sources settle this flag explicitly."
                                     for f in h.get("flags", [])},
               recommended_provisional_status="no", material_gaps=[],
               basis_evidence_ids=sorted(k for k in recs if k.startswith(("ACT:", "ACTOR_TEXT:"))),
               rationale=f"Synthetic producer rationale: the held acting instrument ends the whole of {iid}.")
    Path(dec_path).write_text(json.dumps(dec, indent=1), encoding="utf-8")
    return [f"cat {ev_path}"]


def produce(prompt, sc):
    iid, work, agent = field(prompt, "ORDER"), Path(field(prompt, "SHEET FOLDER")), field(prompt, "AGENT")
    tools = [f"cat {field(prompt, 'VIEW')}"] + list((sc.get("touch") or {}).get(iid, []))
    mode = (sc.get("producer") or {}).get(iid, "submit")
    repair = "REPAIR ROUND" in prompt
    sleep_for(sc, iid)
    if mode == "fail":
        return iid, 1, tools
    s = iid.replace(":", "_")
    df, dr = rows(work / "decisions.csv")
    cf, cr = rows(work / "clauses.csv")
    r = dr[0]
    if mode == "block":
        r.update(outcome="blocked", agent=agent, unresolved_material_gaps=json.dumps(["synthetic: source not held"]))
    else:
        r.update(outcome="submit", approved="true", agent=agent, research_rationale=f"@rationale:{s}.main",
                 original_confirmed="true", inventory_confirmed="true")
        for c in cr:
            c.update(state="terminated", effective_date=sc.get("end_date", "2000-01-02"), effective_date_confirmed="true")
    canned = (sc.get("canned") or {}).get(iid)
    if canned:
        # Exact field values for a real claim-kit fixture (test_conveyor.RealKitFixtureTests).
        r.update(canned["decision"])
        for c in cr:
            c.update(canned["clauses"].get(c["scope_id"], {}))
    if mode == "bad_sheet":
        dr.append(dict(r, instrument_id="EO:999999"))
    write_csv(work / "decisions.csv", df, dr)
    write_csv(work / "clauses.csv", cf, cr)
    text = (canned or {}).get("rationale") or f"Synthetic rationale for {iid}."
    fixed = repair and iid not in sc.get("repair_fails", [])
    if mode == "badclaim" and not fixed:
        text += " BADCLAIM"
    if mode == "checkfail" and not fixed:
        text += " CHECKFAIL"
    (work / "RATIONALES.json").write_text(json.dumps({f"{s}.main": text}), encoding="utf-8")
    (work / "ASSESSMENT.json").write_text(json.dumps({"id": iid, "outcome": r["outcome"]}), encoding="utf-8")
    (work / "REPORT.md").write_text(f"synthetic {iid} {r['outcome']}\n", encoding="utf-8")
    if mode != "block":
        tools += fill_status_decision(prompt, sc, iid, agent)
    return iid, 0, tools


def status_review(prompt, sc):
    """Fill each listed status review sheet: accept, unless the scenario rejects the order."""
    name = field(prompt, "STATUS REVIEWER NAME")
    cfg = sc.get("status_reviewer") or {}
    tools = list(cfg.get("touch", []))
    if cfg.get("fail"):
        return name, 1, tools
    for line in re.findall(r"^MEMBER: (.+)$", prompt, re.M):
        parts = dict(x.split(": ", 1) for x in line.split(" | ")[1:])
        iid = line.split(" | ")[0].strip()
        ev = json.loads(Path(parts["EVIDENCE"]).read_text(encoding="utf-8"))
        dec = json.loads(Path(parts["DECISION"]).read_text(encoding="utf-8"))
        tools += [f"cat {parts['EVIDENCE']}", f"cat {parts['DECISION']}"]
        sheet = Path(parts["SHEET"])
        rv = json.loads(sheet.read_text(encoding="utf-8"))
        reject = iid in cfg.get("reject", [])
        rv.update(decision="reject" if reject else "accept", independence_confirmed=True, source_checks_confirmed=True,
                  checked_evidence_ids=[ev["base_dossier"]["original_source_id"]] + list(dec.get("basis_evidence_ids") or []),
                  rationale=("Synthetic status review: the basis sentence is qualified, so the whole-order end fails."
                             if reject else "Synthetic status review: identity, the basis sentence and its date confirmed."))
        if cfg.get("rename"):
            rv["reviewer"] = cfg["rename"]
        sheet.write_text(json.dumps(rv, indent=1), encoding="utf-8")
    return name, 0, tools


def planted_claim(c, end):
    if "fake_seal" in c:
        return canon({k: v for k, v in c.items() if k != "fake_seal"}) != c["fake_seal"]
    return c.get("whole_order_end", {}).get("date") != end


def review(prompt, sc):
    src, out, name, mode = (field(prompt, "CLAIMS TO REVIEW"), field(prompt, "WRITE REVIEWS TO"),
                            field(prompt, "REVIEWER NAME"), field(prompt, "MODE"))
    arm = name.rsplit("-", 1)[1]
    cfg = (sc.get("reviewer") or {}).get(arm, {})
    packet = field(prompt, "PACKET")
    tools = [f"cat {src}", f"python -X utf8 -c \"import batch; batch.load_packet('{packet}', '.')\"",
             f"python -c \"print(open('{packet}/PACKET.json').read()[:10])\""] + list(cfg.get("touch", []))
    sleep_for(sc, arm + mode)
    if cfg.get("fail"):
        return name, 1, tools
    end = sc.get("end_date", "2000-01-02")
    recs = []
    for line in Path(src).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        c = json.loads(line)
        planted = planted_claim(c, end)
        iid = c["instrument_id"]
        if planted and not cfg.get("miss_controls"):
            v, d = "rejected", [{"field": "whole_order_end.date", "problem": "contradicts the cited source"}]
            if "fake_seal" in c:
                # A fake that names every typed kind: real reviewers name one; kind-specific misses are tested on
                # caught() directly (test_nalimov ConveyorTypedControlTests).
                d.append({"field": "later_events", "problem": "an event is omitted, or the end is partial; the "
                          "original_operative_text identity is another order's; the ending_source provision differs"})
        elif iid in cfg.get("reject", []):
            v, d = "rejected", [{"field": "research_rationale", "problem": "reason does not match the source"}]
        else:
            v, d = ("upheld_after_reveal" if mode == "after_reveal" else "upheld"), []
        recs.append({"instrument_id": iid, "claim_sha256": canon(c), "verdict": v, "defects": d,
                     "reasons": cfg.get("reasons", "synthetic"), "scope": "whole_case"})
    Path(out).write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")
    return name, 0, tools


def emit(ev):
    print(json.dumps(ev), flush=True)


def main():
    prompt = sys.stdin.read()
    sc = json.loads(Path(os.environ["MAUDSLAY_FAKE_SCENARIO"]).read_text()) if os.environ.get("MAUDSLAY_FAKE_SCENARIO") else {}
    files = sorted(os.listdir("."))
    kind = ("producer" if "SHEET FOLDER:" in prompt else "status_reviewer" if "STATUS REVIEWER NAME:" in prompt
            else "reviewer")
    ident, rc, tools = {"producer": produce, "status_reviewer": status_review, "reviewer": review}[kind](prompt, sc)
    usd = (sc.get("usd") or {}).get(kind, 0.5)
    tok = int(sc.get("tokens", 1000))
    turns = int(sc.get("turns", 1))
    sid = str(uuid.uuid4())
    if "exec" in sys.argv[1:]:
        emit({"type": "thread.started", "thread_id": sid})
        for t in tools:
            emit({"type": "item.completed", "item": {"type": "command_execution", "command": t, "aggregated_output": ""}})
        # One turn of `turns` model calls. Like codex, the --json stream reports usage only at turn.completed; the
        # session's rollout file ($CODEX_HOME/sessions/YYYY/MM/DD/rollout-*-<thread>.jsonl) grows a cumulative
        # token_count line after every call.
        rollout = None
        if os.environ.get("CODEX_HOME"):
            d = Path(os.environ["CODEX_HOME"]) / "sessions" / time.strftime("%Y/%m/%d")
            d.mkdir(parents=True, exist_ok=True)
            rollout = d / f"rollout-{time.strftime('%Y-%m-%dT%H-%M-%S')}-{sid}.jsonl"
            with open(rollout, "a", encoding="utf-8") as f:
                f.write(json.dumps({"type": "session_meta", "payload": {"id": sid, "cwd": os.getcwd()}}) + "\n")
        for i in range(1, turns + 1):
            if rollout:
                with open(rollout, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "type": "event_msg",
                                        "payload": {"type": "token_count", "info": {
                                            "total_token_usage": {"input_tokens": 3 * tok * i,
                                                                  "cached_input_tokens": 2 * tok * i,
                                                                  "output_tokens": tok * i},
                                            "last_token_usage": {"input_tokens": 3 * tok}}}}) + "\n")
            time.sleep(float(sc.get("turn_sleep", 0)))
        emit({"type": "turn.completed", "usage": {"input_tokens": 3 * tok * turns, "cached_input_tokens": 2 * tok * turns,
                                                  "output_tokens": tok * turns}})
        if rc:
            emit({"type": "turn.failed"})
    else:
        emit({"type": "system", "subtype": "init", "session_id": sid, "cwd": os.getcwd()})
        for i, t in enumerate(tools):
            emit({"type": "assistant", "message": {"id": f"t{i}", "usage": {"input_tokens": 1, "output_tokens": 1},
                                                   "content": [{"type": "tool_use", "name": "Bash",
                                                                "input": {"command": t}}]}})
        for i in range(turns - 1):
            emit({"type": "assistant", "message": {"id": f"m{i}", "usage": {"input_tokens": tok, "output_tokens": tok},
                                                   "content": [{"type": "text", "text": "working"}]}})
            time.sleep(float(sc.get("turn_sleep", 0)))
        emit({"type": "result", "session_id": sid, "total_cost_usd": usd, "num_turns": 3, "is_error": bool(rc),
              "result": "synthetic", "duration_ms": 10,
              "usage": {"input_tokens": tok, "cache_read_input_tokens": tok, "cache_creation_input_tokens": tok,
                        "output_tokens": tok}})
    if os.environ.get("MAUDSLAY_FAKE_LOG"):
        # One file per call: concurrent appends from several processes can lose a line on Windows.
        with open(f"{os.environ['MAUDSLAY_FAKE_LOG']}.{uuid.uuid4().hex}", "w", encoding="utf-8") as f:
            f.write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(), "files": files, "kind": kind, "id": ident,
                                "repair": "REPAIR ROUND" in prompt, "pid": os.getpid(),
                                "prompt_chars": len(prompt)}) + "\n")
    return rc


if __name__ == "__main__":
    sys.exit(main())

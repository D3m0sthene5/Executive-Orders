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
  "canned": {EO: {"decision": {...}, "clauses": {scope: {...}}, "rationale": str}}."""
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
    return iid, 0, tools


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
        planted = c.get("whole_order_end", {}).get("date") != end
        iid = c["instrument_id"]
        if planted and not cfg.get("miss_controls"):
            v, d = "rejected", [{"field": "whole_order_end.date", "problem": "contradicts the cited source"}]
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
    kind = "producer" if "SHEET FOLDER:" in prompt else "reviewer"
    ident, rc, tools = produce(prompt, sc) if kind == "producer" else review(prompt, sc)
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

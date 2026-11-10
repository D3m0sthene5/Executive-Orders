"""A canned worker for test_conveyor.py: reads the rendered prompt on stdin, writes a canned sheet or review file,
and prints claude-style (`-p --output-format json`) or codex-style (`exec --json`) usage. No model, no network.

Env MAUDSLAY_FAKE_LOG: append {"argv", "prompt_chars", "kind", "id"} per call. Env MAUDSLAY_FAKE_SCENARIO: JSON with
optional "producer": {EO: "block"|"bad_sheet"|"fail"|"badclaim"|"checkfail"}, "repair_fails": [EO],
"reviewer": {"A"|"B": {"miss_controls": bool, "reject": [EO], "fail": bool}}, "usd": {"producer"|"reviewer": x},
"tokens": n, "sleep": {EO: seconds}, "codex_turns": n, "end_date": "2000-01-02"."""
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


def produce(prompt, sc):
    iid, work, agent = field(prompt, "ORDER"), Path(field(prompt, "SHEET FOLDER")), field(prompt, "AGENT")
    mode = (sc.get("producer") or {}).get(iid, "submit")
    repair = "REPAIR ROUND" in prompt
    time.sleep((sc.get("sleep") or {}).get(iid, 0))
    if mode == "fail":
        return iid, 1
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
    return iid, 0


def review(prompt, sc):
    src, out, name, mode = (field(prompt, "CLAIMS TO REVIEW"), field(prompt, "WRITE REVIEWS TO"),
                            field(prompt, "REVIEWER NAME"), field(prompt, "MODE"))
    arm = name.rsplit("-", 1)[1]
    cfg = (sc.get("reviewer") or {}).get(arm, {})
    if cfg.get("fail"):
        return name, 1
    end = sc.get("end_date", "2000-01-02")
    recs = []
    for line in Path(src).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        c = json.loads(line)
        planted = c.get("whole_order_end", {}).get("date") != end
        iid = c["instrument_id"]
        if planted and not cfg.get("miss_controls"):
            v, d = "rejected", [{"field": "whole_order_end.date", "problem": "date contradicts the cited source"}]
        elif iid in cfg.get("reject", []):
            v, d = "rejected", [{"field": "research_rationale", "problem": "reason does not match the source"}]
        else:
            v, d = ("upheld_after_reveal" if mode == "after_reveal" else "upheld"), []
        recs.append({"instrument_id": iid, "claim_sha256": canon(c), "verdict": v, "defects": d,
                     "reasons": "synthetic", "scope": "whole_case"})
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")
    return name, 0


def main():
    prompt = sys.stdin.read()
    sc = json.loads(Path(os.environ["MAUDSLAY_FAKE_SCENARIO"]).read_text()) if os.environ.get("MAUDSLAY_FAKE_SCENARIO") else {}
    kind = "producer" if "SHEET FOLDER:" in prompt else "reviewer"
    ident, rc = produce(prompt, sc) if kind == "producer" else review(prompt, sc)
    if os.environ.get("MAUDSLAY_FAKE_LOG"):
        with open(os.environ["MAUDSLAY_FAKE_LOG"], "a", encoding="utf-8") as f:
            f.write(json.dumps({"argv": sys.argv[1:], "prompt_chars": len(prompt), "kind": kind, "id": ident,
                                "repair": "REPAIR ROUND" in prompt}) + "\n")
    usd = (sc.get("usd") or {}).get(kind, 0.5)
    tok = int(sc.get("tokens", 1000))
    if "exec" in sys.argv[1:]:
        print(json.dumps({"type": "thread.started", "thread_id": str(uuid.uuid4())}), flush=True)
        for _ in range(int(sc.get("codex_turns", 1))):
            print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 3 * tok, "cached_input_tokens": 2 * tok,
                                                                  "output_tokens": tok}}), flush=True)
            time.sleep(float(sc.get("codex_turn_sleep", 0)))
        if rc:
            print(json.dumps({"type": "turn.failed"}), flush=True)
        return rc
    print(json.dumps({"type": "result", "session_id": str(uuid.uuid4()), "total_cost_usd": usd, "num_turns": 3,
                      "is_error": bool(rc), "result": "synthetic", "duration_ms": 10,
                      "usage": {"input_tokens": tok, "cache_read_input_tokens": tok,
                                "cache_creation_input_tokens": tok, "output_tokens": tok}}))
    return rc


if __name__ == "__main__":
    sys.exit(main())

"""Adjudicate the two blind reading arms and, with --apply, write the Jacquard L1 correction.

    python -I research/ulpian/jacquard-l1-correction/adjudicate.py            # DECISIONS.csv, ADJUDICATION.json
    python -I research/ulpian/jacquard-l1-correction/adjudicate.py --apply    # also the ledger and contract change

Rules (D-20261110-ulpian-jacquard-l1-correction; Ulpian RULE.md v2 section 2):
- a KEEP counts only when its quote is verbatim in the item's text and its birth date is on or before 1904-05-02;
- both arms KEEP (valid) -> keep; both RETURN -> return; anything else -> the coordinator's recorded decision in
  COORDINATOR.jsonl, which must exist for every disagreement;
- planted controls are scored against CONTROL_KEY.json and never written to the ledger.
--apply removes the returned rows' lines from the status ledger, writes the wave-1 rows file without them
(PROPOSED_STATUS_ROWS.r1.csv) and updates the Jacquard wave-1 entry of jobs/claim-kit/population_contract.json
(count, rows pin, authorization pins), then validates the population with jobs/claim-kit/population.py.
"""
import csv
import datetime as dt
import hashlib
import importlib.util
import io
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent.parent
LAST_BIRTH = dt.date(1904, 5, 2)
LEDGER = "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv"
CONTRACT = "jobs/claim-kit/population_contract.json"
WAVE1_ROWS = "research/excavator/jacquard-2026-10-31/PROPOSED_STATUS_ROWS.csv"
NEW_ROWS = "research/ulpian/jacquard-l1-correction/PROPOSED_STATUS_ROWS.r1.csv"
RULING = "research/readiness/owner_rulings/2026-11-10-ulpian-outer-bound.md"
REL = "research/ulpian/jacquard-l1-correction/"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pin(rel):
    return {"path": rel, "sha256": sha((REPO / rel).read_bytes())}


def jsonl(name):
    path = HERE / name
    return {r["item"]: r for r in (json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip())} \
        if path.is_file() else {}


def valid(answer, text):
    """(verdict, why) with KEEP downgraded to INVALID when its quote or date does not hold."""
    if not answer:
        return "MISSING", "no answer"
    if answer.get("verdict") != "KEEP":
        return "RETURN", answer.get("reason", "")
    quote = answer.get("quote") or ""
    if len(quote) < 8 or quote not in text:
        return "INVALID", "KEEP quote not verbatim in the text"
    try:
        born = dt.date.fromisoformat(answer.get("born_no_later_than") or "")
    except ValueError:
        return "INVALID", "KEEP without a birth date"
    if born > LAST_BIRTH:
        return "INVALID", f"KEEP birth date {born} is after {LAST_BIRTH}"
    return "KEEP", answer.get("reason", "")


def adjudicate():
    packet = jsonl("PACKET.jsonl")
    key = {k["item"]: k for k in json.loads((HERE / "CONTROL_KEY.json").read_text(encoding="utf-8"))["items"]}
    arm_a, arm_b, coord = jsonl("ARM_A.jsonl"), jsonl("ARM_B.jsonl"), jsonl("COORDINATOR.jsonl")
    rows, controls, pending = [], [], []
    for item in sorted(packet):
        text, k = packet[item]["text"], key[item]
        va, wa = valid(arm_a.get(item), text)
        vb, wb = valid(arm_b.get(item), text)
        c = coord.get(item)
        if c:
            final, by, reason = c["final"], "coordinator", c["reason"]
        elif va == vb and va in ("KEEP", "RETURN"):
            final, by, reason = va, "both_arms", (wa if va == "RETURN" else (arm_a[item].get("reason") or ""))
        else:
            final, by, reason = "PENDING", "", f"arms disagree: A {va} ({wa}); B {vb} ({wb})"
            pending.append(item)
        quote = ""
        if final == "KEEP":
            quote = (c or {}).get("quote") or (arm_a.get(item) or {}).get("quote") or (arm_b.get(item) or {}).get("quote")
        row = {"item": item, "instrument_id": k["instrument_id"], "order_date": k["order_date"],
               "text_path": k["text_path"], "text_sha256": k["text_sha256"], "arm_a": va, "arm_b": vb,
               "final": final, "decided_by": by, "quote": quote,
               "born_no_later_than": (c or {}).get("born_no_later_than") or (arm_a.get(item) or {}).get("born_no_later_than", "")
               if final == "KEEP" else "", "reason": reason}
        if k["control"]:
            ctl = k["control"]
            row.update({"control_kind": ctl["kind"], "expected": ctl["expected"],
                        "voided": bool(ctl.get("voided")), "void_reason": ctl.get("void_reason", "")})
            controls.append(row)
        else:
            rows.append(row)
    return rows, controls, pending


def write_reports(rows, controls, pending):
    fields = ["instrument_id", "order_date", "final", "decided_by", "arm_a", "arm_b", "quote", "born_no_later_than",
              "reason", "text_path", "text_sha256", "item"]
    with open(HERE / "DECISIONS.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in sorted(rows, key=lambda r: int("".join(ch for ch in r["instrument_id"] if ch.isdigit()) or 0)):
            w.writerow({f: r.get(f, "") for f in fields})
    scored = [c for c in controls if not c["voided"]]
    summary = {
        "schema": "ulpian-jacquard-l1-correction/v1",
        "decision": "D-20261110-ulpian-jacquard-l1-correction",
        "rows": len(rows), "keep": sum(r["final"] == "KEEP" for r in rows),
        "return": sum(r["final"] == "RETURN" for r in rows), "pending": pending,
        "agreement": sum(r["arm_a"] == r["arm_b"] for r in rows),
        "coordinator_decided": sum(r["decided_by"] == "coordinator" for r in rows),
        "controls": [{k: c[k] for k in ("item", "instrument_id", "control_kind", "expected", "arm_a", "arm_b",
                                         "voided", "void_reason")} for c in controls],
        "controls_caught_by_both": sum(c["arm_a"] == c["expected"] and c["arm_b"] == c["expected"] for c in scored),
        "controls_scored": len(scored),
        "inputs": [pin(REL + n) for n in ("PACKET.jsonl", "CONTROL_KEY.json", "ARM_A.jsonl", "ARM_B.jsonl",
                                          "COORDINATOR.jsonl", "INSTRUCTIONS.md") if (HERE / n).is_file()],
        "certified": 0,
    }
    (HERE / "ADJUDICATION.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
                                            newline="\n")
    return summary


def population_module():
    spec = importlib.util.spec_from_file_location("kit_population", REPO / "jobs/claim-kit/population.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def apply(rows, summary):
    if summary["pending"]:
        raise SystemExit("refused: disagreements without a coordinator decision: " + ", ".join(summary["pending"]))
    scored = [c for c in summary["controls"] if not c["voided"]]
    if any(c["arm_a"] != c["expected"] or c["arm_b"] != c["expected"] for c in scored):
        raise SystemExit("refused: a scored control was missed by an arm; the review set is not valid")
    returned = {r["instrument_id"] for r in rows if r["final"] == "RETURN"}
    wave1_text = (REPO / WAVE1_ROWS).read_text(encoding="utf-8")
    reader = list(csv.DictReader(io.StringIO(wave1_text, newline="")))
    header = wave1_text.splitlines(keepends=True)[0]
    lines = wave1_text.splitlines(keepends=True)[1:]
    assert len(lines) == len(reader)
    kept_lines = [line for line, r in zip(lines, reader) if r["instrument_id"] not in returned]
    removed_lines = [line for line, r in zip(lines, reader) if r["instrument_id"] in returned]
    assert len(removed_lines) == len(returned), "a returned order is not in the wave-1 rows"
    new_rows = (header + "".join(kept_lines)).encode("utf-8")
    ledger = (REPO / LEDGER).read_text(encoding="utf-8")
    for line in removed_lines:
        if ledger.count(line) != 1:
            raise SystemExit(f"refused: ledger row not present exactly once: {line[:40]}")
        ledger = ledger.replace(line, "")
    record = {"schema": "ulpian-jacquard-l1-correction-record/v1",
              "decision": "D-20261110-ulpian-jacquard-l1-correction", "ruling": pin(RULING),
              "returned": sorted(returned, key=lambda s: int("".join(ch for ch in s if ch.isdigit()))),
              "kept": sorted((r["instrument_id"] for r in rows if r["final"] == "KEEP"),
                             key=lambda s: int("".join(ch for ch in s if ch.isdigit()))),
              "decisions": pin(REL + "DECISIONS.csv"), "adjudication": pin(REL + "ADJUDICATION.json"),
              "replaces_rows": pin(WAVE1_ROWS),
              "effect": "returned orders are undecided again; kept orders stay provisional NO with the quoted fact as basis"}
    contract_path = REPO / CONTRACT
    contract_text = contract_path.read_text(encoding="utf-8")
    contract = json.loads(contract_text)
    entry = next(e for e in contract["accepted_additions"]
                 if e["name"] == "Jacquard individually reviewed owner adoption, wave 1")
    old_count = entry["count"]
    (REPO / NEW_ROWS).write_bytes(new_rows)
    (HERE / "CORRECTION.json").write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8",
                                          newline="\n")
    # Edit the entry's own text in place, so the rest of the contract keeps its bytes and layout.
    start = contract_text.index('"name": "Jacquard individually reviewed owner adoption, wave 1"')
    end = contract_text.index('"name":', start + 10)
    seg = contract_text[start:end]
    new_seg = seg.replace(f'"count": {old_count},', f'"count": {old_count - len(returned)},', 1)
    new_seg = new_seg.replace(f'"path": "{WAVE1_ROWS}",\n        "sha256": "{entry["rows"]["sha256"]}"',
                              f'"path": "{NEW_ROWS}",\n        "sha256": "{sha(new_rows)}"', 1)
    pins_end = new_seg.rindex("]")
    extra = "".join(f',\n        {{\n          "path": "{p["path"]}",\n          "sha256": "{p["sha256"]}"\n        }}'
                    for p in (pin(WAVE1_ROWS), pin(RULING), pin(REL + "CORRECTION.json")))
    body = new_seg[:pins_end].rstrip()
    new_seg = body + extra + "\n      " + new_seg[pins_end:]
    assert new_seg != seg and new_seg.count(NEW_ROWS) == 1, "contract entry edit did not apply"
    contract_path.write_text(contract_text[:start] + new_seg + contract_text[end:], encoding="utf-8", newline="")
    check = next(e for e in json.loads(contract_path.read_text(encoding="utf-8"))["accepted_additions"]
                 if e["name"] == entry["name"])
    assert check["count"] == old_count - len(returned) and check["rows"]["path"] == NEW_ROWS
    (REPO / LEDGER).write_text(ledger, encoding="utf-8", newline="")
    result = population_module().validate_inputs(REPO)
    print(json.dumps({"decided_after": result["decided"], "returned": len(returned),
                      "wave1_count": f"{old_count} -> {check['count']}"}))


def main():
    rows, controls, pending = adjudicate()
    summary = write_reports(rows, controls, pending)
    print(json.dumps({k: summary[k] for k in ("rows", "keep", "return", "pending", "agreement",
                                               "coordinator_decided", "controls_caught_by_both", "controls_scored")}))
    if "--apply" in sys.argv:
        apply(rows, summary)


if __name__ == "__main__":
    main()

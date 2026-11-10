"""Adjudicate the blind arms of every L1R batch and, with --apply, write the correction (D-20261110-ulpian-l1r-correction).

    python -I research/ulpian/jacquard-l1r-correction/adjudicate.py                 # DECISIONS.csv, ADJUDICATION.json
    python -I research/ulpian/jacquard-l1r-correction/adjudicate.py --apply         # plus ledger and contract

Same rules as research/ulpian/jacquard-l1-correction/adjudicate.py: a KEEP counts only when its quote is verbatim in
the item text and its birth date is on or before 1904-05-02; both arms agreeing decides a row; a disagreement needs a
coordinator record in COORDINATOR.jsonl; a batch whose arms missed a scored control is refused. --apply removes the
returned rows' lines from the ledger and rewrites the rows pin, count and authorization pins of the Jacquard wave-2
entry (and of the wave-1 entry for EO 940, 1596, 1604) in jobs/claim-kit/population_contract.json, then validates
the population with jobs/claim-kit/population.py.
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
REL = "research/ulpian/jacquard-l1r-correction/"
LAST_BIRTH = dt.date(1904, 5, 2)
LEDGER = "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv"
CONTRACT = "jobs/claim-kit/population_contract.json"
RULING = "research/readiness/owner_rulings/2026-11-10-ulpian-l1r-correction.md"
ENTRIES = {
    2: {"name": "Jacquard individually reviewed owner adoption, wave 2", "new_rows": REL + "PROPOSED_STATUS_ROWS_W2.r1.csv"},
    1: {"name": "Jacquard individually reviewed owner adoption, wave 1", "new_rows": REL + "PROPOSED_STATUS_ROWS_W1.r2.csv"},
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pin(rel):
    return {"path": rel, "sha256": sha((REPO / rel).read_bytes())}


def jsonl(path):
    return {r["item"]: r for r in (json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip())} \
        if path.is_file() else {}


def valid(answer, text):
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
    key = json.loads((HERE / "CONTROL_KEY.json").read_text(encoding="utf-8"))
    coord = jsonl(HERE / "COORDINATOR.jsonl")
    rows, controls, pending, batches = [], [], [], {}
    for b, bk in sorted(key["batches"].items()):
        packet = jsonl(HERE / f"PACKET_{b}.jsonl")
        arm_a, arm_b = jsonl(HERE / f"ARM_A_{b}.jsonl"), jsonl(HERE / f"ARM_B_{b}.jsonl")
        batches[b] = {"items": len(packet), "arm_a": len(arm_a), "arm_b": len(arm_b)}
        for k in bk["items"]:
            item, text = k["item"], packet[k["item"]]["text"]
            va, wa = valid(arm_a.get(item), text)
            vb, wb = valid(arm_b.get(item), text)
            c = coord.get(item)
            if c:
                final, by, reason = c["final"], "coordinator", c["reason"]
            elif va == vb and va in ("KEEP", "RETURN"):
                final, by, reason = va, "both_arms", wa if va == "RETURN" else (arm_a[item].get("reason") or "")
            else:
                final, by, reason = "PENDING", "", f"arms disagree: A {va} ({wa}); B {vb} ({wb})"
                pending.append(item)
            src = c or (arm_a.get(item) if va == "KEEP" else arm_b.get(item)) or {}
            row = {"batch": b, "item": item, "instrument_id": k["instrument_id"], "wave": k["wave"],
                   "order_date": k["date"], "text_path": k["text_path"], "text_sha256": k["text_sha256"],
                   "arm_a": va, "arm_b": vb, "final": final, "decided_by": by,
                   "quote": src.get("quote", "") if final == "KEEP" else "",
                   "born_no_later_than": src.get("born_no_later_than", "") if final == "KEEP" else "",
                   "reason": reason}
            if k["control"]:
                row.update({"control_kind": k["control"]["kind"], "expected": k["control"]["expected"],
                            "voided": bool(k["control"].get("voided")), "void_reason": k["control"].get("void_reason", "")})
                controls.append(row)
            else:
                rows.append(row)
    return rows, controls, pending, batches


def num(iid):
    digits = "".join(ch for ch in iid if ch.isdigit())
    return int(digits or 0)


def write_reports(rows, controls, pending, batches):
    fields = ["instrument_id", "wave", "order_date", "final", "decided_by", "arm_a", "arm_b", "quote",
              "born_no_later_than", "reason", "batch", "item", "text_path", "text_sha256"]
    with open(HERE / "DECISIONS.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in sorted(rows, key=lambda r: num(r["instrument_id"])):
            w.writerow({f: r.get(f, "") for f in fields})
    scored = [c for c in controls if not c["voided"]]
    summary = {
        "schema": "ulpian-jacquard-l1r-correction/v1", "decision": "D-20261110-ulpian-l1r-correction",
        "batches": batches, "rows": len(rows), "keep": sum(r["final"] == "KEEP" for r in rows),
        "return": sum(r["final"] == "RETURN" for r in rows), "pending": pending,
        "agreement": sum(r["arm_a"] == r["arm_b"] for r in rows),
        "coordinator_decided": sum(r["decided_by"] == "coordinator" for r in rows),
        "controls": [{k: c[k] for k in ("batch", "item", "instrument_id", "control_kind", "expected", "arm_a", "arm_b",
                                         "voided", "void_reason")} for c in controls],
        "controls_caught_by_both": sum(c["arm_a"] == c["expected"] and c["arm_b"] == c["expected"] for c in scored),
        "controls_scored": len(scored),
        "inputs": [pin(REL + p.name) for p in sorted(HERE.glob("*.jsonl")) if p.name != "TAGS.jsonl"]
                  + [pin(REL + "CONTROL_KEY.json"), pin(REL + "INSTRUCTIONS.md")],
        "certified": 0,
    }
    (HERE / "ADJUDICATION.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n",
                                            encoding="utf-8", newline="\n")
    return summary


def population_module():
    spec = importlib.util.spec_from_file_location("kit_population", REPO / "jobs/claim-kit/population.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def edit_entry(contract_text, name, old_rows, new_rows_rel, new_rows_bytes, old_count, removed, extra_pins):
    start = contract_text.index(f'"name": "{name}"')
    nxt = contract_text.find('"name":', start + 10)
    end = nxt if nxt != -1 else len(contract_text)
    seg = contract_text[start:end]
    new = seg.replace(f'"count": {old_count},', f'"count": {old_count - removed},', 1)
    new = new.replace(f'"path": "{old_rows["path"]}",\n        "sha256": "{old_rows["sha256"]}"',
                      f'"path": "{new_rows_rel}",\n        "sha256": "{sha(new_rows_bytes)}"', 1)
    pins_end = new.index("\n      ]", new.index('"authorization_pins"'))
    extra = "".join(f',\n        {{\n          "path": "{p["path"]}",\n          "sha256": "{p["sha256"]}"\n        }}'
                    for p in extra_pins)
    new = new[:pins_end] + extra + new[pins_end:]
    assert new != seg and new.count(new_rows_rel) == 1, f"contract entry edit did not apply: {name}"
    return contract_text[:start] + new + contract_text[end:]


def apply(rows, summary):
    if summary["pending"]:
        raise SystemExit("refused: disagreements without a coordinator decision: " + ", ".join(summary["pending"]))
    scored = [c for c in summary["controls"] if not c["voided"]]
    missed = [c["item"] for c in scored if c["arm_a"] != c["expected"] or c["arm_b"] != c["expected"]]
    if missed:
        raise SystemExit("refused: scored controls missed: " + ", ".join(missed))
    contract_text = (REPO / CONTRACT).read_text(encoding="utf-8")
    contract = json.loads(contract_text)
    ledger = (REPO / LEDGER).read_text(encoding="utf-8")
    before = len(population_module().validate_inputs(REPO)["statuses"])
    record = {"schema": "ulpian-jacquard-l1r-correction-record/v1", "decision": "D-20261110-ulpian-l1r-correction",
              "ruling": pin(RULING), "decisions": pin(REL + "DECISIONS.csv"),
              "adjudication": pin(REL + "ADJUDICATION.json"), "waves": {}}
    plans = []
    for wave, spec in ENTRIES.items():
        entry = next(e for e in contract["accepted_additions"] if e["name"] == spec["name"])
        returned = {r["instrument_id"] for r in rows if r["wave"] == wave and r["final"] == "RETURN"}
        kept = sorted((r["instrument_id"] for r in rows if r["wave"] == wave and r["final"] == "KEEP"), key=num)
        raw = (REPO / entry["rows"]["path"]).read_bytes()
        assert sha(raw) == entry["rows"]["sha256"], "rows file differs from its contract pin"
        text = raw.decode("utf-8").replace("\r\n", "\n")      # the wave-2 rows file is CRLF; the ledger is LF
        lines = text.splitlines(keepends=True)
        parsed = list(csv.DictReader(io.StringIO(text, newline="")))
        assert len(lines) - 1 == len(parsed)
        drop = [line for line, r in zip(lines[1:], parsed) if r["instrument_id"] in returned]
        assert len(drop) == len(returned), f"wave {wave}: a returned order is not in its rows file"
        new_bytes = (lines[0] + "".join(l for l, r in zip(lines[1:], parsed) if r["instrument_id"] not in returned)).encode("utf-8")
        for line in drop:
            if ledger.count(line) != 1:
                raise SystemExit(f"refused: ledger row not present exactly once: {line[:40]}")
            ledger = ledger.replace(line, "")
        record["waves"][str(wave)] = {"entry": spec["name"], "replaces_rows": entry["rows"],
                                      "returned": sorted(returned, key=num), "kept": kept}
        plans.append((spec, entry, new_bytes, len(returned)))
    (HERE / "CORRECTION.json").write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n",
                                          encoding="utf-8", newline="\n")
    for spec, entry, new_bytes, removed in plans:
        (REPO / spec["new_rows"]).write_bytes(new_bytes)
        contract_text = edit_entry(contract_text, spec["name"], entry["rows"], spec["new_rows"], new_bytes,
                                   entry["count"], removed, [entry["rows"], pin(RULING), pin(REL + "CORRECTION.json")])
    (REPO / CONTRACT).write_text(contract_text, encoding="utf-8", newline="")
    (REPO / LEDGER).write_text(ledger, encoding="utf-8", newline="")
    after = len(population_module().validate_inputs(REPO)["statuses"])
    removed_total = sum(p[3] for p in plans)
    assert after == before - removed_total, (before, after, removed_total)
    print(json.dumps({"decided_before": before, "decided_after": after,
                      "returned_by_wave": {str(w): p[3] for w, p in zip(ENTRIES, plans)}}))


def main():
    rows, controls, pending, batches = adjudicate()
    summary = write_reports(rows, controls, pending, batches)
    print(json.dumps({k: summary[k] for k in ("batches", "rows", "keep", "return", "agreement", "coordinator_decided",
                                               "controls_caught_by_both", "controls_scored")} | {"pending": len(pending)}))
    if "--apply" in sys.argv:
        apply(rows, summary)


if __name__ == "__main__":
    main()

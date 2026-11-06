"""Build the order card view: one card per executive order with its readiness steps.

Reads two committed job outputs and changes nothing upstream:
  jobs/domesday-register/output/REGISTER.csv          (date, title, president, best document held)
  jobs/readiness-tracker/output/READINESS_BY_ORDER.csv (status, steps, ready, blockers)
Writes OUTPUT_DIR/CARDS.html (self-contained page) and OUTPUT_DIR/SUMMARY.json.

No count here is a new measurement: every figure is copied or tallied from the tracker's own rows,
and the page names the tracker run it came from. Human certification stays 0 unless the tracker says otherwise.
"""

import csv
import json
import os
import pathlib
import re

HERE = pathlib.Path(__file__).parent
REPO = pathlib.Path(os.environ.get("REPO_ROOT", HERE.parent.parent))
OUT = pathlib.Path(os.environ.get("OUTPUT_DIR", HERE / "output"))

REGISTER = REPO / "jobs/domesday-register/output/REGISTER.csv"
REGISTER_SUMMARY = REPO / "jobs/domesday-register/output/SUMMARY.json"
UNNUMBERED_SUMMARY = REPO / "jobs/domesday-register/output/UNNUMBERED_SUMMARY.json"
READINESS = REPO / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv"
TRACKER_STATUS = REPO / "jobs/readiness-tracker/output/STATUS.json"

STEPS = ["provisional_status", "original_text", "clause_inventory", "ending_or_current_basis",
         "savings_residuals", "counterevidence", "shared_sources", "opus_media"]
STEP_CHAR = {"done": "d", "provisional": "p", "open": "o", "n/a": "-", "": "-"}

# Dates each president took office. Used only when the register names no president; the page marks such
# names as derived from the date, and a date equal to a term's first day is left as uncertain.
TERMS = [
    ("1861-03-04", "Abraham Lincoln"), ("1865-04-15", "Andrew Johnson"), ("1869-03-04", "Ulysses S. Grant"),
    ("1877-03-04", "Rutherford B. Hayes"), ("1881-03-04", "James A. Garfield"),
    ("1881-09-20", "Chester A. Arthur"), ("1885-03-04", "Grover Cleveland"),
    ("1889-03-04", "Benjamin Harrison"), ("1893-03-04", "Grover Cleveland"),
    ("1897-03-04", "William McKinley"), ("1901-09-14", "Theodore Roosevelt"),
    ("1909-03-04", "William Howard Taft"), ("1913-03-04", "Woodrow Wilson"),
    ("1921-03-04", "Warren G. Harding"), ("1923-08-03", "Calvin Coolidge"),
    ("1929-03-04", "Herbert Hoover"), ("1933-03-04", "Franklin D. Roosevelt"),
    ("1945-04-12", "Harry S. Truman"), ("1953-01-20", "Dwight D. Eisenhower"),
    ("1961-01-20", "John F. Kennedy"), ("1963-11-22", "Lyndon B. Johnson"),
    ("1969-01-20", "Richard Nixon"), ("1974-08-09", "Gerald Ford"), ("1977-01-20", "Jimmy Carter"),
    ("1981-01-20", "Ronald Reagan"), ("1989-01-20", "George H.W. Bush"),
    ("1993-01-20", "William J. Clinton"), ("2001-01-20", "George W. Bush"),
    ("2009-01-20", "Barack Obama"), ("2017-01-20", "Donald Trump"),
    ("2021-01-20", "Joseph R. Biden Jr."), ("2025-01-20", "Donald Trump"),
]
TERM_STARTS = {d for d, _ in TERMS}
UNKNOWN_PRES = "President not recorded"


def president_from_date(date):
    """Return (name, how) for an ISO date; how is 'date' or 'transition' or 'none'.

    A year-only or year-month date is attributed only when no term began inside that span."""
    date = date or ""
    if re.fullmatch(r"\d{4}(-\d{2})?", date):
        if any(start.startswith(date) for start in TERM_STARTS):
            return UNKNOWN_PRES, "none"
        name, how = president_from_date(date + ("-12-31" if len(date) == 4 else "-28"))
        return (name, how) if how == "date" else (UNKNOWN_PRES, "none")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        return UNKNOWN_PRES, "none"
    if date in TERM_STARTS:
        return UNKNOWN_PRES, "transition"
    name = None
    for start, who in TERMS:
        if date >= start:
            name = who
    return (name, "date") if name else (UNKNOWN_PRES, "none")


def sort_key(reg):
    num = reg.get("number") or ""
    if num.isdigit():
        return (0, int(num), reg.get("suffix") or "", reg.get("instrument_id"))
    return (1, 0, reg.get("date") or "9999", reg.get("instrument_id"))


def label(instrument_id, reg):
    if reg.get("number"):
        return reg["number"] + (reg.get("suffix") or "")
    m = re.search(r"row:(\d+)$", instrument_id)
    return f"Unnumbered · row {m.group(1)}" if m else instrument_id.removeprefix("EO:")


def origin_family(origin):
    if not origin:
        return ""
    head = origin.split(":", 1)[0]
    return re.sub(r"-\d{4}-\d{2}-\d{2}$", "", head)


class Index(dict):
    def __call__(self, value):
        if value not in self:
            self[value] = len(self)
        return self[value]

    def values_list(self):
        return [k for k, _ in sorted(self.items(), key=lambda kv: kv[1])]


def build(register_rows, readiness_rows, meta):
    reg = {r["instrument_id"]: r for r in register_rows}
    pres, eras, held, tiers, origins, codes = (Index() for _ in range(6))
    rows, mismatch, derived = [], [], 0
    agree = disagree = 0
    for rr in sorted(readiness_rows, key=lambda r: sort_key(reg.get(r["instrument_id"], {"instrument_id": r["instrument_id"]}))):
        i = rr["instrument_id"]
        g = reg.get(i)
        if g is None:
            mismatch.append(i)
            g = {}
        name = g.get("president") or ""
        how = "register"
        guess, guess_how = president_from_date(g.get("date", ""))
        if name:
            if guess_how == "date":
                agree += guess == name
                disagree += guess != name
        else:
            name, how = guess, guess_how
            derived += how == "date"
        steps = "".join(STEP_CHAR.get(rr.get("step_" + s, ""), "o") for s in STEPS)
        blockers = []
        for b in filter(None, (rr.get("blockers") or "").split("|")):
            code, _, detail = b.partition(":")
            blockers.append(str(codes(code)) + (":" + detail if detail else ""))
        status = {"no": 1, "yes": 2}.get(rr.get("provisional_status", ""), 0)
        rows.append([
            label(i, g), g.get("date", ""), g.get("title", ""), pres(name),
            {"register": 0, "date": 1, "transition": 2, "none": 3}[how],
            eras(g.get("era") or "Unknown date"), status, steps,
            1 if rr.get("ready_for_human_review") == "yes" else 0,
            tiers(rr.get("text_evidence_tier") or "missing"), held(g.get("best_held") or "not in register"),
            "|".join(blockers), 1 if rr.get("original_copy_replacement_required") == "yes" else 0,
            origins(origin_family(rr.get("decision_origin", ""))), i,
        ])

    ready = sum(r[8] for r in rows)
    with_status = sum(1 for r in rows if r[6])
    one_step = sum(1 for r in rows if not r[8] and r[6] and sum(c == "o" for c in r[7]) == 1)
    summary = {
        "orders": len(rows), "numbered_series_orders": len(rows), "ready_for_human_review": ready, "with_provisional_status": with_status,
        "not_researched": len(rows) - with_status, "one_step_from_ready": one_step,
        "human_certified": 0,
        "presidents_from_register": len(rows) - derived - sum(1 for r in rows if r[4] in (2, 3)),
        "presidents_derived_from_date": derived,
        "president_left_uncertain_transition_day": sum(1 for r in rows if r[4] == 2),
        "president_unknown_no_date": sum(1 for r in rows if r[4] == 3),
        "date_rule_check_against_register": {"agree": agree, "disagree": disagree},
        "readiness_rows_missing_from_register": mismatch,
        **meta,
    }
    data = {
        "meta": summary, "pres": pres.values_list(), "eras": eras.values_list(), "held": held.values_list(),
        "tiers": tiers.values_list(), "origins": origins.values_list(), "codes": codes.values_list(),
        "steps": STEPS, "rows": rows,
    }
    return data, summary


def unnumbered_meta(path=UNNUMBERED_SUMMARY):
    """Second denominator (owner ruling R10), shown beside the numbered-series count; None when not yet measured."""
    try:
        u = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        obs, est = u["unnumbered_series_observed"], u.get("unnumbered_series_estimate_95")
        if not isinstance(obs, int):
            raise ValueError
        return {"unnumbered_series_observed": obs,
                "unnumbered_series_estimate_95": est if isinstance(est, list) and len(est) == 2 else None}
    except (OSError, ValueError, KeyError, AttributeError):
        return {"unnumbered_series_observed": None, "unnumbered_series_estimate_95": None}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with open(REGISTER, newline="", encoding="utf-8") as f:
        register_rows = list(csv.DictReader(f))
    with open(READINESS, newline="", encoding="utf-8") as f:
        readiness_rows = list(csv.DictReader(f))
    status = json.loads(TRACKER_STATUS.read_text())
    reg_summary = json.loads(REGISTER_SUMMARY.read_text())
    meta = {
        "tracker_finished_utc": status.get("finished_utc"), "tracker_result": status.get("result"),
        "tracker_run_url": status.get("run_url"), "tracker_commit": status.get("commit_run"),
        "register_generated_utc": reg_summary.get("generated_utc"),
        **unnumbered_meta(),
    }
    data, summary = build(register_rows, readiness_rows, meta)
    if summary["readiness_rows_missing_from_register"]:
        print("Readiness rows missing from register:", len(summary["readiness_rows_missing_from_register"]))
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = (HERE / "template.html").read_text(encoding="utf-8").replace("/*__DATA__*/null", payload)
    (OUT / "CARDS.html").write_text(page, encoding="utf-8")
    (OUT / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "readiness_rows_missing_from_register"}, indent=2))
    print(f"CARDS.html: {len(page.encode()):,} bytes")


if __name__ == "__main__":
    main()

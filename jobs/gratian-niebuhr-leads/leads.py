"""Gratian: carry Niebuhr's identifications into the inputs Lewis reads, as leads only.

Niebuhr (research/niebuhr/) searched Clark's unknowns. For orders the census knows only by number, and for numbered
gaps and lettered citations, it reports a signing date and subject, mostly from secondary sources. This job turns
those rows into two typed lead files:

- DATE_LEADS.csv: one row per numbered order with a full date reported at high or medium confidence and no WPA
  disagreement. jobs/_lib/eo_identity.py load_dates() reads it after every official and index source, so Lewis
  (and every other load_dates user) can route by date when nothing better is known. A lead date never overrides
  another source's date; it only fills a missing date or refines a bare year that agrees.
- RESOLVED_REFERENCES.csv: dated references ("the Executive order of <date>") that Niebuhr resolved to an order the
  census already numbers. A candidate pairing for a person to check, not an edge.

Nothing here admits a census entry, sets a date of record, grades a text or authenticates an identity. Certified: 0.
"""
import csv
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_lib"))
import eo_identity as ident  # noqa: E402

SOURCE = "research/niebuhr/CORROBORATION.csv"
NUMBERED_GROUPS = {"in_census_number_only", "number_gap", "cited_lettered"}
IDENTIFIED = {"identified_no_text", "identified_with_text"}
CONFIDENT = {"high", "medium"}
ISO = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
LEAD_GRADE = "secondary_identification_lead"
NOTICE = "Lead only (Niebuhr discovery, mostly secondary sources): no census entry, date of record, grade or identity follows."
DATE_FIELDS = ["instrument_id", "in_census", "group", "date", "title_or_subject", "president", "confidence",
               "outcome", "wpa_check", "official_sources", "first_url", "lead_grade", "notice"]
REF_FIELDS = ["reference_id", "resolved_to", "resolved_in_census", "date", "title_or_subject", "confidence",
              "first_url", "resolution_note", "notice"]


def canonical(value):
    parsed = ident.parse_eo_id(value or "")
    return ident.canon_id(*parsed) if parsed else None


def build(repo):
    repo = Path(repo)
    rows = ident.read_csv(str(repo / SOURCE))
    universe = set(ident.load_universe(str(repo)))
    dates, refs, skipped = [], [], {}

    def skip(reason):
        skipped[reason] = skipped.get(reason, 0) + 1

    for r in rows:
        group, outcome = r.get("group"), r.get("outcome")
        if outcome == "reference_resolved_to_known_order":
            raw = (r.get("resolved_to") or "").strip()
            to = canonical(raw.split()[0] if raw else "")
            if not to:
                skip("resolved_reference_without_numbered_order")
                continue
            refs.append({"reference_id": r.get("target_id", ""), "resolved_to": to,
                         "resolved_in_census": "yes" if to in universe else "no", "date": r.get("date", ""),
                         "title_or_subject": (r.get("title_or_subject") or "")[:200],
                         "confidence": r.get("confidence", ""), "first_url": r.get("first_url", ""),
                         "resolution_note": raw, "notice": NOTICE})
            continue
        if group not in NUMBERED_GROUPS:
            skip("unnumbered_reference_group")
            continue
        if outcome not in IDENTIFIED:
            skip("not_identified:" + str(outcome))
            continue
        iid = canonical(r.get("target_id"))
        date = (r.get("date") or "").strip()
        if not iid:
            skip("target_not_numbered")
        elif r.get("confidence") not in CONFIDENT:
            skip("low_confidence")
        elif not ISO.match(date) or ident.parse_date(date) is None:
            skip("no_full_date")
        elif "disagree" in (r.get("wpa_check") or ""):
            skip("wpa_disagrees")
        else:
            dates.append({"instrument_id": iid, "in_census": "yes" if iid in universe else "no", "group": group,
                          "date": date, "title_or_subject": (r.get("title_or_subject") or "")[:200],
                          "president": r.get("president", ""), "confidence": r["confidence"], "outcome": outcome,
                          "wpa_check": r.get("wpa_check", ""), "official_sources": r.get("official_sources", ""),
                          "first_url": r.get("first_url", ""), "lead_grade": LEAD_GRADE, "notice": NOTICE})
    ids = [d["instrument_id"] for d in dates]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate Niebuhr date lead for one order")
    dates.sort(key=lambda d: ident.parse_eo_id(d["instrument_id"]))
    refs.sort(key=lambda d: (d["reference_id"], d["resolved_to"]))
    summary = {"schema": "gratian-niebuhr-leads/v1", "source": SOURCE, "source_rows": len(rows),
               "date_leads": len(dates), "date_leads_in_census": sum(d["in_census"] == "yes" for d in dates),
               "resolved_references": len(refs), "skipped": dict(sorted(skipped.items())),
               "readers": ["jobs/_lib/eo_identity.py load_dates (label niebuhr_identification_lead)"],
               "establishes": "nothing: leads only; census, dates of record, grades and identity unchanged",
               "network_requests": 0}
    return dates, refs, summary


def write(out, dates, refs, summary):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, fields, rows in (("DATE_LEADS.csv", DATE_FIELDS, dates), ("RESOLVED_REFERENCES.csv", REF_FIELDS, refs)):
        with open(out / name, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    repo = os.environ.get("REPO_ROOT", ".")
    out = os.environ.get("OUTPUT_DIR", str(HERE / "output"))
    dates, refs, summary = build(repo)
    write(out, dates, refs, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

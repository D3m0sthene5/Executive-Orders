"""Build data/TARGETS.csv: the undecided numbered orders 1-5075 that have nothing on file, joined with the
WPA 1944 numbered list's date and one-line summary for each.

Run once by hand (the job reads the committed result):

    python jobs/numbered-early-orders/build_targets.py <path to wpa-lists NUMBERED_ENTRIES.csv>

Targets: every research/gap-census/census.csv row whose evidence columns are all "no" and whose order
number is below 5076 (a lettered or half order counts by its number). The WPA file is the wpa-lists job's
output (branch wpa-lists); its commit and hash go into data/PROVENANCE.json.
"""
import csv
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
CENSUS = "research/gap-census/census.csv"
FIELDS = ["instrument_id", "order_number", "number", "suffix", "wpa_rows", "year", "month_day", "wpa_page",
          "family_hint", "citations", "summary"]


def sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def targets(repo):
    with open(repo / CENSUS, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    cols = [c for c in rows[0] if c not in ("order_number", "instrument_id")]
    out = []
    for r in rows:
        m = re.match(r"(\d+)(.*)$", r["order_number"] or "")
        if m and int(m.group(1)) < 5076 and all(r[c] == "no" for c in cols):
            out.append((r["instrument_id"], r["order_number"], int(m.group(1)), m.group(2)))
    return out


def main(wpa_path, wpa_commit):
    tg = targets(REPO)
    with open(wpa_path, encoding="utf-8", newline="") as fh:
        wpa = {}
        for r in csv.DictReader(fh):
            wpa.setdefault(r["id"], []).append(r)
    rows = []
    for iid, num, n, suffix in tg:
        entries = wpa.get(iid) or [None]
        for i, e in enumerate(entries):
            rows.append({"instrument_id": iid, "order_number": num, "number": n, "suffix": suffix,
                         "wpa_rows": 0 if e is None else len(entries),
                         "year": e["year"] if e else "", "month_day": e["month_day"] if e else "",
                         "wpa_page": e["page"] if e else "", "family_hint": e["family_hint"] if e else "",
                         "citations": e["citations_joined"] if e else "", "summary": e["text"] if e else ""})
    out = HERE / "data" / "TARGETS.csv"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    prov = {
        "targets": {"file": "data/TARGETS.csv", "sha256": sha256(out), "orders": len(tg), "rows": len(rows),
                    "rule": "census.csv rows with every evidence column 'no' and order number below 5076; "
                            "lettered and half orders count by their number",
                    "census": CENSUS, "census_sha256": sha256(REPO / CENSUS)},
        "wpa_numbered_list": {"job": "wpa-lists", "branch": "wpa-lists", "commit": wpa_commit,
                              "file": "jobs/wpa-lists/output/NUMBERED_ENTRIES.csv", "sha256": sha256(wpa_path),
                              "what": "WPA Historical Records Survey, Presidential Executive Orders, Numbered "
                                      "1-8030 (1944), parsed by the wpa-lists job. Only the date, the summary and "
                                      "the citations are used, to recognise an order in a book. A target the "
                                      "parse lacks (half orders and a few others) can be found only by number."},
    }
    (HERE / "data" / "PROVENANCE.json").write_text(json.dumps(prov, indent=1, ensure_ascii=False) + "\n",
                                                   encoding="utf-8")
    print(f"{len(tg)} target orders, {len(rows)} rows, "
          f"{sum(1 for r in rows if r['wpa_rows'] == 0)} without a WPA entry")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "")

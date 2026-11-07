"""Fold the Opus page-check results into the job output.

Reads research/excavator/photius-gpo/packets/*/RESULT.jsonl and writes output/PAGE_CHECKS.csv (one row per checked
order: result, what the page showed, note) and output/RECOVERED.csv (orders whose tag the OCR missed but whose heading
or closing tag a checker saw inside another order's span: number, volume, page, dateline). segment.py reads both.

    python -I jobs/photius-gpo-volumes/apply_checks.py
"""
import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PK = REPO / "research/excavator/photius-gpo/packets"
OUT = REPO / "jobs/photius-gpo-volumes/output"


def main():
    checks, recovered = {}, {}
    orders = {r["instrument_id"]: r for r in csv.DictReader(open(OUT / "ORDERS.csv", encoding="utf-8"))}
    for f in sorted(PK.glob("*/RESULT.jsonl")):
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            iid = r.get("instrument_id")
            if not iid:
                continue
            checks[iid] = {"instrument_id": iid, "result": r.get("result", ""), "by": f"opus/{f.parent.name}",
                           "number_on_page": r.get("number_on_page", ""), "dateline_on_page": r.get("dateline_on_page", ""),
                           "signatory_on_page": r.get("signatory_on_page", ""), "first_words": r.get("first_words", ""),
                           "note": (r.get("note") or "")[:300]}
            htid = orders.get(iid, {}).get("htid", "")
            for o in r.get("other_orders_in_span") or []:
                num = str(o.get("number") or "").strip().upper().replace("-", "")
                if not num or not num[0].isdigit():
                    continue
                recovered.setdefault(num, {"number": num, "htid": htid, "pdf_page": o.get("pdf_page", ""), "dateline": o.get("dateline", ""),
                                           "seen_in_span_of": iid, "by": f"opus/{f.parent.name}"})
    # a recovered order was seen on the page by the checker: that is its page check
    import sys
    sys.path.insert(0, str(REPO / "jobs" / "_lib"))
    import eo_identity as ei
    for num, rr in recovered.items():
        n = int("".join(ch for ch in num if ch.isdigit()))
        suf = "".join(ch for ch in num if ch.isalpha())
        iid = ei.canon_id(n, suf)
        if iid not in checks:
            checks[iid] = {"instrument_id": iid, "result": "pass", "by": rr["by"], "number_on_page": num,
                           "dateline_on_page": rr["dateline"], "signatory_on_page": "", "first_words": "",
                           "note": f"heading or closing tag seen on PDF page {rr['pdf_page']} of {rr['htid']} inside the span of {rr['seen_in_span_of']}"}
    with open(OUT / "PAGE_CHECKS.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["instrument_id", "result", "by", "number_on_page", "dateline_on_page", "signatory_on_page", "first_words", "note"])
        w.writeheader()
        w.writerows(checks.values())
    with open(OUT / "RECOVERED.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["number", "htid", "pdf_page", "dateline", "seen_in_span_of", "by"])
        w.writeheader()
        w.writerows(sorted(recovered.values(), key=lambda r: (r["htid"], str(r["pdf_page"]))))
    from collections import Counter
    print("checks", len(checks), dict(Counter(c["result"] for c in checks.values())), "recovered numbers", len(recovered))


if __name__ == "__main__":
    main()

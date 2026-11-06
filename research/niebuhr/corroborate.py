"""Check every Niebuhr searcher result against the WPA indexes the project already holds.

For a numbered order, the WPA "Presidential Executive Orders, Numbered 1-8030" (1944) OCR text is searched near the
order's number for the month and day the searcher reported. For a dated reference, the New Jersey "List and Index of
Presidential Executive Orders, Unnumbered Series" (1943) is searched for entries on that date. The result says whether
the official index agrees, disagrees or is silent. It never changes a census entry, count or grade.

Usage: python3 -I research/niebuhr/corroborate.py RESULTS_DIR OUT_CSV
"""
import csv
import datetime as dt
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
WPA_N = os.path.join(ROOT, "jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv")
WPA_U = os.path.join(ROOT, "jobs/x1-class-engine/data/WPA_UNNUMBERED_ENTRIES.csv")
MON = ["Jan", "Feb", "Mar", "Apr", "May", "June", "July", "Aug", "Sept", "Oct", "Nov", "Dec"]
MON_RX = ["Jan", "Feb", "Mar", "Apr", "May", "June?", "July?", "Aug", "Sept?", "Oct", "Nov", "Dec"]
HALF = r"(?:½|1/2|l/2|1 /2|i/2|\^2?|%|V2|y2|\*4)"  # OCR spellings of ½ seen in the WPA text


def wpa_text():
    rows = list(csv.DictReader(open(WPA_N, encoding="utf-8")))
    parts, spans = [], []
    pos = 0
    for r in rows:
        t = " " + r["text"]
        parts.append(t)
        spans.append((pos, r))
        pos += len(t)
    return "".join(parts), spans


def numbered_check(full, spans, number, suffix, date):
    """('agrees'|'disagrees'|'silent', excerpt). Looks for an entry head for the number, then the date that follows it."""
    if not date:
        return "no_date_reported", ""
    try:
        d = dt.date.fromisoformat(date)
    except ValueError:
        return "no_date_reported", ""
    target_id = "EO:%d%s" % (number, suffix)
    want = re.compile(MON_RX[d.month - 1])
    for start, r in spans:  # an entry the OCR parse already split out carries its own date column
        if r["id"] == target_id:
            m = re.match(r"\s*([A-Z][a-z]{2,4})\.?\s*(\d{1,2})", r["month_day"] or "")
            if m and r["year"] == str(d.year):
                ok = want.match(m.group(1)) and int(m.group(2)) == d.day
                return ("agrees" if ok else "disagrees"), f"{r['year']} {r['month_day']} p.{r['page']}: {r['text'][:150]}"
    suf = {"½": HALF, "": ""}.get(suffix, r"-?" + re.escape(suffix))
    head = re.compile(r"(?<![\d/])" + str(number) + r"\s*" + suf + (r"(?![\d/])" if not suffix else "") + r"\s*(?:[,-]\s*\d{1,4}\s*)*\*?\s*:")
    found = []
    for m in head.finditer(full):
        after = full[m.end():m.end() + 30]
        dm = re.match(r"\s*\*?\s*\(?\s*([A-Z][a-z]{2,4})\.?\s*(\d{1,2})", after)
        if dm:
            found.append((dm.group(1), int(dm.group(2)), full[max(0, m.start() - 5):m.end() + 160]))
    if not found:
        return "silent", ""
    for mon, day, ex in found:
        if want.match(mon) and day == d.day:
            return "agrees", ex
    return "disagrees", found[0][2]


def unnumbered_check(urows, date):
    try:
        d = dt.date.fromisoformat(date)
    except (TypeError, ValueError):
        return []
    out = []
    for r in urows:
        if r["year"] != str(d.year):
            continue
        m = re.match(r"\s*([A-Z][a-z]{2,4})\.?\s*(\d{1,2})", r["date"] or "")
        if m and re.match(MON_RX[d.month - 1], m.group(1)) and int(m.group(2)) == d.day:
            out.append(r)
    return out


def main(results_dir, out_csv):
    full, spans = wpa_text()
    urows = list(csv.DictReader(open(WPA_U, encoding="utf-8")))
    rows = []
    for path in sorted(glob.glob(os.path.join(results_dir, "*.jsonl"))):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                rows.append({"batch": os.path.basename(path), "target_id": "?", "wpa_check": "unreadable_line"})
                continue
            tid = r.get("target_id", "")
            date = (r.get("date") or "").strip()[:10]
            m = re.match(r"EO:(\d+)(.*)$", tid)
            srcs = r.get("sources") or []
            row = {"batch": os.path.basename(path), "target_id": tid, "group": r.get("group", ""), "outcome": r.get("outcome", ""),
                   "date": date, "title_or_subject": (r.get("title_or_subject") or "")[:200], "president": r.get("president", ""),
                   "resolved_to": r.get("resolved_to", ""), "confidence": r.get("confidence", ""),
                   "sources": len(srcs), "official_sources": sum(1 for s in srcs if s.get("kind") == "official_printing"),
                   "verbatim_quotes": sum(1 for s in srcs if s.get("quote") and not s.get("seen_only_in_snippet")),
                   "first_url": srcs[0].get("url", "") if srcs else ""}
            if m:
                verdict, ex = numbered_check(full, spans, int(m.group(1)), m.group(2), date)
                row["wpa_check"], row["wpa_excerpt"] = verdict, ex[:220]
            elif tid.startswith("DATED:"):
                hits = unnumbered_check(urows, date or tid.split(":")[1])
                row["wpa_check"] = f"unnumbered_list_has_{len(hits)}_same_date" if hits else "unnumbered_list_silent"
                row["wpa_excerpt"] = " | ".join(h["summary"][:110] for h in hits[:2])
            else:
                row["wpa_check"], row["wpa_excerpt"] = "not_applicable", ""
            rows.append(row)
    fields = ["batch", "target_id", "group", "outcome", "date", "title_or_subject", "president", "resolved_to", "confidence",
              "sources", "official_sources", "verbatim_quotes", "first_url", "wpa_check", "wpa_excerpt"]
    with open(out_csv, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    import collections
    print(json.dumps({"rows": len(rows), "outcomes": collections.Counter(r.get("outcome", "") for r in rows),
                      "wpa_check": collections.Counter(r["wpa_check"] for r in rows)}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

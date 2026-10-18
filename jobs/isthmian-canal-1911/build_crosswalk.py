"""Rebuild data/ic1911_crosswalk.csv and data/ic1911_wpa_not_in_volume.csv. Not run by job.py.

The volume prints no EO numbers. On 2026-10-17 each presidential order in its contents was matched
by hand to the WPA numbered list (Executive Orders 1-8030, the project's parse of the 1944 WPA/NARA
list) by same date and subject, and the unnumbered ones to Lord's 1943 list of unnumbered orders.
The reviewed matches are MAP and LORD below; this script only copies the list's own date, citations
and wording next to each match so that the job and its tests can check them without the WPA files.

usage: python -I build_crosswalk.py <NUMBERED_ENTRIES.csv> <UNNUMBERED_ENTRIES.csv> <out data dir>
"""

import csv
import hashlib
import json
import pathlib
import re
import sys

# contents seq -> EO ids (reviewed by hand: same date + subject in the WPA numbered list)
MAP = {
    6: ["EO:273", "EO:274"], 11: ["EO:283"], 12: ["EO:289"], 17: ["EO:317A"], 24: ["EO:330"], 25: ["EO:335A"],
    26: ["EO:341B"], 27: ["EO:348C"], 28: ["EO:351"], 30: ["EO:370"], 31: ["EO:373A"], 32: ["EO:377B"],
    33: ["EO:384"], 34: ["EO:391"], 35: ["EO:393"], 36: ["EO:394"], 37: ["EO:412"], 38: ["EO:418"],
    39: ["EO:430"], 40: ["EO:452"], 41: ["EO:474"], 42: ["EO:481"], 44: ["EO:506"], 48: ["EO:527"],
    49: ["EO:571"], 54: ["EO:577½"], 59: ["EO:588"], 60: ["EO:586"], 61: ["EO:587"], 62: ["EO:589"],
    63: ["EO:593"], 64: ["EO:595"], 66: ["EO:600"], 67: ["EO:606"], 68: ["EO:607"], 70: ["EO:615"],
    71: ["EO:647"], 72: ["EO:643"], 73: ["EO:649"], 75: ["EO:663"], 76: ["EO:673"], 77: ["EO:680½"],
    78: ["EO:665"], 79: ["EO:664"], 89: ["EO:725"], 91: ["EO:729"], 92: ["EO:730"], 93: ["EO:731"],
    94: ["EO:732"], 95: ["EO:741"], 96: ["EO:750"], 97: ["EO:752"], 99: ["EO:761"], 102: ["EO:774"],
    103: ["EO:788"], 111: ["EO:928"], 112: ["EO:937"], 113: ["EO:938"], 116: ["EO:944"], 117: ["EO:947"],
    119: ["EO:946"], 120: ["EO:953"], 122: ["EO:966"], 123: ["EO:967"], 125: ["EO:996"], 126: ["EO:997"],
    127: ["EO:1002"], 129: ["EO:1052"], 132: ["EO:1076"], 133: ["EO:1084"], 134: ["EO:1085"], 135: ["EO:1096"],
    136: ["EO:1111"], 138: ["EO:1116"], 139: ["EO:1115"], 141: ["EO:1126"], 142: ["EO:1130"], 143: ["EO:1131"],
    145: ["EO:1140"], 146: ["EO:1141"], 147: ["EO:1142"], 150: ["EO:1153"], 151: ["EO:1158"], 153: ["EO:1184"],
    154: ["EO:1188"], 155: ["EO:1190"], 157: ["EO:1230"], 158: ["EO:1231"], 159: ["EO:1239"], 160: ["EO:1246"],
    161: ["EO:1250"], 163: ["EO:1253"], 165: ["EO:1285"], 166: ["EO:1286"], 167: ["EO:1295"], 169: ["EO:1319"],
    170: ["EO:1320"], 171: ["EO:1321"], 172: ["EO:1345"], 173: ["EO:1348"], 174: ["EO:1351"], 175: ["EO:1352"],
    176: ["EO:1353"], 177: ["EO:1372"]}
# contents seq -> Lord 1943 unnumbered seq (seq 55 is a Secretary of War order 'by direction of the President')
LORD = {2: "1269", 14: "1283", 55: "1297", 65: "1298"}
NOTES = {
    6: "one printed entry holds both orders: the classification (EO 274) and the Schedule A amendment (EO 273)",
    54: "the WPA parse merges EO 577½ into row 577 (OCR '577%')",
    77: "the WPA parse merges EO 680½ into row 680 (OCR '68OV2')",
    172: "the WPA list reads 'Hay 2' with no day-month parse; the date comes from the volume",
}
SHORT = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "June": 6, "July": 7, "Aug": 8, "Sept": 9, "Oct": 10,
         "Nov": 11, "Dec": 12}
FIRST, LAST = "1904-03-08", "1911-06-12"  # the volume's own range
CANAL = re.compile(r"(?i)isthmian|canal\s+zone|panama")
HALF_MARK = re.compile(r"\b[0-9O]{3,4}(?:%|V2|½)\s*:")  # "577%:" and "68OV2 :" start a merged ½ order


def wpa_date(year: str, md: str) -> str:
    p = md.split()
    if year.isdigit() and len(p) == 2 and p[0] in SHORT and p[1].isdigit():
        return "%s-%02d-%02d" % (year, SHORT[p[0]], int(p[1]))
    return year if year.isdigit() else ""


def half_row(rows, iid):
    """The ½ order merged into its whole-numbered row: 'EO:577½' is the text after '577%:'."""
    base = iid[3:-1]
    digits = "".join("[0O]" if c == "0" else c for c in base)
    pat = re.compile(r"\b%s(?:%%|V2|½)\s*:\s*(%s)\.?\s+(\d{1,2})\s+(.*)$" % (digits, "|".join(SHORT)), re.S)
    for r in rows.get("EO:" + base, []):
        m = pat.search(r["text"])
        if m:
            return {"year": r["year"], "month_day": f"{m.group(1)} {m.group(2)}", "citations_joined": "",
                    "text": m.group(3).strip(), "merged_into": "EO:" + base}
    return None


def main(numbered_p, lord_p, out_dir):
    rows = {}
    for r in csv.DictReader(open(numbered_p, encoding="utf-8-sig")):
        rows.setdefault(r["id"], []).append(r)
    lord = {r["seq"]: r for r in csv.DictReader(open(lord_p, encoding="utf-8-sig"))}
    out = []
    for seq in sorted(set(MAP) | set(LORD)):
        for iid in MAP.get(seq, [""]):
            rec = {"seq": seq, "instrument_id": iid, "lord_seq": LORD.get(seq, ""), "wpa_date": "", "wpa_year": "",
                   "wpa_month_day": "", "wpa_citations": "", "wpa_text": "", "lord_date": "", "lord_pairing": "",
                   "lord_page": "", "lord_summary": "", "note": NOTES.get(seq, "")}
            if iid:
                r = half_row(rows, iid) if iid.endswith("½") else (rows.get(iid) or [None])[0]
                if r is None or (not iid.endswith("½") and len(rows[iid]) != 1):
                    raise SystemExit(f"{iid}: not exactly one WPA row")
                rec.update(wpa_date=wpa_date(r["year"], r["month_day"]), wpa_year=r["year"], wpa_month_day=r["month_day"],
                           wpa_citations=r["citations_joined"], wpa_text=re.sub(r"\s+", " ", r["text"])[:240],
                           basis="same date and subject in the WPA numbered list, reviewed by hand 2026-10-17")
            if seq in LORD:
                lr = lord[LORD[seq]]
                rec.update(lord_date=wpa_date(lr["year"], lr["date"]), lord_pairing=lr["pairing"], lord_page=lr["page"],
                           lord_summary=re.sub(r"\s+", " ", lr["summary"])[:240])
                if not iid:
                    rec["basis"] = "same date (or year) and subject in Lord 1943 unnumbered list, reviewed by hand 2026-10-17"
            out.append(rec)
    mapped = {i for v in MAP.values() for i in v}
    missing = []
    for iid, rs in rows.items():
        for r in rs:
            d = wpa_date(r["year"], r["month_day"])
            if iid in mapped or not d or not (FIRST[:4] <= d[:4] <= LAST[:4]):
                continue
            if len(d) == 10 and not (FIRST <= d <= LAST):
                continue
            own = HALF_MARK.split(r["text"])[0]  # a merged ½ order's text is not this order's subject
            if CANAL.search(own):
                missing.append({"instrument_id": iid, "wpa_date": d if len(d) == 10 else "", "wpa_year": r["year"],
                                "wpa_month_day": r["month_day"], "wpa_citations": r["citations_joined"],
                                "wpa_text": re.sub(r"\s+", " ", own)[:240]})
    out_dir = pathlib.Path(out_dir)
    fields = ["seq", "instrument_id", "lord_seq", "wpa_date", "wpa_year", "wpa_month_day", "wpa_citations", "wpa_text",
              "lord_date", "lord_pairing", "lord_page", "lord_summary", "basis", "note"]
    with open(out_dir / "ic1911_crosswalk.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(out)
    with open(out_dir / "ic1911_wpa_not_in_volume.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(missing[0].keys()))
        w.writeheader()
        w.writerows(missing)
    sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
    print(json.dumps({"crosswalk_rows": len(out), "eo_ids": len(mapped), "lord": len(LORD), "wpa_not_in_volume": len(missing),
                      "numbered_entries_sha256": sha(numbered_p), "unnumbered_entries_sha256": sha(lord_p)}, indent=1))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(*sys.argv[1:4])

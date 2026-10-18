"""Split the Office of the Federal Register's 1974 compilations of pre-1936 orders into one text per order.

Each volume is listed in data/PROVENANCE.json. The job reads the committed text layer of the scan
(data/<volume>_pages.jsonl), never the network. For every order it finds the heading
("Executive Order 5550. February 6, 1931") and the closing tag ("[No. 5550]"), keeps the lines
between them, and records which PDF pages and printed pages they came from. It also reads the
volume's Table 2 (list of every order of the administration) and Table 3 (earlier documents the
volume's orders amended or revoked), and compares everything with the census.

Machine leads only: nothing here admits, merges, dates or changes a census identity or a status.
"""

import csv
import hashlib
import json
import pathlib
import re

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
MONTH_NO = {m: i for i, m in enumerate(MONTHS.split("|"), 1)}
SHORT_NO = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "June": 6, "July": 7, "Aug": 8,
            "Sept": 9, "Oct": 10, "Nov": 11, "Dec": 12}

# "Executive Order 5550. February 6, 1931" and "Executive Order 6022 -A . February 10 , 1933"
HEADING = re.compile(
    r"^\s*Executive\s+Order\s+(\d{3,4})(?:\s*-?\s*([A-Z]))?\s*[.,]\s*(%s)\.?\s+(\d{1,2})\s*,\s*(1[89]\d\d)\b" % MONTHS)
# "[No. 5550]", "[No. 5555 ]", "[No. 5855-A]"
CLOSING = re.compile(r"\[\s*No\s*\.?\s*(\d{3,4})(?:\s*-?\s*([A-Z]))?\s*\]")
# Running heads: "Herbert Hoover , 1929-1933 EO 5550" and "EO 5551 Executive Orders" (OCR may use Greek ΕΟ).
RUNNING_HEAD = re.compile(r"^\s*(?:[A-Z][a-z]+(?: [A-Z]\.)? [A-Z][a-z]+ ?, ?1[89]\d\d-1[89]\d\d\s+[EΕ][OΟ]\s|[EΕ][OΟ]\s+\d{3,4}\S*\s+Executive Orders\s*$)")
PRINTED_PAGE = re.compile(r"^\s*(\d{1,4})\s*$")
T2_LINE = re.compile(r"^\s*(\d{3,4})(?:\s*-\s*([A-Z])|([A-Z]))?\s+(Jan|Feb|Mar|Apr|May|June|July|Aug|Sept|Oct|Nov|Dec)\s*\.?\s*(\d{1,2})?\s*(.*)$")
T3_LINE = re.compile(r"^\s*(\d{1,4}(?:\s*-\s*[A-Z]|[A-Z]|\s*½)?)\s*[-–—_.]*\s+((?:Revoked|Amended|Superseded|Modified|Supplemented|See|Suspended|Continued|Terminated)\b.*)$")
EO_REF = re.compile(r"\b(EO|Proc\.?)\s*(\d{3,4}(?:-?[A-Z])?)")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def order_id(number: str, suffix: str | None) -> str:
    return f"EO:{int(number)}{(suffix or '').upper()}"


def load_pages(path: pathlib.Path) -> list[tuple[int, str]]:
    pages = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            pages.append((int(d["page"]), d["text"]))
    return pages


def page_lines(text: str) -> tuple[list[str], str | None]:
    """Body lines of one page, without its running head and printed page number."""
    lines = [l.rstrip() for l in text.split("\n")]
    while lines and not lines[-1].strip():
        lines.pop()
    printed = None
    if lines and PRINTED_PAGE.match(lines[-1]):
        printed = lines.pop().strip()
    first = next((i for i, l in enumerate(lines) if l.strip()), None)
    if first is not None and RUNNING_HEAD.match(lines[first]):
        del lines[first]
    return lines, printed


def body_and_tables(pages):
    """Split the volume at the 'TABLES OF PRESIDENTIAL DOCUMENTS' divider."""
    for i, (_, text) in enumerate(pages):
        head = " ".join(l.strip() for l in text.split("\n") if l.strip())[:60]
        if head.startswith("TABLES OF") and i > 20:
            return pages[:i], pages[i:]
    return pages, []


def find_orders(pages):
    """Return one dict per order heading, with its text lines and where they came from."""
    stream = []  # (pdf_page, printed_page, line)
    for pno, text in pages:
        lines, printed = page_lines(text)
        for l in lines:
            stream.append((pno, printed, l))
    heads = []
    for i, (_, _, l) in enumerate(stream):
        if not re.match(r"^\s*Executive\s+Order\s+\d", l):
            continue
        # OCR often wraps the date: "Executive Order 5635. June" / "2, 1931"
        m = HEADING.match(" ".join(s[2] for s in stream[i:i + 3]))
        if m:
            heads.append((i, m))
    orders = []
    for k, (i, m) in enumerate(heads):
        nxt = heads[k + 1][0] if k + 1 < len(heads) else len(stream)
        iid = order_id(m.group(1), m.group(2))
        end, closing, other_tag = None, "missing", None
        for j in range(i + 1, nxt):
            line = stream[j][2]
            wrapped = "[" in line and "]" not in line.split("[")[-1] and j + 1 < nxt
            for c in CLOSING.finditer(line + (" " + stream[j + 1][2] if wrapped else "")):
                if order_id(c.group(1), c.group(2)) == iid:
                    # "[No. 5634" / "]": the tag ends on the next line
                    end, closing = (j + 1 if wrapped and c.end() > len(line) else j), "match"
                    break
                other_tag = other_tag or order_id(c.group(1), c.group(2))
            if end is not None:
                break
        if end is None:
            end = nxt - 1
            if other_tag:
                closing = "other_number:" + other_tag
        span = stream[i:end + 1]
        pdf_pages = sorted({s[0] for s in span})
        printed = [s[1] for s in span if s[1]]
        orders.append({
            "instrument_id": iid,
            "number": int(m.group(1)),
            "suffix": (m.group(2) or "").upper(),
            "date": "%s-%02d-%02d" % (m.group(5), MONTH_NO[m.group(3)], int(m.group(4))),
            "heading": l_clean(stream[i][2]),
            "lines": [s[2] for s in span],
            "pdf_pages": (pdf_pages[0], pdf_pages[-1]),
            "printed_pages": (printed[0], printed[-1]) if printed else ("", ""),
            "closing_tag": closing,
            "confidence": "high" if closing == "match" else "medium",
        })
    return orders


def l_clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def parse_table2(table_pages, lo: int, hi: int):
    """Table 2: every order of the administration. Year from the year lines; subject only when on the same line."""
    rows, year = {}, None
    for pno, text in table_pages:
        if "Table 2" not in text:
            continue
        for l in text.split("\n"):
            s = l.strip()
            if re.fullmatch(r"1[89]\d\d", s):
                year = int(s)
                continue
            m = T2_LINE.match(l)
            if not m or not (lo <= int(m.group(1)) <= hi):
                continue
            iid = order_id(m.group(1), m.group(2) or m.group(3))
            rows.setdefault(iid, {
                "instrument_id": iid, "month": SHORT_NO[m.group(4)], "day": int(m.group(5)) if m.group(5) else "",
                "year_from_table": year or "", "subject_same_line": l_clean(m.group(6)), "pdf_page": pno})
    return rows


def parse_table3(table_pages):
    """Table 3: earlier documents affected by this volume's documents. Only lines that carry both the
    document number and the comment are paired; OCR often splits the two columns."""
    rows, unpaired, section = [], 0, None
    started = False
    for pno, text in table_pages:
        if "Table 3" in text:
            started = True
        if not started:
            continue
        for l in text.split("\n"):
            s = l.strip()
            if re.match(r"^PROCLAMATIONS", s):
                section = "proclamation"
                continue
            if re.match(r"^EXECUTIVE ORDERS", s):
                section = "executive_order"
                continue
            if re.match(r"^[A-Z][A-Z ,'-]{6,}$", s) and "TABLE" not in s and "DOCUMENTS" not in s:
                section = "other:" + s.lower()
                continue
            m = T3_LINE.match(l)
            if m and section:
                comment = l_clean(m.group(2))
                rows.append({
                    "section": section, "affected": re.sub(r"-(?=[A-Z]$)", "", l_clean(m.group(1)).replace(" ", "")),
                    "comment": comment, "action": comment.split()[0].lower(),
                    "by": " ".join(f"{a.rstrip('.')} {n}" for a, n in EO_REF.findall(comment)),
                    "pdf_page": pno})
            elif re.fullmatch(r"\d{1,4}\s*[-–—_.]*", s):
                unpaired += 1
    return rows, unpaired


def load_census(path: pathlib.Path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return {r["id"].upper(): r for r in csv.DictReader(fh)}


def census_range(census, lo, hi):
    out = []
    for cid in census:
        m = re.fullmatch(r"EO:(\d+)([A-Z])?", cid)
        if m and lo <= int(m.group(1)) <= hi:
            out.append(cid)
    return out


def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def run_volume(vol, repo: pathlib.Path, job_dir: pathlib.Path, out: pathlib.Path, census, readiness):
    key = vol["key"]
    lo, hi = vol["eo_range"]
    text_path = job_dir / vol["text"]
    text_sha = sha256_bytes(text_path.read_bytes())
    if text_sha != vol["text_sha256"]:
        raise SystemExit(f"{vol['text']}: sha256 {text_sha} does not match PROVENANCE.json")
    pdf = repo / vol["pdf"]
    if not pdf.exists():
        pdf_check = "pdf_not_checked_out"
    elif pdf.read_bytes()[:40].startswith(b"version https://git-lfs"):
        pdf_check = "pdf_is_lfs_pointer_text_layer_hash_verified"
    else:
        pdf_check = "match" if sha256_bytes(pdf.read_bytes()) == vol["pdf_sha256"] else "MISMATCH"
        if pdf_check == "MISMATCH":
            raise SystemExit(f"{vol['pdf']}: sha256 does not match PROVENANCE.json")

    pages = load_pages(text_path)
    body, tables = body_and_tables(pages)
    orders = find_orders(body)
    t2 = parse_table2(tables, *vol["table2_range"])
    t3, t3_unpaired = parse_table3(tables)

    # duplicates and order of headings
    seen, dups = set(), []
    for o in orders:
        if o["instrument_id"] in seen:
            dups.append(o["instrument_id"])
        seen.add(o["instrument_id"])
    orders = [o for i, o in enumerate(orders) if o["instrument_id"] not in {x["instrument_id"] for x in orders[:i]}]
    printed_numbers = {o["number"] for o in orders if not o["suffix"]}
    missing_plain = [n for n in range(lo, hi + 1) if n not in printed_numbers]

    texts = out / "texts"
    texts.mkdir(parents=True, exist_ok=True)
    in_range = census_range(census, lo, hi)
    order_rows, fragments, leads = [], [], []
    for o in orders:
        iid = o["instrument_id"]
        body_text = "\n".join(o["lines"]).strip() + "\n"
        body_sha = sha256_bytes(body_text.encode("utf-8"))
        fname = f"texts/{iid.replace(':', '_')}.txt"
        pp = "PDF pages %d-%d" % o["pdf_pages"]
        printed = "printed pages %s-%s" % o["printed_pages"] if o["printed_pages"][0] else "printed page unread"
        header = (f"# {iid}: {o['heading']}\n"
                  f"# Source: {vol['title']} ({vol['published']}); {vol['digitized_by']}\n"
                  f"# PDF: {vol['pdf']} sha256 {vol['pdf_sha256']}\n"
                  f"# {pp}; {printed}; closing tag {o['closing_tag']}; confidence {o['confidence']}\n"
                  f"# Text: OCR text layer of the scan ({vol['extractor']}), running heads and page numbers removed. "
                  f"Not human-verified. Body sha256 {body_sha}\n\n")
        (out / fname).write_text(header + body_text, encoding="utf-8", newline="\n")
        c = census.get(iid)
        de = (c or {}).get("date_effective", "").strip()
        if not c:
            census_state = "NOT_IN_CENSUS"
        elif not de:
            census_state = "census_date_blank"
        elif len(de) == 4:
            census_state = "census_year_only" if de == o["date"][:4] else "YEAR_CONFLICT"
        else:
            census_state = "census_exact_date" if de == o["date"] else "DATE_CONFLICT"
        t2row = t2.get(iid, {})
        rd = readiness.get(iid, {})
        row = {
            "instrument_id": iid, "date": o["date"], "subject_table2": t2row.get("subject_same_line", ""),
            "pdf_pages": "%d-%d" % o["pdf_pages"], "printed_pages": "%s-%s" % o["printed_pages"],
            "closing_tag": o["closing_tag"], "confidence": o["confidence"], "census": census_state,
            "census_date_effective": de, "provisional_status": rd.get("provisional_status", ""),
            "original_text_step_before": rd.get("step_original_text", ""),
            "text_path": fname, "text_sha256": body_sha, "chars": len(body_text)}
        order_rows.append(row)
        page_or_item = f"{vol['short']}, {printed}, {pp}"
        if c:
            fragments.append({
                "instrument_id": iid, "kind": "original_representation", "produced_by": "ofr-compilations",
                "confidence_note": (f"Machine location lead, confidence {o['confidence']}. "
                                    + ("Order heading and its closing tag [No. ...] both found; "
                                       if o["confidence"] == "high" else "Order heading found, closing tag not matched; ")
                                    + "official Office of the Federal Register compilation (GPO 1974), Google scan via HathiTrust; "
                                      "text is the scan's OCR layer. Identity, boundaries and wording are NOT human-verified; "
                                      "this is not a legal conclusion."),
                "data": {"url": vol["handle_url"], "sha256": vol["pdf_sha256"], "page_or_item": page_or_item,
                         "route": "official/ofr_compilation_1974", "location_confidence": o["confidence"],
                         "location_verified": False, "needs_page_check": o["confidence"] != "high",
                         "signing_date": o["date"], "title": t2row.get("subject_same_line", ""),
                         "text_path": fname, "text_sha256": body_sha,
                         "source_id": f"ofr-compilations:{iid}:{vol['pdf_sha256'][:12]}"},
                "sources": [{"url": vol["handle_url"], "sha256": vol["pdf_sha256"], "page_or_item": page_or_item}]})
        if census_state in ("NOT_IN_CENSUS", "census_date_blank", "YEAR_CONFLICT", "DATE_CONFLICT"):
            leads.append({"instrument_id": iid, "lead": census_state, "date_in_volume": o["date"],
                          "census_date_effective": de, "evidence": f"{vol['short']}, {printed}, {pp}",
                          "text_path": fname})
    # Table 2 orders outside the printed range (the other volume) that the census lacks
    for iid, r in sorted(t2.items()):
        n = int(re.match(r"EO:(\d+)", iid).group(1))
        if not (lo <= n <= hi) and iid not in census:
            leads.append({"instrument_id": iid, "lead": "NOT_IN_CENSUS_listed_in_table2_only",
                          "date_in_volume": "%s-%02d-%02d" % (r["year_from_table"], r["month"], r["day"]) if r["year_from_table"] else "",
                          "census_date_effective": "", "evidence": f"{vol['short']}, Table 2, PDF page {r['pdf_page']}",
                          "text_path": ""})
    found_ids = {o["instrument_id"] for o in orders}
    for cid in sorted(set(in_range) - found_ids):
        leads.append({"instrument_id": cid, "lead": "IN_CENSUS_NOT_FOUND_IN_VOLUME", "date_in_volume": "",
                      "census_date_effective": census[cid].get("date_effective", ""), "evidence": vol["short"], "text_path": ""})

    # Table 2 vs headings: a check on both parsers
    t2_compared = [o for o in orders if t2.get(o["instrument_id"], {}).get("day")]
    t2_agree = sum(1 for o in t2_compared
                   if (t2[o["instrument_id"]]["month"], t2[o["instrument_id"]]["day"]) == (int(o["date"][5:7]), int(o["date"][8:10])))
    t3_rows = []
    for r in t3:
        aid = ("EO:" if r["section"] == "executive_order" else "Proc:") + r["affected"]
        r2 = dict(r, affected_id=aid, in_census=("yes" if aid.upper() in census else "no") if aid.startswith("EO:") else "",
                  provisional_status=readiness.get(aid, {}).get("provisional_status", ""))
        t3_rows.append(r2)

    write_csv(out / f"{key}_ORDERS.csv", order_rows, list(order_rows[0].keys()) if order_rows else ["instrument_id"])
    write_csv(out / f"{key}_TABLE2.csv", sorted(t2.values(), key=lambda r: (int(re.match(r"EO:(\d+)", r["instrument_id"]).group(1)), r["instrument_id"])),
              ["instrument_id", "year_from_table", "month", "day", "subject_same_line", "pdf_page"])
    write_csv(out / f"{key}_AFFECTED_DOCUMENTS.csv", t3_rows,
              ["section", "affected_id", "action", "comment", "by", "in_census", "provisional_status", "pdf_page"])
    with open(out / "FRAGMENTS.jsonl", "a", encoding="utf-8", newline="\n") as fh:
        for f in fragments:
            fh.write(json.dumps(f, ensure_ascii=False, sort_keys=True) + "\n")
    lead_fields = ["instrument_id", "lead", "date_in_volume", "census_date_effective", "evidence", "text_path"]
    lead_path = out / "CENSUS_LEADS.csv"
    new = not lead_path.exists()
    with open(lead_path, "a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["volume"] + lead_fields)
        if new:
            w.writeheader()
        for r in leads:
            w.writerow(dict(r, volume=key))

    decided = [r for r in order_rows if r["provisional_status"]]
    lead_count = {}
    for r in leads:
        lead_count[r["lead"]] = lead_count.get(r["lead"], 0) + 1
    return {
        "volume": key, "title": vol["title"], "pdf_check": pdf_check, "text_sha256": text_sha,
        "orders_printed": len(orders), "printed_range": [lo, hi],
        "plain_numbers_in_range_without_heading": missing_plain,
        "lettered_orders": sorted(o["instrument_id"] for o in orders if o["suffix"]),
        "duplicate_headings": dups,
        "confidence": {c: sum(1 for o in orders if o["confidence"] == c) for c in ("high", "medium")},
        "census_ids_in_range": len(in_range),
        "census_ids_in_range_with_text": len(set(in_range) & found_ids),
        "census_state": {s: sum(1 for r in order_rows if r["census"] == s) for s in sorted({r["census"] for r in order_rows})},
        "census_leads": lead_count,
        "decided_orders_with_text": len(decided),
        "decided_orders_original_text_step_open": sum(1 for r in decided if r["original_text_step_before"] != "done"),
        "fragments": len(fragments),
        "table2_entries": len(t2), "table2_day_read_for_printed_orders": len(t2_compared),
        "table2_month_day_agrees_with_heading": t2_agree,
        "table3_paired_lines": len(t3_rows), "table3_unpaired_number_lines": t3_unpaired,
        "table3_executive_order_lines": sum(1 for r in t3_rows if r["section"] == "executive_order"),
    }


def run(repo_root, job_dir, out_dir):
    repo, job_dir, out = pathlib.Path(repo_root), pathlib.Path(job_dir), pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for stale in ("FRAGMENTS.jsonl", "CENSUS_LEADS.csv"):
        (out / stale).unlink(missing_ok=True)
    prov = json.loads((job_dir / "data" / "PROVENANCE.json").read_text(encoding="utf-8"))
    census = load_census(repo / prov["census"])
    readiness = {}
    rp = repo / prov["readiness"]
    if rp.exists():
        with open(rp, encoding="utf-8-sig", newline="") as fh:
            readiness = {r["instrument_id"].upper(): r for r in csv.DictReader(fh)}
    summary = {"leads_only": "Nothing is admitted, merged, dated or changed in the census or in any status.",
               "census": prov["census"], "readiness_read": rp.exists(), "volumes": []}
    for vol in prov["volumes"]:
        summary["volumes"].append(run_volume(vol, repo, job_dir, out, census, readiness))
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary

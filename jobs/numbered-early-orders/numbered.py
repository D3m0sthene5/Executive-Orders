"""Numbered early orders: find the printed texts of the undecided orders numbered 1-5075 (1862-1929).

3,324 numbered orders from before the Federal Register have nothing on file (data/TARGETS.csv). Many were
printed in government books: the War Department reservation books, the General Land Office reports, the
Indian-reservation and Canal Zone compilations, the Civil Service Commission's annual reports, the
wartime Official U.S. Bulletin, Kappler's Indian Affairs. This job reads every page of each such book and
looks for the target orders in two ways:

* by number: "Executive Order No. 1234", "E. O. 1234-A";
* by date and subject: the order's date as printed ("June 3, 1922", "3d day of June, 1922") with at least
  two of the WPA 1944 summary's distinctive words nearby (one very rare word is enough), because books
  printed before about 1912 do not print the numbers at all.

A hit is cut from the page as an exact slice of the OCR and saved under texts/ with the book, image,
printed page, line span and hashes, and declared in FRAGMENTS.jsonl / SOURCES.jsonl in the same shape as
jobs/wikisource-texts so claim-kit's loader finds it. Every text is a government printed copy, graded
`government_printed_copy` (a compiled transcription), acceptable_as_original=false. A number mention
preceded by "amending", "revoking" and the like is another order citing the target and is listed in
MENTIONS.csv, never saved as the target's text.

Books first come from what the project already holds (early-orders-hunt's fetched books, the 1912
Indian-reservation and 1911 Isthmian Canal compilations, Richardson VI/VII/IX); then from data/BOOKS.json,
one Internet Archive item at a time, with the Archive's sha1 checked. Fetching reuses early-orders-hunt's
code by import, unchanged.

Nothing here admits an order, decides a status or authenticates anything. A slice must be read against the
scan before use. No model tokens are spent.

Environment: NEO_MAX_REQUESTS (default 200), NEO_MAX_BOOKS (default 40 new books per run), NEO_BOOKS
(comma-separated keys to restrict new books to), NEO_OFFLINE=1, JOB_CACHE_DIR.
"""
from __future__ import annotations

import collections
import csv
import gzip
import hashlib
import json
import os
import pathlib
import re
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "early-orders-hunt"))
import hunt  # noqa: E402  (unchanged; fetch, checksum, page-map and date helpers)

PRODUCER = "numbered-early-orders"
GRADE = "government_printed_copy"
FLAGS = "compiled_transcription derivative government printed copy, not an original"

MONTH_ALT = (r"(January|Jan|February|Feb|Febuary|March|Mar|April|Apr|May|June|Jun|July|Jul|August|Aug|"
             r"September|Sept|Sep|October|Oct|November|Nov|December|Dec)")
DATE_MDY = re.compile(r"\b" + MONTH_ALT + r"\.?\s+(\d{1,2})(?:st|nd|rd|th|d)?\s*[,.]?\s*(?:A\.\s*D\.\s*)?(1[89]\d\d)\b")
DATE_DMY = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th|d)?\s+(?:day\s+of\s+)?" + MONTH_ALT +
                      r"\.?\s*,?\s*(?:A\.\s*D\.\s*)?(1[89]\d\d)\b")
NUMBER_RE = re.compile(r"(?i)\b(?:executive\s+order|E\.\s*O\.)\s*(?:No\s*\.?|number|numbered)?\s*\[?\s*"
                       r"(\d{1,4})(?:\s*-\s*([A-Z])(?![A-Za-z])|([A-Z])(?![A-Za-z])|\s*(½|1/2))?\]?")
PAREN_NO = re.compile(r"\(\s*No\s*[.,]?\s*(\d{1,4})(?:\s*-?\s*([A-Z])|\s*(½|1/2))?\s*\)")
# Another order citing the target: "amending Executive order No. 1234", "under the Executive order of June
# 3, 1922". ("amended by Executive order No. 1234" names the target as the actor and is kept.)
CITED_CUE = re.compile(r"(?i)\b(amending|revoking|rescinding|superseding|modifying|vacating|extending|suspending|"
                       r"continuing|in\s+lieu\s+of|under\s+(?:the\s+)?(?:provisions|authority|terms)|pursuant\s+to|"
                       r"see|cited\s+in|as\s+amended)\b[^.;:]{0,60}$")
# Words too common in these summaries to identify an order on their own (on top of the hunt's STOP list).
GENERIC = set("""national forest forests withdrawn withdrawal withdrawals restored restoration entry settlement
appointment appointed eligible regard service rules rule civil classified position positions clerk clerks
amended amending revoked revoking established establishing transferred transfer purposes government office
offices district districts administrative site sites station stations ranger administration public
lighthouse lighthouses reservations described lands island islands river rivers creek without with
regulations regulation further permitted permit authorized authorizing provided provide providing modified
modifying placed under jurisdiction excluded diminished enlarged created creating extended extending
temporary temporarily pending legislation legislative partly portion portions those these them they
there thereof herein hereby following required requirements require same into upon also than made other
promotion reinstatement examination examinations postmaster postmasters fourth class""".split())


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


# ----------------------------------------------------------------------------- targets

def norm_suffix(s):
    s = (s or "").strip()
    if s in ("½", "1/2"):
        return "half"
    return s.upper()


def parse_month_day(year, md):
    m = re.match(r"\s*([A-Za-z]+)\.?\s*(\d{1,2})", md or "")
    if not m or not re.fullmatch(r"1[89]\d\d", year or ""):
        return None
    mo = hunt.MONTH_NO.get(m.group(1).lower()) or hunt.MONTH_NO.get(m.group(1).lower()[:3])
    d = int(m.group(2))
    if not mo or not 1 <= d <= 31:
        return None
    return f"{year}-{mo:02d}-{d:02d}"


NOT_NAMES = set(hunt.MONTHS) | {"sept", "proc", "dept", "sec'y", "secy", "exec", "gov't", "govt", "terr", "certain",
                                 "president", "congress", "secretary", "executive", "order", "orders", "rules", "service"}


def split_joined(lw, vocab):
    """The WPA list's OCR often runs two words together ("restrictionagainst", repeatedly). Split a long word
    into two words that are each more common in the summaries than the joined form, the most balanced
    split first."""
    if vocab is None or len(lw) < 10:
        return [lw]
    best = None
    n = vocab.get(lw, 0)
    for i in range(4, len(lw) - 3):
        a, b = lw[:i], lw[i:]
        if min(vocab.get(a, 0), vocab.get(b, 0)) > max(n, 1):
            if best is None or min(len(a), len(b)) > min(len(best[0]), len(best[1])):
                best = (a, b)
    return list(best) if best else [lw]


def tokens(text, vocab=None):
    """Distinct summary words, each with whether it is a name (capitalised mid-sentence, not an abbreviation
    or a month). Names carry the identification; the other words only support it."""
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text or "")
    text = re.sub(r"\b\d{4}\s*CSR\s*\d+\b|\bCSR\b|\bCSA\b", " ", text)
    out, seen = [], set()
    for m in re.finditer(r"[A-Za-z][A-Za-z'\-]{3,}", text):
        w = m.group(0)
        abbrev = text[m.end():m.end() + 1] == "." and len(w) <= 5
        for k, lw in enumerate(split_joined(w.lower().strip("'-"), vocab)):
            if len(lw) < 4 or lw in hunt.STOP or lw in GENERIC or lw in seen:
                continue
            name = k == 0 and w[0].isupper() and m.start() > 0 and not abbrev and lw not in NOT_NAMES
            seen.add(lw)
            out.append((lw, name))
    return out


def load_targets(job_dir):
    """{iid: {"instrument_id", "number", "suffix", "entries": [{date, summary, ...}]}} plus df of words."""
    targets = {}
    with open(job_dir / "data" / "TARGETS.csv", encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            t = targets.setdefault(r["instrument_id"], {
                "instrument_id": r["instrument_id"], "order_number": r["order_number"], "number": int(r["number"]),
                "suffix": norm_suffix(r["suffix"]), "entries": []})
            if int(r["wpa_rows"] or 0):
                t["entries"].append({"date": parse_month_day(r["year"], r["month_day"]), "year": r["year"],
                                     "month_day": r["month_day"], "summary": r["summary"],
                                     "family_hint": r["family_hint"], "citations": r["citations"]})
    vocab = collections.Counter()
    for t in targets.values():
        for e in t["entries"]:
            vocab.update(w.lower() for w in re.findall(r"[A-Za-z]{3,}", re.sub(r"([a-z])([A-Z])", r"\1 \2", e["summary"])))
    for t in targets.values():
        for e in t["entries"]:
            e["words"] = tokens(e["summary"], vocab)
    df = collections.Counter()
    for t in targets.values():
        for w in set(w for e in t["entries"] for w, _ in e["words"]):
            df[w] += 1
    for t in targets.values():
        for e in t["entries"]:
            e["keywords"] = [w for w, _ in e["words"] if df[w] <= 25]
            e["names"] = set(w for w, name in e["words"] if name and df[w] <= 25)
            e["df"] = {w: df[w] for w in e["keywords"]}
    return targets


# ----------------------------------------------------------------------------- books

def held_books(repo):
    """The books the project already holds as page text, with their source URL and byte hash."""
    books = []
    hb = repo / "jobs" / "early-orders-hunt" / "output" / "books"
    for meta_path in sorted(hb.glob("*.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        pages_path = hb / f"{meta_path.stem}_pages.jsonl.gz"
        if not pages_path.is_file():
            continue
        cust = meta.get("custody") or {}
        if meta.get("status") == "held_in_repo":
            continue  # Richardson VI/VII/IX: read below from richardson-volumes, their source
        books.append({"key": meta["book_key"], "series": meta["book_key"].split("_")[0], "label": meta.get("label") or meta["book_key"],
                      "held": True, "path": pages_path, "format": "hunt_gz",
                      "url": cust.get("page_text_url"), "sha256": cust.get("page_text_sha256"),
                      "item_url": cust.get("item_url"), "archival_id": "ia:" + str(meta.get("ia_identifier")),
                      "via": "jobs/early-orders-hunt/output/books/" + meta_path.name})
    for job, prov_key in (("indian-reservations-1912", "volumes"), ("isthmian-canal-1911", "volume"),
                          ("richardson-volumes", "volumes")):
        prov = json.loads((repo / "jobs" / job / "data" / "PROVENANCE.json").read_text(encoding="utf-8"))
        vols = prov[prov_key] if isinstance(prov.get(prov_key), list) else [prov.get("volume") or prov]
        for v in vols:
            if not v.get("text"):
                continue
            books.append({"key": v["key"], "series": {"IR1912": "IR", "IC1911": "IC"}.get(v["key"], "RICH"),
                          "label": v.get("short") or v.get("title"), "held": True,
                          "path": repo / "jobs" / job / v["text"], "format": "page_jsonl",
                          "url": v.get("handle_url"), "sha256": v.get("pdf_sha256"), "item_url": v.get("handle_url"),
                          "archival_id": v.get("handle_url"), "via": f"jobs/{job}/data/PROVENANCE.json"})
    return books


def read_pages(book):
    """[(image, printed_or_None, text)]"""
    path = book["path"]
    opener = gzip.open if str(path).endswith(".gz") else open
    pages = []
    with opener(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            img = int(d.get("image") or d.get("page"))
            pages.append((img, d.get("printed"), d.get("text") or ""))
    return pages


# ----------------------------------------------------------------------------- matching

def page_dates(text):
    out = []
    for m in DATE_MDY.finditer(text):
        mo = hunt.MONTH_NO.get(m.group(1).lower()[:4].rstrip(".")) or hunt.MONTH_NO.get(m.group(1).lower()[:3])
        if m.group(1).lower() == "febuary":
            mo = 2
        d = int(m.group(2))
        if mo and 1 <= d <= 31:
            out.append((f"{m.group(3)}-{mo:02d}-{d:02d}", m.start(), m.end()))
    for m in DATE_DMY.finditer(text):
        mo = hunt.MONTH_NO.get(m.group(2).lower()[:4]) or hunt.MONTH_NO.get(m.group(2).lower()[:3])
        d = int(m.group(1))
        if mo and 1 <= d <= 31:
            out.append((f"{m.group(3)}-{mo:02d}-{d:02d}", m.start(), m.end()))
    return out


def page_numbers(text):
    out = []
    for m in NUMBER_RE.finditer(text):
        suffix = norm_suffix(m.group(2) or m.group(3) or m.group(4) or "")
        out.append((int(m.group(1)), suffix, m.start(), m.end()))
    # "Executive order of November 30, 1915 (No. 2275)": the War Department books' form.
    for m in PAREN_NO.finditer(text):
        if re.search(r"(?i)executive\s+orders?\b", text[max(0, m.start() - 160):m.start()]):
            out.append((int(m.group(1)), norm_suffix(m.group(2) or m.group(3) or ""), m.start(), m.end()))
    return out


def kw_hits(low, keywords, lo, hi, common=frozenset()):
    """[(word, position)] of whole-word hits in low[lo:hi], skipping words common in this book."""
    lo = max(0, lo)
    seg = low[lo:hi]
    out = []
    for k in keywords:
        if k in common:
            continue
        m = re.search(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])", seg)
        if m:
            out.append((k, lo + m.start()))
    return out


def accept_words(hits, entry, book_freq):
    """At least two summary words, one of them a name; or one rare long name (in at most three target
    summaries and on at most 0.5% of this book's pages)."""
    words = [h for h, _ in hits]
    names = [w for w in words if w in entry["names"]]
    if len(words) >= 2 and names:
        return True
    # Orders without a name (trust-period extensions, rule changes): three summary words, each uncommon in
    # this book, around the exact date.
    if len([w for w in words if len(w) >= 5 and book_freq.get(w, 0) <= 0.01]) >= 3:
        return True
    return any(entry["df"].get(w, 99) <= 3 and len(w) >= 6 and book_freq.get(w, 0) <= 0.005 for w in names)


def line_of(text, pos):
    return text.count("\n", 0, pos)


def excerpt(text, positions, max_lines=70):
    lines = text.split("\n")
    lo = min(line_of(text, p) for p in positions)
    hi = max(line_of(text, p) for p in positions)
    start, end = max(0, lo - 3), min(len(lines) - 1, hi + 6)
    if end - start + 1 > max_lines:
        end = start + max_lines - 1
    return "\n".join(lines[start:end + 1]), start, end


def book_word_freq(pages):
    """Share of this book's pages each word appears on. Words on more than 3% are common here."""
    n = 0
    c = collections.Counter()
    for _, _, text in pages:
        if text:
            n += 1
            c.update(set(re.findall(r"[a-z][a-z'\-]{3,}", text.lower())))
    freq = {w: v / max(n, 1) for w, v in c.items()}
    return freq, frozenset(w for w, f in freq.items() if f > 0.03)


def book_splitter(freq):
    """A summary word absent from this book but made of two words the book uses ("restrictionagainst") is
    read as those two words."""
    memo = {}

    def expand(keywords):
        out = []
        for k in keywords:
            if k not in memo:
                parts = [k]
                if len(k) >= 9 and not freq.get(k):
                    best = None
                    for i in range(4, len(k) - 2):
                        a, b = k[:i], k[i:]
                        if freq.get(a) and freq.get(b) and (best is None or min(len(a), len(b)) > min(map(len, best))):
                            best = (a, b)
                    parts = [p for p in (best or (k,)) if p not in hunt.STOP and p not in GENERIC]
                memo[k] = parts
            out.extend(p for p in memo[k] if p not in out)
        return out
    return expand


def match_book(book, pages, targets, by_date, by_number):
    """The best hit per target order in this book, and the number mentions that are only citations."""
    freq, common = book_word_freq(pages)
    expand = book_splitter(freq)
    found = {}
    mentions = []

    def mention(iid, img, printed, text, s, e, cited, date_near, hits):
        mentions.append({"book_key": book["key"], "image": img, "printed_page": printed, "instrument_id": iid,
                         "number_text": text[s:e], "cited_cue": cited, "date_near": date_near,
                         "keyword_hits": "|".join(h for h, _ in hits),
                         "context": re.sub(r"\s+", " ", text[max(0, s - 100):e + 100])})

    for img, printed, text in pages:
        if not text:
            continue
        low = text.lower()
        nums = page_numbers(text)
        dates = page_dates(text)
        cand = []
        for date, s, e in dates:
            for iid, entry in by_date.get(date, ()):
                hits = kw_hits(low, expand(entry["keywords"]), s - 1200, e + 1800, common)
                if not accept_words(hits, entry, freq):
                    continue
                if CITED_CUE.search(text[max(0, s - 120):s]):
                    mention(iid, img, printed, text, s, e, True, True, hits)
                    continue
                cand.append((iid, {"how": "date_and_subject", "date": date, "anchor": [s, e],
                                   "keyword_hits": [h for h, _ in hits], "positions": [s] + [p for _, p in hits],
                                   "score": 3 + min(len(hits), 4)}))
        for n, suffix, s, e in nums:
            for iid in by_number.get((n, suffix), ()):
                t = targets[iid]
                cited = bool(CITED_CUE.search(text[max(0, s - 120):s]))
                date_near, hits = None, []
                for entry in t["entries"]:
                    for d, ds, de in dates:
                        if d == entry["date"] and abs(ds - s) < 1500:
                            date_near = (d, ds)
                    h = kw_hits(low, expand(entry["keywords"]), s - 600, e + 1800, common)
                    if len(h) > len(hits) and (any(w in entry["names"] for w, _ in h)):
                        hits = h
                if cited or not (date_near or hits):
                    mention(iid, img, printed, text, s, e, cited, bool(date_near), hits)
                    continue
                how = "number_date_subject" if date_near and hits else ("number_and_date" if date_near else "number_and_subject")
                pos = [s] + ([date_near[1]] if date_near else []) + [p for _, p in hits]
                cand.append((iid, {"how": how, "date": date_near[0] if date_near else None, "anchor": [s, e],
                                   "keyword_hits": [h for h, _ in hits], "positions": pos,
                                   "score": 6 + (2 if date_near else 0) + min(len(hits), 4)}))
        for iid, hit in cand:
            hit.update(image=img, printed_page=printed)
            prev = found.get(iid)
            if prev is None or hit["score"] > prev["score"]:
                hit["_text"] = text
                found[iid] = hit
    # One printed passage claimed by several orders of the same date: keep the orders with the most words;
    # if they tie, all are kept and marked shared (the reviewer decides which entry is which).
    by_passage = collections.defaultdict(list)
    for iid, hit in found.items():
        if hit["how"] == "date_and_subject":
            by_passage[(hit["image"], hit["anchor"][0])].append(iid)
    for ids in by_passage.values():
        if len(ids) < 2:
            continue
        top = max(len(found[i]["keyword_hits"]) for i in ids)
        keep = [i for i in ids if len(found[i]["keyword_hits"]) == top]
        for i in ids:
            if i not in keep:
                del found[i]
            elif len(keep) > 1:
                found[i]["shared_with"] = [k for k in keep if k != i]
    return found, mentions


# ----------------------------------------------------------------------------- saving

def safe_id(iid):
    return iid.replace(":", "_").replace("½", "half").replace("/", "_")


def save_text(out, book, iid, target, hit, retrieved):
    text = hit.pop("_text")
    slice_, l0, l1 = excerpt(text, hit["positions"])
    entry = next((e for e in target["entries"] if e["date"] == hit.get("date")), target["entries"][0] if target["entries"] else {})
    name = f"{safe_id(iid)}__{book['key']}_i{hit['image']}.txt"
    page_desc = f"scanned image {hit['image']}" + (f", printed page {hit['printed_page']}" if hit.get("printed_page") not in (None, "") else "")
    header = [
        f"# order: {iid}  (WPA 1944: {entry.get('year', '')} {entry.get('month_day', '')})",
        "# WPA summary: " + re.sub(r"\s+", " ", entry.get("summary", ""))[:400],
        f"# book: {book['label']}",
        f"# {page_desc}; page lines {l0 + 1}-{l1 + 1}",
        f"# source: {book['url']}  sha256 {book['sha256']}",
        f"# found by: {hit['how']}; date {hit.get('date') or '-'}; words {'|'.join(hit['keyword_hits']) or '-'}",
        "# Government printed copy (OCR of a compilation or report), not the signed original. A lead for the",
        "# original_text step: read it against the scan before use. Exact slice of the page OCR follows.",
        "----- EXACT SLICE -----",
    ]
    body = ("\n".join(header) + "\n" + slice_ + "\n").encode("utf-8")
    (out / "texts" / name).write_bytes(body)
    page_or_item = f"{book['label']}; {page_desc}; lines {l0 + 1}-{l1 + 1}"
    source = {"url": book["url"], "sha256": book["sha256"], "archival_id": book["archival_id"], "page_or_item": page_or_item}
    data = {"acceptable_as_original": False, "grade": GRADE, "representation_type": "government_printed_copy",
            "flags": FLAGS, "location_verified": False, "needs_page_check": True, **source,
            "book_key": book["key"], "book_item_url": book.get("item_url"), "image": hit["image"],
            "printed_page": hit.get("printed_page"), "line_span": [l0 + 1, l1 + 1], "match": hit["how"],
            "match_date": hit.get("date"), "keyword_hits": hit["keyword_hits"],
            "passage_shared_with": hit.get("shared_with") or [],
            "text_path": "texts/" + name, "text_sha256": sha256_bytes(body),
            "source_id": f"{PRODUCER}:{iid}:{book['key']}:{hit['image']}"}
    frag = {"kind": "original_representation", "instrument_id": iid, "produced_by": PRODUCER,
            "acceptable_as_original": False, "grade": GRADE, "representation_type": "government_printed_copy",
            "confidence_note": "Government printed copy (compiled_transcription), found by " + hit["how"] +
                               "; not an original, not authenticated, no legal conclusion. Read against the scan.",
            "data": data, "sources": [source]}
    src = {"instrument_ids": [iid], "acceptable_as_original": False, "grade": GRADE,
           "representation_type": "government_printed_copy", "flags": FLAGS, **source,
           "text_path": data["text_path"], "text_sha256": data["text_sha256"], "retrieved_utc": retrieved,
           "book_key": book["key"], "image": hit["image"], "printed_page": hit.get("printed_page"),
           "match": hit["how"], "source_id": data["source_id"],
           "notes": "OCR slice of a government printed copy; not an original. No legal finding."}
    row = {"instrument_id": iid, "book_key": book["key"], "series": book["series"], "held_before": book["held"],
           "image": hit["image"], "printed_page": hit.get("printed_page"), "match": hit["how"],
           "match_date": hit.get("date") or "", "keyword_hits": "|".join(hit["keyword_hits"]),
           "text_path": data["text_path"], "lines": f"{l0 + 1}-{l1 + 1}",
           "shared_with": "|".join(hit.get("shared_with") or [])}
    return frag, src, row


# ----------------------------------------------------------------------------- new books

def load_new_books(job_dir):
    return json.loads((job_dir / "data" / "BOOKS.json").read_text(encoding="utf-8"))["books"]


DJVU_MAX = 60_000_000


def fetch_copy(ident, book, pool, budget):
    """early-orders-hunt's fetch_copy, copied here with two changes: an item the Archive marks
    access-restricted (a lending copy) is refused without any download, and a scan whose DjVu XML is larger
    than DJVU_MAX bytes is read from the Archive's hOCR search text and page index instead (the same OCR,
    a few MB instead of hundreds). Each file's sha1 is checked against the one the Archive publishes."""
    out = {"ia_identifier": ident, "status": "", "edition": {}, "custody": {}, "pages": None}
    try:
        meta, files, mr = hunt.ia_metadata(pool, budget, ident)
    except hunt.FetchError as e:
        out.update(status="metadata_fetch_failed", error=str(e))
        return out
    out["edition"] = hunt.check_edition(meta, book.get("verify", {}))
    if str(meta.get("access-restricted-item", "")).lower() == "true":
        out.update(status="access_restricted", error="lending copy; not downloaded")
        return out
    xml_name = ident + "_djvu.xml"
    st_name, pi_name = ident + "_hocr_searchtext.txt.gz", ident + "_hocr_pageindex.json.gz"
    use_hocr = (xml_name not in files or int(files[xml_name].get("size") or 0) > DJVU_MAX) and st_name in files and pi_name in files
    if xml_name not in files and not use_hocr:
        out.update(status="no_page_text_file", files_seen=sorted(files)[:20])
        return out
    names = [st_name, pi_name] if use_hocr else [xml_name]
    got = {}
    for name in names:
        if not budget.take():
            out["status"] = "request_budget_exhausted"
            return out
        try:
            got[name] = pool.fetch(hunt.IA_DOWNLOAD.format(ident=ident, name=name))
        except hunt.FetchError as e:
            out.update(status="page_text_fetch_failed", error=f"{name}: {e}")
            return out
    sha1s = {n: (files[n].get("sha1"), hunt.sha1_bytes(got[n]["body"])) for n in names}
    if use_hocr:
        text = gzip.decompress(got[st_name]["body"]).decode("utf-8", "replace")
        index = json.loads(gzip.decompress(got[pi_name]["body"]).decode("utf-8"))
        pages = [(i + 1, text[e[0]:e[1]]) for i, e in enumerate(index)]
    else:
        pages = hunt.djvu_pages(got[xml_name]["body"])
    main = got[names[0]]
    pdf = files.get(ident + ".pdf", {})
    out["custody"] = {
        "metadata_url": hunt.IA_METADATA.format(ident=ident), "metadata_sha256": mr["sha256"],
        "page_text_format": "hocr_searchtext+pageindex" if use_hocr else "djvu_xml",
        "page_text_url": main["url"], "page_text_bytes": main["bytes"], "page_text_sha256": main["sha256"],
        "page_text_sha1": sha1s[names[0]][1], "archive_published_sha1": sha1s[names[0]][0],
        "sha1_matches_archive": all(p == a for p, a in sha1s.values() if p) if any(p for p, _ in sha1s.values()) else None,
        "page_index_url": got[pi_name]["url"] if use_hocr else None,
        "page_index_sha256": got[pi_name]["sha256"] if use_hocr else None,
        "pdf_url": hunt.IA_DOWNLOAD.format(ident=ident, name=ident + ".pdf") if pdf else None,
        "pdf_bytes": int(pdf["size"]) if pdf.get("size") else None, "pdf_archive_sha1": pdf.get("sha1"), "pdf_fetched": False,
        "item_url": "https://archive.org/details/" + ident,
        "scanned_by": meta.get("scanner") or meta.get("contributor") or meta.get("sponsor"),
    }
    out.update(status="fetched", pages=pages)
    return out


def fetch_book(book, pool, budget, out_books, log):
    """One new book: metadata, edition check, page text with the Archive's sha1 (fetch_copy above)."""
    rec = {"book_key": book["key"], "series": book["series"], "label": book["label"], "status": "", "copies_tried": []}
    for ident in [book.get("ia_identifier")] + list(book.get("ia_alternates") or []):
        if not ident:
            continue
        copy = fetch_copy(ident, book, pool, budget)
        n = len(copy["pages"]) if copy.get("pages") else 0
        rec["copies_tried"].append({"ia_identifier": ident, "status": copy["status"], "pages": n,
                                    "edition_ok": copy.get("edition", {}).get("edition_ok"), "error": copy.get("error")})
        if copy["status"] == "request_budget_exhausted":
            rec["status"] = "request_budget_exhausted"
            return rec, None
        if copy["status"] != "fetched":
            continue
        if not copy["edition"].get("edition_ok"):
            log(f"  {book['key']}: {ident} metadata does not match the edition check {copy['edition']}; passed over")
            continue
        pages = copy["pages"]
        pm, stats = hunt.printed_page_map(pages)
        rows = [{"image": img, "section": pm.get(img, ("", None))[0], "printed": pm.get(img, ("", None))[1], "text": t}
                for img, t in pages]
        pages_path = out_books / f"{book['key']}_pages.jsonl.gz"
        with gzip.open(pages_path, "wt", encoding="utf-8", compresslevel=9) as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        cust = copy["custody"]
        rec.update(status="fetched", ia_identifier=ident, pages=len(pages), custody=cust, edition=copy["edition"],
                   page_map={k: stats[k] for k in ("heads_read", "heads_agree", "pages_mapped")},
                   retrieved_utc=hunt.now_utc(), pages_file="books/" + pages_path.name)
        (out_books / f"{book['key']}.json").write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        b = {"key": book["key"], "series": book["series"], "label": book["label"], "held": False, "path": pages_path,
             "format": "hunt_gz", "url": cust["page_text_url"], "sha256": cust["page_text_sha256"],
             "item_url": cust["item_url"], "archival_id": "ia:" + ident, "via": "data/BOOKS.json"}
        log(f"  {book['key']}: {len(pages)} pages from {ident}; sha1 {'matches' if cust.get('sha1_matches_archive') else 'NOT matched'}")
        return rec, b
    rec["status"] = rec["copies_tried"][-1]["status"] if rec["copies_tried"] else "no_identifier"
    if rec["copies_tried"] and rec["copies_tried"][-1]["status"] == "fetched":
        rec["status"] = "edition_check_failed"
    (out_books / f"{book['key']}.json").write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return rec, None


# ----------------------------------------------------------------------------- run

def write_csv(path, rows, fields):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def run(repo_root, job_dir, output_dir, transport=None):
    repo, job_dir, out = pathlib.Path(repo_root).resolve(), pathlib.Path(job_dir), pathlib.Path(output_dir)
    for sub in ("texts", "books"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    log_lines = []

    def log(msg):
        print(msg, flush=True)
        log_lines.append(msg)

    t0 = time.time()
    targets = load_targets(job_dir)
    by_date, by_number = collections.defaultdict(list), collections.defaultdict(list)
    for iid, t in targets.items():
        if t["suffix"] in ("", "half") or re.fullmatch(r"[A-Z]", t["suffix"]):
            by_number[(t["number"], t["suffix"])].append(iid)  # "106-1"-style duplicates: by date only
        for e in t["entries"]:
            if e["date"] and e["keywords"]:
                by_date[e["date"]].append((iid, e))
    log(f"Targets: {len(targets)} orders; {sum(1 for t in targets.values() if any(e['date'] for e in t['entries']))} "
        f"with a day date from the WPA list; {sum(1 for t in targets.values() if any(e['date'] and e['keywords'] for e in t['entries']))} "
        "with a date and distinctive summary words.")

    best = {}            # iid -> list of (book, hit)
    mentions, book_rows, failures = [], [], []
    per_book_found = {}

    def scan(book):
        t1 = time.time()
        pages = read_pages(book)
        found, ments = match_book(book, pages, targets, by_date, by_number)
        mentions.extend(ments)
        for iid, hit in found.items():
            best.setdefault(iid, []).append((book, hit))
        per_book_found[book["key"]] = set(found)
        book_rows.append({"book_key": book["key"], "series": book["series"], "label": book["label"],
                          "held_before": book["held"], "pages": len(pages), "orders_found": len(found),
                          "new_orders": len(set(found) - found_before[0]), "mentions": len(ments),
                          "source_url": book["url"], "sha256": book["sha256"], "via": book["via"],
                          "seconds": round(time.time() - t1, 1)})
        found_before[0] |= set(found)
        log(f"  {book['key']}: {len(pages)} pages, {len(found)} target orders, {len(ments)} number mentions only")

    found_before = [set()]
    log("Books the project already holds:")
    for book in held_books(repo):
        if not book["path"].is_file():
            failures.append({"book_key": book["key"], "stage": "held", "error": "page file missing"})
            continue
        scan(book)
    held_found = set(found_before[0])
    log(f"Found in held books: {len(held_found)} orders.")

    offline = os.environ.get("NEO_OFFLINE") == "1"
    budget = hunt.Budget(env_int("NEO_MAX_REQUESTS", 200))
    max_books = env_int("NEO_MAX_BOOKS", 40)
    only = set(k.strip() for k in os.environ.get("NEO_BOOKS", "").split(",") if k.strip())
    cache_dir = os.environ.get("JOB_CACHE_DIR") or os.path.join(tempfile.gettempdir(), "numbered-early-orders-cache")
    pool = hunt.make_pool(cache_dir, offline, transport)
    fetch_recs = []
    log("New books (data/BOOKS.json, in rank order):")
    fetched = 0
    for book in load_new_books(job_dir):
        if only and book["key"] not in only:
            continue
        if fetched >= max_books:
            fetch_recs.append({"book_key": book["key"], "series": book["series"], "label": book["label"], "status": "deferred_book_budget"})
            continue
        try:
            rec, b = fetch_book(book, pool, budget, out / "books", log)
        except Exception as exc:  # one bad book never stops the run
            rec, b = {"book_key": book["key"], "series": book["series"], "label": book["label"],
                      "status": "error", "error": f"{type(exc).__name__}: {exc}"}, None
        fetch_recs.append(rec)
        if b is None:
            failures.append({"book_key": book["key"], "stage": "fetch", "error": rec.get("status") + " " +
                             "; ".join(f"{c['ia_identifier']}: {c['status']} {c.get('error') or ''}" for c in rec.get("copies_tried", []))})
            log(f"  {book['key']}: not fetched ({rec['status']})")
            continue
        fetched += 1
        scan(b)

    # Save the best hit per order per book (up to three books per order, best first).
    frags, srcs, found_rows = [], [], []
    retrieved = hunt.now_utc()
    for iid in sorted(best):
        hits = sorted(best[iid], key=lambda bh: (-bh[1]["score"], not bh[0]["held"], bh[0]["key"]))[:3]
        for book, hit in hits:
            frag, src, row = save_text(out, book, iid, targets[iid], hit, retrieved)
            frags.append(frag)
            srcs.append(src)
            found_rows.append(row)
    with open(out / "FRAGMENTS.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for f in frags:
            fh.write(json.dumps(f, ensure_ascii=False, sort_keys=True) + "\n")
    with open(out / "SOURCES.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for s in srcs:
            fh.write(json.dumps(s, ensure_ascii=False, sort_keys=True) + "\n")

    mention_ids = set(m["instrument_id"] for m in mentions)
    not_found = []
    for iid, t in sorted(targets.items()):
        if iid in best:
            continue
        has_date = any(e["date"] for e in t["entries"])
        has_kw = any(e["date"] and e["keywords"] for e in t["entries"])
        why = ("only cited by another order's text (see MENTIONS.csv)" if iid in mention_ids else
               "no WPA entry; findable by number only" if not t["entries"] else
               "WPA date not day-precise or unreadable" if not has_date else
               "WPA summary has no distinctive words; findable by number only" if not has_kw else
               "not printed in any book searched")
        e0 = t["entries"][0] if t["entries"] else {}
        not_found.append({"instrument_id": iid, "wpa_date": e0.get("date") or "", "family_hint": e0.get("family_hint", ""),
                          "reason": why, "summary": re.sub(r"\s+", " ", e0.get("summary", ""))[:200]})
    write_csv(out / "FOUND.csv", found_rows, ["instrument_id", "book_key", "series", "held_before", "image", "printed_page",
                                              "match", "match_date", "keyword_hits", "text_path", "lines", "shared_with"])
    write_csv(out / "NOT_FOUND.csv", not_found, ["instrument_id", "wpa_date", "family_hint", "reason", "summary"])
    write_csv(out / "MENTIONS.csv", mentions, ["instrument_id", "book_key", "image", "printed_page", "number_text",
                                               "cited_cue", "date_near", "keyword_hits", "context"])
    write_csv(out / "BOOKS.csv", book_rows, ["book_key", "series", "label", "held_before", "pages", "orders_found",
                                             "new_orders", "mentions", "source_url", "sha256", "via", "seconds"])
    write_csv(out / "FETCHES.csv", [{**r, "ia_identifier": r.get("ia_identifier", ""), "pages": r.get("pages", ""),
                                     "tried": "; ".join(f"{c['ia_identifier']}:{c['status']}" for c in r.get("copies_tried", []))}
                                    for r in fetch_recs],
              ["book_key", "series", "label", "status", "ia_identifier", "pages", "tried", "error"])
    write_csv(out / "FAILURES.csv", failures, ["book_key", "stage", "error"])

    new_found = set(best) - held_found
    series_new = collections.Counter()
    for iid in new_found:
        for s in set(b["series"] for b, _ in best[iid] if not b["held"]):
            series_new[s] += 1
    how = collections.Counter(h["how"] for iid in best for _, h in best[iid][:1])
    summary = {
        "targets": len(targets), "orders_with_text": len(best), "found_in_held_books": len(held_found),
        "found_only_in_new_books": len(new_found), "still_without_text": len(targets) - len(best),
        "texts_saved": len(frags), "new_orders_by_series": dict(series_new.most_common()),
        "match_kinds_best_hit": dict(how), "number_mentions_only": len(mention_ids - set(best)),
        "books_held_scanned": sum(1 for r in book_rows if r["held_before"]),
        "books_new_fetched": sum(1 for r in book_rows if not r["held_before"]),
        "fetch_failures": len(failures), "requests": budget.spent, "requests_refused": budget.refused,
        "not_found_reasons": dict(collections.Counter(r["reason"] for r in not_found)),
        "seconds": round(time.time() - t0, 1),
        "note": "Leads only. Each text is OCR of a government printed copy, never the signed original; a "
                "date-and-subject hit is a machine match a reviewer must confirm against the scan. No status, "
                "census row or identity is changed.",
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    log(json.dumps(summary, indent=1, sort_keys=True))
    return summary

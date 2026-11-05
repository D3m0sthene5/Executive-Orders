"""Tischendorf: find the official printing of orders the project holds only as transcriptions.

Three routes, cheapest first. Each uses the held transcription's text fingerprint (fingerprint.py) to prove that a
candidate page carries the same order, together with the order's own number or signing date on that page.

  A. corroborate  An official find already on file but flagged for a page check (fr-originals, ofr-compilations,
                  isthmian-canal-1911, indian-reservations-1912). Offline: the found pages' text is compared with the
                  transcription. If the order's own number marker and its text are both there, the location is
                  confirmed by text.
  B. fr_by_date   Orders signed on or after 14 March 1936 with no official find: the govinfo scans of the daily
                  Federal Register issues printed in the three weeks after signing are read for the order's own
                  heading or closing number tag (source-ladder's fr_pages locator) and its text.
  C. ia_fulltext  Everything else: the transcription's rarest word runs are searched in the Internet Archive's
                  full-text index; each volume that matches is checked for government publication, its OCR is read
                  page by page, and the best page window is scored for the order's text, number and date.

Outputs are leads or located official printings in the producer schema the readiness tracker already uses.
needs_page_check is false only when every check in STRONG_RULES passes; the tracker counts nothing from this job
until the job is registered there (a separate owner decision). No status, identity or count changes here.
"""
from __future__ import annotations

import concurrent.futures
import csv
import datetime as dt
import io
import json
import os
import re
import sys
import threading
import time
import urllib.parse
import xml.etree.ElementTree as ET
from collections import Counter, OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("REPO_ROOT", HERE.parent.parent)).resolve()
sys.path.insert(0, str(REPO / "jobs/_lib"))
sys.path.insert(0, str(REPO / "jobs/source-ladder"))
sys.path.insert(0, str(HERE))

import eo_identity as ident  # noqa: E402
import fingerprint as fp  # noqa: E402
import fr_pages  # noqa: E402

JOB = "tischendorf-originals"
PRODUCED_BY = JOB
STATE_VERSION = 1
FIRST_FR = dt.date(1936, 3, 14)
FR_WINDOW_DAYS = 21
STRONG_SCORE = 0.5     # calibrated on 600 orders held both as an APP transcription and an FR original:
LEAD_SCORE = 0.3       # matched pairs: 5th percentile 0.55, median 0.87; unrelated pairs: maximum 0.06
STRONG_MARKERS = {"heading", "closing_number_tag"}
# OCR-damaged or mid-line headings anchor a strong verdict only with a higher text score.
WEAK_MARKERS = {"heading_ocr_damaged", "heading_midline"}
WEAK_MARKER_SCORE = 0.6
STRONG_RULES = ("own number heading or closing tag on the pages (an OCR-damaged or mid-line heading only with a "
                f"text score >= {WEAK_MARKER_SCORE}; in a compilation that prints no numbers, the signing date), "
                f"text fingerprint score >= {STRONG_SCORE}, distinctive fingerprint "
                f"(>= {fp.MIN_RARE} rare shingles), government-printed source, and no planted control failed this run")
OFFICIAL_PRODUCERS = ("fr-originals", "ofr-compilations", "isthmian-canal-1911", "indian-reservations-1912")
GOV_PUBLISHER = re.compile(r"government printing|govt\.? print|g\.\s?p\.\s?o|u\.\s?s\.\s?(dept|department)|"
                           r"department of|dept\.? of|war department|navy department|treasury|general land office|"
                           r"united states\b|u\.s\. g\.p\.o", re.I)
EO_COMPILATION = re.compile(r"executive\s+orders?|proclamations\s+and\s+executive", re.I)
RESTRICTED_COLLECTIONS = {"inlibrary", "printdisabled", "lendinglibrary", "browserlending"}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
IA_FTS = ("https://archive.org/services/search/beta/page_production/?user_query={q}&hits_per_page=10&page=1"
          "&service_backend=fts")


# --------------------------------------------------------------------------------------------- inputs

def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def order_number(iid, reg):
    """The number as printed, e.g. '1234' or '1234-A' -> '1234A' style used by fr_pages."""
    if reg.get("number"):
        return reg["number"] + (reg.get("suffix") or "")
    m = re.match(r"EO:(\d+)([A-Z]?)$", iid)
    return (m.group(1) + m.group(2)) if m else None


def parse_date(value):
    try:
        return dt.date.fromisoformat(value) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value or "") else None
    except ValueError:
        return None


def load_inputs(root=REPO):
    readiness = {r["instrument_id"]: r for r in read_csv(root / "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv")}
    register = {r["instrument_id"]: r for r in read_csv(root / "jobs/domesday-register/output/REGISTER.csv")}
    frags = ident.load_fragments(str(root))
    texts = {}
    sources = {}
    for iid, f, text in ident.iter_texts(frags, classes=("transcription",)):
        texts[iid] = texts.get(iid, "") + "\n" + text
        sources.setdefault(iid, set()).add(f["produced_by"])
    official = {}
    for iid, fs in frags.items():
        for f in fs:
            if f["class"] == "official":
                official.setdefault(iid, []).append(f)
    return readiness, register, texts, sources, official


def targets_from(readiness, register, texts, official):
    """Orders that need an official printing and for which a transcription is held.

    Two groups: orders whose original-text step is still open, and orders whose text step is satisfied only by a
    transcription (the tracker's original_copy_replacement_required), including dossiers already ready for human
    review. For the second group a find replaces the transcription and its quotation recheck obligation."""
    out = []
    for iid, r in readiness.items():
        replacement = r.get("original_copy_replacement_required") == "yes"
        if iid not in texts or not (r.get("step_original_text") == "open" or replacement):
            continue
        reg = register.get(iid, {})
        num = order_number(iid, reg)
        date = parse_date(reg.get("date", ""))
        flagged = [f for f in official.get(iid, []) if f.get("needs_page_check")]
        if flagged:
            route = "corroborate"
        elif date and date >= FIRST_FR:
            route = "fr_by_date"
        else:
            route = "ia_fulltext"
        out.append({"instrument_id": iid, "number": num, "date": date.isoformat() if date else (reg.get("date") or ""),
                    "title": reg.get("title", ""), "route": route, "flagged_finds": flagged,
                    "blockers": r.get("blockers", ""), "has_status": bool(r.get("provisional_status")),
                    "ready": r.get("ready_for_human_review") == "yes", "replacement": replacement})
    # Cheapest route first; within a route, ready dossiers resting on a transcription first, then orders with a
    # provisional status (nearest to a dossier).
    return sorted(out, key=lambda t: ({"corroborate": 0, "fr_by_date": 1, "ia_fulltext": 2}[t["route"]],
                                      not t["ready"], not t["has_status"], t["instrument_id"]))


# --------------------------------------------------------------------------------------------- checks

def long_dates(iso):
    d = parse_date(iso)
    if not d:
        return []
    m = MONTHS[d.month - 1]
    return [f"{m} {d.day}, {d.year}", f"{m} {d.day} {d.year}", f"{m[:3]}. {d.day}, {d.year}"]


def date_on(text, iso):
    norm = re.sub(r"\s+", " ", text or "")
    return any(re.search(re.escape(v).replace(r"\ ", r"\s?"), norm, re.I) for v in long_dates(iso))


def marker_in(page_texts, number, pages):
    if not number or not re.match(r"\d", str(number)):
        return None
    pages = list(pages)
    marker, _ = fr_pages.find_marker(page_texts, number, pages)
    if marker:
        return marker[0]
    for i in pages:
        if 0 <= i < len(page_texts) and fr_pages.fuzzy_heading(page_texts[i], number):
            return "heading_ocr_damaged"
    return None


def verdict(score, marker, date_ok, distinctive, government, controls_ok=True, numbers_printed=True):
    anchor = ((marker in STRONG_MARKERS) or (marker in WEAK_MARKERS and score >= WEAK_MARKER_SCORE)
              or (not numbers_printed and date_ok))
    if score >= STRONG_SCORE and anchor and distinctive and government and controls_ok:
        return "strong"
    if score >= LEAD_SCORE and (marker or date_ok):
        return "lead"
    return None


# --------------------------------------------------------------------------------------------- shared

def keep_better(st, res):
    if res and (not st.get("result") or (res["verdict"] == "strong", res["score"]) >
                (st["result"]["verdict"] == "strong", st["result"]["score"])):
        st["result"] = res


class CountingPool:
    """Counts each route's requests so one route cannot spend another's share."""

    def __init__(self, pool, counter, lock, route):
        self.pool, self.counter, self.lock, self.route = pool, counter, lock, route

    def fetch(self, url):
        with self.lock:
            self.counter[self.route] += 1
        return self.pool.fetch(url)

    @property
    def requests(self):
        return self.pool.requests


_PDF_POOL = None


def parse_pdf(raw):
    """PDF text extraction is CPU-bound; run it in worker processes so threads waiting on downloads overlap it."""
    global _PDF_POOL
    if os.environ.get("TISCHENDORF_INLINE_PDF") == "1":
        return pdf_pages(raw)
    if _PDF_POOL is None:
        _PDF_POOL = concurrent.futures.ProcessPoolExecutor(max_workers=max(1, (os.cpu_count() or 2)))
    return _PDF_POOL.submit(pdf_pages, raw).result()


def shutdown_pdf_workers():
    global _PDF_POOL
    if _PDF_POOL is not None:
        _PDF_POOL.shutdown()
        _PDF_POOL = None


# --------------------------------------------------------------------------------------------- route A

def body_of(saved_text):
    """Drop the provenance header the producing jobs put above the page text (it names the order's id)."""
    head, sep, rest = saved_text.partition("\n\n")
    return rest if sep and re.search(r"^(Instrument|Source|SHA-256)", head, re.M) else saved_text


def corroborate(target, F, root=REPO):
    best = None
    for f in target["flagged_finds"]:
        path = f.get("text_path")
        if not path or not os.path.isfile(path):
            continue
        text = body_of(Path(path).read_text(encoding="utf-8", errors="replace"))
        score = F.score(text)
        marker = marker_in([text], target["number"], [0])
        # The 1912 Indian-reservations compilation prints no order numbers; its orders are anchored by date.
        v = verdict(score, marker, date_on(text, target["date"]), F.distinctive, government=True,
                    numbers_printed=f["produced_by"] != "indian-reservations-1912")
        cand = {"route": f"corroborate/{f['produced_by']}", "verdict": v, "score": round(score, 3), "marker": marker,
                "url": f["url"], "sha256": f["sha256"], "page_or_item": f["page_or_item"], "text": text[:40000],
                "source_kind": "official find already on file (" + f["produced_by"] + ")"}
        if best is None or (v == "strong", score) > (best["verdict"] == "strong", best["score"]):
            best = cand
    return best


# --------------------------------------------------------------------------------------------- route B

class IssueTexts:
    """Federal Register daily issues, parsed once each and shared between worker threads."""

    def __init__(self, pool, keep=60):
        self.pool, self.keep, self.cache = pool, keep, OrderedDict()
        self.lock, self.day_locks = threading.Lock(), {}

    def get(self, day):
        key = day.isoformat()
        with self.lock:
            day_lock = self.day_locks.setdefault(key, threading.Lock())
        with day_lock:  # two orders waiting on the same issue download and parse it once
            with self.lock:
                if key in self.cache:
                    self.cache.move_to_end(key)
                    return self.cache[key]
            url = f"https://www.govinfo.gov/content/pkg/FR-{key}/pdf/FR-{key}.pdf"
            try:
                got = self.pool.fetch(url)
            except Exception as exc:  # noqa: BLE001 - a missing issue (404) or a block is recorded, never fatal
                val = {"url": url, "error": str(exc)[:200]}
            else:
                val = {"url": url, "sha256": got["sha256"], "pages": parse_pdf(got["body"])}
            with self.lock:
                self.cache[key] = val
                while len(self.cache) > self.keep:
                    self.cache.popitem(last=False)
            return val


def pdf_pages(raw):
    from pypdf import PdfReader
    try:
        reader = PdfReader(io.BytesIO(raw))
        return [(p.extract_text() or "") for p in reader.pages]
    except Exception:  # noqa: BLE001
        return []


def fr_issue_days(signing_iso):
    d = parse_date(signing_iso)
    if not d:
        return []
    days = [d + dt.timedelta(days=k) for k in range(1, FR_WINDOW_DAYS + 1)] + [d]
    return [x for x in days if x.weekday() != 6]  # no Sunday issues


def fr_by_date(target, F, issues, tried):
    best = None
    for day in fr_issue_days(target["date"]):
        key = day.isoformat()
        if key in tried:
            continue
        issue = issues.get(day)
        if "error" in issue and "HTTP 404" not in issue["error"]:
            return best, False  # transient: stop and retry next run without marking the rest tried
        tried.append(key)
        pages = issue.get("pages") or []
        if not pages:
            continue
        loc = fr_pages.locate_order(pages, target["number"])
        if not loc["found"]:
            continue
        a, b = loc["first_page"], loc["last_page"]
        text = "\n".join(pages[a - 1:b])
        score = F.score(text)
        pmap = fr_pages.printed_page_map(pages)
        printed = [p for p, i in pmap.items() if a - 1 <= i <= b - 1]
        v = verdict(score, loc.get("marker_kind"), date_on(text, target["date"]), F.distinctive, government=True)
        cand = {"route": "official/fr_issue_by_date", "verdict": v, "score": round(score, 3),
                "marker": loc.get("marker_kind"), "url": issue["url"], "sha256": issue["sha256"],
                "page_or_item": f"Federal Register {key}; PDF pages {a}-{b}"
                                + (f"; printed pages {min(printed)}-{max(printed)}" if printed else ""),
                "text": text[:40000], "source_kind": "govinfo scan of the printed Federal Register daily issue",
                "fr_locator": {k: loc.get(k) for k in ("confidence", "method", "marker_kind", "notes", "locator_version")}}
        if best is None or (cand["verdict"] == "strong", score) > (best["verdict"] == "strong", best["score"]):
            best = cand
        if v == "strong":
            break
    return best, True


# --------------------------------------------------------------------------------------------- route C

class Archive:
    def __init__(self, pool, max_xml_bytes=90_000_000):
        self.pool, self.meta, self.pages, self.max_xml = pool, {}, OrderedDict(), max_xml_bytes
        self.lock, self.item_locks = threading.Lock(), {}

    def _item_lock(self, item):
        with self.lock:
            return self.item_locks.setdefault(item, threading.Lock())

    def search(self, phrase):
        url = IA_FTS.format(q=urllib.parse.quote(f'"{phrase}"'))
        got = self.pool.fetch(url)
        data = json.loads(got["body"].decode("utf-8", "replace"))
        hits = (((data.get("response") or {}).get("body") or {}).get("hits") or {}).get("hits") or []
        out = []
        for h in hits:
            for fields in (h.get("fields") or {}, h.get("_source") or {}, h):
                ident_ = fields.get("identifier") if isinstance(fields, dict) else None
                if isinstance(ident_, list):
                    ident_ = ident_[0] if ident_ else None
                if ident_:
                    out.append(ident_)
                    break
        return list(dict.fromkeys(out))

    def metadata(self, item):
        with self._item_lock("meta:" + item):
            if item not in self.meta:
                got = self.pool.fetch(f"https://archive.org/metadata/{urllib.parse.quote(item)}")
                self.meta[item] = json.loads(got["body"].decode("utf-8", "replace"))
            return self.meta[item]

    def classify(self, item):
        m = self.metadata(item)
        md = m.get("metadata") or {}
        flat = lambda v: " ; ".join(v) if isinstance(v, list) else str(v or "")  # noqa: E731
        collections = set(md.get("collection") if isinstance(md.get("collection"), list) else [md.get("collection")])
        publisher, title = flat(md.get("publisher")), flat(md.get("title"))
        xml = next((f for f in m.get("files", []) if f.get("name", "").endswith("_djvu.xml")), None)
        return {"item": item, "title": title, "publisher": publisher, "date": flat(md.get("date")),
                "government": bool(GOV_PUBLISHER.search(publisher)) or "fedlink" in collections
                              or "usgovernmentdocuments" in collections,
                "eo_compilation": bool(EO_COMPILATION.search(title)),
                "restricted": bool(collections & RESTRICTED_COLLECTIONS) or str(md.get("access-restricted-item")) == "true",
                "xml": xml.get("name") if xml else None, "xml_size": int(xml.get("size") or 0) if xml else 0}

    def page_texts(self, info):
        item = info["item"]
        with self._item_lock("pages:" + item):
            with self.lock:
                if item in self.pages:
                    self.pages.move_to_end(item)
                    return self.pages[item]
            url = f"https://archive.org/download/{urllib.parse.quote(item)}/{urllib.parse.quote(info['xml'])}"
            got = self.pool.fetch(url)
            texts = djvu_pages(got["body"])
            vol = {"url": url, "sha256": got["sha256"], "pages": texts, "shingles": [fp.shingles(t) for t in texts]}
            with self.lock:
                self.pages[item] = vol
                while len(self.pages) > 16:
                    self.pages.popitem(last=False)
            return vol


def djvu_pages(raw):
    pages = []
    for _, el in ET.iterparse(io.BytesIO(raw), events=("end",)):
        if el.tag == "OBJECT":
            pages.append(" ".join((w.text or "") for w in el.iter("WORD")))
            el.clear()
    return pages


def best_window(pages, F, number, iso, page_shingles=None):
    page_shingles = page_shingles or [fp.shingles(t) for t in pages]
    best = None
    for i in range(len(pages)):
        for span in (1, 2):
            if i + span > len(pages):
                continue
            # A shingle broken across the page turn is lost; that only lowers the score.
            score = F.score_set(set().union(*page_shingles[i:i + span]))
            if best is None or score > best[0] + 0.02 or (abs(score - best[0]) <= 0.02 and span < best[2]):
                best = (score, i, span)
    if not best:
        return None
    score, i, span = best
    text = "\n".join(pages[i:i + span])
    marker = marker_in(pages, number, range(max(0, i - 1), min(len(pages), i + span + 1)))
    numbers_printed = any(marker_in(pages, str(n), range(max(0, i - 2), min(len(pages), i + span + 2)))
                          for n in _nearby_numbers(number))
    return {"score": score, "first": i + 1, "last": i + span, "text": text, "marker": marker,
            "date_ok": date_on(text, iso), "numbers_printed": bool(marker) or numbers_printed}


def _nearby_numbers(number):
    m = re.match(r"(\d+)", number or "")
    if not m:
        return []
    n = int(m.group(1))
    return [k for k in (n - 2, n - 1, n + 1, n + 2) if k > 0]


def ia_fulltext(target, F, archive, tried, budget_ok):
    phrases = F.phrases(k=3, source_text=target["_text"])
    best = None
    for phrase in phrases:
        if phrase in tried["phrases"]:
            continue
        if not budget_ok():
            return best, False
        try:
            items = archive.search(phrase)
        except Exception:  # noqa: BLE001 - search outage: retry next run
            return best, False
        tried["phrases"].append(phrase)
        for item in items:
            if item in tried["items"] or not budget_ok():
                continue
            tried["items"].append(item)
            try:
                info = archive.classify(item)
                if info["restricted"] or not info["xml"] or info["xml_size"] > archive.max_xml:
                    continue
                vol = archive.page_texts(info)
            except Exception:  # noqa: BLE001
                continue
            w = best_window(vol["pages"], F, target["number"], target["date"], vol.get("shingles"))
            if not w:
                continue
            v = verdict(w["score"], w["marker"], w["date_ok"], F.distinctive,
                        government=info["government"] and info["eo_compilation"], numbers_printed=w["numbers_printed"])
            cand = {"route": "official/ia_fulltext" if info["eo_compilation"] else "lead/ia_fulltext",
                    "verdict": v, "score": round(w["score"], 3), "marker": w["marker"], "date_ok": w["date_ok"],
                    "url": f"https://archive.org/details/{item}/page/n{w['first'] - 1}", "sha256": vol["sha256"],
                    "page_or_item": f"{info['title']} ({info['publisher'] or 'publisher not recorded'}, "
                                    f"{info['date'] or 'n.d.'}), Internet Archive {item}, scan leaves {w['first']}-{w['last']}",
                    "text": w["text"][:40000], "text_layer_url": vol["url"], "search_phrase": phrase,
                    "source_kind": ("government-printed compilation of executive orders" if info["government"] and info["eo_compilation"]
                                    else "government publication" if info["government"] else "non-government publication"),
                    "volume": {k: info[k] for k in ("item", "title", "publisher", "date", "government", "eo_compilation")}}
            if best is None or (cand["verdict"] == "strong", w["score"]) > (best["verdict"] == "strong", best["score"]):
                best = cand
            if v == "strong":
                return best, True
    return best, True


# --------------------------------------------------------------------------------------------- controls

def run_controls(official, texts, df, n_docs, register, sample=60):
    """Planted checks for the text-and-marker rule, run offline every time.

    Positives: orders whose official find already counts (needs_page_check false) must be confirmed by their own
    transcription. Negatives: the same pages paired with a different order's transcription and number must never be
    confirmed. One accepted negative blocks every strong verdict in this run.
    """
    pool = sorted(i for i, fs in official.items() if i in texts and any(f.get("needs_page_check") is False and
                  f.get("text_path") and os.path.isfile(f["text_path"]) for f in fs))
    step = max(1, len(pool) // sample)
    chosen = pool[::step][:sample]
    pos = neg = pos_ok = neg_bad = 0
    bad = []
    for k, iid in enumerate(chosen):
        f = next(f for f in official[iid] if f.get("needs_page_check") is False and f.get("text_path")
                 and os.path.isfile(f["text_path"]))
        text = body_of(Path(f["text_path"]).read_text(encoding="utf-8", errors="replace"))
        num = order_number(iid, register.get(iid, {}))
        F = fp.Fingerprint(texts[iid], df, n_docs)
        if F.distinctive:
            pos += 1
            pos_ok += verdict(F.score(text), marker_in([text], num, [0]), False, True, True) == "strong"
        # Negative 1: the right text on these pages, but a number that is not this order's.
        if F.distinctive and num and num.isdigit():
            wrong = str(int(num) + 7)
            neg += 1
            if verdict(F.score(text), marker_in([text], wrong, [0]), False, True, True) == "strong":
                neg_bad += 1
                bad.append([iid, "accepted under wrong number", wrong])
        # Negative 2: these pages paired with an unrelated order's transcription and number.
        other = chosen[(k + len(chosen) // 2) % len(chosen)]
        if other == iid:
            continue
        G = fp.Fingerprint(texts[other], df, n_docs)
        onum = order_number(other, register.get(other, {}))
        if G.distinctive:
            neg += 1
            if verdict(G.score(text), marker_in([text], onum, [0]), False, True, True) == "strong":
                neg_bad += 1
                bad.append([other, "on pages of", iid])
    return {"positives": pos, "positives_confirmed": pos_ok, "negatives": neg, "negatives_accepted": neg_bad,
            "accepted_negatives": bad, "passed": neg_bad == 0 and pos > 0 and pos_ok / pos >= 0.8}


# --------------------------------------------------------------------------------------------- outputs

def fragment(target, res):
    iid = target["instrument_id"]
    strong = res["verdict"] == "strong"
    text_path = f"texts/{re.sub(r'[^A-Za-z0-9]+', '_', iid)}.txt"
    data = {"url": res["url"], "sha256": res["sha256"], "page_or_item": res["page_or_item"],
            "source_id": f"{JOB}:{iid}:{res['sha256'][:12]}", "text_path": text_path,
            "signing_date": target["date"], "title": target["title"], "route": res["route"],
            "location_confidence": "high" if strong else "medium" if res["verdict"] == "lead" else "low",
            "location_verified": False, "needs_page_check": not strong,
            "match": {k: res.get(k) for k in ("score", "marker", "date_ok", "search_phrase", "source_kind")},
            "text_layer_url": res.get("text_layer_url")}
    note = (f"Machine location by text fingerprint, verdict {res['verdict']}: {res['source_kind']}; fingerprint score "
            f"{res['score']} against the held transcription; own-number marker {res.get('marker') or 'not found'}. "
            + ("Every strong-rule check passed. " if strong else "Needs a page check before it counts as the original. ")
            + "Identity, page boundaries and wording are NOT human-verified; this is not a legal conclusion.")
    return ({"instrument_id": iid, "kind": "original_representation", "grade": "machine_read_government_printed_copy",
             "acceptable_as_original": False, "data": data,
             "sources": [{"url": res["url"], "sha256": res["sha256"], "page_or_item": res["page_or_item"]}],
             "confidence_note": note, "produced_by": PRODUCED_BY}, text_path)


def load_prior_state(root=REPO):
    try:
        import prior_output
        prior = prior_output.PriorOutput.from_git_head(str(root), f"jobs/{JOB}/output")
        raw = prior.read("STATE.json")
        if raw:
            data = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
            if data.get("state_version") == STATE_VERSION:
                return data.get("orders", {}), "git_head"
    except Exception:  # noqa: BLE001
        pass
    path = root / f"jobs/{JOB}/output/STATE.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text())
            if data.get("state_version") == STATE_VERSION:
                return data.get("orders", {}), "folder"
        except ValueError:
            pass
    return {}, "none"


def main(out=None, pool=None, root=REPO, now=time.monotonic):
    out = Path(out or os.environ.get("OUTPUT_DIR", HERE / "output"))
    out.mkdir(parents=True, exist_ok=True)
    (out / "texts").mkdir(exist_ok=True)
    started = now()
    budget_s = float(os.environ.get("JOB_TIME_BUDGET_MIN", "200")) * 60
    max_requests = int(os.environ.get("JOB_MAX_REQUESTS", "9000"))
    # Each network route gets its own share, so one route cannot starve the other.
    route_cap = {"fr_by_date": int(os.environ.get("JOB_MAX_REQUESTS_FR", "1500")),
                 "ia_fulltext": int(os.environ.get("JOB_MAX_REQUESTS_IA", "7500"))}
    workers = int(os.environ.get("JOB_WORKERS", "24"))

    readiness, register, texts, sources, official = load_inputs(root)
    df, n_docs = fp.document_frequency(texts)
    targets = targets_from(readiness, register, texts, official)
    controls = run_controls(official, texts, df, n_docs, register)
    print(f"{len(targets)} targets; controls: {json.dumps(controls)[:300]}")

    if pool is None:
        from fetch_pool import FetchPool
        cache = Path(os.environ.get("JOB_CACHE_DIR", REPO / ".job-cache" / JOB))
        # Owner, 2026-11-05: go as fast as is reasonable. FetchPool's ceiling of 6 requests in flight per host and
        # 0.1 s between starts; robots.txt and any crawl-delay it sets are still obeyed.
        pool = FetchPool(cache, workers=workers, per_host=6, user_agent="EO-Road-System/1.0 (tischendorf-originals)",
                         min_interval=0.1, max_bytes=100_000_000)
    lock = threading.Lock()
    route_used = Counter()

    def budget_for(route):
        return lambda: (pool.requests < max_requests and now() - started < budget_s
                        and route_used[route] < route_cap.get(route, max_requests))

    issues = IssueTexts(CountingPool(pool, route_used, lock, "fr_by_date"))
    archive = Archive(CountingPool(pool, route_used, lock, "ia_fulltext"))
    prior, prior_from = load_prior_state(root)
    state, counts, network = {}, Counter(), []

    # Offline work first (carried results, corroboration), in order; network work is collected.
    for t in targets:
        iid = t["instrument_id"]
        st = prior.get(iid) or {"tried": {"issues": [], "phrases": [], "items": []}, "result": None, "complete": False}
        st["route"] = t["route"]
        state[iid] = st
        if st.get("result") and st["result"]["verdict"] == "strong":
            counts["carried_strong"] += 1
            continue
        F = fp.Fingerprint(texts[iid], df, n_docs)
        t["_text"] = texts[iid]
        if t["route"] == "corroborate":
            keep_better(st, corroborate(t, F, root))
            st["complete"] = True
            counts["attempted_corroborate"] += 1
        elif t["route"] == "ia_fulltext" and not F.distinctive:
            st["note"] = "transcription too generic to verify by text"
            counts["ia_not_distinctive"] += 1
        elif not (t["route"] == "fr_by_date" and st.get("complete")):
            network.append((t, F))
    print(f"[{round(now() - started)}s] offline work done; {len(network)} orders need the network", flush=True)

    # Federal Register orders by date, so neighbouring orders share issues still held in memory.
    network.sort(key=lambda x: (x[0]["route"] != "fr_by_date", x[0]["date"] if x[0]["route"] == "fr_by_date" else ""))
    done = [0]
    errors = []

    def work(item):
        t, F = item
        st = state[t["instrument_id"]]
        ok = budget_for(t["route"])
        if not ok():
            with lock:
                counts[f"deferred_{t['route']}"] += 1
            return
        try:
            if t["route"] == "fr_by_date":
                res, complete = fr_by_date(t, F, issues, st["tried"]["issues"])
            else:
                res, complete = ia_fulltext(t, F, archive, st["tried"], ok)
        except Exception as exc:  # noqa: BLE001 - one bad order or page must never cost the whole run's results
            with lock:
                counts[f"error_{t['route']}"] += 1
                errors.append({"instrument_id": t["instrument_id"], "route": t["route"],
                               "error": f"{type(exc).__name__}: {exc}"[:300]})
            return
        with lock:
            keep_better(st, res)
            st["complete"] = complete
            counts[f"attempted_{t['route']}"] += 1
            done[0] += 1
            if done[0] % 50 == 0:
                print(f"[{round(now() - started)}s] {done[0]}/{len(network)} network orders, {pool.requests} requests, "
                      f"{dict(route_used)}", flush=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        for _ in ex.map(work, network):
            pass
    shutdown_pdf_workers()

    # Write fragments: strong verdicts count only if the planted controls passed this run.
    frags, leads = [], []
    by_route = Counter()
    for t in targets:
        st = state[t["instrument_id"]]
        res = st.get("result")
        if not res or not res.get("verdict"):
            continue
        if res["verdict"] == "strong" and not controls["passed"]:
            res = dict(res, verdict="lead")
        frag, text_path = fragment(t, res)
        header = (f"Instrument: {t['instrument_id']}\nSource: {res['url']}\nSHA-256 of the downloaded file: {res['sha256']}\n"
                  f"Location: {res['page_or_item']}\nMachine text layer (OCR) of the pages Tischendorf located; may contain "
                  "recognition errors and neighbouring documents. Not an authenticated transcription.\n\n")
        (out / text_path).write_text(header + res["text"], encoding="utf-8")
        frags.append(frag)
        by_route[(res["route"].split("/")[0] + "/" + res["route"].split("/")[-1], res["verdict"])] += 1
        leads.append({"instrument_id": t["instrument_id"], "verdict": res["verdict"], "route": res["route"],
                      "score": res["score"], "marker": res.get("marker") or "", "page_or_item": res["page_or_item"],
                      "url": res["url"], "source_kind": res["source_kind"]})

    with open(out / "ERRORS.jsonl", "w", encoding="utf-8") as f:
        for e in errors:
            f.write(json.dumps(e) + "\n")
    with open(out / "FRAGMENTS.jsonl", "w", encoding="utf-8") as f:
        for fr in frags:
            f.write(json.dumps(fr, ensure_ascii=False, sort_keys=True) + "\n")
    with open(out / "FINDS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["instrument_id", "verdict", "route", "score", "marker", "page_or_item", "url",
                                          "source_kind"])
        w.writeheader()
        w.writerows(sorted(leads, key=lambda r: (r["verdict"] != "strong", r["instrument_id"])))
    lean = {iid: {k: v for k, v in st.items()} for iid, st in state.items()}
    (out / "STATE.json").write_text(json.dumps({"state_version": STATE_VERSION, "orders": lean}, ensure_ascii=False,
                                               sort_keys=True) + "\n", encoding="utf-8")
    strong = sum(1 for r in leads if r["verdict"] == "strong")
    summary = {
        "job": JOB, "targets": len(targets), "targets_by_route": Counter(t["route"] for t in targets),
        "replacement_targets": sum(t["replacement"] for t in targets),
        "replacement_targets_ready": sum(t["replacement"] and t["ready"] for t in targets),
        "replacement_strong": sum(1 for t in targets if t["replacement"] and (state[t["instrument_id"]].get("result") or {}).get("verdict") == "strong"),
        "strong": strong, "leads": len(leads) - strong, "by_route_and_verdict": {f"{a}|{b}": c for (a, b), c in sorted(by_route.items())},
        "controls": controls, "strong_rules": STRONG_RULES, "requests": pool.requests,
        "requests_by_route": dict(route_used), "order_errors": len(errors), "request_caps": {"total": max_requests, **route_cap},
        "workers": workers,
        "bytes_downloaded": getattr(pool, "bytes_downloaded", None), "seconds": round(now() - started),
        "prior_state_from": prior_from, "run_counts": counts,
        "counted_by_tracker": False,
        "what_this_is_not": "No status, identity, census, codebook or readiness change. Strong finds are machine "
                            "locations; the tracker counts them only after this job is registered there.",
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=2, default=dict) + "\n")
    report = [f"# Tischendorf: originals for transcription-only orders", "",
              f"Targets: {len(targets)} ({', '.join(f'{k} {v}' for k, v in summary['targets_by_route'].items())}).",
              f"Located with every strong check passed: **{strong}**. Leads needing a page check: {len(leads) - strong}.",
              f"Planted controls: {controls['positives_confirmed']}/{controls['positives']} true pairs confirmed, "
              f"{controls['negatives_accepted']}/{controls['negatives']} false pairs accepted "
              f"({'passed' if controls['passed'] else 'FAILED: every strong verdict was downgraded to a lead'}).",
              f"Requests this run: {pool.requests}.", "", "| Route | Verdict | Orders |", "|---|---|---:|"]
    report += [f"| {a} | {b} | {c} |" for (a, b), c in sorted(by_route.items())]
    report += ["", f"Strong rule: {STRONG_RULES}.", "",
               "These are machine locations, not authentication. The readiness tracker does not read this job yet."]
    (out / "REPORT.md").write_text("\n".join(report) + "\n")
    print("\n".join(report))
    return summary


if __name__ == "__main__":
    main()

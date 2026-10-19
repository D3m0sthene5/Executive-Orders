"""X1 step 1: give every pre-1937 order a type, its evidence and a confidence.

Sources, in order of weight:
  wpa   the WPA 1944 numbered list's one-line summary (data/WPA_NUMBERED_ENTRIES.csv)
  app   the American Presidency Project title, when it is more than "Executive Order"
  text  the first part of a saved text of the order (claim-kit TEXT_REPRESENTATIONS)

Confidence:
  high    two sources give the same type, or one gives a strong type and another the same class
  medium  one source gives a strong type and no source disagrees on the class
  low     only a weak (generic-word) type, or sources disagree on the class
  none    nothing matched: type "unknown"

Census-gap rows (orders APP counts that the project does not hold) are typed
from APP's unnumbered pre-1937 titles and, separately, Lord's 1943 unnumbered
list; those rows name no project identity.
"""
import collections, csv, json, re
from pathlib import Path

import taxonomy as tx

MODERN_FROM = 7532   # first order in the OFR catalog (January 1937), as build_effort.py
TEXT_HEAD = 2500     # characters of a saved text read for keywords
GRADE_RANK = ["official_fr_scan_ocr_text", "fr_originals_needs_page_check", "official_compilation_high",
              "government_printed_copy", "government_printed_copy_needs_page_check",
              "machine_read_government_printed_copy", "machine_read_government_printed_copy_needs_page_check",
              "mirror_transcription", "mirror_transcription_needs_page_check", "mirror_transcription_app",
              "website_transcription", "compiled_transcription_lead_needs_page_check", "held_text_lead", "derivative_lead"]


def num(iid):
    m = re.match(r"EO:(\d+)", iid or "")
    return int(m.group(1)) if m else None


def load_universe(repo):
    out = {}
    for r in csv.DictReader(open(repo / "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv")):
        n = num(r["id"])
        year = int(r["date_effective"]) if r["date_effective"].isdigit() else None
        if (n is not None and n < MODERN_FROM) or (n is None and year is not None and year < 1937):
            out[r["id"]] = {"year": year, "number": n}
    return out


# The OCR'd list sometimes runs one entry into the next ("... 28-1:Jan. 30 Mourning ...").
NEXT_ENTRY = re.compile(r"(?<!E\. 0\. )(?<!No\. )\b\d{1,4}(?:-\d+|[A-Z]|½|l/2)?(?:,\s?\d{1,4})*\s?:\s?"
                        r"(?:Jan|Feb|Mar|Apr|May|June?|July?|Aug|Sept?|Oct|Nov|Dec)\b")


def load_wpa(job):
    w = collections.defaultdict(list)
    for r in csv.DictReader(open(job / "data/WPA_NUMBERED_ENTRIES.csv")):
        m = NEXT_ENTRY.search(r["text"], 10)
        if m:
            r = dict(r, text=r["text"][:m.start()].rstrip(), text_truncated_at_next_entry="yes")
        w[r["id"]].append(r)
    return w


def load_app(repo):
    t = {}
    for r in csv.DictReader(open(repo / "jobs/app-executive-orders/output/INDEX.csv")):
        if r["instrument_id"]:
            t.setdefault(r["instrument_id"], r)
    return t


def app_title_body(title):
    """APP titles read 'Executive Order 1234—Subject'; return the subject or ''."""
    parts = re.split(r"\s*[—–]\s*", title, maxsplit=1)
    body = parts[1] if len(parts) > 1 else ""
    return "" if tx.APP_GENERIC_TITLE.match(title.strip()) else body


def load_texts(repo, ids):
    """Best-graded saved text per order (path, grade), from claim-kit's text index."""
    best = {}
    rank = {g: i for i, g in enumerate(GRADE_RANK)}
    path = repo / "jobs/claim-kit/output/TEXT_REPRESENTATIONS.jsonl"
    for line in open(path):
        x = json.loads(line)
        i = x.get("instrument_id")
        if i not in ids:
            continue
        p = x.get("text_path")
        if not p or not (repo / p).exists():
            continue
        r = rank.get(x.get("grade"), len(rank))
        if i not in best or r < best[i][2]:
            best[i] = (p, x.get("grade"), r)
    return {i: (p, g) for i, (p, g, _) in best.items()}


def read_head(repo, path, n=TEXT_HEAD):
    try:
        return (repo / path).read_text(encoding="utf-8", errors="replace")[:n]
    except OSError:
        return ""


def decide(hits_by_source):
    """hits_by_source: {source: [(type, pattern, match), ...]} in precedence order.

    Returns type, class, confidence, agreeing sources, chosen evidence."""
    tops = {s: h[0] for s, h in hits_by_source.items() if h}
    if not tops:
        return "unknown", "unknown", "none", [], None
    strong = lambda s: tx.TYPE_STRENGTH[tops[s][0]] == "strong"
    # The WPA summary describes the whole order; APP's title names it. A saved
    # text is read only as a fallback: compiled volumes often run into the
    # neighbouring orders, so its keywords can belong to another order.
    described = [s for s in ("wpa", "app") if s in tops]
    if described:
        chosen_src = next((s for s in described if strong(s)), described[0])
    else:
        chosen_src = "text"
    t = tops[chosen_src][0]
    cls = tx.TYPE_CLASS[t]
    agree = sorted(s for s, h in tops.items() if h[0] == t)
    # Another source agrees on the class if any of its hits is in this class.
    others = [s for s in tops if s != chosen_src]
    class_agree = [s for s in others if any(tx.TYPE_CLASS[x[0]] == cls for x in hits_by_source[s])]
    class_disagree = [s for s in others if s not in class_agree and strong(s) and s != "text"]
    is_strong = tx.TYPE_STRENGTH[t] == "strong"
    if chosen_src == "text":
        conf = "medium" if is_strong and class_agree else "low"
    elif is_strong and (len(agree) >= 2 or class_agree) and not class_disagree:
        conf = "high"
    elif is_strong and not class_disagree:
        conf = "medium"
    else:
        conf = "low"
    return t, cls, conf, agree, (chosen_src,) + tuple(tops[chosen_src])


def classify(repo, job):
    universe = load_universe(repo)
    wpa, app = load_wpa(job), load_app(repo)
    texts = load_texts(repo, set(universe))
    rows = []
    for iid, u in sorted(universe.items(), key=lambda kv: (kv[1]["number"] or 0, kv[0])):
        year = u["year"]
        srcs = {}
        w = wpa.get(iid, [])
        if w:
            wtext = " ".join(r["text"] for r in w)
            wyear = int(w[0]["year"]) if w[0]["year"].isdigit() else year
            srcs["wpa"] = tx.matches(wtext, wyear or year)
        a = app.get(iid)
        if a and app_title_body(a["title"]):
            srcs["app"] = tx.matches(app_title_body(a["title"]), year or (int(a["date"][:4]) if a["date"][:4].isdigit() else None))
        tp = texts.get(iid)
        if tp:
            srcs["text"] = tx.matches(read_head(repo, tp[0]), year)
        t, cls, conf, agree, ev = decide(srcs)
        rows.append({
            "instrument_id": iid, "number": u["number"] if u["number"] is not None else "", "year": year or "",
            "type": t, "class": cls, "rule_id": tx.TYPE_RULE.get(t, ""), "confidence": conf,
            "sources_agreeing": "|".join(agree),
            "wpa_type": (srcs.get("wpa") or [("",)])[0][0] if "wpa" in srcs else "",
            "app_type": (srcs.get("app") or [("",)])[0][0] if "app" in srcs else "",
            "text_type": (srcs.get("text") or [("",)])[0][0] if "text" in srcs else "",
            "evidence_source": ev[0] if ev else "", "evidence_pattern": ev[2] if ev else "",
            "evidence_match": ev[3] if ev else "",
            "wpa_summary": (" ".join(r["text"] for r in w))[:400],
            "app_title": a["title"] if a else "",
            "text_path": tp[0] if tp else "", "text_grade": tp[1] if tp else "",
            "wpa_hint": w[0]["family_hint"] if w else "",
        })
    return rows


def classify_gap(repo, job, project_ids):
    """Type APP's pre-1937 rows that name no project identity, and Lord's unnumbered entries."""
    out = []
    for r in csv.DictReader(open(repo / "jobs/app-executive-orders/output/INDEX.csv")):
        if r["date"] >= "1937" or (r["instrument_id"] and r["instrument_id"] in project_ids):
            continue
        body = app_title_body(r["title"])
        year = int(r["date"][:4]) if r["date"][:4].isdigit() else None
        hits = {"app": tx.matches(body, year)} if body else {}
        t, cls, conf, agree, ev = decide(hits)
        out.append({"gap_source": "app_index", "key": r["url"], "president": r["president"], "date": r["date"],
                    "type": t, "class": cls, "confidence": conf, "summary": r["title"][:300],
                    "evidence_pattern": ev[2] if ev else ""})
    for r in csv.DictReader(open(job / "data/WPA_UNNUMBERED_ENTRIES.csv")):
        year = int(r["year"]) if r["year"].isdigit() else None
        if year is None or year >= 1937:
            continue
        t, cls, conf, agree, ev = decide({"wpa": tx.matches(r["summary"], year)})
        out.append({"gap_source": "lord_1943_unnumbered", "key": "seq:" + r["seq"], "president": "", "date": r["date"] or str(year),
                    "type": t, "class": cls, "confidence": conf, "summary": r["summary"][:300],
                    "evidence_pattern": ev[2] if ev else ""})
    return out

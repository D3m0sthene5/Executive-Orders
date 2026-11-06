"""Mabillon held printings: official printings the project already holds but files as transcriptions.

`jobs/hathi-gpo-orders` saved, for 1,531 orders numbered 5076-8027, the text of government-printed pages: the
Government Printing Office's bound "Executive Orders" volumes (Wikimedia Commons DjVu scans, OCR), the 1974 GPO
compilation *Proclamations and Executive Orders: Herbert Hoover* (Internet Archive) and govinfo scans of 1936
Federal Register issues. The readiness tracker reads that job as a compiled transcription (a lead only), so 552 of
the orders in Mabillon's frame still show NO_OFFICIAL_SOURCE_LOCATED although their official printing is held.

This job proves, by machine, which of those saved passages are the order: it scores each government-printed passage
against the order's independent transcription (the American Presidency Project's text, a different witness) with
Tischendorf's text fingerprint, and requires the order's own number as a heading or closing tag on the passage.
The matching rules are Tischendorf's, imported unchanged (`jobs/tischendorf-originals`), so a strong verdict here
means exactly what it means there. No network is used.

Planted controls every run (the run's strong verdicts become leads if any control fails):
- positives: orders whose official original already counts and that also have a government-printed passage here;
  the passage must be confirmed against the order's own transcription;
- negatives, three per eligible passage: the passage under a number that is not the order's (+7), and the passage
  under its own number paired with the transcription of the order one and two places away in the same printed
  volume (the hardest case: adjacent orders on similar subjects, often on the same page). The neighbour's text under
  the neighbour's own number is not a negative, because a saved page often really prints both orders; those cases
  are counted apart (`neighbour_also_printed_on_passage`).
The error rate on negatives is reported with its 95% upper bound.

Outputs are machine locations in the producer schema the tracker reads, `acceptable_as_original: false`. Nothing
here changes a status, identity, census entry, codebook grade or count; the tracker does not read this job until
the owner registers it.
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("REPO_ROOT", HERE.parent.parent)).resolve()
sys.path.insert(0, str(REPO / "jobs/_lib"))
sys.path.insert(0, str(REPO / "jobs/source-ladder"))
sys.path.insert(0, str(REPO / "jobs/tischendorf-originals"))

import eo_identity as ident  # noqa: E402
import fingerprint as fp  # noqa: E402
import tischendorf as T  # noqa: E402  (matching rules reused unchanged)

JOB = "mabillon-held-printings"
HATHI = "jobs/hathi-gpo-orders/output"
FRAME = REPO / "research/mabillon/frame/FRAME.csv"
# Routes of hathi-gpo-orders whose passage is a government printing of the order (not a volunteer transcription).
GOV_ROUTES = {
    "commons_gpo_ocr": "GPO bound volume of executive orders (Wikimedia Commons scan, local OCR)",
    "ia_hoover": "1974 GPO compilation, Proclamations and Executive Orders: Herbert Hoover (Internet Archive)",
    "govinfo_fr": "govinfo scan of the printed Federal Register daily issue",
}
REFERENCE_PRODUCERS = ("app-executive-orders",)  # an independent witness of the order's text
SEP = "----- EXACT SOURCE TEXT -----"
STRONG_RULES_ADDED = ("; scored on the order's own printed segment (between the previous closing number tag and its "
                      "own); and the claimed order's text beats every order numbered within 3 of it by at least 0.15")


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def passage(path):
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    return raw.split(SEP, 1)[1] if SEP in raw else T.body_of(raw)


def wilson_upper(k, n):
    """One-sided 95% upper bound on a rate with k events in n trials (exact for k = 0)."""
    if n == 0:
        return None
    if k == 0:
        return round(1 - 0.05 ** (1 / n), 4)
    z = 1.645
    p = k / n
    return round((p + z * z / (2 * n) + z * ((p * (1 - p) + z * z / (4 * n)) / n) ** 0.5) / (1 + z * z / n), 4)


def load(root=REPO):
    hathi = {}
    for line in (root / HATHI / "FRAGMENTS.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            d = json.loads(line)
            route = d["data"]["source_id"].split(":")[1]
            if route in GOV_ROUTES:
                hathi[d["instrument_id"]] = dict(d, route=route,
                                                 path=str(root / HATHI / d["data"]["text_path"]))
    frags = ident.load_fragments(str(root))
    refs, texts = {}, {}
    for iid, f, text in ident.iter_texts(frags, classes=("transcription",)):
        if f["produced_by"] == "hathi-gpo-orders":
            continue
        texts[iid] = texts.get(iid, "") + "\n" + text          # document frequencies over independent texts
        if f["produced_by"] in REFERENCE_PRODUCERS:
            refs[iid] = refs.get(iid, "") + "\n" + text
    official = {iid: [f for f in fs if f["class"] == "official" and f.get("needs_page_check") is False
                      and f.get("text_path") and os.path.isfile(f["text_path"])] for iid, fs in frags.items()}
    register = {r["instrument_id"]: r for r in read_csv(root / "jobs/domesday-register/output/REGISTER.csv")}
    frame = {r["instrument_id"] for r in read_csv(FRAME)} if FRAME.is_file() else set()
    return hathi, refs, texts, {k: v for k, v in official.items() if v}, register, frame


# Any closing number tag ("[No. 7405]", OCR "[No. 74051", "(No. 7405)") ends one printed document.
ANY_CLOSING = re.compile(r"[\[\(|]\s*N\s?[oO0]\s?\.?\s*\d{3,5}[^\n]{0,4}")


def own_segment(text, number):
    """The order's own document inside a saved passage that may also print its neighbours.

    Change from Tischendorf (justified by this job's planted neighbour controls, 11 of 4,382 accepted without it):
    the hathi-gpo passages are whole printed pages, so they often carry the next order too. When the order's own
    closing tag or heading is found, only the text between the previous document's closing tag and the order's own
    closing tag is scored. Without an own marker the passage cannot be strong anyway."""
    if not number or not re.match(r"\d", str(number)):
        return text, None
    marker, _ = T.fr_pages.find_marker([text], number, [0])
    if not marker:
        return text, None
    kind, _, start, end = marker[:4]
    if kind == "closing_number_tag":
        prev = [m.end() for m in ANY_CLOSING.finditer(text, 0, start)]
        return text[(prev[-1] if prev else 0):end], kind
    nxt = ANY_CLOSING.search(text, end)
    return text[start:(nxt.end() if nxt else len(text))], kind


MARGIN = 0.15      # the claimed order's text must beat every nearby order's text on the segment by this much
NEIGHBOURS = 3     # nearby = numbers within this distance of the number marked on the passage


class Competitors:
    """Fingerprints of the orders numbered near a passage's marked number.

    Second change from Tischendorf, again from this job's controls: orders printed as families (codes of fair
    competition, veterans regulations, land withdrawals for resurvey) share many rare phrases, so a neighbour's
    transcription can score above 0.5 on an order's own segment (49 of 4,382 neighbour negatives without this rule).
    A strong verdict therefore also needs the claimed order's text to beat every order within three numbers by
    MARGIN, a likelihood-ratio style uniqueness test; if a neighbour matches nearly as well, the find stays a lead."""

    def __init__(self, refs, df, n_docs):
        self.refs, self.df, self.n_docs, self.cache = refs, df, n_docs, {}
        self.by_number = collections.defaultdict(list)
        for iid in refs:
            p = ident.parse_eo_id(iid)
            if p:
                self.by_number[p[0]].append(iid)

    def fp(self, iid):
        if iid not in self.cache:
            self.cache[iid] = fp.Fingerprint(self.refs[iid], self.df, self.n_docs)
        return self.cache[iid]

    def best(self, segment, number, exclude):
        m = re.match(r"(\d+)", str(number or ""))
        if not m:
            return 0.0, None
        n, cand = int(m.group(1)), set()
        for k in range(n - NEIGHBOURS, n + NEIGHBOURS + 1):
            cand.update(self.by_number.get(k, []))
        cand.discard(exclude)
        best = (0.0, None)
        shingles = fp.shingles(segment)
        for iid in sorted(cand):
            G = self.fp(iid)
            if G.distinctive:
                sc = G.score_set(shingles)
                if sc > best[0]:
                    best = (sc, iid)
        return best


COMP = None


def judge(text, F, number, date, ref_id=None):
    seg, kind = own_segment(text, number)
    score = F.score(seg)
    marker = T.marker_in([text], number, [0])
    v = T.verdict(score, marker, T.date_on(text, date), F.distinctive, government=True)
    if v == "strong" and COMP is not None:
        rival, _ = COMP.best(seg, number, ref_id)
        if score - rival < MARGIN:
            v = "lead"
    return v, round(score, 3), marker


def controls(hathi, refs, official, register, df, n_docs):
    """Planted positives and negatives over the government-printed passages."""
    pos = pos_ok = 0
    pos_fail = []
    eligible = sorted((iid for iid in hathi if iid in refs), key=lambda i: (hathi[i]["route"], ident.parse_eo_id(i) or (0, "")))
    for iid in eligible:
        if iid not in official:
            continue
        # Label check: the passage must also agree with the counted official text, else its label is uncertain.
        off = T.body_of(Path(official[iid][0]["text_path"]).read_text(encoding="utf-8", errors="replace"))
        text = passage(hathi[iid]["path"])
        if fp.Fingerprint(off, df, n_docs).score(text) < T.STRONG_SCORE:
            continue
        F = fp.Fingerprint(refs[iid], df, n_docs)
        if not F.distinctive:
            continue
        num = T.order_number(iid, register.get(iid, {}))
        pos += 1
        v = judge(text, F, num, register.get(iid, {}).get("date", ""), iid)[0]
        pos_ok += v == "strong"
        if v != "strong":
            pos_fail.append(iid)
    neg = neg_bad = neighbour_printed = 0
    neg_by_route = collections.Counter()
    bad = []
    by_route = collections.defaultdict(list)
    for iid in eligible:
        by_route[hathi[iid]["route"]].append(iid)
    for route, ids in by_route.items():
        for k, iid in enumerate(ids):
            text = passage(hathi[iid]["path"])
            num = T.order_number(iid, register.get(iid, {}))
            F = fp.Fingerprint(refs[iid], df, n_docs)
            if F.distinctive and num and num.isdigit():
                neg += 1
                neg_by_route[route] += 1
                if judge(text, F, str(int(num) + 7), "", iid)[0] == "strong":
                    neg_bad += 1
                    bad.append([iid, "wrong number", str(int(num) + 7)])
            for off in (1, 2):
                if k + off >= len(ids):
                    continue
                other = ids[k + off]
                G = fp.Fingerprint(refs[other], df, n_docs)
                onum = T.order_number(other, register.get(other, {}))
                if not G.distinctive:
                    continue
                # Negative: the neighbour's text under this passage's own number. (The neighbour's text under the
                # neighbour's number is not a negative: a page often really prints both; those are counted apart.)
                neg += 1
                neg_by_route[route] += 1
                if judge(text, G, num, register.get(iid, {}).get("date", ""), other)[0] == "strong":
                    neg_bad += 1
                    bad.append([other, "text accepted under the number of", iid])
                if judge(text, G, onum, register.get(other, {}).get("date", ""), other)[0] == "strong":
                    neighbour_printed += 1
    return {"positives": pos, "positives_confirmed": pos_ok, "positives_not_confirmed": pos_fail[:50],
            "negatives": neg, "negatives_accepted": neg_bad, "accepted_negatives": bad[:50],
            "false_accept_upper95": wilson_upper(neg_bad, neg),
            "neighbour_also_printed_on_passage": neighbour_printed, "negatives_by_route": dict(neg_by_route),
            "sensitivity": round(pos_ok / pos, 3) if pos else None,
            "passed": neg_bad == 0 and pos > 0 and pos_ok / pos >= 0.8}


def main(out=None, root=REPO):
    out = Path(out or os.environ.get("OUTPUT_DIR", HERE / "output"))
    (out / "texts").mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    hathi, refs, texts, official, register, frame = load(root)
    df, n_docs = fp.document_frequency(texts)
    global COMP
    COMP = Competitors(refs, df, n_docs)
    ctl = controls(hathi, refs, official, register, df, n_docs)
    print("controls:", json.dumps({k: v for k, v in ctl.items() if not isinstance(v, list)}), flush=True)

    # Targets: every government-printed passage of an order with no counted official original.
    rows, frags, sources = [], [], []
    counts = collections.Counter()
    for iid in sorted(hathi, key=lambda i: ident.parse_eo_id(i) or (0, "")):
        if iid in official:
            continue
        h = hathi[iid]
        reg = register.get(iid, {})
        num = T.order_number(iid, reg)
        text = passage(h["path"])
        in_frame = iid in frame
        if iid not in refs:
            v, score, marker = None, None, T.marker_in([text], num, [0])
            why = "no independent transcription to compare"
        else:
            F = fp.Fingerprint(refs[iid], df, n_docs)
            v, score, marker = judge(text, F, num, reg.get("date", ""), iid)
            why = "" if F.distinctive else "transcription too generic to verify by text"
            if v == "strong" and not ctl["passed"]:
                v = "lead"
        if v is None and marker:
            v = "lead"  # own number on a government printing, but no text comparison possible
        counts[(h["route"], v or "unverified", in_frame)] += 1
        d = h["data"]
        rows.append({"instrument_id": iid, "in_frame": in_frame, "route": h["route"], "verdict": v or "unverified",
                     "score": score if score is not None else "", "marker": marker or "", "note": why,
                     "page_or_item": d.get("page_or_item", ""), "url": d.get("url", "")})
        if not v:
            continue
        strong = v == "strong"
        tp = f"texts/{re.sub(r'[^A-Za-z0-9]+', '_', iid)}.txt"
        header = (f"Instrument: {iid}\nSource: {d.get('url')}\nSHA-256 of the source file: {d.get('sha256')}\n"
                  f"Location: {d.get('page_or_item')}\nGovernment-printed passage saved by hathi-gpo-orders "
                  f"({GOV_ROUTES[h['route']]}); machine OCR, may contain recognition errors and neighbouring text.\n\n")
        (out / tp).write_text(header + text, encoding="utf-8")
        data = {"url": d.get("url"), "sha256": d.get("sha256"), "page_or_item": d.get("page_or_item"),
                "source_id": f"{JOB}:{iid}:{(d.get('sha256') or '')[:12]}", "text_path": tp,
                "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "signing_date": reg.get("date", ""), "title": reg.get("title", ""), "route": f"held/{h['route']}",
                "location_confidence": "high" if strong else "medium", "location_verified": False,
                "needs_page_check": not strong,
                "match": {"score": score, "marker": marker, "reference": "app-executive-orders",
                          "source_kind": GOV_ROUTES[h["route"]], "held_by": "hathi-gpo-orders"}}
        note = (f"Machine location by text fingerprint, verdict {v}: {GOV_ROUTES[h['route']]}; score {score} against "
                f"the American Presidency Project transcription; own-number marker {marker or 'not found'}. "
                + ("Every strong-rule check passed (Tischendorf's rule). " if strong else
                   "Needs a page check before it counts as the original. ")
                + "Identity, page boundaries and wording are NOT human-verified; this is not a legal conclusion.")
        frags.append({"instrument_id": iid, "kind": "original_representation",
                      "grade": "machine_read_government_printed_copy", "acceptable_as_original": False, "data": data,
                      "sources": [{"url": d.get("url"), "sha256": d.get("sha256"), "page_or_item": d.get("page_or_item")}],
                      "confidence_note": note, "produced_by": JOB})
        sources.append({"instrument_ids": [iid], "url": d.get("url"), "sha256": d.get("sha256"),
                        "page_or_item": d.get("page_or_item"), "grade": "machine_read_government_printed_copy",
                        "representation_type": "machine_read_government_printed_copy",
                        "acceptable_as_original": False, "needs_page_check": not strong, "route": h["route"],
                        "held_by": "hathi-gpo-orders", "exact_source_text_sha256": data["text_sha256"]})

    with open(out / "FRAGMENTS.jsonl", "w", encoding="utf-8") as f:
        for x in frags:
            f.write(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n")
    with open(out / "SOURCES.jsonl", "w", encoding="utf-8") as f:
        for x in sources:
            f.write(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n")
    with open(out / "FINDS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["instrument_id"])
        w.writeheader()
        w.writerows(rows)
    frame_strong = sum(1 for r in rows if r["in_frame"] and r["verdict"] == "strong")
    frame_lead = sum(1 for r in rows if r["in_frame"] and r["verdict"] == "lead")
    rules_sha = {p: hashlib.sha256((REPO / p).read_bytes()).hexdigest() for p in
                 ("jobs/tischendorf-originals/tischendorf.py", "jobs/tischendorf-originals/fingerprint.py",
                  "jobs/source-ladder/fr_pages.py")}
    summary = {"job": JOB, "passages": len(hathi), "targets": len(rows),
               "frame_orders": len(frame), "frame_targets": sum(r["in_frame"] for r in rows),
               "frame_strong": frame_strong, "frame_lead": frame_lead,
               "strong": sum(r["verdict"] == "strong" for r in rows), "lead": sum(r["verdict"] == "lead" for r in rows),
               "by_route_verdict_in_frame": {f"{a}|{b}|{'frame' if c else 'other'}": n for (a, b, c), n in sorted(counts.items())},
               "controls": ctl, "strong_rules": T.STRONG_RULES + STRONG_RULES_ADDED, "rules_sha256": rules_sha,
               "seconds": round(time.monotonic() - started), "network_requests": 0, "counted_by_tracker": False,
               "what_this_is_not": "No status, identity, census, codebook or readiness change. Strong finds are machine "
                                   "locations of held government printings; the tracker counts them only after the "
                                   "owner registers this job."}
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    rep = ["# Mabillon held printings: official printings already held, proved by text", "",
           f"Government-printed passages held by hathi-gpo-orders: {len(hathi)}. Orders without a counted original "
           f"among them: {len(rows)}, of which {summary['frame_targets']} are in Mabillon's frame.",
           f"Frame orders located with every strong check passed: **{frame_strong}**; leads: {frame_lead}.",
           f"Planted controls: {ctl['positives_confirmed']}/{ctl['positives']} true pairs confirmed; "
           f"{ctl['negatives_accepted']}/{ctl['negatives']} false pairs accepted (95% upper bound on the false-accept "
           f"rate {ctl['false_accept_upper95']}); {'passed' if ctl['passed'] else 'FAILED: strong verdicts written as leads'}.",
           "", "| Route | Verdict | In frame | Orders |", "|---|---|---|---:|"]
    rep += [f"| {a} | {b} | {'yes' if c else 'no'} | {n} |" for (a, b, c), n in sorted(counts.items())]
    rep += ["", f"Strong rule: Tischendorf's ({T.STRONG_RULES}){STRONG_RULES_ADDED}.", "",
            "Machine locations, not authentication. The readiness tracker does not read this job yet."]
    (out / "REPORT.md").write_text("\n".join(rep) + "\n")
    print("\n".join(rep))
    return summary


if __name__ == "__main__":
    main()

"""Build DRAFT operative-clause inventories from saved original texts.

Reads (never writes) the repo; writes only to OUTPUT_DIR (and the scan cache in
JOB_CACHE_DIR). See README.md for what the outputs mean and do not mean.
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import segment as S
import sources as SRC

JOB = "clause-drafts"
LEGAL_CUTOFF = "2026-10-14"
UNIVERSE = "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv"
PROVISIONAL = "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv"
DEFAULT_INPUT_JOBS = ("fr-originals", "source-ladder")
NEEDS_JUDGMENT = ["state_at_cutoff", "first_end_or_current_predicate", "later_events", "clause_boundaries_and_completeness"]
PREVIEW_CHARS = 200
APP_FRAGMENTS = "FRAGMENTS_APP.jsonl"  # transcription-based drafts (American Presidency Project fallback input)

# A draft with any of these warnings may be about the WRONG ORDER. It is written to
# IDENTITY_QUARANTINE.csv instead of FRAGMENTS.jsonl / SOURCES.jsonl.
IDENTITY_MARKERS = (
    "identity_doubt_",                                   # signer or printed date does not fit the order's year
    "body_cites_its_own_order_number_identity_doubtful",  # the text cites "its own" number as an earlier order
    "no_heading_in_text_identity_from_source_url_only",  # web text with no heading: identity only from the address
    "app_page_title_number_",                            # web page title and address name different orders
    "heading_has_no_number_identity_from_file_name_only",
)
# A draft with any of these warnings is labelled "partial" (never "good").
NOT_GOOD_MARKERS = IDENTITY_MARKERS + (
    "identity", "ocr_text_noisy", "contents_listing", "no_operative_unit", "incomplete_", "section_number_gap",
    "ocr_columns_may_be_interleaved", "no_signature_block_found", "long_unnumbered_text",
)
# OCR interleave signals that mean the clause text mixes other documents: rejected.
OCR_REJECT = ("fr_masthead_or_contents_text", "second_enacting_clause_inside_body", "no_enacting_or_operative_words")


def log(msg):
    print(msg, flush=True)


def fail(msg, code=2):
    print("ERROR: " + msg, flush=True)
    sys.exit(code)


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_limit(raw):
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        n = int(raw)
    except ValueError:
        fail(f"JOB_LIMIT must be a whole number such as 40 (it is {raw!r}). Leave it unset to process every order.")
    if n <= 0:
        fail(f"JOB_LIMIT must be 1 or more (it is {n}). Leave it unset to process every order.")
    return n


def read_universe(repo: Path):
    ids, era, date = set(), {}, {}
    p = repo / UNIVERSE
    if not p.exists():
        return ids, era, date
    with open(p, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            ids.add(row["id"])
            era[row["id"]] = (row.get("year_group") or "Unknown date").replace("–", "-")
            date[row["id"]] = row.get("date_effective") or ""
    return ids, era, date


def read_provisional(repo: Path):
    p = repo / PROVISIONAL
    if not p.exists():
        return set()
    with open(p, encoding="utf-8", newline="") as fh:
        return {r["instrument_id"] for r in csv.DictReader(fh)}


def number_key(iid: str):
    m = re.match(r"EO:(\d+)(.*)", iid)
    return (int(m.group(1)), m.group(2)) if m else (10 ** 9, iid)


def choose_orders(order_ids, era, provisional, limit, only):
    """Pick which orders to process. With a limit, spread the picks across eras
    (round robin), provisional cases first within each era."""
    ids = sorted(order_ids, key=number_key)
    if only:
        return [i for i in ids if i in only]
    if not limit or limit >= len(ids):
        return ids
    by_era = defaultdict(list)
    for i in ids:
        by_era[era.get(i, "unknown")].append(i)
    for k in by_era:
        lst = by_era[k]
        prov = [i for i in lst if i in provisional]
        rest = [i for i in lst if i not in provisional]

        # spread through the era so that the sample is not all from one decade
        def spread(seq):
            if not seq:
                return []
            step = max(1, len(seq) // max(1, limit))
            picked = seq[::step]
            return picked + [x for x in seq if x not in set(picked)]
        by_era[k] = spread(prov) + spread(rest)
    out = []
    eras = sorted(by_era)
    while len(out) < limit and any(by_era.values()):
        for k in eras:
            if by_era[k] and len(out) < limit:
                out.append(by_era[k].pop(0))
    return sorted(out, key=number_key)


def norm_number(n: str) -> str:
    m = re.match(r"0*(\d+)\s*[-‐–]?\s*([A-Za-z]?)", n or "")
    return (m.group(1) + m.group(2).upper()) if m else (n or "")


def identity_problems(warnings):
    return [w for w in warnings if any(w.startswith(m) for m in IDENTITY_MARKERS)]


def ocr_signals(warnings):
    for w in warnings:
        if w.startswith("ocr_columns_may_be_interleaved:"):
            return w.split(":", 1)[1].split("+")
    return []


def usable(cand, seg, loc):
    """False when the draft would mostly be noise: no clauses, or old-FR OCR whose
    columns are interleaved / heavily garbled / without a signature block."""
    if not seg["clauses"]:
        return False
    if cand.grade == "official_fr_scan_ocr_text":
        w = seg["warnings"]
        noise = max([float(x.rsplit("_", 1)[1]) for x in w if x.startswith("ocr_text_noisy_")] or [0.0])
        if noise >= 0.12 or any("contents_listing" in x for x in w) or not loc.signature_found:
            return False
        if any(sig in OCR_REJECT for sig in ocr_signals(w)):
            return False
    return True


def is_good(seg, loc, cand):
    """'good' = usable, signature block found, and none of the NOT_GOOD warnings."""
    w = seg["warnings"]
    return usable(cand, seg, loc) and loc.signature_found and not any(m in x for x in w for m in NOT_GOOD_MARKERS)


def quality(seg, loc, cand):
    """Sort key (higher is better): usable, identity not in doubt, good, numbered heading, fewer warnings."""
    w = seg["warnings"]
    return (1 if usable(cand, seg, loc) else 0, 0 if identity_problems(w) else 1, 1 if is_good(seg, loc, cand) else 0,
            1 if loc.heading_style == "numbered" else 0, -len(w), len(seg["clauses"]))


def safe_id(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s)


def page_label(cand, page_starts, doc_start, start, end):
    """FR page range for an offset range of a Stage 21 PDF text."""
    if not page_starts:
        return None
    a = start + doc_start
    b = end + doc_start - 1
    pa = max(i for i, p in enumerate(page_starts) if p <= a)
    pb = max(i for i, p in enumerate(page_starts) if p <= max(a, b))
    pdf = f"PDF p. {pa + 1}" if pa == pb else f"PDF pp. {pa + 1}-{pb + 1}"
    if cand.fr_volume and cand.fr_start_page:
        fa, fb = cand.fr_start_page + pa, cand.fr_start_page + pb
        fr = f"{cand.fr_volume} FR {fa}" if fa == fb else f"{cand.fr_volume} FR {fa}-{fb}"
        return f"{fr} ({pdf})"
    return pdf


def try_candidate(cand, text, universe_year):
    """Locate and segment one candidate copy. Returns (loc, seg, evidence) or (None, reason, None)."""
    stripped = text.strip()
    if stripped.count("\n") < 3 and len(stripped) > 600:
        # e.g. Opus review extracts "Title || By virtue of ... SEC. 2. ... RICHARD NIXON The White House, ..."
        return None, "text_flattened_to_one_line_paragraph_and_section_breaks_lost", None
    loc = S.locate_order(text, cand.number)
    if loc is None and cand.body_only_ok:
        others = sorted({n for n, _ in S.find_headings(text) if norm_number(n) != norm_number(cand.number)})
        if others:
            return None, "body_only_refused_text_has_heading_for_other_order_" + ",".join(others[:3]), None
        loc = S.locate_body_only(text)
        if loc is not None and cand.origin.startswith("job:"):
            loc.warnings = [("no_heading_in_text_identity_from_input_job_record"
                             if w == "no_heading_in_text_identity_from_source_url_only" else w) for w in loc.warnings]
    if loc is None:
        return None, "order_not_located_in_text", None
    seg = S.segment(text, loc, cand.instrument_id)
    seg["warnings"] += [f for f in cand.extra.get("identity_flags", []) if f not in seg["warnings"]]
    evidence = S.identity_evidence(text, loc)
    seg["warnings"] += S.identity_doubts(evidence, universe_year)
    if cand.grade == "official_fr_scan_ocr_text":
        sig = S.ocr_interleave_signals(text, loc.body_start, loc.doc_end)  # body + anything kept after the signature
        first = text[seg["clauses"][0]["start"]:seg["clauses"][0]["end"]] if seg["clauses"] else ""
        if not seg["recitals"] and not re.match(
                r"(?i)\s*(?:it\s+is|i\s+(?:do\s+)?hereby|i,|by\s+virtue|under|pursuant|upon|in\s+order|the\s|all\s|there|s\s?e\s?c|1\.|\(a\))", first):
            sig.append("order_opening_not_found")  # the text starts mid-sentence: the start is in another column
        if S._quote_state(text, loc.body_start, loc.body_end)[1]:
            sig.append("unbalanced_quotes")  # e.g. inserted text announced but printed in another column
        if sig:
            seg["warnings"].append("ocr_columns_may_be_interleaved:" + "+".join(sig))
    return loc, seg, evidence


def check_inputs(repo: Path, universe, log_fn):
    """Find the Opus zip and report which inputs are available. Missing essential
    inputs stop the job (unless CLAUSE_ALLOW_PARTIAL_INPUTS=1), so that a broken
    download never replaces a full previous output with a small one."""
    status = {"universe": "ok" if universe else "missing", "opus_zip": None, "stage21_custody": None}
    p = repo / SRC.OPUS_ZIP
    zpath = None
    if not p.exists():
        status["opus_zip"] = "missing"
    else:
        zpath = SRC.ensure_lfs(repo, SRC.OPUS_ZIP, log_fn)
        if zpath is None:
            status["opus_zip"] = "git_lfs_pointer_not_downloaded"
        else:
            try:
                with zipfile.ZipFile(zpath) as z:
                    z.namelist()
                status["opus_zip"] = "ok"
            except Exception as exc:  # noqa: BLE001
                status["opus_zip"] = f"unreadable:{type(exc).__name__}"
                zpath = None
    custody = repo / SRC.STAGE21_DIR / "CASE_ORIGINAL_SOURCE_CUSTODY.csv"
    status["stage21_custody"] = "ok" if custody.exists() else "missing"
    return zpath, status


def main():
    t0 = time.time()
    out = Path(os.environ["OUTPUT_DIR"]).resolve()
    repo = Path(os.environ.get("REPO_ROOT", ".")).resolve()
    cache = Path(os.environ.get("JOB_CACHE_DIR") or (out.parent / f"{JOB}-cache")).resolve()
    limit = parse_limit(os.environ.get("JOB_LIMIT"))
    only = {x.strip() for x in os.environ.get("JOB_IDS", "").split(",") if x.strip()}
    input_jobs = [x.strip() for x in os.environ.get("CLAUSE_INPUT_JOBS", ",".join(DEFAULT_INPUT_JOBS)).split(",") if x.strip()]
    allow_partial = os.environ.get("CLAUSE_ALLOW_PARTIAL_INPUTS", "").strip() == "1"
    # APP transcriptions from app-executive-orders: fallback draft inputs (CLAUSE_APP_INPUT=0 turns them off).
    use_app = os.environ.get("CLAUSE_APP_INPUT", "1").strip() != "0"
    # Segment every candidate copy, not only until the first good one, to measure each source's
    # segmentation outcomes (env CLAUSE_MEASURE_ALL=1 or a MEASURE_ALL file in this folder). Selection is unchanged.
    measure_all = (os.environ.get("CLAUSE_MEASURE_ALL", "").strip() == "1"
                   or (Path(__file__).resolve().parent / "MEASURE_ALL").is_file())

    universe, era, dates = read_universe(repo)
    provisional = read_provisional(repo)
    zpath, input_status = check_inputs(repo, universe, log)
    missing = [k for k in ("universe", "opus_zip") if input_status[k] != "ok"]
    if missing and not allow_partial:
        fail("required input(s) not available: " + ", ".join(f"{k} = {input_status[k]}" for k in missing)
             + ". Nothing was built, so the previous results are not replaced by a smaller set. "
             "On GitHub, check that needs.txt lists the folder and that 'git lfs pull' worked (LFS quota). "
             "To build anyway from what is available, set CLAUSE_ALLOW_PARTIAL_INPUTS=1.", code=3)
    if missing:
        log("WARNING: building from partial inputs (CLAUSE_ALLOW_PARTIAL_INPUTS=1): " + ", ".join(missing))
    out.mkdir(parents=True, exist_ok=True)
    (out / "texts").mkdir(exist_ok=True)
    log(f"Universe: {len(universe)} orders; provisional cases: {len(provisional)}")

    # ---- collect candidates -------------------------------------------------
    cands = defaultdict(list)
    problems = []
    s21, p = SRC.stage21_candidates(repo, universe, log)
    problems += p
    for c in s21:
        cands[c.instrument_id].append(c)
    log(f"Stage 21 PDFs: {len(s21)} usable, {len(p)} problems")

    opus_stats = {}
    if zpath:
        scan = SRC.scan_opus_zip(zpath, universe, log, cache)
        opus_stats = scan["stats"]
        oc = SRC.opus_candidates(scan, universe)
        for c in oc:
            cands[c.instrument_id].append(c)
        log(f"Opus zip: {opus_stats.get('text_members')} text members, {opus_stats.get('source_ok')} usable order-text sources, {len(oc)} order candidates")
        for e in scan["entries"]:
            if e.get("member_hash_check") == "MISMATCH":
                problems.append((e["url"], "opus_text_member_sha256_differs_from_meta", e["member"]))
    else:
        log("Opus release zip not available; skipped.")

    jc, p, job_seen = SRC.job_candidates(repo, input_jobs, universe, log)
    problems += p
    for c in jc:
        cands[c.instrument_id].append(c)
    log(f"Other jobs: {job_seen}")
    app_seen = {}
    if use_app:
        ac, p, app_seen = SRC.app_job_candidates(repo, universe, dates, log)
        problems += p
        for c in ac:
            cands[c.instrument_id].append(c)
        log(f"APP transcriptions ({SRC.APP_JOB}, fallback only): {app_seen}, {len(p)} refused")

    # Identity sanity: an FR issue cannot print an order signed years later or long before.
    dropped = 0
    for iid in list(cands):
        year = (dates.get(iid) or "")[:4]
        keep = []
        for c in cands[iid]:
            iy = SRC.issue_year(c.url)
            if year.isdigit() and iy and not (int(year) <= iy <= int(year) + 1):
                problems.append((iid, "fr_issue_year_inconsistent_with_order_date", f"order {year}, issue {iy}: {c.locator}"))
                dropped += 1
                continue
            keep.append(c)
        if keep:
            cands[iid] = keep
        else:
            del cands[iid]
    log(f"Dropped {dropped} candidates whose FR issue year does not fit the order's date")

    # out of scope: signed after the legal cutoff (by universe date when it is a full date)
    order_ids = [i for i in cands if not (dates.get(i, "")[:10] > LEGAL_CUTOFF and len(dates.get(i, "")) >= 10)]
    chosen = choose_orders(order_ids, era, provisional, limit, only)
    log(f"Orders with at least one candidate text: {len(order_ids)}; processing {len(chosen)}" + (f" (JOB_LIMIT={limit})" if limit else ""))

    # ---- segment -------------------------------------------------------------
    loader = SRC.TextLoader(repo, zpath)
    frag_fh = open(out / "FRAGMENTS.jsonl", "w", encoding="utf-8", newline="\n")
    # Drafts from APP transcriptions go to their own file: together the two would pass GitHub's 95 MB file limit.
    app_fh = open(out / APP_FRAGMENTS, "w", encoding="utf-8", newline="\n")
    src_fh = open(out / "SOURCES.jsonl", "w", encoding="utf-8", newline="\n")
    rows, failures, quarantine = [], [], []
    stats = Counter()
    by_era = defaultdict(Counter)
    check = Counter()
    used_hash_checks = Counter()
    written_sources = set()
    ocr_maps = {}
    measured = defaultdict(Counter)  # input kind -> segmentation outcome per candidate copy tried

    def input_kind(c):
        return "app_transcription_job" if c.extra.get("fallback_only") else f"{c.origin.split(':', 1)[0]}:{c.grade}"

    def select_key(q, c):
        # Usable and identity-clean first; then any non-fallback copy before an APP transcription; then quality.
        return (q[0], q[1], 0 if c.extra.get("fallback_only") else 1) + tuple(q[2:])

    for n_done, iid in enumerate(chosen, 1):
        tried = []
        best = None
        best_key = None
        settled = False
        uyear = (dates.get(iid) or "")[:4]
        uyear = int(uyear) if uyear.isdigit() else None
        ordered = sorted(cands[iid], key=lambda c: (c.rank, c.extra.get("variant_rank", 0), c.locator))
        for cand in ordered:
            if settled and not measure_all:
                break
            try:
                text, starts = loader.load(cand)
            except Exception as exc:  # noqa: BLE001
                measured[input_kind(cand)]["load_error"] += 1
                if not settled:
                    tried.append(f"{cand.grade}:load_error:{type(exc).__name__}")
                continue
            loc, seg, evidence = try_candidate(cand, text, uyear)
            if loc is None:
                measured[input_kind(cand)]["not_located:" + re.sub(r"_(?:\d|[A-Z]).*$", "", seg)] += 1
                if not settled:
                    tried.append(f"{cand.grade}:{seg}")
                continue
            q = quality(seg, loc, cand)
            state = ("good" if q[2] else "partial") if q[0] else "unusable"
            if q[0] and not q[1]:
                state = "identity_doubt"
            measured[input_kind(cand)][state] += 1
            if settled:
                continue  # measuring only; the selection is already made
            tried.append(f"{cand.grade}:segmented:{state}" + (f"({';'.join(seg['warnings'])})" if state != "good" else ""))
            key = select_key(q, cand)
            if best is None or key > best_key:
                best, best_key = (q, cand, text, starts, loc, seg, evidence), key
            if q[0] and q[1] and q[2]:
                settled = True  # best-ranked good copy wins
        if best is None or not best[0][0]:
            failures.append({"instrument_id": iid, "era": era.get(iid, "unknown"), "candidates": len(ordered),
                             "best_source_url": best[1].url if best else "", "attempts": " | ".join(tried)})
            stats["orders_not_segmented"] += 1
            continue
        q, cand, text, starts, loc, seg, evidence = best
        transcription = bool(cand.extra.get("transcription_based"))
        doubts = identity_problems(seg["warnings"])
        if doubts:
            quarantine.append({
                "instrument_id": iid, "era": era.get(iid, "unknown"),
                "in_provisional_3359": "yes" if iid in provisional else "no",
                "reasons": ";".join(doubts), "source_grade": cand.grade, "url": cand.url, "sha256": cand.sha256,
                "route": cand.route, "signature_line": evidence.get("signature_line") or "",
                "document_year": evidence.get("document_year") or "", "universe_year": uyear or "",
                "units_found": len(seg["clauses"]),
                "heading_preview": " ".join(text[loc.doc_start:loc.body_start].split())[:160],
                "attempts": " | ".join(tried),
            })
            stats["orders_identity_quarantined"] += 1
            continue
        good = bool(q[2])
        span = text[loc.doc_start:loc.doc_end]
        off = loc.doc_start
        sid = f"cd-{cand.origin.replace(':', '-')}-{safe_id(cand.number)}-{cand.sha256[:10]}"
        text_rel = f"texts/{sid}.txt"
        with open(out / text_rel, "w", encoding="utf-8", newline="") as fh:
            fh.write(span)
        if cand.origin == "opus_zip":
            used_hash_checks[cand.extra.get("member_hash_check", "unknown")] += 1
        # FR pages for old scanned issues: candidate page numbers read from the OCR text
        ocr = None
        if cand.origin == "opus_zip" and cand.grade == "official_fr_scan_ocr_text":
            if cand.locator not in ocr_maps:
                ocr_maps = {cand.locator: SRC.ocr_page_map(text)}
            ocr = ocr_maps[cand.locator]
        issue_y = SRC.issue_year(cand.url)

        def item_for(a_abs, b_abs):
            if starts:
                return page_label(cand, starts, 0, a_abs, b_abs) or cand.page_or_item
            if ocr:
                lab = SRC.ocr_page_label(ocr[0], ocr[1], a_abs, b_abs, issue_y, SRC.first_pdf_page(cand.locator))
                if lab:
                    return f"{cand.page_or_item}: {lab}"
            return cand.page_or_item
        doc_item = item_for(loc.doc_start, loc.doc_end)
        if ocr and ocr[1] is not None:
            stats["ocr_fragments_with_candidate_fr_page"] += 1
        if sid not in written_sources:
            written_sources.add(sid)
            if cand.bytes is None:
                stats["source_records_bytes_unknown"] += 1
            src_fh.write(json.dumps({
                "source_id": sid,
                "instrument_ids": [iid],
                "url": cand.url,
                "sha256": cand.sha256,
                "bytes": cand.bytes,
                "content_type": cand.content_type,
                "retrieved_utc": cand.retrieved_utc,
                "route": cand.route,
                "page_or_item": doc_item,
                "text_path": text_rel,
                "cache_path": None,
                "notes": (
                    f"grade={cand.grade}. Saved text is the located document span (chars {loc.doc_start}-{loc.doc_end}) of "
                    + ("the pypdf text layer with FR page furniture lines removed" if cand.origin == "stage21" else f"{cand.locator}")
                    + f". {cand.notes}."
                    + (f" Zip text member vs meta text hash: {cand.extra.get('member_hash_check')}." if cand.origin == "opus_zip" else "")
                    + " Clause drafting only; authenticity not verified."
                ),
            }, ensure_ascii=False) + "\n")
        base_ref = {"url": cand.url, "sha256": cand.sha256, "page_or_item": doc_item}
        clauses = []
        for c in seg["clauses"]:
            a, b = c["start"] - off, c["end"] - off
            clause_text = span[a:b]
            check["clauses_checked"] += 1
            ok = clause_text == text[c["start"]:c["end"]] and clause_text in span and bool(clause_text.strip())
            check["exact_substring_ok" if ok else "exact_substring_FAILED"] += 1
            item = f"{item_for(c['start'], c['end'])}; {c['label']}"
            entry = {
                "scope_id": c["scope_id"],
                "label": c["label"],
                "heading": c["heading"],
                "clause_kind": c["clause_kind"],
                "related_orders": c["related_orders"],
                "original_operative_text": clause_text,
                "original_source": {"url": cand.url, "sha256": cand.sha256, "page_or_item": item},
                "text_offsets": {"text_path": text_rel, "start": a, "end": b},
                "contains_page_furniture": c["contains_page_furniture"],
                "state_at_cutoff": None,
                "first_end": None,
                "current_predicate": None,
                "later_events": [],
                "needs_judgment": list(NEEDS_JUDGMENT),
                "draft_status": "machine_draft_unverified",
            }
            if c["contains_page_furniture"]:
                entry["reading_text"] = S.reading_text(span, a, b)
            clauses.append(entry)
            stats[f"kind:{c['clause_kind']}"] += 1
            rows.append({
                "instrument_id": iid, "scope_id": c["scope_id"], "label": c["label"], "clause_kind": c["clause_kind"],
                "heading": c["heading"] or "",
                "related_orders": ";".join(f"{r['instrument_id']}({r['role']})" for r in c["related_orders"]),
                "era": era.get(iid, "unknown"), "in_provisional_3359": "yes" if iid in provisional else "no",
                "structure": seg["structure"], "segmentation_quality": "good" if good else "partial",
                "source_grade": cand.grade, "source_id": sid,
                "url": cand.url, "sha256": cand.sha256, "page_or_item": item,
                "text_path": text_rel, "start": a, "end": b, "chars": b - a,
                "contains_page_furniture": "yes" if c["contains_page_furniture"] else "no",
                "segmentation_warnings": ";".join(seg["warnings"]),
                "text_preview": " ".join(clause_text.split())[:PREVIEW_CHARS],
            })
        alternates = []
        seen_alt = {(cand.url, cand.sha256)}
        for o in ordered:
            if (o.url, o.sha256) in seen_alt:
                continue
            seen_alt.add((o.url, o.sha256))
            alternates.append({"url": o.url, "sha256": o.sha256, "page_or_item": o.page_or_item, "grade": o.grade})
        nonop = [{"kind": "title_and_heading", "text": span[0:loc.body_start - off]}]
        nonop += [{"kind": "recital", "text": span[r["start"] - off:r["end"] - off]} for r in seg["recitals"]]
        excluded = [{"kind": "signature_date_and_filing_block", "text": span[loc.body_end - off:]}]
        frag = {
            "instrument_id": iid,
            "kind": "operative_clauses",
            "data": clauses,
            "sources": [base_ref],
            "confidence_note": (
                ("TRANSCRIPTION-BASED: clause texts come from an American Presidency Project transcription "
                 "(app-executive-orders), not an official edition; check every clause against the official original. "
                 if transcription else "")
                + f"Machine DRAFT from a {cand.grade} copy; structure '{seg['structure']}', {len(clauses)} units; "
                + (f"warnings: {', '.join(seg['warnings'])}; " if seg["warnings"] else "")
                + ("no structural problems detected by the automatic checks (heading, body and signature found; "
                   "no unsplit section markers or over-long units); " if good
                   else "segmentation PARTIAL: see segmentation_warnings; ")
                + "boundaries, kinds, targets and completeness are unverified leads; every state field needs human judgment."
            ),
            "produced_by": JOB,
            "source_id": sid,
            "source_grade": cand.grade,
            "structure": seg["structure"],
            "segmentation_quality": "good" if good else "partial",
            "segmentation_warnings": seg["warnings"],
            "identity_evidence": {
                "basis": cand.extra.get("identity_basis") or ("heading_in_text" if loc.heading_style != "body_only" else "input_record"),
                "signature_line": evidence.get("signature_line"),
                "document_year": evidence.get("document_year"),
                "universe_year": uyear,
            },
            "non_operative": nonop,
            "excluded": excluded,
            "alternate_sources": alternates,
            "era": era.get(iid, "unknown"),
        }
        if transcription:
            frag.update(transcription_based=True, representation_type="secondary_compilation_transcription",
                        acceptable_as_original=False)
            stats["fragments_from_app_transcription"] += 1
            stats[f"app_quality:{'good' if good else 'partial'}"] += 1
        (app_fh if transcription else frag_fh).write(json.dumps(frag, ensure_ascii=False) + "\n")
        stats["fragments_written"] += 1
        stats["clauses_total"] += len(clauses)
        stats[f"grade:{cand.grade}"] += 1
        stats[f"structure:{seg['structure']}"] += 1
        stats[f"quality:{'good' if good else 'partial'}"] += 1
        e = era.get(iid, "unknown")
        by_era[e]["orders"] += 1
        by_era[e]["clauses"] += len(clauses)
        by_era[e]["good" if good else "partial"] += 1
        if n_done % 200 == 0:
            log(f"  {n_done}/{len(chosen)} orders processed")
    frag_fh.close()
    app_fh.close()
    src_fh.close()
    loader.close()

    fields = ["instrument_id", "scope_id", "label", "clause_kind", "heading", "related_orders", "era", "in_provisional_3359",
              "structure", "segmentation_quality", "source_grade", "source_id", "url", "sha256", "page_or_item", "text_path",
              "start", "end", "chars", "contains_page_furniture", "segmentation_warnings", "text_preview"]
    with open(out / "CLAUSES.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    with open(out / "NOT_SEGMENTED.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["instrument_id", "era", "candidates", "best_source_url", "attempts"])
        w.writeheader()
        w.writerows(failures)
    qfields = ["instrument_id", "era", "in_provisional_3359", "reasons", "source_grade", "url", "sha256", "route",
               "signature_line", "document_year", "universe_year", "units_found", "heading_preview", "attempts"]
    with open(out / "IDENTITY_QUARANTINE.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=qfields)
        w.writeheader()
        w.writerows(quarantine)
    with open(out / "INPUT_PROBLEMS.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["instrument_id_or_input", "problem", "detail"])
        w.writerows(problems)

    # Independent re-check from the files just written (not from memory).
    recheck = Counter()
    for name in ("FRAGMENTS.jsonl", APP_FRAGMENTS):
        with open(out / name, encoding="utf-8") as fh:
            for line in fh:
                f = json.loads(line)
                for c in f["data"]:
                    with open(out / c["text_offsets"]["text_path"], encoding="utf-8", newline="") as tf:
                        saved = tf.read()
                    o = c["text_offsets"]
                    good = saved[o["start"]:o["end"]] == c["original_operative_text"] and c["original_operative_text"] in saved
                    recheck["ok" if good else "FAILED"] += 1
    reasons = Counter(re.sub(r"_(?:\d|[A-Z]).*$", "", r) for q in quarantine for r in q["reasons"].split(";"))
    summary = {
        "job": JOB,
        "generated_utc": now_utc(),
        "legal_cutoff": LEGAL_CUTOFF,
        "job_limit": limit,
        "job_ids": sorted(only) or None,
        "inputs": {
            "availability": input_status,
            "allow_partial_inputs": allow_partial,
            "stage21_pdfs_usable": len(s21),
            "opus_zip": opus_stats,
            "other_jobs": job_seen,
            "app_transcriptions": app_seen if use_app else "off (CLAUSE_APP_INPUT=0)",
            "input_problems": len(problems),
        },
        "orders_in_universe": len(universe),
        "orders_with_candidate_text": len(order_ids),
        "orders_processed": len(chosen),
        "fragments_written": stats["fragments_written"],
        "orders_not_segmented": stats["orders_not_segmented"],
        "orders_identity_quarantined": stats["orders_identity_quarantined"],
        "identity_quarantine_reasons": dict(reasons),
        "clauses_total": stats["clauses_total"],
        "segmentation_quality": {k.split(":", 1)[1]: v for k, v in stats.items() if k.startswith("quality:")},
        "by_source_grade": {k.split(":", 1)[1]: v for k, v in stats.items() if k.startswith("grade:")},
        "fragments_from_app_transcription": stats["fragments_from_app_transcription"],
        "app_transcription_quality": {k.split(":", 1)[1]: v for k, v in stats.items() if k.startswith("app_quality:")},
        "segmentation_outcomes_by_input": {
            "measured_every_candidate": measure_all,
            "note": ("one count per candidate copy tried; with measured_every_candidate false, copies after the first "
                     "good one are not tried, so fallback inputs are only measured where nothing better was good"),
            "by_input": {k: dict(sorted(v.items())) for k, v in sorted(measured.items())},
        },
        "by_structure": {k.split(":", 1)[1]: v for k, v in stats.items() if k.startswith("structure:")},
        "by_clause_kind": {k.split(":", 1)[1]: v for k, v in stats.items() if k.startswith("kind:")},
        "by_era": {k: dict(v) for k, v in sorted(by_era.items())},
        "source_records_written": len(written_sources),
        "source_records_bytes_unknown": stats["source_records_bytes_unknown"],
        "ocr_fragments_with_candidate_fr_page": stats["ocr_fragments_with_candidate_fr_page"],
        "self_check": {
            "clauses_checked": check["clauses_checked"],
            "original_operative_text_is_exact_substring_of_saved_text": check["exact_substring_ok"],
            "failures": check["exact_substring_FAILED"],
            "recheck_from_written_files_ok": recheck["ok"],
            "recheck_from_written_files_failed": recheck["FAILED"],
            "opus_text_member_sha256_vs_meta_text_hash_for_sources_used": dict(used_hash_checks),
            "passed": check["exact_substring_FAILED"] == 0 and recheck["FAILED"] == 0,
        },
        "seconds": round(time.time() - t0, 1),
        "what_this_is_not": "Draft clause boundaries from saved texts. Not legal conclusions; no status, ledger or count is changed.",
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    log("")
    log("Summary")
    log(f"  Orders with a saved text found: {len(order_ids)}; processed: {len(chosen)}")
    log(f"  Draft clause inventories written: {stats['fragments_written']} "
        f"({summary['segmentation_quality'].get('good', 0)} with no structural problems detected, "
        f"{summary['segmentation_quality'].get('partial', 0)} partial)")
    log(f"  Held back because the text may be a different order: {stats['orders_identity_quarantined']} (see IDENTITY_QUARANTINE.csv)")
    log(f"  Orders whose text could not be split: {stats['orders_not_segmented']} (see NOT_SEGMENTED.csv)")
    log(f"  Drafts from APP transcriptions (fallback, transcription-based): {stats['fragments_from_app_transcription']}")
    log(f"  Clauses: {stats['clauses_total']}; by era: " + ", ".join(f"{k}: {v['orders']} orders/{v['clauses']} clauses" for k, v in summary["by_era"].items()))
    log(f"  Self-check: {check['exact_substring_ok']}/{check['clauses_checked']} clause texts are exact substrings of the saved text"
        f" (re-check from files: {recheck['ok']} ok, {recheck['FAILED']} failed); zip text vs meta hash: {dict(used_hash_checks)}")
    log("  These are DRAFTS for human review: no provisional status, ledger or count was changed.")
    if not summary["self_check"]["passed"]:
        log("ERROR: self-check failed")
        sys.exit(1)

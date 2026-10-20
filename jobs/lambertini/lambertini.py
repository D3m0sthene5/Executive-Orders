#!/usr/bin/env python3
"""LAMBERTINI: shared savings readings and recorded counterevidence searches (zero-agent part).

Named for Prospero Lambertini (Benedict XIV), who formalized the devil's advocate's search for
counterevidence.  Design: research/plans/LAMBERTINI_DESIGN.md.  Standard library only.

  python3 -I jobs/lambertini/lambertini.py build [--repo R] [--output DIR]
  python3 -I jobs/lambertini/lambertini.py probe --pool LAMBS|LAMBC --n 20 --seed TEXT --out DIR [--repo R] [--output DIR]

`build` writes, under jobs/lambertini/output/ (or --output):
  SAVINGS_PACKETS.jsonl     one per acting EO whose held official text ends >= 1 decided NO order: the text's
                            source (url, sha256, page), the sha256 of the held text file, every savings-type and
                            transfer-type phrase with character offsets, and for each target the offsets where
                            the acting text names it.  ONE reading of this packet serves every order it ends.
  SAVINGS_PREFILL.csv       one per decided order with a draft: its savings class (S0..S9 / Y0..Y9), the packet,
                            and a suggested state that is a PREFILL A READER CONFIRMS, never a closure.
  COUNTEREVIDENCE_RECORDS.jsonl  one per decided not-ready order whose counterevidence is open because it has no
                            OFR catalog entry: a claim-shaped DRAFT later_source_search that states what was
                            searched, its coverage, every lead found and what was NOT searched.
  POOL_LAMBS.txt / POOL_LAMBC.txt   the probe pools (ids, one per line) for Llull's ids_file.
  SUMMARY.json   (STATUS.json is written by the Actions runner)
`probe` draws a seeded random batch from a pool and writes PROBE_BATCH.json with each order's packet/record.

Nothing here is a legal conclusion.  It writes no claim, no EXHAUSTED line, no status, no tier; it never changes
the codebook or the certified count (0).  A savings phrase is a lead; its absence is a lead.
"""
import argparse, collections, csv, hashlib, json, os, random, re, subprocess, sys, datetime

sys.dont_write_bytecode = True
csv.field_size_limit(1 << 28)

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_REPO = os.path.dirname(os.path.dirname(HERE))
SCHEMA = "lambertini/1"
NUMBERED_SERIES_1937 = 7532   # first EO in the OFR catalog
WINDOW = 1500                 # characters either side of a target mention ("near")

P = {
    "readiness": "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv",
    "drafts": "jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl",
    "fr_fragments": "jobs/fr-originals/data/full_run/FRAGMENTS.jsonl",
    "fr_dir": "jobs/fr-originals/data/full_run",
    "claims_glob": "research/readiness/claims",
    "le_edges": "jobs/later-events/output/EDGES.csv",
    "le_scan": "jobs/later-events/output/TEXT_SCAN_LOG.csv",
    "le_status": "jobs/later-events/output/STATUS.json",
    "cl_orders": "jobs/current-law/output/ORDERS_CURRENT_LAW.csv",
    "cl_status": "jobs/current-law/output/STATUS.json",
    "wpa": "jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv",
}

SAVINGS_RE = re.compile(
    r"shall not (?:be construed to )?(?:affect|impair|abate)|savings? (?:clause|provision)|"
    r"heretofore (?:taken|issued|prescribed|made|granted)|shall (?:remain|continue) in (?:full )?(?:force|effect)|"
    r"pending (?:proceedings|actions|suits|matters|cases)|rights? (?:accrued|vested|already acquired)|"
    r"without prejudice to|shall continue to be (?:valid|effective)|until (?:modified|superseded|revoked)", re.I)
TRANSFER_RE = re.compile(
    r"transfer(?:red|s)?\b|abolish|wind(?:ing)? up|liquidat|records,? property|unexpended balances|"
    r"personnel|incumbent|shall not apply to|except(?:ing)? (?:that|as)", re.I)
CONTRARY_MECH = {"reinstatement", "continuation", "extension", "ratification"}
WPA_REVOKE_RE = re.compile(r"revok|rescind|supersed|amend|abolish|terminat|annul|void", re.I)
MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
          "aug": 8, "sept": 9, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
RULES = ["prefills and draft search records are leads a reader confirms; nothing here closes a step",
         "writes no claim, EXHAUSTED line, status or tier; codebook unchanged; certified stays 0",
         "AI statuses are hypotheses"]


# ------------------------------------------------------------------ small helpers
def rp(repo, key):
    return os.path.join(repo, P[key])


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def jsonl(path):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git_head(repo):
    try:
        return subprocess.run(["git", "-C", repo, "rev-parse", "--short=9", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return None


def eo_number(iid):
    """'EO:1234' -> 1234, 'EO:1234-A' -> 1234, otherwise None."""
    m = re.match(r"EO:(\d+)(?:-?[A-Z]{1,2})?$", iid or "")
    return int(m.group(1)) if m else None


def job_date(repo, key):
    try:
        with open(rp(repo, key), encoding="utf-8") as fh:
            s = json.load(fh)
        return (s.get("finished_utc") or s.get("started_utc") or "")[:10] or None
    except Exception:
        return None


# ------------------------------------------------------------------ pure text logic (tested)
def mention_spans(text, number):
    """Character spans where `number` appears as a whole token.  `strict` when an order word precedes it."""
    out = []
    for m in re.finditer(r"(?<![\d.,])" + re.escape(str(number)) + r"(?![\d])", text):
        before = text[max(0, m.start() - 200):m.start()]
        # an order word, then nothing but a list of numbers (with dates) up to this number
        strict = bool(re.search(r"(?:Orders?|E\.\s?O\.|Ex\.\s?Ords?\.|Nos?\.)\s*"
                                r"(?:[\dA-Z\-]+(?:\s+of\s+[A-Z][a-z]+\.?\s+\d{1,2},\s+\d{4})?\s*(?:,|;|and|or)\s*)*$",
                                before))
        out.append({"start": m.start(), "end": m.end(), "strict": strict})
    return out


def phrase_spans(text, rx):
    return [{"start": m.start(), "end": m.end(), "phrase": m.group(0)} for m in rx.finditer(text)]


def near(spans, mentions, window=WINDOW):
    return any(abs(s["start"] - m["start"]) <= window for s in spans for m in mentions)


def classify_no(info):
    """Savings class for a provisional-NO order (see LAMBERTINI_DESIGN.md).  `info` keys: actors (set),
    acting_held, named, savings_anywhere, savings_near, transfer_near, own_transfer, own_lead, conflict."""
    actors = info["actors"]
    if not actors:
        return "S9_no_end_candidate", "wait_for_ending"
    if len(actors) > 1:
        return "S9_multiple_acting", "review"
    a = next(iter(actors))
    if not (isinstance(a, str) and a.startswith("EO:")):
        return "S8_acting_not_EO", "review"
    if not info["acting_held"]:
        return "S8_acting_text_not_held", "fetch_acting_text"
    if not info["named"]:
        return "S8_acting_text_does_not_name_order", "review"
    if info["conflict"]:
        return "S4_conflict", "review"
    if info["own_lead"]:
        return "S3_own_savings_lead", "review"
    if info["savings_near"]:
        return "S2_savings_phrase_near", "review"
    if info["savings_anywhere"]:
        return "S2b_savings_phrase_elsewhere_in_acting", "review"
    if info["transfer_near"] or info["own_transfer"]:
        return "S1_transfer_wording", "review"
    return "S0_none_candidate", "none_after_bounded_search"


def classify_yes(info):
    if info["conflict"]:
        return "Y4_conflict", "review"
    if info["own_lead"]:
        return "Y3_own_savings_lead", "review"
    if info["later_events"]:
        return "Y1_later_events", "review"
    return "Y0_no_later_events", "none_after_bounded_search"


def parse_wpa_date(year, month_day):
    m = re.match(r"([A-Za-z]+)\.?\s*(\d{1,2})", (month_day or "").strip())
    if not m or not str(year).isdigit():
        return None
    mon = MONTHS.get(m.group(1).lower().rstrip("."))
    return (int(year), mon, int(m.group(2))) if mon else None


def wpa_date_regex(d):
    """Matches 'Mar. 28, 1917' / 'March 28,1917' style mentions of date d=(y,m,day) in OCR text."""
    names = [k for k, v in MONTHS.items() if v == d[1]]
    alt = "|".join(sorted({n[:3] for n in names} | set(names), key=len, reverse=True))
    return re.compile(r"\b(?:%s)[a-z]*\.?\s*%d\s*,\s*%d\b" % (alt, d[2], d[0]), re.I)


def names_number(text, number):
    """WPA OCR cites orders as 'E. O. 36', 'E. 0. [9]' or 'E. 0.s [983 and 1624]': look for the number in the
    short span after each such cite, before any ' of ' date."""
    for m in re.finditer(r"E\.\s?[O0]\.(?:s|\'s)?", text):
        seg = text[m.end():m.end() + 40].split(" of ")[0]
        if re.search(r"(?<![\d.])%d(?![\d])" % number, seg):
            return True
    return False


def wpa_leads(target_id, target_num, target_date, entries):
    """WPA 1944 list entries after the target that name it (by 'E. O. N' or by its date) next to an
    ending/changing word.  Leads only: WPA summaries are a finding aid, never an original."""
    out = []
    date_rx = wpa_date_regex(target_date) if target_date else None
    for e in entries:
        if e["id"] == target_id:
            continue
        n = eo_number(e["id"])
        if target_num and n is not None and n <= target_num:
            continue
        t = e.get("text") or ""
        hit = None
        if target_num and names_number(t, target_num):
            hit = "number"
        elif date_rx and date_rx.search(t) and WPA_REVOKE_RE.search(t):
            hit = "date_with_change_word"
        if hit:
            out.append({"wpa_entry": e["id"], "page": e.get("page"), "match": hit,
                        "change_word": bool(WPA_REVOKE_RE.search(t)), "text": t[:300]})
    return out


def scan_coverage(target_num, scanned_numbers):
    """Share of numbered EOs after the target and before the OFR catalog (7532) whose text later-events scanned."""
    if target_num is None or target_num >= NUMBERED_SERIES_1937:
        return None
    window = range(target_num + 1, NUMBERED_SERIES_1937)
    held = sum(1 for n in window if n in scanned_numbers)
    return {"numbered_orders_after_it_before_1937": len(window), "texts_scanned": held,
            "share": round(held / len(window), 4) if len(window) else 1.0}


# ------------------------------------------------------------------ build
def load_texts(repo):
    txt = {}
    for f in jsonl(rp(repo, "fr_fragments")) or []:
        d = f.get("data") or {}
        if f.get("kind") == "original_representation" and d.get("needs_page_check") is False and d.get("text_path"):
            p = os.path.join(rp(repo, "fr_dir"), d["text_path"])
            if os.path.exists(p):
                txt[f["instrument_id"]] = {"path": p, "rel": os.path.relpath(p, repo), "url": d.get("url"),
                                           "source_sha256": d.get("sha256"), "page_or_item": d.get("page_or_item"),
                                           "signing_date": d.get("signing_date")}
    return txt


def load_claims(repo):
    claims, base = {}, os.path.join(repo, P["claims_glob"])
    if os.path.isdir(base):
        for fn in sorted(os.listdir(base)):
            if fn.endswith(".jsonl"):
                for c in jsonl(os.path.join(base, fn)):
                    if c.get("instrument_id"):
                        claims[c["instrument_id"]] = c
    return claims


def build(repo, out):
    rows = {r["instrument_id"]: r for r in read_csv(rp(repo, "readiness"))}
    if not rows:
        raise SystemExit("readiness tracker output missing: %s" % P["readiness"])
    texts = load_texts(repo)
    claims = load_claims(repo)
    decided = {i for i, r in rows.items() if r.get("provisional_status") in ("yes", "no")}

    # ---- per-order facts from drafts
    facts = {}
    for c in jsonl(rp(repo, "drafts")) or []:
        i = c.get("instrument_id")
        if i not in decided:
            continue
        d = c.get("_draft") or {}
        p = d.get("proposals") or {}
        ends = p.get("whole_order_end") or []
        facts[i] = {"status": d.get("provisional_status") or rows[i]["provisional_status"],
                    "actors": {e.get("proposal", {}).get("actor") for e in ends if e.get("proposal")},
                    "end": [e.get("proposal") for e in ends][:3],
                    "own_lead": bool(p.get("savings_leads")), "conflict": bool(d.get("conflicts")),
                    "later_events": bool(p.get("later_events"))}

    # ---- packets per acting EO
    by_actor = collections.defaultdict(list)
    for i, f in facts.items():
        if f["status"] == "no" and len(f["actors"]) == 1:
            a = next(iter(f["actors"]))
            if isinstance(a, str) and a.startswith("EO:"):
                by_actor[a].append(i)
    packets, per_target = {}, {}
    for a in sorted(by_actor):
        if a not in texts:
            continue
        t = texts[a]
        with open(t["path"], encoding="utf-8", errors="ignore") as fh:
            body = fh.read()
        sav, tra = phrase_spans(body, SAVINGS_RE), phrase_spans(body, TRANSFER_RE)
        targets = {}
        for i in sorted(by_actor[a]):
            n = eo_number(i)
            ms = mention_spans(body, n) if n is not None else []
            strict = any(m["strict"] for m in ms)
            # a short number (e.g. 36) also matches page numbers and dates: count it only after an order word
            info = {"named": strict or (bool(ms) and n >= 1000), "named_strict": strict,
                    "mentions": [[m["start"], m["end"]] for m in ms[:10]],
                    "savings_near": near(sav, ms), "transfer_near": near(tra, ms)}
            targets[i] = info
            per_target[i] = dict(info, savings_anywhere=bool(sav))
        packets[a] = {"schema": SCHEMA, "packet_id": "LSP:" + a, "acting_id": a,
                      "text": {"repo_path": t["rel"], "text_sha256": sha256_file(t["path"]), "chars": len(body),
                               "source_url": t["url"], "source_sha256": t["source_sha256"],
                               "page_or_item": t["page_or_item"], "signing_date": t["signing_date"]},
                      "savings_phrases": [dict(s, context=body[max(0, s["start"] - 200):s["end"] + 200]) for s in sav],
                      "transfer_phrases": [[s["start"], s["end"], s["phrase"]] for s in tra],
                      "targets": targets, "target_count": len(targets),
                      "reader_question": "Does any provision of this acting order save, continue, transfer or "
                                         "preserve anything done, accrued or pending under the orders it ends? Answer "
                                         "once with section/page pin; then per target only whether it falls in an "
                                         "exception."}

    # ---- own-text transfer wording of the ended order itself
    def own_transfer(i):
        if i not in texts:
            return False
        with open(texts[i]["path"], encoding="utf-8", errors="ignore") as fh:
            return bool(TRANSFER_RE.search(fh.read()))

    prefill = []
    for i in sorted(facts, key=lambda x: (eo_number(x) or 0, x)):
        f, r = facts[i], rows[i]
        if f["status"] == "no":
            pt = per_target.get(i, {})
            a = next(iter(f["actors"])) if len(f["actors"]) == 1 else None
            info = {"actors": f["actors"], "acting_held": a in texts if a else False,
                    "named": pt.get("named", False), "savings_anywhere": pt.get("savings_anywhere", False),
                    "savings_near": pt.get("savings_near", False), "transfer_near": pt.get("transfer_near", False),
                    "own_transfer": own_transfer(i), "own_lead": f["own_lead"], "conflict": f["conflict"]}
            cls, sug = classify_no(info)
        else:
            a, info = None, {}
            cls, sug = classify_yes(f)
        claim = claims.get(i) or {}
        prefill.append({"instrument_id": i, "provisional_status": f["status"], "savings_class": cls,
                        "suggested_state": sug, "packet_id": ("LSP:" + a) if a in packets else "",
                        "acting_id": a or "", "named_strict": str(per_target.get(i, {}).get("named_strict", "")),
                        "own_text_transfer_wording": str(info.get("own_transfer", "")),
                        "ready_for_human_review": r.get("ready_for_human_review"),
                        "step_original_text": r.get("step_original_text"),
                        "step_clause_inventory": r.get("step_clause_inventory"),
                        "step_ending_or_current_basis": r.get("step_ending_or_current_basis"),
                        "step_savings_residuals": r.get("step_savings_residuals"),
                        "step_counterevidence": r.get("step_counterevidence"),
                        "step_opus_media": r.get("step_opus_media"),
                        "claim_savings_state": ((claim.get("savings_residuals") or {}).get("state") or "")})

    # ---- calibration: prefill vs the states written in claims of READY orders (hand-written, not certified)
    calib = collections.Counter()
    for p in prefill:
        if p["ready_for_human_review"] == "yes" and p["claim_savings_state"]:
            calib[p["savings_class"] + " -> " + p["claim_savings_state"]] += 1

    # ---- counterevidence records (no OFR catalog entry)
    scanned = {eo_number(r["acting_id"]) for r in read_csv(rp(repo, "le_scan")) if eo_number(r.get("acting_id"))}
    edges = collections.defaultdict(list)
    for e in read_csv(rp(repo, "le_edges")):
        if e.get("target_id"):
            edges[e["target_id"]].append(e)
    cl = {r["instrument_id"]: r for r in read_csv(rp(repo, "cl_orders"))}
    wpa = read_csv(rp(repo, "wpa"))
    wpa_by_id = {}
    for e in wpa:
        wpa_by_id.setdefault(e["id"], e)
    le_date, cl_date = job_date(repo, "le_status"), job_date(repo, "cl_status")
    today = datetime.date.today().isoformat()
    records = []
    for i in sorted(decided, key=lambda x: (eo_number(x) or 0, x)):
        r = rows[i]
        if r.get("ready_for_human_review") == "yes" or r.get("step_counterevidence") != "open":
            continue
        bl = r.get("blockers", "")
        if "NO_OFR_CATALOG_ENTRY" not in bl:
            continue
        n = eo_number(i)
        w = wpa_by_id.get(i)
        tdate = parse_wpa_date(w["year"], w["month_day"]) if w else None
        leads = wpa_leads(i, n, tdate, wpa) if (n or tdate) else []
        e_i = edges.get(i, [])
        contrary = [e for e in e_i if e.get("mechanism") in CONTRARY_MECH]
        clr = cl.get(i, {})
        cl_hits = sum(int(clr.get(k) or 0) for k in ("usc_mentions", "ecfr_mentions"))
        cov = scan_coverage(n, scanned)
        search = [
            {"repository": "Office of the Federal Register executive-order catalog (federalregister.gov API v1, "
                           "1937-2026), disposition notes on later catalogued orders",
             "query_or_scope": "notes on every catalogued order (1937 onward) naming %s; the order itself has no "
                               "catalog record, so its own disposition notes do not exist" % i,
             "checked_on": le_date, "searched_by": "jobs/later-events (machine search), summarized by jobs/lambertini"},
            {"repository": "project saved order texts (jobs/later-events TEXT_SCAN_LOG)",
             "query_or_scope": "revocation, amendment, supersession and reinstatement sentences naming %s; coverage "
                               "of numbered orders after it and before 1937: %s" % (
                                   i, ("%d of %d texts" % (cov["texts_scanned"], cov["numbered_orders_after_it_before_1937"]))
                                   if cov else "n/a"),
             "checked_on": le_date, "searched_by": "jobs/later-events (machine search), summarized by jobs/lambertini"},
            {"repository": "U.S. Code (OLRC) and eCFR/CFR (jobs/current-law)",
             "query_or_scope": "every citation of %s by number in statute text, notes and regulations" % i,
             "checked_on": cl_date, "searched_by": "jobs/current-law (machine search), summarized by jobs/lambertini"},
            {"repository": "WPA Historical Records Survey, Presidential Executive Orders, numbered 1-8030 (1944), "
                           "OCR parse (jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv); a finding aid",
             "query_or_scope": "summaries of later numbered orders naming %s by number, or by its date (%s) next to an "
                               "ending/changing word" % (i, "%04d-%02d-%02d" % tdate if tdate else "date unknown"),
             "checked_on": today, "searched_by": "jobs/lambertini (machine search)"},
        ]
        cls = ("C3_quarantined" if "QUARANTINED" in bl else
               "C1_contrary_or_wpa_lead" if (contrary or leads or "CONTRARY" in bl) else
               "C2_original_text_open" if r.get("step_original_text") != "done" else
               "C0_no_lead_found")
        records.append({"schema": SCHEMA, "record_id": "LCR:" + i, "instrument_id": i,
                        "provisional_status": r["provisional_status"], "counter_class": cls,
                        "draft_not_claim": True,
                        "later_source_search_draft": search,
                        "leads": {"later_events_edges": [{k: e.get(k) for k in ("edge_id", "acting_id", "mechanism",
                                                           "date_candidate", "evidence_type")} for e in e_i[:20]],
                                  "later_events_edge_count": len(e_i), "contrary_mechanism_edges": len(contrary),
                                  "current_law_mentions": cl_hits, "wpa": leads[:10], "wpa_count": len(leads)},
                        "coverage": cov,
                        "not_searched": ["texts of pre-1937 orders, proclamations and statutes not held by the project "
                                         "(see coverage)", "Statutes at Large indexes and private/special acts",
                                         "agency and departmental records", "WPA list for unnumbered orders (not scanned)"],
                        "adequacy": "owner ruling required (LAMBERTINI Q-L2): is this bounded record an adequate "
                                    "later-source search for a pre-1937 order?"})

    pool_s = [p["instrument_id"] for p in prefill if p["savings_class"] == "S0_none_candidate"
              and p["ready_for_human_review"] == "no" and p["step_savings_residuals"] == "open"
              and p["step_original_text"] == "done" and p["step_counterevidence"] == "done"]
    pool_c = [x["instrument_id"] for x in records if x["counter_class"] == "C0_no_lead_found"]

    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "SAVINGS_PACKETS.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
        for a in sorted(packets, key=lambda x: (-packets[x]["target_count"], x)):
            fh.write(json.dumps(packets[a], sort_keys=True) + "\n")
    with open(os.path.join(out, "SAVINGS_PREFILL.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(prefill[0]) if prefill else ["instrument_id"])
        w.writeheader()
        w.writerows(prefill)
    with open(os.path.join(out, "COUNTEREVIDENCE_RECORDS.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
        for x in records:
            fh.write(json.dumps(x, sort_keys=True) + "\n")
    for name, ids in (("POOL_LAMBS.txt", pool_s), ("POOL_LAMBC.txt", pool_c)):
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("".join(i + "\n" for i in ids))

    open_sav = [p for p in prefill if p["step_savings_residuals"] == "open" and p["ready_for_human_review"] == "no"]
    pk_sizes = sorted((p["target_count"] for p in packets.values()), reverse=True)
    summary = {"schema": SCHEMA, "repo_head": git_head(repo), "rules": RULES,
               "decided_orders_with_draft": len(prefill),
               "savings_open_by_class": dict(sorted(collections.Counter(p["savings_class"] for p in open_sav).items())),
               "packets": len(packets), "packet_targets": sum(pk_sizes),
               "packet_top": [[a, packets[a]["target_count"]] for a in
                              sorted(packets, key=lambda x: (-packets[x]["target_count"], x))[:10]],
               "packets_covering_half_of_targets": next((k + 1 for k in range(len(pk_sizes))
                                                         if sum(pk_sizes[:k + 1]) * 2 >= sum(pk_sizes)), 0),
               "calibration_on_ready_claims": dict(sorted(calib.items())),
               "counterevidence_records": len(records),
               "counterevidence_by_class": dict(sorted(collections.Counter(x["counter_class"] for x in records).items())),
               "pool_LAMBS": len(pool_s), "pool_LAMBC": len(pool_c)}
    with open(os.path.join(out, "SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return summary


def cmd_probe(a):
    out = a.output or os.path.join(a.repo, "jobs", "lambertini", "output")
    fn = {"LAMBS": "POOL_LAMBS.txt", "LAMBC": "POOL_LAMBC.txt"}[a.pool]
    with open(os.path.join(out, fn), encoding="utf-8") as fh:
        pool = [l.strip() for l in fh if l.strip()]
    excluded = set()
    for path in a.exclude or []:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            excluded |= set(re.findall(r"EO:[0-9A-Za-z:_-]+", fh.read()))
    pool = [i for i in pool if i not in excluded]
    rng = random.Random(hashlib.sha256(a.seed.encode()).hexdigest())
    pick = sorted(rng.sample(pool, min(a.n, len(pool))), key=lambda x: (eo_number(x) or 0, x))
    pre = {r["instrument_id"]: r for r in read_csv(os.path.join(out, "SAVINGS_PREFILL.csv"))}
    packets = {p["packet_id"]: p for p in jsonl(os.path.join(out, "SAVINGS_PACKETS.jsonl"))}
    recs = {x["instrument_id"]: x for x in jsonl(os.path.join(out, "COUNTEREVIDENCE_RECORDS.jsonl"))}
    items = []
    for i in pick:
        p = pre.get(i, {})
        pk = packets.get(p.get("packet_id"))
        items.append({"instrument_id": i, "prefill": p,
                      "packet": ({k: pk[k] for k in ("packet_id", "acting_id", "text", "savings_phrases",
                                                     "transfer_phrases", "target_count")} |
                                 {"this_target": pk["targets"].get(i)}) if pk else None,
                      "counterevidence_record": recs.get(i)})
    os.makedirs(a.out, exist_ok=True)
    batch = {"schema": SCHEMA, "pool": a.pool, "pool_size": len(pool), "n": len(pick), "seed": a.seed,
             "excluded_files": a.exclude or [], "excluded_ids": len(excluded),
             "draw": "random.Random(sha256(seed)).sample(pool, n)", "repo_head": git_head(a.repo), "items": items}
    with open(os.path.join(a.out, "PROBE_BATCH_%s.json" % a.pool), "w", encoding="utf-8") as fh:
        json.dump(batch, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps({"pool": a.pool, "pool_size": len(pool), "drawn": pick}))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="lambertini", description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--output", default=None, help="default <repo>/jobs/lambertini/output")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    for name in ("probe", "continue"):
        s = sub.add_parser(name)
        s.add_argument("--pool", choices=["LAMBS", "LAMBC"], required=True)
        s.add_argument("--n", type=int, default=20)
        s.add_argument("--seed", required=True)
        s.add_argument("--out", required=True)
        s.add_argument("--exclude", action="append", help="file whose EO ids are left out (other workflows' batches)")
        if name == "continue":
            s.add_argument("--gate-contract", required=True)
            s.add_argument("--gate-observation", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "build":
        out = a.output or os.path.join(a.repo, "jobs", "lambertini", "output")
        print(json.dumps(build(a.repo, out), indent=1))
    elif a.cmd == "continue":
        # Scale/continuation must use the frozen probe contract, including every
        # planted test. An incomplete test never becomes a pass by omission.
        import importlib.util
        from pathlib import Path
        module_path = Path(__file__).resolve().parents[1] / "llull" / "gates.py"
        spec = importlib.util.spec_from_file_location("lambertini_gates", module_path)
        gates = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gates)
        try:
            contract = json.loads(Path(a.gate_contract).read_text())
            observation = json.loads(Path(a.gate_observation).read_text())
            receipt = gates.evaluate_gate(contract, observation)
            errors = gates.verify_evidence(observation, a.repo)
            if errors:
                receipt.update(status="untested", may_continue=False, evidence_errors=errors)
        except (OSError, ValueError, TypeError) as exc:
            receipt = {"status":"untested", "may_continue":False, "error":str(exc)}
        os.makedirs(a.out, exist_ok=True)
        receipt_path = Path(a.out) / "CONTINUATION_GATE.json"
        if receipt_path.exists():
            raise ValueError("continuation output already contains a gate receipt; use a new output directory")
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        if not receipt["may_continue"]:
            print(json.dumps(receipt, sort_keys=True))
            return 5
        cmd_probe(a)
    else:
        cmd_probe(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Numbered-series crosswalk: which independent listings name each numbered executive-order label.

Run from the repo root:  python3 -I research/petty-census-closure-2026-11-24/crosswalk/crosswalk.py [REPO_ROOT] [OUT_DIR]
Reads held files only (no network). Deterministic: same inputs, same bytes out.
Writes NUMBERED_CROSSWALK.csv, SOURCES.csv, EXCEPTIONS.csv, ABSENT_NUMBERS.csv,
DATE_CONFLICTS.csv, SUMMARY.json into OUT_DIR (REPORT.md is written separately).
"""
import bisect, collections, csv, datetime, glob, gzip, hashlib, json, os, re, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
OUT = sys.argv[2] if len(sys.argv) > 2 else "research/petty-census-closure-2026-11-24/crosswalk"
MAXN = 14435
CONFLICT_CAP = 1000  # detail rows per conflict type; all conflicts are counted

csv.field_size_limit(10 ** 9)


def P(*a):
    return os.path.join(ROOT, *a)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rd(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def norm(raw):
    """'EO:7677-A' / 'Executive Order 7677-A' / '130A' -> (number:int, suffix) or None."""
    s = (raw or "").strip()
    s = re.sub(r"^(EO:|Executive Order( No\.)?\s*)", "", s)
    m = re.match(r"^(\d+)(.*)$", s)
    if not m:
        return None
    suf = m.group(2).strip()
    if re.match(r"^-[A-Za-z]$", suf):
        suf = suf[1:]
    return int(m.group(1)), (suf.upper() if re.match(r"^[A-Za-z]$", suf) else suf)


def label(k):
    return "EO:%d%s" % k


MONTHS = {m: i + 1 for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split())}


def wpa_date(year, md):
    m = re.match(r"^\s*([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2})\s*$", md or "")
    if not m or m.group(1).lower() not in MONTHS or not (year or "").isdigit():
        return None
    try:
        return datetime.date(int(year), MONTHS[m.group(1).lower()], int(m.group(2)))
    except ValueError:
        return None


def iso(s):
    try:
        return datetime.date.fromisoformat((s or "").strip()[:10])
    except ValueError:
        return None


SRC = collections.OrderedDict()
HITS = collections.defaultdict(lambda: collections.defaultdict(int))
DATES = collections.defaultdict(lambda: collections.defaultdict(set))
UNPARSED = collections.Counter()


def reg(col, kind, family, what, paths, independence, note=""):
    SRC[col] = dict(column=col, kind=kind, family=family, what=what, paths=paths, independence=independence, note=note,
                    rows=0, labels=set(), nmin=None, nmax=None, unparsed_ids=0)


def hit(col, key, date=None):
    s = SRC[col]
    HITS[key][col] += 1
    s["labels"].add(key)
    s["rows"] += 1
    if date:
        DATES[key][col].add(date)


reg("WPA1944", "catalog", "WPA", "Lord/WPA 1944 'Presidential Executive Orders, Numbered 1-8030' (OCR parse)",
    ["jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv"], "independent",
    "Primary finding aid compiled by Lord's staff from department records, Statutes at Large and printed compilations; "
    "OCR text layer, never an original. Held as a copy of jobs/wpa-lists (unmerged branch).")
reg("OFR_CATALOG", "catalog", "OFR", "Office of the Federal Register executive-order index (federalregister.gov API export), 1937-2026",
    ["jobs/fr-originals/data/ofr_index/fedreg_bulk_01.json.gz ... 07"], "independent",
    "Built by OFR from the Federal Register itself; catalog metadata, not the legal edition.")
reg("PROQUEST_LINKLIST", "catalog", "PROQUEST", "Owner-supplied ProQuest Congressional link list (links to pre-1937 numbered-order records)",
    ["jobs/pinakes-proquest-ingest/output/SUPPLIED_LINKS_RECONCILED.csv"], "independent_partial",
    "Only 2,765 links were supplied; ProQuest's own facet claims 9,503 numbered records. This is a partial subset of the "
    "ProQuest catalog, not the whole of it.")
reg("PROQUEST_PDF", "text_replica", "PROQUEST", "ProQuest 'Replica of Original' PDFs held in the repository",
    ["jobs/pinakes-proquest-ingest/output/INVENTORY.csv"], "independent_partial",
    "Same ProQuest family as the link list (counted once). Archival replica scans, not counted as originals.")
reg("APP_INDEX", "catalog", "APP", "American Presidency Project executive-order index (app_index)",
    ["jobs/app-executive-orders/output/INDEX.csv"], "NOT independent",
    "APP compiles from Lord/WPA and the Federal Register, so it repeats those catalogs.")
reg("HOOVER_V2_TABLE2", "catalog_in_printing", "OFFTEXT", "Table 2 (orders by number and date) in the OFR 1974 Hoover volume II",
    ["jobs/ofr-compilations/output/HOOVER_V2_TABLE2.csv"], "independent",
    "A listing inside an official printing; counted in the official-text family.")
reg("T_FR_ORIGINALS", "text_official", "OFFTEXT", "Federal Register original pages located for the order",
    ["jobs/fr-originals/output/ (via REGISTER official_sources)"], "independent", "Taken from REGISTER official_sources.")
reg("T_OFR_COMPILATIONS", "text_official", "OFFTEXT", "OFR 1974 Hoover compilation text of the order",
    ["jobs/ofr-compilations/output/ (via REGISTER official_sources)"], "independent", "Taken from REGISTER official_sources.")
reg("T_ISTHMIAN_1911", "text_official", "OFFTEXT", "GPO 1911 Isthmian Canal Commission compilation",
    ["jobs/isthmian-canal-1911/output/ (via REGISTER official_sources)"], "independent", "Taken from REGISTER official_sources.")
reg("T_INDIAN_RES_1912", "text_official", "OFFTEXT", "GPO 1912 Executive Orders Relating to Indian Reservations",
    ["jobs/indian-reservations-1912/output/ (via REGISTER official_sources)"], "independent", "Taken from REGISTER official_sources.")
reg("T_PHOTIUS_GPO", "text_official", "OFFTEXT", "GPO bound slip-order series, HathiTrust 000070271 (EO 4306-9284), verdict pass or check",
    ["jobs/photius-gpo-volumes/output/ORDERS.csv"], "independent",
    "A tagged order was found in the volume; 'fail' verdict rows are excluded. Page check still pending for many.")
reg("T_PHOTIUS_CSC", "text_official", "OFFTEXT", "Civil Service Commission annual-report printings that passed the page check",
    ["jobs/photius-csc-printings/output/RESULTS.csv"], "independent", "Only rows with counts_as_official_printing=yes.")
reg("T_HATHI_GPO", "text_gov_print", "GOVPRINT", "Government-printed copy OCR located by hathi-gpo-orders (mostly the 1974 Hoover compilation)",
    ["jobs/hathi-gpo-orders/output/ (via REGISTER transcription_sources)"], "independent_of_catalogs",
    "Machine-read; overlaps the OFR Hoover compilation, so may repeat T_OFR_COMPILATIONS.")
reg("T_CSC_REPORTS", "text_gov_print", "GOVPRINT", "Civil Service Commission annual reports (leads taken from WPA citations)",
    ["jobs/csc-annual-reports/output/ (via REGISTER transcription_sources)"], "NOT independent of WPA",
    "Located using WPA citations; shown but not counted.")
reg("T_RICHARDSON", "text_gov_print", "GOVPRINT", "Richardson, Messages and Papers of the Presidents (GPO 1896-99)",
    ["jobs/richardson-volumes/output/ (via REGISTER transcription_sources)"], "independent_of_catalogs",
    "Compiled from department records and newspapers; WPA cites it.")
reg("T_NUMBERED_EARLY", "text_gov_print", "GOVPRINT", "Printed books searched by numbered-early-orders (matched by number or date)",
    ["jobs/numbered-early-orders/output/ (via REGISTER transcription_sources)"], "NOT independent of WPA",
    "Targets and dates come from the WPA list; machine matches; shown but not counted.")
reg("T_WIKISOURCE", "text_volunteer", "VOLUNTEER", "Wikisource volunteer transcriptions",
    ["jobs/wikisource-texts/output/ (via REGISTER transcription_sources)"], "NOT independent", "Volunteer transcription; not counted.")
reg("T_APP_TEXT", "text_volunteer", "APP", "APP page text for the order",
    ["jobs/app-executive-orders/output/ (via REGISTER transcription_sources)"], "NOT independent", "Same family as APP_INDEX; not counted.")

FAMILIES_INDEPENDENT = ["WPA", "OFR", "PROQUEST", "OFFTEXT", "GOVPRINT"]
CATALOG_FAMILIES = ["WPA", "OFR", "PROQUEST"]
FAM_OF = {c: m["family"] for c, m in SRC.items()}
NOT_COUNTED = {"T_CSC_REPORTS", "T_NUMBERED_EARLY"}
COUNTED_COL_FAMILY = {c: f for c, f in FAM_OF.items() if f in FAMILIES_INDEPENDENT and c not in NOT_COUNTED}

paths_sha = {}

# ---- WPA
p = P("jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv")
paths_sha["WPA1944"] = sha(p)
for r in rd(p):
    k = norm(r["id"])
    if not k:
        SRC["WPA1944"]["unparsed_ids"] += 1
        continue
    d = wpa_date(r["year"], r["month_day"])
    if r["year"] and r["month_day"] and not d:
        UNPARSED["WPA1944"] += 1
    hit("WPA1944", k, d)

# ---- OFR catalog
ofr_files = sorted(glob.glob(P("jobs/fr-originals/data/ofr_index/fedreg_bulk_0*.json.gz")))
paths_sha["OFR_CATALOG"] = hashlib.sha256("".join(sha(f) for f in ofr_files).encode()).hexdigest()
for f in ofr_files:
    for r in json.load(gzip.open(f))["results"]:
        k = norm(r.get("executive_order_number"))
        if not k:
            SRC["OFR_CATALOG"]["unparsed_ids"] += 1
            continue
        hit("OFR_CATALOG", k, iso(r.get("signing_date")))

# ---- ProQuest
p = P("jobs/pinakes-proquest-ingest/output/SUPPLIED_LINKS_RECONCILED.csv")
paths_sha["PROQUEST_LINKLIST"] = sha(p)
pq_dates = {}
for r in rd(P("jobs/pinakes-proquest-ingest/output/ORDERS.csv")):
    k = norm(r["instrument_id"])
    if k:
        pq_dates[k] = iso(r["signing_date"])
for r in rd(p):
    k = norm(r["instrument_id"])
    if not k:
        SRC["PROQUEST_LINKLIST"]["unparsed_ids"] += 1
        continue
    hit("PROQUEST_LINKLIST", k, pq_dates.get(k))
p = P("jobs/pinakes-proquest-ingest/output/INVENTORY.csv")
paths_sha["PROQUEST_PDF"] = sha(p)
seen = set()
for r in rd(p):
    k = norm(r["instrument_id"])
    if k and r["pdf_signature"] == "yes" and k not in seen:
        seen.add(k)
        hit("PROQUEST_PDF", k)

# ---- APP
p = P("jobs/app-executive-orders/output/INDEX.csv")
paths_sha["APP_INDEX"] = sha(p)
for r in rd(p):
    k = norm(r["instrument_id"]) or norm(r["eo_number_raw"])
    if k:
        hit("APP_INDEX", k, iso(r["date"]))

# ---- Hoover table 2
p = P("jobs/ofr-compilations/output/HOOVER_V2_TABLE2.csv")
paths_sha["HOOVER_V2_TABLE2"] = sha(p)
for r in rd(p):
    k = norm(r["instrument_id"])
    if not k:
        continue
    try:
        d = datetime.date(int(r["year_from_table"]), int(r["month"]), int(r["day"]))
    except (ValueError, TypeError):
        d = None
    hit("HOOVER_V2_TABLE2", k, d)

# ---- Photius
p = P("jobs/photius-gpo-volumes/output/ORDERS.csv")
paths_sha["T_PHOTIUS_GPO"] = sha(p)
for r in rd(p):
    k = norm(r["instrument_id"])
    if k and r["verdict"] in ("pass", "check"):
        hit("T_PHOTIUS_GPO", k, iso(r["dateline_seen"]))
p = P("jobs/photius-csc-printings/output/RESULTS.csv")
paths_sha["T_PHOTIUS_CSC"] = sha(p)
for r in rd(p):
    k = norm(r["instrument_id"])
    if k and r["counts_as_official_printing"] == "yes":
        hit("T_PHOTIUS_CSC", k, iso(r["date_on_page"]))

# ---- REGISTER
REG_PATH = P("jobs/domesday-register/output/REGISTER.csv")
paths_sha["REGISTER"] = sha(REG_PATH)
REGISTER = rd(REG_PATH)
REGMAP = {"fr-originals": "T_FR_ORIGINALS", "ofr-compilations": "T_OFR_COMPILATIONS", "isthmian-canal-1911": "T_ISTHMIAN_1911",
          "indian-reservations-1912": "T_INDIAN_RES_1912", "hathi-gpo-orders": "T_HATHI_GPO", "csc-annual-reports": "T_CSC_REPORTS",
          "richardson-volumes": "T_RICHARDSON", "numbered-early-orders": "T_NUMBERED_EARLY", "wikisource-texts": "T_WIKISOURCE",
          "app-executive-orders": "T_APP_TEXT"}
census = {}
for r in REGISTER:
    if r["number"] == "":
        continue
    k = (int(r["number"]), r["suffix"])
    census[k] = r
    for fld in ("official_sources", "transcription_sources"):
        for s in r[fld].split("|"):
            if s in REGMAP:
                hit(REGMAP[s], k)
for c in ("T_FR_ORIGINALS", "T_OFR_COMPILATIONS", "T_ISTHMIAN_1911", "T_INDIAN_RES_1912", "T_HATHI_GPO", "T_CSC_REPORTS",
          "T_RICHARDSON", "T_NUMBERED_EARLY", "T_WIKISOURCE", "T_APP_TEXT"):
    paths_sha[c] = paths_sha["REGISTER"]
for c, s in SRC.items():
    ns = [k[0] for k in s["labels"]]
    s["nmin"], s["nmax"] = (min(ns), max(ns)) if ns else (None, None)

# ---- audit pointers (shown, never counted)
audit_ids = {}
for r in rd(P("research/graunt-census-audit-2026-11-12/EO_reconciled_inventory.csv")):
    k = norm(r["id"]) if r["series"] == "Numbered" else None
    if k:
        audit_ids[k] = r["source_url"]
cand = {}
for r in rd(P("jobs/domesday-register/output/CANDIDATES_NOT_IN_REGISTER.csv")):
    k = norm(r["instrument_id"])
    if k:
        cand[k] = r["named_by"] + ":" + r["strength"]
AUDIT_MISSING = {(n, "") for n in (list(range(36, 50)) + [51, 52, 53, 92, 2103, 2539, 2703, 3493, 3733, 6585])} | \
                {(130, "A"), (2687, "A"), (5151, "A"), (7010, "F"), (8606, "A")}

# ---- rows
present_nums = {k[0] for k in census}
named_not_census = {k for k in HITS if k not in census}
absent_whole = [n for n in range(1, MAXN + 1) if n not in present_nums]
sorted_c = sorted(census)
sorted_nums = [k[0] for k in sorted_c]


def era_for(n):
    i = bisect.bisect_right(sorted_nums, n) - 1
    return census[sorted_c[max(i, 0)]]["era"]


all_keys = set(census) | named_not_census | {(n, "") for n in absent_whole}
cols = list(SRC)
rows = []
for k in sorted(all_keys):
    c = census.get(k)
    h = HITS.get(k, {})
    fam = {FAM_OF[col] for col in h if col in COUNTED_COL_FAMILY}
    fam_c = {f for f in fam if f in CATALOG_FAMILIES}
    cd = c["date"] if c else ""
    if not cd:
        for col in ("WPA1944", "OFR_CATALOG", "PROQUEST_LINKLIST", "APP_INDEX"):
            if DATES[k].get(col):
                cd = min(DATES[k][col]).isoformat()
                break
    status = "in_census" if c else ("named_not_in_census" if h else "absent_no_listing")
    n = k[0]
    notes = []
    if k in AUDIT_MISSING:
        notes.append("census-audit missing label; " + ("now in census as " + c["census_class"] if c else "still absent from census"))
    elif c and c["census_class"].startswith("admitted"):
        notes.append(c["census_class"])
    if k in audit_ids and not c:
        notes.append("in audit reconciled inventory")
    if k in cand:
        notes.append("domesday candidate " + cand[k])
    row = {"label": label(k), "number": n, "suffix": k[1], "in_census": 1 if c else 0, "census_status": status,
           "census_class": c["census_class"] if c else "", "date": cd, "date_source": c["date_source"] if c else "",
           "era": c["era"] if c else era_for(n)}
    for col in cols:
        row[col] = 1 if col in h else 0
    row["WPA_rows"] = h.get("WPA1944", 0)
    row["n_listings"] = len(h)
    row["n_catalogs_independent"] = len(fam_c)
    row["n_independent_listings"] = len(fam)
    row["independent_families"] = "|".join(f for f in FAMILIES_INDEPENDENT if f in fam)
    row["wpa_range_covers"] = 1 if n <= 8030 else 0
    row["ofr_range_covers"] = 1 if n >= 7532 else 0
    row["official_text_held"] = c["best_held"] if c else ""
    row["notes"] = "; ".join(notes)
    rows.append(row)

FIELDS = ["label", "number", "suffix", "in_census", "census_status", "census_class", "date", "date_source", "era"] + cols + \
         ["WPA_rows", "n_listings", "n_catalogs_independent", "n_independent_listings", "independent_families",
          "wpa_range_covers", "ofr_range_covers", "official_text_held", "notes"]


def write(name, fields, data):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fields, lineterminator="\n")
        w.writeheader()
        w.writerows(data)


write("NUMBERED_CROSSWALK.csv", FIELDS, rows)

# ---- exceptions
exc = []
for r in rows:
    if r["in_census"] and r["n_independent_listings"] <= 1:
        k = (r["number"], r["suffix"])
        h = HITS.get(k, {})
        why = []
        if r["n_independent_listings"] == 0:
            why.append("named only by non-counted sources: " + (",".join(sorted(h)) or "none"))
        else:
            why.append("only family " + r["independent_families"])
        if not r["wpa_range_covers"]:
            why.append("number above 8030 (WPA list ends)")
        elif "WPA" not in r["independent_families"]:
            why.append("within WPA range but WPA parse does not name this label")
        if not r["ofr_range_covers"]:
            why.append("before 7532 (OFR catalog begins)")
        elif "OFR" not in r["independent_families"]:
            why.append("within OFR range but OFR catalog does not list this label")
        if r["official_text_held"] == "nothing":
            why.append("no text of any kind held")
        exc.append({"label": r["label"], "number": r["number"], "era": r["era"], "census_class": r["census_class"],
                    "n_independent_listings": r["n_independent_listings"], "independent_families": r["independent_families"],
                    "all_columns_naming_it": "|".join(sorted(h)), "official_text_held": r["official_text_held"],
                    "why": "; ".join(why)})
write("EXCEPTIONS.csv", ["label", "number", "era", "census_class", "n_independent_listings", "independent_families",
                         "all_columns_naming_it", "official_text_held", "why"], exc)

# ---- absent numbers
ab = []
for n in absent_whole:
    ks = sorted(k for k in HITS if k[0] == n)
    ab.append({"number": n, "named_by": "|".join(sorted({c for k in ks for c in HITS[k]})),
               "labels_named": "|".join(label(k) for k in ks), "audit_missing": 1 if (n, "") in AUDIT_MISSING else 0,
               "in_audit_inventory": 1 if (n, "") in audit_ids else 0, "in_wpa_range": 1 if n <= 8030 else 0})
write("ABSENT_NUMBERS.csv", ["number", "named_by", "labels_named", "audit_missing", "in_audit_inventory", "in_wpa_range"], ab)

# ---- date conflicts
DATE_COLS = ["WPA1944", "OFR_CATALOG", "PROQUEST_LINKLIST", "APP_INDEX", "HOOVER_V2_TABLE2", "T_PHOTIUS_GPO"]
pair_conf, census_conf = [], []
pair_counts, census_counts = collections.Counter(), collections.Counter()
cmp_pairs = cmp_census = 0


def gap(a, b):
    return min(abs((x - y).days) for x in a for y in b)


for k in sorted(DATES):
    ds = {c: v for c, v in DATES[k].items() if v and c in DATE_COLS}
    cs = sorted(ds)
    for i in range(len(cs)):
        for j in range(i + 1, len(cs)):
            cmp_pairs += 1
            g = gap(ds[cs[i]], ds[cs[j]])
            if g > 1:
                pair_counts[(cs[i], cs[j])] += 1
                pair_conf.append({"type": "listing_vs_listing", "label": label(k), "source_a": cs[i],
                                  "dates_a": "|".join(sorted(d.isoformat() for d in ds[cs[i]])), "source_b": cs[j],
                                  "dates_b": "|".join(sorted(d.isoformat() for d in ds[cs[j]])), "min_gap_days": g})
    c = census.get(k)
    cdate = iso(c["date"]) if c and len(c["date"]) >= 10 else None
    if cdate:
        for col in cs:
            cmp_census += 1
            g = gap(ds[col], {cdate})
            if g > 1:
                census_counts[col] += 1
                census_conf.append({"type": "listing_vs_census(date_source=%s)" % c["date_source"], "label": label(k),
                                    "source_a": col, "dates_a": "|".join(sorted(d.isoformat() for d in ds[col])),
                                    "source_b": "CENSUS", "dates_b": c["date"], "min_gap_days": g})
write("DATE_CONFLICTS.csv", ["type", "label", "source_a", "dates_a", "source_b", "dates_b", "min_gap_days"],
      pair_conf[:CONFLICT_CAP] + census_conf[:CONFLICT_CAP])

# ---- sources + summary
src_rows = []
for c, m in SRC.items():
    src_rows.append({"column": c, "kind": m["kind"], "family": m["family"], "independence": m["independence"],
                     "counted_in_n_independent": 1 if c in COUNTED_COL_FAMILY else 0, "what": m["what"],
                     "paths": " ; ".join(m["paths"]), "sha256": paths_sha.get(c, ""), "rows_read": m["rows"],
                     "distinct_labels": len(m["labels"]), "labels_in_census": sum(1 for x in m["labels"] if x in census),
                     "labels_not_in_census": sum(1 for x in m["labels"] if x not in census), "number_min": m["nmin"],
                     "number_max": m["nmax"], "unparsed_ids": m["unparsed_ids"], "note": m["note"]})
write("SOURCES.csv", list(src_rows[0].keys()), src_rows)

inc = [r for r in rows if r["in_census"]]


def bucket(n):
    return "3+" if n >= 3 else str(n)


by_n = collections.Counter(bucket(r["n_independent_listings"]) for r in inc)
by_cat = collections.Counter(bucket(r["n_catalogs_independent"]) for r in inc)
by_era = collections.defaultdict(collections.Counter)
by_era_cat = collections.defaultdict(collections.Counter)
fam_counts = collections.Counter()
for r in inc:
    by_era[r["era"]][bucket(r["n_independent_listings"])] += 1
    by_era_cat[r["era"]][bucket(r["n_catalogs_independent"])] += 1
    for f_ in r["independent_families"].split("|"):
        if f_:
            fam_counts[f_] += 1
named_out = [r for r in rows if r["census_status"] == "named_not_in_census"]
idx = {(r["number"], r["suffix"]): r for r in rows}
summary = {
    "register_sha256": paths_sha["REGISTER"],
    "census_rows_total": len(REGISTER),
    "census_unnumbered_rows_excluded": sum(1 for r in REGISTER if r["number"] == ""),
    "census_numbered_labels": len(inc),
    "total_rows_in_crosswalk": len(rows),
    "numbers_1_to_14435_absent_from_census": len(absent_whole),
    "absent_numbers_named_by_any_listing": sum(1 for a in ab if a["named_by"]),
    "absent_numbers_named_by_no_listing": sum(1 for a in ab if not a["named_by"]),
    "labels_named_by_a_listing_but_not_in_census": len(named_out),
    "named_not_in_census": [r["label"] + " [" + "|".join(c for c in cols if r[c]) + "]" for r in named_out],
    "labels_by_n_independent_listings": dict(sorted(by_n.items())),
    "labels_by_n_independent_catalogs": dict(sorted(by_cat.items())),
    "labels_by_era_n_independent_listings": {e: dict(sorted(v.items())) for e, v in sorted(by_era.items())},
    "labels_by_era_n_independent_catalogs": {e: dict(sorted(v.items())) for e, v in sorted(by_era_cat.items())},
    "labels_per_independent_family": dict(sorted(fam_counts.items())),
    "labels_with_0_or_1_independent_listing": len(exc),
    "labels_with_0_independent_listings": sum(1 for r in exc if r["n_independent_listings"] == 0),
    "labels_named_by_no_listing_at_all": sum(1 for r in inc if r["n_listings"] == 0),
    "audit_missing_29": {label(k): {"in_census_now": int(k in census),
                                   "n_independent_listings": idx[k]["n_independent_listings"] if k in idx else 0,
                                   "named_by": sorted(HITS.get(k, {}))} for k in sorted(AUDIT_MISSING)},
    "date_conflicts": {"definition": "nearest pair of dates differs by more than 1 day; only full dates compared",
                       "listing_vs_listing_comparisons": cmp_pairs, "listing_vs_listing_conflicts": len(pair_conf),
                       "listing_vs_listing_by_pair": {"|".join(k): v for k, v in sorted(pair_counts.items())},
                       "listing_vs_census_comparisons": cmp_census, "listing_vs_census_conflicts": len(census_conf),
                       "listing_vs_census_by_source": dict(sorted(census_counts.items())),
                       "detail_rows_cap_per_type": CONFLICT_CAP, "unparsed_wpa_dates": UNPARSED["WPA1944"]},
    "sources": {r["column"]: {k: r[k] for k in ("family", "independence", "rows_read", "distinct_labels", "labels_in_census",
                                                "labels_not_in_census", "number_min", "number_max", "sha256")} for r in src_rows},
}
with open(os.path.join(OUT, "SUMMARY.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=1, sort_keys=True, ensure_ascii=False)
    f.write("\n")
print(json.dumps({k: summary[k] for k in ("census_numbered_labels", "numbers_1_to_14435_absent_from_census",
                                          "absent_numbers_named_by_any_listing", "labels_named_by_a_listing_but_not_in_census",
                                          "labels_by_n_independent_listings", "labels_by_n_independent_catalogs",
                                          "labels_with_0_or_1_independent_listing", "labels_named_by_no_listing_at_all",
                                          "date_conflicts")}, indent=1))

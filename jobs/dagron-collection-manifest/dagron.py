"""Dagron: order-level acquisition manifests for external collections of executive orders.

Named for Rene Dagron, who put the dispatches of besieged Paris (1870-71) on microfilm for the pigeon post.

For each collection spec in `collections/*.json` (numbered units such as reels or volumes, and a date range), it
lists every tracked order the collection could supply missing evidence for: what the project holds for the order,
by kind of witness and with retained paths, what is held only remotely, the likely unit, an acquisition priority,
and identity or coverage doubts. It also marks orders whose images are already staged in the collection's staging
folder, so nobody fetches them twice.

Read-only. It changes no status, readiness count, census row, codebook text or other job's output, and decides
nothing about identity or custody. The readiness tracker's committed output is the authority for whether an
order's original-text step is satisfied; this script never recomputes or overrides it.

    python3 -I dagron.py [REPO_ROOT] [OUTPUT_DIR] [SPEC ...]     (defaults: $REPO_ROOT, $OUTPUT_DIR, collections/*.json)
"""
import collections
import csv
import glob
import gzip
import io
import json
import os
import re
import subprocess
import sys

csv.field_size_limit(min(2 ** 31 - 1, 10 ** 9))
HERE = os.path.dirname(os.path.abspath(__file__))

# Evidence lanes exactly as jobs/readiness-tracker/tracker.py reads them (its J dict), plus app-transcriptions.
LANES = {
    "fr-originals": ("official_printed_copy", "counting_lane"),
    "ofr-compilations": ("official_printed_copy", "counting_lane"),
    "isthmian-canal-1911": ("official_printed_copy", "counting_lane"),
    "indian-reservations-1912": ("official_printed_copy", "counting_lane"),
    "tischendorf-originals": ("official_printed_copy", "counting_lane"),
    "mabillon-held-printings": ("official_printed_copy", "counting_lane"),
    "opus-media-match": ("opus_media_original", "counting_lane"),
    "pinakes-proquest-ingest": ("signed_original_replica_scan", "lead_only_until_page_check_and_grade"),
    "richardson-volumes": ("transcription", "lead_only_never_original"),
    "app-executive-orders": ("transcription", "lead_only_never_original"),
    "app-transcriptions": ("transcription", "lead_only_never_original"),
    "wikisource-texts": ("transcription", "lead_only_never_original"),
    "hathi-gpo-orders": ("official_printed_copy_uncounted_lane", "lead_only_never_original"),
    "numbered-early-orders": ("official_printed_copy_uncounted_lane", "lead_only_never_original"),
    "csc-annual-reports": ("report_reprint", "lead_only_never_original"),
}
FRAGMENT_FILES = [
    "jobs/fr-originals/output/FRAGMENTS.jsonl", "jobs/ofr-compilations/output/FRAGMENTS.jsonl",
    "jobs/isthmian-canal-1911/output/FRAGMENTS.jsonl", "jobs/indian-reservations-1912/output/FRAGMENTS.jsonl",
    "jobs/tischendorf-originals/output/FRAGMENTS.jsonl", "jobs/mabillon-held-printings/output/FRAGMENTS.jsonl",
    "jobs/opus-media-match/output/FRAGMENTS.jsonl", "jobs/pinakes-proquest-ingest/output/FRAGMENTS.jsonl",
    "jobs/richardson-volumes/output/FRAGMENTS.jsonl", "jobs/app-executive-orders/output/FRAGMENTS.jsonl",
    "jobs/app-executive-orders/output/MIRROR_FRAGMENTS.jsonl", "jobs/app-transcriptions/output/FRAGMENTS.jsonl",
    "jobs/wikisource-texts/output/FRAGMENTS.jsonl", "jobs/hathi-gpo-orders/output/FRAGMENTS.jsonl",
    "jobs/numbered-early-orders/output/FRAGMENTS.jsonl", "jobs/csc-annual-reports/output/FRAGMENTS.jsonl",
]
# Source indexes whose records name a committed copy of a source's bytes (measured 2026-11-06: these resolve every
# retained source behind a pre-1937 fragment), plus the salvage folders' indexes, matched in the tree.
RETENTION_INDEXES = ["jobs/wikisource-texts/output/SOURCES.jsonl", "jobs/cotton-capture-custody/output/SOURCES.jsonl",
                     "jobs/ptolemy-custody/output/SOURCES.jsonl", "jobs/cassiodorus/output/SOURCES.jsonl"]
RETENTION_GLOB = re.compile(r"^research/salvage/.+/SOURCES[^/]*\.jsonl$")
P = {
    "readiness": "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv",
    "domesday": "jobs/domesday-register/output/REGISTER.csv",
    "domesday_summary": "jobs/domesday-register/output/SUMMARY.json",
    "candidates": "jobs/domesday-register/output/CANDIDATES_NOT_IN_REGISTER.csv",
    "census": "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv",
    "admissions": "research/stage15/CENSUS/ADMISSIONS_*.csv",
    "frame": "research/mabillon/frame/FRAME.csv",
    "mabillon_coverage": "research/mabillon/frame/COVERAGE.csv",
    "lewis": "jobs/lewis-originals/output/ROUTES.csv",
    "nara": "jobs/mabillon-nara/output/BY_ORDER.csv",
    "pq_orders": "jobs/pinakes-proquest-ingest/output/ORDERS.csv",
    "pq_missing": "jobs/pinakes-proquest-ingest/output/MISSING_FROM_UPLOAD.csv",
    "custody": "research/stage21/original_sources/CASE_ORIGINAL_SOURCE_CUSTODY.csv",
    "causal": "research/stage19/output/CAUSAL_QUEUE.csv",
    "crosswalk": "research/stage21/sources_index/OFFICIAL_SOURCE_CASE_CROSSWALK.csv",
}
TEXT_BLOCKERS = ("ORIGINAL_FOUND_NEEDS_PAGE_CHECK", "OFFICIAL_URL_KNOWN_NOT_DOWNLOADED", "NO_OFFICIAL_SOURCE_LOCATED",
                 "ONLY_COMPILED_TRANSCRIPTION_FOUND", "ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK")
PATH_KEYS = ("cache_path", "path", "repository_path", "file", "local_path", "retained_path")
LFS = re.compile(r"^version https://git-lfs\.github\.com/spec/v1\s+oid sha256:([0-9a-f]{64})\s", re.M)
CSV_COLS = ["manifest_group", "acquisition_priority", "instrument_id", "proposed_id_not_in_census", "eo_designation",
            "number", "suffix", "signature_date", "date_source", "title", "president", "census_class", "likely_unit",
            "likely_secondary_unit_unverified", "staged_acquisitions", "missing_accepted_original_witness",
            "missing_accepted_working_text", "original_copy_replacement_required", "no_image_of_any_kind_retained",
            "has_signed_original_replica_scan", "replica_scan_text_usable", "has_official_printed_copy_lead",
            "has_uncounted_printing_or_reprint", "has_transcription_only", "no_witness_of_any_kind",
            "step_original_text", "text_evidence_tier", "original_text_blockers", "provisional_status", "claim_present",
            "domesday_best_held", "mabillon_best_route_20261105", "retained_files", "source_refs", "remote_not_retained",
            "other_routes_known", "identity_uncertainty", "coverage_uncertainty", "priority_reason"]


class Repo:
    """Reads files from the working tree, falling back to `git show HEAD:path` (the runner's partial clone fetches
    the blob). The file list is the git tree, so existence checks do not need files on disk."""

    def __init__(self, root):
        self.root = root
        self.git = os.path.isdir(os.path.join(root, ".git")) or os.path.isfile(os.path.join(root, ".git"))
        if self.git:
            out = subprocess.run(["git", "-C", root, "ls-tree", "-r", "--name-only", "-z", "HEAD"],
                                 capture_output=True, check=True).stdout
            self.tree = set(p.decode("utf-8") for p in out.split(b"\0") if p)
            self.commit = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True,
                                         text=True, check=True).stdout.strip()
        else:
            self.tree = {os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/")
                         for d, _, fs in os.walk(root) for f in fs}
            self.commit = ""

    def text(self, path):
        full = os.path.join(self.root, path)
        if os.path.isfile(full):
            with open(full, encoding="utf-8", errors="replace") as fh:
                return fh.read()
        if self.git and path in self.tree:
            r = subprocess.run(["git", "-C", self.root, "show", f"HEAD:{path}"], capture_output=True)
            return r.stdout.decode("utf-8", errors="replace") if r.returncode == 0 else None
        return None

    def csv(self, path):
        t = self.text(path)
        return list(csv.DictReader(io.StringIO(t))) if t else []

    def jsonl(self, path):
        out = []
        for line in (self.text(path) or "").splitlines():
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return out

    def glob(self, pattern):
        rx = re.compile("^" + re.escape(pattern).replace(r"\*", "[^/]*") + "$")
        return sorted(p for p in self.tree if rx.match(p))


def split_designation(s):
    m = re.fullmatch(r"(\d+)(.*)", s.strip())
    return (int(m.group(1)), m.group(2)) if m else (None, s)


def designation(number, suffix):
    return f"EO {number}{suffix}" if number else "(unnumbered)"


def unit_for(spec, number, suffix):
    """(unit, note) from the spec's numbered ranges. A bound's suffix is honoured (reel 11 starts at 6925A); a
    variant of a unit's last number with no explicit bound stays with that unit, with a boundary note."""
    if not str(number).isdigit():
        return None, ""
    n = int(number)
    units = spec["units"]
    for i, u in enumerate(units):
        fn, fs = split_designation(u["first"])
        ln, ls = split_designation(u["last"])
        if not (fn <= n <= ln):
            continue
        if n == fn and fs and (not suffix or suffix < fs):
            continue  # before this unit's suffixed first bound: belongs to the previous unit
        if n == ln and ls and suffix and suffix > ls:
            continue
        note = ""
        nxt = units[i + 1] if i + 1 < len(units) else None
        if n == ln and suffix and not ls:
            nn, ns = split_designation(nxt["first"]) if nxt else (None, "")
            if nxt and nn == n and ns:
                continue  # the next unit explicitly starts with a suffixed variant of this number
            note = (f"variant of {spec['unit_label']} {u['unit']}'s last number: may follow {n} on {spec['unit_label']} "
                    f"{u['unit']} or open {spec['unit_label']} {u['unit'] + 1 if nxt else '(none)'}")
        elif n == ln and nxt and split_designation(nxt["first"])[0] == n:
            note = f"{designation(n, '')} is the last item of {spec['unit_label']} {u['unit']}; the next starts at {nxt['first']}"
        elif n == fn and i > 0:
            note = f"first number of {spec['unit_label']} {u['unit']}"
        return u["unit"], note
    return None, ""


def numbered_range(spec):
    return split_designation(spec["units"][0]["first"])[0], split_designation(spec["units"][-1]["last"])[0]


def load(repo):
    """Everything the manifest reads, once per run (shared by all specs)."""
    d = {k: repo.csv(v) for k, v in P.items() if k not in ("admissions", "domesday_summary")}
    d["admissions"] = [r for p in repo.glob(P["admissions"]) for r in repo.csv(p)]
    d["domesday_summary"] = json.loads(repo.text(P["domesday_summary"]) or "{}")
    retained = {}
    for path in RETENTION_INDEXES + sorted(p for p in repo.tree if RETENTION_GLOB.match(p)):
        base = os.path.dirname(path)
        job_dir = "/".join(path.split("/")[:2]) if path.startswith("jobs/") else base
        for r in repo.jsonl(path):
            sha = r.get("sha256")
            if not isinstance(sha, str):
                continue
            for k in PATH_KEYS:
                v = r.get(k)
                if not isinstance(v, str) or not v:
                    continue
                for cand in (v, f"{base}/{v}", f"{job_dir}/{v}", f"{job_dir}/output/{v}"):
                    cand = os.path.normpath(cand).replace(os.sep, "/")
                    if cand in repo.tree:
                        retained.setdefault(sha, cand)
                        break
    for path in sorted(p for p in repo.tree if p.startswith("releases/source_books/") and p.endswith(".pdf")):
        m = LFS.match(repo.text(path) or "")  # Git LFS pointer: its oid is the file's SHA-256
        if m:
            retained.setdefault(m.group(1), path)
    for r in d["custody"]:
        if r.get("sha256") and r.get("repository_path") in repo.tree:
            retained.setdefault(r["sha256"], r["repository_path"])
    d["retained"] = retained
    pq = {r["instrument_id"]: r for r in d["pq_orders"]}
    frags = collections.defaultdict(list)
    for path in FRAGMENT_FILES:
        job = path.split("/")[1]
        for r in repo.jsonl(path):
            if r.get("kind") != "original_representation" or not isinstance(r.get("instrument_id"), str):
                continue
            x = r.get("data") if isinstance(r.get("data"), dict) else {}
            lane_class, lane_rule = LANES[job]
            counted = job == "opus-media-match" or (lane_rule == "counting_lane" and x.get("needs_page_check") is False)
            text_path = x.get("text_path") or ""
            text_repo = os.path.normpath(f"jobs/{job}/output/{text_path}").replace(os.sep, "/") if text_path else ""
            src_sha = x.get("sha256") or x.get("local_file_sha256") or ""
            file_repo = x.get("file") if x.get("file") in repo.tree else ""
            url = x.get("url") or x.get("upstream_url") or x.get("book_item_url") or ""
            for s in ([] if url else r.get("sources") or []):
                if isinstance(s, dict) and (s.get("url") or s.get("upstream_url")):
                    url = s.get("url") or s.get("upstream_url")
                    break
            frags[r["instrument_id"]].append({
                "witness_class": lane_class, "tracker_rule": lane_rule, "counted_by_tracker_rule": counted,
                "produced_by": job, "fragment_file": path,
                "grade": r.get("grade") or x.get("grade") or "",
                "representation_type": r.get("representation_type") or x.get("representation_type") or "",
                "needs_page_check": x.get("needs_page_check"),
                "acceptable_as_original": r.get("acceptable_as_original", x.get("acceptable_as_original")),
                "page_or_item": x.get("page_or_item") or "", "route": x.get("route") or "", "url": url,
                "source_sha256": src_sha, "source_bytes_retained_path": file_repo or retained.get(src_sha, ""),
                "text_path": text_repo if text_repo in repo.tree else "",
                "text_path_declared_but_absent": text_repo if text_repo and text_repo not in repo.tree else "",
                "text_usable": pq.get(r["instrument_id"], {}).get("text_usable", "") if job == "pinakes-proquest-ingest" else "",
                "signing_date_seen": x.get("signing_date") or x.get("app_date") or x.get("match_date") or "",
            })
    d["frags"] = frags
    return d


def build(spec, repo, d):
    R = {r["instrument_id"]: r for r in d["readiness"]}
    D = {r["instrument_id"]: r for r in d["domesday"]}
    census = {r["id"]: r for r in d["census"]}
    admissions = {r["id"]: r for r in d["admissions"]}
    frame = {r["instrument_id"]: r for r in d["frame"]}
    mab = {r["instrument_id"]: r for r in d["mabillon_coverage"]}
    lewis = {r["instrument_id"]: r for r in d["lewis"]}
    nara = {r["instrument_id"]: r for r in d["nara"]}
    pq_missing = {r["instrument_id"]: r for r in d["pq_missing"]}
    custody = {r["instrument_id"]: r for r in d["custody"]}
    causal = {r["instrument_id"]: r for r in d["causal"]}
    crosswalk = {r["instrument_id"]: r for r in d["crosswalk"]}
    frags = d["frags"]
    lo_n, hi_n = numbered_range(spec)
    date_lo, date_hi = spec["date_coverage"]
    U = spec["unit_label"]
    staged = collections.defaultdict(list)
    staging = spec.get("staging_dir", "")
    for r in repo.jsonl(f"{staging}/PROVENANCE.jsonl") if staging else []:
        if r.get("instrument_id"):
            staged[r["instrument_id"]].append({k: r.get(k, "") for k in (
                "collection", "file", "sha256", "witness_kind_observed", "observed_number", "retrieved_utc")})
    alias_of = {}
    for i in R:
        if i not in D and i.upper() != i and i.upper() in D:
            alias_of[i] = i.upper()
    for i in D:
        if i not in R and i.upper() in R:
            alias_of[i] = i.upper()

    def base(i):
        dm = D.get(i) or D.get(alias_of.get(i, ""), {}) or {}
        ce = census.get(i) or census.get(alias_of.get(i, ""), {}) or {}
        ad = admissions.get(i, {})
        number = dm.get("number") or ad.get("number") or ""
        suffix = (dm.get("suffix") if dm else ad.get("suffix", "")) or ""
        date = dm.get("date") or ad.get("date") or ""
        source = dm.get("date_source") or ("admission_held_official" if ad.get("date") else "")
        if not date and ce.get("date_effective"):
            date, source = ce["date_effective"], f"census:{ce.get('date_source_type', '')}"
        return dm, ce, ad, number, suffix, date, source

    def in_dates(date):
        return not date or date_lo[:len(date)] <= date <= date_hi[:len(date)]

    rows, in_scope = [], set()
    for i in sorted(R):
        r = R[i]
        dm, ce, ad, number, suffix, date, date_source = base(i)
        numbered = number.isdigit()
        n = int(number) if numbered else None
        step, tier = r.get("step_original_text", ""), r.get("text_evidence_tier", "")
        fs = list(frags.get(i, []))
        if ad.get("held_official_path"):
            fs.append({"witness_class": "official_printed_copy", "tracker_rule": "census_admission_record",
                       "counted_by_tracker_rule": False, "produced_by": "census admission " + ad.get("source_row", ""),
                       "fragment_file": "research/stage15/CENSUS/ADMISSIONS", "grade": "", "representation_type": "",
                       "needs_page_check": None, "acceptable_as_original": None,
                       "page_or_item": ad.get("held_official_page", ""), "route": "", "url": "",
                       "source_sha256": ad.get("held_official_sha256", ""),
                       "source_bytes_retained_path": ad["held_official_path"] if ad["held_official_path"] in repo.tree else "",
                       "text_path": ad.get("text_path", "") if ad.get("text_path", "") in repo.tree else "",
                       "text_path_declared_but_absent": "", "text_usable": "", "signing_date_seen": ad.get("date", "")})
        missing_original = tier != "original_supported"
        counted = [f for f in fs if f["counted_by_tracker_rule"]]
        missing_working_text = step == "open" or (not missing_original and not any(f["text_path"] for f in counted))
        identity, coverage = [], []
        if suffix.startswith("-"):
            identity.append(f"numeric suffix '{suffix}' (a second order recorded under number {number}); the numbered "
                            "sequence may hold only one item for this number")
        if suffix == "½":
            identity.append("fraction designation; the collection may file it beside its base number")
        elif suffix and suffix.isalpha():
            identity.append(f"lettered variant '{suffix}'; check that the {U} carries it as its own item")
        if i in alias_of:
            identity.append(f"id alias: {i} ~ {alias_of[i]}")
        if ce.get("bibliographic_class") == "validated_historical_reprint":
            identity.append("census class validated_historical_reprint")
        if not date:
            identity.append("no signing date on record")
        elif len(date) < 10:
            identity.append(f"date known only to {'year' if len(date) == 4 else 'month'} ({date}); source {date_source}")
        if date_source in ("wpa_numbered_list", "wpa_pre1900_list", "census_year"):
            identity.append(f"date from {date_source}: an index date, not a verified signing date")
        seen = {f["signing_date_seen"] for f in fs if f["signing_date_seen"]} - {date}
        if len(date) == 10 and seen:
            identity.append("other dates seen in held sources: " + "|".join(sorted(seen)[:4]))
        if not dm.get("title"):
            identity.append("no title on record")
        if i in admissions:
            identity.append("admitted to the census after the Domesday register's 14,972 (claim-kit population contract)")

        group = None
        if numbered and lo_n <= n <= hi_n:
            if suffix.startswith("-") or i in alias_of:
                group = "3_unnumbered_or_ambiguous_identity"
            elif missing_original:
                group = "1_missing_accepted_original_witness"
            elif missing_working_text:
                group = "2_missing_accepted_working_text_only"
        elif not numbered and in_dates(date):
            group = "3_unnumbered_or_ambiguous_identity"
            identity.append(f"unnumbered order: inclusion in the numbered {U}s is NOT established")
        elif numbered and n > hi_n and date and date[:len(date_hi)] <= date_hi and (missing_original or missing_working_text):
            group = "4_edge_numbered_after_last_unit_within_dates"
            coverage.append(f"number above the last cataloged {U} ({hi_n}); only the collection's date range suggests coverage")
        if group is None:
            continue
        unit, note = unit_for(spec, number, suffix) if numbered else (None, "")
        if note:
            coverage.append(note)
        if not numbered:
            coverage.append(f"no number: locate by date and title in the {U} or volume covering the date; may be absent")
            if date and date < "1862-02-14":
                coverage.append("predates EO 1 (1862): only the collection's date range suggests coverage")
        coverage.append(f"{U} ranges are catalog routing leads, not proof that this order or variant survives in the collection")

        by = collections.defaultdict(list)
        for f in fs:
            by[f["witness_class"]].append(f)
        replica = by["signed_original_replica_scan"]
        official = by["official_printed_copy"] + by["opus_media_original"]
        uncounted = by["official_printed_copy_uncounted_lane"] + by["report_reprint"]
        trans = by["transcription"]
        idx = []
        if ce.get("bibliographic_class") in ("validated_historical_index", "documented_unnumbered"):
            idx.append({"witness_class": "index_entry", "source": f"census bibliographic_class={ce['bibliographic_class']}",
                        "date_source_type": ce.get("date_source_type", "")})
        if frame.get(i, {}).get("wpa_citations"):
            idx.append({"witness_class": "index_entry", "source": "WPA/Lord numbered list citation",
                        "wpa_citations": frame[i]["wpa_citations"], "wpa_print_kinds": frame[i].get("wpa_print_kinds", "")})
        na = nara.get(i)
        if na:
            idx.append({"witness_class": "index_entry" if na.get("with_objects") in ("", "0") else "signed_original_image_remote",
                        "source": "NARA catalog (RG 11) description", "naIds": na.get("naIds", ""),
                        "objects": na.get("objects", ""), "first_object_url": na.get("first_object_url", "")})
        remote = [{"kind": f"{f['witness_class']} source bytes not retained (text {'retained' if f['text_path'] else 'not retained'})",
                   "produced_by": f["produced_by"], "url": f["url"], "sha256": f["source_sha256"]}
                  for f in fs if f["url"] and not f["source_bytes_retained_path"]]
        if i in pq_missing or (dm.get("proquest_link_supplied") == "yes" and not dm.get("proquest_pdf_file")):
            remote.append({"kind": "ProQuest 'Replica of Original' link supplied, PDF not in repository",
                           "url": lewis.get(i, {}).get("lead_url_or_search", "")})
        if na and na.get("first_object_url"):
            remote.append({"kind": "NARA digitized object (image of signed original), not retained",
                           "url": na["first_object_url"], "naIds": na.get("naIds", "")})
        if crosswalk.get(i, {}).get("selected_literal_URL"):
            remote.append({"kind": "Stage 21 crosswalk official URL", "url": crosswalk[i]["selected_literal_URL"]})
        lw = lewis.get(i, {})
        routes = ([{"router": "lewis-originals", "route": lw["best_route"], "status": lw.get("route_status", ""),
                    "next_action": lw.get("next_action", ""), "lead_url_or_search": lw.get("lead_url_or_search", "")}]
                  if lw.get("best_route") and lw["best_route"] != "proquest_local" else [])
        image_retained = any(f["source_bytes_retained_path"] for f in replica + official + uncounted)
        text_usable = any(f["text_usable"] == "yes" for f in replica)
        flags = {
            "missing_accepted_original_witness": missing_original,
            "missing_accepted_working_text": missing_working_text,
            "original_copy_replacement_required": r.get("original_copy_replacement_required") == "yes",
            "no_image_of_any_kind_retained": not image_retained,
            "has_signed_original_replica_scan": bool(replica),
            "replica_scan_text_usable": text_usable if replica else None,
            "has_official_printed_copy_lead": bool(official) and not counted,
            "has_uncounted_printing_or_reprint": bool(uncounted),
            "has_transcription_only": bool(trans) and not (replica or official or uncounted),
            "no_witness_of_any_kind": not fs,
        }
        if group.startswith("1"):
            if flags["original_copy_replacement_required"]:
                pr, why = 1, "working text accepted only provisionally (transcription-dependent); an official image replaces it and closes the recheck"
            elif not (replica or official or uncounted):
                pr, why = 1, "no image or printing of any kind held; this collection may be the only reachable image"
            elif replica and not text_usable:
                pr, why = 2, "only a ProQuest replica scan, whose text is unusable (likely handwritten); a second image is a second witness"
            elif not replica:
                kinds = ([f"official printing lead flagged for a page check ({', '.join(sorted({f['produced_by'] for f in official}))})"] if official else []) + \
                        ([f"uncounted printing or reprint ({', '.join(sorted({f['produced_by'] for f in uncounted}))})"] if uncounted else [])
                pr, why = 2, "no image of the signed original; held only: " + "; ".join(kinds)
            else:
                pr, why = 3, "ProQuest replica scan held with usable text, pending page check; this image corroborates it"
            if r.get("claim_present") == "yes" or r.get("provisional_status") in ("yes", "no"):
                why += "; order already has a provisional status or claim"
        elif group.startswith("2"):
            pr, why = 3, "counted original witness on record but no retained working text for it"
        elif group.startswith("3"):
            pr, why = 4, "identity or inclusion must be confirmed before any image is attached"
        else:
            pr, why = 5, f"outside the cataloged {U}s; check the date-range coverage only"
        rows.append({
            "manifest_group": group, "instrument_id": i, "eo_designation": designation(number, suffix) if numbered else "(unnumbered)",
            "number": number, "suffix": suffix, "signature_date": date, "date_source": date_source,
            "title": dm.get("title", ""), "president": dm.get("president", ""),
            "census_class": dm.get("census_class") or ce.get("bibliographic_class", ""),
            "likely_unit": unit, "likely_secondary_unit_unverified": unit if spec.get("secondary_unit_label") else None,
            "acquisition_priority": pr, "priority_reason": why, "staged_acquisitions": staged.get(i, []),
            "missing": flags,
            "tracker": {"step_original_text": step, "text_evidence_tier": tier,
                        "original_text_blockers": [b for b in (r.get("blockers") or "").split("|") if b in TEXT_BLOCKERS],
                        "provisional_status": r.get("provisional_status", ""), "claim_present": r.get("claim_present", ""),
                        "ready_for_human_review": r.get("ready_for_human_review", ""),
                        "provisional_text_grade": r.get("provisional_text_grade", ""),
                        "informational_flags": r.get("informational_flags", "")},
            "domesday_best_held": dm.get("best_held", ""),
            "mabillon_best_route_20261105": mab.get(i, {}).get("best_route", ""),
            "held": {"signed_original_replica_scans": replica, "official_printed_copies": official,
                     "uncounted_printings_or_reprints": uncounted, "transcriptions": trans, "index_entries": idx,
                     "stage21_custody_state": custody.get(i, {}).get("custody_state", ""),
                     "stage19_locally_preserved_primary": causal.get(i, {}).get("locally_preserved_primary_representation", "")},
            "remote_evidence_not_retained_locally": remote, "other_acquisition_routes_known": routes,
            "identity_uncertainty": identity, "coverage_uncertainty": coverage,
        })
        in_scope.add(i)

    for c in d["candidates"]:
        num, dates = c.get("number", ""), c.get("dates_seen", "")
        if not ((num.isdigit() and lo_n <= int(num) <= hi_n) or (dates and in_dates(dates[:10]))):
            continue
        unit, note = unit_for(spec, num, c.get("suffix", ""))
        rows.append({
            "manifest_group": "3_unnumbered_or_ambiguous_identity", "instrument_id": "",
            "proposed_id_not_in_census": c["instrument_id"], "eo_designation": designation(num, c.get("suffix", "")),
            "number": num, "suffix": c.get("suffix", ""), "signature_date": dates, "date_source": "dates_seen_beside_citation",
            "title": c.get("titles_seen", ""), "president": "", "census_class": "not_in_census_candidate",
            "likely_unit": unit, "likely_secondary_unit_unverified": unit if spec.get("secondary_unit_label") else None,
            "acquisition_priority": 4,
            "priority_reason": f"not a tracked order: census candidate named by {c.get('named_by', '')} (strength {c.get('strength') or 'unrated'}); an image would support census intake, not readiness",
            "staged_acquisitions": staged.get(c["instrument_id"], []),
            "missing": {"missing_accepted_original_witness": True, "missing_accepted_working_text": True,
                        "no_witness_of_any_kind": True},
            "tracker": {}, "domesday_best_held": "", "mabillon_best_route_20261105": "",
            "held": {"index_entries": [{"witness_class": "index_entry", "source": c.get("named_by", ""),
                                        "example_source": c.get("example_source", ""), "note": c.get("note", "")}]},
            "remote_evidence_not_retained_locally": [], "other_acquisition_routes_known": [],
            "identity_uncertainty": ["not in the census: an index or citation names it; identity unadjudicated"] + ([note] if note else []),
            "coverage_uncertainty": [f"{U} ranges are catalog routing leads, not proof that this order or variant survives in the collection"],
        })
    rows.sort(key=lambda x: (x["manifest_group"], x["acquisition_priority"],
                             int(x["number"]) if str(x["number"]).isdigit() else 10 ** 9, x["suffix"],
                             x["instrument_id"] or x.get("proposed_id_not_in_census", "")))
    return rows, summarize(spec, repo, d, rows, R, in_scope, base)


def summarize(spec, repo, d, rows, R, in_scope, base):
    C = collections.Counter
    U = spec["unit_label"]
    tracked = [x for x in rows if x["instrument_id"]]
    g1 = [x for x in tracked if x["manifest_group"].startswith("1")]

    def pre1933(ids):
        return sum(1 for i in ids if base(i)[5][:4].isdigit() and int(base(i)[5][:4]) < 1933)

    tier_not = [i for i, r in R.items() if r["text_evidence_tier"] != "original_supported"]
    step_open = [i for i, r in R.items() if r["step_original_text"] == "open"]
    excluded = C()
    for i in step_open:
        if i in in_scope:
            continue
        number, date = base(i)[3], base(i)[5]
        excluded["numbered above the last unit, outside the dates" if number.isdigit() else
                 "unnumbered, outside the dates" if not number else "other"] += 1
    unit_key = lambda v: (v is None, v or 0)  # noqa: E731
    return {
        "schema": "dagron-collection-manifest/v1", "collection": spec["id"], "commit": repo.commit,
        "tracker_generation": next(iter(R.values()))["generation_id"] if R else "",
        "domesday_generated": d["domesday_summary"].get("generated_utc"),
        "rows": len(rows), "tracked_unique_orders": len({x["instrument_id"] for x in tracked}),
        "untracked_census_candidates": len(rows) - len(tracked),
        "staged_orders": sum(1 for x in rows if x["staged_acquisitions"]),
        "by_group": dict(sorted(C(x["manifest_group"] for x in rows).items())),
        "by_group_and_priority": {g: dict(sorted(C(x["acquisition_priority"] for x in rows if x["manifest_group"] == g).items()))
                                  for g in sorted({x["manifest_group"] for x in rows})},
        f"by_{U}_and_group": {str(u): dict(sorted(C(x["manifest_group"] for x in rows if x["likely_unit"] == u).items()))
                              for u in sorted({x["likely_unit"] for x in rows}, key=unit_key)},
        "group1_priority_reasons": dict(C(f"P{x['acquisition_priority']} {x['priority_reason'].split(';')[0].split(':')[0]}" for x in g1).most_common()),
        "group1_missing_categories": {k: sum(1 for x in g1 if x["missing"].get(k)) for k in (g1[0]["missing"] if g1 else {})},
        "group1_by_step_original_text": dict(C(x["tracker"]["step_original_text"] for x in g1)),
        "group1_with_remote_evidence_not_retained": sum(1 for x in g1 if x["remote_evidence_not_retained_locally"]),
        "group1_remote_kinds": dict(C(e["kind"] for x in g1 for e in x["remote_evidence_not_retained_locally"]).most_common()),
        "group1_other_routes": dict(C(e["route"] for x in g1 for e in x["other_acquisition_routes_known"]).most_common()),
        "group1_pre1933": sum(1 for x in g1 if x["signature_date"][:4].isdigit() and int(x["signature_date"][:4]) < 1933),
        "group1_undated": sum(1 for x in g1 if not x["signature_date"][:4].isdigit()),
        "tracker_measures": {
            "universe": len(R),
            "step_original_text_open": {"all": len(step_open), "pre1933_dated": pre1933(step_open),
                                        "not_in_manifest_by_reason": dict(excluded)},
            "text_evidence_tier_not_original_supported": {"all": len(tier_not), "pre1933_dated": pre1933(tier_not)},
        },
        "what_this_is_not": "A routing list. No identity, custody grade, readiness count or legal status changes here.",
    }


def gz_write(path, text):
    with open(path, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as fh:
        fh.write(text.encode("utf-8"))


def flat(x):
    held = x.get("held", {})
    allf = [f for k in ("signed_original_replica_scans", "official_printed_copies", "uncounted_printings_or_reprints",
                        "transcriptions") for f in held.get(k, [])]
    m, t = x.get("missing", {}), x.get("tracker", {})
    row = {k: x.get(k, "") for k in CSV_COLS if k in x}
    row.update({k: m.get(k, "") for k in CSV_COLS if k in m})
    row.update({k: t.get(k, "") for k in CSV_COLS if k in t})
    row["original_text_blockers"] = "|".join(t.get("original_text_blockers", []))
    row["staged_acquisitions"] = " ; ".join(f"{s['collection']}:{s['file']}" for s in x.get("staged_acquisitions", []))
    row["retained_files"] = " ; ".join(f"{f['witness_class']}:{p}" for f in allf
                                       for p in (f.get("source_bytes_retained_path"), f.get("text_path")) if p)
    row["source_refs"] = " ; ".join([f"{f['witness_class']}|{f['produced_by']}|{f.get('page_or_item', '')}|{f.get('url', '')}" for f in allf] +
                                    [f"index_entry|{e.get('source', '')}|{e.get('wpa_citations', e.get('naIds', ''))}" for e in held.get("index_entries", [])])
    row["remote_not_retained"] = " ; ".join(f"{e['kind']}: {e.get('url', '')}" for e in x.get("remote_evidence_not_retained_locally", []))
    row["other_routes_known"] = " ; ".join(f"{e['route']}: {e['lead_url_or_search']}" for e in x.get("other_acquisition_routes_known", []))
    row["identity_uncertainty"] = " ; ".join(x.get("identity_uncertainty", []))
    row["coverage_uncertainty"] = " ; ".join(x.get("coverage_uncertainty", []))
    return row


def sample(rows):
    """A small, stable, representative sample: one row per distinct situation."""
    tests = [
        lambda x: x["manifest_group"].startswith("1") and x["missing"].get("original_copy_replacement_required"),
        lambda x: x["manifest_group"].startswith("1") and x["missing"].get("no_witness_of_any_kind"),
        lambda x: x["manifest_group"].startswith("1") and x["acquisition_priority"] == 1 and x["missing"].get("has_transcription_only"),
        lambda x: x["manifest_group"].startswith("1") and x["acquisition_priority"] == 2 and x["missing"].get("has_signed_original_replica_scan"),
        lambda x: x["manifest_group"].startswith("1") and x["acquisition_priority"] == 2 and not x["missing"].get("has_signed_original_replica_scan"),
        lambda x: x["manifest_group"].startswith("1") and x["acquisition_priority"] == 3,
        lambda x: x["manifest_group"].startswith("1") and any("last item" in c or "variant of" in c for c in x["coverage_uncertainty"]),
        lambda x: x["manifest_group"].startswith("1") and x["suffix"] == "½",
        lambda x: x["manifest_group"].startswith("2"),
        lambda x: x["manifest_group"].startswith("3") and x["instrument_id"] and not x["number"],
        lambda x: x["manifest_group"].startswith("3") and x["suffix"].startswith("-"),
        lambda x: x["manifest_group"].startswith("3") and not x["instrument_id"],
        lambda x: x["manifest_group"].startswith("4"),
    ]
    out = []
    for t in tests:
        hit = next((x for x in rows if t(x) and x not in out), None)
        if hit:
            out.append(hit)
    return out


def report(spec, s):
    U = spec["unit_label"]
    lines = [f"# {spec['name']}", "", f"Generated by `jobs/dagron-collection-manifest` from commit `{s['commit']}` "
             f"(tracker generation `{s['tracker_generation']}`). {s['rows']} rows: {s['tracked_unique_orders']} tracked "
             f"orders and {s['untracked_census_candidates']} census candidates; {s['staged_orders']} with staged images.", "",
             "| Group | Rows | By priority |", "|---|---:|---|"]
    for g, n in s["by_group"].items():
        lines.append(f"| `{g}` | {n} | {', '.join(f'P{k}: {v}' for k, v in s['by_group_and_priority'][g].items())} |")
    groups = list(s["by_group"])
    lines += ["", f"| {U} | " + " | ".join(groups) + " |", "|---|" + "---:|" * len(groups)]
    for u, c in s[f"by_{U}_and_group"].items():
        lines.append(f"| {u} | " + " | ".join(str(c.get(g, 0)) for g in groups) + " |")
    lines += ["", "Group 1 missing-evidence flags (overlapping): " +
              "; ".join(f"{k} {v}" for k, v in s["group1_missing_categories"].items()) + ".", "",
              f"Tracker measures: original-text step open {s['tracker_measures']['step_original_text_open']['all']} "
              f"({s['tracker_measures']['step_original_text_open']['pre1933_dated']} dated before 1933); not original-supported "
              f"{s['tracker_measures']['text_evidence_tier_not_original_supported']['all']}.", "",
              "Restrictions recorded for this collection:", ""] + [f"- {r}" for r in spec.get("restrictions", [])]
    return "\n".join(lines) + "\n"


def main(argv):
    root = argv[0] if len(argv) > 0 else os.environ.get("REPO_ROOT", ".")
    out = argv[1] if len(argv) > 1 else os.environ.get("OUTPUT_DIR", "output")
    specs = argv[2:] or sorted(glob.glob(os.path.join(HERE, "collections", "*.json")))
    repo = Repo(root)
    d = load(repo)
    totals = {}
    for path in specs:
        with open(path, encoding="utf-8") as fh:
            spec = json.load(fh)
        rows, s = build(spec, repo, d)
        od = os.path.join(out, spec["id"])
        os.makedirs(od, exist_ok=True)
        gz_write(os.path.join(od, "MANIFEST.jsonl.gz"), "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows))
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=CSV_COLS, lineterminator="\n")
        w.writeheader()
        for x in rows:
            w.writerow(flat(x))
        gz_write(os.path.join(od, "MANIFEST.csv.gz"), buf.getvalue())
        with open(os.path.join(od, "SAMPLE.jsonl"), "w", encoding="utf-8") as fh:
            for x in sample(rows):
                fh.write(json.dumps(x, ensure_ascii=False) + "\n")
        with open(os.path.join(od, "SUMMARY.json"), "w", encoding="utf-8") as fh:
            json.dump(s, fh, indent=1, ensure_ascii=False)
        with open(os.path.join(od, "REPORT.md"), "w", encoding="utf-8") as fh:
            fh.write(report(spec, s))
        totals[spec["id"]] = {"rows": s["rows"], "by_group": s["by_group"]}
    with open(os.path.join(out, "SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump({"schema": "dagron-collection-manifest/v1", "commit": repo.commit, "collections": totals}, fh, indent=1)
    print(json.dumps(totals, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])

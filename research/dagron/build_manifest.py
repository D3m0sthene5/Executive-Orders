"""Dagron: order-level acquisition manifest for NYU Bobst Film 709 (Trans-Media "Presidential executive orders",
11 reels, EO 1-7403) and NYU's HeinOnline "Presidential Executive Orders" (11 volumes, 1845-1936).

Named for Rene Dagron, who put the dispatches of besieged Paris (1870-71) on microfilm for the pigeon post.

Read-only. Every input is read from ONE pinned commit with `git show`, so the manifest is reproducible:

    python3 -I research/dagron/build_manifest.py COMMIT OUT_DIR

It changes no status, readiness count, census row, codebook text or job output. It decides nothing about
identity or custody: it lists, per order, what the project holds and what is missing, so a browser agent can
fetch images from the NYU collection. The readiness tracker's own output at COMMIT is the authority for whether
the original-text step is satisfied; this script never recomputes or overrides it.
"""
import collections
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys

csv.field_size_limit(1 << 30)

# Cataloged reel ranges (NYU record alma990007538410107876). Routing leads only.
REELS = [(1, "1", "707"), (2, "708", "1348"), (3, "1349", "2125"), (4, "2126", "2891"), (5, "2892", "3579"),
         (6, "3580", "4304"), (7, "4305", "5075"), (8, "5076", "5760"), (9, "5761", "6336"), (10, "6337", "6925"),
         (11, "6925A", "7403")]
REEL_END = {int(re.match(r"\d+", e).group()): n for n, _, e in REELS}
DATE_LO, DATE_HI = "1845-01-01", "1936-12-31"  # HeinOnline's stated coverage

# Evidence lanes exactly as jobs/readiness-tracker/tracker.py reads them (J dict), plus app-transcriptions.
LANES = {
    # official printed copies; counted by the tracker only when the job did not flag needs_page_check
    "fr-originals": ("official_printed_copy", "counting_lane"),
    "ofr-compilations": ("official_printed_copy", "counting_lane"),
    "isthmian-canal-1911": ("official_printed_copy", "counting_lane"),
    "indian-reservations-1912": ("official_printed_copy", "counting_lane"),
    "tischendorf-originals": ("official_printed_copy", "counting_lane"),
    "mabillon-held-printings": ("official_printed_copy", "counting_lane"),
    # Opus Stage 9/11 evidence originals matched to the order (counted by the tracker)
    "opus-media-match": ("opus_media_original", "counting_lane"),
    # ProQuest "Replica of Original": a scan of the signed original, lead only until page check + codebook grade
    "pinakes-proquest-ingest": ("signed_original_replica_scan", "lead_only_until_page_check_and_grade"),
    # compiled transcriptions and uncounted printings: leads only, never the original (tracker J comment)
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
TEXT_BLOCKERS = ("ORIGINAL_FOUND_NEEDS_PAGE_CHECK", "OFFICIAL_URL_KNOWN_NOT_DOWNLOADED", "NO_OFFICIAL_SOURCE_LOCATED",
                 "ONLY_COMPILED_TRANSCRIPTION_FOUND", "ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK")
PATH_KEYS = ("cache_path", "path", "repository_path", "file", "local_path", "retained_path")


def git(*args, binary=False):
    out = subprocess.run(["git", *args], capture_output=True, check=True).stdout
    return out if binary else out.decode("utf-8")


class Repo:
    def __init__(self, commit):
        self.commit = commit
        self.tree = set(git("ls-tree", "-r", "--name-only", commit).splitlines())

    def text(self, path):
        return git("show", f"{self.commit}:{path}") if path in self.tree else None

    def csv(self, path):
        t = self.text(path)
        return list(csv.DictReader(io.StringIO(t))) if t is not None else []

    def jsonl(self, path):
        t = self.text(path)
        out = []
        for line in (t or "").splitlines():
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return out

    def sha256(self, path):
        p = subprocess.Popen(["git", "cat-file", "blob", f"{self.commit}:{path}"], stdout=subprocess.PIPE)
        h = hashlib.sha256()
        for chunk in iter(lambda: p.stdout.read(1 << 20), b""):
            h.update(chunk)
        p.wait()
        return h.hexdigest()


def designation(number, suffix):
    if not number:
        return ""
    return f"EO {number}{suffix}" if suffix and not suffix.startswith("-") else f"EO {number}{suffix}"


def reel_for(number, suffix):
    """Likely reel from the cataloged ranges, with a boundary note. Leads only."""
    n = int(number)
    if n < 1 or n > 7403:
        return None, ""
    for reel, s, e in REELS:
        sn, en = int(re.match(r"\d+", s).group()), int(re.match(r"\d+", e).group())
        if sn <= n <= en:
            if n == 6925:
                return (11, "") if suffix else (10, "EO 6925 is the last item of reel 10; reel 11 starts at 6925A")
            note = ""
            if n == en and suffix:
                note = (f"variant of reel {reel}'s last number: may follow {n} on reel {reel} or open reel {reel + 1} "
                        "(the catalog starts reel 11 at 6925A)")
            elif n == sn and reel > 1:
                note = f"first number of reel {reel}"
            return reel, note
    return None, ""


def main(commit, out_dir):
    repo = Repo(commit)
    os.makedirs(out_dir, exist_ok=True)
    R = {r["instrument_id"]: r for r in repo.csv("jobs/readiness-tracker/output/READINESS_BY_ORDER.csv")}
    D = {r["instrument_id"]: r for r in repo.csv("jobs/domesday-register/output/REGISTER.csv")}
    census = {r["id"]: r for r in repo.csv("research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv")}
    admissions = {r["id"]: r for r in repo.csv("research/stage15/CENSUS/ADMISSIONS_2026-11-06.csv")}
    candidates = repo.csv("jobs/domesday-register/output/CANDIDATES_NOT_IN_REGISTER.csv")
    frame = {r["instrument_id"]: r for r in repo.csv("research/mabillon/frame/FRAME.csv")}
    mab_cov = {r["instrument_id"]: r for r in repo.csv("research/mabillon/frame/COVERAGE.csv")}
    lewis = {r["instrument_id"]: r for r in repo.csv("jobs/lewis-originals/output/ROUTES.csv")}
    nara = {r["instrument_id"]: r for r in repo.csv("jobs/mabillon-nara/output/BY_ORDER.csv")}
    pq_orders = {r["instrument_id"]: r for r in repo.csv("jobs/pinakes-proquest-ingest/output/ORDERS.csv")}
    pq_missing = {r["instrument_id"]: r for r in repo.csv("jobs/pinakes-proquest-ingest/output/MISSING_FROM_UPLOAD.csv")}
    custody = {r["instrument_id"]: r for r in repo.csv("research/stage21/original_sources/CASE_ORIGINAL_SOURCE_CUSTODY.csv")}
    causal = {r["instrument_id"]: r for r in repo.csv("research/stage19/output/CAUSAL_QUEUE.csv")}
    crosswalk = {r["instrument_id"]: r for r in repo.csv("research/stage21/sources_index/OFFICIAL_SOURCE_CASE_CROSSWALK.csv")}
    generation = next(iter(R.values()))["generation_id"] if R else ""
    alias_of = {}
    for i in R:
        if i not in D and i.upper() != i and i.upper() in D:
            alias_of[i] = i.upper()
    for i in D:
        if i not in R and i.upper() in R:
            alias_of[i] = i.upper()

    # sha256 -> retained repository path, from every committed SOURCES index plus held source books.
    retained = {}
    for path in sorted(p for p in repo.tree if re.search(r"(^|/)SOURCES[^/]*\.jsonl$", p) and not p.startswith("jobs/_attempts/")):
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
                    cand = os.path.normpath(cand)
                    if cand in repo.tree:
                        retained.setdefault(sha, cand)
                        break
    for path in sorted(p for p in repo.tree if p.startswith("releases/source_books/") and p.endswith(".pdf")):
        retained.setdefault(repo.sha256(path), path)
    for r in custody.values():
        if r.get("sha256") and r.get("repository_path") in repo.tree:
            retained.setdefault(r["sha256"], r["repository_path"])

    # every original_representation fragment per order
    frags = collections.defaultdict(list)
    for path in FRAGMENT_FILES:
        job = path.split("/")[1]
        for r in repo.jsonl(path):
            if r.get("kind") != "original_representation" or not isinstance(r.get("instrument_id"), str):
                continue
            d = r.get("data") if isinstance(r.get("data"), dict) else {}
            lane_class, lane_rule = LANES[job]
            counted = lane_rule == "counting_lane" and d.get("needs_page_check") is False
            if job == "opus-media-match":
                counted = True
            text_path = d.get("text_path") or ""
            text_repo = os.path.normpath(f"jobs/{job}/output/{text_path}") if text_path else ""
            src_sha = d.get("sha256") or d.get("local_file_sha256") or ""
            file_repo = d.get("file") if d.get("file") in repo.tree else ""
            ret = file_repo or retained.get(src_sha, "")
            url = d.get("url") or d.get("upstream_url") or d.get("book_item_url") or ""
            if not url:
                for s in r.get("sources") or []:
                    if isinstance(s, dict) and (s.get("url") or s.get("upstream_url")):
                        url = s.get("url") or s.get("upstream_url")
                        break
            frags[r["instrument_id"]].append({
                "witness_class": lane_class,
                "tracker_rule": lane_rule,
                "counted_by_tracker_rule": counted,
                "produced_by": job,
                "fragment_file": path,
                "grade": r.get("grade") or d.get("grade") or "",
                "representation_type": r.get("representation_type") or d.get("representation_type") or "",
                "needs_page_check": d.get("needs_page_check"),
                "acceptable_as_original": r.get("acceptable_as_original", d.get("acceptable_as_original")),
                "page_or_item": d.get("page_or_item") or "",
                "route": d.get("route") or "",
                "url": url,
                "source_sha256": src_sha,
                "source_bytes_retained_path": ret,
                "text_path": text_repo if text_repo in repo.tree else "",
                "text_path_declared_but_absent": text_repo if text_repo and text_repo not in repo.tree else "",
                "text_usable": (pq_orders.get(r["instrument_id"], {}).get("text_usable", "")
                                if job == "pinakes-proquest-ingest" else ""),
                "signing_date_seen": d.get("signing_date") or d.get("app_date") or d.get("match_date") or "",
            })

    rows, group_of = [], {}

    def base_record(i):
        r, dm = R.get(i, {}), D.get(i) or D.get(alias_of.get(i, ""), {}) or {}
        ce = census.get(i) or census.get(alias_of.get(i, ""), {}) or {}
        ad = admissions.get(i, {})
        number = dm.get("number") or ad.get("number") or ""
        suffix = dm.get("suffix") if dm else ad.get("suffix", "")
        date = dm.get("date") or ad.get("date") or ""
        date_source = dm.get("date_source") or ("admission_held_official" if ad.get("date") else "")
        if not date and ce.get("date_effective"):
            date, date_source = ce["date_effective"], f"census:{ce.get('date_source_type', '')}"
        title = dm.get("title") or ""
        return r, dm, ce, ad, number, suffix or "", date, date_source, title

    def evidence(i):
        fs = frags.get(i, [])
        by = collections.defaultdict(list)
        for f in fs:
            by[f["witness_class"]].append(f)
        idx = []
        ce = census.get(i, {})
        if ce.get("bibliographic_class") in ("validated_historical_index", "documented_unnumbered"):
            idx.append({"witness_class": "index_entry", "source": f"census bibliographic_class={ce['bibliographic_class']}",
                        "date_source_type": ce.get("date_source_type", "")})
        fr_ = frame.get(i, {})
        if fr_.get("wpa_citations"):
            idx.append({"witness_class": "index_entry", "source": "WPA/Lord numbered list citation",
                        "wpa_citations": fr_["wpa_citations"], "wpa_print_kinds": fr_.get("wpa_print_kinds", "")})
        na = nara.get(i)
        if na:
            idx.append({"witness_class": "index_entry" if na.get("with_objects") in ("", "0") else "signed_original_image_remote",
                        "source": "NARA catalog (RG 11) description", "naIds": na.get("naIds", ""),
                        "objects": na.get("objects", ""), "first_object_url": na.get("first_object_url", ""),
                        "retained_locally": False})
        return fs, by, idx

    def remote_only(i, fs):
        out = []
        for f in fs:
            if f["url"] and not f["source_bytes_retained_path"]:
                out.append({"kind": f"{f['witness_class']} source bytes not retained (text {'retained' if f['text_path'] else 'not retained'})",
                            "produced_by": f["produced_by"], "url": f["url"], "sha256": f["source_sha256"]})
        pm = pq_missing.get(i)
        dm = D.get(i, {})
        if pm or (dm.get("proquest_link_supplied") == "yes" and not dm.get("proquest_pdf_file")):
            out.append({"kind": "ProQuest 'Replica of Original' link supplied, PDF not in repository",
                        "url": (lewis.get(i, {}).get("lead_url_or_search") or (pm or {}).get("rec", ""))})
        na = nara.get(i)
        if na and na.get("first_object_url"):
            out.append({"kind": "NARA digitized object (image of signed original), not retained",
                        "url": na["first_object_url"], "naIds": na.get("naIds", "")})
        cx = crosswalk.get(i, {})
        if cx.get("selected_literal_URL"):
            out.append({"kind": "Stage 21 crosswalk official URL", "url": cx["selected_literal_URL"]})
        return out

    def other_routes(i):
        """Other acquisition leads already recorded (searches and ranges, not located copies)."""
        lw = lewis.get(i, {})
        if not lw.get("best_route") or lw["best_route"] == "proquest_local":
            return []
        return [{"router": "lewis-originals", "route": lw["best_route"], "status": lw.get("route_status", ""),
                 "next_action": lw.get("next_action", ""), "lead_url_or_search": lw.get("lead_url_or_search", "")}]

    in_scope_ids = set()
    for i in sorted(R):
        r, dm, ce, ad, number, suffix, date, date_source, title = base_record(i)
        numbered = bool(number) and number.isdigit()
        n = int(number) if numbered else None
        identity = []
        coverage = []
        group = None
        step, tier = r.get("step_original_text", ""), r.get("text_evidence_tier", "")
        missing_original = tier != "original_supported"
        fs, by, idx = evidence(i)
        counted = [f for f in fs if f["counted_by_tracker_rule"]]
        has_counted_text = any(f["text_path"] for f in counted)
        missing_working_text = step == "open" or (not missing_original and not has_counted_text)
        in_dates = (not date) or (DATE_LO <= date[:10].ljust(10, "0") <= DATE_HI) or (len(date) == 4 and DATE_LO[:4] <= date <= DATE_HI[:4])
        if suffix.startswith("-"):
            identity.append(f"numeric suffix '{suffix}' (a second order recorded under number {number}); the film's "
                            "numbered sequence may hold only one item for this number")
        if suffix == "½":
            identity.append("fraction designation; the film may file it beside its base number")
        elif suffix and suffix.isalpha():
            identity.append(f"lettered variant '{suffix}'; check that the reel carries it as its own item")
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
        if date and len(date) == 10 and seen:
            identity.append("other dates seen in held sources: " + "|".join(sorted(seen)[:4]))
        if not title:
            identity.append("no title on record")
        if i in admissions:
            identity.append("admitted to the census 2026-11-06 (claim-kit population contract); not in Domesday's 14,972")

        if numbered and 1 <= n <= 7403:
            if suffix.startswith("-") or i in alias_of:
                group = "3_unnumbered_or_ambiguous_identity"
            elif missing_original:
                group = "1_missing_accepted_original_witness"
            elif missing_working_text:
                group = "2_missing_accepted_working_text_only"
        elif not numbered:
            if in_dates:
                group = "3_unnumbered_or_ambiguous_identity"
                identity.append("unnumbered order: inclusion in the numbered film or Hein volumes is NOT established")
        elif numbered and n > 7403 and date and date[:4] <= "1936" and (missing_original or missing_working_text):
            group = "4_edge_numbered_after_reel_11_within_hein_dates"
            coverage.append("number above the last cataloged reel (7403); only Hein's stated 1845-1936 range suggests coverage")
        if group is None:
            continue
        reel, reel_note = reel_for(number, suffix) if numbered else (None, "")
        if reel_note:
            coverage.append(reel_note)
        if group.startswith("3") and not numbered:
            coverage.append("no number: locate by date and title in the volume or reel covering the date; may be absent")
        if date and date < "1862-02-14" and not numbered:
            coverage.append("predates EO 1 (1862): only Hein's 1845 start suggests coverage")
        coverage.append("reel ranges are catalog routing leads, not proof that this order or variant survives on film")

        # what exists, by distinction
        replica = by.get("signed_original_replica_scan", [])
        official = by.get("official_printed_copy", []) + by.get("opus_media_original", [])
        if ad.get("held_official_path"):
            # census admission of 2026-11-06: the admitting record names a held official printing
            official = official + [{
                "witness_class": "official_printed_copy", "tracker_rule": "census_admission_record",
                "counted_by_tracker_rule": False, "produced_by": "census admission " + ad.get("source_row", ""),
                "fragment_file": "research/stage15/CENSUS/ADMISSIONS_2026-11-06.csv", "grade": "", "representation_type": "",
                "needs_page_check": None, "acceptable_as_original": None, "page_or_item": ad.get("held_official_page", ""),
                "route": "", "url": "", "source_sha256": ad.get("held_official_sha256", ""),
                "source_bytes_retained_path": ad["held_official_path"] if ad["held_official_path"] in repo.tree else "",
                "text_path": ad.get("text_path", "") if ad.get("text_path", "") in repo.tree else "",
                "text_path_declared_but_absent": "", "text_usable": "", "signing_date_seen": ad.get("date", "")}]
        uncounted_print = by.get("official_printed_copy_uncounted_lane", []) + by.get("report_reprint", [])
        trans = by.get("transcription", [])
        image_retained = any(f["source_bytes_retained_path"] for f in replica + official + uncounted_print)
        replica_text_usable = any(f["text_usable"] == "yes" for f in replica)
        blockers = [b for b in (r.get("blockers") or "").split("|") if b]
        text_blockers = [b for b in blockers if b in TEXT_BLOCKERS]
        flags = {
            "missing_accepted_original_witness": missing_original,
            "missing_accepted_working_text": missing_working_text,
            "original_copy_replacement_required": r.get("original_copy_replacement_required") == "yes",
            "no_image_of_any_kind_retained": not image_retained,
            "has_signed_original_replica_scan": bool(replica),
            "replica_scan_text_usable": replica_text_usable if replica else None,
            "has_official_printed_copy_lead": bool(official) and not counted,
            "has_uncounted_printing_or_reprint": bool(uncounted_print),
            "has_transcription_only": bool(trans) and not (replica or official or uncounted_print),
            "no_witness_of_any_kind": not fs,
        }
        # priority (1 = acquire first); see README for the rule
        if group.startswith("1"):
            if flags["original_copy_replacement_required"]:
                pr, why = 1, "working text accepted only provisionally (transcription-dependent); an official image replaces it and closes the recheck"
            elif not replica and not official and not uncounted_print:
                pr, why = 1, "no image or printing of any kind held; NYU may be the only reachable image"
            elif replica and not replica_text_usable:
                pr, why = 2, "only a ProQuest replica scan, whose text is unusable (likely handwritten); NYU image is a second witness"
            elif not replica:
                kinds = ([f"official printing lead flagged for a page check ({', '.join(sorted({f['produced_by'] for f in official}))})"] if official else []) + \
                        ([f"uncounted printing or reprint ({', '.join(sorted({f['produced_by'] for f in uncounted_print}))})"] if uncounted_print else [])
                pr, why = 2, "no image of the signed original; held only: " + "; ".join(kinds)
            else:
                pr, why = 3, "ProQuest replica scan held with usable text, pending page check; NYU image corroborates"
            if r.get("claim_present") == "yes" or r.get("provisional_status") in ("yes", "no"):
                why += "; order already has a provisional status or claim"
        elif group.startswith("2"):
            pr, why = 3, "counted original witness on record but no retained working text for it"
        elif group.startswith("3"):
            pr, why = 4, "identity or inclusion must be confirmed before any image is attached"
        else:
            pr, why = 5, "outside the cataloged reels; check Hein only"
        rec = {
            "manifest_group": group,
            "instrument_id": i,
            "eo_designation": designation(number, suffix) if numbered else "(unnumbered)",
            "number": number, "suffix": suffix,
            "signature_date": date, "date_source": date_source,
            "title": title, "president": dm.get("president", ""),
            "census_class": dm.get("census_class") or ce.get("bibliographic_class", ""),
            "likely_reel": reel, "likely_hein_volume_unverified": reel,
            "acquisition_priority": pr, "priority_reason": why,
            "missing": flags,
            "tracker": {"step_original_text": step, "text_evidence_tier": tier, "original_text_blockers": text_blockers,
                        "provisional_status": r.get("provisional_status", ""), "claim_present": r.get("claim_present", ""),
                        "ready_for_human_review": r.get("ready_for_human_review", ""),
                        "provisional_text_grade": r.get("provisional_text_grade", ""),
                        "informational_flags": r.get("informational_flags", "")},
            "domesday_best_held": dm.get("best_held", ""),
            "mabillon_best_route_20261105": mab_cov.get(i, {}).get("best_route", ""),
            "held": {
                "signed_original_replica_scans": replica,
                "official_printed_copies": official,
                "uncounted_printings_or_reprints": uncounted_print,
                "transcriptions": trans,
                "index_entries": idx,
                "stage21_custody_state": custody.get(i, {}).get("custody_state", ""),
                "stage19_locally_preserved_primary": causal.get(i, {}).get("locally_preserved_primary_representation", ""),
            },
            "remote_evidence_not_retained_locally": remote_only(i, fs),
            "other_acquisition_routes_known": other_routes(i),
            "identity_uncertainty": identity,
            "coverage_uncertainty": coverage,
        }
        rows.append(rec)
        in_scope_ids.add(i)

    # Census candidates that something names but the census does not hold (never tracked rows)
    for c in candidates:
        num = c.get("number", "")
        dates = c.get("dates_seen", "")
        if not ((num.isdigit() and int(num) <= 7403) or (dates and dates[:4] <= "1936")):
            continue
        reel, reel_note = reel_for(num, c.get("suffix", "")) if num.isdigit() else (None, "")
        rows.append({
            "manifest_group": "3_unnumbered_or_ambiguous_identity",
            "instrument_id": "", "proposed_id_not_in_census": c["instrument_id"],
            "eo_designation": designation(num, c.get("suffix", "")),
            "number": num, "suffix": c.get("suffix", ""), "signature_date": dates, "date_source": "dates_seen_beside_citation",
            "title": c.get("titles_seen", ""), "president": "", "census_class": "not_in_census_candidate",
            "likely_reel": reel, "likely_hein_volume_unverified": reel,
            "acquisition_priority": 4,
            "priority_reason": f"not a tracked order: census candidate named by {c.get('named_by', '')} (strength {c.get('strength', '') or 'unrated'}); an image would support census intake, not readiness",
            "missing": {"missing_accepted_original_witness": True, "missing_accepted_working_text": True,
                        "no_witness_of_any_kind": True},
            "tracker": {}, "domesday_best_held": "", "mabillon_best_route_20261105": "",
            "held": {"index_entries": [{"witness_class": "index_entry", "source": c.get("named_by", ""),
                                        "example_source": c.get("example_source", ""), "note": c.get("note", "")}]},
            "remote_evidence_not_retained_locally": [], "other_acquisition_routes_known": [],
            "identity_uncertainty": ["not in the census: an index or citation names it; identity unadjudicated"] + ([reel_note] if reel_note else []),
            "coverage_uncertainty": ["reel ranges are catalog routing leads, not proof that this order or variant survives on film"],
        })

    rows.sort(key=lambda x: (x["manifest_group"], x["acquisition_priority"],
                             int(x["number"]) if str(x["number"]).isdigit() else 10 ** 9, x["suffix"], x["instrument_id"]))
    with open(os.path.join(out_dir, "NYU_FILM709_MANIFEST.jsonl"), "w", encoding="utf-8") as fh:
        for x in rows:
            fh.write(json.dumps(x, ensure_ascii=False, sort_keys=False) + "\n")
    flat_cols = ["manifest_group", "acquisition_priority", "instrument_id", "proposed_id_not_in_census", "eo_designation",
                 "number", "suffix", "signature_date", "date_source", "title", "president", "census_class",
                 "likely_reel", "likely_hein_volume_unverified", "missing_accepted_original_witness",
                 "missing_accepted_working_text", "original_copy_replacement_required", "no_image_of_any_kind_retained",
                 "has_signed_original_replica_scan", "replica_scan_text_usable", "has_official_printed_copy_lead",
                 "has_uncounted_printing_or_reprint", "has_transcription_only", "no_witness_of_any_kind",
                 "step_original_text", "text_evidence_tier", "original_text_blockers", "provisional_status", "claim_present",
                 "domesday_best_held", "mabillon_best_route_20261105", "retained_files", "source_refs",
                 "remote_not_retained", "other_routes_known", "identity_uncertainty", "coverage_uncertainty", "priority_reason"]
    with open(os.path.join(out_dir, "NYU_FILM709_MANIFEST.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=flat_cols)
        w.writeheader()
        for x in rows:
            held = x.get("held", {})
            allf = [f for k in ("signed_original_replica_scans", "official_printed_copies",
                                "uncounted_printings_or_reprints", "transcriptions") for f in held.get(k, [])]
            files = []
            for f in allf:
                for p in (f.get("source_bytes_retained_path"), f.get("text_path")):
                    if p:
                        files.append(f"{f['witness_class']}:{p}")
            refs = [f"{f['witness_class']}|{f['produced_by']}|{f.get('page_or_item', '')}|{f.get('url', '')}" for f in allf]
            refs += [f"index_entry|{e.get('source', '')}|{e.get('wpa_citations', e.get('naIds', ''))}" for e in held.get("index_entries", [])]
            m, t = x.get("missing", {}), x.get("tracker", {})
            row = {k: x.get(k, "") for k in flat_cols if k in x}
            row.update({k: m.get(k, "") for k in flat_cols if k in m})
            row.update({k: t.get(k, "") for k in flat_cols if k in t})
            row["original_text_blockers"] = "|".join(t.get("original_text_blockers", []))
            row["retained_files"] = " ; ".join(files)
            row["source_refs"] = " ; ".join(refs)
            row["remote_not_retained"] = " ; ".join(f"{e['kind']}: {e.get('url', '')}" for e in x.get("remote_evidence_not_retained_locally", []))
            row["other_routes_known"] = " ; ".join(f"{e['route']}: {e['lead_url_or_search']}" for e in x.get("other_acquisition_routes_known", []))
            row["identity_uncertainty"] = " ; ".join(x.get("identity_uncertainty", []))
            row["coverage_uncertainty"] = " ; ".join(x.get("coverage_uncertainty", []))
            w.writerow(row)

    # summary + reconciliation
    C = collections.Counter
    tracked = [x for x in rows if x["instrument_id"]]

    def yr(x):
        d = x["signature_date"] or ""
        return int(d[:4]) if d[:4].isdigit() else None

    def pre1933(ids):
        return sum(1 for i in ids if (lambda d: d[:4].isdigit() and int(d[:4]) < 1933)(base_record(i)[6]))

    tier_not = [i for i, r in R.items() if r["text_evidence_tier"] != "original_supported"]
    step_open = [i for i, r in R.items() if r["step_original_text"] == "open"]
    nosrc = [i for i, r in R.items() if "NO_OFFICIAL_SOURCE_LOCATED" in r["blockers"]]
    dm_not = [i for i, r in D.items() if r["best_held"] != "official_original_counted"]
    g1 = [x for x in tracked if x["manifest_group"].startswith("1")]
    summary = {
        "schema": "dagron-nyu-film709-manifest/v1",
        "commit": commit, "tracker_generation": generation,
        "domesday_generated": (json.loads(repo.text("jobs/domesday-register/output/SUMMARY.json") or "{}").get("generated_utc")),
        "rows": len(rows), "tracked_unique_orders": len({x["instrument_id"] for x in tracked}),
        "untracked_census_candidates": len(rows) - len(tracked),
        "by_group": dict(sorted(C(x["manifest_group"] for x in rows).items())),
        "by_group_and_priority": {g: dict(sorted(C(x["acquisition_priority"] for x in rows if x["manifest_group"] == g).items()))
                                  for g in sorted({x["manifest_group"] for x in rows})},
        "by_reel": {str(k): v for k, v in sorted(C(x["likely_reel"] for x in rows).items(), key=lambda kv: (kv[0] is None, kv[0] or 0))},
        "by_reel_and_group": {str(rl): dict(sorted(C(x["manifest_group"] for x in rows if x["likely_reel"] == rl).items()))
                              for rl in sorted({x["likely_reel"] for x in rows}, key=lambda v: (v is None, v or 0))},
        "group1_missing_categories": {k: sum(1 for x in g1 if x["missing"].get(k)) for k in g1[0]["missing"]} if g1 else {},
        "group1_by_step_original_text": dict(C(x["tracker"]["step_original_text"] for x in g1)),
        "group1_by_text_evidence_tier": dict(C(x["tracker"]["text_evidence_tier"] for x in g1)),
        "group1_by_domesday_best_held": dict(C(x["domesday_best_held"] for x in g1)),
        "group1_with_remote_evidence_not_retained": sum(1 for x in g1 if x["remote_evidence_not_retained_locally"]),
        "group1_remote_kinds": dict(C(e["kind"] for x in g1 for e in x["remote_evidence_not_retained_locally"]).most_common(20)),
        "group1_other_routes": dict(C(e["route"] for x in g1 for e in x.get("other_acquisition_routes_known", []))),
        "group3_breakdown": dict(C(("not_in_census_candidate" if not x["instrument_id"] else
                                     "unnumbered" if not x["number"] else "numeric_suffix_or_alias")
                                    for x in rows if x["manifest_group"].startswith("3"))),
        "group1_pre1933": sum(1 for x in g1 if (yr(x) or 9999) < 1933), "group1_undated": sum(1 for x in g1 if yr(x) is None),
        "reconciliation_current_definitions": {
            "tracker_universe": len(R),
            "text_evidence_tier_not_original_supported": {"all": len(tier_not), "pre1933_dated": pre1933(tier_not)},
            "step_original_text_open": {"all": len(step_open), "pre1933_dated": pre1933(step_open)},
            "blocker_NO_OFFICIAL_SOURCE_LOCATED": {"all": len(nosrc), "pre1933_dated": pre1933(nosrc)},
            "domesday_best_held_not_official_original_counted": {"all": len(dm_not), "pre1933_dated": pre1933(dm_not),
                                                                 "domesday_rows": len(D)},
            "not_original_supported_outside_EO_1_7403": len([i for i in tier_not if i not in in_scope_ids]),
        },
    }
    out_of_scope = collections.Counter()
    for i in tier_not:
        if i in in_scope_ids:
            continue
        number, suffix, date = base_record(i)[4], base_record(i)[5], base_record(i)[6]
        if number.isdigit() and int(number) > 7403:
            out_of_scope["numbered_above_7403" + ("_dated_1936_or_earlier" if date and date[:4] <= "1936" else "_after_1936")] += 1
        elif not number:
            out_of_scope["unnumbered_outside_dates"] += 1
        else:
            out_of_scope["other"] += 1
    summary["reconciliation_current_definitions"]["not_original_supported_excluded_by_reason"] = dict(out_of_scope)
    with open(os.path.join(out_dir, "SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1, ensure_ascii=False)
    print(json.dumps({k: summary[k] for k in ("rows", "tracked_unique_orders", "by_group")}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:3])

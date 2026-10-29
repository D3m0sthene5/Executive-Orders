"""Current dashboard from committed research records and published job outputs.

This renderer never runs a research gate or assigns readiness. Claim hashes use
the same canonical JSON encoding as research/stage19/code/claim_gate.claim_sha.
Missing inputs remain unknown; old checker receipts cannot count new filings.
"""
from __future__ import annotations

import collections
import csv
import datetime as dt
import hashlib
import io
import json
import os
import subprocess
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

LEGAL_CUTOFF = "2026-10-14"
PATHS = {
    "universe": "research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv",
    "statuses": "research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv",
    "tracker": "jobs/readiness-tracker/output/SUMMARY.json",
    "tracker_status": "jobs/readiness-tracker/output/STATUS.json",
    "checker": "jobs/claim-checker/output/SUMMARY.json",
    "checker_receipts": "jobs/claim-checker/output/PER_CLAIM.json",
    "checker_status": "jobs/claim-checker/output/STATUS.json",
    "human_review": "research/stage19/output/PROGRESS.json",
    "pinakes": "jobs/pinakes-proquest-ingest/output/SUMMARY.json",
    "pinakes_status": "jobs/pinakes-proquest-ingest/output/STATUS.json",
    "cotton": "jobs/cotton-capture-custody/output/SUMMARY.json",
    "cotton_status": "jobs/cotton-capture-custody/output/STATUS.json",
}


def claim_sha(claim):
    return hashlib.sha256(json.dumps(claim, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def read_inputs(root):
    data, versions, problems = {}, {}, []
    for name, relative in PATHS.items():
        path = root / relative
        try:
            raw = path.read_bytes()
            versions[name] = {"path": relative, "sha256": hashlib.sha256(raw).hexdigest(),
                              "bytes": len(raw)}
            if path.suffix == ".csv":
                data[name] = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
            else:
                value = json.loads(raw)
                if not isinstance(value, dict):
                    raise ValueError("expected a JSON object")
                data[name] = value
        except (OSError, ValueError, UnicodeError, csv.Error) as exc:
            data[name] = None
            problems.append(f"{relative}: {type(exc).__name__}")
    return data, versions, problems


def claims_inventory(root):
    directory = root / "research/readiness/claims"
    paths = sorted(directory.glob("*.jsonl"), key=lambda p: (p.name, str(p)))
    records, effective, files, problems = [], {}, {}, []
    if not directory.is_dir():
        problems.append("research/readiness/claims: unavailable")
    nonblank = 0
    for path in paths:
        relative = path.relative_to(root).as_posix()
        raw = path.read_bytes()
        files[relative] = hashlib.sha256(raw).hexdigest()
        for number, line in enumerate(raw.split(b"\n"), 1):
            if not line.strip():
                continue
            nonblank += 1
            key = f"{relative}:{number}"
            try:
                obj = json.loads(line.decode("utf-8-sig" if number == 1 else "utf-8"))
                if not isinstance(obj, dict):
                    raise ValueError("expected claim object")
                iid = obj.get("instrument_id")
                if not isinstance(iid, str) or not iid.startswith("EO:"):
                    raise ValueError("missing executive-order identity")
                record = {"claim_key": key, "instrument_id": iid, "claim_sha256": claim_sha(obj)}
                records.append(record)
                # This is the checker/tracker's filename-then-line selection order.
                effective[iid] = record
            except (ValueError, UnicodeError, RecursionError):
                problems.append(key)
    available = directory.is_dir()
    return {"available": available, "files": files, "nonblank_lines": nonblank if available else None,
            "valid_claim_lines": len(records) if available else None, "unique_orders": len(effective) if available else None,
            "superseded_or_repeated_lines": len(records) - len(effective) if available else None,
            "parse_problems": problems, "records": records, "effective": effective}


def receipt_coverage(inventory, receipts, checker):
    current_files = {Path(p).name for p in inventory["files"]}
    checked_files = set((checker or {}).get("claim_files", []))
    result = {"current_claim_files_absent_from_checker_summary": sorted(current_files - checked_files),
              "checker_summary_files_no_longer_present": sorted(checked_files - current_files),
              "exact_current_claim_lines": None, "unmatched_current_claim_lines": None,
              "effective_orders_with_matching_receipt": None, "unmatched_effective_orders": None,
              "state": "unknown", "unmatched_claim_keys": []}
    if not inventory["available"] or not isinstance(receipts, dict):
        return result
    rows = receipts.get("claims")
    if not isinstance(rows, list):
        return result
    indexed = {r.get("claim_key"): r for r in rows if isinstance(r, dict)}
    missing = [r["claim_key"] for r in inventory["records"]
               if indexed.get(r["claim_key"], {}).get("claim_sha256") != r["claim_sha256"]]
    by_order = receipts.get("by_instrument", {})
    if not isinstance(by_order, dict):
        by_order = {}
    unmatched_orders = sorted(iid for iid, r in inventory["effective"].items()
                              if by_order.get(iid, {}).get("claim_sha256") != r["claim_sha256"])
    result.update({"exact_current_claim_lines": inventory["valid_claim_lines"] - len(missing),
                   "unmatched_current_claim_lines": len(missing),
                   "effective_orders_with_matching_receipt": inventory["unique_orders"] - len(unmatched_orders),
                   "unmatched_effective_orders": len(unmatched_orders),
                   "unmatched_claim_keys": missing, "unmatched_order_ids": unmatched_orders,
                   "state": "stale" if (missing or unmatched_orders or inventory["parse_problems"]
                       or current_files != checked_files) else "claim_versions_match"})
    return result


def status_inventory(rows, universe_rows):
    if rows is None:
        return {"rows": None, "unique_orders": None, "yes": None, "no": None,
                "without_provisional_status": None, "problems": ["Status register unavailable"]}
    universe = {r.get("id") for r in universe_rows or [] if r.get("id")}
    by_order, problems, duplicate_ids = {}, [], set()
    for row in rows:
        iid, status = row.get("instrument_id"), row.get("provisional_substantive_status")
        if not iid or status not in ("yes", "no"):
            problems.append(f"Invalid provisional status row: {iid}")
            continue
        if universe_rows is not None and iid not in universe:
            problems.append(f"Status identity outside working universe: {iid}")
            continue
        if iid in by_order:
            duplicate_ids.add(iid)
            if by_order[iid] != status:
                problems.append(f"Conflicting provisional statuses: {iid}")
                by_order[iid] = "conflict"
        else:
            by_order[iid] = status
    counts = collections.Counter(by_order.values())
    recognized = counts["yes"] + counts["no"]
    return {"rows": len(rows), "unique_orders": recognized, "yes": counts["yes"], "no": counts["no"],
            "duplicate_order_ids": sorted(duplicate_ids), "problems": problems,
            "without_provisional_status": len(universe) - recognized if universe_rows is not None else None,
            "human_certified_flags_in_status_register": sum(
                str(r.get("human_certified_by_this_release", "")).lower() in ("yes", "true", "1") for r in rows)}


def input_commit(root):
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except OSError:
        pass
    return os.environ.get("GITHUB_SHA") or None


def build(root, generated_utc=None):
    root = Path(root).resolve()
    data, versions, problems = read_inputs(root)
    inventory = claims_inventory(root)
    coverage = receipt_coverage(inventory, data["checker_receipts"], data["checker"])
    statuses = status_inventory(data["statuses"], data["universe"])
    tracker, checker = data["tracker"] or {}, data["checker"] or {}
    universe = (len({r["id"] for r in data["universe"] if r.get("id")})
                if data["universe"] is not None else None)
    discrepancies = list(statuses["problems"]) + list(inventory["parse_problems"])
    if universe is not None and tracker.get("orders_total") != universe:
        discrepancies.append("Tracker working-universe count differs from the current identity register")
    if statuses["unique_orders"] is not None and tracker.get("orders_with_provisional_status") != statuses["unique_orders"]:
        discrepancies.append("Tracker provisional-status count differs from the current status register")
    # Matching claim hashes are necessary but cannot certify all tracker inputs.
    # A newer generator may supply exact input freshness separately; until then,
    # retain the published generation and never call it fully current.
    freshness = {"state": "stale" if coverage["state"] == "stale" or discrepancies else "generation_reported",
                 "claim_receipts": coverage,
                 "tracker_generation": data["tracker_status"],
                 "checker_generation": data["checker_status"],
                 "discrepancies": discrepancies,
                 "interpretation": "Claim-version matching does not establish freshness of every source, policy, or tracker input."}
    pinakes, cotton = data["pinakes"] or {}, data["cotton"] or {}
    progress = data["human_review"] or {}
    report = {
        "schema": "eo-current-dashboard/v1",
        "generated_utc": generated_utc or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "legal_cutoff": LEGAL_CUTOFF, "repository_input_commit": input_commit(root),
        "working_identities": universe, "provisional_status": statuses,
        "readiness": {"published_ready_for_human_review": tracker.get("ready_for_human_review"),
                      "by_tier": tracker.get("ready_by_tier", {}),
                      "by_text_evidence_tier": tracker.get("ready_by_text_evidence_tier", {}),
                      "original_replacement_obligations": tracker.get("original_replacement_obligations"),
                      "quotation_recheck_obligations": tracker.get("quotation_recheck_obligations"),
                      "step_done_among_decided": tracker.get("step_done_among_decided", {}),
                      "decided_orders_blocked_by": tracker.get("decided_orders_blocked_by", {}),
                      "input_problems": tracker.get("input_problems", [])},
        "filed_claims": {k: v for k, v in inventory.items() if k not in ("records", "effective")},
        "checker": {k: checker.get(k) for k in ("claims_checked", "orders_with_claim", "claims_gate_passed",
                    "claims_all_checks_passed", "claims_mechanical_fail", "claims_mechanical_unverified")},
        "freshness": freshness,
        "human_review": {"published_whole_lifecycle_certifications": progress.get("independently_reviewed_whole_lifecycle_complete"),
                         "source": PATHS["human_review"],
                         "interpretation": "Last published human-review register. AI claims, checker passes and readiness never confer human certification."},
        "source_acquisition": {
            "pinakes": {"pdf_files": pinakes.get("files", {}).get("pdf_files"),
                        "orders_with_pdf": pinakes.get("orders", {}).get("with_pdf"),
                        "usable_texts": pinakes.get("texts", {}).get("usable"),
                        "low_quality_probably_handwritten": pinakes.get("texts", {}).get("low_quality_probably_handwritten"),
                        "supplied_links_missing": pinakes.get("supplied_links", {}).get("missing"),
                        "generated_utc": pinakes.get("generated_utc")},
            "cotton": {k: cotton.get(k) for k in ("published", "failed", "not_web_sources", "wanted_hashes")}},
        "sources": versions,
        "source_generations": {name: data[name + "_status"] for name in ("tracker", "checker", "pinakes", "cotton")},
        "unavailable_inputs": problems,
        "limits": ["The working bibliography is not the complete historical universe.",
                   "Filed claim lines include replacements and partial claims; they are not completed orders.",
                   "The dashboard displays published readiness; it does not assign or recompute it.",
                   "Historical effort estimates are not measured savings and are not recalibrated by this renderer."]}
    return report


def number(value):
    return f"{value:,}" if isinstance(value, int) and not isinstance(value, bool) else "unavailable"


def md_text(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def display_time(value):
    if not value:
        return "unavailable"
    try:
        timestamp = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            return value
        try:
            zone = ZoneInfo("America/New_York")
        except ZoneInfoNotFoundError:
            # Windows may have no IANA database. Keep an explicit accurate zone
            # instead of making an optional display conversion stop the report.
            zone = dt.timezone.utc
        return timestamp.astimezone(zone).strftime("%Y-%m-%d %H:%M %Z")
    except (TypeError, ValueError):
        return str(value)


def render_markdown(report):
    r, s, f = report["readiness"], report["provisional_status"], report["filed_claims"]
    freshness, human = report["freshness"], report["human_review"]
    cover = freshness["claim_receipts"]
    generation = freshness.get("tracker_generation") or {}
    tier = r["by_text_evidence_tier"]
    lines = ["# Executive Orders — current research dashboard", "",
             f"Generated {display_time(report['generated_utc'])}. Legal cutoff: **{report['legal_cutoff']}** (America/New_York).", ""]
    if freshness["state"] == "stale":
        lines += ["**Readiness generation is behind the current records.** The published ready count below is retained with its generation date. New or changed claims require matching checker receipts and a tracker refresh before they can advance readiness.", ""]
    else:
        lines += ["Readiness below is the latest published tracker generation. Exact claim-receipt coverage is reported separately; matching versions alone does not verify every source or policy input.", ""]
    lines += ["## Research progress", "", "| Measure | Count | Meaning |", "|---|---:|---|",
              f"| Working identities | {number(report['working_identities'])} | Bibliographic inventory; historical census remains incomplete |",
              f"| **Ready for human review, published** | **{number(r['published_ready_for_human_review'])}** | Every applicable tracker step passed or was documented exhausted; independent human verification is separate |",
              f"| Ready with original-supported text | {number(tier.get('original_supported'))} | Tracker's text-evidence tier |",
              f"| Ready dependent on provisional transcriptions | {number(tier.get('transcription_dependent'))} | Explicit working-text limitations remain |",
              f"| Provisional YES / NO | {number(s['yes'])} / {number(s['no'])} | Current status register, unique admitted identities |",
              f"| Without a provisional status | {number(s['without_provisional_status'])} | Working identities without a recognized YES/NO |",
              f"| Filed claim lines / distinct orders | {number(f['valid_claim_lines'])} / {number(f['unique_orders'])} | Includes partial claims and replacement versions; not a completion measure |",
              f"| Superseded or repeated claim lines | {number(f['superseded_or_repeated_lines'])} | Difference between valid lines and unique orders |",
              f"| Human-certified whole histories, published register | {number(human['published_whole_lifecycle_certifications'])} | Separate Stage19 human-review record; never inferred from AI passes |", "",
              f"Tracker generation: **{display_time(generation.get('finished_utc'))}**; input commit `{generation.get('commit_run', 'unavailable')}`."]
    if generation.get("run_url"):
        lines.append(f"[Tracker workflow]({generation['run_url']}).")
    lines += ["", "## Receipt coverage and freshness", "",
              "| Measure | Count |", "|---|---:|",
              f"| Current claim lines with an exact checker receipt | {number(cover['exact_current_claim_lines'])} / {number(f['valid_claim_lines'])} |",
              f"| Current claim lines without a matching receipt | {number(cover['unmatched_current_claim_lines'])} |",
              f"| Latest claim per order with a matching checker receipt | {number(cover['effective_orders_with_matching_receipt'])} / {number(f['unique_orders'])} |",
              f"| Distinct orders whose latest claim lacks a matching receipt | {number(cover['unmatched_effective_orders'])} |",
              f"| Original-replacement / quotation-recheck obligations | {number(r['original_replacement_obligations'])} / {number(r['quotation_recheck_obligations'])} |", "",
              "Receipt matching checks canonical claim content hashes. A matching receipt may record a failure; coverage is not an approval count. Readiness always comes from the tracker."]
    missing = cover["current_claim_files_absent_from_checker_summary"]
    if missing:
        lines += ["", "Files not represented in the published checker summary:", ""]
        lines += [f"- `{md_text(name)}`" for name in missing]
    if freshness["discrepancies"]:
        lines += ["", "Input differences requiring a refresh or correction:", ""]
        lines += [f"- {md_text(item)}" for item in freshness["discrepancies"][:12]]
    steps = r["step_done_among_decided"]
    labels = {"original_text": "Original or approved working text", "clause_inventory": "Operative clause inventory",
              "ending_or_current_basis": "Ending or current legal basis", "savings_residuals": "Surviving effects",
              "counterevidence": "Counterevidence review", "shared_sources": "Shared cited sources", "opus_media": "Opus evidence images"}
    lines += ["", "## Published step completion among provisionally classified orders", "",
              "| Step | Done / applicable |", "|---|---:|"]
    for key, label in labels.items():
        if key in steps:
            lines.append(f"| {label} | {number(steps[key].get('done'))} / {number(steps[key].get('applicable'))} |")
    lines += ["", "Steps overlap across orders and are not equal amounts of work.", "", "## Source acquisition", "",
              "| Source measure | Count |", "|---|---:|"]
    pq, ct = report["source_acquisition"]["pinakes"], report["source_acquisition"]["cotton"]
    for label, value in [("ProQuest PDFs / matched orders", f"{number(pq['pdf_files'])} / {number(pq['orders_with_pdf'])}"),
                         ("ProQuest usable machine texts", number(pq["usable_texts"])),
                         ("Low-quality, probably handwritten texts", number(pq["low_quality_probably_handwritten"])),
                         ("Supplied ProQuest links still missing a PDF", number(pq["supplied_links_missing"])),
                         ("Cotton published web-source copies", number(ct["published"])),
                         ("Cotton failed captures", number(ct["failed"]))]:
        lines.append(f"| {label} | {value} |")
    lines += ["", "File acquisition and machine text do not establish legal conclusions or independently admit an order to the census.", "",
              "## Provenance and interpretation", "",
              f"Dashboard run input commit: `{report['repository_input_commit'] or 'unavailable'}`. The JSON records SHA-256 hashes of the exact files read, including outputs regenerated during the same run.", "",
              "| Input | Published generation | Source |", "|---|---|---|"]
    for name, label in [("tracker", "Readiness"), ("checker", "Claim checker"), ("pinakes", "ProQuest ingestion"), ("cotton", "Web-source custody")]:
        source = report["sources"].get(name, {})
        status = report["source_generations"].get(name) or {}
        if name == "pinakes":
            when = pq.get("generated_utc")
        else:
            when = status.get("finished_utc")
        path = source.get("path", PATHS[name])
        lines.append(f"| {label} | {display_time(when) if when else 'see source STATUS.json'} | [{path}](../../../{path}) |")
    lines += ["", f"[Canonical provisional statuses](../../../{PATHS['statuses']}) · "
              f"[Published human-review record](../../../{PATHS['human_review']}) · "
              "[Exact dashboard data and input hashes](DASHBOARD.json) · [Daily changes](DIGEST.md)", ""]
    lines += [f"- {item}" for item in report["limits"]]
    if report["unavailable_inputs"]:
        lines += ["", "**Unavailable inputs:** " + "; ".join(md_text(x) for x in report["unavailable_inputs"]) + "."]
    return "\n".join(lines) + "\n"


def write(root, output):
    report = build(root)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "DASHBOARD.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "DASHBOARD.md").write_text(render_markdown(report), encoding="utf-8")
    return report

#!/usr/bin/env python3
"""Deterministic census of effective claim source references and ProQuest PDF leads.

Selection follows claim-checker: paths sorted by (basename, full path), then the
last valid claim row for each instrument wins. The script does not alter claims,
receipts, source records, or legal statuses.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import pathlib
import re
import subprocess
import sys
import io
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[4]
CLAIMS_GLOB = "research/readiness/claims/*.jsonl"
OUT_DIR = pathlib.Path(__file__).resolve().parent
CHECKER_PATH = ROOT / "jobs/claim-checker/checker.py"
GATE_PATH = ROOT / "research/stage19/code/claim_gate.py"
RECEIPT_PATH = ROOT / "jobs/claim-checker/output/PER_CLAIM.json"
CHECKS_PATH = ROOT / "jobs/claim-checker/output/CLAIM_CHECKS.csv"
METADATA_PATHS = [
    "jobs/pinakes-proquest-ingest/output/FRAGMENTS.jsonl",
    "jobs/pinakes-proquest-ingest/output/INVENTORY.csv",
    "jobs/pinakes-proquest-ingest/output/ORDERS.csv",
    "research/stage21/original_sources/CASE_ORIGINAL_SOURCE_CUSTODY.csv",
]
PROQUEST_PDF_SEARCH_DIRS = [
    "research/pre-1937-sources/ProQuest Pre-1937 Orders",
    "ProQuest Pre-1937 Orders",
]
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
PDF_PATH_KEY = re.compile(r"(?:^|_)(?:file|local_path|pdf_path|filename|document_path)$", re.I)
REF_COLUMNS = ["instrument_id", "claim_file", "claim_line", "canonical_claim_sha256", "ref_path",
               "source_hash", "sha256", "local_file_sha256", "text_sha256", "url",
               "page_or_item", "source_id", "representation_type", "route", "local_path",
               "pdf_hint_fields", "pdf_hint_values", "proquest_hint_fields", "receipt_version_status",
               "receipt_mechanical_result", "receipt_all_checks_passed", "source_status_coverage", "source_statuses"]


def import_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def file_pin(path: pathlib.Path) -> dict:
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as fh:
        while chunk := fh.read(1 << 20):
            size += len(chunk)
            h.update(chunk)
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": size, "sha256": h.hexdigest()}


def json_lines(path: pathlib.Path):
    """Yield checker-compatible nonblank JSONL rows, including parse failures."""
    rel = path.relative_to(ROOT).as_posix()
    with path.open("rb") as fh:
        for n, raw in enumerate(fh, 1):
            try:
                line = raw.decode("utf-8-sig" if n == 1 else "utf-8")
            except UnicodeDecodeError as exc:
                if raw.strip():
                    yield (f"{rel}:{n}", rel, n, None, f"line is not valid UTF-8 ({exc.reason} at byte {exc.start})")
                continue
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    raise ValueError("line is not a JSON object")
                yield (f"{rel}:{n}", rel, n, obj, None)
            except (ValueError, RecursionError) as exc:
                yield (f"{rel}:{n}", rel, n, None, f"{type(exc).__name__}: {exc}"[:200])


def sha_fields(ref: dict) -> dict:
    # Keep the source-byte hashes used by claim-checker separate from text hashes.
    return {
        "sha256": ref.get("sha256") if isinstance(ref.get("sha256"), str) else None,
        "local_file_sha256": ref.get("local_file_sha256") if isinstance(ref.get("local_file_sha256"), str) else None,
        "text_sha256": ref.get("text_sha256") if isinstance(ref.get("text_sha256"), str) else None,
    }


def source_hash(ref: dict):
    # Same precedence as checker.check_source; URL never supplies a hash.
    raw = ref.get("sha256") or ref.get("local_file_sha256")
    if isinstance(raw, str) and HEX64.fullmatch(raw.strip()):
        return raw.strip().lower()
    return None


def leaf_pdf_hints(ref: dict):
    hints = []
    for key, value in ref.items():
        if not isinstance(value, (str, list)):
            continue
        vals = value if isinstance(value, list) else [value]
        for item in vals:
            if not isinstance(item, str):
                continue
            low = item.lower()
            if low.endswith(".pdf") or ".pdf?" in low or (PDF_PATH_KEY.search(key) and ".pdf" in low):
                hints.append({"field": key, "value": item, "kind": "pdf_path_or_name"})
    for key in ("mime_type", "media_type", "content_type", "format"):
        val = ref.get(key)
        if isinstance(val, str) and "pdf" in val.lower():
            hints.append({"field": key, "value": val, "kind": "pdf_media_type"})
    return hints


def proquest_hints(ref: dict):
    hints = []
    for key, value in ref.items():
        if isinstance(value, str) and ("proquest" in value.lower() or "pinakes-proquest" in value.lower()):
            hints.append({"field": key, "value": value, "kind": "proquest_text"})
    return hints


def pinakes_metadata(root: pathlib.Path):
    """Index current sparse Pinakes rows by exact instrument ID and recorded PDF SHA."""
    out = defaultdict(list)
    for rel in ("jobs/pinakes-proquest-ingest/output/ORDERS.csv",
                "jobs/pinakes-proquest-ingest/output/INVENTORY.csv"):
        path = root / rel
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                iid, sha = row.get("instrument_id"), row.get("sha256")
                if isinstance(iid, str) and isinstance(sha, str) and HEX64.fullmatch(sha):
                    out[(iid, sha.lower())].append({"metadata_path": rel,
                        "instrument_id": iid, "sha256": sha.lower(),
                        "file": row.get("file"), "folder": row.get("folder"),
                        "bytes": row.get("bytes"), "pages": row.get("pages"),
                        "text_path": row.get("text_path"), "text_sha256": row.get("text_sha256"),
                        "accession_url": row.get("accession_url")})
    return out


def git_blob(commit: str, relpath: str):
    """Read and stream-hash a pinned git blob without checking out or changing Git state."""
    proc = subprocess.Popen(["git", "-C", str(ROOT), "cat-file", "blob", f"{commit}:{relpath}"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    digest = hashlib.sha256()
    chunks = []
    size = 0
    assert proc.stdout is not None
    while chunk := proc.stdout.read(1 << 20):
        digest.update(chunk)
        size += len(chunk)
        chunks.append(chunk)
    stderr = proc.stderr.read() if proc.stderr else b""
    code = proc.wait()
    if code:
        raise SystemExit(f"git blob unavailable {commit}:{relpath}: {stderr.decode('utf-8', 'replace')[:300]}")
    pin = {"path": relpath, "bytes": size, "sha256": digest.hexdigest(),
           "source_git_commit": commit, "source_kind": "git_blob"}
    return b"".join(chunks), pin


def checker_receipt_summary(receipts: dict, check_rows: dict, effective_rows: list, gate, checker):
    versions = {}
    for key, rel, line, claim, _ in effective_rows:
        iid = claim["instrument_id"]
        sha = gate.claim_sha(claim)
        rec = receipts.get(iid)
        status = "missing" if not isinstance(rec, dict) else ("exact" if rec.get("claim_sha256") == sha else "stale")
        versions[iid] = (status, rec if isinstance(rec, dict) else None, key, rel, line, sha)
    exact_refs = status_rows = record_only_refs = 0
    per_ref = {}
    for key, rel, line, claim, _ in effective_rows:
        iid = claim["instrument_id"]
        status, rec, *_ = versions[iid]
        refs_for_claim = []
        if status == "exact":
            for path, field_key, value, _chain in checker.walk(claim):
                if field_key in checker.SOURCE_KEYS and isinstance(value, dict):
                    refs_for_claim.append((path, value))
                elif field_key in checker.SOURCE_LIST_KEYS and isinstance(value, list):
                    refs_for_claim.extend((f"{path}[{n}]", obj) for n, obj in enumerate(value) if isinstance(obj, dict))
            for ref_path, _ref in refs_for_claim:
                source_rows = check_rows.get((key, ref_path, "source_held"), [])
                exact_refs += 1
                status_pairs = [[r.get("result") or "", r.get("status") or ""] for r in source_rows]
                per_ref[(key, ref_path)] = status_pairs
                status_rows += bool(status_pairs)
                if any(pair[1] == "custody_record_only" for pair in status_pairs):
                    record_only_refs += 1
        else:
            # Preserve claim refs in denominator only when receipt is exact, matching source status availability.
            continue
    ids = sorted({iid for iid, (status, rec, *_rest) in versions.items() if status == "exact" and
                  any(s[1] == "custody_record_only" for (key, _path), pairs in per_ref.items()
                      if key == versions[iid][2] for s in pairs)})
    return {"effective_claims": len(versions), "exact": sum(v[0] == "exact" for v in versions.values()),
            "stale": sum(v[0] == "stale" for v in versions.values()),
            "missing": sum(v[0] == "missing" for v in versions.values()),
            "effective_refs_with_exact_receipt": exact_refs,
            "exact_receipt_refs_with_source_status_row": status_rows,
            "exact_receipt_refs_without_source_status_row": exact_refs - status_rows,
            "exact_custody_record_only_refs": record_only_refs,
            "exact_custody_record_only_instruments": ids}, versions, per_ref


def parse_check_csv(raw: bytes):
    rows = defaultdict(list)
    with io.StringIO(raw.decode("utf-8-sig"), newline="") as fh:
        for row in csv.DictReader(fh):
            rows[(row.get("claim_key", ""), row.get("field", ""), row.get("check", ""))].append(row)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default=str(OUT_DIR))
    ap.add_argument("--receipts-ref", help="Git ref/commit containing fresh PER_CLAIM.json and CLAIM_CHECKS.csv")
    args = ap.parse_args()
    out = pathlib.Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    checker = import_module("claim_census_checker", CHECKER_PATH)
    gate = import_module("claim_census_claim_gate", GATE_PATH)
    claim_paths = sorted(ROOT.glob(CLAIMS_GLOB), key=lambda p: (p.name, p.as_posix()))
    pins = [file_pin(p) for p in claim_paths]
    baseline_receipt_bytes = RECEIPT_PATH.read_bytes()
    baseline_checks_bytes = CHECKS_PATH.read_bytes()
    baseline_pins = [file_pin(p) for p in (RECEIPT_PATH, CHECKS_PATH)]
    pins += baseline_pins
    pins += [file_pin(p) for p in [CHECKER_PATH, GATE_PATH] + [ROOT / p for p in METADATA_PATHS] if p.exists()]
    missing_metadata = [p for p in METADATA_PATHS if not (ROOT / p).exists()]
    if args.receipts_ref:
        selected_commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", args.receipts_ref], text=True).strip()
        selected_receipt_bytes, selected_receipt_pin = git_blob(selected_commit, "jobs/claim-checker/output/PER_CLAIM.json")
        selected_checks_bytes, selected_checks_pin = git_blob(selected_commit, "jobs/claim-checker/output/CLAIM_CHECKS.csv")
        pins.extend([selected_receipt_pin, selected_checks_pin])
        receipt_source = {"kind": "pinned_git_ref", "requested_ref": args.receipts_ref, "resolved_commit": selected_commit}
    else:
        selected_commit = None
        selected_receipt_bytes, selected_checks_bytes = baseline_receipt_bytes, baseline_checks_bytes
        receipt_source = {"kind": "current_checkout", "path": "jobs/claim-checker/output"}

    # Audit the streaming decoder and selection order against the checker reader.
    streamed = [row for path in claim_paths for row in json_lines(path)]
    checker_rows = checker.read_claims([str(p) for p in claim_paths], ROOT)
    signature = lambda rows: [(k, f, n, c, e) for k, f, n, c, e in rows]
    if signature(streamed) != signature(checker_rows):
        raise SystemExit("streaming JSONL reader differs from checker.read_claims")

    last = {}
    valid_rows = []
    for row in streamed:
        key, rel, line, claim, error = row
        if claim is not None:
            valid_rows.append(row)
            iid = claim.get("instrument_id")
            if isinstance(iid, str):
                last[iid] = key
    effective = [r for r in valid_rows if last.get(r[3].get("instrument_id")) == r[0]]
    by_id = {r[3]["instrument_id"]: (r[3], gate.claim_sha(r[3])) for r in effective}

    baseline_receipt_doc = json.loads(baseline_receipt_bytes)
    baseline_receipts = baseline_receipt_doc.get("by_instrument", {})
    baseline_check_rows = parse_check_csv(baseline_checks_bytes)
    baseline_receipt_summary, _, _ = checker_receipt_summary(baseline_receipts, baseline_check_rows, effective, gate, checker)

    receipt_doc = json.loads(selected_receipt_bytes)
    receipts = receipt_doc.get("by_instrument", {})
    receipt_versions = {}
    for iid, (claim, sha) in by_id.items():
        rec = receipts.get(iid)
        if not isinstance(rec, dict):
            receipt_versions[iid] = ("missing", None)
        elif rec.get("claim_sha256") == sha:
            receipt_versions[iid] = ("exact", rec)
        else:
            receipt_versions[iid] = ("stale", rec)

    check_rows = parse_check_csv(selected_checks_bytes)
    selected_receipt_summary, _, selected_per_ref_statuses = checker_receipt_summary(receipts, check_rows, effective, gate, checker)
    pinakes_rows = pinakes_metadata(ROOT)

    refs = []
    artifacts = defaultdict(list)
    ref_counts_all = Counter()
    ref_counts_effective = Counter()
    total_pdf_hints = total_proquest_hints = 0
    for key, rel, line, claim, _ in valid_rows:
        iid = claim.get("instrument_id")
        is_effective = isinstance(iid, str) and last.get(iid) == key
        canonical_sha = gate.claim_sha(claim)
        for path, field_key, value, _chain in checker.walk(claim):
            found = []
            if field_key in checker.SOURCE_KEYS and isinstance(value, dict):
                found = [(path, value)]
            elif field_key in checker.SOURCE_LIST_KEYS and isinstance(value, list):
                found = [(f"{path}[{n}]", obj) for n, obj in enumerate(value) if isinstance(obj, dict)]
            for ref_path, ref in found:
                ref_counts_all["refs"] += 1
                if not is_effective:
                    continue
                ref_counts_effective["refs"] += 1
                pdf = leaf_pdf_hints(ref)
                pq = proquest_hints(ref)
                total_pdf_hints += bool(pdf)
                total_proquest_hints += bool(pq)
                artifact_sha = source_hash(ref)
                pinakes_matches = pinakes_rows.get((iid, artifact_sha), []) if artifact_sha else []
                for match in pinakes_matches:
                    candidate_paths = [f"{directory}/{match['file']}" for directory in PROQUEST_PDF_SEARCH_DIRS]
                    match["local_candidate_paths_checked"] = candidate_paths
                    match["pdf_bytes_present_at_candidate_path"] = any((ROOT / p).is_file() for p in candidate_paths)
                receipt_status, receipt = receipt_versions.get(iid, ("missing", None))
                statuses = selected_per_ref_statuses.get((key, ref_path), []) if receipt_status == "exact" else []
                record = {
                    "instrument_id": iid,
                    "claim_file": rel,
                    "claim_line": line,
                    "claim_key": key,
                    "canonical_claim_sha256": canonical_sha,
                    "ref_path": ref_path,
                    "source_hash": artifact_sha,
                    "hash_fields": sha_fields(ref),
                    "url": ref.get("url") if isinstance(ref.get("url"), str) else None,
                    "page_or_item": ref.get("page_or_item") if isinstance(ref.get("page_or_item"), str) else None,
                    "source_id": ref.get("source_id") if isinstance(ref.get("source_id"), str) else None,
                    "representation_type": ref.get("representation_type") if isinstance(ref.get("representation_type"), str) else None,
                    "route": ref.get("route") if isinstance(ref.get("route"), str) else None,
                    "local_path": ref.get("local_path") if isinstance(ref.get("local_path"), str) else None,
                    "pinakes_metadata_matches": pinakes_matches,
                    "pdf_hints": pdf,
                    "proquest_hints": pq,
                    "receipt_claim_sha256": receipt.get("claim_sha256") if receipt else None,
                    "receipt_exact_for_claim": receipt_status == "exact",
                    "receipt_version_status": receipt_status,
                    "receipt_mechanical_result": receipt.get("mechanical_result") if receipt else None,
                    "receipt_all_checks_passed": str(receipt.get("all_checks_passed")).lower() if receipt and "all_checks_passed" in receipt else "",
                    "source_status_coverage": "exact_ref_row_present" if statuses else ("no_row_in_nonpass_csv" if receipt_status == "exact" else "no_exact_claim_receipt"),
                    "source_statuses": statuses,
                    "pdf_hint_fields": sorted({h["field"] for h in pdf}),
                    "pdf_hint_values": json.dumps([[h["field"], h["value"]] for h in pdf
                        if h["field"] not in ("url", "local_path")], ensure_ascii=False, separators=(",", ":")),
                    "proquest_hint_fields": sorted({h["field"] for h in pq}),
                }
                if artifact_sha:
                    artifacts[artifact_sha].append(len(refs))
                refs.append(record)

    # Receipt must agree with current effective claim set, claim by claim.
    exact_receipt_count = sum(status == "exact" for status, _ in receipt_versions.values())
    counts = {
        "claim_files": len(claim_paths),
        "raw_rows_nonblank_including_parse_errors": len(streamed),
        "valid_claim_rows": len(valid_rows),
        "parse_error_rows": len(streamed) - len(valid_rows),
        "unique_effective_instruments": len(last),
        "effective_claim_rows": len(effective),
        "superseded_valid_rows": len(valid_rows) - len(effective),
        "source_refs_all_valid_claim_rows": ref_counts_all["refs"],
        "source_refs_effective_claims": ref_counts_effective["refs"],
        "effective_refs_with_exact_checker_receipt": sum(r["receipt_exact_for_claim"] for r in refs),
        "exact_receipt_refs_with_source_status_row": sum(bool(r["source_statuses"]) for r in refs if r["receipt_exact_for_claim"]),
        "exact_receipt_refs_without_source_status_row": sum(not r["source_statuses"] for r in refs if r["receipt_exact_for_claim"]),
        "effective_claims_with_exact_checker_receipt": exact_receipt_count,
        "effective_claims_with_stale_checker_receipt": sum(status == "stale" for status, _ in receipt_versions.values()),
        "effective_claims_with_missing_checker_receipt": sum(status == "missing" for status, _ in receipt_versions.values()),
        "distinct_explicit_source_sha256": len(artifacts),
        "effective_pdf_hint_refs": total_pdf_hints,
        "effective_proquest_hint_refs": total_proquest_hints,
        "effective_instruments_with_pdf_hint": len({r["instrument_id"] for r in refs if r["pdf_hints"]}),
        "effective_instruments_with_proquest_hint": len({r["instrument_id"] for r in refs if r["proquest_hints"]}),
        "effective_refs_with_pinakes_metadata_match": sum(bool(r["pinakes_metadata_matches"]) for r in refs),
        "effective_instruments_with_pinakes_metadata_match": len({r["instrument_id"] for r in refs if r["pinakes_metadata_matches"]}),
        "exact_receipt_claims_with_custody_record_only": len({r["instrument_id"] for r in refs if r["receipt_exact_for_claim"] and any(s[1] == "custody_record_only" for s in r["source_statuses"])}),
        "exact_receipt_claims_with_proquest_custody_record_only": len({r["instrument_id"] for r in refs if r["receipt_exact_for_claim"] and r["proquest_hints"] and any(s[1] == "custody_record_only" for s in r["source_statuses"])}),
        "exact_receipt_source_refs_custody_record_only": sum(1 for r in refs if r["receipt_exact_for_claim"] and any(s[1] == "custody_record_only" for s in r["source_statuses"])),
        "exact_receipt_proquest_source_refs_custody_record_only": sum(1 for r in refs if r["receipt_exact_for_claim"] and r["proquest_hints"] and any(s[1] == "custody_record_only" for s in r["source_statuses"])),
    }
    repository_revision = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    candidate_ids = sorted({r["instrument_id"] for r in refs
        if r["receipt_exact_for_claim"] and any(s[1] == "custody_record_only" for s in r["source_statuses"])})
    custody_candidates = []
    for iid in candidate_ids:
        group = [(n, r) for n, r in enumerate(refs) if r["instrument_id"] == iid and r["receipt_exact_for_claim"]
                 and any(s[1] == "custody_record_only" for s in r["source_statuses"])]
        first = group[0][1]
        matched_meta = []
        for _, ref in group:
            for meta in ref["pinakes_metadata_matches"]:
                if meta not in matched_meta:
                    matched_meta.append(meta)
        custody_candidates.append({"instrument_id": iid, "claim_file": first["claim_file"],
            "claim_line": first["claim_line"], "claim_sha256": first["canonical_claim_sha256"],
            "receipt_version_status": first["receipt_version_status"],
            "reference_indexes": [n for n, _ in group],
            "source_hashes": sorted({r["source_hash"] for _, r in group if r["source_hash"]}),
            "proquest_metadata_matches": matched_meta,
            "local_pdf_bytes_present_at_checked_paths": any(m["pdf_bytes_present_at_candidate_path"] for m in matched_meta)})

    pinakes_population = []
    for iid in sorted({r["instrument_id"] for r in refs if r["pinakes_metadata_matches"]}):
        group = [(n, r) for n, r in enumerate(refs) if r["instrument_id"] == iid and r["pinakes_metadata_matches"]]
        matched_meta = []
        for _, ref in group:
            for meta in ref["pinakes_metadata_matches"]:
                if meta not in matched_meta:
                    matched_meta.append(meta)
        pinakes_population.append({"instrument_id": iid, "reference_indexes": [n for n, _ in group],
                                   "metadata_matches": matched_meta,
                                   "current_custody_record_only": iid in candidate_ids})

    # Intern repeated strings so every exact reference is preserved once without
    # repeating long paths, URLs, IDs, statuses, and hashes in the JSON file.
    text_values = set()
    raw_rows = []
    for ref in refs:
        row = []
        for col in REF_COLUMNS:
            value = ref.get(col)
            if col == "claim_line":
                row.append(value)
            elif col in ("pdf_hint_fields", "proquest_hint_fields", "pdf_hint_values"):
                value = ";".join(value or [])
                text_values.add(value)
                row.append(value)
            elif col == "source_statuses":
                value = ";".join(f"{x[0]}:{x[1]}" for x in (value or []))
                text_values.add(value)
                row.append(value)
            else:
                value = value if isinstance(value, str) else ""
                text_values.add(value)
                row.append(value)
        raw_rows.append(row)
    string_table = sorted(text_values)
    string_ix = {s: n for n, s in enumerate(string_table)}
    compact_refs = [[v if isinstance(v, int) else string_ix[v] for v in row] for row in raw_rows]

    common = {
        "schema": "proquest-effective-claim-census/v1",
        "repository_revision": repository_revision,
        "baseline_revision": "f9c6d806ad059dcad7875ab3708715f20ea386df",
        "selection": "claim-checker sorted by (basename, full path); last valid JSON object row per instrument_id wins",
        "equivalence": {"streaming_reader_matches_checker_read_claims": True,
                        "checker_read_claims_rows": len(checker_rows),
                        "streaming_rows": len(streamed)},
        "input_pins": sorted(pins, key=lambda p: p["path"]),
        "receipt_policy": "Per-instrument receipt is exact only when PER_CLAIM.by_instrument claim_sha256 equals claim_gate.claim_sha(current effective claim). Per-source statuses come from CLAIM_CHECKS.csv rows for that exact effective claim_key and ref_path. This checker CSV defaults to non-pass rows, so absent rows are marked no_row_in_nonpass_csv and no per-reference pass is inferred from a claim-level pass.",
        "receipt_source": receipt_source,
        "receipt_generations": {"main_baseline_checkout": baseline_receipt_summary,
                                "selected": selected_receipt_summary},
        "hash_policy": "URL values are never converted to hashes. Distinct artifact grouping uses only explicit sha256 or local_file_sha256 values matching 64 hex characters; text_sha256 is preserved separately.",
        "metadata_completeness": {"inspected_current_checkout_paths": METADATA_PATHS,
                                  "missing_metadata_paths": missing_metadata,
                                  "local_pdf_candidate_search_directories": PROQUEST_PDF_SEARCH_DIRS,
                                  "scope_note": "Only listed current checkout metadata paths were inspected. A hint does not establish retained PDF bytes or readiness; custody_record_only is reported only from an exact current checker receipt."},
        "counts": counts,
    }
    references_doc = {"schema": common["schema"], "repository_revision": repository_revision,
        "baseline_revision": common["baseline_revision"], "selection": common["selection"],
        "equivalence": common["equivalence"], "columns": REF_COLUMNS,
        "string_table": string_table, "references": compact_refs}
    census_doc = {**common, "reference_file": "EFFECTIVE_REFERENCES.json",
        "reference_encoding": "Each references row is an array aligned to EFFECTIVE_REFERENCES.columns; string-valued cells index the shared string_table. claim_line remains numeric."
        , "artifact_reference_indexes": [[sha, indexes] for sha, indexes in sorted(artifacts.items())],
        "pinakes_metadata_population": pinakes_population,
        "custody_candidates": custody_candidates}
    (out / "EFFECTIVE_REFERENCES.json").write_text(json.dumps(references_doc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (out / "CLAIM_CENSUS.json").write_text(json.dumps(census_doc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(counts, sort_keys=True))


if __name__ == "__main__":
    main()

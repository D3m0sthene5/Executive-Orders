"""Offline evidence-presence census. Reads existing records; writes only CSV/summary.

Use --input-root for a checkout containing the claim-kit overlay/status-history
outputs. No acquisition, classification, readiness change, or legal judgment.
"""
import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess


FIELDS = {
    "held_order_text": "Nonempty attributed order text file, including derivative representations.",
    "original_candidate_text": "Held text whose existing acceptable_as_original flag is true; no authentication inferred.",
    "publication_reference": "Recorded catalog citation/publication URL or attributed text page/item locator.",
    "status_history": "Nonempty saved status-history file referenced by claim-kit.",
    "later_event_record": "At least one known acting-order ID in claim-kit's overlay input.",
    "acting_provision_text": "Nonempty acting-provision text recorded for this target, including machine leads.",
    "clause_draft": "At least one nonempty clause text in the existing selected-text clause draft.",
    "own_terms_record": "At least one existing own-terms candidate record; no applicable term inferred.",
    "current_law_reference": "At least one current-law lead, including citation-only pointers.",
    "attributed_current_law_text": "Current-law lead includes text, source, and character offsets, rather than just a snippet.",
    "recorded_later_source_search": "Nonempty per-order search record in tracker or claim-kit overlay output.",
}
TRACKER = "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv"
KIT = "jobs/claim-kit/output/"
INPUTS = [TRACKER, KIT + "STATUS_LEADS.jsonl", KIT + "OVERLAY_INPUTS.jsonl",
          KIT + "TEXT_REPRESENTATIONS.jsonl", KIT + "ACTING_PROVISIONS.jsonl",
          KIT + "CLAUSES.jsonl", "jobs/later-events/output/CATALOG_INDEX.csv",
          "jobs/readiness-tracker/output/MACHINE_LATER_SEARCH.jsonl"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--expected-count", type=int, default=11613)
    args = parser.parse_args()
    root = args.input_root.resolve()
    pins, files = {}, {}

    def path(rel):
        result = (root / rel).resolve()
        if not result.is_relative_to(root):
            raise ValueError("Input path escapes checkout: " + rel)
        return result

    def records(rel):
        data = path(rel).read_bytes()  # Missing or unreadable inputs stop the run.
        pins[rel] = hashlib.sha256(data).hexdigest()
        if data.startswith(b"version https://git-lfs.github.com/spec/v1"):
            raise ValueError("Input is an LFS pointer, not records: " + rel)
        text = data.decode("utf-8-sig")
        return csv.DictReader(io.StringIO(text)) if rel.endswith(".csv") else (
            json.loads(line) for line in text.splitlines() if line.strip())

    def held(rel):
        if not rel:
            return False
        if rel not in files:
            p = path(rel)
            data = p.read_bytes() if p.is_file() else b""
            present = bool(data.decode("utf-8-sig").strip()) and not data.startswith(
                b"version https://git-lfs.github.com/spec/v1")
            files[rel] = (present, hashlib.sha256(data).hexdigest() if data else "absent")
        return files[rel][0]

    def indexed(rel):
        result = {}
        for item in records(rel):
            iid = item["instrument_id"]
            if iid in result:
                raise ValueError("Duplicate order in " + rel + ": " + iid)
            result[iid] = item
        return result

    tracker = indexed(TRACKER)
    if any(r["provisional_status"] not in ("", "yes", "no") for r in tracker.values()):
        raise ValueError("Unexpected provisional status; population is ambiguous")
    ids = sorted(iid for iid, r in tracker.items() if r["provisional_status"] == "")
    if len(ids) != args.expected_count:
        raise ValueError(f"Expected {args.expected_count} undecided orders; found {len(ids)}")
    present = {iid: {key: False for key in FIELDS} for iid in ids}
    leads = indexed(KIT + "STATUS_LEADS.jsonl")
    overlays = indexed(KIT + "OVERLAY_INPUTS.jsonl")
    if set(leads) != set(ids) or set(overlays) != set(ids):
        raise ValueError("Claim-kit records do not cover exactly the tracker undecided population")
    for iid in ids:
        row, lead, overlay = present[iid], leads[iid], overlays[iid]
        history = lead["status_history"]
        row["status_history"] = bool(history and held(history["history_path"]))
        row["later_event_record"] = bool(overlay["known_actor_ids"])
        row["own_terms_record"] = bool(lead["own_terms"])
        row["current_law_reference"] = bool(lead["current_law_leads"])
        row["attributed_current_law_text"] = any(
            x.get("text", "").strip() and x.get("source") and
            "char_start" in x and "char_end" in x for x in lead["current_law_leads"])
        row["recorded_later_source_search"] = bool(overlay["machine_searches"])
    for item in records(KIT + "TEXT_REPRESENTATIONS.jsonl"):
        if item["instrument_id"] not in present:
            continue
        row = present[item["instrument_id"]]
        text_present = held(item["text_path"])
        row["held_order_text"] |= text_present
        row["original_candidate_text"] |= text_present and item["acceptable_as_original"] is True
        row["publication_reference"] |= bool(item["source"].get("page_or_item", "").strip())
    for item in records("jobs/later-events/output/CATALOG_INDEX.csv"):
        if item["id"] in present:
            present[item["id"]]["publication_reference"] |= any(
                item[k].strip() for k in ("citation", "html_url", "pdf_url", "raw_text_url"))
    for rel, field, iid_key, value_key in [
        (KIT + "ACTING_PROVISIONS.jsonl", "acting_provision_text", "target_id", "provision_text"),
        (KIT + "CLAUSES.jsonl", "clause_draft", "instrument_id", "clauses"),
        ("jobs/readiness-tracker/output/MACHINE_LATER_SEARCH.jsonl",
         "recorded_later_source_search", "instrument_id", "later_source_search"),
    ]:
        for item in records(rel):
            if item[iid_key] in present:
                value = item[value_key]
                exists = any(c.get("text", "").strip() for c in value) if field == "clause_draft" else bool(value)
                present[item[iid_key]][field] |= exists
    if set(pins) != set(INPUTS):
        raise ValueError("Not all required inputs were inspected")
    for rel, expected in pins.items():
        if hashlib.sha256(path(rel).read_bytes()).hexdigest() != expected:
            raise ValueError("Input changed during census: " + rel)
    missing = {key: sum(not row[key] for row in present.values()) for key in FIELDS}
    combinations = collections.Counter(tuple(key for key in FIELDS if not row[key]) for row in present.values())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "census.csv"
    with output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["order_number", "instrument_id", *FIELDS])
        writer.writeheader()
        for iid in ids:
            writer.writerow({"order_number": iid[3:] if iid.startswith("EO:") else "",
                             "instrument_id": iid, **{k: "yes" if v else "no" for k, v in present[iid].items()}})
    with output.open(encoding="utf-8", newline="") as fh:
        saved = list(csv.DictReader(fh))
    if len(saved) != len(ids) or {r["instrument_id"] for r in saved} != set(ids):
        raise ValueError("CSV coverage check failed")
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    fingerprint = hashlib.sha256(json.dumps({"inputs": pins, "referenced_files": files}, sort_keys=True).encode()).hexdigest()
    summary = ["Evidence on file for undecided executive orders", "",
               f"Population: {len(ids):,} tracker entries with no provisional yes/no status. CSV has exactly {len(saved):,} rows, unique IDs, no omissions or extras.", "",
               "Evidence | Missing orders | Presence rule", "---------|---------------:|--------------"]
    summary += [f"{key} | {missing[key]:,} | {FIELDS[key]}" for key in sorted(FIELDS, key=lambda k: (-missing[k], k))]
    summary += ["", "Five most common exact combinations of missing pieces", "",
                "Missing pieces (all other columns are yes) | Orders", "----------------------------------------|------:"]
    summary += [f"{', '.join(keys) or '(none)'} | {count:,}" for keys, count in sorted(combinations.items(), key=lambda x: (-x[1], x[0]))[:5]]
    summary += ["", "Yes/no reports record or file presence only. No means absent from the inspected project records, not unavailable elsewhere or necessarily needed by that order. Machine leads, clause drafts, and original-candidate flags are retained without judging their accuracy or legal effect. Publication references and current-law pointers do not imply that source bytes are held. Text-file checks exclude empty files and Git LFS pointer stubs. Unnumbered orders retain their instrument IDs and have blank order_number.", "",
                f"Evidence checkout commit: {source_commit}", f"Inputs and referenced-file SHA-256 fingerprint: {fingerprint}",
                "Input paths and all presence rules are in check_evidence.py. Use the existing corpus-excavator evidence checkout, whose overlay/history outputs are not on the older census branch base.",
                "Rerun: python research/gap-census/check_evidence.py --input-root /path/to/evidence-checkout", ""]
    (args.output_dir / "summary.txt").write_text("\n".join(summary), encoding="utf-8")
    print(json.dumps({"rows": len(saved), "missing": missing, "top_combination": combinations.most_common(1),
                      "coverage_exact": True, "source_commit": source_commit}, indent=2))


if __name__ == "__main__":
    main()

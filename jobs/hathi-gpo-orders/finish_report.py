"""Offline target census and read-only claim-kit ingestion check."""
import collections
import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "output"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lines(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()] if path.exists() else []


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def csv_file(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def order_key(identity):
    return int(re.match(r"EO:(\d+)", identity)[1]), identity


def main():
    plan = json.loads((HERE / "data/TARGETS.json").read_text(encoding="utf-8"))
    targets = {r["instrument_id"]: r for r in plan["orders"]}
    assert len(targets) == len(plan["orders"]) == 1712
    assert digest(ROOT / plan["input"]) == plan["input_sha256"]
    prior = json.loads((OUT / "INGESTION_CHECK.json").read_text(encoding="utf-8"))
    for name, expected in prior["protected_inputs_sha256"].items():
        assert digest(ROOT / name) == expected, name
    state = json.loads((OUT / "STATUS.json").read_text(encoding="utf-8"))
    if state.get("state") == "stopped_access_check" and not (OUT / "HATHI_ACCESS_STOP.json").exists():
        write_json(OUT / "HATHI_ACCESS_STOP.json", state)
    source_rows = lines(OUT / "SOURCES.jsonl")
    sources = {r["instrument_ids"][0]: r for r in source_rows}
    assert len(sources) == len(source_rows) and set(sources) <= set(targets)
    fragments = lines(OUT / "FRAGMENTS.jsonl")
    assert len(fragments) == len(sources)
    assert {r["instrument_id"] for r in fragments} == set(sources)
    assert {p.relative_to(OUT).as_posix() for p in (OUT / "texts").glob("*.txt")} == {r["text_path"] for r in source_rows}
    artifact_hashes = {}
    for identity, r in sources.items():
        raw = (OUT / r["text_path"]).read_bytes()
        text = raw.decode("utf-8")
        assert b"\r\n" not in raw and len(text) > 100
        assert r["acceptable_as_original"] is False
        assert "not authenticated as an original" in text.splitlines()[0]
        assert r.get("url", "").startswith("https://") and r.get("page_or_item")
        assert re.fullmatch(r"[a-f0-9]{64}", r["sha256"])
        assert digest(OUT / r["text_path"]) == r["text_sha256"]
        body = text.split("----- EXACT SOURCE TEXT -----\n", 1)[1].strip()
        assert hashlib.sha256(body.encode("utf-8")).hexdigest() == r["exact_source_text_sha256"]
        assert "[PAGE OCR FAILED:" not in body
        if r.get("source_artifact"):
            p = OUT / r["source_artifact"]
            assert p.is_file(), p
            if p.suffix in (".djvu", ".pdf", ".html"):
                if p not in artifact_hashes:
                    artifact_hashes[p] = digest(p)
                assert artifact_hashes[p] == r["sha256"], p
        if r["route"] in ("wikisource_residual", "wikisource_scan_pages"):
            assert r.get("revision_id") and r.get("revision_url") and r.get("archival_id")
            for page in r.get("transcribed_pages", []):
                assert digest(OUT / page["source_artifact"]) == page["sha256"]
        elif r["route"] in ("ia_hoover", "commons_gpo_ocr", "govinfo_fr"):
            assert r.get("scan_image_start") or r.get("pdf_first_page"), identity
        if r["route"] == "govinfo_fr":
            assert digest(OUT / "books" / ("FR-" + r["publication_date"] + ".pdf")) == r["sha256"]
    for r in fragments:
        assert r["acceptable_as_original"] is r["data"]["acceptable_as_original"] is False
        assert r["data"]["text_sha256"] == sources[r["instrument_id"]]["text_sha256"]
    watched = set(prior["protected_inputs_sha256"]) | {
        "jobs/fr-originals/fr_originals.py", "jobs/source-ladder/fetch_ladder.py",
        "jobs/source-ladder/fr_pages.py", "jobs/_lib/fetch_pool.py", "jobs/wikisource-texts/harvest.py"}
    protected = {p: digest(ROOT / p) for p in sorted(watched)}
    for p, actual in protected.items():
        git_bytes = subprocess.check_output(["git", "show", "HEAD:" + p], cwd=ROOT)
        assert (ROOT / p).read_bytes().replace(b"\r\n", b"\n") == git_bytes.replace(b"\r\n", b"\n"), p
    kit_out = ROOT / "jobs/claim-kit/output"
    before = {p.relative_to(ROOT).as_posix(): digest(p) for p in kit_out.rglob("*") if p.is_file()} if kit_out.exists() else {}
    spec = importlib.util.spec_from_file_location("claim_kit_read_only", ROOT / "jobs/claim-kit/inputs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    corpus = module.load_corpus(ROOT)
    recognized = [r for r in corpus["texts"] if r["text_path"].startswith("jobs/hathi-gpo-orders/")]
    assert {r["instrument_id"] for r in recognized} == set(sources)
    assert len(recognized) == len(sources), "Duplicate loader representations"
    assert all(r["acceptable_as_original"] is False for r in recognized)
    assert not corpus["warnings"], corpus["warnings"]
    after = {p.relative_to(ROOT).as_posix(): digest(p) for p in kit_out.rglob("*") if p.is_file()} if kit_out.exists() else {}
    assert before == after and protected == {p: digest(ROOT / p) for p in watched}
    by_id = collections.defaultdict(list)
    for r in lines(OUT / "EXTRACTION_FAILURES.jsonl"):
        if r.get("instrument_id") in targets:
            by_id[r["instrument_id"]].append(r)
    missing = set(targets) - set(sources)
    rows, failures = [], []
    for identity in sorted(targets, key=order_key):
        s = sources.get(identity, {})
        reason = ""
        if identity in missing:
            reason = " | ".join(dict.fromkeys(r["reason"] for r in by_id[identity])) or "No complete passage with readable exact identity and boundaries recovered from checked sources"
            failures.append({"instrument_id": identity, "result": "text_not_saved", "reason": reason,
                             "qualification": "Acquisition result, not source-absence or legal-status finding"})
        rows.append({"instrument_id": identity, "order_number": targets[identity]["order_number"],
                     "text_saved": "yes" if s else "no", "route": s.get("route", ""),
                     "copy_kind": s.get("representation_type", ""), "source_url": s.get("url", ""),
                     "page_or_item": s.get("page_or_item", ""), "revision": s.get("revision_id", ""),
                     "text_path": "output/" + s["text_path"] if s else "", "failure_reasons": reason})
    csv_file(OUT / "RESULTS.csv", list(rows[0]), rows)
    csv_file(OUT / "MISSING.csv", list(rows[0]), [r for r in rows if r["text_saved"] == "no"])
    with (OUT / "FAILURES.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for r in failures:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    with (OUT / "RESULTS.csv").open(encoding="utf-8") as fh:
        assert len(list(csv.DictReader(fh))) == 1712
    assert len(missing) + len(sources) == 1712
    volumes, queue = [], []
    for p in sorted((OUT / "books").glob("Executive_Orders_*.djvu.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        low, high = map(int, re.search(r"(\d+)-(\d+)", rec["volume"]).groups())
        ids = [i for i in missing if low <= order_key(i)[0] <= high]
        volumes.append({"volume": rec["volume"], "range_min": low, "range_max": high,
                        "remaining_range_candidates": len(ids), "source_url": rec["url"],
                        "held_scan": "output/books/" + rec["volume"],
                        "qualification": "Range candidates, not verified individual texts"})
        with gzip.open(OUT / "books" / (rec["volume"] + "_ocr.jsonl.gz"), "rt", encoding="utf-8") as fh:
            pages = [json.loads(s) for s in fh]
        for identity in sorted(ids, key=order_key):
            number = identity[3:]
            pat = r"(?<!\d)" + re.escape(number[:-1]) + r"\s*[-]?\s*" + number[-1] + r"(?![\dA-Z])" if number[-1].isalpha() else r"(?<!\d)" + number + r"(?!\d|\s*[-]\s*[A-Z])"
            hits = [p["image"] for p in pages if re.search(pat, p["text"], re.I)]
            if hits:
                queue.append({"instrument_id": identity, "volume": rec["volume"], "candidate_scan_pages": ";".join(map(str, hits[:15])),
                              "source_url": rec["url"] + "?page=" + str(hits[0]),
                              "qualification": "Number occurrence only; may be a reference. Verify full heading and closing boundary on scan."})
    csv_file(OUT / "REMAINING_BY_VOLUME.csv", list(volumes[0]), volumes)
    csv_file(OUT / "PAGE_CHECK_QUEUE.csv", ["instrument_id", "volume", "candidate_scan_pages", "source_url", "qualification"], queue)
    summary = {"orders_targeted": 1712, "orders_with_text_saved": len(sources), "orders_still_missing_text": len(missing),
               "saved_by_route": dict(sorted(collections.Counter(r["route"] for r in source_rows).items())),
               "government_bound_volumes_used": len({r.get("volume") for r in source_rows if r["route"] in ("ia_hoover", "commons_gpo_ocr")}),
               "federal_register_issues_used": len({r["publication_date"] for r in source_rows if r["route"] == "govinfo_fr"}),
               "missing_hoover_5076_6070": sum(order_key(i)[0] <= 6070 for i in missing),
               "missing_fdr_6071_7531": sum(order_key(i)[0] >= 6071 for i in missing),
               "remaining_with_candidate_scan_page": len({r["instrument_id"] for r in queue}),
               "largest_remaining_volume": max(volumes, key=lambda r: r["remaining_range_candidates"]),
               "authenticated_originals": 0, "all_derivative_records_acceptable_as_original_false": True,
               "claim_kit_recognized": len(recognized),
               "qualification": "Text acquisition only. OCR copies need page checks; no status or original-authentication decisions."}
    write_json(OUT / "SUMMARY.json", summary)
    write_json(OUT / "STATUS.json", {"state": "completed_available_routes", **summary, "no_automatic_continuation": True,
                                    "remaining_actions": "research/orders-1929-1936/HUMAN_STEPS.md"})
    write_json(OUT / "INGESTION_CHECK.json", {"method": "unchanged jobs/claim-kit/inputs.py load_corpus, read-only",
               "recognized_new_order_texts": len(recognized), "expected_saved_order_texts": len(sources),
               "unique_source_and_fragment_identities": len(sources), "results_csv_rows": 1712,
               "all_recognized_acceptable_as_original_false": True, "text_hashes_valid": True,
               "claim_kit_output_before": before, "claim_kit_output_after": after,
               "protected_inputs_sha256": protected, "protected_inputs_unchanged": True,
               "git_comparison": "CRLF/LF normalized for Windows checkout; prior protected working-byte hashes also checked exactly",
               "base_main_commit": "224fd70cb6982f764d7f95f99102d1f1ab7d3fce", "warnings": corpus["warnings"]})
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

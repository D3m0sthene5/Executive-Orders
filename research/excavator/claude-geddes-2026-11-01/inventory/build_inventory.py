#!/usr/bin/env python3
"""Rebuild the Apollo genuine-rejection inventory from pinned review/completion records."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
APOLLO = ROOT / "research/excavator/claude-apollo-2026-10-31"
OUT = Path(__file__).resolve().parent
EXCLUDED = {"EO:6471A", "EO:7016"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def records(path: Path):
    raw = path.read_bytes()
    for line_no, line in enumerate(raw.splitlines(keepends=True), 1):
        if line.strip():
            yield line_no, line, json.loads(line)


def abs_path(rel: str) -> Path:
    return ROOT / rel


def category(path: Path) -> str:
    batch = path.as_posix().split("/claude-apollo-2026-10-31/", 1)[-1].split("/", 1)[0]
    return "NRA" if batch.startswith("n") else "general"


def main():
    reviews = {}
    controls = set()
    completions = []
    for cp in sorted(APOLLO.glob("*/packet/**/completion/COMPLETION.json")):
        c = json.loads(cp.read_text())
        completions.append((cp, c))
        for item in c.get("controls", []):
            controls.add((item.get("instrument_id"), item.get("planted_claim_sha256")))
        rp = cp.parent.parent / "reviews"
        for name in ("BLIND_REVIEW.jsonl", "AFTER_REVEAL.jsonl"):
            f = rp / name
            if not f.exists():
                continue
            for ln, line, r in records(f):
                reviews.setdefault((r.get("instrument_id"), r.get("claim_sha256"), name), []).append(
                    (f, ln, line, r)
                )

    member_map = {}
    for cp, c in completions:
        for m in c.get("members", []):
            member_map[(m.get("instrument_id"), m.get("claim_sha256"))] = (cp, m)

    # Rejected claims are absent from successful completion pointers. Locate their exact
    # bytes by the reviewer-record claim hash across all retained proposed claim files.
    claim_bytes = {}
    for f in sorted(APOLLO.glob("**/CLAIMS.proposed.jsonl")):
        blob = f.read_bytes()
        for ln, line in enumerate(blob.splitlines(keepends=True), 1):
            if not line.strip():
                continue
            rec_hash = sha(line.rstrip(b"\r\n"))
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            claim_bytes[(obj.get("instrument_id"), rec_hash)] = (f, ln, sha(blob))

    chosen = []
    # Blind genuine rejections exclude the planted version. The five rejected after-reveal
    # originals are added by their exact genuine claim hashes.
    for (eo, claim_hash, name), entries in reviews.items():
        if eo in EXCLUDED or name != "BLIND_REVIEW.jsonl":
            continue
        if entries[0][3].get("verdict") != "rejected":
            continue
        if (eo, claim_hash) in controls:
            continue
        chosen.append((entries[0], "blind"))
    for (eo, claim_hash, name), entries in reviews.items():
        if eo in EXCLUDED or name != "AFTER_REVEAL.jsonl":
            continue
        if entries[0][3].get("verdict") == "rejected":
            chosen.append((entries[0], "after_reveal"))

    rows = []
    for (review_path, ln, raw, r), phase in chosen:
        eo, claim_hash = r.get("instrument_id"), r.get("claim_sha256")
        member_pair = member_map.get((eo, claim_hash))
        if member_pair is None:
            # After-reveal records are for genuine versions that may not appear in the
            # current completion manifest; find same-instrument completion member.
            member_pair = next(((cp, m) for cp, c in completions for m in c.get("members", [])
                                if m.get("instrument_id") == eo), None)
        claim_entry = claim_bytes.get((eo, claim_hash))
        if claim_entry:
            claim_file, claim_line, claim_file_sha = claim_entry
            claim_path = str(claim_file.relative_to(ROOT))
        else:
            claim_path, claim_file_sha, claim_line = None, None, None
        if member_pair is None:
            cp = None
        else:
            cp, m = member_pair
        rows.append({
            "instrument_id": eo,
            "track": category(review_path),
            "review_phase": phase,
            "review_source": {"path": str(review_path.relative_to(ROOT)), "line": ln,
                              "file_sha256": sha(review_path.read_bytes()), "record_sha256": sha(raw)},
            "review_claim_sha256": claim_hash,
            "defects": r.get("defects", []),
            "prior_claim": {"path": claim_path, "file_sha256": claim_file_sha,
                            "line": claim_line, "record_sha256": claim_hash},
            "completion_path": str(cp.relative_to(ROOT)) if cp else None,
        })
    rows.sort(key=lambda x: (x["track"], int(x["instrument_id"].split(":")[1].rstrip("A")) if x["instrument_id"].split(":")[1].rstrip("A").isdigit() else 0, x["instrument_id"]))

    if len(rows) != 40 or len({r["instrument_id"] for r in rows}) != 40:
        raise ValueError("Apollo genuine-rejection denominator changed; reconcile before retry")
    if Counter(r["track"] for r in rows) != {"NRA": 6, "general": 34}:
        raise ValueError("Apollo rejection tracks changed")
    after_ids = {r["instrument_id"] for r in rows if r["review_phase"] == "after_reveal"}
    if after_ids != {"EO:6876", "EO:8163", "EO:10103", "EO:10915", "EO:12095"}:
        raise ValueError("after-reveal genuine versions differ from Apollo reconciliation")
    for row in rows:
        ref = row["prior_claim"]
        if not ref["path"] or not ref["line"]:
            raise ValueError("exact rejected claim bytes missing: " + row["instrument_id"])
        raw = abs_path(ref["path"]).read_bytes()
        line = raw.splitlines()[ref["line"] - 1]
        if sha(raw) != ref["file_sha256"] or sha(line) != ref["record_sha256"]:
            raise ValueError("rejected claim pointer/hash mismatch: " + row["instrument_id"])
        if json.loads(line)["instrument_id"] != row["instrument_id"]:
            raise ValueError("rejected claim identity mismatch")
        if row["instrument_id"] in EXCLUDED or (row["instrument_id"], ref["record_sha256"]) in controls:
            raise ValueError("owner-held or planted version cannot be a retry candidate")

    # Group at most 20 rows per stable batch file.
    for f in OUT.glob("batch-*.jsonl"):
        f.unlink()
    groups = [("n01", [x for x in rows if x["track"] == "NRA"])]
    general = [x for x in rows if x["track"] == "general"]
    groups += [(f"g{i:02d}", general[(i-1)*20:i*20]) for i in range(1, (len(general)+19)//20+1)]
    for name, chunk in groups:
        if not 1 <= len(chunk) <= 20 or len({r["track"] for r in chunk}) != 1:
            raise ValueError("retry batches must be nonempty, at most 20, and one track")
        out = OUT / f"batch-{name}.jsonl"
        out.write_text("".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in chunk))
    manifest = {
        "schema": "apollo-genuine-rejections-v1",
        "worker": {"role": "Codex deterministic inventory", "model_identifier": "gpt-6-luna",
                   "elapsed_seconds": None, "elapsed_note": "start wall marker unavailable; elapsed time not reconstructed",
                   "token_usage": None},
        "source_root": str(APOLLO.relative_to(ROOT)),
        "count": len(rows),
        "expected_count": 40,
        "matches_expected": len(rows) == 40,
        "tracks": {t: sum(x["track"] == t for x in rows) for t in ("NRA", "general")},
        "defect_fields": dict(sorted(Counter(d.get("field", "(unspecified)")
            for x in rows for d in x["defects"]).items())),
        "excluded_owner_hold": sorted(EXCLUDED),
        "completion_drops_not_resubmitted": [
            {"instrument_id": "EO:12921", "custody_block": "mirror/PDF bytes absent from repository custody"},
            {"instrument_id": "EO:12987", "custody_block": "mirror/PDF bytes absent from repository custody"},
            {"instrument_id": "EO:8937", "custody_block": "mirror/PDF bytes absent from repository custody"},
            {"instrument_id": "EO:8168", "custody_block": "quoted OCR text differs from checker copy"},
            {"instrument_id": "EO:10570", "custody_block": "quoted OCR text differs from checker copy"},
            {"instrument_id": "EO:10346", "custody_block": "quoted OCR text differs from checker copy"},
        ],
        "batch_files": [f"batch-{name}.jsonl" for name, _ in groups],
        "batch_sizes": {name: len(chunk) for name, chunk in groups},
        "rows": rows,
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {len(rows)} genuine rejection rows; expected 40: {len(rows) == 40}")


if __name__ == "__main__":
    main()

"""Eumenes: publish store locators for the National Mediation Board report PDFs, so the checker can hold them.

Named for Eumenes II, who built the Library of Pergamon. Owner decision D-20261110-papinian-board-bytes: the board
reports go into the Pergamon release-asset store, not onto main, and claim-checker reads them there. On 2026-11-10,
all 119 distinct report PDFs recorded by source-ladder were re-downloaded from nmb.gov, re-hashed (all matched their
recorded SHA-256) and uploaded. data/PERGAMON_MANIFEST.jsonl is the store's own record of them.

This job joins each manifest record to source-ladder's record of the same bytes and writes output/SOURCES.jsonl in
the shared source-record format, with a `pergamon` field. claim-checker's Pergamon adapter (sources.py) then fetches
the bytes from the locator and re-hashes them before counting them as held. The store is never trusted on its own.

It also fetches every manifest record by its locator and re-hashes it (no token needed) and fails if one is missing, so a
locator that does not resolve is never published. Standard library only.
"""
import json
import os
import sys
from pathlib import Path

REPO = Path(os.environ.get("REPO_ROOT", Path(__file__).resolve().parents[2]))
JOB = Path(os.environ.get("JOB_DIR", Path(__file__).resolve().parent))
OUT = Path(os.environ.get("OUTPUT_DIR", JOB / "output"))
LADDER = "jobs/source-ladder/output/SOURCES.jsonl"
sys.path.insert(0, str(REPO / "jobs/_lib"))


def read_jsonl(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def build(manifest, ladder, present):
    """(records, summary). present(record) -> bool says whether the store holds the bytes."""
    by_sha = {}
    for r in ladder:
        sha = r.get("sha256")
        if sha and "nmb.gov" in str(r.get("url", "")):
            by_sha.setdefault(sha, []).append(r)
    records, missing_in_store, no_ladder_record = [], [], []
    for m in manifest:
        sha = m.get("sha256")
        if not present(m):
            missing_in_store.append(sha)
            continue
        found = by_sha.get(sha)
        if not found:
            no_ladder_record.append(sha)
            continue
        ids = sorted({i for r in found for i in (r.get("instrument_ids") or []) if isinstance(i, str)})
        first = found[0]
        records.append({"sha256": sha, "url": first.get("url"), "bytes": m.get("bytes"), "instrument_ids": ids,
                        "page_or_item": first.get("page_or_item"), "route": "pergamon_store:nmb_report",
                        "citation": first.get("citation"),
                        "pergamon": {k: m[k] for k in ("sha256", "bytes", "ext", "backend", "locator", "stored_utc")
                                     if k in m}})
    records.sort(key=lambda r: r["sha256"])
    summary = {"manifest_records": len(manifest), "published": len(records),
               "orders_covered": len({i for r in records for i in r["instrument_ids"]}),
               "missing_in_store": missing_in_store, "no_source_ladder_record": no_ladder_record}
    return records, summary


def main():
    import pergamon_store as P
    store = P.Store.from_env()
    manifest = read_jsonl(JOB / "data/PERGAMON_MANIFEST.jsonl")
    def present(m):
        # Fetch by the record's own locator and re-hash, exactly as the checker will: the strongest test that the
        # published locator resolves to these bytes. (store.has() asks the configured backend, which on a runner
        # without Pergamon settings is the local git folder.)
        try:
            store.get_verified(m)
            return True
        except Exception:  # noqa: BLE001 - any failure means "not held"; it is reported, never trusted
            return False

    records, summary = build(manifest, read_jsonl(REPO / LADDER), present)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "SOURCES.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for r in records:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    (OUT / "SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in summary.items()}))
    if summary["missing_in_store"]:
        sys.exit(f"{len(summary['missing_in_store'])} manifest records are not in the store; nothing is trusted")
    return 0


if __name__ == "__main__":
    sys.exit(main())

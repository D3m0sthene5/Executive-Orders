"""Rebuild the claim checker's committed Opus data from the Opus Stage 11 complete zip.

The zip (207 MB, Git LFS) is not downloaded on GitHub's daily run, so the
checker reads two small committed files instead. Run this on the PC, where the
zip is present:

    python jobs/claim-checker/build_opus_index.py
        Rebuild data/opus_manifest_index.csv.gz: what the Opus release holds
        (path, bytes, sha256 of every file, plus the URL/sha256 pairs in the
        Opus fetch metadata *.meta.json). Needed only when the Opus release changes.

    python jobs/claim-checker/build_opus_index.py --text-pack
        Rebuild data/opus_text_pack.jsonl.gz: the text of every Opus-held source
        that a claim in research/readiness/claims/ cites, so GitHub can check
        those quotations too. Rerun it after agents add claims that cite Opus
        sources, then commit the jobs/claim-checker/data/ change.
"""

import argparse
import csv
import glob
import gzip
import hashlib
import io
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sources as S  # noqa: E402

HEX = re.compile(r"\b[0-9a-fA-F]{64}\b")
PACK_MAX_MB = 20  # gzip size; above this the pack is not written (keep committed data small)


def write_gz(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        with gzip.GzipFile(filename="", fileobj=fh, mode="wb", mtime=0) as gz:  # byte-identical reruns
            gz.write(data)


def require_zip(repo):
    zpath = repo / S.OPUS_COMPLETE_ZIP
    if not zpath.is_file() or S.is_lfs_pointer(zpath):
        sys.exit(f"{zpath} is missing or only a Git LFS pointer; run: git lfs pull --include \"{S.OPUS_COMPLETE_ZIP}\"")
    return zpath


def build_manifest_index(repo):
    zpath = require_zip(repo)
    rows, built = S.opus_index_rows_from_zip(zpath)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=S.INDEX_FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    data = buf.getvalue().encode("utf-8")
    write_gz(HERE / "data" / "opus_manifest_index.csv.gz", data)
    meta = {
        "built_from": S.OPUS_COMPLETE_ZIP,
        "zip_sha256": S.file_sha256(zpath),
        "zip_bytes": zpath.stat().st_size,
        "zip_manifest_built_utc": built,
        "rows_file": sum(r["kind"] == "file" for r in rows),
        "rows_fetch_meta": sum(r["kind"] == "meta" for r in rows),
        "csv_sha256": hashlib.sha256(data).hexdigest(),
        "note": "Index of what the Opus release holds. Holding a file is custody only, not authentication.",
    }
    (HERE / "data" / "opus_manifest_index.json").write_text(json.dumps(meta, indent=2) + "\n", "utf-8")
    print(json.dumps(meta, indent=2))


def cited_hashes(claims_glob):
    found = set()
    for p in sorted(glob.glob(claims_glob)):
        try:
            text = pathlib.Path(p).read_text("utf-8", "replace")
        except OSError:
            continue
        found.update(h.lower() for h in HEX.findall(text))
    return found


def build_text_pack(repo, claims_glob, out_path, shown=None):
    zpath = require_zip(repo)
    index = S.build_index(repo, HERE)
    reader = S.TextReader(None)
    cited = cited_hashes(claims_glob)
    records, skipped = [], {"not_opus": 0, "also_held_in_repo": 0, "no_text": 0}
    for sha in sorted(cited):
        copies = index.lookup_sha(sha)
        opus = [c for c in copies if c.origin.startswith("opus")]
        if not opus:
            skipped["not_opus"] += 1
            continue
        if any(c.custody == "repo_file" for c in copies):  # GitHub can read it from the repo
            skipped["also_held_in_repo"] += 1
            continue
        got = None
        for copy in opus:
            texts, _ = reader.texts(copy)
            if texts:
                pages, how = texts[0]
                got = {"sha256": sha, "how": how, "pages": pages,
                       "from": copy.page_or_item or (copy.text_path[1] if isinstance(copy.text_path, tuple) else "")}
                break
        if got is None:
            skipped["no_text"] += 1
        else:
            records.append(got)
    data = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records).encode("utf-8")
    compressed = gzip.compress(data, mtime=0)
    if len(compressed) > PACK_MAX_MB * 1_000_000:
        sys.exit(f"text pack would be {len(compressed) / 1e6:.1f} MB gzip (limit {PACK_MAX_MB} MB); not written")
    write_gz(out_path, data)
    meta = {
        "built_from": S.OPUS_COMPLETE_ZIP, "zip_sha256": S.file_sha256(zpath),
        "claims_glob": shown or claims_glob,
        "hashes_cited_in_claims": len(cited), "texts": len(records), "skipped": skipped,
        "gzip_bytes": len(compressed), "jsonl_sha256": hashlib.sha256(data).hexdigest(),
        "note": "Text extracted from Opus-held copies cited by claims; used only to check quotations on GitHub.",
    }
    out_path.with_name(out_path.name.replace(".jsonl.gz", ".json")).write_text(json.dumps(meta, indent=2) + "\n", "utf-8")
    print(json.dumps(meta, indent=2))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--text-pack", action="store_true", help="build data/opus_text_pack.jsonl.gz instead")
    ap.add_argument("--claims", default=None, help="glob of claim files (default research/readiness/claims/*.jsonl)")
    ap.add_argument("--out", default=None, help="where to write the text pack (default data/opus_text_pack.jsonl.gz)")
    args = ap.parse_args(argv)
    repo = HERE.parent.parent
    if args.text_pack:
        claims = args.claims or "research/readiness/claims/*.jsonl"
        claims_glob = claims if pathlib.Path(claims).is_absolute() else str(repo / claims)
        build_text_pack(repo, claims_glob, pathlib.Path(args.out) if args.out else HERE / S.TEXT_PACK,
                        shown=claims if not pathlib.Path(claims).is_absolute() else "(a folder outside the repo)")
    else:
        build_manifest_index(repo)


if __name__ == "__main__":
    main()

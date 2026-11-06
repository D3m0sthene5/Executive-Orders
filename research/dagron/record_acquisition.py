"""Record one image or PDF downloaded from the NYU collection, with provenance, in a STAGING folder.

    python3 -I research/dagron/record_acquisition.py FILE --id EO:708 --collection hein \
        --hein-volume 2 --hein-image 14 --url "https://heinonline.org/..." \
        --witness-kind official_printed_copy --observed-number 708 --observed-date 1907-11-02 \
        --signature-visible no --retrieved-by "browser agent (name/model)" [--note "..."]
    python3 -I research/dagron/record_acquisition.py --check

It copies FILE to research/dagron/acquired/<collection>/<EO id>__<sha12>.<ext> and appends one line to
research/dagron/acquired/PROVENANCE.jsonl. Nothing in production reads this folder: no job, the tracker or the
claim checker globs research/dagron/, and the file is not named SOURCES*.jsonl. Every record is graded
`nyu_collection_image_pending_codebook` with acceptable_as_original false and needs_page_check true; wiring the
images into the tracker is a separate, owner-approved step (see README.md). The script refuses an id that is not
in the manifest, a duplicate SHA-256, and a file that is not a PDF/JPEG/PNG/TIFF by its magic bytes.
"""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ACQ = os.path.join(HERE, "acquired")
PROV = os.path.join(ACQ, "PROVENANCE.jsonl")
MANIFEST = os.path.join(HERE, "NYU_FILM709_MANIFEST.jsonl")
CATALOG = {
    "hein": "https://search.library.nyu.edu/discovery/fulldisplay?docid=alma9998673098807871&vid=01NYU_INST:NYU&context=L",
    "film709": "https://search.library.nyu.edu/discovery/fulldisplay?docid=alma990007538410107876&vid=01NYU_INST:NYU&context=L",
}
WITNESS_KINDS = ("signed_original", "official_printed_copy", "typescript_or_file_copy", "transcription",
                 "index_or_register_entry", "not_at_expected_position", "different_order_at_position", "unclear")
MAGIC = {b"%PDF-": ("pdf", "application/pdf"), b"\xff\xd8\xff": ("jpg", "image/jpeg"),
         b"\x89PNG\r\n\x1a\n": ("png", "image/png"), b"II*\x00": ("tif", "image/tiff"), b"MM\x00*": ("tif", "image/tiff")}


def manifest_ids():
    ids = {}
    with open(MANIFEST, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            ids[r["instrument_id"] or r.get("proposed_id_not_in_census", "")] = r
    return ids


def records():
    if not os.path.exists(PROV):
        return []
    with open(PROV, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def check():
    ids, seen, bad = manifest_ids(), set(), 0
    for n, r in enumerate(records(), 1):
        path = os.path.join(os.path.dirname(HERE), "..", r["file"])
        problems = []
        if r["instrument_id"] not in ids:
            problems.append("id not in manifest")
        if r["sha256"] in seen:
            problems.append("duplicate sha256")
        seen.add(r["sha256"])
        if not os.path.exists(path):
            problems.append("file missing")
        else:
            with open(path, "rb") as fh:
                if hashlib.sha256(fh.read()).hexdigest() != r["sha256"]:
                    problems.append("sha256 mismatch")
        if r.get("acceptable_as_original") is not False or r.get("needs_page_check") is not True:
            problems.append("grade flags changed")
        if problems:
            bad += 1
            print(f"line {n} {r['instrument_id']}: {', '.join(problems)}")
    print(f"{len(seen)} records, {bad} with problems")
    return 1 if bad else 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--id")
    ap.add_argument("--collection", choices=sorted(CATALOG))
    ap.add_argument("--url", default="", help="exact page/image URL or citation as shown by the viewer")
    ap.add_argument("--hein-volume", default="")
    ap.add_argument("--hein-image", default="", help="image/page sequence the viewer shows")
    ap.add_argument("--reel", default="")
    ap.add_argument("--frame", default="", help="microfilm frame or position, if read from film")
    ap.add_argument("--witness-kind", choices=WITNESS_KINDS)
    ap.add_argument("--observed-number", default="", help="number exactly as printed/written, letters and fractions kept")
    ap.add_argument("--observed-date", default="")
    ap.add_argument("--observed-title", default="", help="title or first words as shown")
    ap.add_argument("--signature-visible", choices=("yes", "no", "unclear"), default="unclear")
    ap.add_argument("--retrieved-by", default="")
    ap.add_argument("--note", default="")
    a = ap.parse_args(argv)
    if a.check:
        return check()
    if not (a.file and a.id and a.collection and a.witness_kind and a.retrieved_by):
        ap.error("FILE, --id, --collection, --witness-kind and --retrieved-by are required")
    ids = manifest_ids()
    if a.id not in ids:
        sys.exit(f"{a.id} is not in the manifest; record it in a note for the owner instead")
    with open(a.file, "rb") as fh:
        data = fh.read()
    kind = next((v for k, v in MAGIC.items() if data.startswith(k)), None)
    if not kind:
        sys.exit("not a PDF/JPEG/PNG/TIFF by its first bytes (an access-denied HTML page saved as .pdf?)")
    sha = hashlib.sha256(data).hexdigest()
    if any(r["sha256"] == sha for r in records()):
        sys.exit(f"already recorded: {sha}")
    safe = a.id.replace(":", "_").replace("/", "_")
    rel = f"research/dagron/acquired/{a.collection}/{safe}__{sha[:12]}.{kind[0]}"
    dest = os.path.join(HERE, "acquired", a.collection, os.path.basename(rel))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copyfile(a.file, dest)
    m = ids[a.id]
    rec = {
        "schema": "dagron-nyu-acquisition/v1", "instrument_id": a.id, "eo_designation": m["eo_designation"],
        "manifest_group": m["manifest_group"], "collection": a.collection, "catalog_record": CATALOG[a.collection],
        "url": a.url, "hein_volume": a.hein_volume, "hein_image": a.hein_image, "reel": a.reel, "frame": a.frame,
        "manifest_likely_reel": m.get("likely_reel"), "file": rel, "sha256": sha, "bytes": len(data),
        "content_type": kind[1], "original_filename": os.path.basename(a.file),
        "retrieved_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "retrieved_by": a.retrieved_by, "access_route": "NYU Libraries authenticated access",
        "witness_kind_observed": a.witness_kind, "observed_number": a.observed_number,
        "observed_date": a.observed_date, "observed_title": a.observed_title,
        "signature_visible": a.signature_visible, "note": a.note,
        "grade": "nyu_collection_image_pending_codebook", "acceptable_as_original": False, "needs_page_check": True,
        "what_this_is_not": "Not an authenticated original, identity finding, custody grade or legal conclusion.",
    }
    os.makedirs(ACQ, exist_ok=True)
    with open(PROV, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(rel)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

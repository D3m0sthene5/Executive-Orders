"""Recover all 844 accepted Opus reviewer records from the pinned complete ZIP.

Usage: python research/stage20/code/extract_full_opus.py FULL_LFS_ZIP /tmp/opus844.jsonl
This extracts research evidence, NEVER complete legal findings.
"""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

EXPECTED_SHA="1fbbd45e9a8846a955cbdcaa5bba2b0f138c10c80049c5bb6063197f6ac62d47"
BASE="OPUS_STAGE11_FINITE_STATUS_DELTA/"
def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()
def main():
    if len(sys.argv)!=3:raise SystemExit(__doc__)
    archive,destination=map(Path,sys.argv[1:])
    if sha256(archive)!=EXPECTED_SHA:raise SystemExit("Incorrect complete Opus ZIP SHA-256 (Git LFS pointer or wrong archive?)")
    with zipfile.ZipFile(archive) as z:
        approved=[json.loads(r) for r in z.read(BASE+"STAGE11_ACCEPTED.jsonl").splitlines() if r.strip()]
        records=[json.loads(r) for r in z.read(BASE+"STAGE11_STATUS_RECORDS.jsonl").splitlines() if r.strip()]
    aid={r["instrument_id"]:r for r in approved};rid={r["instrument_id"]:r for r in records}
    if (len(aid),len(rid))!=(844,1155):raise SystemExit("Unexpected count or duplicate IDs")
    if any(x not in rid or rid[x]["final_substantive_effect"]!=r["final_substantive_effect"] for x,r in aid.items()):
        raise SystemExit("Accepted/record status mismatch")
    fields=["instrument_id","final_substantive_effect","lane","footprint_complete","historical_causes","review_verdict","review_problems","what_remains_inferential","text_source_grade","evidence_dir","review_dir"]
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open("w",encoding="utf-8") as f:
        for x in sorted(aid):
            f.write(json.dumps({k:rid[x].get(k) for k in fields},ensure_ascii=False,sort_keys=True)+"\n")
    print(json.dumps({"recovered_notes":len(aid),"human_certifications":0,"sha256":EXPECTED_SHA}))
if __name__=="__main__":main()

"""Append reviewed source requests, preserving the entire prior queue byte prefix."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
queue = ROOT / "research/readiness/FETCH_QUEUE.jsonl"
before = queue.read_bytes()
existing = [json.loads(s) for s in before.decode().splitlines() if s.strip()]
key = lambda r: (r["instrument_id"], tuple(sorted(r.get("urls", []))), r.get("step"))
keys = {key(r) for r in existing}
proposed = []
for iid in ("11022", "11256", "11782", "11829", "12095"):
    folder = HERE / "producer" / f"EO_{iid}"
    for path in folder.glob("proposed-source-requests.json*"):
        if path.suffix == ".jsonl":
            proposed += [json.loads(s) for s in path.read_text().splitlines() if s.strip()]
        else:
            proposed += json.loads(path.read_text())
proposed += [json.loads(s) for s in (HERE / "reviewer/EO_11022/FETCH_REQUESTS.jsonl").read_text().splitlines() if s.strip()]
proposed.append({"instrument_id":"EO:11782", "urls":["https://www.govinfo.gov/content/pkg/FR-1974-05-07/pdf/FR-1974-05-07.pdf"], "citation":"39 FR 15991", "step":"original_text", "requested_by":"Astra source retention 2026-10-18", "note":"Retain existing official source PDF page 7 for visual review; no image verification is inferred from extract."})
appended = []
for r in proposed:
    assert r.get("urls") and all(u.startswith("https://") for u in r["urls"])
    if key(r) not in keys:
        r["requested_by"] = "Astra source retention 2026-10-18"
        appended.append(r)
        keys.add(key(r))
with queue.open("ab") as fh:
    if before and not before.endswith(b"\n"):
        fh.write(b"\n")
    for r in appended:
        fh.write((json.dumps(r, ensure_ascii=False)+"\n").encode())
assert queue.read_bytes().startswith(before)

page_map = {
    "FR-1962-05-17": [5], "FR-1965-11-10": [7,8], "FR-1974-05-07": [7],
    "FR-1975-01-08": [11], "FR-1967-10-19": [5], "FR-1979-01-03": list(range(319,331)),
    "FR-1975-04-21": [9], "FR-1982-08-19": [9,10],
    "STATUTE-86": [], "STATUTE-93": [], "STATUTE-87": [], "STATUTE-88": [],
}
fixity = json.loads((ROOT / "jobs/official-fixity/output/MATCHED_BY_SHA256.json").read_text())
by_url = {r["url"]: h for h,r in fixity.items() if r.get("result") == "match"}
merged = {}
for r in proposed:
    for url in r["urls"]:
        package = next((p for p in page_map if f"/pkg/{p}/pdf/" in url), None)
        if not package:
            continue
        item = merged.setdefault(url, {"url":url,"instrument_ids":[],"pages":page_map[package],"expected_sha256":by_url.get(url)})
        if r["instrument_id"] not in item["instrument_ids"]:
            item["instrument_ids"].append(r["instrument_id"])
manifest = list(merged.values())
(ROOT / "jobs/astra-source-retention/REQUESTS.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
audit = {"queue_sha256_before":hashlib.sha256(before).hexdigest(),"prefix_bytes":len(before),"prefix_preserved":True,
         "appended_lines":len(appended),"retention_urls":len(manifest),"requests":appended}
(HERE / "SOURCE_QUEUE_APPEND_AUDIT.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:v for k,v in audit.items() if k != "requests"}))

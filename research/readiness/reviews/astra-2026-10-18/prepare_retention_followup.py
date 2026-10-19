"""Append follow-up requests; keep existing source-retention items for cache reuse."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
queue = ROOT / "research/readiness/FETCH_QUEUE.jsonl"
before = queue.read_bytes()
existing = [json.loads(s) for s in before.decode("utf-8").splitlines() if s.strip()]
seen = {(q["instrument_id"],u,q.get("step")) for q in existing for u in q.get("urls",[])}
proposals = json.loads((HERE / "NEXT_RETENTION_REQUESTS.json").read_text(encoding="utf-8"))
for case in ("EO_12159","EO_12182","EO_12285","EO_12075/v2"):
    for path in (HERE / "producer" / case).glob("proposed-source-requests.json*"):
        text = path.read_text(encoding="utf-8")
        proposals += json.loads(text) if path.suffix == ".json" else [json.loads(s) for s in text.splitlines() if s.strip()]
# The narrower 93 Stat.29 route above supersedes the producer's whole-volume
# discovery request; retain that proposal in its audit, without a redundant download.
appended = []
for r in proposals:
    assert r.get("urls") and all(u.startswith("https://") for u in r["urls"])
    urls = [u for u in r["urls"] if (r["instrument_id"],u,r.get("step")) not in seen]
    if urls:
        q = {**r,"urls":urls,"requested_by":"Astra source retention follow-up 2026-10-18"}
        appended.append(q)
        seen.update((q["instrument_id"],u,q.get("step")) for u in urls)
with queue.open("ab") as fh:
    for q in appended:
        fh.write((json.dumps(q,ensure_ascii=False)+"\n").encode("utf-8"))
assert queue.read_bytes().startswith(before)

manifest_path = ROOT / "jobs/astra-source-retention/REQUESTS.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
by_url = {r["url"]:r for r in manifest}
page_map = {
    "FR-1964-06-24":list(range(7,15)), "FR-1981-02-25":[11,12],
    "STATUTE-93-Pg29":[], "STATUTE-95-Pg357":list(range(155,173)),
    "STATUTE-93-Pg668":[], "STATUTE-92-Pg1705":[], "STATUTE-44-Pg577":[],
    "USCODE-1976-title45-chap8-subchapI-sec160":[],
}
fixity = json.loads((ROOT / "jobs/official-fixity/output/MATCHED_BY_SHA256.json").read_text(encoding="utf-8"))
hash_by_url = {v["url"]:k for k,v in fixity.items() if v.get("result") == "match"}
all_queue = existing + appended
for q in all_queue:
    if not str(q.get("requested_by","")).startswith("Astra"):
        continue
    for url in q.get("urls",[]):
        key = next((key for key in page_map if url.endswith('/'+key+'.pdf')), None)
        if not key:
            continue
        item = by_url.setdefault(url,{"url":url,"instrument_ids":[],"pages":page_map[key],"expected_sha256":hash_by_url.get(url)})
        if q["instrument_id"] not in item["instrument_ids"]:
            item["instrument_ids"].append(q["instrument_id"])
manifest = list(by_url.values())
manifest_path.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8",newline="\n")
audit = {"queue_sha256_before":hashlib.sha256(before).hexdigest(),"prefix_bytes":len(before),"prefix_preserved":True,
         "appended_lines":len(appended),"retention_urls":len(manifest),"requests":appended,
         "not_appended":"EO12262 whole93Statvolume request superseded by exact93Stat29 route located in held current-law lead.",
         "page_hints":"New statute page hints are acquisition instructions, not visually confirmed printed-to-PDF mappings."}
(HERE / "SOURCE_QUEUE_FOLLOWUP_AUDIT.json").write_text(json.dumps(audit,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({k:v for k,v in audit.items() if k not in ("requests",)}))

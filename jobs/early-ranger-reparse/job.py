"""Reparse cached LOC JSON WITHOUT network requests.

The documented LOC API sometimes uses HTTP in its id field. Earlier HTTPS
filtering discarded valid catalog records. Convert only trusted loc.gov item
URLs to HTTPS; preserve the original metadata, exact cached response bytes,
original SHA256 and item texts. All results remain discovery-only.
"""
import collections
import csv
import gzip
import hashlib
import json
import os
import re
import urllib.parse
from pathlib import Path

ROOT=Path(os.environ["REPO_ROOT"])
OUT=Path(os.environ["OUTPUT_DIR"])
PRIOR=ROOT/"jobs/early-ranger-scout/output"
ATTEMPTS=PRIOR/"LIVE_SEARCH_ATTEMPTS.jsonl"
CACHE=PRIOR/"response_cache"

def canonical(s):
    if not isinstance(s,str):return ""
    p=urllib.parse.urlsplit(s.strip())
    if p.scheme not in ("http","https") or p.hostname not in ("www.loc.gov","loc.gov"):
        return ""
    if not (p.path.startswith("/item/") or p.path.startswith("/resource/")):
        return ""
    return urllib.parse.urlunsplit(("https",p.netloc,p.path,p.query,""))

def text(v):
    if isinstance(v,list):return " ".join(text(x) for x in v)[:600]
    if isinstance(v,dict):return json.dumps(v,ensure_ascii=False)[:600]
    return str(v or "")[:600]

def relevance(title,date,route):
    s=title.lower()
    score=sum(3 for k in ("instructions","order","directive","secretary",
                          "militia","warrant","commission","regulation","troops")
              if k in s)
    if route.get("target_year") and route["target_year"] in date:score+=6
    if route.get("collection"):score+=1
    if re.search(r"\b(?:17[89]\d|18[0-5]\d)\b",date):score+=2
    return score

def main():
    a=[json.loads(x) for x in ATTEMPTS.read_text().splitlines() if x]
    runs=[x for x in a if x["provider"]=="loc" and x["status"].startswith("json_response")]
    if len(runs)!=23:raise ValueError("expected 23 original LOC responses")
    pool={}
    counts={}
    for route in runs:
        digest=route["response_sha256"]
        if not re.fullmatch(r"[a-f0-9]{64}",digest):raise ValueError("missing hash")
        f=CACHE/(digest+".json.gz")
        if f.stat().st_size>2_000_000:raise ValueError("cache too large")
        raw=gzip.decompress(f.read_bytes())
        if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError("raw response hash mismatch")
        data=json.loads(raw)
        n=0
        for obj in data.get("results",[]):
            orig=obj.get("id") or obj.get("url") or ""
            dest=canonical(orig)
            if not dest:continue
            n+=1
            title=text(obj.get("title"));date=text(obj.get("date"))
            objrow={
                "loc_item_https":dest,"catalog_id_as_returned":str(orig),
                "title":title,"catalog_date":date,"description":text(obj.get("description")),
                "contributors":text(obj.get("contributor")),
                "response_sha256":digest,"search_route":route["request_id"],
                "research_rank_NOT_legal_confidence":relevance(title,date,route),
                "original_authentication":"not_reviewed",
                "executive_order_inclusion":"not_decided"
            }
            if dest not in pool:pool[dest]=objrow
            else:
                old=pool[dest]
                old["search_route"]+=" | "+route["request_id"]
                old["research_rank_NOT_legal_confidence"]=max(
                    old["research_rank_NOT_legal_confidence"],objrow["research_rank_NOT_legal_confidence"])
        counts[route["request_id"]]={
          "response_sha256":digest,"returned_rows":len(data.get("results",[])),
          "accepted_loc_item_and_resource_identifiers":n}
    records=sorted(pool.values(),key=lambda x:(-x["research_rank_NOT_legal_confidence"],x["loc_item_https"]))
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/"LOC_MANUSCRIPT_CANDIDATES.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator="\n")
        w.writeheader();w.writerows(records)
    summary={
       "schema":"eo-loc-reparsed-catalog/v1",
       "existing_loc_json_responses_reused":len(runs),
       "cached_result_rows":sum(x["returned_rows"] for x in counts.values()),
       "loc_item_links_in_cached_responses":sum(x["accepted_loc_item_and_resource_identifiers"] for x in counts.values()),
       "unique_canonical_LOC_item_or_resource_links":len(records),
       "date_hints_from_1789_1861_NOT_confirmed":sum(
          bool(re.search(r"\b(?:17[89]\d|18[0-5]\d)\b",x["catalog_date"])) for x in records),
       "network_requests_made":0,
       "new_EO_identities_authenticated":0,
       "new_lifecycle_findings":0,
       "method":"LOC explicitly documents that API id values may use http. Permit an HTTPS rewrite only for a trusted loc.gov item/resource path."
    }
    (OUT/"REPARSE_SUMMARY.json").write_text(json.dumps(summary,indent=2)+"\n")
    (OUT/"PER_QUERY_COUNTS.json").write_text(json.dumps(counts,indent=2)+"\n")
    lines=["# Historical LOC manuscripts recovered from already downloaded JSON","",
           f"Recovered {len(records)} unique LOC item/resource links from {len(runs)} cached official API responses.",
           "These are **catalog candidates**. Verify the document's own pages, presidential action, date and inclusion before counting.", "",
           "## Candidates (sorted by research relevance, not legal confidence)",""]
    for r in records[:90]:
        lines.append(f"- [{r['title'][:150]}]({r['loc_item_https']}) — {r['catalog_date']}; "
                     f"research rank {r['research_rank_NOT_legal_confidence']}")
    (OUT/"LOC_RECOVERED_REVIEW.md").write_text("\n".join(lines)+"\n")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()

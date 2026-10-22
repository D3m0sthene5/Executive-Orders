"""Early original-document ranger: open LOC item metadata and image source pointers.

Focus on titles screened as possible *in-term* presidential papers.
Collect reproducible primary manuscript item metadata, link specific digital
resources, crosswalk Lord index date mentions, and preserve unresolved legal
inclusion. Prefer source recovery to extra certification or unrelated scans.
"""
from __future__ import annotations
import collections, csv, gzip, hashlib, io, json, os, re, time
import urllib.error, urllib.parse, urllib.request
from datetime import datetime,timezone
from pathlib import Path
import sys

ROOT=Path(os.environ["REPO_ROOT"])
OUT=Path(os.environ["OUTPUT_DIR"])
SEEDS=ROOT/"jobs/early-ranger-triage/output/PRIORITIZED_PRESIDENTIAL_PERIOD_CANDIDATES.csv"
LORD=ROOT/"research/stage14/LORD/LORD_CHRONOLOGICAL_REVIEW_LEADS.csv"
CACHE=OUT/"raw_LOC_metadata"
RESPONSE_MAX=4_000_000
TIMEOUT=17
MAX_ITEMS=22

sys.path.insert(0,str(ROOT/"jobs/_lib"))
from fetch_pool import FetchPool
POOL=FetchPool(Path(os.environ.get("JOB_CACHE_DIR",str(OUT.parent/"download-cache"))),max_bytes=RESPONSE_MAX)

def hash256(data):return hashlib.sha256(data).hexdigest()
def load_csv(p):
    with p.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def trim(v,limit=1600):
    if isinstance(v,list):return " | ".join(trim(x,500) for x in v)[:limit]
    if isinstance(v,dict):return json.dumps(v,ensure_ascii=False,sort_keys=True)[:limit]
    return str(v or "")[:limit]

def item_id(url):
    p=urllib.parse.urlsplit(url)
    if p.scheme!="https" or p.hostname not in ("loc.gov","www.loc.gov"):
        raise ValueError("Only exact official LOC item URLs are admitted")
    match=re.fullmatch(r"/item/([A-Za-z0-9_.-]+)/?",p.path)
    if not match:raise ValueError("Unexpected LOC item path")
    return match.group(1)

def fetch_item(item):
    url="https://www.loc.gov/item/"+item+"/?fo=json&at=item,resources"
    fetched=POOL.fetch(url)
    if urllib.parse.urlsplit(fetched['final_url']).hostname not in ('www.loc.gov','loc.gov'):raise ValueError('unexpected LOC JSON redirect')
    body=fetched['body']
    data=json.loads(body)
    if not isinstance(data,dict) or not isinstance(data.get("item"),dict):
        raise ValueError("LOC JSON missing item object")
    return body,data,url

def safe_https(candidate):
    if not isinstance(candidate,str):return ""
    if candidate.startswith("//"):candidate="https:"+candidate
    p=urllib.parse.urlsplit(candidate)
    if p.scheme not in ("https","http"):return ""
    host=p.hostname or ""
    if host not in ("www.loc.gov","loc.gov","cdn.loc.gov","tile.loc.gov",
                    "memory.loc.gov","hdl.loc.gov"):return ""
    return urllib.parse.urlunsplit(("https",p.netloc,p.path,p.query,""))

def collect_media(obj):
    """Collect source-controlled resource pointers, not inferred page claims."""
    accepted={}
    seen=set()
    def scan(v,depth=0):
        if depth>7 or len(seen)>=1300:return
        if isinstance(v,list):
            for x in v[:300]:scan(x,depth+1)
        elif isinstance(v,dict):
            for k,x in v.items():
                if k in ("image","url","pdf","fulltext_file","fulltext_derivative","filename","download","id"):
                    if isinstance(x,str):
                        url=safe_https(x)
                        if url and (re.search(r"\.(?:jpe?g|png|tif|tiff|pdf|txt|xml)(?:$|\?)",url,re.I) or "/resource/" in url):
                            tag=k+"|"+url
                            if tag not in seen:
                                seen.add(tag)
                                accepted[url]={"url":url,"link_role_as_metadata":k}
                if isinstance(x,(list,dict)):scan(x,depth+1)
    scan(obj.get("resources",[]))
    item=obj.get("item",{})
    for key in ("resource_links","service_low","service_medium","image_url"):
        scan(item.get(key,[]))
    # Prefer image file source candidates to thumbnails; no source image
    # is identified as the original page until visually inspected.
    def rank(x):
        u=x["url"].lower()
        return (0 if ".tif" in u or ".jpg" in u else 1 if ".pdf" in u else 2,
                1 if ("_150px" in u or "_300px" in u) else 0,len(u))
    return sorted(accepted.values(),key=rank)[:24],len(accepted)

def lord_nearby(iso,lord):
    # Date equality is a potential bibliographic crosswalk only; Lord's OCR
    # year can come from a neighboring row and must be treated as uncertain.
    if not re.fullmatch(r"\d{4}-\d\d-\d\d",iso or ""):return []
    yyyy,mm,dd=[int(x) for x in iso.split("-")]
    matches=[]
    for x in lord:
        try:
            if int(x.get("year_hint_UNVERIFIED") or 0)!=yyyy:continue
            if int(x.get("month") or 0)!=mm:continue
            if int(x.get("day") or 0)!=dd:continue
        except (ValueError,TypeError):continue
        matches.append({
            "lord_candidate_id":x.get("candidate_id",""),
            "lord_unverified_excerpt":trim(x.get("source_excerpt_UNVERIFIED"),360),
            "lord_scanned_page":x.get("loc_page_url",""),
            "identity_not_established":True
        })
    return matches[:12]

def build_plan(rows):
    target=[r for r in rows if r["triage_lane_NOT_identification"] in (
        "priority_presidential_period_directive_wording",
        "presidential_correspondence_needs_full_page")]
    target=sorted(target,key=lambda r:(-int(r["review_priority_NOT_probability"]),
                                       r["catalog_item_url"]))
    # Same-date "Madison to Armstrong" also has an alternative item in
    # the official collection; keep both as a duplicate-test set.
    additional=[{"catalog_item_url":"https://www.loc.gov/item/mjm022917/",
                 "title_as_indexed":"Madison to John Armstrong, August 13, 1814 (alternative catalog item)",
                 "date_as_indexed":"1814-08-13",
                 "triage_lane_NOT_identification":"possible_same_document_representation",
                 "review_priority_NOT_probability":"0"}]
    # These three previously selected manuscripts remain explicit follow-up
    # targets even when a refreshed search page no longer returns them.
    followups=["mjm017456","maj012871","mtjbib012509"]
    known={item_id(r["catalog_item_url"]):r for r in target}
    pinned=[]
    for id_ in followups:
        pinned.append(known.get(id_) or {
            "catalog_item_url":"https://www.loc.gov/item/"+id_+"/",
            "title_as_indexed":"Previously selected manuscript "+id_+" (metadata recheck)",
            "date_as_indexed":"",  # do not invent a refreshed date/title
            "triage_lane_NOT_identification":"historical_full_page_followup",
            "review_priority_NOT_probability":"0"})
    plan=[];seen=set()
    for row in pinned+target+additional:
        id_=item_id(row["catalog_item_url"])
        if id_ not in seen:plan.append(row);seen.add(id_)
    return plan

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    CACHE.mkdir(parents=True,exist_ok=True)
    rows=load_csv(SEEDS)
    lord=load_csv(LORD)
    plan=build_plan(rows)
    packets=[]
    request_logs=[]
    errors=0
    for i,r in enumerate(plan):
        id_=item_id(r["catalog_item_url"])
        entry={"catalog_item_id":id_,"url":r["catalog_item_url"],
               "original_title_from_prior_search":r["title_as_indexed"],
               "search_date_hint_unverified":r["date_as_indexed"],
               "prior_lane":r["triage_lane_NOT_identification"],
               "research_priority":r["review_priority_NOT_probability"],
               "status":"not_requested","source_metadata_sha256":"",
               "catalog_authorship_not_presidential_certification":True,
               "legal_EO_inclusion":"unknown"}
        if i>=MAX_ITEMS:
            entry["status"]="deferred_after_item_budget"
            packets.append(entry)
            continue
        if errors>=4:
            entry["status"]="skipped_after_provider_failures"
            packets.append(entry)
            continue
        try:
            raw,data,url=fetch_item(id_)
            digest=hash256(raw)
            with gzip.GzipFile(filename=str(CACHE/(digest+".json.gz")),mode="wb",mtime=0) as stream:stream.write(raw)
            item=data["item"]
            resources,total_resources=collect_media(data)
            entry.update({
                "status":"official_item_JSON_retrieved",
                "metadata_url_requested":url,
                "source_metadata_sha256":digest,
                "official_item_title":trim(item.get("title")),
                "item_date":trim(item.get("date") or item.get("sort_date")),
                "creator_names_from_catalog":trim(item.get("creators") or item.get("creator") or item.get("contributor_names")),
                "repository_issued_by":trim(item.get("repository")),
                "collection_titles":trim(item.get("source_collection") or item.get("partof")),
                "bibliographic_notes":trim(item.get("notes"),1400),
                "catalog_summary":trim(item.get("summary"),1200),
                "original_format_metadata":trim(item.get("original_format") or item.get("format")),
                "digitized_metadata":bool(item.get("digitized")),
                "count_media_candidate_links":total_resources,
                "media_resource_candidates":resources,
                "possible_Lord_same_date_entries_NOT_identity_proven":lord_nearby(
                    r["date_as_indexed"],lord),
                "source_metadata_does_not_prove_original_pages":True,
                "presidential_legal_authority_unverified":True
            })
            errors=0
        except Exception as exc:
            errors+=1
            entry["status"]="metadata_request_failed"
            entry["error"]=str(type(exc).__name__)+": "+str(exc)[:300]
        packets.append(entry)
        request_logs.append({"id":id_,"status":entry["status"],
                             "sha256":entry["source_metadata_sha256"]})
        print(f"{i+1}/{len(plan)} {id_} {entry['status']}",flush=True)
        time.sleep(0.7)
    summary={
        "schema":"eo-early-original-item-metadata/v1",
        "items_planned":len(plan),
        "item_request_budget":MAX_ITEMS,
        "item_metadata_deferred":sum(x["status"]=="deferred_after_item_budget" for x in packets),
        "item_metadata_retrieved":sum(x["status"]=="official_item_JSON_retrieved" for x in packets),
        "item_metadata_failed":sum(x["status"]=="metadata_request_failed" for x in packets),
        "item_metadata_skipped":sum(x["status"]=="skipped_after_provider_failures" for x in packets),
        "LOC_item_metadata_responses_custodied":len(list(CACHE.glob("*.json.gz"))),
        "digital_resource_link_candidates":sum(x.get("count_media_candidate_links",0) for x in packets),
        "items_with_any_media_resource_candidate":sum(bool(x.get("media_resource_candidates")) for x in packets),
        "items_with_Lord_same_date_OCR_candidates":sum(bool(x.get("possible_Lord_same_date_entries_NOT_identity_proven")) for x in packets),
        "unverified_instrument_originals_acquired":0,
        "presidential_inclusion_adjudicated":0,
        "human_certified_lifecycle":0,
        "limitation":"Catalog resource URLs and creators are finding aids. Exact original manuscript pages still require inspection; a same-date Lord index hit is not identity matching."
    }
    (OUT/"PRIMARY_ITEM_METADATA.jsonl").write_text(
        "".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in packets))
    (OUT/"METRICS.json").write_text(json.dumps(summary,indent=2)+"\n")
    (OUT/"REQUEST_LOG.json").write_text(json.dumps(request_logs,indent=2)+"\n")
    cols=["catalog_item_id","official_item_title","item_date","creator_names_from_catalog",
          "repository_issued_by","collection_titles","catalog_item_url","prior_lane",
          "status","media_links_found","near_Lord_same_date_candidates","legal_EO_inclusion"]
    rows=[]
    for x in packets:
        rows.append({
          "catalog_item_id":x["catalog_item_id"],
          "official_item_title":x.get("official_item_title") or x["original_title_from_prior_search"],
          "item_date":x.get("item_date") or x["search_date_hint_unverified"],
          "creator_names_from_catalog":x.get("creator_names_from_catalog",""),
          "repository_issued_by":x.get("repository_issued_by",""),
          "collection_titles":x.get("collection_titles",""),
          "catalog_item_url":x["url"],"prior_lane":x["prior_lane"],
          "status":x["status"],"media_links_found":len(x.get("media_resource_candidates",[])),
          "near_Lord_same_date_candidates":len(x.get("possible_Lord_same_date_entries_NOT_identity_proven",[])),
          "legal_EO_inclusion":"UNREVIEWED"
        })
    with (OUT/"EARLY_ORIGINAL_ITEM_WORKLIST.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols,lineterminator="\n")
        w.writeheader();w.writerows(rows)
    lines=["# Early presidential papers: item-level source acquisition","",
           f"Planned {len(plan)} official Library of Congress item endpoints; "
           f"attempted {len(request_logs)} metadata retrievals; "
           f"retrieved {summary['item_metadata_retrieved']} metadata packets. ",
           "",
           "The packet contains original manuscript/resource entry points, catalog creators "
           "and same-day Lord-index matches as distinct hypotheses. None is a confirmed "
           "executive order or legally operative clause.",
           "",
           "## Official item pages and research limitations",""]
    for x in packets:
        title=x.get("official_item_title") or x["original_title_from_prior_search"]
        lines.append(f"- [{title[:125]}]({x['url']}) — {x.get('item_date') or x['search_date_hint_unverified']}; "
                     f"status {x['status']}; media candidates {len(x.get('media_resource_candidates',[]))}; "
                     f"Lord same-date leads {len(x.get('possible_Lord_same_date_entries_NOT_identity_proven',[]))}.")
    lines.append("\n## Immediate next step\nOpen the LOC item images linked in PRIMARY_ITEM_METADATA.jsonl and "
                 "transcribe the operative instruction from its exact page. Test presidential capacity and "
                 "whether the instrument is already in Lord or the modern EO census. Preserve separate "
                 "unknown legal-causation fields.\n")
    (OUT/"ORIGINAL_SOURCE_REVIEW.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps(summary,indent=2),flush=True)

if __name__=="__main__":
    main()

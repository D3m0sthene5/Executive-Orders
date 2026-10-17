"""Acquire bounded original LOC manuscript facsimiles for top historical leads.

Source URIs come only from previously saved LOC item metadata. Retrieve an
official PDF of all pages where present, otherwise the listed master JPEGs.
No OCR, accession, identity certification, legal status, or cause is inferred.
"""
import csv,gzip,hashlib,json,os,re,time,urllib.parse,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(os.environ["REPO_ROOT"])
OUT=Path(os.environ["OUTPUT_DIR"])
ITEMS=ROOT/"jobs/early-ranger-original-items/output/PRIMARY_ITEM_METADATA.jsonl"
TARGET=[
 "mjm017456","maj012871","mtjbib012509",
 "mjm017450","mjm018302","mtjbib011110","mtjbib016595"
]
MAX_PER_FILE=13_000_000
MAX_PER_DOC_FILES=9

def sha(data):return hashlib.sha256(data).hexdigest()
def acceptable(url):
    p=urllib.parse.urlsplit(url)
    return (p.scheme=="https" and p.hostname=="tile.loc.gov"
        and p.path.startswith("/storage-services/")
        and re.search(r"\.(pdf|jpe?g)$",p.path,re.I))

def plan(record):
    if record.get("status")!="official_item_JSON_retrieved":
        raise ValueError("Missing document item metadata")
    c=record.get("media_resource_candidates",[])
    pdf=[x["url"] for x in c if x.get("link_role_as_metadata")=="pdf" and acceptable(x.get("url",""))]
    # Master scan JPEG pages are preferred to lossy thumbnails and avoid
    # accidentally retrieving identical preview images as separate pages.
    images=[x["url"] for x in c if acceptable(x.get("url",""))
            and re.search(r"\.jpe?g$",urllib.parse.urlsplit(x.get("url","")).path,re.I)
            and "/master/" in x["url"]]
    if pdf:return list(dict.fromkeys(pdf))[:1]
    return list(dict.fromkeys(images))[:MAX_PER_DOC_FILES]

def fetch(url):
    if not acceptable(url):raise ValueError("Unapproved candidate image link")
    request=urllib.request.Request(url,headers={
        "User-Agent":"ExecutiveOrdersHistoricalFacsimileRecovery/1.0",
        "Accept":"application/pdf,image/jpeg"})
    with urllib.request.urlopen(request,timeout=35) as response:
        final=urllib.parse.urlsplit(response.geturl())
        if final.scheme!="https" or final.hostname!="tile.loc.gov":
            raise ValueError("Unexpected facsimile redirect host")
        body=response.read(MAX_PER_FILE+1)
        if len(body)>MAX_PER_FILE:raise ValueError("Facsimile exceeded bound")
    suffix=urllib.parse.urlsplit(url).path.lower()
    if suffix.endswith(".pdf") and not(body.startswith(b"%PDF-") and b"%%EOF" in body[-4096:]):
        raise ValueError("not valid PDF byte structure")
    if suffix.endswith((".jpg",".jpeg")) and not(body.startswith(b"\xff\xd8\xff") and body.rstrip().endswith(b"\xff\xd9")):
        raise ValueError("not valid JPEG byte structure")
    return body

def main():
    inp=[json.loads(x) for x in ITEMS.read_text(encoding="utf-8").splitlines() if x]
    index={r["catalog_item_id"]:r for r in inp}
    if len(index)!=len(inp):raise ValueError("duplicate catalog id")
    if any(id_ not in index for id_ in TARGET):raise ValueError("target missing source metadata")
    OUT.mkdir(parents=True,exist_ok=True)
    links=[]
    for id_ in TARGET:
        record=index[id_]
        urls=plan(record)
        if not urls:
            links.append({"catalog_item_id":id_,"item_url":record["url"],
                         "retrieval_state":"no_original_facsimile_URL","download_count":0,
                         "presidential_authorship_verified":False})
            continue
        (OUT/"facsimiles"/id_).mkdir(parents=True,exist_ok=True)
        files=[]
        for i,url in enumerate(urls):
            suffix=".pdf" if url.lower().endswith(".pdf") else ".jpg"
            rel=f"facsimiles/{id_}/source_{i+1:02}{suffix}"
            path=OUT/rel
            row={"source_url":url,"stored_relpath":rel,
                 "state":"failed","sha256":"","bytes":0}
            try:
                body=fetch(url)
                if path.is_file() and path.read_bytes()!=body:
                    raise ValueError("Existing source file unexpectedly changed")
                if not path.exists():path.write_bytes(body)
                row.update({"state":"downloaded_exact_source_bytes",
                            "sha256":sha(body),"bytes":len(body)})
            except Exception as e:
                row["error"]=type(e).__name__+": "+str(e)[:280]
            files.append(row)
            print(id_,i+1,len(urls),row["state"],flush=True)
            time.sleep(0.6)
        links.append({
            "catalog_item_id":id_,
            "item_url":record["url"],
            "source_item_metadata_sha256":record["source_metadata_sha256"],
            "retrieval_state":"item_facsimiles_attempted",
            "download_count":sum(f["state"]=="downloaded_exact_source_bytes" for f in files),
            "facsimile_files":files,
            "original_page_handwriting_checked":False,
            "presidential_authorship_verified":False,
            "historical_EO_inclusion":False,
            "whole_lifecycle_status_verified":False})
    metrics={
        "schema":"eo-early-facsimile-pilot/v1",
        "targeted_original_item_ids":len(TARGET),
        "total_facsimile_urls_attempted":sum(len(x.get("facsimile_files",[])) for x in links),
        "facsimile_files_retained":sum(x["state"]=="downloaded_exact_source_bytes"
                                       for r in links for x in r.get("facsimile_files",[])),
        "items_with_facsimiles_retained":sum(x["download_count"]>0 for x in links),
        "acquired_source_bytes":sum(f["bytes"] for r in links for f in r.get("facsimile_files",[])),
        "newly_admitted_historical_presidential_orders":0,
        "complete_clause_histories":0,
        "source_warning":"LOC facsimile bytes are source images, not automatic evidence of legally operative clauses or presidential order status."
    }
    (OUT/"FACSIMILE_CUSTODY.json").write_text(json.dumps(links,ensure_ascii=False,indent=2)+"\n")
    (OUT/"FACSIMILE_METRICS.json").write_text(json.dumps(metrics,indent=2)+"\n")
    lines=["# Original LOC facsimile recovery: targeted early directive candidates","",
           "Source images were acquired from URLs published by LOC item metadata. "
           "They remain unreviewed for original signer, complete page coverage and "
           "EO inclusion. The source XML texts and original catalog records are in earlier jobs.",
           ""]
    for r in links:
        lines.append(f"- [{r['catalog_item_id']}]({r['item_url']}): "
                     f"{r['download_count']} of {len(r.get('facsimile_files',[]))} facsimile files retained.")
        for f in r.get("facsimile_files",[]):
            if f["state"]=="downloaded_exact_source_bytes":
                lines.append(f"  - \`{f['stored_relpath']}\` — {f['bytes']} bytes; SHA-256 \`{f['sha256']}\`")
            else:
                lines.append(f"  - Attempt failed: {f.get('error')}")
    (OUT/"FACSIMILE_REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps(metrics,indent=2),flush=True)

if __name__=="__main__":
    main()

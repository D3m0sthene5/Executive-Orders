"""Acquire full listed master JPEG page images for three substantive 1803–1832 leads.

These are actual image resource bytes rather than the service-layer PDF link.
No metadata-based legal conclusion or complete EO claim follows from retrieval.
"""
import csv,hashlib,json,os,re,time,urllib.parse,urllib.request
from pathlib import Path

ROOT=Path(os.environ["REPO_ROOT"])
OUT=Path(os.environ["OUTPUT_DIR"])
INPUT=ROOT/"jobs/early-ranger-original-items/output/PRIMARY_ITEM_METADATA.jsonl"
IDS=["mjm017456","maj012871","mtjbib012509"]
EXPECT={"mjm017456":3,"maj012871":3,"mtjbib012509":4}
MAX_BYTES=5_000_000

def sha(b):return hashlib.sha256(b).hexdigest()
def fetch(url):
    p=urllib.parse.urlsplit(url)
    if p.scheme!="https" or p.hostname!="tile.loc.gov" or "/storage-services/master/" not in p.path or not p.path.endswith(".jpg"):
        raise ValueError("Unapproved original manuscript JPEG source")
    req=urllib.request.Request(url,headers={"User-Agent":"ExecutiveOrdersOriginalManuscriptPages/1.0",
                                            "Accept":"image/jpeg"})
    with urllib.request.urlopen(req,timeout=25) as r:
        final=urllib.parse.urlsplit(r.geturl())
        if final.scheme!="https" or final.hostname!="tile.loc.gov":
            raise ValueError("Unexpected media redirect")
        raw=r.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES or not raw.startswith(b"\xff\xd8\xff") or not raw.rstrip().endswith(b"\xff\xd9"):
        raise ValueError("Bad or oversized JPEG")
    return raw

def main():
    rs=[json.loads(s) for s in INPUT.read_text(encoding="utf-8").splitlines() if s]
    by={x["catalog_item_id"]:x for x in rs}
    rows=[]
    for id_ in IDS:
        packet=by[id_]
        resources=[x["url"] for x in packet.get("media_resource_candidates",[])
                   if ".jpg" in x.get("url","") and "/master/" in x.get("url","")]
        resources=list(dict.fromkeys(resources))
        if len(resources)!=EXPECT[id_]:
            raise ValueError("Original manuscript pages differ from LOC metadata for "+id_)
        folder=OUT/id_
        folder.mkdir(parents=True,exist_ok=True)
        for n,url in enumerate(resources,1):
            item={"catalog_item":id_,"item_url":packet["url"],"page_in_LOC_resource_sequence":n,
                  "source_URL":url,"metadata_SHA256":packet["source_metadata_sha256"],
                  "source_state":"failed","stored_path":"","sha256":"","bytes":0,
                  "exact_executive_order_clause_checked":False}
            try:
                raw=fetch(url)
                rel=f"{id_}/page_{n:02}.jpg"
                (OUT/rel).write_bytes(raw)
                item.update({"source_state":"original_page_JPEG_bytes_acquired",
                             "stored_path":rel,"sha256":sha(raw),"bytes":len(raw)})
            except Exception as exc:
                item["error"]=type(exc).__name__+": "+str(exc)[:250]
            rows.append(item)
            print(id_,n,item["source_state"],flush=True)
            time.sleep(0.5)
    with (OUT/"PAGE_IMAGE_CUSTODY.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n")
        w.writeheader();w.writerows(rows)
    metric={"schema":"eo-early-LOC-full-page-images/v1",
            "target_items":len(IDS),"LOC_page_resources_in_known_item_manifest":len(rows),
            "original_scan_JPEGs_acquired":sum(x["source_state"].startswith("original_page") for x in rows),
            "total_scan_bytes":sum(x["bytes"] for x in rows),
            "new_historical_EOs_admitted":0,"original_clause_authentication_done":False}
    (OUT/"PAGE_IMAGE_METRICS.json").write_text(json.dumps(metric,indent=2)+"\n")
    lines=["# Direct manuscript page sequence for historical instruction candidates","",
           "These are the master JPEG bytes linked from LOC item metadata (rather than a tiny service-layer PDF). "
           "Page image sequence provides material for actual manuscript/edition comparison. No identity inclusion or legal status decision is made.",""]
    for row in rows:
        if row["source_state"]=="original_page_JPEG_bytes_acquired":
            lines.append(f"- {row['catalog_item']} source page {row['page_in_LOC_resource_sequence']}: "
                f"[LOC master image]({row['source_URL']}) · SHA-256 {row['sha256']}")
        else:
            lines.append(f"- {row['catalog_item']} page {row['page_in_LOC_resource_sequence']}: {row.get('error')}")
    (OUT/"PRIMARY_PAGES.md").write_text("\n".join(lines)+"\n")
    print(json.dumps(metric,indent=2),flush=True)

if __name__=="__main__":main()

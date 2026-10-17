"""Reconcile 1862-1906 proxy-year frame to exact Stage17 SQLite.

The Stage15 year projection reports 611 rows while the later Stage17 tracker
reports 617. This is NOT a trivial discrepancy when prioritizing apparently
empty historical years. Restore only the 8.25MB compressed database pack, then
recompute without touching earlier releases or changing the working universe.
"""
import collections,csv,hashlib,json,os,re,sqlite3
from pathlib import Path
import zstandard

ROOT=Path(os.environ["REPO_ROOT"])
OUT=Path(os.environ["OUTPUT_DIR"])
PARTS=ROOT/"research/releases/database"
STAGE15=ROOT/"research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv"
LORD=ROOT/"research/stage14/LORD/LORD_CHRONOLOGICAL_REVIEW_LEADS.csv"
ZST_SHA="1ff2cebcba4f3c4fef08140d15e0fc958a26b743fdd41acb4c8f3585e4a9f923"
DB_SHA="c362f5a8de7c31be2d1a700b00272aca9597136d74ff575fdc72ac24373984e1"

def sha(b):return hashlib.sha256(b).hexdigest()
def rows(path):
    with path.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))
def getyear(v):
    s=str(v or "")
    match=re.match(r"^(\d{4})",s)
    return int(match.group(1)) if match else None
def write_csv(path,rs):
    if not rs:return
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator="\n")
        w.writeheader();w.writerows(rs)

def main():
    parts=sorted(PARTS.glob("database.part???"))
    if len(parts)!=5:raise ValueError("Stage17 database fragment count changed")
    compressed=b"".join(p.read_bytes() for p in parts)
    if sha(compressed)!=ZST_SHA:raise ValueError("Unrecognized canonical compressed archive")
    raw=zstandard.ZstdDecompressor().decompress(compressed,max_output_size=150_000_000)
    if sha(raw)!=DB_SHA:raise ValueError("Stage17 database original SHA-256 mismatch")
    OUT.mkdir(parents=True,exist_ok=True)
    sqlite_path=OUT/"STAGE17_REFERENCE.sqlite"
    sqlite_path.write_bytes(raw)
    try:
        c=sqlite3.connect(f"file:{sqlite_path.as_posix()}?mode=ro",uri=True)
        cols={r[1] for r in c.execute("PRAGMA table_info(instruments)")}
        if not {"id","issuance_date","include_proxy"}.issubset(cols):raise ValueError("Unexpected Stage17 schema")
        data=list(c.execute("SELECT id,issuance_date FROM instruments WHERE include_proxy=1"))
        if len(data)!=14972:raise ValueError("Working bibliography changed")
        c.close()
    finally:
        sqlite_path.unlink(missing_ok=True)
    stage15=rows(STAGE15);lord=rows(LORD)
    if len(stage15)!=14972 or len(lord)!=1023:raise ValueError("Historical inputs changed")
    stage15_ids={r["id"]:r for r in stage15}
    latest={id_:getyear(y) for id_,y in data}
    if set(stage15_ids)!=set(latest):raise ValueError("Stage15/17 proxy identity mismatch")
    older={id_:getyear(r["date_effective"]) for id_,r in stage15_ids.items()}
    changes=[]
    for id_ in sorted(latest):
        if older[id_]!=latest[id_]:
            changes.append({"instrument_id":id_,"stage15_year":older[id_] or "",
                            "stage17_year":latest[id_] or "",
                            "date_change_requires_original_confirmation":"yes"})
    lordyears=collections.Counter()
    for row in lord:
        y=getyear(row.get("year_hint_UNVERIFIED"))
        if y:lordyears[y]+=1
    oldCount=collections.Counter(older.values())
    newCount=collections.Counter(latest.values())
    rowsOut=[]
    for y in range(1862,1907):
        rowsOut.append({"year":y,"stage15_proxy_count":oldCount[y],
                        "stage17_canonical_proxy_count":newCount[y],
                        "delta":newCount[y]-oldCount[y],
                        "Lord_OCR_markers_UNVERIFIED":lordyears[y],
                        "stage17_empty_year_with_Lord_leads":int(newCount[y]==0 and lordyears[y]>0),
                        "document_gap_inference":"UNKNOWN_NEEDS_PRIMARY_SOURCE"})
    summary={
     "schema":"eo-stage17-early-year-bridge/v1",
     "stage15_universe":len(stage15),
     "stage17_universe":len(latest),
     "stage15_1862_1906_proxies":sum(oldCount[y] for y in range(1862,1907)),
     "stage17_1862_1906_proxies":sum(newCount[y] for y in range(1862,1907)),
     "ids_whose_year_projection_changed":len(changes),
     "stage17_empty_years_with_Lord_OCR_date_leads":sum(x["stage17_empty_year_with_Lord_leads"] for x in rowsOut),
     "year_bibliography_is_not_complete_historical_census":True,
     "new_authenticated_unnumbered_Orders":0,
     "status":"Recomputed from original verified Stage17 SQLite; no legal decision inferred."
    }
    write_csv(OUT/"STAGE15_TO_STAGE17_YEAR_CHANGES.csv",changes)
    write_csv(OUT/"LATEST_1862_1906_CENSUS_YEAR_MATRIX.csv",rowsOut)
    (OUT/"BRIDGE_SUMMARY.json").write_text(json.dumps(summary,indent=2)+"\n")
    lines=["# Latest 19th-century census proxy crosswalk","",
           f"Stage15 ({summary['stage15_1862_1906_proxies']}) vs Stage17 "
           f"({summary['stage17_1862_1906_proxies']}) included 1862–1906 date projections; "
           f"**{summary['ids_whose_year_projection_changed']}** year-coordinate differences across whole bibliography.",
           "Uncounted Lord OCR markers are candidate bibliography, not proven EO documents.","",
           "## Latest Stage17 zero-proxy years with unverified Lord references"]
    for r in rowsOut:
        if r["stage17_empty_year_with_Lord_leads"]:
            lines.append(f"- {r['year']}: 0 Stage17 included proxies; {r['Lord_OCR_markers_UNVERIFIED']} Lord OCR date markers (unverified)")
    lines.append("\nDo not infer actual issuance count from either frame. Work from primary images, president/agency attribution and date-crosswalks.")
    (OUT/"BRIDGE_REPORT.md").write_text("\n".join(lines)+"\n")
    print(json.dumps(summary,indent=2),flush=True)

if __name__=="__main__":main()

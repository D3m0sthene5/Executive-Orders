"""Extend early-order census diagnostics through 1906 using existing evidence.

A number assigned retrospectively, a bibliographic proxy, and a presidential
order are distinct. We compare the 1862-1906 stage15 included frame to Lord
OCR date leads without counting raw OCR as additional orders.
"""
from __future__ import annotations
import collections,csv,json,os,re
from pathlib import Path
from urllib.parse import urlencode

ROOT=Path(os.environ["REPO_ROOT"])
OUT=Path(os.environ["OUTPUT_DIR"])
FRAME=ROOT/"research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv"
LORD=ROOT/"research/stage14/LORD/LORD_CHRONOLOGICAL_REVIEW_LEADS.csv"

def load(path):
    with path.open(encoding="utf-8",newline="") as f:return list(csv.DictReader(f))

def int_year(x):
    try:
        v=int(str(x or "").strip())
        return v if 1789<=v<=2026 else None
    except ValueError:return None

def row_date(r):
    y=int_year(r.get("year_hint_UNVERIFIED"))
    if y is None:return None
    try:
        m=int(r.get("month") or 0);d=int(r.get("day") or 0)
        if 1<=m<=12 and 1<=d<=31:return (y,m,d)
    except ValueError:pass
    return (y,None,None)

def main():
    frame=load(FRAME)
    lord=load(LORD)
    if len(frame)!=14972 or len(lord)!=1023:
        raise ValueError("Historic frozen source population changed")
    years=collections.defaultdict(list)
    for r in frame:
        if r.get("included_in_bibliography") not in ("1","True","true"):
            raise ValueError("Historical census frame inclusion changed")
        year=int_year(r.get("date_effective"))
        if year and 1862<=year<=1906:
            years[year].append(r)
    lord_by_year=collections.defaultdict(list)
    for r in lord:
        date=row_date(r)
        if date is None:continue
        year=date[0]
        if 1862<=year<=1906:
            lord_by_year[year].append((r,date))
    categories={"civil_service":"appointments civil service eligibility",
                "public_land":"president land reservation military reservation survey",
                "naval_war":"president war secretary navy military directives",
                "printed_register":"executive orders printed General Land Office Department of the Interior"}
    annual=[]
    plan=[]
    detailed=[]
    for year in range(1862,1907):
        proxies=years[year]
        markers=lord_by_year[year]
        unique_days={(d[1],d[2]) for _,d in markers if d[1] is not None}
        flags=sum(bool(x.get("flags")) for x,_ in markers)
        # Input dates are unverified OCR; both source classes may omit EOs.
        if not proxies and markers:lane="OCR_LEAD_WITH_NO_INCLUDED_PROXY"
        elif not markers and proxies:lane="INCLUDED_PROXY_WITH_NO_LORD_OCR_MARKER"
        elif not markers:lane="NO_MATCHING_LEADS_UNKNOWN_NOT_ZERO"
        else:lane="BOTH_UNRECONCILED_INVENTORIES"
        annual.append({
            "year":year,"working_included_bibliographic_proxies":len(proxies),
            "distinct_proxy_ids":len({x["id"] for x in proxies}),
            "Lord_date_markers_UNVERIFIED":len(markers),
            "Lord_distinct_date_tokens_UNVERIFIED":len(unique_days),
            "Lord_flagged_markers_UNVERIFIED":flags,
            "gap_category":lane,
            "identity_inclusion_newly_proven":0,
            "originals_verified":0,
            "review_action":"Crosswalk each date to original agency or presidential paper; avoid inferring a physical EO from OCR"
        })
        for kind,terms in categories.items():
            query=f"{year} {terms}"
            plan.append({
                "year":year,"route":kind,"query":query,
                "loc_query":"https://www.loc.gov/search/?"+urlencode({"fo":"json","q":query,"c":"10"}),
                "nara_human_search":"https://catalog.archives.gov/search?"+urlencode({"q":query}),
                "route_status":"planned_NOT_executed",
                "EO_identity_authenticated":0
            })
        for row,date in markers:
            detailed.append({
                "year_unverified":year,
                "candidate_id":row.get("candidate_id",""),
                "date_hint_unverified":f"{year:04}-{date[1]:02}-{date[2]:02}" if date[1] is not None else str(year),
                "source_excerpt_unverified":row.get("source_excerpt_UNVERIFIED",""),
                "Lord_printed_page_URL":row.get("loc_page_url",""),
                "Lord_row_flags":row.get("flags",""),
                "same_year_included_proxy_count":len(proxies),
                "identity_already_crosswalked":"unknown",
                "presidential_authority_authenticated":"no",
                "new_EO_inclusion_state":"unassessed"
            })
    # Prioritize specific OCR leads whose relative bibliographic geography
    # is sparse. Scores guide work, NEVER measure legal truth probability.
    weights={r["year"]:r for r in annual}
    detailed.sort(key=lambda x:(weights[x["year_unverified"]]["working_included_bibliographic_proxies"],
                                -len(x["source_excerpt_unverified"]),x["candidate_id"]))
    OUT.mkdir(parents=True,exist_ok=True)
    def csvout(filename,items):
        with (OUT/filename).open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(items[0]),lineterminator="\n")
            w.writeheader();w.writerows(items)
    csvout("HISTORICAL_1862_1906_YEAR_MATRIX.csv",annual)
    csvout("UNAUTHENTICATED_19C_LORD_DATE_LEADS.csv",detailed)
    csvout("HISTORICAL_1862_1906_QUERY_PLAN.csv",plan)
    summary={
      "schema":"eo-19c-census-gap-audit/v1",
      "research_years":len(annual),
      "working_included_1862_1906_proxies":sum(len(v) for v in years.values()),
      "distinct_included_1862_1906_proxy_years":sum(bool(years[y]) for y in range(1862,1907)),
      "Lord_OCR_date_markers_1862_1906_UNVERIFIED":len(detailed),
      "Lord_date_markers_in_years_with_zero_included_proxies":sum(
         int(x["working_included_bibliographic_proxies"])==0 and int(x["Lord_date_markers_UNVERIFIED"])>0 for x in annual),
      "years_with_proxy_but_zero_Lord_marker":sum(r["working_included_bibliographic_proxies"]>0 and r["Lord_date_markers_UNVERIFIED"]==0 for r in annual),
      "new_annual_historical_search_routes_PLANNED":len(plan),
      "new_historical_EOs_auth":0,
      "source_frame":"Stage15 14,972 included bibliographic proxies and unverified Lord OCR date leads",
      "interpretation":"Neither source is a complete inventory. This is a targeted omission screen and archive worklist, not an EO count or availability assertion."
    }
    (OUT/"GAP_SUMMARY.json").write_text(json.dumps(summary,indent=2)+"\n")
    markdown=["# 1862–1906 early-order ranger: 45-year source coverage screen","",
      f"Working bibliography proxies: **{summary['working_included_1862_1906_proxies']}**. "
      f"Unverified Lord OCR date markers in this period: **{len(detailed)}**. "
      f"Search routes prepared: **{len(plan)}** (not executed).",
      "",
      "These units are different: numbered/bibliographic EO IDs, provisional year hints and physical presidential orders require a source-to-document crosswalk.",
      "",
      "## Highest-priority annual discrepancies","",
      "| Year | Included proxies | Lord OCR hints | Classification |",
      "|---:|---:|---:|---|"]
    for r in sorted(annual,key=lambda x:(not x["gap_category"].startswith("OCR_LEAD"),x["working_included_bibliographic_proxies"],-x["Lord_date_markers_UNVERIFIED"]))[:30]:
        markdown.append(f"| {r['year']} | {r['working_included_bibliographic_proxies']} | {r['Lord_date_markers_UNVERIFIED']} | {r['gap_category']} |")
    markdown += ["", "The source-excerpt worklist is sorted toward low-coverage years. Review presidential signatures, secretary-by-command issuances and archival duplicates before adding instruments. No candidate was promoted into the census."]
    (OUT/"19C_GAP_REPORT.md").write_text("\n".join(markdown)+"\n")
    print(json.dumps(summary,indent=2),flush=True)

if __name__=="__main__":main()

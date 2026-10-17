"""Generate, optionally run, and preserve multi-route early-order source searches.

Inputs are *catalogue leads*, not authenticated orders. The default plan mode
needs no network. --fetch queries the documented public LOC JSON search API,
stores exact JSON response bytes by SHA-256, and never admits any result to the
working EO bibliography. NARA catalog queries remain human links because its
official API requires a key.
"""

import argparse
import csv
import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LORD = ROOT / "research/stage14/LORD/LORD_CHRONOLOGICAL_REVIEW_LEADS.csv"
SEEDS = ROOT / "research/stage18/data/EARLY_SOURCE_CANDIDATES.csv"
STOP = set("the and for from with that this there which under into have been were shall said such their those these president united states executive order secretary department government congress act laws provision american washington dated date letter copy image source unknown year state general two one his her she him them you your i a an of to in on by at as is it be or not no of".split())
MONTHS = {1:"January",2:"February",3:"March",4:"April",5:"May",6:"June",7:"July",8:"August",9:"September",10:"October",11:"November",12:"December"}


def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def year_hint(raw):
    if raw and re.fullmatch(r"1[789][0-9]{2}|19[0-3][0-9]",raw):
        return int(raw)
    return None


def distinctive(text, limit=5):
    words=[]
    for token in re.findall(r"[A-Za-z][A-Za-z'-]{3,}",text or ""):
        word=token.lower().strip("'-")
        if word not in STOP and word not in words and not word.endswith("conge"):
            words.append(word)
    return words[:limit]


def search_url(query):
    return "https://www.loc.gov/search/?"+urllib.parse.urlencode({"q":query,"fo":"json","at":"results,pagination","c":"5","sp":"1"})


def catalog_url(query):
    return "https://catalog.archives.gov/search?"+urllib.parse.urlencode({"q":query})


def load_leads():
    with LORD.open(newline="",encoding="utf-8") as stream:
        lord=list(csv.DictReader(stream))
    with SEEDS.open(newline="",encoding="utf-8") as stream:
        seeds=list(csv.DictReader(stream))
    if len(lord)!=1023 or len(seeds)!=6:
        raise ValueError("unexpected early-source lead inventory")
    out=[]
    for r in lord:
        year=year_hint(r["year_hint_UNVERIFIED"])
        month=int(r["month"]) if r["month"].isdigit() else None
        day=int(r["day"]) if r["day"].isdigit() else None
        # The OCR geometry can pair a wrong year with a neighboring line.
        date=f"{year:04d}-{month:02d}-{day:02d}" if year and month and day else None
        text=r["source_excerpt_UNVERIFIED"]
        out.append({"lead_id":r["candidate_id"],"lead_origin":"lord_ocr_unverified","date_hint_unverified":date,"year_hint_unverified":year,"title_or_excerpt":text,"issuer_hint_unverified":"","lord_scan_url":r["loc_page_url"],"known_primary_source_url":"","known_source_representation":"","inclusion_state":"unverified_catalogue_lead","source_pdf_sha256":r["source_pdf_sha256"],"date_warning":"OCR year/day may belong to adjacent row; inspect scanned Lord page"})
    for r in seeds:
        out.append({"lead_id":r["candidate_id"],"lead_origin":"stage18_curated_candidate","date_hint_unverified":r["date"],"year_hint_unverified":int(r["date"][:4]),"title_or_excerpt":r["document_identity"],"issuer_hint_unverified":r.get("claimed_issuer", ""),"lord_scan_url":"","known_primary_source_url":r["primary_source_url"],"known_source_representation":r["source_representation"],"inclusion_state":r["inclusion_state"],"source_pdf_sha256":"","date_warning":"source-located date; presidential-order identity and inclusion remain unadjudicated"})
    # A blank-space grid finds possible documents that the Lord index never listed.
    # These are survey cells, not claims that an order exists in every year.
    for year in range(1789,1801):
        out.append({"lead_id":f"SURVEY-18C-{year}","lead_origin":"systematic_18c_survey","date_hint_unverified":"","year_hint_unverified":year,"title_or_excerpt":f"Unindexed presidential directives or instructions issued in {year}","issuer_hint_unverified":"","lord_scan_url":"","known_primary_source_url":"","known_source_representation":"","inclusion_state":"survey_cell_no_document_asserted","source_pdf_sha256":"","date_warning":"year is a survey boundary, not a document date"})
    return out


def routes_for(lead):
    year=lead["year_hint_unverified"]
    if lead["lead_origin"]=="systematic_18c_survey":
        patterns=[
            ("presidential_letterbooks",f"{year} presidential letterbook instructions"),
            ("departmental_recipient",f"{year} secretary treasury war state presidential directions"),
            ("military_frontier",f"{year} presidential militia frontier instructions"),
            ("land_treaty",f"{year} presidential land Indian treaty directive"),
            ("printed_ephemera",f"{year} by command president broadside proclamation"),
            ("congressional_reprint",f"{year} presidential instructions American State Papers"),
        ]
        return [{"lead_id":lead["lead_id"],"route":kind,"query":query,"loc_api_url":search_url(query),"nara_human_search_url":catalog_url(query),"state":"planned_not_searched"} for kind,query in patterns]
    tokens=distinctive(lead["title_or_excerpt"])
    date=lead["date_hint_unverified"]
    name=lead["issuer_hint_unverified"]
    focus=" ".join(tokens[:4]) or "presidential directive"
    queries=[]
    # Distinct routes intentionally do not rely on only a supposed EO number.
    if date:
        yy,mm,dd=map(int,date.split("-"))
        queries.append(("date_topic",f"{MONTHS[mm]} {dd} {yy} {focus}"))
    else:
        queries.append(("era_topic",f"{year or ''} {focus}".strip()))
    queries.append(("recipient_or_subject",f"{focus} {year or ''}".strip()))
    queries.append(("presidential_collection",f"{name or 'presidential papers'} {focus} {year or ''}".strip()))
    if any(x in lead["title_or_excerpt"].lower() for x in ("pension","by command","regulation","war office","proclamation")):
        queries.append(("printed_ephemera",f"{focus} {year or ''} broadside".strip()))
    if any(x in lead["title_or_excerpt"].lower() for x in ("indian","treaty","frontier","militia","st. clair")):
        queries.append(("congressional_reprint",f"{focus} {year or ''} American State Papers".strip()))
    unique=[]
    seen=set()
    for kind,query in queries:
        query=re.sub(r"\s+"," ",query).strip()
        if query not in seen:
            unique.append({"lead_id":lead["lead_id"],"route":kind,"query":query,"loc_api_url":search_url(query),"nara_human_search_url":catalog_url(query),"state":"planned_not_searched"})
            seen.add(query)
    return unique


def score_result(lead, result):
    """Transparent candidate ranking; score is not document authentication."""
    hay=" ".join(str(result.get(x) or "") for x in ("title","description","date")).lower()
    tokens=distinctive(lead["title_or_excerpt"],8)
    score=sum(2 for x in tokens if x in hay)
    year=lead["year_hint_unverified"]
    if year and str(year) in hay:
        score+=3
    if lead["date_hint_unverified"] and lead["date_hint_unverified"] in hay:
        score+=5
    if result.get("image_url"):
        score+=1
    return score


def fetch_loc(routes, leads_by_id, cache, limit, delay):
    cache.mkdir(parents=True,exist_ok=True)
    matches=[]
    fetched=0
    failures=[]
    for route in routes:
        if fetched>=limit:
            break
        url=route["loc_api_url"]
        name=hashlib.sha256(url.encode()).hexdigest()+".json"
        path=cache/name
        try:
            if path.is_file():
                data=path.read_bytes()
                route["state"]="cached_response"
            else:
                request=urllib.request.Request(url,headers={"User-Agent":"ExecutiveOrdersResearch/Stage19 (public archival discovery)","Accept":"application/json"})
                with urllib.request.urlopen(request,timeout=20) as response:
                    if response.status!=200 or "json" not in (response.headers.get("Content-Type") or "").lower():
                        raise ValueError("non-JSON or non-200 response")
                    data=response.read(3_000_001)
                if len(data)>3_000_000:
                    raise ValueError("response exceeded 3 MB cap")
                json.loads(data)
                path.write_bytes(data)
                route["state"]="fetched_response"
                time.sleep(delay)
            payload=json.loads(data)
            if not isinstance(payload.get("results"),list):
                raise ValueError("LOC response missing results array")
            route["response_sha256"]=hashlib.sha256(data).hexdigest()
            route["response_cache_file"]=str(path)
            route["reported_total_results"]=payload.get("pagination",{}).get("of")
            for item in payload["results"]:
                result={"lead_id":route["lead_id"],"route":route["route"],"source":"loc_search_api","catalog_id":item.get("id") or item.get("url") or "","title":item.get("title") or "","date":item.get("date") or "","description":" ".join(item.get("description") or []) if isinstance(item.get("description"),list) else str(item.get("description") or ""),"url":item.get("id") or item.get("url") or "","result_state":"search_hit_not_authenticated","response_sha256":route["response_sha256"]}
                result["match_score_not_confidence"]=score_result(leads_by_id[route["lead_id"]],item)
                matches.append(result)
        except (urllib.error.URLError,TimeoutError,ValueError,json.JSONDecodeError) as error:
            route["state"]="fetch_error"
            route["error"]=str(error)[:240]
            failures.append({"url":url,"error":str(error)[:240]})
        fetched+=1
    return matches,failures


def write_csv(path, rows, fields):
    with path.open("w",encoding="utf-8",newline="") as stream:
        w=csv.DictWriter(stream,fieldnames=fields,extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()})


def make_html(leads,routes,matches,path):
    route_by={}
    for route in routes:
        route_by.setdefault(route["lead_id"],[]).append({k:route[k] for k in ("route","query","loc_api_url","nara_human_search_url","state")})
    match_by={}
    for match in matches:
        match_by.setdefault(match["lead_id"],[]).append(match)
    preview=[]
    for lead in leads[:250]:
        preview.append({**lead,"routes":route_by.get(lead["lead_id"],[]),"matches":match_by.get(lead["lead_id"],[])})
    payload=json.dumps(preview,ensure_ascii=False).replace("</","<\\/")
    page=r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Early order source ranger</title><style>body{font:15px/1.5 system-ui,sans-serif;background:#f6f8fa;color:#1b2a36;margin:0}header{background:#213b36;color:white;padding:22px 5vw}h1{font-size:24px;margin:0}main{max-width:1180px;margin:auto;padding:18px}input{font:inherit;padding:10px;width:min(100%,500px)}article{background:white;border:1px solid #d9e1df;border-radius:8px;margin:10px 0;padding:14px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f4;padding:9px}a{overflow-wrap:anywhere}.muted{color:#586c67}.warn{color:#82331d}</style><header><h1>Early-order source ranger</h1><div>Catalog routes and candidate hits only. Open the historical page and inspect identity, signer, and legal form.</div></header><main><p class="warn">No OCR lead or search result is admitted to the 14,972 working bibliography by this tool.</p><input id="search" placeholder="Find year, lead, subject…"><span id="count" class="muted"></span><section id="items"></section></main><script id="data" type="application/json">%%DATA%%</script><script>const data=JSON.parse(document.querySelector('#data').textContent),$=id=>document.getElementById(id);function e(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}function link(u,label){return /^https:\/\//.test(u)?'<a href="'+e(u)+'" target="_blank" rel="noopener noreferrer">'+e(label)+'</a>':e(label)}function draw(){let q=$('search').value.toLowerCase(),x=data.filter(r=>(r.lead_id+' '+r.title_or_excerpt+' '+r.date_hint_unverified).toLowerCase().includes(q));$('count').textContent=x.length+' / '+data.length+' displayed leads';$('items').innerHTML=x.slice(0,100).map(r=>'<article><b>'+e(r.lead_id)+'</b> • '+e(r.date_hint_unverified||'date uncertain')+' • '+e(r.inclusion_state)+'<p>'+e(r.title_or_excerpt.slice(0,550))+'</p><div>'+link(r.lord_scan_url,'Lord source page')+' '+link(r.known_primary_source_url,'Known primary representation')+'</div><details><summary>'+r.routes.length+' search routes; '+r.matches.length+' candidate hits</summary><ul>'+r.routes.map(t=>'<li>'+e(t.route)+' — '+link(t.loc_api_url,'LOC')+' / '+link(t.nara_human_search_url,'NARA catalog')+' — '+e(t.state)+'</li>').join('')+'</ul><pre>'+e(JSON.stringify(r.matches,null,2))+'</pre></details></article>').join('')} $('search').oninput=draw;draw();</script></html>'''
    path.write_text(page.replace("%%DATA%%",payload),encoding="utf-8")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--fetch",action="store_true")
    p.add_argument("--max-requests",type=int,default=0)
    p.add_argument("--delay-seconds",type=float,default=1.5)
    args=p.parse_args()
    if args.max_requests<0 or args.delay_seconds<0:
        raise ValueError("request cap and delay must be nonnegative")
    args.out.mkdir(parents=True,exist_ok=True)
    leads=load_leads()
    # Source-located leads, then uncatalogued 18c survey cells, then Lord OCR.
    rank={"stage18_curated_candidate":0,"systematic_18c_survey":1,"lord_ocr_unverified":2}
    leads.sort(key=lambda r:(rank[r["lead_origin"]],r["year_hint_unverified"] or 9999,r["lead_id"]))
    routes=[route for lead in leads for route in routes_for(lead)]
    lead_by={lead["lead_id"]:lead for lead in leads}
    matches=[]
    for lead in leads:
        if lead["known_primary_source_url"]:
            matches.append({"lead_id":lead["lead_id"],"route":"curated_source","source":"stage18_direct_source_pilot","catalog_id":"","title":lead["title_or_excerpt"],"date":lead["date_hint_unverified"],"description":lead["known_source_representation"],"url":lead["known_primary_source_url"],"result_state":"primary_representation_located_identity_not_admitted","response_sha256":"","match_score_not_confidence":"not_scored"})
    failures=[]
    if args.fetch and args.max_requests:
        extra,failures=fetch_loc(routes,lead_by,args.out/"loc_api_cache",args.max_requests,args.delay_seconds)
        matches.extend(extra)
    write_csv(args.out/"RANGER_LEADS.csv",leads,list(leads[0]))
    write_csv(args.out/"RANGER_ROUTES.csv",routes,["lead_id","route","query","loc_api_url","nara_human_search_url","state","response_sha256","reported_total_results","error"])
    write_csv(args.out/"CANDIDATE_MATCHES.csv",matches,["lead_id","route","source","catalog_id","title","date","description","url","result_state","response_sha256","match_score_not_confidence"])
    make_html(leads,routes,matches,args.out/"RANGER_WORKBENCH.html")
    summary={"schema":"eo-early-ranger/v1","lord_source_sha256":digest(LORD),"stage18_candidate_sha256":digest(SEEDS),"lord_ocr_leads":1023,"curated_uncounted_leads":6,"systematic_1789_1800_survey_cells":12,"eighteenth_century_inherited_leads":sum(r["year_hint_unverified"] and r["year_hint_unverified"]<1800 and r["lead_origin"]!="systematic_18c_survey" for r in leads),"total_leads":len(leads),"search_routes_planned":len(routes),"loc_api_routes_attempted":sum(r["state"]!="planned_not_searched" for r in routes),"loc_api_routes_succeeded":sum(r["state"] in ("cached_response","fetched_response") for r in routes),"loc_api_failures":failures,"curated_primary_representations_located":sum(bool(r["known_primary_source_url"]) for r in leads),"new_included_executive_orders":0,"interpretation":"Search routes and candidate matches are discovery leads. The 12 survey cells assert no document exists. OCR dates are unverified. A LOC hit can be a later transcription or broadside rather than an original signed presidential directive; no result changes the census automatically.","api_docs":"https://www.loc.gov/apis/json-and-yaml/requests/parameters/","nara_api_key_requirement":"https://github.com/usnationalarchives/Catalog-API/blob/master/README.md"}
    (args.out/"RANGER_SUMMARY.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"leads":len(leads),"routes":len(routes),"api_successes":summary["loc_api_routes_succeeded"],"candidate_matches":len(matches)}))


if __name__=="__main__":
    main()

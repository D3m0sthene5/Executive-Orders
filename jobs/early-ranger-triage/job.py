"""Early-order triage: separate presidential-term manuscript leads from noise.

Inputs: 65 verified-custody LOC catalog links, the 73-year historic gap grid,
and Stage 18 earlier candidate documents. All classification is research triage,
NOT presidential attribution, EO census admission or legal effect.
"""
import collections
import csv
import json
import os
import re
from pathlib import Path

ROOT=Path(os.environ["REPO_ROOT"])
OUT=Path(os.environ["OUTPUT_DIR"])
SOURCE=ROOT/"jobs/early-ranger-reparse/output/LOC_MANUSCRIPT_CANDIDATES.csv"
GRID=ROOT/"research/stage20/output/ARCHIVAL_COVERAGE_GRID.csv"
CURATED=ROOT/"research/stage18/data/EARLY_SOURCE_CANDIDATES.csv"

PRESIDENTS=[
 ("George Washington","1789-04-30","1797-03-04"),
 ("John Adams","1797-03-04","1801-03-04"),
 ("Thomas Jefferson","1801-03-04","1809-03-04"),
 ("James Madison","1809-03-04","1817-03-04"),
 ("James Monroe","1817-03-04","1825-03-04"),
 ("John Quincy Adams","1825-03-04","1829-03-04"),
 ("Andrew Jackson","1829-03-04","1837-03-04"),
 ("Martin Van Buren","1837-03-04","1841-03-04"),
 ("William Henry Harrison","1841-03-04","1841-04-04"),
 ("John Tyler","1841-04-04","1845-03-04"),
 ("James K. Polk","1845-03-04","1849-03-04"),
 ("Zachary Taylor","1849-03-04","1850-07-09"),
 ("Millard Fillmore","1850-07-09","1853-03-04"),
 ("Franklin Pierce","1853-03-04","1857-03-04"),
 ("James Buchanan","1857-03-04","1861-03-04"),
]
ACTION=re.compile(r"\b(instruct(?:ion|ions|ed)?|order|warrant|commission|directive|regulations?|military|militia)\b",re.I)

def read(path):
    with path.open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def date_bounds(raw):
    m=re.search(r"\b(17\d\d|18\d\d)-(\d\d)-(\d\d)\b",raw or "")
    if m:return m.group(0),"exact"
    m=re.search(r"\b(17\d\d|18\d\d)\b",raw or "")
    if m:return m.group(1),"year_only"
    return "","unresolved"

def presidency_at(iso):
    if len(iso)==10:
        return next((name for name,begin,end in PRESIDENTS if begin<=iso<end),None)
    if len(iso)==4:
        y=int(iso)
        return [name for name,start,end in PRESIDENTS if int(start[:4])<=y<=int(end[:4])]
    return None

def attribution(title,iso):
    # Historic collections have material written by many people; a collection
    # name alone never establishes sender. Only titles starting with the
    # actual president's personal name can be a plausible presidential
    # direction after matching the issue date to a term.
    for name,start,end in PRESIDENTS:
        if not title.startswith(name):continue
        if len(iso)==10 and start<=iso<end:
            return name,"name_in_title_and_date_within_term_NOT_AUTHENTICATED"
        if len(iso)==4 and int(start[:4])<=int(iso)<=int(end[:4]):
            return name,"year_overlap_requires_exact_date_NOT_AUTHENTICATED"
        if iso:
            return name,"person_named_but_OUTSIDE_their_presidency"
        return name,"person_named_no_valid_issuance_date"
    return "","issuer_of_item_NOT_ESTABLISHED"

def main():
    items=read(SOURCE);grid=read(GRID);curated=read(CURATED)
    if len(items)!=65 or len(grid)!=73 or len(curated)!=6:
        raise ValueError("Unexpected frozen early source input count")
    year_map={r["year"]:r for r in grid}
    seen=set();rows=[]
    for c in items:
        url=c["loc_item_https"]
        if url in seen:raise ValueError("Duplicate catalog item")
        seen.add(url)
        iso,precision=date_bounds(c["catalog_date"])
        y=iso[:4] if iso else ""
        title=c["title"]
        issuer,capacity=attribution(title,iso)
        action=bool(ACTION.search(title))
        previous_gap=(y in year_map and
             year_map[y]["year_risk"]=="NO_INHERITED_LEADS_MEANS_UNKNOWN_NOT_ZERO")
        if capacity.startswith("person_named_but_OUTSIDE"):
            lane="historical_nonpresidential_context_or_by_command_check"
        elif issuer and "term" in capacity and action:
            lane="priority_presidential_period_directive_wording"
        elif issuer and "term" in capacity:
            lane="presidential_correspondence_needs_full_page"
        elif action:
            lane="directive_wording_but_issuer_unresolved"
        else:
            lane="generic_manuscript_background"
        score=(20 if lane.startswith("priority") else
              11 if lane=="presidential_correspondence_needs_full_page" else
              5 if lane=="directive_wording_but_issuer_unresolved" else 0)
        if previous_gap:score+=5
        if precision=="exact":score+=2
        rows.append({
            "catalog_item_url":url,
            "date_as_indexed":c["catalog_date"],
            "year_hint":y,
            "date_precision_not_legally_verified":precision,
            "title_as_indexed":title,
            "possible_issuer_in_title":issuer,
            "presidential_term_screen_ONLY":capacity,
            "directive_wording_in_title":int(action),
            "no_Lord_lead_for_year_in_prior_grid":int(previous_gap),
            "triage_lane_NOT_identification":lane,
            "review_priority_NOT_probability":score,
            "source_response_sha256":c["response_sha256"],
            "original_item_bytes_checked":0,
            "eo_inclusion_judgment":"unknown",
            "next_action":("Read original manuscript and its contemporaneous context; "
                           "identify issuer capacity, recipient, operative instructions "
                           "and duplicates before historical inclusion")
        })
    rows.sort(key=lambda r:(-r["review_priority_NOT_probability"],r["catalog_item_url"]))
    out=OUT
    out.mkdir(parents=True,exist_ok=True)
    with (out/"PRIORITIZED_PRESIDENTIAL_PERIOD_CANDIDATES.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n")
        w.writeheader();w.writerows(rows)
    gap_years=sorted({r["year_hint"] for r in rows if r["no_Lord_lead_for_year_in_prior_grid"]=="1" or r["no_Lord_lead_for_year_in_prior_grid"]==1})
    # Related primary representations may appear in more than one series;
    # they must not become multiple alleged executive orders by automated math.
    same_day=collections.defaultdict(list)
    for r in rows:
        if r["date_precision_not_legally_verified"]!="exact":continue
        if not r["possible_issuer_in_title"]:continue
        key=(r["date_as_indexed"],r["possible_issuer_in_title"])
        same_day[key].append(r["catalog_item_url"])
    multi={day+"|"+author:ids for (day,author),ids in same_day.items() if len(ids)>1}
    summary={
        "schema":"eo-early-ranger-presidency-capacity-triage/v1",
        "loc_item_candidates":len(rows),
        "year_hints_1789_1861":sum(
            bool(r["year_hint"]) and 1789<=int(r["year_hint"])<=1861
            for r in rows),
        "catalog_items_dated_in_years_previously_without_inherited_specific_leads":
            sum(r["no_Lord_lead_for_year_in_prior_grid"] for r in rows),
        "distinct_previous_gap_years_with_catalog_leads":len(gap_years),
        "gap_years_with_leads_not_equivalent_to_orders":gap_years,
        "high_priority_presidential_period_titles_with_directive_keywords":
            sum(r["triage_lane_NOT_identification"]=="priority_presidential_period_directive_wording"
                for r in rows),
        "within_presidency_correspondence_non_directive_titles":
            sum(r["triage_lane_NOT_identification"]=="presidential_correspondence_needs_full_page"
                for r in rows),
        "historical_named_correspondents_outside_own_presidency":
            sum(r["triage_lane_NOT_identification"]=="historical_nonpresidential_context_or_by_command_check"
                for r in rows),
        "possible_same_date_author_matched_item_groups":len(multi),
        "new_authenticated_executive_orders":0,
        "legal_effects_adjudicated":0,
        "caution":"Title/dates used only for ordering source inspection; original pages and attribution have not been authenticated."
    }
    (out/"TRIAGE_SUMMARY.json").write_text(json.dumps(summary,indent=2)+"\n")
    (out/"SAME_DAY_POSSIBLE_DUPLICATE_IMAGES.json").write_text(
        json.dumps(multi,indent=2)+"\n")
    lines=["# 1789–1861: capacity-aware archival discovery triage","",
           f"**{len(rows)}** Library of Congress catalog items examined as indexed records. "
           f"**{len(gap_years)}** previously empty Lord-index years now have *some "
           "catalog item leads*, not proven EOs.","",
           "The screen explicitly demotes a famous person's **pre-presidency or "
           "post-presidency letters**. Its chronology is a research filter, not a "
           "conclusive document identity test.","",
           "## First original pages to inspect",""]
    for r in rows:
        if r["triage_lane_NOT_identification"] in (
                "priority_presidential_period_directive_wording",
                "presidential_correspondence_needs_full_page"):
            lines.append(f"- [{r['title_as_indexed']}]({r['catalog_item_url']}) "
                         f"— {r['date_as_indexed']}; "
                         f"{r['triage_lane_NOT_identification']}")
    lines += ["","## Checks that cannot be skipped","",
              "Compare item images/transcripts and provenance to identify a presidential "
              "instruction as opposed to a presidential paper, secretary's independent "
              "direction, nomination or later editorial copy. Match duplicate representations "
              "before admitting an identity. Keep statutory authority, publication and "
              "operative first cessation separate.", ""]
    (out/"CAPACITY_TRIAGE_REPORT.md").write_text("\n".join(lines))
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()

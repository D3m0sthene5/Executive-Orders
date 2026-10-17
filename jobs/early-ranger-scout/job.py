"""Early-order ranger: bounded live manuscript/catalog expedition, 1789–1861.

Uses Stage 20 year-gap inventory and documented LOC presidential manuscript
collections. Searches the public LOC JSON service and Internet Archive metadata.
Preserves response bytes by hash, exact query routes, results and failures.
No catalog result is authenticated as a presidential executive order.

This is a *discovery* job. It does not infer legal status, amend census, or
pretend a query failure establishes that no document exists.
"""
from __future__ import annotations

import collections
import csv
import gzip
import hashlib
import io
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ["REPO_ROOT"])
OUT = Path(os.environ["OUTPUT_DIR"])
CACHE = OUT / "response_cache"
GRID = ROOT / "research/stage20/output/ARCHIVAL_COVERAGE_GRID.csv"
CURATED = ROOT / "research/stage18/data/EARLY_SOURCE_CANDIDATES.csv"
LEGAL_CUTOFF = "2026-10-14"
RESULTS_PER_QUERY = 8
RESPONSE_MAX_BYTES = 2_000_000
MAX_REQUESTS = 65

# These are collection discovery hints, not claims that the collection contains
# a particular presidential directive or that a signer can be inferred by year.
COLLECTIONS = [
    ("washington", "george-washington-papers", 1789, 1797),
    ("jefferson", "thomas-jefferson-papers", 1801, 1809),
    ("madison", "james-madison-papers", 1809, 1817),
    ("monroe", "james-monroe-papers", 1817, 1825),
    ("jackson", "andrew-jackson-papers", 1829, 1837),
    ("van-buren", "martin-van-buren-papers", 1837, 1841),
    ("harrison", "william-henry-harrison-papers", 1841, 1841),
    ("tyler", "john-tyler-papers", 1841, 1845),
    ("polk", "james-k-polk-papers", 1845, 1849),
    ("taylor", "zachary-taylor-papers", 1849, 1850),
    ("fillmore", "millard-fillmore-papers", 1850, 1853),
    ("pierce", "franklin-pierce-papers", 1853, 1857),
    ("buchanan", "james-buchanan-papers", 1857, 1861),
]
COLLECTION_QUERIES = ["instructions", "secretary of war", "militia"]
# Historically documented digital source entry points, independently locatable
# before this job; individual items remain unverified as executive orders.
ANCHORS = [
    {
        "anchor_id": "LOC-GW-LETTERBOOK-17",
        "title": "Washington letterbook 17 (May 1789 – September 1791)",
        "url": "https://www.loc.gov/resource/mgw2.017/?st=gallery",
        "kind": "digitized_1789_1791_presidential_correspondence_collection",
        "research_value": "Inspect multiple outgoing departmental instructions and neighboring leaves, especially missing 1791 directives.",
    },
    {
        "anchor_id": "LOC-GW-LETTERBOOK-23",
        "title": "Washington letterbook 23 (August 1790 – March 1793)",
        "url": "https://www.loc.gov/resource/mgw2.023/?st=gallery",
        "kind": "digitized_1790_1793_presidential_correspondence_collection",
        "research_value": "Inspect contemporaneous correspondence and neighboring signed-command copies; distinct same-date letters may exist.",
    },
    {
        "anchor_id": "LOC-GW-1791-LIQUOR",
        "title": "George Washington, March 15, 1791, State Liquor Inspectors",
        "url": "https://www.loc.gov/resource/mgw2.033/",
        "kind": "digitized_historical_item_to_authenticate",
        "research_value": "Potential underindexed 1791 Treasury regulatory/implementation directive; verify page text, recipient, signer, scope and inclusion.",
    },
    {
        "anchor_id": "LOC-MVB-MESSAGES",
        "title": "Martin Van Buren Papers Series 4: Messages, 1837–1838",
        "url": "https://www.loc.gov/item/mss438280140/",
        "kind": "digitized_presidential_messages_manuscript_series",
        "research_value": "1837–1838 contemporaneous manuscript lead source; distinguish messages to Congress from executive directives.",
    },
]
USER_AGENT = "EOHistoricalRanger/1.0 (noncommercial archival metadata research)"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(params):
    return urllib.parse.urlencode(params)


def loc_url(slug=None, query="", year=None):
    endpoint = (f"https://www.loc.gov/collections/{slug}/" if slug
                else "https://www.loc.gov/search/")
    params = [("fo", "json"), ("at", "results,pagination"),
              ("c", str(RESULTS_PER_QUERY)), ("sp", "1")]
    if query:
        params.append(("q", query if year is None else f"{query} {year}"))
    return endpoint + "?" + encode(params)


def ia_url(query):
    params = [
        ("q", query), ("fl[]", "identifier"), ("fl[]", "title"),
        ("fl[]", "date"), ("fl[]", "creator"), ("rows", "8"),
        ("page", "1"), ("output", "json"),
    ]
    return "https://archive.org/advancedsearch.php?" + encode(params)


def read_grid():
    with GRID.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def query_plan():
    grid = read_grid()
    if len(grid) != 73:
        raise ValueError("Stage20 1789–1861 year grid has drifted")
    missing = [int(x["year"]) for x in grid
               if x["year_risk"] == "NO_INHERITED_LEADS_MEANS_UNKNOWN_NOT_ZERO"]
    if len(missing) != 43:
        raise ValueError("Unexpected stage20 unindexed years")
    plans = []
    # Query *inside* digital presidential collections. Searching by collection
    # and role gives a reusable set of pages and recipients; year-only Google
    # search misses archival originals filed under departmental recipients.
    for president, slug, first, last in COLLECTIONS:
        for q in COLLECTION_QUERIES[:2]:
            plans.append({
                "request_id": f"LOC-COLLECTION-{president}-{q.replace(' ','-')}",
                "provider": "loc", "route": "presidential_manuscript_collection",
                "target_year": "", "collection": slug,
                "q": q, "url": loc_url(slug, q),
                "year_range": f"{first}-{last}",
            })
    # Each sparse-year route is a separate targeted discovery request; avoid
    # treating the absence of inherited OCR leads as absence of manuscripts.
    # 18 well-distributed gap years + 6 role-specific first/last years provide
    # the initial yield/latency test before increasing a provider's workload.
    stride = max(1, len(missing) // 18)
    chosen = missing[::stride][:18]
    for year in chosen:
        q = "presidential directions secretary"
        plans.append({
            "request_id": f"LOC-UNKNOWN-{year}",
            "provider": "loc", "route": "year_gap_search",
            "target_year": str(year), "collection": "",
            "q": q, "url": loc_url(None, q, year),
            "year_range": str(year),
        })
    for year in (1789, 1791, 1806, 1828, 1837, 1850, 1860):
        q = "presidential instructions"
        plans.append({
            "request_id": f"LOC-ACTOR-{year}",
            "provider": "loc", "route": "focused_presidential_instructions",
            "target_year": str(year), "collection": "",
            "q": q, "url": loc_url(None, q, year),
            "year_range": str(year),
        })
    for k, query in enumerate([
        'title:("Messages and Papers of the Presidents") AND mediatype:texts',
        'title:("Executive orders") AND mediatype:texts',
        'title:("Washington papers") AND mediatype:texts',
        'title:("Presidential correspondence") AND mediatype:texts',
        'title:("American state papers") AND mediatype:texts',
    ]):
        plans.append({
            "request_id": f"IA-BOOKS-{k+1:02}",
            "provider": "internet_archive", "route": "digitized_source_collection",
            "target_year": "", "collection": "public_bibliography",
            "q": query, "url": ia_url(query),
            "year_range": "1789-1861",
        })
    if len(plans) > MAX_REQUESTS:
        raise ValueError("Unexpected unbounded early-source query plan")
    if len({x["request_id"] for x in plans}) != len(plans):
        raise ValueError("Duplicate query route identities")
    return grid, missing, plans


def get_json(url, provider):
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=12) as response:
        final = urllib.parse.urlsplit(response.geturl())
        allow = ({"www.loc.gov", "loc.gov"} if provider == "loc"
                 else {"archive.org", "www.archive.org"})
        if final.scheme != "https" or final.hostname not in allow:
            raise ValueError("Provider redirected outside approved archive")
        mime = (response.headers.get("Content-Type") or "").lower()
        if "json" not in mime:
            raise ValueError("Provider returned non-JSON MIME: " + mime[:80])
        body = response.read(RESPONSE_MAX_BYTES+1)
        if len(body) > RESPONSE_MAX_BYTES:
            raise ValueError("JSON response over 2 MB bound")
    data = json.loads(body)
    return body, data


def single_text(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        if isinstance(value, list):
            return " ".join(str(x) for x in value if x is not None)[:600]
        return json.dumps(value, ensure_ascii=False, sort_keys=True)[:600]
    return str(value)[:600]


def catalog_candidates(route, data, response_sha):
    provider = route["provider"]
    if provider == "loc":
        results = data.get("results")
        if not isinstance(results, list):
            raise ValueError("LOC results array missing")
    else:
        results = data.get("response", {}).get("docs")
        if not isinstance(results, list):
            raise ValueError("IA response.docs list missing")
    candidates = []
    for item in results:
        if not isinstance(item, dict):
            continue
        if provider == "loc":
            link = str(item.get("id") or item.get("url") or "")
            title = single_text(item.get("title"))
            raw_date = single_text(item.get("date"))
            excerpt = single_text(item.get("description"))
            contributors = single_text(item.get("contributor"))
        else:
            identifier = item.get("identifier")
            if not isinstance(identifier, str) or not identifier:
                continue
            link = "https://archive.org/details/" + urllib.parse.quote(identifier)
            title = single_text(item.get("title"))
            raw_date = single_text(item.get("date"))
            excerpt = ""
            contributors = single_text(item.get("creator"))
        # Reject off-domain and non-HTTPS URLs rather than embedding a phishing link
        parsed = urllib.parse.urlsplit(link)
        allowed = ({"www.loc.gov", "loc.gov"} if provider=="loc"
                   else {"archive.org", "www.archive.org"})
        if parsed.scheme!="https" or parsed.hostname not in allowed:
            continue
        query = route["q"].lower()
        hay = " ".join([title,raw_date,excerpt,contributors]).lower()
        event_terms = ("instructions", "order", "militia", "directive",
                       "commission", "secretary", "regulation", "treasury")
        score = sum(bool(re.search(r"\b"+re.escape(w)+r"\b",hay))
                    for w in event_terms)
        if route["target_year"] and route["target_year"] in raw_date:
            score += 3
        if route["collection"] and route["provider"] == "loc":
            score += 1
        if any(w in title.lower() for w in ("order", "instructions", "commission")):
            score += 2
        candidates.append({
            "provider": provider,
            "candidate_catalog_url": link,
            "catalog_title": title,
            "catalog_date_as_indexed": raw_date,
            "catalog_description_preview": excerpt,
            "catalog_contributors": contributors,
            "search_route_ids": [route["request_id"]],
            "catalog_relevance_score_NOT_authentication": score,
            "source_response_sha256s": [response_sha],
            "identity_and_presidential_attribution": "UNASSESSED",
            "operative_clause_evidence": "UNASSESSED",
            "included_historical_EO": "NO_DECISION",
        })
    return candidates, len(results)


def write_csv(path, rows, headers):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    grid, missing, plans = query_plan()
    attempts, candidates = [], {}
    providers = collections.Counter()
    errors = collections.Counter()
    consecutive_failures = collections.defaultdict(int)
    disabled_providers = set()
    for i, route in enumerate(plans):
        provider = route["provider"]
        attempt = {
            **route, "status": "not_attempted", "retrieved_at_utc": "",
            "response_sha256": "", "matched_catalog_rows": 0, "error": "",
            "raw_response_cache": "", "http_status": "",
        }
        if provider in disabled_providers:
            attempt["status"] = "skipped_provider_unavailable"
            attempts.append(attempt)
            continue
        print(f"[{i+1}/{len(plans)}] {route['request_id']}: {route['url']}", flush=True)
        try:
            body, payload = get_json(route["url"], provider)
            digest = sha(body)
            hits, count = catalog_candidates(route, payload, digest)
            target = CACHE / f"{digest}.json.gz"
            if not target.exists():
                with target.open("wb") as stream:
                    with gzip.GzipFile(fileobj=stream, mode="wb", mtime=0) as archive:
                        archive.write(body)
            attempt.update({
                "status": "json_response_preserved_NOT_authenticated",
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "response_sha256": digest,
                "raw_response_cache": str(target.relative_to(OUT)),
                "matched_catalog_rows": count,
            })
            providers[provider] += 1
            consecutive_failures[provider] = 0
            for candidate in hits:
                key = (candidate["provider"], candidate["candidate_catalog_url"])
                if key in candidates:
                    prior = candidates[key]
                    prior["search_route_ids"].extend(candidate["search_route_ids"])
                    prior["source_response_sha256s"].extend(candidate["source_response_sha256s"])
                    prior["catalog_relevance_score_NOT_authentication"] = max(
                        prior["catalog_relevance_score_NOT_authentication"],
                        candidate["catalog_relevance_score_NOT_authentication"])
                else:
                    candidates[key] = candidate
        except Exception as exc:
            attempt["status"] = "request_failed_NO_NEGATIVE_CENSUS_INFERENCE"
            attempt["error"] = (type(exc).__name__ + ": " + str(exc))[:500]
            errors[provider] += 1
            consecutive_failures[provider] += 1
            # Stop hammering a blocked archive; report the rest as unsearched.
            if consecutive_failures[provider] >= 3:
                disabled_providers.add(provider)
        attempts.append(attempt)
        time.sleep(0.65)
    enriched = []
    for cand in candidates.values():
        cand["search_route_ids"] = sorted(set(cand["search_route_ids"]))
        cand["source_response_sha256s"] = sorted(set(cand["source_response_sha256s"]))
        enriched.append({**cand,
            "search_route_ids": " | ".join(cand["search_route_ids"]),
            "source_response_sha256s": " | ".join(cand["source_response_sha256s"])})
    enriched.sort(key=lambda c:(-c["catalog_relevance_score_NOT_authentication"],
                                 c["provider"],c["candidate_catalog_url"]))
    write_csv(OUT/"LIVE_CATALOG_CANDIDATES.csv",enriched,
        ["provider","candidate_catalog_url","catalog_title","catalog_date_as_indexed",
         "catalog_description_preview","catalog_contributors","search_route_ids",
         "catalog_relevance_score_NOT_authentication","source_response_sha256s",
         "identity_and_presidential_attribution","operative_clause_evidence",
         "included_historical_EO"])
    with (OUT/"LIVE_SEARCH_ATTEMPTS.jsonl").open("w",encoding="utf-8") as stream:
        for r in attempts:
            stream.write(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n")
    (OUT/"DOCUMENTED_COLLECTION_ANCHORS.json").write_text(
        json.dumps(ANCHORS,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    searched = [a for a in attempts if a["status"].startswith("json_response")]
    report = {
        "schema": "eo-early-ranger-live-scout/v1",
        "executed_on": datetime.now(timezone.utc).isoformat(),
        "legal_cutoff": LEGAL_CUTOFF,
        "stage20_years_1789_to_1861": len(grid),
        "inherited_no_specific_candidate_years": len(missing),
        "live_query_routes_prepared": len(plans),
        "live_http_json_responses_preserved": len(searched),
        "provider_successes": dict(providers),
        "provider_failures": dict(errors),
        "request_failures": sum(x["status"] == "request_failed_NO_NEGATIVE_CENSUS_INFERENCE"
                                for x in attempts),
        "routes_skipped_due_to_provider_failure": sum(
            x["status"] == "skipped_provider_unavailable" for x in attempts),
        "raw_json_response_files_with_sha256": len(list(CACHE.glob("*.json.gz"))),
        "raw_catalog_rows_seen_sum_not_distinct": sum(
            x["matched_catalog_rows"] for x in searched),
        "distinct_catalog_item_links_from_successful_queries": len(enriched),
        "documented_external_collection_or_item_anchors": len(ANCHORS),
        "candidate_legal_identity_verified": 0,
        "newly_authenticated_pre_1862_executive_orders": 0,
        "no_results_does_not_prove_absence": True,
        "interpretation": ("Candidate results may be editions or unrelated manuscript "
            "records. No EO number, legal cause, date, inclusion or absence is "
            "inferred from title, search failure, or OCR. Source responses are "
            "preserved for item-level verification."),
    }
    (OUT/"SCOUT_SUMMARY.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
        encoding="utf-8")
    lines=[
        "# Live archival scout: manuscript collection and historical-gap reconnaissance",
        "",f"Requests prepared: **{len(plans)}**; successful JSON responses: **{len(searched)}**; "
        f"distinct catalog item links: **{len(enriched)}**.",
        f"Archive errors: **{report['request_failures']}**; skipped after provider "
        f"blocking: **{report['routes_skipped_due_to_provider_failure']}**.",
        "",
        "Every entry below is a **catalog discovery lead**, not a verified "
        "presidential order. The 1789–1861 source census remains open.",
        "",
        "## Highest-priority returned catalog candidates", "",
    ]
    for c in enriched[:40]:
        lines.append(f"- [{c['catalog_title'][:145]}]({c['candidate_catalog_url']}) "
                     f"— {c['catalog_date_as_indexed']} ({c['provider']}; "
                     f"retrieval relevance {c['catalog_relevance_score_NOT_authentication']}).")
    if not enriched:
        lines += ["No JSON catalog candidates retrieved in this run. The curated "
                   "manuscript collections below remain usable as online leads.", ""]
    lines += ["", "## Documented source collection/item anchors", ""]
    for r in ANCHORS:
        lines.append(f"- [{r['title']}]({r['url']}): {r['research_value']}")
    lines += ["", "## Source limits", "",
              "The LOC metadata service can rate-limit or time out. IA can return "
              "digitized modern editions. A hit requires image, exact clause, "
              "presidential authority, date and census-identity review; a miss "
              "never proves archival absence. See LIVE_SEARCH_ATTEMPTS.jsonl "
              "and the SHA-256-addressed response_cache for reconstruction.", ""]
    (OUT/"SCOUT_REPORT.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)


if __name__ == "__main__":
    main()

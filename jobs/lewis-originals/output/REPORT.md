# Lewis: originals for transcription-only orders

Generated 2026-10-21T20:31:32Z. Leads and verified file facts; no count or grade changes.

**Scope: 4723 orders** (clark_identified 37, clark_identified_not_in_universe 42, transcription_only 4644).

## Where they stand on the ladder

| Route | Status | Orders |
|---|---|---:|
| proquest_phrase_search | manual_lead | 1960 |
| gpo_bound_volumes | in_volume_range_not_found | 1253 |
| ofr_hoover_compilation | in_volume_range_not_found | 474 |
| federal_register | in_ofr_catalog_no_citation | 431 |
| federal_register | fetch_request_proposed | 266 |
| federal_register | fr_era_not_in_ofr_catalog | 215 |
| proquest_local | file_verified_pages_unchecked | 114 |
| proquest_supplied_link | awaiting_acquisition | 10 |

## ProQuest folder

2750 PDF files (2750 unique by SHA-256) cover 2750 orders; 114 of them are in Lewis's scope and 2636 belong to orders outside it (Clark's no-text orders, mostly). 2440 text layers pass the quality screen (handwritten originals give noise and are excluded). The supplied link list has 2765 links, 124 for orders in this scope.

## Proposed fetch requests

266 requests for the source-ladder job in `PROPOSED_FETCH_REQUESTS.jsonl` (validated with the source-ladder request contract: True). To enqueue them: `python jobs/source-ladder/request_contract.py enqueue --input jobs/lewis-originals/output/PROPOSED_FETCH_REQUESTS.jsonl --queue research/readiness/FETCH_QUEUE.jsonl`.

## Next actions by owner

| Owner | Orders |
|---|---:|
| agent_check | 2487 |
| owner | 1970 |
| machine_job | 266 |

## First twenty rows

| Order | Date | Route | Status | Next action |
|---|---|---|---|---|
| EO:1 | 1862-02-14 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:2 | 1862-02-27 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:3 | 1865-04-29 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:4 | 1865-05-09 | proquest_local | file_verified_pages_unchecked | Compare the PDF pages with the transcription; owner decides the custody grade |
| EO:5 | 1866-04-13 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:6 | 1868-07-20 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:8 | 1872-04-16 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:8-1 | 1873-03-14 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:9 | 1873-01-17 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:9-2 | 1873-01-28 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:11 | 1873-08-05 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:13 | 1874-03-09 | proquest_local | file_verified_pages_unchecked | Compare the PDF pages with the transcription; owner decides the custody grade |
| EO:16 | 1874-05-29 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:17 | 1874-08-31 | proquest_local | file_verified_pages_unchecked | Compare the PDF pages with the transcription; owner decides the custody grade |
| EO:18 | 1875-07-31 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:19 | 1875-11-22 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:20 | 1876-08-21 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:21 | 1881 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:22 | 1884-04-09 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:23-1 | 1885 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |

## Web search (online stage)

28 of 4723 targets advanced this run (4695 never searched yet); 268 of 500 requests used. 422 hits on file, 3 pages confirmed to name the order (1 orders): `WEB_LEADS.csv`. State in `WEB_STATE.json` carries forward; nothing is marked exhausted by the machine.

| Engine | Status |
|---|---|
| bing_api | needs_key |
| bing_rss | blocked_by_robots_txt |
| brave_api | needs_key |
| brave_html | blocked_by_robots_txt |
| duckduckgo_html | error |
| duckduckgo_lite | error |
| federal_register_api | ok |
| google_books | http_429 |
| google_cse | needs_key |
| govinfo_search_page | ok |
| hathitrust_catalog | blocked_by_robots_txt |
| internet_archive | ok |
| loc_books | ok |
| loc_manuscripts | ok |
| loc_newspapers | ok |
| marginalia | error |
| mojeek_html | blocked_by_robots_txt |
| nara_catalog | needs_key |
| presidency_project | ok |
| serpapi_google | needs_key |
| wikipedia_search | blocked_by_robots_txt |
| wikisource_search | blocked_by_robots_txt |
| yandex_html | blocked_by_robots_txt |

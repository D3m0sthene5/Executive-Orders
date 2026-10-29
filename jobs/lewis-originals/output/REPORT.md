# Lewis: originals for transcription-only orders

Generated 2026-10-29T07:26:45Z. Leads and verified file facts; no count or grade changes.

**Scope: 5306 orders** (clark_identified 13, clark_identified_not_in_universe 42, transcription_only 5251).

## Where they stand on the ladder

| Route | Status | Orders |
|---|---|---:|
| proquest_phrase_search | manual_lead | 2663 |
| gpo_bound_volumes | in_volume_range_not_found | 1188 |
| ofr_hoover_compilation | in_volume_range_not_found | 474 |
| federal_register | in_ofr_catalog_no_citation | 431 |
| federal_register | fetch_request_proposed | 265 |
| federal_register | fr_era_not_in_ofr_catalog | 185 |
| proquest_local | pinakes_file_record_pages_unchecked | 98 |
| proquest_supplied_link | awaiting_acquisition | 2 |

## ProQuest folder

2750 PDF files (2750 unique by SHA-256) cover 2750 orders; 98 of them are in Lewis's scope and 2652 belong to orders outside it (Clark's no-text orders, mostly). 2440 text layers pass the quality screen (handwritten originals give noise and are excluded). The supplied link list has 2765 links, 100 for orders in this scope.

Authority: pinakes-proquest-ingest. PDF signature results are not reported for 2750 inventory records; missing values are unknown, not verification failures or successful checks. Pinakes order records are reused without rereading PDFs or duplicating its fragments.

## Proposed fetch requests

265 requests for the source-ladder job in `PROPOSED_FETCH_REQUESTS.jsonl` (validated with the source-ladder request contract: True). To enqueue them: `python jobs/source-ladder/request_contract.py enqueue --input jobs/lewis-originals/output/PROPOSED_FETCH_REQUESTS.jsonl --queue research/readiness/FETCH_QUEUE.jsonl`.

## Next actions by owner

| Owner | Orders |
|---|---:|
| owner | 2665 |
| agent_check | 2376 |
| machine_job | 265 |

## First twenty rows

| Order | Date | Route | Status | Next action |
|---|---|---|---|---|
| EO:1 | 1862-02-14 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:2 | 1862-02-27 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:3 | 1865-04-29 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:4 | 1865-05-09 | proquest_local | pinakes_file_record_pages_unchecked | Compare the PDF pages with the transcription; owner decides the custody grade |
| EO:5 | 1866-04-13 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:6 | 1868-07-20 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:8 | 1872-04-16 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:8-1 | 1873-03-14 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:9 | 1873-01-17 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:9-2 | 1873-01-28 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:11 | 1873-08-05 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:13 | 1874-03-09 | proquest_local | pinakes_file_record_pages_unchecked | Compare the PDF pages with the transcription; owner decides the custody grade |
| EO:16 | 1874-05-29 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:17 | 1874-08-31 | proquest_local | pinakes_file_record_pages_unchecked | Compare the PDF pages with the transcription; owner decides the custody grade |
| EO:18 | 1875-07-31 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:19 | 1875-11-22 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:20 | 1876-08-21 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:21 | 1881 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:22 | 1884-04-09 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:23-1 | 1885 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |

## Web search (online stage)

1 of 5306 targets advanced this run (5021 never searched yet); 17 of 12 requests used. 4147 hits on file, 41 pages confirmed to name the order (29 orders): `WEB_LEADS.csv`. State in `WEB_STATE.json` carries forward; nothing is marked exhausted by the machine.

| Engine | Status |
|---|---|
| bing_api | needs_key |
| bing_rss | blocked_by_robots_txt |
| brave_api | needs_key |
| brave_html | blocked_by_robots_txt |
| duckduckgo_html | error |
| duckduckgo_lite | ok |
| federal_register_api | not_tried |
| google_books | http_429 |
| google_cse | needs_key |
| govinfo_search_page | not_tried |
| hathitrust_catalog | not_tried |
| internet_archive | ok |
| loc_books | ok |
| loc_manuscripts | ok |
| loc_newspapers | ok |
| marginalia | error |
| mojeek_html | blocked_by_robots_txt |
| nara_catalog | needs_key |
| presidency_project | not_tried |
| serpapi_google | needs_key |
| wikipedia_search | not_tried |
| wikisource_search | not_tried |
| yandex_html | blocked_by_robots_txt |

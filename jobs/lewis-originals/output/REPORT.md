# Lewis: originals for transcription-only orders

Generated 2026-11-26T00:47:48Z. Leads and verified file facts; no count or grade changes.

**Scope: 393 orders** (clark_identified 1, clark_identified_not_in_universe 15, transcription_only 377).

## Where they stand on the ladder

| Route | Status | Orders |
|---|---|---:|
| proquest_phrase_search | manual_lead | 184 |
| proquest_local | pinakes_file_record_pages_unchecked | 150 |
| federal_register | fr_era_not_in_ofr_catalog | 47 |
| federal_register | in_ofr_catalog_no_citation | 6 |
| gpo_bound_volumes | in_volume_range_not_found | 2 |
| federal_register | retrieval_recorded_needs_review | 2 |
| proquest_supplied_link | awaiting_acquisition | 1 |
| federal_register | queued_retry_later | 1 |

## ProQuest folder

4841 PDF files (4841 unique by SHA-256) cover 4841 orders; 150 of them are in Lewis's scope and 4691 belong to orders outside it (Clark's no-text orders, mostly). 4267 text layers pass the quality screen (handwritten originals give noise and are excluded). The supplied link list has 2765 links, 143 for orders in this scope.

Authority: pinakes-proquest-ingest. PDF signature results are not reported for 4841 inventory records; missing values are unknown, not verification failures or successful checks. Pinakes order records are reused without rereading PDFs or duplicating its fragments.

## Proposed fetch requests

0 requests for the source-ladder job in `PROPOSED_FETCH_REQUESTS.jsonl` (validated with the source-ladder request contract: True). To enqueue them: `python jobs/source-ladder/request_contract.py enqueue --input jobs/lewis-originals/output/PROPOSED_FETCH_REQUESTS.jsonl --queue research/readiness/FETCH_QUEUE.jsonl`.

## Next actions by owner

| Owner | Orders |
|---|---:|
| agent_check | 207 |
| owner | 185 |
| machine_job | 1 |

## First twenty rows

| Order | Date | Route | Status | Next action |
|---|---|---|---|---|
| EO:1 | 1862-02-14 | proquest_local | pinakes_file_record_pages_unchecked | Compare the PDF pages with the transcription; owner decides the custody grade |
| EO:2 | 1862-02-27 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:8-1 | 1873-03-14 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:9-2 | 1873-01-28 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:11 | 1873-08-05 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:22 | 1884-04-09 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:23-1 | 1885 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:25 | 1885 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:27 | 1887-10-24 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:27-1 | 1887-10-24 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:27A |  | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:28-1 | 1891-01-30 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:30-1 | 1893 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:36 | 1894-11-02 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:37 | 1894-11-02 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:41 | 1894-11-02 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:44 | 1894-11-02 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:46 | 1894-11-02 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:47 | 1894-11-02 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |
| EO:49 | 1894-11-02 | proquest_phrase_search | manual_lead | Not on the supplied ProQuest list: find the record by phrase search and add its link to a  |

## Web search (online stage)

100 of 393 targets advanced this run (101 never searched yet); 771 of 1500 requests used. 33257 hits on file, 248 pages confirmed to name the order (159 orders): `WEB_LEADS.csv`. State in `WEB_STATE.json` carries forward; nothing is marked exhausted by the machine.

| Engine | Status |
|---|---|
| bing_api | needs_key |
| bing_rss | blocked_by_robots_txt |
| brave_api | error |
| brave_html | blocked_by_robots_txt |
| duckduckgo_html | http_403 |
| duckduckgo_lite | http_403 |
| federal_register_api | ok |
| google_books | http_429 |
| google_cse | needs_key |
| govinfo_search_page | blocked_by_robots_txt |
| hathitrust_catalog | blocked_by_robots_txt |
| internet_archive | ok |
| loc_books | http_429 |
| loc_manuscripts | http_429 |
| loc_newspapers | http_429 |
| marginalia | error |
| mojeek_html | blocked_by_robots_txt |
| nara_catalog | needs_key |
| presidency_project | ok |
| serpapi_google | needs_key |
| wikipedia_search | blocked_by_robots_txt |
| wikisource_search | blocked_by_robots_txt |
| yandex_html | blocked_by_robots_txt |

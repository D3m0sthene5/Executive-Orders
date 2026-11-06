# Repetita: the List of CFR Sections Affected, read for executive orders

Named for Justinian's *Codex repetitae praelectionis* (534), the revised edition of his Code. Zero model tokens.
Part of the Encyclopedie campaign (stream `enc-lsa`, branch `enc/lsa`).

**Why.** Executive orders are codified in Title 3 of the CFR. The **List of CFR Sections Affected (LSA)** is the
monthly finding aid that lists every CFR part or section changed and, for Title 3, every proclamation, executive order,
notice and memorandum published or changed, each with the Federal Register citation of the change. Read as data, it can
date a revocation or amendment of an order ("13799 Revoked by EO 13820 ... 18-969" is 83 FR 969) or show that an order
is still being named by later documents ("12543 Continued by Notice of Jan. 2, 1997").

## What it reads

1. **LSA 1997 on, keyless.** govinfo's LSA collection. Issues are listed from the year sitemaps
   (`https://www.govinfo.gov/sitemap/LSA_sitemap_index.xml`, then `LSA_<year>_sitemap.xml`; months after the newest listed
   one are tried too and a missing one is not a failure). Each issue's bytes are
   `https://www.govinfo.gov/content/pkg/<LSA-YYYY-MM>.zip`, which holds one html member per CFR title
   (`html/<issue>-title<N>.htm`), a pdf per title and mods/premis/dip xml. Only the html members are parsed. Fetched
   through `jobs/_lib/fetch_pool.py` (robots.txt, 4 requests in flight at most, 0.25 s apart, sha256). robots.txt on
   `www.govinfo.gov` permits `/content/`. **The full run needs no key and does not wait for one.**
2. **Key handling.** The job reads `API_DATA_GOV_KEY` (alias `GOVINFO_API_KEY`) from the environment and never prints
   it. With a real key it also cross-checks the sitemap listing against the govinfo API
   (`api.govinfo.gov/collections/LSA/...`, key in an `X-Api-Key` header, never in a URL); the bytes always come from the
   keyless URLs above (the zip of 1997-01 is the same 5,491,302 bytes at both hosts). `DEMO_KEY` is used only in a
   smoke run and is refused for a full run. `SUMMARY.json` `route` says which key kind was present, whether the
   cross-check ran and what it found. `api.govinfo.gov/robots.txt` answers HTTP 500, which is why the API is not the
   byte route.
3. **Before 1997** (manifest only, no volume download). HathiTrust's monthly *hathifile* (the documented catalog dump,
   streamed and filtered, never stored) for volumes titled "List of CFR sections affected", "CFR parts affected",
   "Codification of presidential proclamations and executive orders" and full-view Title 3 / President volumes of the
   Code of Federal Regulations, with `access` (`allow` = full view) and `rights`; HathiTrust's Bibliographic API as a
   second reading of access for the LSA records; and the Internet Archive's `advancedsearch.php` and metadata API, with
   one smoke read of an LSA OCR text (size, sha256, counts; the text is not kept). HathiTrust page images and the Data
   API sit under `babel.hathitrust.org/cgi/`, which that host's robots.txt disallows for this agent, so no Hathi volume
   is read. HeinOnline, Westlaw, Lexis and ProQuest are never touched. `www.hathitrust.org` answers non-browser clients
   with a Cloudflare challenge at random; the job pauses and retries a robots/list request up to three times and never
   answers or evades the challenge. If it stays challenged (it did on GitHub's runner on 2026-11-06), the job falls back
   to HathiTrust's Bibliographic API (`catalog.hathitrust.org`) on 11 seed record numbers (the LSA and codification
   series, found by reading the 2026-11-01 hathifile from the owner's PC) and lists those records' items with their rights;
   `PRE1997_SUMMARY.json` says which route ran. It also carries the coordinator's survey leads (`survey_leads`): the Library
   of Congress holds sample LSA items for 1971-1982 whose scans come from HeinOnline under a stated term against bulk
   download (listed, never fetched; the owner has not decided), the Internet Archive has the 1973-1985 volumes, and the
   Federal Register's own Codification Guide sits inside the FR issues, which govinfo has for 1936-2026 with no key (not
   read here). No complete pre-1997 LSA run was found.

## What it writes (`output/`, at most 20 MiB in all and no file over 5 MiB, enforced by the job)

| File | Contents |
|---|---|
| `LSA_EO_ROWS.csv` (or `.<year>.csv` shards when over 4 MiB) | One row per (issue, CFR section or Title 3 item, change, Federal Register reference). Title 3: every entry. Other titles: entries that mention "E.O.", "EO nnnn", "Executive Order", "Exec. Order" or "Ex. Ord.". Columns: issue, title, item, change (verbatim), mechanism, acting instrument(s) parsed (`EO:`, `PROC:`, `PLO:`, `NOTICE:<date>`, `MEMORANDUM:<date>`, `PL:`), `fr_ref` as printed, `fr_cite` (volume and page), `ref_kind`, `eo_mention`, `eo_target` (the order a Title 3 "Executive Orders" row is about), `member`, `member_sha256`, `span_start`/`span_end` (byte span of the entry in the html member), `first_issue`, `last_issue`, `n_issues`. |
| `FRAGMENTS*.jsonl` | `later_event_candidates` for each Title 3 Executive Orders row whose acting instrument parses, in the shape the claim kit reads (same as Selden and current-law): `instrument_id` = the target order, `data[0]` with `acting_id`, `mechanism`, `quote` (the verbatim entry), `quote_span`, source id/url/sha256. |
| `SOURCES.jsonl` | Per issue: the zip (URL, sha256, size, retrieval time) and each html member used (public URL, sha256, size). `instrument_ids` is `[]` so the claim kit never reads an LSA listing as an order's own text. |
| `ISSUES.jsonl` | Per issue: status, zip sha256, entries parsed, an independent count of leader lines, span-check results, control results. It is also the resume state. |
| `CONTROLS.json` | Planted and known controls with the measured error rate (below). |
| `SUMMARY.json`, `BUDGET.json` | Counts and the route/key finding; committed bytes per file and the refusals if a limit was hit. |
| `PRE1997_MANIFEST.csv`, `PRE1997_SUMMARY.json` | Pre-1997 availability (HathiTrust full view or not, Internet Archive items), the Hathi bibliographic cross-check, the Internet Archive smoke read, the Hathi robots finding. |

Raw zips and html stay in the runner cache (`JOB_CACHE_DIR`), deleted after each issue is parsed, and are never committed.

## How to read a row

* **The LSA is cumulative within a calendar year.** The December issue repeats every entry of January to November. A
  row is kept once, at the first issue that prints it, with `first_issue`, `last_issue` and `n_issues`; `first_issue`
  bounds the month of the change from above (the LSA is published about a month after its date). `rows_before_dedupe`
  per issue is in `ISSUES.jsonl`. This departs from "one row per issue" on purpose: one row per issue would be about
  5 times larger than the 20 MiB budget.
* **The last column is a pointer.** From 1997 to early 2018 it is `YY-PAGE` (two-digit year of the Federal Register
  volume, then page: `97-4415` is 62 FR 4415); later it is the page alone, and its volume is then the issue's year
  (`year_assumed` = 1; a page printed in a January issue that belongs to the previous year's volume would be wrong,
  which is why such rows carry that flag). Volume = year - 1935.
* **An entry's category matters.** In Title 3, a bare number under "Proclamations" is a proclamation, under "Executive
  Orders" an order. Entries before the 20th century numbering ("Jan. 22, 1912 Revoked by PLO 7230") are orders known
  by date; they have no `eo_target`.
* A line that begins with "See" is a cross-reference (`mechanism_class` mention), not a stated amendment.

## A revocation date derived from the LSA stays a lead

An LSA entry says only that a document, published at a Federal Register page, revoked, amended, superseded or
continued an order. It does not give the document's signing or publication date, its text, or its scope (whole order or
part). Until the Federal Register page it names is held and read (the page's text, its date, its words), no claim may
treat the entry as a revocation date. Fragments carry the flag `lead_until_fr_page_held`. Nothing here changes a
status, a census, the codebook or a count. Certified: 0.

## Controls (`CONTROLS.json`)

Run on every issue's own Title 3 bytes, and on the final rows:

* **Planted positive:** a block with a heading and one entry is inserted before `</pre>` in memory; the parser must
  return that entry exactly once with its exact span, and the block must add exactly one entry.
* **Planted negatives:** a line without a dot leader, and one whose reference is not a number, must not become entries.
* **Known facts** (independent of the parser, from the orders themselves): 13799 revoked by EO 13820 (83 FR 969, issue
  2018-01); 10865 amended by EO 13284 (68 FR 4075, 2003-03); 12543 continued by notice of 1997-01-02 (62 FR 587, 1997-01);
  13292 revoked by EO 13526 (75 FR 707, 2010-05); 12667 revoked by EO 13233 (66 FR 56025, 2001-11). Checked in whichever
  of those issues is read.
* **Negatives on all rows:** a made-up order number, near misses of real entries (wrong revoking order, wrong page, wrong
  amending order), a made-up CFR section of a made-up title and of a real title must be absent.
* **Member check:** for up to three issues, the member's public URL hashes to the same bytes as the zip member.
* **Span check:** every entry (all titles) re-sliced from the held bytes ends with its reference and starts with its item.
* **Coverage:** `entries` against an independent regex count of leader lines per issue (`ISSUES.jsonl`); headings and
  titles with "No amendments" notes are the difference.

## Limits

* Parsing is by layout (dot leaders, wrapped lines, reference-only lines, page markers). Lines that are neither entries
  nor headings are counted as `dropped_pending_lines`. Entry text with unusual layout can be mis-split between item and
  change; the verbatim span is always right.
* Acting instruments are parsed from the change text only for the forms listed above; "Amended by 11044" (a bare number)
  is recorded in `acting_bare_number` and gets no fragment.
* LSA entries exist only for documents the Federal Register published and that affect CFR sections or Title 3 lists; they
  say nothing about orders never published there.
* Before 1997 only a manifest. The pre-1986 equivalents (CFR Parts Affected tables) also appear at the back of each
  Federal Register issue; those are in the Federal Register volumes the project holds, not here.
* The first Internet Archive hit is a Readex microprint copy of a GPO publication; its `rights` field is empty, so the
  public-domain basis is "United States Government Printing Office publication" (17 U.S.C. 105), a lead for the owner.

## Running

Push to this folder (the runner commits results back) or run by hand. `SMOKE` in the folder (or `JOB_SMOKE=1`; `JOB_SMOKE=0`
overrides the file) reads three issues (1997-01, 2003-03, 2018-01) and the pre-1997 manifest; delete the file for the full
run. `JOB_TIME_BUDGET_MIN` (default 300) stops starting new issues; the next run resumes from `output/ISSUES.jsonl` (issues
already `ok` are carried forward with no request; the newest two are always re-read; `JOB_FORCE=1` re-reads all;
`JOB_SKIP_PRE1997=1` skips the manifest). The job fails when more issue requests fail than succeed, when a byte limit is
hit, when no rows are parsed or when the control error rate is above 5%. Offline tests (`test_repetita.py`) run first.

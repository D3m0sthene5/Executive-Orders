# Archive-capture audit: live APP text versus Common Crawl / Wayback captures

Written 2026-10-18 from `MIRROR_AUDIT.jsonl` (205 rows), `MIRROR_DOCUMENTS.jsonl` (10,270 captures)
and `DOCUMENTS.jsonl` (792 live pages). No census, ledger, codebook or certified count is touched.

## Method

- Population: the 10,270 APP order pages the archive lane (`app_mirror.py`) read from Common Crawl
  WARC records (crawls CC-MAIN-2024-10 to CC-MAIN-2026-04) and Wayback Machine original-byte
  captures (`web.archive.org/web/<ts>id_/`). A capture is the APP page as of its `captured_utc`.
- Sample: every 50th covered path in lexicographic path order (positions 0, 50, 100, ... 10,250 of
  the sorted path list) = 206 paths. The sample is systematic, not random; because slugs start with
  the EO number it is spread across the whole numbered range and across all crawls present.
- Live side: `app_harvest.py documents --audit-every 50`, one request at a time, 10 s apart (APP's
  robots.txt Crawl-delay), User-Agent EO-Historical-Research/1.0, fetched 2026-10-18 23:05:43 to
  23:58:10 UTC. 0 failures, no 5xx, no challenge page in this pass.
- Comparison: both sides go through the same parser (`parse_document`). `text_agrees` = SHA-256 of
  `texts/<slug>.txt` (capture) equals SHA-256 of `texts/<slug>.live.txt` (live); both are UTF-8, LF,
  APP footnote excluded. `page_agrees` = SHA-256 of the raw HTML bytes agree.
- 205 of the 206 sampled paths have an audit row. The 206th, EO 5382
  (`/documents/executive-order-5382-authorizing-the-paymaster-the-panama-canal-advance-funds-bonded`),
  was fetched live at 22:13:09 UTC by the run that was already in progress when the archive lane read
  its capture (22:07:03 UTC), so the audit run treated it as done. Comparing the two recorded hashes
  gives the same answer as the sample: text SHA-256 `c1c04681...` on both sides (agrees), page hash
  differs. It is reported here but not counted in the 205.

## Result: text agreement by archive and capture year

| archive | capture year | sampled | text_agrees | page_agrees |
|---|---|---:|---:|---:|
| common-crawl | 2024 | 27 | 27 | 0 |
| common-crawl | 2025 | 150 | 150 | 0 |
| common-crawl | 2026 | 17 | 17 | 0 |
| wayback | 2022 | 1 | 1 | 0 |
| wayback | 2023 | 2 | 2 | 0 |
| wayback | 2024 | 2 | 2 | 0 |
| wayback | 2025 | 5 | 5 | 0 |
| wayback | 2026 | 1 | 1 | 0 |
| **common-crawl, all** | | **194** | **194** | 0 |
| **wayback, all** | | **11** | **11** | 0 |
| **total** | | **205** | **205** | 0 |

Captures in the sample date from 2022-07-28 (Wayback) to 2026-01-29 (CC-MAIN-2026-04). Common Crawl
crawls represented: 2025-38 (38), 2025-43 (32), 2025-47 (26), 2026-04 (17), 2025-51 (16), 2025-26 (15),
2025-13 (12), 2024-46 (9), 2025-05 (9), 2024-42 (6), 2024-18 (4), 2024-51 (3), 2024-22 (2), 2024-33 (2),
2025-21 (2), 2024-10 (1).

## Disagreements

None. Every sampled capture's order text is byte-identical to the text APP served on 2026-10-18.
There is therefore no diff to list.

`page_agrees` is false for all 205: the raw HTML differs on every page (page chrome: scripts, menus,
timestamps, cache tokens). That is expected and is not a finding; only the extracted order text is
the representation this job keeps.

## Reading the number

- 0 disagreements in 205 gives a one-sided 95% upper bound of about 1.5% (rule of three, 3/205) on the
  share of captures whose text no longer matches APP, under the assumption that the systematic sample
  behaves like a random one. The oldest agreeing capture is from July 2022, so APP's order texts have
  been stable over at least the 2022-2026 capture window for the sampled pages.
- Agreement means the capture equals APP's current editorial transcription. It says nothing about
  APP's accuracy against an original. Every text stays grade `mirror_transcription`,
  `representation_type=secondary_compilation_transcription`, `acceptable_as_original=false`;
  it is historical-document discovery, not identity authentication or a legal finding.
- 47 captures hold no order text (APP's own "[Not Published.]" pages, `MIRROR_FAILURES.jsonl`,
  reason `no_usable_text`); they are outside this sample by construction.

## Files

- `MIRROR_AUDIT.jsonl`: one row per audited path (`instrument_id`, `archive`, `captured_utc`,
  `live_retrieved_utc`, both text and page SHA-256s, `text_agrees`, `page_agrees`).
- `texts/<slug>.txt` (capture) and `texts/<slug>.live.txt` (live) for each audited path.

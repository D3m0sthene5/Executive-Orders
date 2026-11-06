# Mabillon NARA: the National Archives' own catalog of signed executive orders

Named for Jean Mabillon (1632-1707), founder of diplomatics, the science of authenticating original documents.

The signed originals of the numbered executive orders are in Record Group 11 (General Records of the United States
Government) at the National Archives. This job asks the Archives' own public bulk export of its Catalog which of
them are described and imaged, without a key: the AWS Registry of Open Data bucket `nara-national-archives-catalog`
(anonymous HTTPS, `descriptions/record-groups/rg_11/rg_11-N.jsonl`; see
https://www.archives.gov/developer/national-archives-catalog-dataset). It does not call the Catalog API, which needs
a key and whose terms ask users not to cache or store returned content.

## Stage 1: census (`census.py`)

Resolves the record-group folders (RG 11, plus RG 59, 48, 95 and 130 only to rule out other imaged copies; a group too large for the cap is skipped whole and its size reported), lists their chunks, estimates bytes and time before reading (`plan` in the log and `SUMMARY.json`), reads each
chunk once (cap `JOB_MAX_BYTES`, default 3 GB; 4 workers, 4 in flight, 0.1 s apart, every body hashed), and keeps
every description whose own or an ancestor's title names executive orders. Order numbers are read from item titles
("Executive Order No. 1234", "E.O. 1234", a bare "No. 1234" only under an executive-order series); a file unit's
explicit number range is kept as weaker range coverage.

| File | What it is |
|---|---|
| `SUMMARY.json` | Plan, counts, coverage of Mabillon's frame (`research/mabillon/frame/FRAME.csv`), top series. |
| `SERIES.csv` | Each series (or top description) naming executive orders: descriptions, imaged descriptions, objects, number span. |
| `BY_ORDER.csv` | Every order number named by an item description, with object counts and the first object URL. |
| `FRAME_COVERAGE.csv` | Every frame order: item descriptions, imaged ones, range coverage, NAIDs. |
| `EO_DESCRIPTIONS.jsonl.gz` | The lean kept descriptions (NAID, level, title, ancestors, dates, object URLs, chunk). |
| `SCHEMA_SAMPLE.json` | Key paths of the export and sample records, so later stages read fields exactly. |
| `CHUNKS.jsonl`, `ERRORS.jsonl` | Each chunk's bytes, SHA-256, ETag and date; failures. |

A description or object URL is a location lead, not a verified match. Nothing here changes a status, identity,
census entry, codebook grade or count, and the readiness tracker does not read this job.

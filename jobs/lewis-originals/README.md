# Lewis: originals for orders held only as transcriptions

Lewis and Clark (`jobs/clark-discovery`) are a pair. Clark establishes *what an order is* when the
project has only a number, or not even that; Lewis finds *the official original* once the order's
identity and wording are known. Clark's finds flow into Lewis (`HANDOFF_TO_LEWIS.jsonl`); the
ProQuest text layers Lewis verifies flow back into Clark's citation harvest on the next run.

## Scope

Every order whose `original_text` readiness step is open with the blocker
`ONLY_COMPILED_TRANSCRIPTION_FOUND` (4,644 orders on 2026-10-21: a Richardson, American Presidency
Project, Wikisource, HathiTrust or other printed-copy text exists, so the date and wording are known,
but no official original is saved), plus any order Clark hands over with identity evidence. Orders
with no transcription at all are Clark's, not Lewis's.

## The ladder

For each order Lewis records where it stands on a fixed ladder of routes and the one next action:

| Route | When | Status Lewis can give | Who acts |
|---|---|---|---|
| `proquest_local` | A ProQuest "Replica of Original" PDF for the order is in `research/pre-1937-sources/ProQuest Pre-1937 Orders/` | `file_verified_pages_unchecked` (signature, SHA-256, page count checked; contents not) | agent compares pages; owner decides the custody grade |
| `proquest_supplied_link` | The owner's ProQuest link list names the order, no PDF yet | `awaiting_acquisition` | owner uploads the PDF |
| `federal_register` | Signed on or after 1936-03-14 | `fetch_request_proposed` (OFR citation known), `in_ofr_catalog_no_citation`, or `fr_era_not_in_ofr_catalog` (1936 orders: the catalog starts at EO 7532) | source-ladder job, after the owner enqueues the proposals |
| `gpo_bound_volumes` | EO 5800–8027, not found by hathi-gpo-orders | `in_volume_range_not_found` | agent checks the volume index |
| `ofr_hoover_compilation` | EO 5076–5549, not found by ofr-compilations | `in_volume_range_not_found` | agent checks Hoover vol. I |
| `proquest_phrase_search` | Before 1937, not on the supplied list | `manual_lead` with the exact phrase to search | owner (ProQuest needs the NYU sign-in) |
| `nara_rg11` | Anything left | `manual_lead` | owner |

## Outputs (`output/`)

| File | What it is |
|---|---|
| `ROUTES.csv` | One row per order in scope: date and its source, title, which transcription jobs hold it, ProQuest file facts, FR citation, `best_route`, `route_status`, `next_action`, `action_owner`, and the URL or search phrase to use. |
| `PROQUEST_INVENTORY.csv` | Every PDF in the ProQuest folder: parsed year/number/suffix, bytes, SHA-256, `%PDF-` signature, pages, text-layer size and quality, duplicate-of (byte-identical copies such as Chrome's ` (1)`), and whether the order is in the census. |
| `FRAGMENTS.jsonl` | One project fragment per verified ProQuest PDF, `produced_by: lewis-originals`, grade `archival_replica_scan_pending_codebook`, `acceptable_as_original: false`, `needs_page_check: true`. The readiness tracker does not read these yet: counting them is a codebook decision for the owner (see below). |
| `texts/EO_<n>.txt` | The PDF text layer, only where it passes the quality screen (printed originals; handwritten scans give noise and are not written). Clark reads these. |
| `PROPOSED_FETCH_REQUESTS.jsonl` | Source-ladder requests for FR-era orders with an OFR citation, validated with `jobs/source-ladder/request_contract.py`. Lewis never writes to `research/readiness/FETCH_QUEUE.jsonl` itself. |
| `REPORT.md`, `SUMMARY.json` | Counts by route, status and owner; folder statistics; problems. |

To enqueue the proposals:

```sh
python jobs/source-ladder/request_contract.py enqueue --input jobs/lewis-originals/output/PROPOSED_FETCH_REQUESTS.jsonl --queue research/readiness/FETCH_QUEUE.jsonl
```

## What Lewis does not do

- It fetches nothing from the network. ProQuest needs a sign-in; the Federal Register route goes through the source-ladder job.
- It changes no readiness step or count. A verified ProQuest file is a lead with byte evidence, not an original: the
  tracker counts only finds a job did not flag `needs_page_check`, and every Lewis fragment is flagged. If the owner
  decides ProQuest replica scans may count after a page check, the change is one rule in `jobs/readiness-tracker/tracker.py`
  (a new class in `J`, with a test), not here.
- It never guesses a ProQuest URL for acquisition. The `proquest_phrase_search` lead is the search the project's own
  survey found to work (`research/pre-1937-sources/PROQUEST_CONGRESSIONAL.md`); the permalink pattern in a fragment's
  `url` is the accession's documented form and is marked unverified by `location_verified: false`.

## Running

GitHub: Actions → Run jobs → `lewis-originals`. It runs daily, after `clark-discovery` and `readiness-tracker` when
they run together, and whenever `research/pre-1937-sources/` or the census changes. Needs about 20 seconds and no network.

Locally, from the repo root:

```sh
REPO_ROOT=. OUTPUT_DIR=/tmp/lewis python jobs/lewis-originals/job.py
```

`job.py` runs `test_lewis.py` first (synthetic repository, no network) and stops if a test fails.
`pypdf` is optional: without it the inventory still verifies bytes and hashes but reports no page counts or text layers.

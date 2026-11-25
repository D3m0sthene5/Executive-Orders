# Peiresc: ProQuest replicas of the numbered orders that had no official text

Named for Nicolas-Claude Fabri de Peiresc (1580–1637), who built his library from copies of other people's manuscripts that he asked correspondents across Europe to make for him.

On 2026-11-24 the tracker listed 2,192 numbered orders with no official text (no Federal Register page, no official compilation, no checked original). In samples, ProQuest Congressional held a "Replica of Original" PDF for about 93% of them. This harvest fetched those PDFs, using the owner's logged-in NYU session, with ProQuest use approved by an NYU librarian.

## Method

- **Fetch.** Each PDF was fetched in the page with the site's own numbered-order PDF route, one request at a time, with up to 4 tries and backoff. The bytes, their sha256 and their length were kept in the browser.
- **Transfer.** The bytes were moved into the workspace as base64 page text. `decode.py` rebuilt each file. It wrote a file only when the sha256 and length matched what the browser received; no mismatches occurred.
- **Commit.** Files were committed as `research/pre-1937-sources/ProQuest Pre-1937 Orders/PT1-<year>-EO-<number>.pdf`, the Pinakes naming, in four batches on this branch.

## Result

| | Orders |
|---|---:|
| Targeted | 2,192 |
| Fetched and verified (`MANIFEST.csv`, 358 MB) | 2,097 |
| Not on ProQuest: 404 | 15 |
| Not on ProQuest: 500 on every try (73 are lettered suffix orders such as 324c) | 80 |

`NOT_FETCHED.csv` lists the 95 orders that were not fetched. Most numbers in the harvest predate 1937. The rest are later orders the tracker also held without official text, from 1938 to 1993.

## What it fed

- **Pinakes** (runs 45547393448 and 45550428437). The project now holds ProQuest replicas for 4,841 orders, up from 2,750. Every order has text: 3,984 from the PDF's own text layer and 857 from OCR. 574 read as low quality, probably handwritten.
- **Tracker** (run 45551893827). 2,101 orders now carry the lead `ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK`:
  - 1,873 have no provisional status;
  - 210 are decided orders also blocked by `NO_OFR_CATALOG_ENTRY_SEARCH_INCOMPLETE`;
  - 17 are decided orders that a passing page check moves straight into the claim-ready pool.
- **Page check.** This is the Photius method under D-20261106-photius-p4, run as Bentham ranks it. See `../photius-replica-peiresc/` and Kean D-20261125-peiresc-page-check.

A replica is ProQuest's image of the State Department file copy. A replica that passes the check credits the original-text step. Its `acceptable_as_original` stays false. Nothing in this harvest changes a status, the census, the codebook or the human-certified count, which stays 0.

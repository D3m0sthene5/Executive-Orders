# Lewis schema follow-up, 2026-10-22

## Observed production failure

[Run 39802916101](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39802916101) completed the repaired ranger chain, census intake, tracker, case bundles, Clark, corpus, Lambertini, x1, Polya, portfolio validation, Neyman, pilot and digest. Clark ran about 47 minutes (15:20:08–16:07:10 UTC). Lewis then failed at its summary's `r["pdf_signature"]` lookup; Domesday was correctly blocked. Successful outputs and failed-attempt receipts are retained in bot commit `5510babb6c608d677c5620ad5eeab7645597ebd7`.

That published generation reports **280 of 14,972 ready for human review**, 3,359 provisional statuses, no tracker input problems and all six source-audit holds retained. Ranger acquired 20 of 21 metadata records, ten JPEGs and ten XML transcriptions (10,514 words); the failed metadata retrieval is not counted as a success. Clark used 783 requests, reused eight cached pages and explicitly deferred 679 engine queries. Its 23 confirmed lead pages are research leads, not reviewed claims. Portfolio validation passed with six actual claim records and no new human or legal decisions.

## Repair and scope

Current Pinakes `ORDERS.csv` is a per-order schema. `pdf_signature` and `name_parsed` belong to its inventory schema and are absent from the order export. Lewis now adapts that export explicitly, validates required identities/hash/numeric fields, and records absent facts as unknown. Its route label says a Pinakes file record exists with pages unchecked. A recorded PDF is not described as verified. No PDF reread, OCR, duplicate fragment, custody promotion or legal finding is introduced.

An absent Pinakes file retains the original legacy-inventory fallback. A present but empty Pinakes file remains authoritative, avoiding a redundant rescan. Malformed published records fail explicitly rather than silently falling back. All prior source-audit holds and existing status/census/codebook files are untouched.

## Validation

- 24 Lewis tests pass with sockets blocked, including five new schema/fallback/empty/malformed-record cases. Existing legacy fragment tests preserve `acceptable_as_original: false`.
- All 2,750 records from actual bot `5510babb` Pinakes `ORDERS.csv` parse; Git blob `b413399030b1fbc9d5739c1c668ca9993f8d83d0` was verified. 2,440 report usable text. An offline run with these real Pinakes records and a **synthetic three-order readiness scope** succeeds, writes no duplicate fragments, performs no PDF reads/scans, and reports all 2,750 missing signature facts as unknown. This is not a full production acquisition replay.
- Independent reviewer reran all 24 Lewis and three Domesday tests, verified the actual Pinakes blob, and repeated the 2,750-record/synthetic-three-order replay with legacy scanning forbidden. Three downstream probes (current Pinakes, present-empty, absent/legacy) retain open original-text work and pages-unchecked custody; the new route label is display-only downstream. No blocking findings or reviewer source edits.
- CI's permanent road-test entry point now includes Lewis. All 227 tests across its suites pass locally. Job suites prohibit socket connections. Runner fixtures use temporary repositories. The system Git was blocked by local Xcode licensing; runner tests passed using bundled Git and the existing Python interpreter. Initial environment failures are preserved in local scratch, and successful suite logs are in `LEWIS_ROAD_TESTS.log`.
- Scheduler selection for this commit is exactly `lewis-originals`, `domesday-register`, `example-hello`. Existing completed ranger/Clark outputs remain the base; their expensive work is not selected again.

The new live Lewis web stage and final Domesday publication must still be verified after the fix is pushed. Existing search budgets are unchanged. No new token, cash or CPU-speed savings are claimed.

# Eumenes: National Mediation Board report PDFs in the Pergamon store

Named for Eumenes II, who built the Library of Pergamon.

Owner decision D-20261110-papinian-board-bytes stores the board reports in the Pergamon release-asset store, not on
main, and gives claim-checker a store adapter. Under the board rule (D-20261108-board-rule), a board's command ends
when its report is transmitted. Until now, every report PDF existed only in source-ladder's runner cache, so on
GitHub the checker graded each one `custody_record_only`, and the board orders could not close their ending step
(Kean F-20261110-papinian-board-custody).

## What was done (2026-11-10)

- **Downloaded:** all 119 distinct report PDFs that source-ladder recorded (its `nmb.gov` records), re-downloaded
  from nmb.gov.
- **Verified:** every one hashed to the SHA-256 source-ladder recorded. None differed.
- **Stored:** uploaded with `jobs/_lib/pergamon_store.py migrate` (release backend): 119 uploaded, 0 failed,
  206,512,111 bytes. `data/PERGAMON_MANIFEST.jsonl` is the store's record of them.

## What the job does

`job.py` joins each manifest record to source-ladder's record of the same bytes. It writes `output/SOURCES.jsonl`
in the shared source-record format, with a `pergamon` field holding the locator. It first fetches every record by
its locator and re-hashes it, with no token needed. It publishes nothing if any record is missing or differs.
Measured: 119 published, 126 orders covered, about 37 seconds.

claim-checker's Pergamon adapter (`jobs/claim-checker/sources.py`, the reviewed patch from
`research/encyclopedie-campaign/storage/checker_adapter.patch`) reads that field. It treats the locator as another
way to obtain the file, fetches the bytes into its cache, and re-hashes them. Only bytes that hash to the recorded
SHA-256 count as held (`held_bytes_verified`). The store is never trusted by itself.

## Run

After merge, dispatch once:

```bash
gh workflow run run-jobs.yml --ref main -f job=eumenes-nmb-reports -f only=true
```

It reruns when source-ladder's `SOURCES.jsonl` or the manifest changes (`triggers.txt`). Tests: `test_job.py`.

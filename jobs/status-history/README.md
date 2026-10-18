# Reusable dated status-history preparation

Compiles the already held 1989 OFR disposition table and raw OFR API responses,
crosswalks them to the existing census, and attaches exact-source candidate events.
This removes repeated table lookup, raw-note search, date typing, event sorting,
source reassembly and obvious conflict triage from individual-order startup.
It does not decide status, first cessation, legal intervals, or identity admission.

```sh
python -B jobs/status-history/job.py
python -B jobs/claim-kit/kit.py history EO:12331
python -B jobs/claim-kit/kit.py history EO:12331 --full
python -B jobs/claim-kit/kit.py status-sheet EO:12331 --agent NAME --write research/readiness/decisions/NAME-DATE/EO_12331-status.json
python -B jobs/status-history/audit.py --out research/excavator/2026-10-18/status-history-pilot
```

The job reads only local inputs, declares its upstream jobs in `after.txt`, runs
tests first and writes only `output/`. `INPUTS.json` hashes every input and the
compiler. Individual histories hash their own observation/event records, so an
unrelated source change does not invalidate every decision. Unchanged histories
are byte-for-byte reused in a warm local run; GitHub's runner empties output first,
so that runner rebuilds them. No network or model call occurs in this component.
Do not consume a failed `STATUS.json` or `FAILED.json`. Direct history/status-sheet
readers and fragment ingestion reject failed runs. A successful local rerun does
not overwrite a runner's failed STATUS; rerun through the runner to replace it.

`INDEX.json` covers every included census ID, including explicit no-history cases.
`histories/` stores conditional temporal constraints, flags, next actions and exact
record fingerprints. `observations/` and `events/` hold shared sharded records once;
full packets include acting-note observations even when they belong to another EO.
`FRAGMENTS.jsonl` feeds the existing claim-kit collector: decided dossiers and
undecided `STATUS_LEADS` receive a pointer, with no status/original/event promotion.
`UNRESOLVED_WITNESSES.jsonl` preserves unmatched identities separately.
`SHARED_SOURCE_READS.json` exposes reproducible source/order memberships;
`SUMMARY.json` and `METRICS.json` distinguish coverage and execution measurements.

Default claim-kit history output is a compact UTF-8 JSON startup (18,000-byte cap,
excluding final newline). It keeps warnings and typed dates, labels note truncation,
counts omitted event records, and names the full-evidence command. Full records
remain available; previewing them is not a legal source read. The status sheet is
blank and pinned, with `approved:false`, no recommended status and no accepted
intervals. There is no status-sheet publishing command. After reviewed provisional
adjudication, use the existing claim-kit dossier/sheet/assemble/check workflow.

Scientific boundaries:

- The book describes an editorial snapshot at **1989-01-20**. Ended rows supply
  only a conditional upper bound on the editor-described disposition, with an
  unknown lower bound. Active rows describe one point, not continuity or 2026 effect.
- Exact positioned OCR chunks are quoted individually with page/x/y/offsets and
  hashes. The reconstructed table row is labeled producer interpretation, not a
  verbatim contiguous quote or an image-verified original. Existing volume
  acquisition/extraction is reused rather than downloaded again.
- Raw API capture date **2026-10-15** is a custody date, not the legal cutoff.
  Exact time is unavailable. Candidate signing, note and stated-effective dates
  keep their original meanings. Events after the cutoff are flagged.
- Only whitespace differences may match an edge to a raw note. Punctuation/OCR
  changes and repeated ambiguous strings remain unverified. Target and actor
  notes are dependent editorial evidence, not independent corroboration.
- Casing, duplicate raw numbers, corrections and same-date historical witnesses
  are never silently normalized into identities. Empty notes prove nothing current.
- Source/exact-span QA tests stored evidence integrity, not legal correctness.
  The independent AI audit is not human certification.

Pilot and independent review: `research/excavator/2026-10-18/REPORT.md`.


# Daily research digest

New York date: 2026-10-22. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Ready for human review: 278 of 14,972 orders (1.9%)**

Of these, 0 rest on a labeled transcription for the text step (owner ruling 2026-10-21: provisional; original not yet held).

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,359. The other 11,613 have not been researched yet.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,359 | 3,359 | 100.0% |
| Original text saved in the project | 3,212 | 3,359 | 95.6% |

## Changes since the previous day

Comparison snapshot: 2026-10-20; intervening runs may be absent.
- claim-checker: held_distinct_sha256: 43487 → 44695
- domesday-register: orders: unavailable → 14972; with_any_text_file: unavailable → 11517; with_date: unavailable → 14887; with_title: unavailable → 10139
- family-rules: saved_texts_scanned: 46996 → 47033
- lambertini: pool_LAMBC: 18 → 455; pool_LAMBS: 91 → 103
- lewis-originals: fragments_written: unavailable → 11
- official-fixity: carried_forward: 5136 → 5154; checked_this_run: 18 → 3; files: 5154 → 5157; premis_bytes_read_this_run: 327680 → 0
- readiness-tracker: orders_with_provisional_text: unavailable → 4651; ready_resting_on_transcriptions: unavailable → 0
- source-ladder: attempts_logged: 50 → 30; bytes_downloaded: 475352251 → 850521061; distinct_new_source_hashes: 38 → 29; earlier_found_failing_todays_checks: 2 → 0

## Top shared unlocks

- orders_unblocked: 431; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source USC::48 U.S.C. 863); blocker: SHARED_SOURCE_NOT_RETRIEVED:USC::48 U.S.C. 863)
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6964; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6964
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6910; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6910
- orders_unblocked: 2; kind: one_source; action: Retrieve shared source CFR::26 CFR 458.324; blocker: SHARED_SOURCE_NOT_RETRIEVED:CFR::26 CFR 458.324

## Open asks from the newest handoff entries

- notes-astra.md: No open ask recorded in newest entry.
- notes-claude.md: - **Asks:** `@Claude` / `@Codex`: one tracker rule so a labeled transcription satisfies `original_text` provisionally (ruling 6), with a separate count of ready orders that rest on transcriptions; then rerun the tracker.
- notes-codex.md: No open ask recorded in newest entry.
- notes-sol.md: - **Asks:** None while validation is running.

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- early-ranger-transcriptions: failed (https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39080984937)
- hathi-gpo-orders: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39799572427)

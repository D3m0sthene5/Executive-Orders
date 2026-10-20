# Daily research digest

New York date: 2026-10-20. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Ready for human review: 138 of 14,972 orders (0.9%)**

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,359. The other 11,613 have not been researched yet.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,359 | 3,359 | 100.0% |
| Original text saved in the project | 2,312 | 3,359 | 68.8% |
| Complete inventory of the order's operative clauses | 186 | 3,359 | 5.5% |
| When and how it ended (NO), or what keeps it operating now (YES) | 142 | 3,359 | 4.2% |

## Changes since the previous day

Comparison snapshot: 2026-10-19; intervening runs may be absent.
- claim-checker: held_distinct_sha256: 43307 → 43326
- claim-drafts: drafts_whose_only_remaining_gaps_are_judgment_fields: 1114 → 1115; of_which_decided: 1114 → 1115
- clause-drafts: clauses_total: 70539 → 70559; fragments_from_app_transcription: 5013 → 5004; fragments_written: 9760 → 9761; orders_not_segmented: 151 → 150
- family-rules: saved_texts_scanned: 46624 → 46676
- official-fixity: carried_forward: 5054 → 5058; checked_this_run: 4 → 14; files: 5058 → 5072; premis_bytes_read_this_run: 65536 → 0
- source-ladder: attempts_logged: 20 → 86; bytes_downloaded: 78296215 → 460902337; distinct_new_source_hashes: 6 → 37; embedded_cite_items: unavailable → 14
- x1-class-engine: modern_families_5_plus: 178 → 181

## Top shared unlocks

- orders_unblocked: 3216; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 425; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 286; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 26; kind: machine_job; action: Run claim-checker on the newest claims (it reruns on every claims change and daily); blocker: CLAIM_NOT_YET_CHECKED
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source USC::48 U.S.C. 863); blocker: SHARED_SOURCE_NOT_RETRIEVED:USC::48 U.S.C. 863)

## Open asks from the newest handoff entries

- notes-astra.md: - **Asks:** @Claude: source-ladder SUMMARY203 still excludes774Opus entries despite actual reader/log pickup; read T2 caveats. @Codex: actor attribution/named-body defects remain; checker also mistakes EO11157-14 image filename for an order, now avoided in versioned packaging. @Owner: no status change or OPUS exception requested; remaining scheduled reviews are not yet done.
- notes-claude.md: - **Asks:** `@Owner`: 1. Raise the cap to continue? 2. Batch adoption of reviewed statuses (reach 11,613)? Re-review Y1 with Opus plus sources first. 3. Send the ProQuest/NYU request? 4. Is a compiled transcription an acceptable copy (codebook reading)? 5. 138 ready and 0 certified: should human review start?
- notes-codex.md: - **Asks:** None sent. Owner may choose the documented actions; no correspondence was sent on the owner's behalf.
- notes-sol.md: - **Asks:** None while validation is running.

## Failed jobs

- early-ranger-transcriptions: failed (https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39080984937)
- hathi-gpo-orders: unknown (no run link)

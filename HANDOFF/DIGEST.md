# Daily research digest

New York date: 2026-10-20. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Ready for human review: 251 of 14,972 orders (1.7%)**

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,359. The other 11,613 have not been researched yet.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,359 | 3,359 | 100.0% |
| Original text saved in the project | 2,312 | 3,359 | 68.8% |
| Complete inventory of the order's operative clauses | 315 | 3,359 | 9.4% |
| When and how it ended (NO), or what keeps it operating now (YES) | 273 | 3,359 | 8.1% |

## Changes since the previous day

Comparison snapshot: 2026-10-19; intervening runs may be absent.
- claim-checker: claim_lines_found: 226 → 358; claims_all_checks_passed: 141 → 270; claims_checked: 226 → 358; claims_gate_passed: 141 → 273
- claim-drafts: drafts_whose_only_remaining_gaps_are_judgment_fields: 1114 → 1115; of_which_decided: 1114 → 1115
- clause-drafts: clauses_total: 70539 → 70593; fragments_from_app_transcription: 5013 → 4971; fragments_written: 9760 → 9761; orders_not_segmented: 151 → 149
- family-rules: saved_texts_scanned: 46624 → 46954
- lambertini: counterevidence_records: unavailable → 687; decided_orders_with_draft: unavailable → 3359; packet_targets: unavailable → 807; packets: unavailable → 84
- neyman-pilot: attempts: unavailable → 24; complete_dossiers: unavailable → 0; human_certifications_added: unavailable → 0; legal_decisions_added: unavailable → 0
- official-fixity: carried_forward: 5054 → 5104; checked_this_run: 4 → 32; files: 5058 → 5136; orders_with_a_gpo_matched_file: 5068 → 5069
- readiness-tracker: ready_for_human_review: 138 → 251
- source-ladder: attempts_logged: 20 → 64; bytes_downloaded: 78296215 → 89048310; distinct_new_source_hashes: 6 → 45; earlier_found_carried_with_defect: unavailable → 0
- valla: active_claims: unavailable → 357; examined_dependencies: unavailable → 0; legal_promotions: unavailable → 0; model_calls: unavailable → 0
- x1-class-engine: modern_families_5_plus: 178 → 188

## Top shared unlocks

- orders_unblocked: 4644; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 435; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 286; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 19; kind: one_source; action: Retrieve shared source STAT::66 Stat. 259; blocker: SHARED_SOURCE_NOT_RETRIEVED:STAT::66 Stat. 259
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source USC::48 U.S.C. 863); blocker: SHARED_SOURCE_NOT_RETRIEVED:USC::48 U.S.C. 863)

## Open asks from the newest handoff entries

- notes-astra.md: No open ask recorded in newest entry.
- notes-claude.md: - **Asks:** `@Owner`: 1. Report-deadline ruling (47 orders now, about 89 in all). 2. Adopt the 56 NO proposals? 3. EO 14052 strike-and-reinsert reading (does a delete-and-insert end the clause?). 4. The transcription-as-copy and Lamm readings are still pending.
- notes-codex.md: - **Asks:** None requiring owner confirmation; user already authorized software integration.
- notes-sol.md: - **Asks:** None while validation is running.

## Published output status

A failed attempt preserves the prior successful output. Newer failure receipts are retained under jobs/_attempts; the current workflow status is authoritative for this execution.
- early-ranger-transcriptions: failed (https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39080984937)
- hathi-gpo-orders: unknown (no run link)
[Current workflow status and retained attempt artifacts](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39503891853)

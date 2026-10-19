# Daily research digest

New York date: 2026-10-18. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Ready for human review: 130 of 14,972 orders (0.9%)**

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,359. The other 11,613 have not been researched yet.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,359 | 3,359 | 100.0% |
| Original text saved in the project | 2,312 | 3,359 | 68.8% |
| Complete inventory of the order's operative clauses | 178 | 3,359 | 5.3% |
| When and how it ended (NO), or what keeps it operating now (YES) | 134 | 3,359 | 4.0% |

## Changes since the previous day

Comparison snapshot: 2026-10-17; intervening runs may be absent.
- app-footnote-leads: distinct_footnotes: unavailable → 1981; fr_citations_with_volume_and_page: unavailable → 1; fr_publication_dates_inferred: unavailable → 1184; later_order_edges: unavailable → 4
- app-transcriptions: orders_with_archive_fragment: unavailable → 9386; orders_with_source_record: unavailable → 9843; orders_with_source_record_in_census: unavailable → 9812; pages_tabulated: unavailable → 10727
- census-completeness: ambiguous_same_date_pairs: unavailable → 5119
- claim-checker: claim_lines_found: 42 → 218; claims_all_checks_passed: 1 → 133; claims_checked: 42 → 218; claims_gate_passed: 1 → 133
- claim-drafts: drafts_whose_only_remaining_gaps_are_judgment_fields: 770 → 1114; fragment_orders_not_in_universe: 34 → 66; of_which_decided: 770 → 1114; orders_with_any_conflict: 311 → 421
- clause-drafts: clauses_total: 35750 → 70268; fragments_from_app_transcription: unavailable → 4968; fragments_written: 4747 → 9715; orders_identity_quarantined: 144 → 10
- family-rules: saved_texts_scanned: 18681 → 43906
- indian-reservations-1912: acts: unavailable → 309; acts_before_1900: unavailable → 214; acts_with_a_lord_match: unavailable → 178; body_lines: unavailable → 11522
- isthmian-canal-1911: affected_document_leads: unavailable → 58; affected_targets_resolved: unavailable → 22; census_unnumbered_ids_not_comparable: unavailable → 19; contents_entries: unavailable → 177
- later-events: cache_hits: 7 → 0; decided_orders_with_any_candidate: 1839 → 1842; decided_orders_with_event_candidate_excluding_see: 1560 → 1563; edges: 19994 → 23837
- readiness-tracker: ready_for_human_review: 1 → 130
- richardson-volumes: lord_entries_citing_richardson: unavailable → 369; wpa_entries_parsed: unavailable → 155
- source-ladder: attempts_logged: 43 → 69; bytes_downloaded: 784275283 → 327863094; found: 122 → 147; found_carried_forward: 87 → 122

## Top shared unlocks

- orders_unblocked: 3172; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 472; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 286; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source USC::48 U.S.C. 863); blocker: SHARED_SOURCE_NOT_RETRIEVED:USC::48 U.S.C. 863)
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6964; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6964

## Open asks from the newest handoff entries

- notes-astra.md: No open ask recorded in newest entry.
- notes-claude.md: - **Asks:** `@Owner`: decide on the Common Crawl captures (above); approve committing crawl progress as it lands. `@Astra` / `@Codex`: `MIRROR_FRAGMENTS.jsonl` is discovery material only, same as `FRAGMENTS.jsonl`.
- notes-codex.md: No open ask recorded in newest entry.
- notes-sol.md: - **Asks:** None while validation is running.

## Failed jobs

- early-ranger-transcriptions: failed (https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39080984937)

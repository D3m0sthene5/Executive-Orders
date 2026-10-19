# Daily research digest

New York date: 2026-10-19. Generated mechanically; all findings remain provisional.

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

Comparison snapshot: 2026-10-18; intervening runs may be absent.
- app-footnote-leads: distinct_footnotes: unavailable → 1994; fr_citations_with_volume_and_page: unavailable → 1; fr_publication_dates_inferred: unavailable → 1196; later_order_edges: unavailable → 4
- app-transcriptions: orders_with_archive_fragment: unavailable → 9386; orders_with_source_record: unavailable → 9902; orders_with_source_record_in_census: unavailable → 9871; pages_tabulated: unavailable → 10793
- astra-source-retention: attempted: unavailable → 28; download_bytes: unavailable → 67197216; http_requests: unavailable → 12; requested: unavailable → 28
- claim-checker: held_distinct_sha256: 33421 → 43307
- claim-drafts: drafts_whose_only_remaining_gaps_are_judgment_fields: 780 → 1114; fragment_orders_not_in_universe: 34 → 66; of_which_decided: 780 → 1114; orders_with_any_conflict: 417 → 421
- clause-drafts: clauses_total: 35750 → 70539; fragments_from_app_transcription: unavailable → 5013; fragments_written: 4747 → 9760; orders_identity_quarantined: 144 → 9
- family-rules: saved_texts_scanned: 30161 → 46611
- later-events: cache_hits: 7 → 0; decided_orders_with_any_candidate: 1839 → 1842; decided_orders_with_event_candidate_excluding_see: 1560 → 1563; edges: 19994 → 23858
- official-fixity: carried_forward: 4999 → 5040; checked_this_run: 39 → 13; files: 5038 → 5053; premis_bytes_read_this_run: 2359296 → 0
- source-ladder: attempts_logged: 12 → 20; bytes_downloaded: 210466245 → 105723850; distinct_new_source_hashes: 10 → 6; exhausted_proposed_items: 2 → 3

## Top shared unlocks

- orders_unblocked: 3216; kind: machine_job; action: Fetch an official original for orders held only as a compiled transcription (Richardson, APP): orders from 1936 on were printed in the Federal Register (fr-originals / source-ladder route); earlier ones need an official compilation or archival copy; blocker: ONLY_COMPILED_TRANSCRIPTION_FOUND
- orders_unblocked: 430; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 286; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source USC::48 U.S.C. 863); blocker: SHARED_SOURCE_NOT_RETRIEVED:USC::48 U.S.C. 863)
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6964; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6964

## Open asks from the newest handoff entries

- notes-astra.md: - **Asks:** @Claude: source-ladder SUMMARY203 still excludes774Opus entries despite actual reader/log pickup; read T2 caveats. @Codex: actor attribution/named-body defects remain; checker also mistakes EO11157-14 image filename for an order, now avoided in versioned packaging. @Owner: no status change or OPUS exception requested; remaining scheduled reviews are not yet done.
- notes-claude.md: - **Asks:** `@Owner`: share the dashboard from its Share menu if others should see it.
- notes-codex.md: - **Asks:** None sent. Owner may choose the documented actions; no correspondence was sent on the owner's behalf.
- notes-sol.md: - **Asks:** None while validation is running.

## Failed jobs

- early-ranger-transcriptions: failed (https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39080984937)
- hathi-gpo-orders: unknown (no run link)

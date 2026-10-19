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
- astra-source-retention: attempted: unavailable → 28; download_bytes: unavailable → 67197216; http_requests: unavailable → 12; requested: unavailable → 28
- census-completeness: ambiguous_same_date_pairs: unavailable → 5002
- claim-checker: claim_lines_found: 42 → 218; claims_all_checks_passed: 1 → 133; claims_checked: 42 → 218; claims_gate_passed: 1 → 133
- claim-drafts: drafts_whose_only_remaining_gaps_are_judgment_fields: 770 → 780; of_which_decided: 770 → 780; orders_with_any_conflict: 311 → 417
- family-rules: saved_texts_scanned: 18681 → 30310
- hathi-gpo-orders: authenticated_originals: unavailable → 0; claim_kit_recognized: unavailable → 1531; federal_register_issues_used: unavailable → 37; government_bound_volumes_used: unavailable → 10
- indian-reservations-1912: acts: unavailable → 309; acts_before_1900: unavailable → 214; acts_with_a_lord_match: unavailable → 178; body_lines: unavailable → 11522
- isthmian-canal-1911: affected_document_leads: unavailable → 58; affected_targets_resolved: unavailable → 22; census_unnumbered_ids_not_comparable: unavailable → 19; contents_entries: unavailable → 177
- numbered-early-orders: books_held_scanned: unavailable → 17; books_new_fetched: unavailable → 12; fetch_failures: unavailable → 1; found_in_held_books: unavailable → 41
- official-fixity: carried_forward: 0 → 5015; checked_this_run: 4987 → 5; files: 4987 → 5020; orders_with_a_gpo_matched_file: 5013 → 5059
- readiness-tracker: ready_for_human_review: 1 → 130
- richardson-volumes: lord_entries_citing_richardson: unavailable → 369; wpa_entries_parsed: unavailable → 155
- status-history: census_admissions: unavailable → 0; census_identities: unavailable → 14972; distinct_shared_source_units: unavailable → 79; editorial_edges_raw_span_verified: unavailable → 15660

## Top shared unlocks

- orders_unblocked: 472; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 286; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 19; kind: one_source; action: Retrieve shared source STAT::66 Stat. 259; blocker: SHARED_SOURCE_NOT_RETRIEVED:STAT::66 Stat. 259
- orders_unblocked: 11; kind: one_source; action: Retrieve shared source EO::9337; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::9337
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 9; kind: one_source; action: Retrieve shared source EO::8417; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::8417
- orders_unblocked: 9; kind: one_source; action: Retrieve shared source EO::9515; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::9515

## Open asks from the newest handoff entries

- notes-astra.md: - **Asks:** @Claude: source-ladder SUMMARY omission of774 Opus requests and T2 estimator caveats remain. @Codex: actor attribution and named-body omissions remain documented; source-scope audits now explicitly enumerate searched roots and missing paths. @Owner: preserve current status and OPUS_MEDIA_NONE_CITED rules; later status reviews remain pending.
- notes-claude.md: - **Asks:** `@Owner`: a sanctioned route to the remaining CSC annual reports (1909-13, 1916-17, 1919-21, 1923-29) would reach most of the remaining 695 civil-service waivers.
- notes-codex.md: - **Asks:** None sent. Owner may choose the documented actions; no correspondence was sent on the owner's behalf.
- notes-sol.md: - **Asks:** None while validation is running.

## Failed jobs

- early-ranger-transcriptions: failed (https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39080984937)
- hathi-gpo-orders: unknown (no run link)
- source-ladder: failed (https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39186983698)

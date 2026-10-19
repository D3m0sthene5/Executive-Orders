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
- astra-source-retention: attempted: unavailable → 12; download_bytes: unavailable → 423969684; http_requests: unavailable → 13; requested: unavailable → 12
- census-completeness: ambiguous_same_date_pairs: unavailable → 5002
- claim-checker: claim_lines_found: 42 → 218; claims_all_checks_passed: 1 → 133; claims_checked: 42 → 218; claims_gate_passed: 1 → 133
- claim-drafts: drafts_whose_only_remaining_gaps_are_judgment_fields: 770 → 780; of_which_decided: 770 → 780; orders_with_any_conflict: 311 → 417
- clause-drafts: orders_not_segmented: 1672 → 1678; orders_processed: 6563 → 6569; orders_with_candidate_text: 6563 → 6569
- family-rules: saved_texts_scanned: 18681 → 30236
- hathi-gpo-orders: authenticated_originals: unavailable → 0; claim_kit_recognized: unavailable → 1531; federal_register_issues_used: unavailable → 37; government_bound_volumes_used: unavailable → 10
- indian-reservations-1912: acts: unavailable → 309; acts_before_1900: unavailable → 214; acts_with_a_lord_match: unavailable → 178; body_lines: unavailable → 11522
- isthmian-canal-1911: affected_document_leads: unavailable → 58; affected_targets_resolved: unavailable → 22; census_unnumbered_ids_not_comparable: unavailable → 19; contents_entries: unavailable → 177
- numbered-early-orders: books_held_scanned: unavailable → 17; books_new_fetched: unavailable → 12; fetch_failures: unavailable → 1; found_in_held_books: unavailable → 41
- official-fixity: carried_forward: 0 → 4999; checked_this_run: 4987 → 39; files: 4987 → 5038; orders_with_a_gpo_matched_file: 5013 → 5067
- readiness-tracker: ready_for_human_review: 1 → 130
- richardson-volumes: lord_entries_citing_richardson: unavailable → 369; wpa_entries_parsed: unavailable → 155
- source-ladder: attempts_logged: 43 → 12; bytes_downloaded: 784275283 → 210466245; distinct_new_source_hashes: unavailable → 10; exhausted_proposed_items: 4 → 2
- status-history: census_admissions: unavailable → 0; census_identities: unavailable → 14972; distinct_shared_source_units: unavailable → 79; editorial_edges_raw_span_verified: unavailable → 15660

## Top shared unlocks

- orders_unblocked: 440; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 286; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source USC::48 U.S.C. 863); blocker: SHARED_SOURCE_NOT_RETRIEVED:USC::48 U.S.C. 863)
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6964; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6964
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6910; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6910

## Open asks from the newest handoff entries

- notes-astra.md: - **Asks:** @Claude: preserve the now-working Opus pickup but fix SUMMARY to include from_opus_refetch (774) and total queue objects (947) for these pinned inputs; also read the linked T2 review before quoting census lower bounds. @Codex: no new action yet; PR24 is now merged, so its reservations/holds remain excluded here. @Owner: the brief file `research/plans/ASTRA_SIDE_BRIEF_2026-10-18.md` is absent on current main; this session is following the pasted brief. OPUS_MEDIA_NONE_CITED remains a block; no exception inferred.
- notes-claude.md: - **Asks:** `@Owner`: a sanctioned route to the remaining CSC annual reports (1909-13, 1916-17, 1919-21, 1923-29) would reach most of the remaining 695 civil-service waivers.
- notes-codex.md: - **Asks:** None sent. Owner may choose the documented actions; no correspondence was sent on the owner's behalf.
- notes-sol.md: - **Asks:** None while validation is running.

## Failed jobs

- early-ranger-transcriptions: failed (https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39080984937)
- hathi-gpo-orders: unknown (no run link)

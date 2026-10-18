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
- claim-checker: claim_lines_found: 42 → 218; claims_all_checks_passed: 1 → 133; claims_checked: 42 → 218; claims_gate_passed: 1 → 133
- claim-drafts: drafts_whose_only_remaining_gaps_are_judgment_fields: 770 → 780; of_which_decided: 770 → 780; orders_with_any_conflict: 311 → 417
- indian-reservations-1912: acts: unavailable → 309; acts_before_1900: unavailable → 214; acts_with_a_lord_match: unavailable → 178; body_lines: unavailable → 11522
- isthmian-canal-1911: affected_document_leads: unavailable → 58; affected_targets_resolved: unavailable → 22; census_unnumbered_ids_not_comparable: unavailable → 19; contents_entries: unavailable → 177
- readiness-tracker: ready_for_human_review: 1 → 130
- richardson-volumes: lord_entries_citing_richardson: unavailable → 369; wpa_entries_parsed: unavailable → 155
- source-ladder: attempts_logged: 43 → 69; bytes_downloaded: 784275283 → 327863094; found: 122 → 147; found_carried_forward: 87 → 122

## Top shared unlocks

- orders_unblocked: 472; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 286; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source USC::48 U.S.C. 863); blocker: SHARED_SOURCE_NOT_RETRIEVED:USC::48 U.S.C. 863)
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6964; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6964
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6910; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6910

## Open asks from the newest handoff entries

- notes-astra.md: No open ask recorded in newest entry.
- notes-claude.md: - **Asks:** - `@Owner`: review and approve pushing `wire-new-sources` (wiring + 176 claims) as one PR. - `@Astra`: before claiming an order in a family whose actor is EO 11708, 12534, 11811, 11812, 12110 or 9687, check `claude-2026-10-18-codif-b*.jsonl`; those targets are claimed here.
- notes-codex.md: No open ask recorded in newest entry.

## Failed jobs

- early-ranger-transcriptions: failed (https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39080984937)

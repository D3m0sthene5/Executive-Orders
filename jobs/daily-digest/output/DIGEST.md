# Daily research digest

New York date: 2026-10-19. Generated mechanically; all findings remain provisional.

## Tracker headline

# Readiness tracker

**Ready for human review: 135 of 14,972 orders (0.9%)**

An order is ready when the machines have finished every step it needs: each step is backed by a saved
source or a claim that passes the Stage 19 claim gate, or is recorded as searched to the end in
`research/readiness/EXHAUSTED.jsonl`. Human verification is a later, separate count.

Orders with a provisional YES/NO status: 3,359. The other 11,613 have not been researched yet.

## Steps finished (orders with a provisional status)

| Step | Done | Of | Share |
|---|---:|---:|---:|
| Has a provisional YES/NO status | 3,359 | 3,359 | 100.0% |
| Original text saved in the project | 2,312 | 3,359 | 68.8% |
| Complete inventory of the order's operative clauses | 183 | 3,359 | 5.4% |
| When and how it ended (NO), or what keeps it operating now (YES) | 139 | 3,359 | 4.1% |

## Changes since the previous day

Comparison snapshot: 2026-10-18; intervening runs may be absent.
- claim-checker: claim_lines_found: 218 → 223; claims_all_checks_passed: 133 → 138; claims_checked: 218 → 223; claims_gate_passed: 133 → 138
- readiness-tracker: ready_for_human_review: 130 → 135
- x1-class-engine: batches: unavailable → 128; modern_families_5_plus: unavailable → 153; pre1937_orders: unavailable → 8014

## Top shared unlocks

- orders_unblocked: 440; kind: machine_job; action: Re-fetch the PDFs Opus downloaded but left out of its release: add their URLs to research/readiness/FETCH_QUEUE.jsonl; blocker: OPUS_MEDIA_REFETCH_NEEDED
- orders_unblocked: 286; kind: agent_check; action: Check the page location of fr-originals and official-compilation finds marked medium/low confidence; blocker: ORIGINAL_FOUND_NEEDS_PAGE_CHECK
- orders_unblocked: 10; kind: one_source; action: Retrieve shared source EO::4314; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::4314
- orders_unblocked: 6; kind: one_source; action: Retrieve shared source EO::6868; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6868
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source USC::48 U.S.C. 863); blocker: SHARED_SOURCE_NOT_RETRIEVED:USC::48 U.S.C. 863)
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6964; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6964
- orders_unblocked: 3; kind: one_source; action: Retrieve shared source EO::6910; blocker: SHARED_SOURCE_NOT_RETRIEVED:EO::6910

## Open asks from the newest handoff entries

- notes-astra.md: No open ask recorded in newest entry.
- notes-claude.md: - **Asks:** `@Owner`: (1) risk-tiered review stays off (flag `X1_RISK_TIERED_REVIEW`, default off) until you decide; (2) a route to CSC annual reports / Official Register would date the 1,490 one-person waivers. `@Codex` / `@Sol` (claim-kit): an own-terms end mechanism (EO 5763, 5930 blocked only by this) and locating the EO 7968 and EO 5707 provisions in dossiers (6 rows). `@Astra`: EO 5874 is recited by EO 5881 but is not in the identity universe; check as a census gap. Anyone: the 5,297 `status_first` rows need a provisional-status path before X1 sheets help.
- notes-codex.md: - **Asks:** None sent. Owner may choose the documented actions; no correspondence was sent on the owner's behalf.
- notes-sol.md: - **Asks:** None while validation is running.

## Failed jobs

- early-ranger-transcriptions: failed (https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39080984937)
- hathi-gpo-orders: unknown (no run link)

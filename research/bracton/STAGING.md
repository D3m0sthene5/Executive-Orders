# Bracton staging receipt — 2026-11-08

## State

- Base: main `883bd8f78f12ac4c1cf6625d74a20f4b56480360` after the new source-ladder result. The frozen claim-kit corpus was last published from main `67b6adeeb902d91a5ead9e4684c09207c442f87a` and reports a successful run.
- Budget: no dollar cap under the owner's 2026-11-08 exhaustive #1–#9 goal. Running model cost is in `COST.md`. No Bracton producer or reviewer model call has started. Cujas is a separate wave.
- Phase: evidence and assignment staging only. No claim, status, census, codebook, human review, or certified count changed. Certified count remains 0.
- Timing: the owner chose staging now and Claude-family blind review after the Monday, 2026-11-09, 6 PM ET usage reset. Recheck main, reservations, packet freshness, and the dispatch gate immediately before production.

## Refreshed ranking

`plan/PLAN.md` records the earlier capped pilot. The current `jobs/bentham/output/PLAN.md` is the uncapped recomputation. The historical recovery list contained 48 mechanically rejected orders, but the current tracker already marks 39 ready. `jobs/bentham/candidates.py` now filters that recovery action to the 9 still not ready. Ranks #7–#9 are recovery (9), one-step-away correction (223), and YES/FR production (338). Each production action must pass its own gate.

Montfaucon (`sol/montfaucon-2026-11-08`) owns ranks #10 and #13 and all page-check records. Sol writes claims only. A #1–#9 order held solely for a missing page check is recorded as blocked on Montfaucon with its order and source, then retried in a later batch after that check lands on main. Sol excludes all 193 identities in `research/photius-193-recheck/compare_193.csv` while Cujas is active, including recovery EO:8538 and EO:8907.

## Disjoint packets

| Packet | Orders | Frozen packet SHA-256 | Fresh offline dispatch | Scope |
|---|---|---|---|---|
| `pilot-b01/packet-v1` | EO:10010, EO:10923, EO:10944 | `409cb1272600d3158faf694660e352e5774acd5b921b750f9230f577b86fada6` | `dispatch-v3.json`: pass, 3/3, 14 distinct custody checks | One-step-away board corrections, isolated replacement proposals for Justinian R3 claims; owner adoption remains separate. |
| `pilot-y02/packet-v1` | EO:10538 | `528349db40c2b6789dad45e84664114a7dfa956798fa5611833545cef8129948` | `dispatch-v2.json`: pass, 1/1, 2 distinct custody checks | Claim-ready YES/FR pilot, reserved to `sol-bracton` in `CLAIM_KIT_LOCK.json`. |

The Cujas c01/c02 Photius batch uses different identities; its published branch report lists c01 as 21 filed, with c02 paused before review. Cujas's source-ladder job advanced main while these packets were staged. The board packet has no ownership transfer or active order lease; acquire leases before its producer assignment and confirm no intervening work.

`pilot-y01/packet-v1` preserves an exploratory five-order YES packet. All five were source blocked before acquisition. No producer saw it and no reservation was made for its other four orders. `pilot-y02` is the selected one-order subset with a passing fresh check.

## Source custody and handoff

The first board dispatch check failed on missing exact original bytes. Nine public PDF files from govinfo and the National Mediation Board reproduced their frozen hashes. Four changed APP pages could not be reproduced from their live URLs; their fixed Common Crawl WARC ranges did reproduce the frozen hashes. Those four exact response bodies and WARC pointers are committed under `jobs/bracton-source-custody/`. The ten verified PDFs (nine board, one YES) are held in local `jobs/fr-originals/fr-originals-cache/` and `jobs/source-ladder/source-ladder-cache/` paths named by their existing `SOURCES.jsonl` records. They are untracked. A fresh checkout must re-fetch and hash-check them before dispatch; never treat this receipt as portable custody.

The Valla v2 schema acceptance fix is required for `kit.py prepare` with existing Justinian board retags. Its 35 tests pass. Bentham candidate/planner tests pass (8+5). Full legal source analysis, board report fact/date verification, current-law predicate, safeguards, blind controls, both independent reviewer verdicts, actual claim checker, tracker delta, and Bentham gates are pending. Source matches and an offline dispatch pass are preparation checks only.

## Monday continuation

1. Pull the latest main and Cujas outcome. If any shared input changes, prepare a new immutable packet; never renew a stale seal. Confirm the Sol YES lock and acquire short-lived Kean leases for dispatched orders.
2. Re-run `kit.py dispatch-check` on exact intended members. Ensure all selected later-event and current-law sources have custody, not just mandatory originals.
3. Follow Bentham rank and diagnostic gate: triage the nine still-not-ready recovery cases, then run a small board correction pilot under the owner board rule. Continue through the full YES stratum, recording each member's outcome.
4. Use a different model family for blinded independent reviews, with planted controls. File only both-upheld claims through `kit.py complete --publish` and report actual checker and tracker changes. Do not represent AI review as human certification.

## Exhaustive-goal update, 2026-11-08

The `sol/bracton-2026-11-08` branch supersedes this receipt's earlier branch and $300 plan. `BASELINE.csv` lists all 570 current members of ranks #7–#9 (9 recovery, 223 one-step, 338 YES/FR), with exactly EO:8538 and EO:8907 excluded under Cujas. `RECOVERY_TRIAGE.csv` records the nine recovery dispositions. `BLOCKED_MONTFAUCON.csv` names three recovery orders and exact FR source issues whose page reading is the only current route around an OCR/checker block. No page-check record was made here.

The first targeted source-ladder Run jobs invocation is [42510818817](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42510818817), with nine selected source identities in `ACQUISITIONS.csv`. Its source outcomes must be read from the published `jobs/source-ladder/output/STATUS.json`, `RESULTS.csv`, and `SOURCES.jsonl`; the run was still executing when this update was written. A workflow-file push also started a separate valla/kean/bentham/example-hello run on this branch; remove its incidental branch outputs before a PR. Keep the target run's pinned input stable until publication.

`BOARD_REPORT_STATUS.csv` records 109 current report-source records and 37 absent ones across Haloander's 146 R3 report-date cases; all 146 have queue requests for report-date sources. This is source-record presence, not verified PDF custody or page authentication. A next targeted source-ladder run can use `queue:EO:<number>:` prefixes for the 37 absent cases. `source-requests-v2.jsonl` and `SOURCE_DISCOVERY.md` hold three direct govinfo issue leads for EO:10053, EO:10578 and EO:11633; the append-only queue changes await the next run. EO:8947 still needs an official compilation or archival original.

The coordinator's Codex usage is unmetered in this environment. `COST.md` reports measured worker cost separately and will be updated after each result batch. The sanitized Bentham usage output has an explicit Bracton Claude-session prefix and zero calls so far; the unfiltered command's unrelated transcripts were discarded.

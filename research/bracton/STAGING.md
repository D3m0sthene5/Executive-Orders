# Bracton staging receipt — 2026-11-08

## State

- Base: main `883bd8f78f12ac4c1cf6625d74a20f4b56480360` after the new source-ladder result. The frozen claim-kit corpus was last published from main `67b6adeeb902d91a5ead9e4684c09207c442f87a` and reports a successful run.
- Budget: $300 API-equivalent ceiling for the campaign. No Bracton producer or reviewer model call has started. Bracton worker spend is therefore zero; coordinator usage is unmeasured. Cujas has a separate capped batch and is excluded from this budget receipt.
- Phase: evidence and assignment staging only. No claim, status, census, codebook, human review, or certified count changed. Certified count remains 0.
- Timing: the owner chose staging now and Claude-family blind review after the Monday, 2026-11-09, 6 PM ET usage reset. Recheck main, reservations, packet freshness, and the dispatch gate immediately before production.

## Refreshed ranking

`plan/PLAN.md` is Bentham's $300 recomputation. The historical recovery list contained 48 mechanically rejected orders, but the current tracker already marks 39 ready. `jobs/bentham/candidates.py` now filters that recovery action to the 9 still not ready. The top measured agent actions are recovery (9, estimated $3.60) and one-step-away correction (223, estimated $144). YES/FR production is rank 9 and must pass its own gate and remaining-budget check before spending.

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
3. Follow Bentham rank and budget gate: triage the nine still-not-ready recovery cases, then run a small board correction pilot under the owner board rule. Keep YES staged until its ranking and measured gate justify spending.
4. Use a different model family for blinded independent reviews, with planted controls. File only both-upheld claims through `kit.py complete --publish` and report actual checker and tracker changes. Do not represent AI review as human certification.

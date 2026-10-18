# EO12553 package B: legal production findings

Owner: producer `produce_12553_b`; independent reviewer: `review_12553_b`.
Assignment: decided EO12553-family targets numbered 10000 or greater. Kickoff
main: `a12a5c73adebdf5e1ac75c9edd36c9ce9c7ca8be`.

The first five orders have 18 exact saved-OCR clause blocks in partial claims.
None is ready for human review. EO12553 expressly removes orders already
"no longer necessary"; its 1986 cleanup revocation does not establish when
the earlier duties first ended. The producer read its complete seven-page
saved official OCR, including the target list. Published official fixity and
visual original-page review remain open. No rule custody flag was changed.

## Pilot: actual legal judgments

| Order | Inventory | Material first-cessation issue |
|---|---|---|
| EO12495 | Four complete sections, including establishment, reporting, standstill, expiration | Actual report submission ends board; standstill independently lasts 60 days after report. Reporting deadline cannot prove actual submission. |
| EO12492 | Four complete sections | Same event-dependent separation of board and standstill. |
| EO12491 | Four complete sections | Same event-dependent separation of board and standstill. |
| EO12486 | Four complete sections | Board effective August 25, 1984, despite August 24 signing. Standstill has 120-day outer duration; board termination depends on actual report. Earlier agreement or other ending must be examined. |
| EO12482 | Two amendments | Amendment (a) changes substantive functions; (b) changes the parent committee sunset to December 31, 1984, unless sooner extended. Need parent EO12426 and extension history. |

Independent pilot review found one substantive failure in five: producer had
mistakenly assigned December 23, 1984 as EO12486 section 3's first end.
That calculation establishes a conditional outer endpoint, subject to earlier
agreement or another ending. The producer stopped scaling at 20% failure,
cleared the date and every unverified original_representation, and retained
all missing-evidence gaps. Independent rereview passed the corrected partial
method and matched 18/18 quoted blocks to saved OCR. The tracker must receive
no new complete orders from this pilot.

`STRUCTURAL_GATE.json` records the remaining structural failures. The first
offline claim-checker invocation stopped before checking any claims because
the local hydration lacked the census CSV. Its absence is an environment
input problem, not evidence exhaustion. No second claim batch was generated
while waiting for the required post-batch checker report.

## Additional evidence read while waiting for checker

Each following order was started from its one bundle fetch, then the relevant
complete saved original text was read. These are analytical observations,
not additional committed lifecycle claims.

| Order(s) | Consequence for later review |
|---|---|
| EO12397; EO12402 | Reporting deadline changes for the Social Security Reform commission. EO12402 saved OCR heading reads "12432" while the record says 12402; identity needs visual resolution. |
| EO12398; EO12429; EO12447; EO12455 | Shared cost-control committee extension chain: June 30, October 30, December 31, 1983, and January 31, 1984 sunset language. Successive amendments displace earlier dates; no isolated sunset can establish first cessation. EO12398 also changes membership to 170. |
| EO12405 | Distinct report-triggered board termination and report-plus-30-day standstill. |
| EO12409; EO12463 | EURATOM inherited-period extensions to March 10, 1984 and March 10, 1985; read the inherited authority and later extensions before treating a printed date as first cessation. |
| EO12414 | Report-plus-60-day standstill; attachment defines nine labor organizations and must remain part of the scope. |
| EO12415 | Drunk-driving commission sunset amendment to December 31, 1983; parent order and other amendments still matter. Saved extraction includes unrelated subsequent orange regulations, which are outside the order. |
| EO12427 | Four sections establish and administer the private-sector advisory council, including travel expenses and a two-year sunset unless extended. Do not lose accrued expense leads. |
| EO12434 | Alaska Railroad rates order expressly preserves existing EO11107 rates and addresses contracts; this is a substantive savings lead. OCR of sections 2/3 is noisy and requires page comparison. |
| EO12440; EO12457 | Industrial-competitiveness commission membership goes from 30 to 35; EO12457 also sets a conditional December 31, 1984 sunset. Raw EO12457 OCR interleaves "President" from amendment (a) after (b); do not silently repair the quote. |
| EO12442 | Indian Reservation Economies commission report deadline plus termination 30 days after actual transmission, unless extended; deadline is distinct from actual transmission. |
| EO12449 | Central America commission report deadline is February 1, 1984; report deadline alone does not establish commission expiration. |
| EO12476 | Renames a binational commission and broadens functions as well as extending sunset; all three amendments need separate lifecycle treatment. |
| EO12480; EO12481 | Board effective June 20, 1984; 120-day standstill and report-triggered board termination remain separate. Saved EO12481 extraction includes neighboring regulations after the order. |

## Source requests and telemetry

`FETCH_QUEUE.proposed.jsonl` contains six known official PDF/page/fixity
requests and four actual-board-report identification requests for coordinator
integration into the shared queue. The report requests explicitly lack known
URLs; they are identification work, never exhaustion. No external source was
fetched directly, and no HeinOnline automation was used.

Actual model billing tokens are unavailable in the agent interface. No
estimated startup-payload token count is represented as actual consumption.
The package's initial saved-source snapshot was created at
2026-10-18T00:12:54Z; all earlier required-document and source retrieval time
precedes that timestamp. An end timestamp and measured interval should be
recorded on final packaging; that interval is a partial observation, not total
session time or time per complete order.

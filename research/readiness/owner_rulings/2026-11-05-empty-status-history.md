# Owner decision: the claim kit may start an order with an explicit empty status history (2026-11-05)

On 2026-11-05 at 21:54 EST the owner, Danny, answered Kean ask A-20261105-1 in chat: "may the kit start an order
whose search found no later event? is yes, as long as thats noted".

## The ruling

The claim kit may prepare, freeze and review an undecided order for which `jobs/status-history` located no dated
status observation and no later event. The order then carries an **explicit empty history** instead of being
refused with "no dated history located", on these conditions:

- The empty history is noted wherever the order's work is read: the frozen history packet carries
  `empty_history: true`, the flag `EMPTY_HISTORY_STARTED_UNDER_OWNER_RULING_2026_11_05` and a notice stating what was
  searched and that nothing was found; the dossier's `missing` list says so in plain words; and a status proposal
  built on it states its `history_basis`.
- An empty history is not evidence that the order is in force or has ended. Any status proposal for such an order
  rests on the order's own terms and the bounded later-source searches recorded in its dossier, and the reviewers
  judge it on that basis.
- Status adoption, the codebook, the census and the certified count are unchanged: proposals still need the owner's
  adoption through the authoritative process. Certified: 0.

## Why

The Herschel survey (`research/herschel/REPORT.md`) found 5,918 of the 10,681 undecided orders without a dated
history, 5,449 of them from 1907 to 1936, because the 1989 Office of the Federal Register disposition tables do not
reach most pre-1937 orders. The WPA list of orders 1 to 8030 names only 111 of them as later amended or revoked, so no
held source would fill the gap: most of these orders were simply never expressly revoked.

## Where it is carried out

`jobs/status-history/history.py` (`show` returns the explicit empty packet), `jobs/claim-kit/status_overlay.py`
(the dossier note and the proposal's `history_basis`), with tests in both jobs. Kean decision
D-20261105-empty-history; ask A-20261105-1 answered.

# Questions waiting for the owner

Generated from `jobs/kean/register/asks.jsonl` by `python3 -I jobs/kean/kean.py brief`; do not edit by hand.
Answer with `kean.py answer --id ID --answer TEXT`.

## A-20261108-lean-main (2026-11-08, claude)

Should bulk job outputs, data and attempt receipts (~163,000 of main's 194,167 files) be packed into fewer files or moved out of main's tree, accepting that path-based pins and citations must then be re-issued?

*Why:* ChatGPT and claude.ai GitHub connectors and cloud clones see main's whole tree; .ignore, the Claude hook and Ariadne do not reach them. Packing or moving changes evidence paths that pins and certificates cite, so it needs the owner's ruling. No action until answered.

Sources: `.ignore`

## A-20261110-respondendi-standing-rule (2026-11-10, Claude)

Approve jobs/respondendi-adoption/RULE.md (sha256 85a990233d5cad3fb30870e4b80ed0c6102ae6232f7be595b28d545750250934) as a standing adoption rule, so that undecided-route status proposals in its lot are adopted without a per-order owner decision? The lot: express, named, unqualified whole-order revocations by a later order or proclamation (687 undecided orders have such a held ending on an acceptable original). Each order still needs the full route (admission in a Bentham action, independent status review accepted, both blind arms upholding the exact claim, at least 2 typed planted controls caught by every arm, the checker passing), and nothing reaches the ledger until a person or another model family has audited it: every member until the 95% upper bound on the error rate is 5% (59 audits with no confirmed error), then 20% of each lot. Disagreements are adjudicated; 2 confirmed errors in 59 audits stop the rule until you resume it; at most 60 orders a lot, 300 a week, one lot a day; any adoption can be reversed; you can suspend the rule at any time. Statuses stay provisional AI hypotheses and human-certified stays 0; count-changing pull requests still need your merge. Recommended: yes. To approve, the agent recording your answer commits an owner-ruling file and a Kean decision that both contain respondendi-rule-sha256:85a990233d5cad3fb30870e4b80ed0c6102ae6232f7be595b28d545750250934 (different numbers mean a new hash, which that agent computes).

*Why:* Every undecided-route adoption so far (16 orders in 3 decisions: Dorotheus 7, Haloander 3, Papinian 6) followed the same standard and none that met it was declined; per-batch asks add owner work and latency, not information. The tool (jobs/respondendi-adoption/respondendi.py) refuses every write until this exact hash is approved.

Sources: `research/excavator/claude-respondendi-2026-11-10/REPORT.md`, `jobs/respondendi-adoption/RULE.md`

## A-20261110-respondendi-standing-rule-v2 (2026-11-10, Claude)

Approve Respondendi rule version 2 (jobs/respondendi-adoption/RULE.md, sha256 e15ae99b3e5ae800e18d331cb2b5fe6ae233aa36052b13f512b86eabbec01423) as a standing rule covering every kind of undecided order, so that qualifying status proposals are adopted after the audits it requires, with no per-order or per-kind owner decision? It supersedes A-20261110-respondendi-standing-rule (v1, one lot). Kinds: express named revocation and own terms (active now); spent on issue including amendment-only orders (opens when F5 merges); YES with a positive current source (opens when F3 merges); the Ulpian life-bound lot you approved in D-20261110-ulpian-life-bound (opens when PR #271 is on main); a working-text basis for each (opens when F6 merges). A kind opens only when GitHub's main declares its route in the claim kit's UNDECIDED_ROUTES, and starts on its own probation: every member audited by another model family or you until the 95% upper bound on its error rate is 5% (59 audits with no confirmed error), then 20%; YES and spent-on-issue are always audited in full. Two confirmed errors in 59 audits stop a kind (one for YES) until you resume it; an order with an error never returns; reversals count as errors; at most 60 orders a lot, 300 a week, one lot a day. Measured reach on main: 468 orders today, 1,484 once PR #271, F3, F5 and F6 merge (upper bounds). Two hostile review rounds shaped it (REPORT.md section 7). Statuses stay provisional AI hypotheses; human-certified stays 0. Recommended: yes. To approve, the agent recording your answer merges an owner-ruling file and a Kean decision whose ruling is exactly: Owner approves respondendi-rule-sha256:e15ae99b3e5ae800e18d331cb2b5fe6ae233aa36052b13f512b86eabbec01423

*Why:* The owner asked (2026-11-10) for one approval covering every kind of undecided order instead of per-batch adoption asks; v1 reached only 620 orders. The tool refuses every write until this exact hash is approved on GitHub's main.

Sources: `jobs/respondendi-adoption/RULE.md`, `research/excavator/claude-respondendi-2026-11-10/REPORT.md`, `research/excavator/claude-respondendi-2026-11-10/KINDS.json`

## A-20261110-ulpian-l1r-correction (2026-11-10, Claude)

Extend the Jacquard L1 correction to wave 2? 582 L1R provisional NO statuses (PR 119, same L1 card and its 'at least 14' premise, which you declined in D-20261110-ulpian-no-floor) were adopted; 527 are dated on or after 1904-05-03 and 26 have no exact date, plus 3 undated wave-1 L1 rows (EO 940, 1596, 1604). Recommended: yes, read them by the same blind two-arm method with planted controls (research/ulpian/jacquard-l1-correction), keep those whose own text quotes a sufficient fact and return the rest by a correction PR you merge, in batches of at most 100. Alternatives: ratify the premise for wave 2 only (inconsistent with D-20261110-ulpian-no-floor), or leave them.

*Why:* The 42-row wave-1 reading kept 9 and returned 33 (21% kept). At that rate about 110 of the 527 would stay and about 420 would return to undecided. Cost of the 42: about 196k worker tokens (two arms) plus coordination, so the 556 would cost roughly 2.6M worker tokens. Until read, those statuses rest on a basis you declined.

Sources: `research/ulpian/jacquard-l1-correction/README.md`, `research/excavator/jacquard-2026-10-31-w2/README.md`

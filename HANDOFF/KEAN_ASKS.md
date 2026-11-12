# Questions waiting for the owner

Generated from `jobs/kean/register/asks.jsonl` by `python3 -I jobs/kean/kean.py brief`; do not edit by hand.
Answer with `kean.py answer --id ID --answer TEXT`.

## A-20261108-lean-main (2026-11-08, claude)

Should bulk job outputs, data and attempt receipts (~163,000 of main's 194,167 files) be packed into fewer files or moved out of main's tree, accepting that path-based pins and citations must then be re-issued?

*Why:* ChatGPT and claude.ai GitHub connectors and cloud clones see main's whole tree; .ignore, the Claude hook and Ariadne do not reach them. Packing or moving changes evidence paths that pins and certificates cite, so it needs the owner's ruling. No action until answered.

Sources: `.ignore`

## A-20261110-larrey-soft-probe (2026-11-10, claude)

Larrey keeps 1,014 undecided orders out only on the soft gate later_order_text_held (fitted on 28 failures, 0 of 33 successes lost). May a coordinator spend about 15-20 USD on one 30-order probe of soft-gated orders (LARREY_LEVEL=hard) to measure its lost yield before it is relied on at scale?

*Why:* Gated-out orders are never dispatched, so the soft gate's lost yield cannot otherwise be measured; the independent review asked for this before enforcing it by default. Until answered the gate stays on (no paid discovery of missing inputs).

Sources: `jobs/larrey-triage/README.md`

## A-20261110-respondendi-standing-rule (2026-11-10, Claude)

Approve jobs/respondendi-adoption/RULE.md (sha256 85a990233d5cad3fb30870e4b80ed0c6102ae6232f7be595b28d545750250934) as a standing adoption rule, so that undecided-route status proposals in its lot are adopted without a per-order owner decision? The lot: express, named, unqualified whole-order revocations by a later order or proclamation (687 undecided orders have such a held ending on an acceptable original). Each order still needs the full route (admission in a Bentham action, independent status review accepted, both blind arms upholding the exact claim, at least 2 typed planted controls caught by every arm, the checker passing), and nothing reaches the ledger until a person or another model family has audited it: every member until the 95% upper bound on the error rate is 5% (59 audits with no confirmed error), then 20% of each lot. Disagreements are adjudicated; 2 confirmed errors in 59 audits stop the rule until you resume it; at most 60 orders a lot, 300 a week, one lot a day; any adoption can be reversed; you can suspend the rule at any time. Statuses stay provisional AI hypotheses and human-certified stays 0; count-changing pull requests still need your merge. Recommended: yes. To approve, the agent recording your answer commits an owner-ruling file and a Kean decision that both contain respondendi-rule-sha256:85a990233d5cad3fb30870e4b80ed0c6102ae6232f7be595b28d545750250934 (different numbers mean a new hash, which that agent computes).

*Why:* Every undecided-route adoption so far (16 orders in 3 decisions: Dorotheus 7, Haloander 3, Papinian 6) followed the same standard and none that met it was declined; per-batch asks add owner work and latency, not information. The tool (jobs/respondendi-adoption/respondendi.py) refuses every write until this exact hash is approved.

Sources: `research/excavator/claude-respondendi-2026-11-10/REPORT.md`, `jobs/respondendi-adoption/RULE.md`

## A-20261110-respondendi-standing-rule-v2 (2026-11-10, Claude)

Approve Respondendi rule version 2 (jobs/respondendi-adoption/RULE.md, sha256 e15ae99b3e5ae800e18d331cb2b5fe6ae233aa36052b13f512b86eabbec01423) as a standing rule covering every kind of undecided order, so that qualifying status proposals are adopted after the audits it requires, with no per-order or per-kind owner decision? It supersedes A-20261110-respondendi-standing-rule (v1, one lot). Kinds: express named revocation and own terms (active now); spent on issue including amendment-only orders (opens when F5 merges); YES with a positive current source (opens when F3 merges); the Ulpian life-bound lot you approved in D-20261110-ulpian-life-bound (opens when PR #271 is on main); a working-text basis for each (opens when F6 merges). A kind opens only when GitHub's main declares its route in the claim kit's UNDECIDED_ROUTES, and starts on its own probation: every member audited by another model family or you until the 95% upper bound on its error rate is 5% (59 audits with no confirmed error), then 20%; YES and spent-on-issue are always audited in full. Two confirmed errors in 59 audits stop a kind (one for YES) until you resume it; an order with an error never returns; reversals count as errors; at most 60 orders a lot, 300 a week, one lot a day. Measured reach on main: 468 orders today, 1,484 once PR #271, F3, F5 and F6 merge (upper bounds). Two hostile review rounds shaped it (REPORT.md section 7). Statuses stay provisional AI hypotheses; human-certified stays 0. Recommended: yes. To approve, the agent recording your answer merges an owner-ruling file and a Kean decision whose ruling is exactly: Owner approves respondendi-rule-sha256:e15ae99b3e5ae800e18d331cb2b5fe6ae233aa36052b13f512b86eabbec01423

*Why:* The owner asked (2026-11-10) for one approval covering every kind of undecided order instead of per-batch adoption asks; v1 reached only 620 orders. The tool refuses every write until this exact hash is approved on GitHub's main.

Sources: `jobs/respondendi-adoption/RULE.md`, `research/excavator/claude-respondendi-2026-11-10/REPORT.md`, `research/excavator/claude-respondendi-2026-11-10/KINDS.json`

## A-20261110-ulpian-named-war (2026-11-10, Claude)

Count service in a named war as a dated fact? Eight returned L1R orders (EO 437, 444, 453, 411 and four others; list in research/ulpian/jacquard-l1r-correction/COORDINATOR.jsonl) say the person is a veteran of the Civil War (1861-1865) or the Spanish war (1898) but print no date. RULE.md v2 section 2, which you approved, counts only facts whose date the text states, so they were returned. Recommended: yes, add to the lot rule (a new RULE.md version and hash) that service in a named war ending before 1904-05-02 places the person's birth no later than the war's last year (Civil War 1865-12-31; Spanish-American War 1898-12-31); then re-tag these 8. Alternative: leave them undecided.

*Why:* Such a person was certainly born before 1904; the rule's letter, not the evidence, keeps them open. 8 orders now; the same wording likely recurs in later one-person readings.

Sources: `research/ulpian/jacquard-l1r-correction/README.md`, `jobs/ulpian-outer-bound/RULE.md`

## A-20261111-film709-count (2026-11-11, Claude)

NYU Film 709 (11 reels, EO 1-7403) is free to scan yourself at Bobst on the ScanPro stations, and NARA New York is closed. Count your own Film 709 scans as the R38 microfilm witness, like M1118? Bytes stay private (owner inbox, as with Hein); only hashes and page facts go public. Counting starts only after a pilot reel shows Film 709 matches the State Department file copy, compared frame by frame against a held NARA image.

*Why:* A-20261106-dagron-nyu (answered no on 2026-11-09, 'revisit only if M1118 acquisition fails') keeps Film 709 uncounted. M1118 is not viewable in NYC, its roll list is not online, and digitized rolls cost about 25 each. 1,533 orders in the film's range have no located official source.

Sources: `research/dagron/README.md`

## A-20261112-cis-unnumbered-check (2026-11-12, Claude)

Check the 875 CIS unnumbered executive orders that fall on dates with no known order (research/graunt-census-audit-2026-11-12/cis-kaufman/CIS_UNNUMBERED_EO_GROUPS_PRE1937.csv) for admission to the unnumbered series? A pilot of 30 on the CIS fiche at Bobst or ProQuest would show how many are presidential, distinct and not departmental, before any bulk work.

*Why:* CIS (1987) is an independent, more complete frame than Lord; if most of the 875 are presidential, the identified unnumbered series grows by up to about 1,600.

Sources: `research/graunt-census-audit-2026-11-12/cis-kaufman/README.md`

## A-20261112-lind-stage0 (2026-11-12, Claude)

After the claim-kit rebuild publishes, may Claude run one Lind stage-0 batch: 30 undecided orders (15 passing every Larrey gate, 15 passing only the hard gates, drawn by research/lind/stage0/draw.py), Papinian configuration, one pooled review set, hard cap $35 list-price allowance? It also needs an Augur review of research/lind/stage0/WAVE.json by another model family (Codex or Astra) or you, bound to its hash. This replaces A-20261110-larrey-soft-probe.

*Why:* It decides whether the soft gates exclude worthwhile work (2,073 orders) and whether the rebuilt kit lifts undecided yield; every result row has an action in DECISION_2026-11-12.md section 6.3. Cost: about $22-26 expected, $35 cap, plus your adoption decisions.

Sources: `research/lind/DECISION_2026-11-12.md`

## A-20261112-lind-stage0-v2 (2026-11-12, Claude)

Approve the Lind stage-0 pilot exactly as research/lind/stage0/WAVE.json (sha256 f2b07a1923354e3484a9f510a3419fbb2d882150ce68cce9dc02f6ff0d3b8a1d): 30 undecided orders, 15 drawn at random from the 3,447 that pass every Larrey gate and 15 from the 1,834 that pass only the hard gates (never attempted), hard gates only, Papinian configuration, one pooled blind review set, cap $35 list-price allowance all-in (setup 1, coordination 6, production 7, review 17, correction 2, integration 2), with the stop and decision rules in DECISION_2026-11-12.md section 7.3? Approving also commits you to one adoption decision on the batch's upheld proposals (as A-20261110-papinian-adopt-u01b), so the endpoint is ready (6/6), not proposals. Preconditions: merge PR #302 then #301; the main run of larrey-triage and bentham publishes; an Augur review of the plan by another model family (Codex or Astra) or you, bound to that hash. Supersedes A-20261112-lind-stage0 and A-20261110-larrey-soft-probe.

*Why:* It measures whether the repaired workflow produces ready dossiers cheaply, and whether soft-filtered orders are worth processing, each group reported separately; every outcome, including inconclusive, has a stated next spending decision.

Sources: `research/lind/stage0/WAVE.json`

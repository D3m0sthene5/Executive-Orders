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

# Nine serial retirement exemptions produced from Namier-supplied packets (2026-10-28)

Producer: Claude (agent `claude-namier-20261028`, Anthropic family). Reviewer: a separate Claude context
(`claude-namier-reviewer-20261028`, same family, disclosed; `same_family_separate_context`). No human
review, no certification, no status change. Everything below is a research proposal awaiting independent
human review; the certified whole-lifecycle count stays 0.

## Why these nine

Three chains found by `jobs/namier` (Kean F-20261028-7): Harry O. Bailey (EO 6088 → 6998 → 7597), Jacob L.
Nuber (EO 6013 → 6615 → 6974) and Carleton W. Sturtevant (EO 6577 → 6773 → 7217). The 2026-10-28 probe
(F-20261028-4) had blocked four retirement exemptions because their extension orders were not in the packet.
After Namier and the claim-kit printed-reference fix (F-20261028-8) regenerated on the runner (run
40770547716), `kit.py prepare` put every chain member's text into each dossier as an actor context, labelled
`cited by number, no change provision located: EO:X` or `names the same person (name-match lead, read before
use): EO:X`. The producer searched nothing; every later order it needed was in `packet/READ.md`.

## What was decided

Each order is one command: a named employee is exempted from compulsory retirement under section 204 of the
Legislative Appropriation Act of June 30, 1932, "and continued in the service until <date>". Each ends by its
own terms on the stated date, recorded inclusive with the exclusive reading stated as the alternative (owner
ruling 2026-10-21, until dates). Each later "further exemption" of the same person is recorded as a later
event with its own date and quote; none revokes, amends or shortens the earlier order (each recites it and
grants a new term that overlaps the earlier order's last days). EO 6013 names two persons; only Nuber's chain
continues, and nothing held names Edwin H. Pearson again. The machine term leads dated at a recited birthday
(EO 6615, 6773, 6974: "who was 70 years of age on ...") were read and set aside; the operative until-date
governs. The OFR disposition note calling EO 7597 an amendment of EO 6088/6998 was read against the texts,
which amend nothing. Savings: `transferred_or_accrued` (service and pay already earned); no continuing duty,
office or rule. Searches judged adequate: U.S. Code and eCFR (0 hits), the OFR catalog (pre-1937 coverage
warning stated), and Namier's complete held-text search for each person's name (`SEARCH_COVERAGE.csv`),
which found exactly the chain members and nothing else. Whether any of the three separated on or before the
last stated date is in no held source and is not asserted.

Decision sheets: `packet/decisions.csv`, `packet/clauses.csv`, `packet/RATIONALES.json`. Assembled claims:
`packet/applied-v3/CLAIMS.proposed.jsonl` (7); `packet/applied-v3/AUDIT.json` records the two blocked members.

## Review

Eight opaque cards (`packet/review/ASSIGNMENT.json`): the seven assembled claims and one planted control, a
copy of the EO 6615 claim with `whole_order_end.date` and `first_end.date` moved to the recited birthday
1935-02-26 while the quote and reasons kept 1935-02-28 (`packet/review/SEED_RECEIPT.json`). The reviewer read
every cited held text, tested for earlier endings, and sealed `BLIND_REVIEW.jsonl` (sha256
228b4ea0836b8022c72fd2e52d6757096fa7161a5f81dc7b6bdbaaf1d02680fa, `BLIND_SEAL.json`): 7 genuine upheld, the
control rejected for the date defect. After reveal: `CONTROL_ADJUDICATION.json` (caught, strict) and
`AFTER_REVEAL.jsonl` (EO 6615 genuine, `upheld_after_reveal`, card re-hashed). Private cards and the key stayed
outside the repository.

## Completion and the blocker it exposed

`kit.py complete COMPLETION.json --write complete-v1` (no `--publish`): 9 attempted, 7 submitted, 2 blocked,
1 control placed and caught, source review upheld for all 7, **0 eligible**. Every one of the 7 was
`rejected_mechanical` on one check only: `source_held: custody_record_only` (36 rows; `complete-v1/EXCEPTIONS.json`,
`complete-v1/checker/CLAIM_CHECKS.csv`). The American Presidency Project pages these transcriptions come from
were hashed when read but their bytes are kept in no committed place, so the checker cannot re-hash them and
never sets `all_checks_passed`. The same will stop every transcription-dependent whole-case claim in the
project (about 4,644 orders are held only as transcriptions). `jobs/cassiodorus` was written to keep those
page bytes from the recorded Common Crawl and Wayback captures; it must run on GitHub's runner (the agents'
container cannot reach the archives). After it runs, `complete` is to be rerun from the same manifest.

## The two blocked members

EO 6773's APP page exists in two held copies with one page sha256: the `app-executive-orders` text ends with
the date line "June 30 1934." and the `clause-drafts` re-cut drops it, because `segment.py`'s `DATE_LINE`
requires a comma. The checker searches the clause-drafts copy for that sha, so a whole-text quote fails
`quote_verbatim` ("first 223 of 226 words found"). EO 6577 cites EO 6773 as its later event and is blocked
with it. Research on both is complete. 76 APP pages share this defect
(`CLAUSE_DRAFTS_DATE_LINE_DROPS.csv`; Kean F-20261028-9); the fix is a tolerant `DATE_LINE` in
`jobs/clause-drafts/segment.py`, which changes claim-kit's compiler hash and so is applied in a separate step
after the open packets are filed.

## Costs

Producer: one context, about 70 minutes from packet preparation through completion, including diagnosis of
two checker failures and the custody blocker; model tokens not metered by the tooling. Reviewer: one separate
context, 164,567 tokens for the blind pass, 171,047 cumulative with the reveal step. Machine: prepare 44.6 s,
apply about 60 s each, batch-check about 2 min, complete 104 s. No per-order agent-hour saving is claimed from
this batch; the removed step is the per-order search for extension orders, which the packet now supplies.

# Sinclair independent cross-family review — 2026-10-22

**29 uphold; 2 needs research; 0 reject.** This reviews exactly the 31 records in
`PENDING_CROSS_FAMILY_REVIEW.json`. The adoption proposal appends the 29 upheld rows
to `research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv`: **3,374 → 3,403**.
Every existing CSV byte is preserved. Adoption takes effect only if the owner
merges the PR. These remain provisional substantive-status hypotheses at the
2026-10-14 cutoff, not findings, any-effect determinations, verified first
cessations or human certification. Certified whole-lifecycle count remains **0**.

## Review provenance and method

The sole substantive reviewer is Codex, **OpenAI GPT family**, independent of the
Anthropic Claude/Opus Sinclair producer. No exact model version is asserted.
The review follows the [owner ruling](../../../readiness/owner_rulings/2026-10-21-status-proposal-adoption.md).
Base commit: `bf01fb77f171461c76a47bbae65df2425634efb8`.

The fixed checklist asks: (Q1) correct identity/provisional claim and pins;
(Q2) operative held basis and named target; (Q3) whole-instrument coverage;
(Q4) exceptions, savings, transferred functions and independent commands;
(Q5) D6 later events affecting target or ending actor; (Q6) signing/publication/
effective dates, own terms and cutoff; (Q7) errors, assumptions and material gaps.
Every row answers all seven questions in [CROSS_FAMILY_REVIEW.json](CROSS_FAMILY_REVIEW.json),
with manual scope assessments, exact held-text spans and bounded D6 records.

Only repository-held sources were used: original and ending texts, frozen
producer evidence/history, the held EDGES and CHAINS indexes, and held passages
needed to assess later events. No source search or acquisition, re-research,
new whole-lifecycle claim or exhaustive absence claim was performed. Reading a
held index does not imply reading every linked source. The 104 file pins are in
[CROSS_FAMILY_INPUTS.json](CROSS_FAMILY_INPUTS.json). Held derivative/OCR texts
were reviewed; no new page-image authentication was performed. Producer
canonical JSON fingerprints and raw file hashes are distinguished and checked.

## Two proposals withheld

| Instrument | Held evidence and unresolved issue |
| --- | --- |
| EO 9380 | EO 9630 terminates the FEA but transfers functions, including those under paragraph 4 of EO 9380. Its paragraphs 12–13 preserve directives and amend prior orders only to the extent of conflict. EO 10945 §5(a)(5) later supersedes only then-effective export-control provisions. This does not establish the end of every substantive function. |
| EO 9593 | EO 9603 requires return of seized property as soon as practicable, as determined by the holding officer with approval of the Director of Economic Stabilization. It amends conflicting orders only to the extent of conflict. Neither completed return nor the Secretary determination in EO 9593 paragraph 5 is established by the held packet. The 1989 editorial termination note is insufficient primary proof. |

The operative files are `jobs/fr-originals/data/full_run/texts/EO_9630.txt`,
`EO_10945.txt`, `EO_9593.txt` and `EO_9603.txt` in that same directory. These
records remain unresolved; no follow-up research was undertaken here.

## Material corrections within the upheld set

- D6 includes EO 13787 after 13775 (EO 13762), EO 14045 after 13935
  (EO 13555), and EO 12341 after 12251 (EO 12246). Each replacement is
  distinguished from revival of the target.
- EO 12785's current chain attributes a 2015 amendment to EO 13697; the cited
  held U.S. Code page instead contains a historical revocation note. EO 12869
  §4(e) explicitly names EO 12785; the subsequent EO 12882 action concerns §2.
- EO 14219 borrows a definition from EO 13422; this later reference is disclosed
  without treating it as reinstatement. EO 13975's ending actor is EO 14005
  §14(a), not EO 14006.
- EO 10704 relies on direct revocation in EO 10931, not an earlier-displacement
  theory. EO 11105 relies on its direct listing in EO 12553, not an assertion
  that inserted amendments automatically disappear. The relevant table is on
  51 FR 7240. Surviving text or effects in other instruments are not adjudicated.
- Dates and savings are qualified in each record. In particular, EO 12513's
  cited ending was signed/effective March 13, 1990 and published March 14;
  own-term dates are bounds where an earlier condition remains unresolved.

The six parent-ending holds **EO 11261, 11943, 11979, 12240, 12573 and 13371**
were neither reviewed nor adopted. Their file and historical review records
remain byte-for-byte unchanged. Expressly named amenders in the upheld set
are assessed under their own held revoking language, not an unnamed-parent rule.

## Fresh planted controls

A separate seeder prepared nine supplemental scratch-only items: three mutated
controls and six genuine items. The root reviewer froze verdicts before the
seeder released scoring. All **3/3 plants were caught strictly** and all **6/6
genuine items accepted**. Defects concerned an omitted D6 event, an incorrect
own-term date and an incorrect ending actor. The seeder did not adjudicate the
31 production proposals. See [CROSS_FAMILY_CONTROLS.json](CROSS_FAMILY_CONTROLS.json)
for source correspondence, custody pins and limitations.

This is an execution check, not a general accuracy estimate: one plant per
type, paired variants of the same orders, prior exposure to the historical
review, and instructed rather than filesystem-enforced blinding. Full mutated
packets, keys and item verdicts remain outside the repository; only the aggregate
audit is included. The historical plant score is unchanged.

## Adoption and validation

[CROSS_FAMILY_ADOPTION_ROWS.csv](CROSS_FAMILY_ADOPTION_ROWS.csv) contains exactly
the 29 upheld rows. Relative to the frozen pending rows, only `decision_origin`
and `audit_next_step` change, to identify this review and owner-merge condition.
No generated job outputs, codebook, census, human claims or other agent's
handoff notes change. The historical pending manifest remains an immutable
record; this new review records its resolution as 29 eligible and two unresolved.

Run the bounded offline validator from the repository root:

```sh
python research/excavator/sinclair-2026-10-20/lean-review-2026-10-22/validate_cross_family_review.py
```

[CROSS_FAMILY_VALIDATION.json](CROSS_FAMILY_VALIDATION.json) records exact
coverage, source/producer pins, quote offsets, row fidelity, append-only
adoption, unchanged historical records and the changed-file allowlist. It does
not turn manual legal assessments into automated proof or independently
re-score the sealed control packet. No full pipeline refresh or readiness
increase is claimed. Exact per-order time, token and cost telemetry is unavailable.

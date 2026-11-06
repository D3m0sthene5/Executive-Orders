# Selden: official texts of the later instruments that act on an order

Named for John Selden (1584-1654), who went back to the records for the actual texts of statutes and precedents.
Work of the night of 2026-11-05/06, lane `research/selden/` and `jobs/selden-*`. No status, census, codebook or
certified count changed. Certified: 0.

## Conclusions

**The largest Herschel blocker is mostly not a later instrument the project names but lacks.** Herschel projected
that 1,814 open orders are blocked only by "later law, notice or instrument needed for the ending or current basis".
Those 1,814 rest on 21 sampled orders. Read one by one, they need, by projection weight: a source showing the order
is still operative at the 2026-10-14 cutoff (current CFR or agency program text) for about 44%; the text of the
statute the order rests on for 12%; an unnamed later instrument for 13%; an unspecified ending source for 14%; a
fact date (a report submitted, a board dissolved) for 8%; a claim-kit own-terms record for 7%; National Emergencies
Act continuation notices for 2%; and a named later order for about 1% (`HERSCHEL_21.csv`). None of the 36 Herschel
orders blocked on later law is an order whose named acting instrument is merely unheld, and 30 of them have no acting
instrument named anywhere in the finding jobs. Twenty-one orders is a small sample, so these shares are wide.

**Across the census, the named-but-unheld instruments are a smaller, different problem.** The census
(`census.py`, `census/`) reads 16,322 leads from later-events, shepard-citations and current-law that name a later
instrument acting on a census order. Of 5,579 acting instruments, 2,401 are not held as official text: 1,386
executive orders (the order-originals lane; ranked for Mabillon in `ACTING_EO_TEXTS_NEEDED.csv`), 902 Public Land
Orders, 46 proclamations, 24 statutes and 43 others. They act on 1,652 orders whose ending step is open. A further
9,334 orders with an open ending step have no acting instrument named at all.

**What is now held as official text** (first verified runs, 2026-11-06):

| Route (job) | Held | Custody | Orders served |
|---|---|---|---|
| Statutes at Large, govinfo STATUTE 1789 on (`selden-statutes`) | 2,179 of 2,210 statutes the finding jobs name as acting or that an open order's own text cites | sha256 of each granule PDF; text layer kept; whole PDFs kept for the proof orders and those under 400 KB (85) | 4,394 orders whose own text cites a held statute; 30 acting pairs located |
| Federal Register pages of 1936-1993 (`selden-fr-acting`) | 825 of 827 pages printing a named Public Land Order or other non-EO instrument | 802 daily issues byte-identical to the SHA-256 GPO publishes (PREMIS); page extracts committed | 620 orders the pages are wanted for (page location being corrected, below) |
| Federal Register full text, 1994 on (`selden-fr-citers`) | REPLACE_FR | kept document bytes, re-hashable | REPLACE_FR_ORDERS |

Of the 1,015 named instruments that are not executive orders, 817 now have a held official text (781 PLOs, 23
statutes, 13 others); 198 remain (`REMAINING.csv`).

**The proof** REPLACE_PROOF

## How the instruments are located

The locator (`jobs/selden-common/selden_common.py`) reuses Shepard's citation, relation-word and sentence code
and adds readings for OCR-split headings, printed lists, OFR revocation tables, and the instrument's own span on a
page that also prints neighbouring documents. On 5,574 pairs in which OFR's editorial notes say a later order acted
on an earlier one, it found a sentence citing the target in the later order's own held text for 77%, and located
none of 21,940 planted negatives. By hand, 28 of 30 sentences it classed as acting on the order were right; both
errors came from neighbouring documents and that case is now downgraded (`census/LOCATOR_ADJUDICATION.md`).
A located sentence is a lead to what the instrument says, never a finding about its effect.

## Herschel's 21 later-law-only orders

REPLACE_H21

## What still blocks, ranked

`REMAINING.csv` ranks the 1,584 named instruments still unheld by the orders in the proof population they act on.
The executive orders lead (EO 12692, 12319, 11490, 11846) and belong to the originals lane. Among the rest, the
1972 Okinawa treaty, presidential notices before 1994, 121 PLOs without a 1936-1993 FR citation in BLM's table and
46 proclamations without a held citation remain; govinfo's link service has no proclamation-number route.

## Problems and their cost

- The first full Federal Register search returned HTTP 400 for every order: one requested field name is not a valid
  API field, and the offline tests' fake server accepted it. About 45 runner-minutes were lost; the job now fails
  when most requests fail (Kean F-20261106-selden-fr-api-400). The lesson was already in Kean
  (F-20261105-tischendorf-2) and was not applied.
- The first FR-page run read only a window of pages around govinfo's page hint; the hint is often wrong, and about
  750 of the 825 pages kept were not the instrument's own. The job now reads the whole issue when the heading is
  missing and keeps only pages where the instrument's heading was found.
- `claude -p` workers cannot authenticate in this container; the proof's workers ran as subagents of this session.
- Jobs on one branch run in series; at the owner's request downloads were spread over parallel runner branches
  (`claude/selden-shard-*`) at the shared fetch pool's ceiling, and their outputs are united on this branch.

## Registration and counts

`jobs/claim-kit/inputs.py` discovers every `jobs/*/output/FRAGMENTS*.jsonl` and `SOURCES.jsonl`, so merging this
branch registers these sources with the claim kit and, through it, the readiness tracker. That can change counts and
waits for the owner's merge. `jobs/claim-kit/source_supplement.py` adds held excerpts only to decided dossiers, so
the new texts cannot yet reach the 10,681 undecided orders (Kean F-20261106-selden-supplement-decided-only).

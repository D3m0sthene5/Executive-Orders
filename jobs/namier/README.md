# Namier: every held order naming the same person, found once

Named for Sir Lewis Namier, the historian who worked out the eighteenth-century House of
Commons by collecting every record of every member (prosopography) instead of reading each
man's career on its own. This job does that for the project's one-person orders.

## The repeated work it replaces

A civil-service waiver or a retirement exemption concerns one named person. Both type rules
require a search for later orders naming that person (`research/readiness/type-rules/TR-CS-WAIVER.json`
`required_evidence[2]`; `TR-RETIREMENT-EXEMPTION.json` `required_evidence[1]`, "they are often serial").
Before this job, each producer ran that search by hand, one order at a time, and the 2026-10-28 probe
(Kean F-20261028-4) blocked four retirement exemptions because their extension orders were not in the
packet. The number-based tools did not supply them: a serial exemption cites the earlier order ("was
exempted ... by Executive Order No. 6088 ... be further exempted") without a revoke, amend or supersede
verb, so claim-kit located no provision and dropped the pair (fixed in the same change: such citations
now make the citing order a known actor), and a waiver's later use (EO 7072 naming the John V. Shea of
EO 2340) cites no number at all.

Namier parses the person each order names (from the index title, the WPA summary and the order's own
heading and operative sentence), reads every held order text once, and lists every other order whose text
contains that full name. Subjects are the 1,695 pre-1937 orders typed `cs_waiver_individual` or
`retirement_exemption` in `jobs/x1-class-engine/output/TYPES.csv`, plus every other census order whose
index title names a person in an exemption, appointment, reinstatement, transfer, retention or designation
phrase, or mentions compulsory retirement or a civil-service waiver (536 more, mostly 1937-1950s). The
result enters the ordinary pipeline: claim-drafts carries each match as a later-event proposal and enters
the search record; claim-kit makes each matched order a known actor, so its text is in the packet,
labelled `names the same person (name-match lead, read before use): EO:X` (or `cited by number, no change
provision located: EO:X` when the text also cites the number).

## Outputs (`output/`)

| File | Contents |
|---|---|
| `NAME_LINKS.jsonl` | one line per one-person order: the names parsed (with where each came from), every hit with the matched text, exact span, snippet, source text path and SHA-256, relation by date, whether the hit cites this order by number, and flags |
| `EDGES.csv` | one row per (order, other order) lead offered to claim-kit: later or undated, unflagged hits only |
| `FRAGMENTS.jsonl` | the same leads as `later_event_candidates` for claim-drafts (mechanism `names_same_person`) |
| `SEARCH_COVERAGE.csv` | per order: searched (which names) or not (why); claim-drafts enters the search only for listed orders and warns on the unsearched |
| `SUMMARY.json` | counts and the one machine-search declaration (`namier:held_texts_person_name`) |

## What a hit is and is not

- A hit is a name match in a held text. It is not an identity authentication: two people share names,
  and a Federal Register table of contents lists thousands. Read the cited span before using it.
- Hits are kept in `NAME_LINKS.jsonl` but not offered as leads when the middle initial or name in the text
  differs from the order's (`middle_name_conflict`), when the text is an index or table (`index_or_table_context`),
  or when the other order is more than 60 years later (`later_by_more_than_60_years`). A hit on an order within
  three numbers of this one is offered with the caution `adjacent_order_number_check_slice_boundary`, because
  compilation slices sometimes run into the neighbouring order (Kean F-20261026-1). A person named in more
  than 40 other orders (the NRA administrator of EO 6298 appears in 244 code approvals) gets no attached
  leads; the coverage note says so and the hits stay in `NAME_LINKS.jsonl`.
- An empty result covers only the texts this job read: the held texts of the orders with a held text (the
  search record names the producers), and only for orders whose name it could parse (`SEARCH_COVERAGE.csv`).
  It says nothing about the Official Register, agency records or the Civil Service Commission's reports.
- `cites_subject_number` tells whether a hit was already reachable by number.
- Nothing here decides a status, a date, an ending, an identity or a count; `legal_conclusions` is 0.

## Measured on 2026-10-28 (local run, about 3 minutes, zero tokens)

30,725 held texts for 14,913 orders read; 2,231 subject orders (1,695 from the X1 table, 536 from titles);
1,935 with a parsable name (296 not, each listed with the reason); 557 with any hit; 243 with an unflagged
later hit (78 waivers, 48 X1 retirement exemptions, 117 title-detected orders), of which 124 had no later hit
citing the number; 483 leads offered. Serial retirement exemptions found this way include EO 6088 → 6998 → 7597
(Harry O. Bailey), EO 6013 → 6615 → 6974 (Jacob L. Nuber) and EO 6577 → 6773 → 7217 (Carleton W. Sturtevant);
waiver use evidence includes EO 2340 → 7072/7385 (John V. Shea) and EO 7140 → 7472 (Ruth Hampton).

## Running

`python3 -I jobs/namier/job.py` (environment `REPO_ROOT`, `OUTPUT_DIR`); the runner does this after the text
producers and the X1 type table, and before claim-drafts and claim-kit. Tests: `python3 -I -m unittest discover
-s jobs/namier -p 'test_*.py'`. Standard library only; no network.

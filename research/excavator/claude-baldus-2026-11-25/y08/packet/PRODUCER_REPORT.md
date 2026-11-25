# Producer report: packet y08 (producer baldus)

Start 2026-11-25T15:58:12Z; end 2026-11-25T16:10:20Z.

Final applied directory: research/excavator/claude-baldus-2026-11-25/y08/packet/applied-v5 (applied-v1 to v4 were earlier attempts; v1 and v2 failed on missing member checks, v3 was empty after a script error, v4 failed the checker on custody-only current-law sources).

## Outcomes
- EO:12322 submit (YES). All eight clauses decided from the held Federal Register original, EO 12608 (section 2(b), attached as later event, 1987-09-09), and the bounded searches. Section 4 (revokes EO 12113) is carried operative because a completed revocation's effect persists and no ending date is asserted; the route is original_plus_bounded_search (the CURRENT: Code and CFR records are custody_record_only and failed quote and hold checks, so the clauses cite their own held text).
- EO:12234 blocked. Text and current law support an operative YES, but the held FR original (45 FR 58801, sha 1c0ebf1a...) still needs a page or image check (fragment needs_page_check true, no page-check record), so the checker treats it as ungraded derivative. Missing: page-check record for FR-1980-09-05.pdf PDF page 9.
- EO:12312 blocked. EO 13286 section 61 (effective 2003-03-01) must be a later event, but the packet offers only an APP transcription (reopened because the official FR copy of EO 13286 is held) and an excerpt filed under actor EO:12977 (wrong actor). Missing: citable later-event record for EO 13286 section 61 from the official FR text.
- EO:12228 blocked. Missing: current text of 20 U.S.C. 905 and 906 and of EO 10000 (clauses 1-101, 1-102(a), 1-102(b)); 38 U.S.C. 707 text is held and supports 1-102(c) and 1-103.
- EO:12250 blocked. Missing: 29 U.S.C. 794c text (section 1-305); inventory omits section 1-204; no held record of performance of one-time sections 1-301 and 1-403.
- EO:12260 blocked. Missing: current text of 19 U.S.C. 2511-2518 after the Uruguay Round change from the 1979 GATT agreement; USTR section 1-104 threshold notices. The held Code note prints only the preamble.
- EO:12341 blocked. Section 3 (EO 12251 actions continue until superseded by actions under this order) has no held source on which actions existed or were superseded.
- EO:12281, EO:12283 dispatch-blocked (custody_record_only mandatory sources); assessment rows from the views only, decisions rows left as prepared (unresolved).
No order was found not in force on 2026-10-14.

## What took the time (one line each)
- 12322: verifying the 12608 amendment and finding the checker rejects custody-only CURRENT sources.
- 12234: full reading and clause decisions, then discovering the original's page-check status after apply.
- 12312: finding that the only later-event evidence is a mirror or mislabelled excerpt.
- 12228, 12250, 12260, 12341: reading the order and the Code notes to identify the exact missing statute or record.

## Batch-check (applied-v5)
claims_checked 1, strict pass 1, strict fail 0; actual checker: all checks passed 1, mechanical fail 0, unverified 0, gate passed 1. Outcomes: assembled_proposal 1, blocked 6, unresolved 2.

## Geddes
GEDDES_LINT.json: 0 defect flags; 1 coverage gap (citing_corpus_incomplete: 1401 tracked held texts missing or changed, advisory). GEDDES_RESOLUTIONS.json records no resolutions because there are no flags.

## Full-packet files opened beyond the views
LOOKUPS.md, decisions.csv, clauses.csv (own packet, required). Views were supplemented by reading repository files they cite: jobs/current-law output notes and MENTIONS.csv, jobs/later-events/output/EDGES.csv, jobs/theophilus-sources texts, jobs/fr-originals texts (EO_13286, EO_12608), jobs/claim-kit source (batch.py, assemble.py, working_text.py) and research/stage19 claim_gate.py to learn field formats. PACKET.json, READ.md and LOOKUPS.details.json were not opened.

## Tool defects / observations
- The packet citable CURRENT: records for Code notes and CFR sections are custody_record_only at check time, so current_basis_id cannot rest on them; the apply step does not warn before batch-check.
- ACT:...>EO:12977 records in the EO 12312, 12234 and 12341 views are excerpts of EO 13286 filed under the wrong actor.
- The view of EO 12250 omits section 1-204 from its clause inventory.

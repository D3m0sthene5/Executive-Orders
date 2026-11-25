# Producer report, y02 (baldus)

Start 2026-11-25T15:22:41Z. End 2026-11-25T15:37:35Z.

Final applied directory: applied-v3 (applied-v2 is superseded; v2 differed only by one Geddes-flagged sentence in EO:10977's rationale. A first trial applied-v1 was deleted by me before v2.)

## Outcomes

| Order | Outcome | Why |
|---|---|---|
| EO:10977 | submit (yes) | Six scopes, all operative as amended. Later events: EO 11382 sec. 13(3) (1967-11-28) and EO 13286 sec. 72 (effective 2003-03-01 under its sec. 92) on section 2; EO 11231 (1965-07-08), EO 13154 (2000-05-03), EO 13289 (2003-03-12) as "notwithstanding section 3" exceptions on section 3. Original-plus-bounded-search route; no CURRENT record is held, so the predicate rests on the absence of any ending in the three bounded searches and the last operating instruments (2003). The dossier's EO 12977 chain entry is a mislabelled queue file of EO 13286 sec. 72 and is not relied on. |
| EO:10854 | blocked | Substance decided (single operative clause; EO 11326 sec. 7 removed the Ryukyu Islands 1967-02-13; EO 11382 sec. 6(a) 1967-11-28; 49 U.S.C. 40120(b) and note; 14 CFR parts 71, 73; 89 FR 14379). The claim checker rejects the only held original: the PDF hash is also declared by a Montfaucon fragment with acceptable_as_original false and grade official_printing (not a working-text grade), while the fr-originals fragment has location confidence low and requires a page check. Missing: an accepted official-printing fragment for 24 FR 9565. |
| EO:10834 | blocked | Section 25 ("utilized until unserviceable") has no held end or current predicate; an earlier claim was rejected by one blind reviewer for exactly that. Sections 31 (1960-07-04) and 33 (1959-08-21) are spent; the rest is supported by 4 U.S.C. 1 note and 4 U.S.C. 5. |
| EO:10950 | blocked | Section 6(b) selection window (25 years) and the OFR note that the order lapses unless 72 Stat. 339 was amended by 1984-01-03; amending statutes are not held and 72 Stat. 339 is only held_needs_span, so not citable. |
| EO:10910 | blocked | Section 1 text is OCR-garbled; no current-law record held. EO 11287 sec. 6(b) (1966-06-28) deleted section 2 and the last two sentences of section 1. |
| EO:11016 | blocked | Paragraph 8 second sentence (earlier regulations stay in effect until replaced) has no held end source. Paragraphs 1 and 2 were amended by EO 12464 and restated by EO 13758. |
| EO:11023 | blocked | Authority statutes for delegations (a)-(l) are custody_record_only; the 2002 NOAA corps act text is not held. |
| EO:10789 | blocked | Garbled original (paragraphs 4, 21), 20 scopes, seven amendments, emergency dependence under Pub. L. 94-412 not shown from held text. |
| EO:10865 | unresolved | 28 scopes, 25 chain events; EO 13381, EO 13467 and EO 13764 not read against the scopes. Not decided, not a source gap. |

Counts: 1 submitted, 7 blocked, 1 unresolved. Ledger status is YES for all nine; nothing in the held evidence shows any of them not in force on 2026-10-14, and no ledger change is proposed.

## What took the time (one line each)
- 10977: reading six later orders and confirming the EO 12977 mislabel; fastest to decide.
- 10854: inventory correction, page-check record, then discovering the checker's working-text rejection by trial apply.
- 10834: reading the prior reviewed claim in the view and deciding section 25.
- 10950: statute window and OFR note; held_needs_span statute.
- 10910: reading EO 11287 and EO 10961 to see what survives.
- 11016: reading the 1984 and 2017 restatements and paragraph 8.
- 11023, 10789, 10865: inventory size and amendment chains; blocked at once for the named gaps.

## batch-check
claims_checked 1, strict_claim_pass 1, strict_claim_fail 0, actual checker claims_all_checks_passed 1, claims_gate_passed 1, actionable_failures 0. Outcomes: assembled_proposal 1, blocked 7, unresolved 1.

## Geddes
applied-v2: 1 flag (held_source_left_unpinned, EO:10977, rationale sentence about EO 12977). Fixed in applied-v3 by removing reliance on EO 12977 text. applied-v3: 0 flags, 1 coverage gap (citing_corpus_incomplete: 1401 tracked files missing or changed, so an absent citation is not corpus-wide). GEDDES_LINT.json and an empty GEDDES_RESOLUTIONS.json are in applied-v3.

## Full-packet files opened beyond the views
LOOKUPS.md (head, and EO:10950 section), PACKET.json (via batch.load_packet in scratch scripts, for evidence ids, text blocks and sources), LOOKUPS.details.json (key listing only), HELD_SOURCES.json, HELD_SUPPLEMENT.json, DISPATCH_CHECK.json (member entry for EO:10854 and a large source_recovery_tasks print by mistake). Repository sources read: the held order texts and later-order texts cited above, jobs/later-events/output/EDGES.csv, jobs/status-history output for EO:10950, jobs/current-law notes and sections, jobs/theophilus-sources texts, jobs/montfaucon-page-check/output/FRAGMENTS_OFFICIAL.jsonl, jobs/selden-statutes text of 72 Stat. 339, and the claim-kit code (assemble.py, batch.py, working_text.py). No other packet folder was opened; the prior-claim summary for EO:10834 came from the view's prior_research_for_order.

## Tool defects and observations
- dispatch-check passes EO:10854 although apply rejects its original (working-text grade classification of a shared PDF hash).
- HELD_SUPPLEMENT.json "supplement_ready" sources are not in the dossier evidence of this packet (no supp folder), so they cannot be cited without a source-supplement packet; statute and CFR texts that would decide EO:10950, 10854 and 10834 current predicates are therefore lead-only here.
- EO:10854 chain events 5-7 (EO 11938, 12510, 13207) amend EO 10000, not EO 10854; EO:10977's EO 12977 event is a mislabelled queue file.
- `python3 -I` blocks imports from the script directory; scratch scripts under /home/claude/baldus-scr/work/y02 were run without -I.
- Page-check for EO:10854 rests on the Montfaucon record (pass, two reviewers); the PDF bytes are not held locally.

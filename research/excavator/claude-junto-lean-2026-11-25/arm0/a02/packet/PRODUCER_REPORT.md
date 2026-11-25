# Producer report: junto-arm0, packet a02

Start 2026-11-25T08:55:12Z; end 2026-11-25T09:15:21Z (both from `date -u`).

Final applied directory: `applied-v4` (applied-v1 to v3 retained; v1 and v2 had source-custody and inventory problems, v3 differed from v4 only by one sentence in the EO 13549 earlier-end check).

## Outcome per order

| Order | Outcome | Why |
|---|---|---|
| EO:12648 | submit (YES) | One clause (section 1). Own-text route: held official FR text, no own-terms end, no later event, bounded searches (usc 1 hit = Code note, ecfr 0, ofr_catalog 0). |
| EO:13549 | submit (YES) | 61 clauses after an inventory correction (fragment `sec6-b-13526` merged into `sec6-b`). All operative except section 7 (effective-date clause, ended by own terms 2011-02-14). Section 3 carries eight FACA continuation orders (EO 13591 ... EO 14354, continued to 2027-09-30) as later events. Own-text route. |
| EO:12985 | blocked | Section 3 needs EO 13154 and EO 13289 ("Notwithstanding section 3") as later events; their FR PDF bytes are custody_record_only (sha256 a5170c14..., 6670f509...). Legal reading otherwise supports YES (EO 13286 section 20 amends section 2, effective 2003-03-01). |
| EO:12916 | blocked | EO 13380 (70 FR 35509, sha256 c4c1ad04...) ends sections 2 and 3(a)-(c) and amends 1, 3(d), 6, 7(c); its PDF bytes are custody_record_only. Reading otherwise supports YES (sections 4-5, 7-11 unchanged). |
| EO:12560 | blocked | Amends EO 12163 (sections 1-10) and EO 11958 (sections 11-13; EO 11958 revoked by EO 13637, 2013-03-08). Survival of the 1986 amendments after EO 13118's 1999 rewrite of Parts 1-1 and 1-2 cannot be shown; no consolidated EO 12163 text held; EO 12611 text not located. |
| EO:13091 | blocked | Same EO 12163 / EO 11958 problem as EO 12560 (EO 13118 rewrote Part 1-2, amended 1-3 and 1-5). |
| EO:12569 | blocked | Implements Pub. L. 99-239 / Compact; no held text of 48 U.S.C. 1901 et seq. as in force or of later amendments; completed trust-territory duties undated. |
| EO:13094 | blocked | Emergency-dependent; NEA continuation notices attached only for 2015-2025 (FRDOC) and unlocated for 2002-2009; jobs/selden-fr-citers texts absent from checkout; EO 13382 rewrote section 4(a) of EO 12938. |
| EO:13304 | blocked | Emergency-dependent (EO 13219); notices 2009-2021 not attached; jobs/selden-fr-citers texts absent; EO 14033 and EO 14140 further amend EO 13219. |

No held evidence showed an order not in force on 2026-10-14; no member was blocked for that reason.

## What took the time
- EO:12648: single clause; custody discovery (Code-note records are custody_record_only) forced the own-text route.
- EO:13549: 62-clause inventory, one-word fragment, tiny-quote failure fixed by an inventory correction; continuation-order chain verified in the held texts.
- EO:12985 / EO:12916: reading amendments, then discovering that the later-event PDFs are not held.
- EO:12560 / 13091: tracing EO 12163 / EO 11958 amendment history through EO 13118 and EO 13637.
- EO:12569: authority-statute text not held. EO:13094 / 13304: emergency notice chains.

## Batch-check (applied-v4)
packet members 9; claims checked 2; strict pass 2, fail 0; actual claim checker 2 of 2 all checks passed, 0 mechanical failures, 0 unverified; outcomes: 2 assembled, 7 blocked.

## Geddes
Lint ran in batch-check on v4 (an earlier batch-check on v3 reported a Geddes error, "held corpus changed during literal-name search"; a direct lint run succeeded). One flag: EO:13549, `unaddressed_citing_instrument`, flag 91991c7c59e226c4 (EO 13381 said to revoke EO 12333). Disputed in `applied-v4/GEDDES_RESOLUTIONS.json`: EO 13381's cited text is a "nothing in this order shall ... affect" list naming EO 12333 and revokes nothing; EO 13549 does not amend EO 12333. Four coverage gaps (own-order body, corpus completeness) are advisory.

## Files opened beyond the views
LOOKUPS.md (full); PACKET.json (loaded once through batch.load_packet to extract evidence texts, no full read); decisions.csv and clauses.csv; DISPATCH_CHECK.json (summary); LOOKUPS.json and LOOKUPS.details.json (regex scan for "Revoked by / Superseded by" notes: none found); EO_13549.json view `clauses` offsets for the inventory correction. Held texts read from the repository: the order texts of the assigned orders, EO 13118, 13154, 13286, 13289, 13380, 13591-14354 continuation orders (grep), the Code notes for EO 12163, 12569 and 12916, jobs/later-events/output/EDGES.csv (target filter), jobs/current-law POSSIBLE_CONFLICTS.csv. READ.md was not opened.

## Tool defects and observations
- kit.py apply creates the destination before its source check; a second apply to the same folder is refused, so each fix needed a new applied-vN.
- The dossier's EO:12977 record in EO:12985 carries EO 13286 section 23 text (and EO 12977 predates EO 12985); it is not a later event.
- `jobs/selden-fr-citers` is not present in this checkout, so FRDOC continuation notices named in several dossiers cannot be read from disk.
- The U.S. Code release-point zip and several FR PDFs are custody_record_only, so every CURRENT: USC record fails custody; the own-text route was used instead.
- ASSESSMENT.jsonl `first_cause` has no value for an order still in force; "unresolved" is used for in-force orders.

## Update 2026-11-25 (after coordinator restored jobs/selden-fr-citers, selden-fr-acting, ptolemy-custody, astra-source-retention)
Final applied directory is now `applied-v5` (v4 retained). jobs/ptolemy-custody/output/raw now holds the PDF bytes for EO 13380 (c4c1ad04), EO 13154 (a5170c14) and EO 13289 (6670f509), so EO:12916 and EO:12985 were rebuilt as YES submissions (own-text route; later events EO 13380, EO 13286, EO 13154, EO 13289, EO 14354 attached). EO:13094 and EO:13304 stay blocked: the restored files cover the attached notices, but the gap-year notices (EO:13094 1998-2001 and 2010-2014; EO:13304 2009-2021) are still not evidence records in the packet, and EO 13094 still needs the EO 13382 section 4(a) comparison. Batch-check v5: 4 claims (EO:12648, 12916, 12985, 13549), strict 4/4, actual checker 4/4 all checks passed, 5 blocked. Geddes: same single EO:13549 flag (EO 13381), disputed in `applied-v5/GEDDES_RESOLUTIONS.json`. ASSESSMENT.jsonl updated (12916 and 12985 now submit/yes).

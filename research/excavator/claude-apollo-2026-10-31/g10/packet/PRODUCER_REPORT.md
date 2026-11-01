# Producer report, batch g10 (claude)

Start 2026-10-31T22:16:15Z. End 2026-11-01T03:36Z (includes waiting for a usage-limit reset between 2026-10-31 and 2026-11-01).
Final applied directory: `applied-v2` (applied-v1 kept; it differed only in that EO 12521 was submitted and then failed the actual checker).
Result: 9 submitted, 18 blocked, 27 members.

## Submitted (all terminated by an express revocation that names the order or the parent as amended by it)

| Order | End instrument and first-end date | Note |
|---|---|---|
| EO 12209 | EO 12553, 1986-02-25 (signing date, no effective wording) | earlier candidates disclosed, none names the order: period of restated 1-101 ends 1980-03-31; EO 12287 decontrol 1981-01-28; statute lapse not held |
| EO 12227 | EO 12553, 1986-02-25 | EO 12357 (not-later-than 1982-09-30 phase-out of the Mission) disclosed as a bound, not an end |
| EO 12398 (3 clauses) | EO 12553, 1986-02-25 | section 4(b) sunset rewrites by EO 12429, 12447, 12455 recorded in the clause reason; EO 12534 (1985-09-30) revokes parent EO 12369 without naming the order, disclosed |
| EO 12429 | EO 12553, 1986-02-25 | same chain |
| EO 12529 | EO 12610 section 3(e), 1987-09-30 (express section 5) | names EO 12503 "as amended by" EO 12529; report-relative termination is a spent fact (ruling 2026-10-21) |
| EO 12649 | EO 12919 section 904(a)(10), 1994-06-03 (signing date) | |
| EO 12891 (18 clauses) | EO 13062 section 3(a), 1997-09-30 (express section 7) | section 4(b) report-relative termination disclosed |
| EO 12921 | EO 13062 section 3(d), 1997-09-30 | parent sunset 1996-06-01 (EO 12970) disclosed |
| EO 12987 (2 clauses) | EO 13062 section 3(b), 1997-09-30 | EO 13032 date change recorded as a later event on item (i)/(ii) |

## Blocked (precise gap in decisions.csv `unresolved_material_gaps`)

- EO 12263, 12390, 12392, 12397, 12434, 12440, 12442, 12447, 12457, 12476: EO 12553 lists each number in its table (held text offsets recorded) but the dossier carries no located provision or actor text for the pair, so no ending evidence can be cited. A source supplement needs the raw Federal Register PDF (FR-1986-03-03.pdf, sha256 945348af...), which is not held and cannot be fetched here (proxy returns 403). 12434 also needs a page check.
- EO 12317, 12507, 12581: only the parent order is revoked (EO 12379; EO 12610) without naming the amending order; the owner ruling on unnamed instruments makes the naming instrument the end. 12507 also has a "whichever occurs first" own sunset (on or before 1986-04-01) whose report-date trigger is not held.
- EO 12521: assembled in applied-v1 but the actual checker failed all original quotes (the registered text EO_12521.recheck.txt does not match the checker's text of the PDF). Legal analysis complete (EO 12919 section 904(a)(9), 1994-06-03; EO 12649 later event).
- EO 12751: page-check flag, no page images; ending instrument EO 13350 (effective 2004-07-30 12:01 a.m. EDT) names it.
- EO 12883, 13857, 13863 (status yes): no held current-law legal text (snippets only) for a current predicate through 2026-10-14; 12883 also has the page-check flag; 13863 notices of 2025-07-21 and 2026-07-13 are absent from the census.

## What took the time (one line each)

- 12209/12227/12398/12429: reading the EO 12553 table, the earlier-end candidates (EO 12287, EO 12357, EO 12534) and the sunset-rewrite chain.
- 12529: confirming EO 12610 names the amending order and has an express effective date.
- 12649: separating the order from the memorandum printed after it.
- 12891: checking an 18-clause OCR inventory against sections 1 to 4.
- 12921/12987: reading parent orders (EO 12864, 12970, 12964, 13032) for sunsets.
- The 17 blocked: establishing that the ending instrument cannot be cited from the dossier.

## batch-check counts (applied-v2)

27 members; 9 assembled and strictly passed; 18 blocked. Actual checker: 9 claims, 6 all checks passed, 3 mechanically unverified, 0 failed. The 3 unverified (EO 12891, 12921, 12987) report `custody_record_only` for the EO 13062 Federal Register PDF (62 FR 51755, sha256 9d07849b94...), whose bytes are not held; the quotes are held text and the legal content is complete, but the custody gap will need the PDF at completion.

## Tool defects and observations

- `source_supplement.py prepare` requires the raw source PDF at `local_path`; Federal Register PDFs are not stored in the repository, so the route cannot add EO 12553 provisions for the ten blocked orders.
- `EO_12521.recheck.txt` is registered as the original but is not matched by the checker, which searches the clause-drafts text of the same PDF.
- The batch-check lists custody_record_only claims under `actionable_failures` although they are not failures and the exit code is 0.
- Several LOOKUPS number-citation hits for EO 12553 targets are absent because the revocation is a table row.

# Producer report: y02 (dorotheus, YES probe)

Start 2026-11-06T10:20:39Z; end see last line.

## Outcomes (final applied dir: applied-v5)
- EO:11219 **submit** (YES). Original 30 FR 6381-6382 read in full; inventory corrected (14 units: lead, 1 lead, 1(a)-(d), 2(a), 2(b) lead, 2(b)(1)-(3), 3, 4, 5); later events EO 12107 (eff. 1979-01-01) and EO 12292 (eff. as of 1981-02-15) attached; held 5 CFR 315.606/315.201 and the three bounded searches. The packet's EO 9452 "actor" is not an event (pre-dates the order; the file is the FR copy of EO 12292, which revokes EO 9452).
- EO:10431 **blocked**: reading complete (operative, amended by EO 13709, nothing revoked), but the sole later event is custody_record_only for ACTOR_TEXT:EO:13709 and the APP mirror is refused (official_copy_available_recheck_required). Missing: govinfo FR-2015-10-07 PDF (doc 2015-25744) held as bytes.
- EO:10694 **blocked**: EO 13286 only as APP/Common Crawl transcriptions in packet evidence; inventory clause #2 spans the FR contents page. Missing: official FR text of EO 13286 (68 FR 10619) as evidence; two-span inventory.
- EO:11023 **blocked**: twelve statutory delegations (1948 Coast and Geodetic Survey officer acts, replaced by Pub. L. 107-372); missing current statute text for each, and official texts of EOs 12608 and 13341.
- EO:11311 **blocked**: missing Pub. L. 89-634 sec. 3 and the 1988 HTS conversion (clause 1) and 22 U.S.C. 6531/6532/6551 (USIA successor, clause 2). Dossier fragment scope EO:11311#1967 needs removal.
- EO:11396 **blocked**: identity failure; the registered original is an AEC 10 CFR Part 1 rule, not the order. Missing: FR text of EO 11396 at 33 FR 2689.

## What took the time (one line each)
- 10431: full text + 13709; two apply/check cycles to learn the custody and mirror limits.
- 10694: reading text, 13286/14085 amendments, found inventory and mirror problems.
- 11023: read the text and judged that twelve statute-by-statute checks were not possible from held sources.
- 11219: most time: inventory correction, 12107/12292 reading, current CFR check.
- 11311: read text, 22 CFR 61 and 19 U.S.C. 2051 note; blocked on TSUS/USIA gaps.
- 11396: found the identity failure at once.

## Checks
applied-v1 (rejected 10431: unresolved conflict), v2 (conflict resolved; 10431 source custody_record_only), v3 (mirror refused), v4 (generator error; superseded), v5 final. batch-check on v5: 6 members, 1 claim, strict pass 1, fail 0; actual checker 1/1 all checks passed, 0 unverified; outcomes: 5 blocked, 1 assembled.
Geddes: 0 flags, 0 coverage gaps (GEDDES_LINT.json in v5; empty GEDDES_RESOLUTIONS.json).

## Files opened beyond the views
LOOKUPS.md, decisions.csv, clauses.csv, RATIONALES.json; PACKET.json via batch.load_packet (dossier conflicts and current-law leads); no READ.md or LOOKUPS.details.json content beyond keys. Repository sources: held original/actor texts for the six orders, EO 13709, 13286, 14085, 13870, 12292, 12107 FR texts, 5 CFR 315.201/.606, 22 CFR 61, 19 U.S.C. 2051 note. A grep for `original_plus_bounded_search` printed lines from other packets' paths (claude-icecore, y01); I did not open them.

## Tool defects
- load_packet takes Path objects (str failed). The dossier's machine_searches and some leads are unresolved `@eo:ref` stubs outside the views.
- Dossier inventories were wrong for 10694 (#2 spans the FR contents), 11219 (incomplete, mislabeled) and 11311 (fragment "1967.").
- The working-text draft pre-fills a mirror confirmation for 13709 that the policy then refuses when an official copy exists.
End 2026-11-06T10:34:00Z

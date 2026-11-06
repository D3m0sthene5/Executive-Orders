# provisional_status notes, worker H5-w08
Start UTC: 2026-11-05T23:36:48Z
End UTC: 2026-11-05T23:41:42Z

Outcomes (STATUS_DECISION.json filled in undecided/EO_N/; proposals only, nothing adopted):
- EO:11925: done (provisional NO; amends EO 11554, which EO 12082 sec 1-103 revokes as amended, 1978-09-19; EO 12082 does not name 11925)
- EO:9248: done (provisional NO; amends EO 9240, revoked as amended by EO 9601 effective 1945-08-21)
- EO:9866: done (provisional NO; superseded by EO 10156 para 3, 1950-08-26)
- EO:12221: done (provisional NO; amends EO 12044, revoked as amended by EO 12291 sec 10, 1981-02-17)
- EO:13672: done (provisional NO; revoked by name, EO 14173 sec 3(a)(iii), 2025-01-21; see caveat)
- EO:9699: blocked:freeze EO 9809 (jobs/fr-originals/output/texts/EO_9809.txt, 1946-12-12) and the order ending the Office of Temporary Controls as actor texts in a refreshed packet, then judge whether consolidation ended paragraphs 1-2 and whether paragraphs 3-4 are spent
- EO:14331: blocked:held official current-status source through 2026-10-14 (FR presidential documents/disposition pages or dated full-text search of orders 2025-08-07..2026-10-14, held as bytes with hash)
Time: reading each order's dossier and acting texts; 9699 and 14331 needed corpus searches.

For the next worker:
- All five done decisions pass status_overlay._decision_errors with no errors (checked in Python). Blocked two have approved=false, status null, material_gaps filled; their rationale says why.
- Extra field lifecycle_gaps_retained (as in the EO11352 pilot) holds gaps kept for lifecycle work; material_gaps is [] on done ones. proposed_intervals left empty; end dates are in rationales only, not accepted intervals.
- 13672 caveat: section 1 amended EO 11478, which 14173 did not revoke. NO rests on express revocation of 13672 by name; whether the inserted wording survives in EO 11478 text is unresolved (current EO 11478 text not held; U.S. Code note is editorial). Reviewer should look at this one first.
- 11925, 9248, 12221 end through revocation of the amended parent order (strike-and-insert ruling: amendment lives with its parent).
- No decisions.csv/clauses.csv/RATIONALES.json edited. No kit view/apply run. Nothing about 'changed prior research' appeared.

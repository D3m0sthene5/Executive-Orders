# Producer report, batch g06 (claude)

Start UTC: 2026-10-31T22:14:25Z. End UTC: 2026-11-01T03:31:53Z (includes a pause for a usage-limit reset).

Final applied directory: `applied-v2` (`applied-v1` retained; it submitted 21 and had one checker failure, EO 10878).

## Counts

- Submitted (assembled proposals): 20. Blocked: 4. Unresolved: 0. Total 24.
- Batch-check on applied-v2: strict claim pass 20/20; actual claim-checker 20 all checks passed, 0 mechanical fail, 0 unverified; gate 20/20; actionable failures none; independent human certifications 0.
- Batch-check on applied-v1 (for the record): strict 21/21, actual checker 20 pass, 1 mechanical fail (EO 10878).

## Outcome per order and why

Provisional status was adopted unchanged. All submitted orders are provisional `no` and ended by express revocation, with the report date and the end of the status-quo period disclosed as functionally spent facts, not ends.

- 10750, 10757, 10760, 10862, 10868, 10874, 10904, 10933, 10944, 10949, 10951, 10963, 10969, 10971: submitted; revoked by EO 12553 (1986-02-25) through a located acting-provision record.
- 10770, 10877, 10843, 10954: submitted; revoked by EO 12553 (1986-02-25) on the whole actor text, because the dossier has no located acting record for these and no local original is held for a source supplement.
- 10892: submitted; ended 1964-06-22 by EO 11157, which names it.
- 10915: submitted; ended 1961-09-30 by EO 10973, which supersedes it by name.
- 10826: blocked. YES order with no held current legal text. Leads are an eCFR bulk node (5 CFR 351.502) and a search excerpt (5 CFR 351.501); the EO 12107 later event has no dated held record.
- 10849: blocked. YES order; 14 CFR 1221.102 and the 51 U.S.C. 20111 note are not held as text, and the EO 10942 restatement has no dated held record.
- 10863: blocked. YES order; 28 CFR 0.89 and the 22 U.S.C. 401 note are not held as text, and the underlying statute is unchecked.
- 10878: blocked. The registered original and clause text is `EO_10878.recheck.txt`, but the checker resolves the PDF sha256 to a different OCR copy (clause-drafts) that reads "List A - attached" and "Switchmen' s" against "List A- attached" and "Switchmen's". Quotes fail on three fields. Research was complete (EO 12553 revocation); the gap is the original-text registration, not the lifecycle.

## What took the time (one line per order)

- 10750, 10757, 10760, 10862, 10868, 10874, 10904, 10944, 10963, 10969: locating the NMB report date in held texts for the spent-fact disclosure, plus quote verification against the cited span.
- 10770, 10877, 10971: no held NMB report text; confirmed the gap and used the whole actor text for the end.
- 10843, 10954: finding that no acting record exists and that the page-12 row of the EO 12553 table is aligned by position.
- 10933: board 136 extension language spanning a line break; the quote had to be shortened.
- 10949: quote of "and any amendments thereto" lay outside the cited span; rewritten without quotation marks.
- 10951: reading its own terms and the earlier-end search before accepting EO 12553 as the end.
- 10892: held text is hyphen-broken, so quotes became paraphrases.
- 10915: confirming supersession by name in EO 10973 and the effective date.
- 10826, 10849, 10863: searching held current-law material, then blocking with exact gaps.
- 10878: diagnosing the checker failure (recheck text versus clause-drafts copy), then blocking in applied-v2.
- 10843: also a strike-and-insert amendment (new date); the quote of the new date lay outside the cited span and was paraphrased.

## Tool defects

1. Checker and dossier disagree on the original text for a sha when the dossier registers a `.recheck.txt` copy (EO 10878). The checker only searches the clause-drafts copy, so a correctly registered text fails `quote_verbatim`, and `original_representation` (the whole recheck file with its header) cannot match at all. Inventory correction cannot fix it because no dossier evidence id carries the checker's copy.
2. Clause quotes are verified only against the cited span, but ACT enacting-sentence spans exclude the page-12 table rows, so a producer cannot quote the row that actually lists the order. This forced paraphrase for ACT-located orders.
3. Hyphen-broken and line-broken source text (10892, 10933) defeats verbatim quotes; no normalization helper exists in the packet tools.
4. Harness blocks `sleep` followed by a command, so waiting needs bounded `until` loops; apply takes about 85 seconds and batch-check more than 120 seconds.

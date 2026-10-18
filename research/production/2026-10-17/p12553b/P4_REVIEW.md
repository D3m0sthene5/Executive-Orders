# P4 independent source survey

Reviewer: `review_12553_b`. Survey only, with no new claims or certifications. The five principal orders are EO 13037, 13038, 13090, 13147 and 13369, all outside the five original P1 acting-instrument target lists as selected by the producer. The reviewer opened each case bundle and read its complete saved original at `jobs/fr-originals/data/full_run/texts/EO_<number>.txt`. The reviewer also read EO 13138, 13136, 13167, 13316, 13386 and 13446 as relevant later sources. Original PDF page images and published official fixity remain unverified.

| Order | Original source, PDF SHA-256 | Exact sunset text in saved original | Independent conclusion |
|---|---|---|---|
| EO 13037 | 62 FR 10185–10186, PDF pp.1–2; `cc9efd03e59838367929ca8f0ba3f261b4aeccf8aef671e2544825a1a9d8079c` | “The Commission shall terminate 30 days after submitting its report.” | Original condition requires actual report submission. Independently read EO 13108, which expressly replaces it with September 30, 1999. This supplies a second fixed-calendar candidate, subject to earlier cessation/revival and later-event checks. |
| EO 13038 | 62 FR 12065–12066, PDF pp.1–2; `7ccc89f539dbfa6438046465689e3b071d92b442ce65bc0907ae721d9bf2476f` | “The Committee shall terminate 30 days after submitting\nits report, unless extended by the President.” | Actual report and extensions are necessary. The June 1, 1998 report deadline is insufficient. Bundle identifies section 5 of EO 13062 and EO 13065, 13081 and 13102. |
| EO 13090 | 63 FR 36151–36152, PDF pp.1–2; `030b83d958b75c03a61a80a35aeedabc8e3cc001c54ee653163729ea048c7830` | “The Commission shall terminate 60 days after the submission of its\nfinal report.” | Actual final report is needed. EO 13136 changes the report deadline from March 1, 1999 to December 31, 2000 and recites the purpose of extending the commission's life. It does not replace the report-dependent sunset. |
| EO 13147 | 65 FR 13233–13234, PDF pp.1–2; `a7ec60f5bdd77be4da2ba094a3c7c7bc6fedfef6c845192765bd7fb80ec2a034` | “The Commission shall terminate 2 years from the date of this order\nunless extended by the President prior to such date.” | March 7, 2002 is a candidate calendar sunset. The saved EO 13167 only expands membership, without changing that sunset. A search for other extensions or earlier termination and residuals is still necessary. |
| EO 13369 | 70 FR 2323–2324, PDF pp.1–2; `3f23b91227bd02f0a817e2ac9fb4babceba4057fa0298183a8c3e36f39cca439` | “The Advisory Panel shall terminate 30 days after submit-\nting its report pursuant to section 5 of this order.” | The original is report-dependent, but EO 13386 expressly replaces this condition with a fixed November 15, 2005 termination date. This is the strongest fixed-calendar candidate in this survey, subject to earlier/later events, residuals and custody. |

## Later-source checks that change the inference

EO 13108 expressly deletes the report-plus-30 sunset in section 5 of EO 13037 and substitutes “on September 30, 1999”, while separately changing the report deadline to February 1, 1999. Source: `https://www.govinfo.gov/content/pkg/FR-1998-12-15/pdf/98-33382.pdf`, 63 FR 69175, PDF p.1; SHA-256 `a27cdd00350124368a2299a208a06b73b4bd961deb4c2c8084c409aab6450936`. Thus the original report-dependent pattern must be replaced for the commission after that amendment; any actual earlier cessation before the amendment remains a separate check.

EO 13138 section 3 explicitly describes its listed committees as having terminated and completed their work, then revokes EO 13037 and 13038 among others. Its September 30, 1999 effective date cannot be adopted as their first cessation. Its other sections continue committees and make permanent amendments, so it is not itself a whole-order calendar-sunset case. Source: 64 FR 53879–53881, PDF pp.1–3; SHA-256 `dad8da2858e80af84a22cb6255fee337010290cdc3946b55688b1d8f89f22889`.

EO 13386 section 2 reads, exactly in the saved text:

> Sec. 2. Section 7 of Executive Order 13369 of January 7, 2005, is further
> amended by deleting ‘‘30 days after submitting its report pursuant to section
> 5 of this order’’ and inserting in lieu thereof ‘‘November 15, 2005’’.

The same order's section 1 replaces the report deadline with November 1, 2005. The panel's own termination therefore no longer depends on the actual report date. Source: `https://www.govinfo.gov/content/pkg/FR-2005-10-05/pdf/05-20156.pdf`, 70 FR 58289, PDF p.1; SHA-256 `511e2fbcb1da95a1a23c4835356bff6743ebc841328408efdd114e658bcc7425`.

EO 13446 section 3 later revokes EO 13369 as amended by EO 13379 and 13386, describing the panel's work as completed. Section 6 expressly makes this cleanup order effective September 30, 2007, although signed September 28. Current saved full-run source: `https://www.govinfo.gov/content/pkg/FR-2007-10-02/pdf/07-4906.pdf`, 72 FR 56175–56178, PDF pp.1–4; SHA-256 `d0e39c4ac971c4989b7838e73e7408540a41d68a6a834b613a8cf83f70267fd4`. This differs from an older source hash in the EO 13369 bundle; the witnesses must not be silently conflated for fixity.

EO 13167 (65 FR 57079, PDF p.1; SHA-256 `b0922293f877f5ee7418409c789b0a18667f08136a9ecaa243a7829ca45a871e`) changes EO 13147's membership cap from 15 to 20. EO 13316 section 3(i) subsequently revokes the order as amended, in a list of committees that have terminated or completed their work. These later sources support investigating the earlier own-term sunset; they do not establish a complete first-end proof without the bounded source review.

## Scope controls

Do not produce a general rule mapping every report deadline to termination. The useful patterns are actual-report-plus-offset, an expressly conditional anniversary sunset, and a later amendment expressly replacing an event-dependent sunset with a calendar date. Each rule still needs target-specific scope, earlier-ending, extension, later-use and residual checks.

Current-law leads in these bundles were not resolved: the connector returned empty content for the oversized `jobs/current-law/output/FRAGMENTS.jsonl` through `fetch_file`, and raw retrieval explicitly failed for size/format. This is a retrieval limitation, never a negative search result. No all-saved-text counterexample sweep or adequate cutoff-wide search was completed by this reviewer.

Additional rejected candidates read: EO 12668 has an actual-report-plus-30 sunset and independent Counsel-to-the-President implementation-report duties; EO 12852 has a conditional two-year council term and an independent revocation of EO 12737. Their body sunset cannot by itself establish their whole-order first cessation.

## Independent pattern-proposal review

All five producer proposals in `p4-survey/pattern-rules/` were independently reviewed against their complete saved derivative texts. Five of five quoted clauses are exact substrings; five of five text SHA-256 values match the saved bytes; five of five original PDF hashes match the saved header. The scopes preserve custody, visual-page, extension/earlier-end, current-law and residual blockers, and all proposals prohibit production application and whole-order inference. There were zero proposal-scope failures. Exact proposal file hashes and results are in `p4-survey/REVIEW_PATTERN_RULES.json`.

These five custom-schema proposals are not production family rules, passing certificates or ready orders. The producer's limited local sweep is explicitly not an all-corpus/current-law search. No additional claim batch was created or independently approved.

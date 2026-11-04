# Producer report, packet a06 (Tribonian)

Start UTC: 2026-11-04T05:12:24Z. End UTC: 2026-11-04T05:41:54Z.

## Outcomes (final applied directory: applied-v2)

Submitted (10): EO 11767, 13210, 13227, 13278, 13326, 13328, 13422, 13508, 13762, 14042.
Blocked (16): EO 10633, 10751, 12975, 13125, 13192, 13214, 13339, 13515, 13555, 13572, 13824, 13872, 13987, 8129, 8331, 9029.

Submitted orders and first end:
- EO 11767: revoked by EO 13377 section 3, 2005-04-13. Current-law conflict (8 CFR 316.20 list) resolved in the sheet.
- EO 13210, 13227: revoked by EO 13316 section 3, effective 2003-09-30. Report-relative termination clause disclosed, not an end (report-deadline ruling); report dates are not held. EO 13227 records EO 13255 as a strike-and-insert later event on section 3(b).
- EO 13278: own-terms outer date 2003-08-30 (section 6(b), recorded inclusive; exclusive reading stated); EO 13316 revocation (2003-09-30) is a later event.
- EO 13326, 13328: revoked by EO 13385 section 3, effective 2005-09-30; report-relative clauses disclosed.
- EO 13422: revoked by EO 13497 section 1, 2009-01-30; two dossier conflicts resolved.
- EO 13508: revoked by EO 14428 section 2, 2026-09-16 (quoted from the Federal Register text, not from the recital ACT record); current-law note conflict resolved.
- EO 13762: revoked by EO 13775 section 3, 2017-02-09. Section 3 of EO 13762 is a one-time revocation of EO 13557 that was executed on issuance; the tool needs an actor-sourced event, so the clause carries the revocation date with a disclosure and the surviving consequence is in savings. Reviewer should look at this judgment.
- EO 14042: revoked by EO 14099 sections 2 and 3, effective 2023-05-12 (cited to the held Federal Register text through the whole-text actor record); EO 14174 (2025-01-21) is a later event; three dossier conflicts resolved.

Blocked, with the precise gap (also in decisions.csv unresolved_material_gaps):
- 10633: 26 FR 6233 (FR Doc. 61-6503) not held. 10751: 26 FR 8883 (FR Doc. 61-9007, revoking EO 10127) not held.
- 12975: NBAC termination date (EO 13046/13137 extensions, "unless extended") not shown by a held source; sections 1-2 independent.
- 13125, 13339, 13515, 13872, 13555: Commission terms "unless renewed/extended" with no held renewal or termination record; clauses would end on different dates than the supersession.
- 13214: own-terms outer date (2003-05-28) exists, but every own-terms record of this order is registered as a report-deadline kind that the assembler refuses as an end.
- 13572: located revoking provision for the order and CFR leads unresolved. 13192: section 2 preservation and EO 13304 continued-blocking determination are savings questions with unlocated target provisions.
- 13824: amending order whose effect lives in EO 13265 as amended; text not held. 13987: EO 14122 section 3 terminated the Coordinator positions and transferred duties before the 2025 revocation.
- 8129, 8331: no ending evidence held. 9029: PLO 358, 473, 833 texts not held.

## What took the time (one line each)
- 11767, 13762: first-run, learned sheet format; 13762 section 3 one-time-command question.
- 13210, 13227, 13278, 13326, 13328: reading own-terms report clauses and EO 13316/13385; 13278 fixed outer date.
- 13422, 13508, 14042: locating the operative revocation text (ACT record was a recital for 13508; APP-only ACT for 14099) and resolving dossier conflicts.
- 13987, 13824, 13192, AAPI chain (13125, 13339, 13515, 13872), 13555: reading amendment and renewal chains, then blocking.
- 10633, 10751, 9029, 8129, 8331: searching held texts for the revoking instruments (1989 codification leads only).
- Batch-check and Geddes were slow because other producers ran concurrently.

## Batch-check (applied-v2)
packet members 26; claims checked 10; strict pass 10; strict fail 0; blocked 16. Actual checker: 10 mechanical pass-with-unverified (custody-record-only sources, network disabled), 0 mechanical failures, 786 quotations exact. A first small trial (applied-v1, two orders) passed the same way. The coordinator notice about the matched_date checker bug did not apply (no such error occurred).

## Geddes
Lint of applied-v2 (GEDDES_LINT.json): 30 defect flags in 4 claims (EO 13227: 18, EO 13326: 3, EO 13328: 3, EO 13422: 6), 0 coverage gaps. All disputed in applied-v2/GEDDES_RESOLUTIONS.json: the EO 13227 flags concern EO 13255 appearing inside an exact quotation of EO 13316 (the amendment is a later event on the one clause it amends); the EO 13326/13328/13422 flags are held orders that cite or supplement-not-supersede the amended order (EO 12958, EO 12866) or only mention EO 13422 in a definition (EO 14219), none revoking the packet order.

## Full-packet files opened beyond the views
Held repository texts for the orders and later instruments (jobs/fr-originals texts, jobs/app-executive-orders text for EO 14099 only to compare), jobs/ofr-codification-1989 DISPOSITION_1989.csv and EO_12038 text, packet PACKET.json via batch.load_packet (for evidence records; exported to /tmp/claude-0/tribonian-work/a06/dossiers.json). READ.md, LOOKUPS.details.json not opened. The view JSON lacked evidence record texts and per-clause text, which I took from load_packet.

## Tool defects
- batch-check and geddes lint exceed 120 s under concurrent load; run in background.
- The assembler refuses any own-terms record of kind report_deadline as an end, even when the sentence also carries a fixed outer date (EO 13214), and offers no actor-sourced record for one-time commands performed on issuance (EO 13762 section 3).
- ACT records for EO 14428 and EO 14099 pointed to a recital or an APP mirror rather than the operative Federal Register sentence; the whole-text actor record had to be used.

Note: the repository CLAUDE.md asks for HANDOFF and Kean registrations; the task prompt forbade writing outside the packet, so none were written. The coordinator's notice on the matched_date checker bug was acknowledged; batch-check passed without that error.

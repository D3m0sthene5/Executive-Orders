# Producer report, packet y11 (baldus)

Start 2026-11-25 (resumed after context loss; final run ended 2026-11-25T16:50Z). Final applied directory: applied-v6.

## Outcome per order
All nine submitted as YES (operative on 2026-10-14); none blocked, none found out of force. Basis for every operative clause is the registered original text with the three bounded searches (current-law:usc, current-law:ecfr, later-events:ofr_catalog), because the CURRENT: USC and eCFR records are custody_record_only and fail the selected-source check (v1 and v2 failed on it; the statute and regulation records are cited in clause reasons only as context).
- EO:12830 operative (4 clauses; inventory split Sec. 1/Sec. 2). Amended by EO 13286 sec 28.
- EO:12879 operative (11 clauses); no later instrument.
- EO:12938 operative (27 clauses; declaration clause added, order formula merged into it). Sec 4 restated (EO 13094, 13382), sec 6 amended, 3(e) added (EO 13128); 29 notices held through Nov 5, 2025 (2009 not held).
- EO:12957 operative (13 clauses; declaration added). EO 12959 sec 5 and the OFR "revoked in part" notes treated as not ending (conditional "to the extent inconsistent"; Pub. L. 109-293 sec 101 keeps secs 1 and 3). Notices held 2011-2026 only.
- EO:12959 operative (23 clauses); paragraphs 1(a)-(d),(f) ended 1997-08-20 (EO 13059 sec 7); sec 8 exceptions (i),(ii) ended 1995-06-06 by own terms. Notices held through March 2025 (2000, 2017 absent); statute is the continuing predicate.
- EO:12978 operative (21 clauses; declaration and Annex added). EO 13286 sec 22 amendment; 30 notices through Oct 16, 2025.
- EO:13059 operative (32 clauses); 23 notices 2001-2026 (2015-2017 not held).
- EO:13106 operative (15 clauses; two-character span merged into 3(c)); Sections 1-7 ended 1999-12-21 (EO 13144 sec 8; alternative reading 2000-01-01 disclosed); Section 8 operative.
- EO:13111 operative (49 clauses); Sections 5-7 ended 2003-01-11 (EO 13188 amendment of 7(f)); EO 13316 revocation 2003-09-30 recorded as formal disposition. Sections 1-4, 8, 9 operative.

## Judgment calls to review
Transmittal, effective-date and no-rights clauses are recorded operative, not completed. Dossier chain events mislabelled for 12830 (EO 12977) and 13111 (EO 13210, 13227, 13278) are copies of the 13286/13316 text and were not used. Assessment first_cause is "unresolved" for all because no whole-order end exists.

## Time
Most time went on reading texts and building clause tables for 12959, 13111 (49 clauses) and 12938 (restated Section 4), then on fixing custody and short-quote failures.

## Batch-check (applied-v6)
9 packet members, 9 strict pass, 0 fail; actual checker 9 all passed, 0 unverified; batch-check run took about 95 s. Earlier: v1 and v2 rejected (unknown 13286 evidence id for 12978; custody_record_only CURRENT sources); v3 passed but 3 tiny-span "too_short_to_verify" notes; v4 and v5 fixed those.

## Geddes (applied-v6)
3 flags, all unaddressed_citing_instrument, recorded disputed in GEDDES_RESOLUTIONS.json: 76d4b80cc3f2427c (12957, EO 13313), d7375a7ae702b82b (12978, EO 13313), 988da861249b65b8 (13111, EO 14207). Earlier citation-mismatch and unsourced-actor flags were fixed in v6 by wording changes. 15 coverage gaps reported by the lint, not flags.

## Files opened beyond the views
LOOKUPS.md in full; PACKET.json via batch.load_packet; READ.md and LOOKUPS.details.json by line lookup only; jobs/later-events/output/EDGES.csv and current-law MENTIONS files (filtered).

## Tool defects
None blocking. Geddes flags on notice FR citations ("reasoning cites 91 FR 10937; pinned original cites ...") fire on legitimate citations of continuation notices.

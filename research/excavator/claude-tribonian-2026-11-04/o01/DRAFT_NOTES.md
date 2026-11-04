# o01 draft judgments (producer claude), written at coordinator stop, 2026-11-04

Start UTC 2026-11-04T04:48:12Z. No kit.py command was run; decisions.csv and clauses.csv in the packet are untouched (backups .orig were not made). One file was added inside the packet before the stop: packet/producer_build.py, an unrun generator holding the full drafted sheets (rationales, clause reasons, later events). It reads decisions.csv/clauses.csv and writes them, with .orig backups. It has bugs to check before use (e.g. EO 7738/8007 reason string assembly, an unused fr variable) and its quotes must be re-verified against the re-prepared packet.

All 30 orders have provisional status "no". Sources I read: PRODUCTION_ROUTE, BATCH, CLAIM_SCHEMA, the six rulings, the NIRA sheet-field example, views for all orders, held APP/FR texts cited below. Full-packet files opened beyond views: PACKET.json via batch.load_packet (evidence ids and TERM spans), decisions.csv, clauses.csv, LOOKUPS.md (summary lines).

## Family A: 22 compulsory-retirement exemptions (one clause each, `#whole`)
7912, 7914, 7929, 7930, 7931, 7932, 7935, 7945, 7949, 7950, 7954, 7958, 7973, 7974, 7978, 7982, 7988, 7989, 7991, 7995, 7996, 8002.
Decision: submit, state terminated, first end = own terms, date = stated "ending" date inclusive (exclusive reading disclosed per ruling 2026-10-21 until-dates), mechanism own_terms_fixed_term, end_id = the TERM evidence at the registered APP text hash whose span holds the operative sentence ("I hereby [further] exempt ... for a period of ... ending X."), savings transferred_or_accrued with the same TERM as source, search_ids all four (current-law:usc, current-law:ecfr, later-events:ofr_catalog, namier:held_texts_person_name). original_confirmed false, original_pages_confirmed true; working_text prefilled with machine Lachmann confirmations (true for the order's own APP text; extension texts must be set true after the APP page check below).
End dates: 7912 1939-09-30; 7914 1939-07-31; 7929 1939-07-31; 7930 1939-07-31; 7931 1939-11-30; 7932 1939-09-30; 7935 1939-07-31; 7945 1939-08-31; 7949 1939-08-31; 7950 1939-09-30; 7954 1939-09-30; 7958 1939-09-30; 7973 1939-09-30; 7974 1939-10-31; 7978 1939-09-30; 7982 1939-09-30; 7988 1939-10-31; 7989 1939-10-31; 7991 1939-11-30; 7995 1940-01-31; 7996 1939-11-30; 8002 1939-07-31 (six months, not one year).
Recital-based earlier exemptions (separate instruments, not ends): 7912 (EO 7637, ending 1938-09-30), 7930 (EO 7667, ending 1938-07-31), 7945 (EO 7413 and 7635).
Later extension orders (later events, ACTOR_TEXT ids exist in the dossiers; each is a further exemption, not an end; page record in MIRROR_DOCUMENTS checked: heading names number, date and text_sha256 agree):
- 7945: EO 8231, signed 1939-08-31, six months ending 1940-02-29.
- 7958: EO 8252, signed 1939-09-14, one year ending 1940-09-30; EO 8543, signed 1940-09-18, one year ending 1941-09-30.
- 7978: EO 8217, signed 1939-08-07, six months ending 1940-03-31.
- 7995: EO 8326, signed 1940-01-22, six months ending 1940-07-31.
Machine hit counts (OFR catalog and name search) equal the extension counts above for these four and are 0 for the rest. No other held order found for these persons (I listed held app-executive-orders filenames with "retirement" and the surnames; the other same-name orders are earlier or are different people).
Identity notes: register title says "Marlon C. Hargrove" (7931) and "Alfred R. Wheat" (7973) but the APP heading and held text say Marion C. Hargrove and Joseph H. Wheat; the page check passes on the APP heading. 8002 capture is Wayback; the others are Common Crawl.
Open for producer: confirm that the extension texts' working_text confirmations (EO 8231, 8252, 8543, 8217, 8326) get identity/complete/pages true; all five passed my page check.

## EO 7747 (San Clemente Island defensive sea area), submit
Original: FR print 2 FR 2947 (fr-originals EO_7747.txt), original_confirmed true. One clause (`#whole`, three paragraphs: area, navigation restriction, penalty) retained; all depend on the area.
End: EO 9894 (signed 1947-09-23, 12 FR 6353) discontinues the area "established by Executive Order No. 7747 ... as amended by 8536 and 9787"; evidence ACTOR_TEXT:EO:9894; mechanism express discontinuance; date 1947-09-23.
Later events: EO 8536 (1940-09-06; strike "three hundred yards", insert "one nautical mile", add the naming sentence), id ACT:EO:7747>EO:8536; EO 9787 (1946-10-05; restates the order to read as follows: 300 yards, 100 yards in Wilson Cove, part of Pyramid Cove), id ACT:EO:7747>EO:9787. Both amendments, not ends (strike-and-insert ruling).
Savings: none_after_bounded_search, source ACTOR_TEXT:EO:9894 (no saving in 9894; US Code and eCFR searches zero hits).
Avoid quotes across FR OCR line breaks; paraphrase.

## EO 7831 (amends EO 7293 Table I naval-mission wording), submit
Original FR 3 FR 641, original_confirmed true; one clause. 
End: EO 8704 (signed 1941-03-04, 6 FR 1302) supersedes EO 7293 as amended by 7831, 8107, 8440, 8674, effective as of its date except continental-US quarters allowance (effective 1941-07-01). Brazil/Peru naval-mission exception is not a continental quarters allowance, so first end 1941-03-04 with 1941-07-01 disclosed as alternative. Evidence ACT:EO:7831>EO:8704.
Later event: EO 8107 (1939-05-03; strikes "Naval Missions to Brazil and Peru:", inserts "Naval Missions to Brazil, Peru, and Colombia:"), id ACT:EO:7831>EO:8107. Strike-and-insert: continues amended until parent ends.
Do NOT cite the chain event for EO 8109 (it is the Waianae-Kai order on the same FR page; the chain hit is page overlap). 8440 and 8674 contain no Brazil/Peru wording (grep), so they are not events of this clause; do not name them as events.
Savings: transferred_or_accrued, source ACT:EO:7831>EO:8704 (8704 Table I Exception No. 3 covers Naval Missions to Brazil, Colombia, Ecuador, Peru ...).

## EO 7845 (annual leave regulations), submit with corrected inventory
Original FR 3 FR 715-717, original_confirmed true. Dossier inventory (37 clauses) needs correction via inventory_overrides on ORIGINAL:EO:7845 (offsets in the held file EO_7845.txt):
- add the enacting paragraph (from "By virtue of and pursuant to the authority vested in me by \nsection 7" to just before "\nPart I. Definitions");
- sec 9 span contains the page-2 header and table of contents: split into part 1 (start to just after "cover-") and part 2 (from "ing their absence" to the end of the original sec 9 span);
- sec 19-e span merges 19(e) and 19(f) (OCR prints "(f)" as "if)") and holds a page-3 header: split into 19(e) part 1 (to before "=== PDF page 3"), 19(e) part 2 (from "in accordance with these regulations to employees" through "as prescribed in Executive Orders."), and 19(f) (from "if) Employees" to before "\nPart IV.");
- trim Part II heading from the end of sec1-i and Part III heading from the end of sec18.
All other clauses keep the dossier boundaries. Use new scope ids (e.g. suffix -r1) and blank clause_id.
End for regulatory clauses: EO 8384 (signed 1940-03-29) sec 21: "shall supersede Executive Orders No. 7845 ..., No. 7879 ... and No. 8226 ... and shall be effective as of March 2, 1940, except that sections 6 and 9 shall be effective as of July 1, 1936" (8384's own sections 6 and 9, leave adjustment, with a cap proviso). First end 1940-03-02; disclose signing date 1940-03-29 and the retroactive 1936 date for 7845 sec 6 and 9. Evidence ACT:EO:7845>EO:8384; mechanism express supersession of whole order.
One-time commands, ended by performance (BATCH.md: a later revocation does not prove first cessation of a performed command; ruling 2026-10-28): sec 20 (ratify and revoke inconsistent regulations) and sec 21 (effective as of 1938-01-01, supersede EO 7409) performed on issuance 1938-03-21 (alternative effective date 1938-01-01), end_id ORIGINAL:EO:7845; sec 22 (publish) performed by publication in the 1938-03-23 FR issue (page headers read "Wednesday, March 23, 1938"; filed 1938-03-22). This is a judgment call; the alternative is to end sec 20-22 at 1940-03-02 with all others.
Later events: sec 6 restated by EO 7879 (signed 1938-05-09, effective as of 1938-01-01; adds "emergency, or indefinite" positions), id ACT:EO:7845>EO:7879; sec 15 restated by EO 8226 (signed 1939-08-24, effective as of 1939-06-30; adds indefinite/emergency appointments and credit/charge language), id ACT:EO:7845>EO:8226. Chain entries for EO 7880 (amends sec 9 of EO 7846, the sick-leave order) and the "section 7" tag on 8226 are noise; do not cite 7880.
Savings: transferred_or_accrued, source ACT:EO:7845>EO:8384 (leave credit cap proviso carries credits into the new regime).

## EO 7738 and EO 8007 (Civil Service Rules Schedule A, Subdivision VII, paragraph 6), submit
Both FR originals (2 FR 2867 for 7738; 8007 is the FR print with closing number [No. 8007], filed 1938-11-17), original_confirmed true, one clause each, no TERM evidence exists, so end_id = CLAUSES:EO:N#whole.
7738: amends paragraph 6 to cover temporary postal clerks, carriers and laborers for holiday business "from November 15, 1937, to January 15, 1938." End 1938-01-15 (inclusive; exclusive alternative), own terms of the installed text. 
8007: same paragraph for "November 15, 1938, to January 15, 1939." End 1939-01-15.
Quotes: "to January 15, 1938." and "to January 15, 1939." are single-line in the FR text. Do not name 8007 as a later event of 7738 (no citable evidence; it restates the rule for the next season after the window had closed). Chain empty and OFR catalog zero hits for both. Savings: none_after_bounded_search, source ORIGINAL.

## EO 7980 (postponement of EO 6166 sec. 4 for US Marshals disbursement), submit only if the apply accepts it
Problem: the dossier clause (chars 1859-3089) and its only TERM evidence are the text of EO 7981 (Schedule B amendment) on the same FR page; own_text_boundary says verified_whole_order false, coverage_gap order_heading_unresolved. Correct inventory: one clause, ORIGINAL:EO:7980, from "EXECU TIVE ORDER\nPostponement" through the document line ending "3:20 p.m .]" (compute offsets in EO_7980.txt). End: own terms, "be further delayed until December 31, 1938," (single-line quote), date 1938-12-31 inclusive; end_id ORIGINAL:EO:7980 (no usable TERM). If apply or batch-check refuses on the unverified boundary, block with that reason.
Known but not citable from this packet: serial postponement orders EO 8026 (signed 1938-12-23, delay to 1939-06-30), EO 8182 (delay to 1940-06-30), earlier 7917 (to 1938-09-30). They are separate commands; 8026 was signed before 7980's date ran out. Not named in the claim text; mention to the coordinator that a source supplement would be needed to cite them as later events.

## Blocked
EO 7554 (restates sec. 1 of EO 7180, PRRA loan purposes) and EO 7689 (appoints the Secretary of the Interior as PRRA Administrator, authorizes assistant administrator and delegation, amends EO 7057/7180/7493): block. Gap: no held instrument ends EO 7180 as amended, the PRRA's loan authority, or the Administrator's delegation authority; the instrument or statute terminating the Puerto Rico Reconstruction Administration is not held. Regex search of held texts for PRRA near abolish/terminate/dissolve/liquidate/discontinue and EO 7180 near revoke/supersede/rescind: no hits. For 7689 the Secretary's own tenure end is also undated (EO 8294 of 1939-11-30 appoints Leahy "vice Ickes, resigned", no resignation date); later appointment orders 8888, 9278, 9618, 9901, 10468 keep appointing administrators.
Tell the coordinator: 7554's ACT for EO 7689 and the chain amendments are appointments or "amended accordingly" lines, not ends.

## Per-order time notes
Retirement family: fast once the pattern was fixed; time went into extension-order texts and page checks. 7845: inventory correction (37 clauses, page-break junk) and the performance-versus-supersession call for sec 20-22. 7980: discovering the mislocated clause. 7747/7831: tracing amendments and checking 8109 and 8440/8674 noise. 7554/7689: searching for any PRRA-ending source.

## Not done
No apply, batch-check, Geddes lint or PRODUCER_REPORT.md. No hand-off message beyond this note.

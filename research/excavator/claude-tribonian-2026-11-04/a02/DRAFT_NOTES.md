# a02 producer draft notes (started 2026-11-04T04:48:13Z; stopped on coordinator order, packet stale)

No kit.py apply or batch-check was run. Nothing was written inside the packet. My helper scripts and the backup copies of decisions.csv and clauses.csv are in the session scratchpad under a02work/. The packet-view paths vanished when the packet was removed for re-preparation.

All 33 orders have provisional status NO. Only the 15 Emergency Preparedness orders plus EO 10656, 10700, 10460, 11209 and 11120 were checked closely enough to treat as likely submits.

## Rules and format learned
- whole_order_end is the maximum of the clauses' first_end dates.
- The savings state must be one of none_after_bounded_search, continuing_independent or transferred_or_accrued, with a source.
- conflict_resolutions is keyed by conflict code.
- A later instrument is citable only if it has an ACT or ACTOR_TEXT evidence id in the packet. A provision merely named in "missing" is not citable.
- A corrected inventory needs inventory_source_id = ORIGINAL:EO:N, absolute char offsets in the held text file, and a new scope_id per clause. It also needs clause_id left blank.
- For FR originals, original_confirmed is true, and I planned original_pages_confirmed false because I read only the text layer.
- The working_text confirmations must be set true for the cited later-text source, and the standing note stays.
- Do not quote text that contains line breaks or OCR noise. Do not quote a clause-drafts copy.

## Travel-expense family: BLOCK all ten
Orders: 9778, 9805, 9933, 9997, 10069, 10177, 10196, 10274, 10381, 10507.
- EO 11012 (27 FR 2983, 1962-03-27) sec 3 revokes each of them: 9778 (a), 9805 (b), 9933 (c), 9997 (d), 10069 (e), 10177 (f), 10196 (g), 10274 (h), 10381 (i), 10507 (j).
- The revocation takes effect on the date the initial regulations issued by the Bureau of the Budget (later OMB) and by GSA under that order become effective.
- Missing source: the Bureau of the Budget circular (A-56, as revised under EO 11012) and the GSA regulation on commuted rates, or a Federal Register notice. It must show the date both initial regulations took effect.
- Searches of held texts for Circular A-56, Federal Travel Regulations and EO 11012 found no such source. The 1989 OFR codification text of EO 11012 gives no date.

## EO 10085 (amends sec 1(d) of EO 10011): BLOCK
- Revoked by EO 10903 sec 5(a)(3), dated 1961-01-09 (26 FR 217, held in fr-originals as EO_10903.txt). Sec 5(b) saves existing rules and actions.
- The packet has no citable ACT record for EO 10903 ("target provision not located"), so it needs an act override or a source supplement.
- Section 1(d) was restated in full by EO 10187, 10313 and 10391. Under the strike-and-insert ruling these are later events: the clause continues as amended until the parent ends. EO 10477 and 10853 amend other parts of EO 10011.

## Emergency Preparedness family: likely SUBMIT
Orders: 10346, 10997, 10998, 11000, 11001, 11002, 11003, 11004, 11088, 11090, 11091, 11092, 11093, 11094, 11095.
- End: EO 11490 of 1969-10-28, sec 3015, "The following are hereby revoked:".
- The list items are 10346 (4), 10997 (5), 10998 (6), 11000 (8), 11001 (9), 11002 (10), 11003 (11), 11004 (12), 11088 (15), 11090 (17), 11091 (18), 11092 (19), 11093 (20), 11094 (21), 11095 (22).
- No effective-date clause was found in the held text of EO 11490, so the revocation is effective on signing. I checked 11490 sections 3014 and 3015 by reading them in full.
- Sec 3014 reads "Except as provided in Section 3015, nothing in this order shall be deemed to derogate from any now existing assignment...". There is a line break inside this phrase in the held bytes, so do not quote it; paraphrase.
- End source: the FR text in jobs/family-rule-tail/output/texts/EO_11490_tail.txt. Its ACT record spans roughly chars 123705-125622 for 10997, and each order has its own ACT id ending in the tail path. Held_text_lead grade; working_text confirmation applies.
- Use the APP mirror record for 11090 only. The FR text there is garbled ("No.ll090") and the packet has only APP ACT records for it. The APP page check for 11490 passed: heading, date and text_sha256 match the MIRROR_DOCUMENTS row for sha d6209290.
- Machine inventories are bad: they split at lettered paragraphs and miss sections.
- Replace them with section-level override scopes, plus a lead scope, in the held text file between own_text_boundary char_start and char_end. My split.py and ep.py regex found each "Sec. N." heading.
- The OCR-damaged headings need a manual add for 11090, "S ec. S." (Sec. 3) at char offset 2132. 11091 "Sec. 4" has no period.
- Revocation sentences in the final "Prior Actions" section, split into precedence and revocation scopes:
  - 10997: EP Order No. 7
  - 10998: EP Order No. 1
  - 11000: EP Order No. 8
  - 11001: EP Orders Nos. 4 and 5
  - 11002: EP Order No. 9
  - 11003: EP Order No. 3
  - 11004: EP Order No. 6
  - 11091: EP Order No. 12
  - 11094: EP Order No. 10 and Defense Mobilization Orders 1-20, 1-22 and 1-24 (superseded and revoked)
  - 11095: EP Orders 11, 13 and 14
- 11088, 11090 and 11093 have only a precedence rule. 11092 sec 9 is a non-derogation and continuation clause for the telecommunications orders under EO 10705, 10995 and 11051. It ended with the order.
- The revocation scopes are spent on signing (1962-02-16 or 1963-02-26), by performance under the owner's ruling 1.
- EO 11000 is recited as in force by EO 11091 (1963, manpower plans "pursuant to Executive Order No. 11000"). That is not an end.
- EO 10346 specifics:
  - The packet inventory is wrong: its clause spans 12399-17689 are neighbouring orders, and the boundary is unverified.
  - The true order has Sec. 1 (plans, around char 9300 in EO_10346.txt), Sec. 2 (continuity plans, at 9375) and Sec. 3 (Civil Defense Administrator). The heading "EXECUTIVE ORDER 10346" begins before Sec. 1.
  - EO 11051 (1962-09-27, Part VI sec 601 item 3) amends only references in the penultimate sentence of sec 2. That is an amendment, not an end. It is citable as a later event, as the ACT record in the chain.
  - EO 10438 (transfer of NSRB functions) and EO 10773 (reference changes) cite it by number but are not citable in the packet. Mention them only as read, not ends.
- Savings: none_after_bounded_search, with sec 3014 and 3015 read.
- Order-specific text for the reasons must not be copied from siblings.

## EO 10656 (President's Board of Consultants on Foreign Intelligence Activities): likely SUBMIT
- Revoked by EO 10938 sec 4 (26 FR 3951, signed 1961-05-04). The sentence reads "Executive Order No. 10656 of February 6, 1956, is hereby revoked." Whole-order end 1961-05-04.
- The order itself is effective as of 1956-01-13 (sec 6). The packet inventory lacks sec 1 (establishment) and sec 6 (effective date) and needs a section-level override.
- Sec 5 funds the Board from the "Special Projects" appropriation.

## EO 10700 (Operations Coordinating Board): likely SUBMIT (not yet read in full)
- Revoked wholly by EO 10920 (1961-02-18), APP source only. It was amended by EO 10838 (1959-09-16, section 1(b)). That is a later event.
- Need to read the full text, EO 10920 and the APP page check. The working_text lists the 10838, 10920 and 10700 APP texts.

## EO 10460 (Director of Defense Mobilization, telecommunications): likely SUBMIT
- Revoked by EO 10995 of 1962-02-16, in sec 4: "Executive Order No. 10460 of June 16, 1953, is hereby revoked." Source is APP only: the transcription at jobs/app-executive-orders/output/texts/executive-order-10995-assigning-telecommunications-management-functions.txt. It needs an APP page check; not yet done.
- 10995 has no delayed effective clause. The dossier conflict is WHOLE_END_DATE_DISAGREEMENT between 10995 (1962-02-16) and EO 14148 (2025-01-20). Resolve it as follows: 10995 revoked the order by name; 14148 would at most repeat an already ended order. I did not read 14148.
- Sec 5 transfers records and personnel to ODM (one-time act). Sec 6 revokes EO 10297 (one-time).
- Sec 3 sets the Interdepartmental Radio Advisory Committee's reporting duty.
- The USC note says "eff. June 18, 1953".

## EO 11209 (Federal Development Committee for Appalachia): likely SUBMIT
- Ended by EO 11386 sec 1(b) (1967-12-28, FR text held, filed 1968-01-02): "The Federal Development Committee for Appalachia, established by Executive Order No. 11209 of March 25, 1965, is hereby abolished and that order is hereby revoked."
- Dossier conflict FULL_AND_PARTIAL_EVIDENCE_CONFLICT for EO 11386. Resolve it as follows: the sentence names 11209 and revokes it in full, while the other parts of sec 1 amend other orders.
- Not yet checked: whether 11386 has a delayed effective clause, or its sec 1(b) numbering.

## Pay family: EO 10152, 10168, 11120
- Revoked by EO 11157 sec 502, signed 1964-06-22 (29 FR 7973). The list is (b) 10152, (c) 10168, (l) 11120. There is no effective-date clause in the FR text of 11157. The sentence reads "The following Executive orders are revoked:".
- EO 10152 was amended by 10618, 10681, 10739, 10892 and 11120. EO 10168 was amended by 10821, 10989 and 11120. These are later events, with before-and-after text under ruling 2.
- EO 11120 was amended by EO 11146 (1964-03-13).
- The statutory recodification of title 37 is not an end under the evidence-decides ruling.
- Not yet read: the large texts and the amendment orders. 10152 has 30 machine clauses (~20k chars) and 10168 has 40 (~63k chars).

## Not done
- No decisions.csv or clauses.csv edits are installed in the packet.
- No Geddes lint.
- No PRODUCER_REPORT.md.
- Full-packet files opened beyond the views: none. I opened the packet files READ.md and LOOKUPS.md? No: I read neither. I did read decisions.csv and clauses.csv headers, PACKET.json via batch.load_packet(check_sources=False), and the repo texts cited above.

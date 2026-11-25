# Producer report: packet y06 (agent baldus)

Start 2026-11-25T15:42:18Z. End 2026-11-25T16:01:35Z.
Final applied directory: `applied-v4` (applied-v1 to v3 kept; v1 and v2 rejected for source custody, see defects).

## Outcomes

| Order | Outcome | Why |
|---|---|---|
| EO:11926 | submit YES | Section 1 missing from the dossier inventory (OCR "Section  l."), added by override; Section 7 split into its supersession of EO 11544 (executed 1976-07-19) and its continuing proviso. Amendments by EO 13286 (eff. 2003-03-01), EO 13373 (2005-03-10), EO 14131 (2024-12-20) listed as later events; clauses continue as amended. |
| EO:11964 | submit YES | No later instrument found; all six clauses operative; no own-terms end (July 15, 1977 defines the class of vessels, not an end). |
| EO:11988 | blocked | Net effect on the 2015 amendments (EO 13690) of EO 13807 (2017 revocation), EO 14030 (2021 reinstatement) and EO 14148 (2025 revocation of EO 14030) is not stated by any held source; EO 14148 is not citable from this packet. 25-clause inventory also irregular. |
| EO:11997 | submit YES | Section 5 split into revocation of EO 11968 (executed 1977-06-22) and savings sentence (continuing). No later instrument found. |
| EO:12028 | blocked | Sec. 6, 7(a), 7(b) end on the transfer effective date, "April 1, 1978 or at such earlier time" as the OMB Director determines; no OMB determination held, so the end is only bounded and v1 cannot carry a bound. Inventory defects (spurious `sec1-1977`, Sec. 6 and Sec. 4(a)(4) missing). |
| EO:12038 | blocked | 28 clauses each amend or reassign functions under another order; current text or status of most target orders is not held; PROC identities absent from census. |
| EO:12047 | blocked | Secs. 1-3 name the USIA Director; the text of Pub. L. 105-277 div. G (22 U.S.C. 6531, 6532, 6551) abolishing USIA is not in this packet's dossier, so the change of designee cannot be dated or cited as a later event. Order was applied by State on 2026-10-02 (91 FR 62802), so operative force is yes. |
| EO:12058 | blocked | Each section delegates functions vested by named provisions of the Nuclear Non-Proliferation Act and the Atomic Energy Act; no current text of those provisions is held, so survival of each delegated function on 2026-10-14 is not shown. |
| EO:12067 | submit YES | Only 1-101 ends (own date, 1978-07-01); 24 clauses operative; EO 12107 (eff. 1979-01-01) substitution recorded on 1-302. The dossier's "rescission 2017-01-03" conflict is a spurious lead (EEOC rule 82 FR 654 cites the order as authority and does not rescind it); resolved in conflict_resolutions. |

Totals: 4 submitted, 5 blocked. None of the held evidence showed an order not in force on 2026-10-14, so no ledger-contradicting block was needed.

## Route and sources

All four submitted claims use the original-text route: `current_basis_id` is the held Federal Register original, read with `current-law:usc` (release point 119-121, through 2026-10-09), `current-law:ecfr` (as of 2026-10-14) and `later-events:ofr_catalog` (checked 2026-11-25). The `CURRENT:` records (U.S. Code note, eCFR title 31 XML) are custody_record_only and were not used as sources; they appear only as leads in reasoning.

## What took the time (one line each)

- EO 11926: reading three amending orders and finding the Section 1 inventory defect; building overrides.
- EO 11964: confirming no later events and checking the 2022 Navy notice and CFR authority lines.
- EO 11988: tracing EO 13690, 13807, 14030, 14148 and the 2026 HUD proposed rule; concluded block.
- EO 11997: Section 5 split; confirming 31 CFR 215 still names the order.
- EO 12028: reading EO 12122 and 12134 and the Sec. 7(b) bound; concluded block.
- EO 12038: scanning 28 clause scopes and 19 actor contexts; concluded block at once.
- EO 12047: reading EO 12388, the Code note and the 2026 State notice; concluded block on missing statute text.
- EO 12058: reading the delegation clauses against the statute holdings; concluded block.
- EO 12067: 25 clauses, EO 12107 effective-date reading, resolving the conflict lead.

## batch-check (applied-v4)

packet_members 9; claims_checked 4; strict_claim_pass 4; strict_claim_fail 0; outcomes: assembled_proposal 4, blocked 5; actual checker: claims_checked 4, claims_all_checks_passed 4, mechanical_pass 4, mechanical_unverified 0, mechanical_fail 0, gate_passed 4; actionable_failures none; independent_human_certifications 0.

## Geddes

`GEDDES_LINT.json` in applied-v4: 0 defect flags, 10 coverage gaps (citing_corpus_incomplete: 1,401 held texts missing or changed in the inventory; own_order_body_unverified / order_heading_unresolved on 11964, 11997, 12067). Coverage gaps are not flags. `GEDDES_RESOLUTIONS.json` has an empty resolutions list.

## Full-packet files opened beyond the views

- `DISPATCH_CHECK.json` (head only), `HELD_SOURCES.json` (printed member state lines for EO:12047, 12028, 11988, 12038, 12058), `HELD_SUPPLEMENT.json` (head only), `LOOKUPS.md` (read once, as instructed).
- `PACKET.json` was loaded once through `batch.load_packet` (check_sources=False) to read dossier conflicts, original spans, own-term records and evidence record shapes; not catted.
- No other packet folders were opened.

Repository sources outside the packet that were read: held texts of EO 12107, 12122, 12134, 13286, 13373, 13583, 13690, 13807, 14030, 14131, 14148 (windows); `jobs/current-law/output/usc-notes/*` and `usc-sections` listings; `jobs/theophilus-sources/output/texts/cfr-t31-*`; `jobs/selden-fr-citers/output/texts/fr-2016-31397, fr-2022-24484, fr-2026-13939, fr-2026-20213, fr-06-238`; `jobs/later-events/output` and `jobs/current-law/output/ECFR_SEARCH_HITS.csv`; `jobs/claim-kit` and `jobs/claim-checker` code to learn the sheet format.

## Tool defects and notes

- `kit.py apply` refuses an existing destination; the first apply (v1) wrote output although the console tail printed a source-recovery JSON, so each later fix went to a new directory. v1 and v2 used `CURRENT:` records as the current basis and failed the selected-source check (`custody_record_only`: U.S. Code release-point zip and eCFR title 31 XML bytes are not held); v3 and v4 use the held original as the basis.
- The `ACTOR_TEXT:EO:13286@37446` window omits section 92 (the March 1, 2003 effective date); the clause reason states where section 92 sits. No official `ACT:` record exists for EO 13286 section 56; the others are APP mirrors.
- The dossier chain for EO:11926 lists an "EO:12977" amendment whose provision text is EO 13286 section 56 and whose source is a gap note; not cited.
- `kit.py` has no schema v2 option, so bounded ends (EO 12028 Secs. 6-7) cannot be carried and the order was blocked.
- Wall-clock times were short (apply about 10 s; batch-check about 65 s), well below the quoted 10-30 minutes.

## Assessment

`ASSESSMENT.jsonl` has one row per member (9). For orders still in force, `first_cause` is "unresolved" and `formal_revocation_after_earlier_cessation` is "no" because there is no end to classify.

# Producer report: claude-bracton-2026-11-25 / p02 (route: correction)

Start 2026-11-25T10:15:31Z; end 2026-11-25T10:36:26Z (wall clock about 21 minutes). Producer model: Claude Sonnet 5.5, no sub-workers.

Final applied directory: `applied-v2` (applied-v1 had one Geddes flag, fixed in v2).

## Outcomes (3 submitted, 6 blocked)

| Order | Outcome | Why / exact missing source |
|---|---|---|
| EO:11321 | blocked | Board of Inquiry (Taft-Hartley sec. 206) with a report deadline 1966-12-20 and no end in its text; no held source dates the Board's report, discharge or the dispute settlement. Missing: the Board's report/discharge or settlement record for the Dec 1966 Union Carbide (Stellite, Kokomo) dispute. Dossier inventory (16 clauses) belongs to neighbouring FR documents and needs a one-span override (chars 544-2160) when sourced. EO 12553 (1986-02-25) is only the formal disposition. |
| EO:11706 | blocked | Probable first end is Pub. L. 94-455 sec. 1202 (rewrite of IRC sec. 6103, effective 1977-01-01, held at jobs/selden-statutes/output/texts/STATUTE-90-Pg1520.txt) but the packet has no citable evidence id for it, and the pre-1977 sec. 6103(a) text is not held. Missing: source supplement with Pub. L. 94-455 sec. 1202 and old sec. 6103(a). |
| EO:11708 | submit (no) | Express supersession by EO 11768 sec. 4, 1974-02-20 (held FR text). 25-clause dossier inventory confirmed; items (6),(7) of sec. 1 end by EO 11727 deletion (effective as of 1973-07-01), item (8) of sec. 2 by EO 11715 deletion (1973-04-24), sec. 3 spent on 1973-03-23; strike-and-insert amendments recorded as later events with before/after text. The 10 quarantined relationships are resolved (OFR notes on pre-1973 orders amending EO 11248). |
| EO:11771 | blocked | No end in own text; no held source for the end of the PRC Liaison Office or Public Law 93-22 text. Missing: PL 93-22 and an official record of the Liaison Office's end. EO 12553 is only the formal disposition. |
| EO:11812 | submit (no) | Express supersession by EO 11883 sec. 5 read with sec. 4 (replacement rates effective 1975-10-01; alternative reading 1975-10-06 stated). Dossier inventory corrected by six span overrides (sec. 2-4 had been run together; the OCR's adjacent headings had mislabelled sec. 5 as sec. 6). Sec. 5 and 6 are executed-once (1974-10-07, retroactive effect 1974-10-01 as the alternative). The one quarantined relationship (OFR note on EO 11778) is resolved. PL 93-419 (held) is the authority, not an ending instrument. |
| EO:11849 | blocked | No own-terms end. FACA sec. 14(a)(2) two-year default termination (by 1977-04-01 unless renewed) and EO 12110 sec. 1-103(b) ("terminated or work completed", effective 1978-12-31) give only a bound; no held source shows renewal or the termination date. Missing: committee charter/renewal or termination record, or the GSA Committee Management Secretariat annual report 1976-1978, or a Labor Department dissolution notice. |
| EO:12162 | submit (no) | Self-executing amendment of EO 12140 (deleting the first sentence of sec. 1-105) performed on signing 1979-09-28 (precedent mechanism self_executing_amendment_performed_on_issuance); EO 12553 (1986-02-25) is a later event, not the first end. Surviving effect (EO 12140 not lapsing 1979-09-30) in the savings statement. |
| EO:12187 | blocked | Sec. 1-101 is limited by EO 12209 to Jan-Mar 1980, but 1-102/1-103 are restated unchanged; the apparent extinguishing instrument, EO 12287 (1981-01-28, held at jobs/fr-originals/data/full_run/texts/EO_12287.txt), is not citable from the packet. Missing: source supplement adding EO 12287 (and, if relied on, the EPAA expiry text). |
| EO:12189 | blocked | Amendatory restatement of EO 12153 (heavy crude exemption); EO 12209 and EO 12919 leads do not name or end it. Missing: source supplement adding EO 12287 and EO 12153 as amended. |

## What took the time (one line each)
- 11321: held text mislocated the inventory; searched for any board record (none held), blocked.
- 11706: found the statute rewrite in a held 414-page text but no packet evidence id for it.
- 11708: 25 clauses with per-item amendment history (EO 11715, 11727, 11736) and the 10 quarantined leads.
- 11771: searched held texts for the Liaison Office end; none.
- 11812: OCR-garbled sections; inventory correction with absolute spans; effective-date reading of the supersession.
- 11849: FACA sec. 14 and EO 11948/12110 reading; only a bound.
- 12162: read EO 12140 to establish what the deleted sentence did.
- 12187/12189: read EO 12209, 12287, 12153 chain; blocked on citability.

## batch-check (applied-v2)
packet_members 9; claims_checked 3; strict_claim_pass 3; strict_claim_fail 0; actual claim checker 3/3 all checks passed, 3 gate-passed; outcomes: blocked 6, assembled_proposal 3; actionable_failures none. Selected-source check: 3 of 3 mechanically usable. Independent human certifications 0.

## Geddes
applied-v1: 1 flag (EO:11812, event_precedes_order, sec. 5 date 1974-10-01 before the order's own date 1974-10-07), fixed in applied-v2 (flag_id 87f88e00d54c10c9, recorded in applied-v2/GEDDES_RESOLUTIONS.json). applied-v2: 0 flags; 3 coverage gaps (EO:11708 unclassified mention of EO 11248 as the revoked target in sec. 3, which is a target and not an acting instrument; EO:11812 two literal-name search notices), no defects.

## Notes for the coordinator
- The tracker's QUARANTINED_RELATIONSHIP_CONFLICT for EO 11708 and EO 11812 (step counterevidence, not ending) comes from the Stage 19 causal queue count (quarantined_relationship_count) and is not cleared by claim text; the claims resolve each quarantined edge through conflict_resolutions, which the tracker may still count.
- EO 11321, 11706, 12187, 12189 would unblock with a source supplement (EO 12287, Pub. L. 94-455, EO 12153) prepared by the coordinator; I did not run prepare.

## Full-packet files opened beyond the views
None of READ.md, PACKET.json, LOOKUPS.details.json were read directly; PACKET.json was loaded once per script through batch.load_packet (check_sources=False) to list evidence records and dossier conflicts (evidence text spans for EO 11708, 11812 and conflict ids). decisions.csv, clauses.csv, DISPATCH_CHECK.json (head only) and LOOKUPS.md were read.

## Tool defects
None blocking. The packet's evidence ids only cover instruments named by the dossier, so a producer cannot cite a held instrument (EO 12287, Pub. L. 94-455) that the dossier did not surface; this is what forced four blocks.

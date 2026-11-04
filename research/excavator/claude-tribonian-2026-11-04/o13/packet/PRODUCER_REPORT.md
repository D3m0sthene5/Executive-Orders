# Producer report, packet o13 (Tribonian fresh lot)

Producer: Claude (Sonnet 5.5). Start 2026-11-04T06:08:35Z. End 2026-11-04T06:39:24Z.
Final applied directory: applied-v2 (applied-v1 superseded: its GEDDES_LINT.json was written twice at once and one Geddes flag, a quotation of "until and including" broken by OCR hyphenation in EO 10397, was fixed in v2).

## Outcome per order (10 submitted, 20 blocked)

Submitted (all own-terms ends, performed one-time acts, or amended fixed ends; every inventory corrected by override to the operative sentence):
- EO 10229: exemption of Bennett, fixed term ending 1952-04-30 (inclusive; exclusive alternative stated).
- EO 10236: amendment of EO 10129 para 8, sunset at end of 1951-05-31. Census register title is that of the amended order; identity confirmed by number, date and Federal Register heading.
- EO 10255: further exemption of Draper, five years expiring 1956-06-22 (inclusive).
- EO 10320: further exemption of Lawson, one year ending 1953-01-31 (inclusive).
- EO 10397: continuation of Army and Air Force appointments until and including 1953-04-01.
- EO 10417A: one-day closing, 1952-12-26.
- EO 10334: indefinite exemption of Mayer, amended by EO 10569 (signed 1954-10-05) to "until December 31, 1954"; first end 1954-12-31 (own terms as amended), amendment recorded as later event with before and after text.
- EO 10356: date substitution in EO 10349; amended by EO 10362 and EO 10367 (later events); first end 1952-07-03 (own terms as amended, inclusive).
- EO 10388: revocation of EO 8616, exhausted by performance on signing 1952-08-27; consequence in savings.
- EO 10295: seal approval, exhausted by performance on signing 1951-09-28; the dossier conflict (1989 Codification prints it as in force) is answered in conflict_resolutions; the approved seal's continued use is a consequence recorded in savings. A reviewer may dispute whether a performance end fits an approval that still names the official seal.

Blocked (precise gaps are in decisions.csv unresolved_material_gaps):
- Congress-term orders, 10 (EO 10275, 10321, 10326, 10331, 10343, 10412, 10435, 10442; plus EO 10279 and 10304 whose limit is a Senate resolution with no calendar end). For the Congress-limited ones the end date needs the session dates and U.S. Const. amend. XX sec. 1. A held capture exists (jobs/source-ladder/output/texts/queue_EO_11065_87th_Congress_term_dates_..._1fo_1629d9be9b.txt, SHA-256 ae41559e675086cd43b8f55648a5021e8fe6a9c48d2ec1990987ea933aa458e5; it lists 82nd and 83rd Congress session dates) but it is not registered in this packet's dossier and producers may not run a source supplement. EO 10279 and 10304 additionally need the Senate resolutions.
- Indefinite exemptions with person-dependent ends, 7 (EO 10239, 10273, 10315, 10330, 10333, 10364, 10405; EO 10334 is submitted through its amendment). No held source dates the successor's appointment or the person's separation; EO 10273's June 30, 1955 is a not-later-than bound. EO 10364 also has a wrong dossier inventory (38 clauses from neighbouring Federal Register material).
- EO 10237 (no end instrument registered; EO 10450 only recites it), EO 10245 (end contingent on the Commission's completion report, no held record), EO 10263 (sections 4 and 7 have no end and no later instrument is registered; the machine inventory omits sections 5 to 8).

## What took the time (one line each)
- Reading all 30 texts and classifying: most of the session. Congress-term and indefinite-exemption orders were decided as blocks after confirming no registered end source.
- EO 10229, 10255, 10320, 10397, 10417A, 10236: inventory span override and own-terms date; APP transcription ends were dropped because the assembler rejects working texts when an official copy is held, so the ends cite the Federal Register text (or its registered own-term record).
- EO 10334 and 10356: reading the amending orders to fix the final amended date.
- EO 10388, 10295: deciding performance versus continuing effect; 10295 needed the conflict resolution.

## Checks
- apply v2: 10 assembled_proposal, 20 blocked. batch-check v2: 10 claims checked, strict pass 10, fail 0; actual claim-checker all_checks_passed 10, mechanical pass 10, unverified 0, fail 0.
- Geddes (applied-v2): 0 defect flags, 0 coverage gaps. GEDDES_RESOLUTIONS.json records no resolutions. (v1 had one flag, fixed in v2.)

## Full-packet files opened beyond the views
LOOKUPS.md (read in part), decisions.csv and clauses.csv (edited), PACKET.json once through batch.load_packet to export dossier evidence ids and spans (also loaded by my own in-process pre-check harness in /tmp/claude-0/tribonian-work/o13/ before each apply), and one `kit.py view --order EO:10229`.
Repository sources outside the packet, read to resolve points: jobs/fr-originals texts for EO 10349, 10362, 10367, 10368 and 10364; jobs/ofr-codification-1989 EO_10295.txt; the source-ladder text carrying 32 CFR 1800.2 (cites EO 10295); the source-ladder House History session-dates capture; app-executive-orders MIRROR_DOCUMENTS.jsonl (APP page checks, later not needed); three committed claim files under research/readiness/claims (mechanism-label precedents only). Held-text regex searches with cruden.py for the order numbers, person names and subjects.

## Tool defects
- batch-check itself writes GEDDES_LINT.json; running geddes lint by hand into the same file at the same time left v1's file with duplicated trailing text. v2 was written by batch-check alone.
- ORIGINAL-record end sources quote the whole registered text file (about 5 thousand characters) because an original-span override record carries no actor and cannot be an end source.

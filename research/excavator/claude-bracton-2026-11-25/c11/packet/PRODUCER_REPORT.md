# Producer report, c11 (Claude, correction route)

Start 2026-11-25T09:15:12Z. End 2026-11-25T09:26:30Z (approximate).

## Result: apply did not run

`kit.py apply` (and so batch-check and the Geddes lint) stopped at once with `claim-kit: changed prior research; prepare a new version`. Per the brief I did not work around it. No applied-v1 directory exists, no claim was assembled and batch-check counts are 0 of 0.

Diagnosis, read-only: `prior_research.collect(repo, dossiers, exclude=packet)` differs from `PACKET.json["prior_research"]`. The recorded version locations carry file hashes and a `current_canonical` flag that the current collection does not, and the current input pins include nine `jobs/astra-source-retention/output/pages/...` files the packet does not pin. The repository checkout has therefore changed since the packet was prepared. I wrote nothing outside this packet and the scratch folder that could cause it. The filled sheets are kept in the packet and in /home/claude/bracton-scr/work/c11/ (fill.py and content.py regenerate them from the prepared sheets saved as decisions.orig.csv and clauses.orig.csv).

## Outcome per order

Sheets are filled in `decisions.csv` and `clauses.csv`. Quoted fragments in the three submit sheets were checked against held bytes by script.

- EO:8179 submit. Express named revocation by EO 9830 Part III ('No. 8179 of June 21, 1939.'), effective May 1, 1947 by its enacting clause. All six dossier rows end 1947-05-01. No inventory override needed (rows cover the whole operative text). A later restatement of the rule sections is treated as an amendment under the 2026-10-21 strike-and-insert ruling; the amending order's text is not an evidence id in the packet, so it is disclosed in the rationale and not cited.
- EO:8705 submit. Same end (Part III 'No. 8705 of March 6, 1941.'; the order is dated March 5, 1941 and filed March 6, a date difference stated in the sheet). The retroactive effective date of November 7, 1940 is stated as a start, not an end. Three dossier rows cover the whole text.
- EO:9301 submit. Express revocation by EO 9607, signed and filed 1945-08-30, no delayed effective wording. Section 1 ('For the duration of the war') sits inside the lead row. The War Manpower Commission rescission of Regulation No. 3 (August 1945, from the EO 9600 lead text) is disclosed as not ending the order and is not cited because that text is an unconfirmed held_text_lead. EO 9332 (recital of the Chairman's regulations under EO 9301) is attached as a source note to answer the OFR cross-reference.
- EO:6743 blocked. Needs S.J. Res. 113 (held at jobs/astra-source-retention/output/pdf/98e35c56...0305.pdf) as an evidence id of the EO:6743 dossier (SUPPLEMENT:SJRES113); the packet has none. Clause 1 ends 1934-07-09 by its own terms.
- EO:8300 blocked. The EO 9830 revocation line ('No, 8300 of December 12, 1939.', OCR comma) is not in the dossier; the later-event chain and actor evidence are empty. The 'cease to be effective at the close of May 31, 1940' signal belongs to another order on the same Federal Register page.
- EO:9303 blocked. First end depends on Department of State regulations under EOs 9452 and 9521 (not held); EO 10697 effective 1957-03-01 is only a bound.
- EO:9591 blocked. Paragraph 2 (section V-23) needs its regulatory history before 1957-03-01; EO 10697 effective 1957-03-01 is only a bound.
- EO:6437, EO:6530 dispatch-blocked as assigned (assessment rows only; decisions rows left as prepared).

Counts: 3 sheets submit-ready (not assembled), 4 blocked, 2 dispatch-blocked.

## What took the time

- 6743: locating that S.J. Res. 113 is not citable from this packet.
- 8179 and 8705: confirming EO 9830's enacting clause, Part II restatement and Part III list, and the March 5 versus March 6 date.
- 8300: finding that the own-text end signal belongs to a neighbouring order.
- 9301: reconciling the August 1945 Commission rescission and the EO 9332 and 9333 cross-references.
- 9303, 9591: reading the EO 9521 and EO 10697 conditional revocations.

## Batch-check, Geddes

Not run (apply failed). No GEDDES_LINT.json or GEDDES_RESOLUTIONS.json.

## Full-packet files opened beyond the views

PACKET.json (loaded once with batch.load_packet to read dossier evidence texts), LOOKUPS.md, decisions.csv, clauses.csv, RATIONALES.json. LOOKUPS.details.json was opened only to confirm it has no per-hit detail. Outside the packet: held order texts under jobs/fr-originals, jobs/source-ladder and jobs/astra-source-retention for the quoted checks, and a grep of jobs/later-events/output/EDGES.csv.

## Tool defects

- `kit.py apply` refuses the packet with `changed prior research`; the packet and the checkout are out of step.
- The OCR in LOOKUPS own-text signals for EO 8300 crosses into a neighbouring order's text.
- The EO 9830 line for No. 8300 uses 'No,' so the machine locator missed it.

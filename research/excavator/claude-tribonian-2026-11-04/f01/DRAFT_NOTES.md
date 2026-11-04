# f01 draft notes (producer, stopped 2026-11-04 on coordinator order; no kit.py apply was run, no packet file edited)

Start UTC 2026-11-04T04:45:20Z. My own working files are in the session scratchpad dir `f01own/` (lib.py, boards.py, ev.json, app.json, show.py, cl.py); they are not part of the packet and can be rebuilt.

## Findings that apply to every order
- All 37 numbers are in the EO 12553 table (51 FR 7237, held text jobs/fr-originals/data/full_run/texts/EO_12553.txt). Inline rows (page 10+) are in the form "N subject". Numbers on page 9 (first list, up to 9940) and page 11 (10376 to 10906) are in a separate number column. For those, the subject is matched by position. I checked the alignment by code and it is consistent: plural/singular and subject type match each order, e.g. 10848 aligns to a garbled "Amending EO 10843 ... steel industry" line.
- Provisional status is no for all 37. EO 12553 has no effective-date wording and no saving clause. I dated the revocation on signing, 1986-02-25.
- ACT:...>EO:12553 records exist for: 9949, 10032, 10038, 10045, 10048, 10105, 10109, 10125, 10150, 10157, 10286, 10306, 10323, 10328, 10376, 10449, 10504, 10570, 10601, 10635, 10643, 10689, 10709, 10811, 10842, 10848.
- No ACT record exists for 9675, 9731 (view says missing), 9793, 9855, 9899, 9910, 9942, 9965, 9996, 10037, 10696. For these I planned to cite ACTOR_TEXT:EO:12553 as end_id (whole 12553 text as quote). This was not yet tested against apply/checker.
- Report dates cannot be cited as later_events. Held NMB report TERM spans do not contain the cover or transmittal date lines, and the supplement route is impossible because the report PDFs are not held. Precedent claims (apollo-g03, erasmus-r2) put the report date in the reasoning, attributed to the held report, with no later_event.
- Citable later events found:
  - EO 10032: TERM:EO:10032:17b7ff0d12d6ef1f@b9436d84a54d85ed. The President approved the extension on 1949-02-19, to file not later than 1949-04-13.
  - EO 10306: TERM:EO:10306:fccefa708b2f9a2a@d87d90bedc3b2144. On 1951-12-13 the President extended the time to 1952-01-15.
  - EO 10038's extension spans lack the event date, so I did not plan a later_event for it.
- Inventory defects in the dossier. These need `inventory_source_id` overrides on ORIGINAL:EO:n. Because an override applies to every clause row of that instrument, delete the old rows and give one new scope_id.
  - 9855: the dossier's 16 clauses are junk from neighbouring pages. The operative text is at [2301,3124], and the heading is at 4708.
  - 9899: the clause begins after the "create" words. Use [4457,12227].
  - 9965: use [12151,13200]. This includes the "supersedes EO 9958" sentence.
  - 10045: the clauses are wrong. Operative text is at [2034,2876].
  - 10109: the dossier clause [0,2008] is the Red Cross Month proclamation, i.e. the wrong document. Use [3728,11667].
  - 10286: the clause starts mid-order. Use [3554, end of the DPA sec. 502 sentence]; the end offset is still to be found, and 13663 is only the start of "arose".
  - 10709: use [3442,11840].
  - 10811: possibly override [4297,14152]. The existing clause 12356-14152 does contain "create" and "arose".
  - 10689: keep only the lead clause [2453,3197]. The "2." and "1956." clauses are junk.
  - 10848: single clause [860,2738], the amendment of EO 10843. Both existing clauses are interleaved with junk.
  - 9942: merge "4." and "1948." (section 4 reads "effective April 1, 1948").
  - 10306: the existing clause is fine. It has no standstill.
  - 10643: fine; the whole order, heading included.
- Held-text number search: other held texts citing a board order are only adjoining FR pages and own copies. The exception is 10286, cited in the EO 10287 queue page capture, which is the same FR page.

## Per-order judgments
Boards (RLA section 10, 30-day report, standstill; EO 12553 revokes, 1986-02-25; report is a deadline, not an end, under the 2026-10-21 owner ruling): 9675, 9731, 9793, 9855, 9899, 9910, 9965, 9996, 10032, 10037, 10038, 10045, 10048, 10105, 10109, 10125, 10150, 10286, 10306, 10449, 10570, 10635, 10643, 10696, 10709, 10811. Planned outcome for all: submit, terminated by EO 12553, savings none_after_bounded_search, search_ids current-law:usc, current-law:ecfr, later-events:ofr_catalog (all complete).
Order-specific facts to keep true:
- 9793, 10150: independent consideration of each carrier; separate findings (9793 "shall contain", 10150 "may"). A list A and a list B follow.
- 9965: National Airlines; names three members; supersedes EO 9958 (disclose; text not held).
- 10286: extra command to comply with DPA 1950 sec. 502. The PEB-096 report has no text layer on pages 1-3, so no report date is established.
- 10306: carriers under federal management (EO 10155 seizure). There is a non-derogation sentence for the Army Secretary's authority under EO 10155, a DPA sec. 502 command, and separate findings. There is no standstill, so do not carry over standstill wording.
- 10449: the board was never constituted (NMB: no members appointed; the parties agreed on 1953-04-26). Disclose it per the ruling 2026-10-21-eo-10449-never-constituted.
- 10709: the board's carriers are three dock companies, with District 50, UMW.
- 10811: the dispute is Pan American World Airways with TWU. The held report shows a letter of transmittal dated 1959-06-12 and a cover dated 1959-06-15; the parties agreed to extend the report time to 1959-06-15.
- 10045: no report on the merits; the parties reported settlement on 1949-04-04 (NMB index closed 04-06).
- 10109: the report cover is 1950-03-09; the transmittal line reads "1960" in the text layer (OCR error).
- Report cover dates verified by pullman PACKETS plus held bytes:
  - 10032: 1949-04-11
  - 10038: 1949-09-19
  - 10048: 1949-04-29
  - 10105: 1950-02-28
  - 10125: 1950-05-19
  - 10150: 1950-09-09
  - 10306: 1952-02-14
  - 10570: 1954-11-20 (report time extended by stipulation to 1954-11-26)
  - 10635: 1955-10-26 (extended by stipulation to 1955-10-31)
  - 10643: 1955-12-12 (President extended the time to 1955-12-12)
  - 10709: 1957-06-07
- No held report: 9675, 9731, 9793, 9855, 9899, 9910, 9965, 9996, 10037, 10696. Say the report date is not established, and do not invent one.

Boards of inquiry (Taft-Hartley s.206):
- 10689, 10842: boards of inquiry for maritime labor disputes; the report is due 1956-11-24 / 1959-10-10. The text says the board continues in existence until terminated by the President. No held evidence of presidential termination, so say so; EO 12553 is the end. Submit.
- 10848: amends EO 10843 (report date to 1959-10-19). It is an executed amendment; follow the precedent of apollo-g03 10015 and apollo-g07 11029 (terminated by 12553, nothing left to operate on). Submit with the single-clause override above.

Others:
- 9949 (one-person order for Paul D. Miles modifying EO 9721 para. 3(a)): amended by EO 10415 (1952-12-02, strike and insert: "within five years from the date of his transfer to such Board" replaced by "on or before December 31, 1953"). The amendment is a later_event with before and after text; ACT>EO:10415 is available. End: EO 12553, 1986-02-25 (precedents: apollo-g05 10415, rastell-c02 10054). Prior producer versions exist in apollo g03 (and later); there are no reviews, so decide independently. Submit.
- 9942 (Rubber Act of 1948 functions): amended by EO 10539, signed 1954-06-22. Sections 2 and 3 replace "Reconstruction Finance Corporation" with "Federal Facilities Corporation", effective at the close of 1954-06-30 or an earlier time fixed by the Treasury Secretary (no such earlier fixing held). Record as a later_event (strike and insert, before and after). Open question: whether the Rubber Act of 1948 expired or was repealed before 1986. The statute text is not checked and is not clearly held; if it is not held, say so, because the order's own end would then be uncertain. EO 12553 is still the first held end. It needs the inventory merge. Probably submit with that qualification; otherwise block, naming the missing statute source.
- 10157 (competitive status; amended by EO 10217 and EO 10288; recited in EO 10535 and 10536; ACT records exist): needs a full read of the amendments (strike-and-insert before/after). The one-year recommendation window is an own-terms limit and not an end (see the apollo-g04 10080 reasoning). Inventory: 10 dossier clauses incl. duplicates ("a-dup2", "c-dup2"); needs checking. Not started.
- 10323 (SDPA transfer): not read. The view lists "target provision not located: EO:10161". EO 10161 is probably cited, not acting.
- 10328 (Selective Service regulations, 15 clauses, amended by 10420, 10837, 10984): not read; likely blocked or heavy inventory work.
- 10376 (Post Office permanent appointments, effective 30 days after 1952-07-18; section 2 is a one-time conversion): not analysed beyond the text. EO 10180 is only cited ("notwithstanding section 1(a) of EO 10180"). Leaning to submit with 12553 as end, and to record performance of the one-time conversion as not evidenced.
- 10504 (SBA liquidation functions, effective close of business 1953-11-30): usc/ecfr machine hits 2/2 are not examined. Savings: transferred functions. Not finished.
- 10601 (commodity set-aside; sections 3-6 are the main clauses): EO 12148 section 5-105 (1979) revoked "Section 3 of Executive Order No. 10601, as amended". That is an EARLIER partial end than 12553 for the section 3 clause. EO 12148's effective date is to be read from the held text (jobs/app-executive-orders/output/texts/executive-order-12148-federal-emergency-management.txt and jobs/fr-originals/output/texts/EO_12148.txt). Amendments or transfers by EO 10773, 10782, 11051 and 11725 (11725 section: 10601 section 3 listed among functions transferred) are not read. The other sections' ends need analysis. Complex; do after boards.

## Tool notes
- The assembler `batch.py` makes every clause of an instrument an override if any clause row has `inventory_source_id`.
- The `view` and `load_packet` data structures use `@eo:ref` indirection; the evidence texts are resolved only through `batch.load_packet` (returns a tuple; element 0 is the packet dict). `cruden.py table-number` returned only counts, no usable offsets.
- Decision sheet format (copy of apollo-g04 EO:10080 row): outcome submit; approved true; original_confirmed true; original_pages_confirmed true; inventory_confirmed true; working_text empty for FR originals (untested here); savings_state none_after_bounded_search or transferred_or_accrued; search_ids as above; source_notes only with frozen evidence ids.

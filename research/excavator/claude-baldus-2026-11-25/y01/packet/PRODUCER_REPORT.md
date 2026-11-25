# Producer report: packet y01 (producer baldus)

Start UTC 2026-11-25T15:22:40Z. End UTC 2026-11-25T15:42Z.

Final applied directory: `research/excavator/claude-baldus-2026-11-25/y01/packet/applied-v2` (applied-v1 kept: it showed EO 10033 rejected, see below).

## Outcomes

Submitted (4): EO 10457, EO 10521, EO 10579, EO 10641. Blocked (5): EO 10033, EO 10122, EO 10199, EO 10264, EO 10577. No member was found not in force on 2026-10-14, so no block is a not-in-force finding.

- EO 10457 submit. One designation clause (Department of Justice as a defense agency for 35 U.S.C. chapter 17); no later instrument held or listed; original-plus-bounded-search basis.
- EO 10521 submit. Inventory corrected to 14 spans (Section 6 split around the printed contents page). EO 10807 (1959) amended Sections 1, 3, 8(a), 8(b), added Section 10 and revoked Section 8(c) (the only terminated clause, end 1959-03-13). The OFR table also lists EO 12608; its held text does not name EO 10521 and the original has no Bureau of the Budget wording, so it is explained in the rationale and not claimed as an event.
- EO 10579 submit. Inventory corrected from 35 fragments to 12 spans (Section 3 in two parts). All clauses operative on the original-plus-bounded-search basis. Disclosed in the claim: EO 12608 section 2 might change the Bureau of the Budget wording but is not an evidence record in this packet; the cited authority statutes were later restated and no restated text is held. This is the weakest submission; a reviewer may prefer to hold it.
- EO 10641 submit. One clause (Rule VIII); EO 12107 recorded as a later event (agency-name substitution, effective 1979-01-01). EO 12362 and EO 12721 (precedence over Rule 8.2 in conflict) are described as non-endings but are not packet evidence records. Same statute-restatement caveat as EO 10579 (5 CFR part 301 authority line cites 5 U.S.C. 3301, 3302 with the order).
- EO 10033 blocked. Operative as amended (EO 11269, 12013, 12318), but EO 12013's Federal Register copy and provision records are custody_record_only and the APP transcription is rejected by the kit (a trial apply in applied-v1 returned working_text:official_copy_available_recheck_required). Missing: held bytes of FR 1977-10-12 pages 13-15 (42 FR 54931). Inventory also needs correction (Section 1 missing; Section 4 runs through contents-page text).
- EO 10122 blocked. Missing: text of the Career Compensation Act of 1949 authority and its repeal/restatement, and 10 U.S.C. 1216 (note is custody_record_only); no citable current source for Sections 1, 2(a), 2(b), 3, 4; no citable performance source for Section 2(b); inventory omits Section 5. Section 5 is shown operative by held 38 CFR 17.44 and 17.102.
- EO 10199 blocked. Official page check for 15 FR 9217 cannot be done: the ORIGINAL record requires a page check (location confidence low), the PDF bytes are not held and govinfo was not reachable (proxy 403). The dossier clause span (characters 0-1502) is EO 10198's text, so the inventory also needs an override. Substantively it reads as in force (U.S. Code note under 7 U.S.C. 610).
- EO 10264 blocked. Missing a citable source showing performance on 1951-07-01 (the FR 1951-10-06 codification-table note and the 48 U.S.C. 1662 note are not citable evidence records; the latter is custody_record_only) and the text of 48 U.S.C. 1661-1662. The dossier inventory has a spurious clause (item 1951).
- EO 10577 blocked. Thirty-nine clauses across Parts I to IV need a held current source each; the current 5 CFR parts 1 to 7 text and later Civil Service Rule orders are not in the packet evidence.

Assessment rows: `ASSESSMENT.jsonl`, nine rows. For orders still in force, `first_cause` is left as an empty string because the allowed values describe a cessation; the coordinator may map this as needed.

## What took the time (one line per order)

- EO 10457: short order; checking the neighbouring-order text bleed and the 35 U.S.C. 188 note lead.
- EO 10521: reading EO 10807 and tracing the EO 12608 OFR note; correcting the Section 6 inventory around the page break.
- EO 10579: reconciling 35 fragments to section spans, checking the EO 10578 false lead and the Bureau of the Budget wording.
- EO 10641: EO 12107 section 2-101 and the Rule 8.2 references in EO 12362 and EO 12721.
- EO 10033: identifying the missing Section 1 in the inventory, then discovering the EO 12013 custody problem through a trial apply.
- EO 10122: reading EO 10400 and EO 11733 and the 38 CFR 17.44 text; deciding the statute-text block.
- EO 10199: finding that the held clause is EO 10198's text, then the page-check block.
- EO 10264: analysing which items are performed versus continuing; sourcing performance.
- EO 10577: sizing the inventory and the amendment chain before blocking.

## Checks

- `kit.py apply` (applied-v1): 4 assembled, 1 rejected (EO 10033), 4 blocked. applied-v2 (EO 10033 blocked): 4 assembled, 5 blocked, no errors.
- `kit.py batch-check` on applied-v2: packet members 9, claims checked 4, strict pass 4, fail 0; actual claim checker: 4 checked, 4 all-checks passed, 4 gate passed; actionable failures none; independent human certifications 0.
- Geddes lint (`applied-v2/GEDDES_LINT.json`): 0 defect flags, 5 coverage gaps (citing-corpus incomplete for four claims, 1401 of 66745 tracked files missing or changed; and one `other_scope_instrument_mention` on EO 10579 for EO 12608, which the claim deliberately discloses as unattached). `GEDDES_RESOLUTIONS.json` records no resolutions because there are no flags; the EO 12608 gap needs the reviewer's independent source examination.

## Limits to know

- Every submitted claim relies on the original-plus-bounded-search route. The U.S. Code search covers the release point current through 2026-10-09 only; the claims disclose that and treat 2026-10-10 to 2026-10-14 as covered by the absence of any held later instrument.
- No page images were examined for any order (not needed for the four submitted orders: their originals carry requires_page_check false with high location confidence; `original_pages_confirmed` is false for all).
- Current-law context I read from repository texts that are not packet evidence (jobs/theophilus-sources CFR texts, jobs/current-law notes, jobs/peano-formulario OFR table, jobs/fr-originals texts of EO 12608 and EO 12362/12721 from the APP texts) is labelled in the claim text as context, not as a cited source.

## Full-packet files opened beyond the views

LOOKUPS.md (required), decisions.csv and clauses.csv (to edit), DISPATCH_CHECK.json (custody states per evidence id, scripted), HELD_SOURCES.json (one scripted search, no hit), and PACKET.json through `batch.load_packet(check_sources=False)` in scratch scripts (jobs/claim-kit/batch.py; no changes to the packet) to read evidence records and clause inventories. READ.md and LOOKUPS.details.json were not opened.

## Tool defects and friction

- `cruden.py search` on a bare number prints all matching held texts (hundreds of unrelated lines for EO 10521); a result cap would help.
- The dossier inventory can start a clause inside a neighbouring order or run through interleaved contents-page text (EO 10199, EO 10033, EO 10521, EO 10579, EO 10264); every such span needed an override.
- Trial `apply` is the only way to learn that an APP transcription is barred when an official copy text exists; the dossier does not warn of it in advance.
- Direct web access to govinfo is blocked by the proxy, so no PDF page check could be made.

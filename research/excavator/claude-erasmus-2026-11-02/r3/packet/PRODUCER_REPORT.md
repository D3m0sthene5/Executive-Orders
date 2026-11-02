# Producer report, Erasmus batch r3 (agent: claude)

Start: 2026-11-02T03:51:31Z. End: 2026-11-02T04:14:30Z.

Final applied directory: `applied-v2`. batch-check: 11 members, 10 claims checked, 10 strict passes, 0 failures,
no actionable failures; actual claim checker 10/10 passed (network downloads disabled); Geddes 0 defect flags,
1 coverage gap. `applied-v1` failed for EO 10319 and EO 10693 (see tool defects) and is kept.

Outcome: 10 submitted, 1 blocked. Certified count unchanged at 0. No status changed.

## Outcome per order

| Order | Outcome | End | Why |
|---|---|---|---|
| EO 10319 | submit | 1986-02-25, EO 12553 | Railway Labor Act board. The NMB record (PEB-100) shows the board was never constituted, three extensions were granted, the parties agreed on 1952-04-24 and no report was made. Functionally spent 1952-04-24; under the never-constituted ruling the order stayed on the books until EO 12553. |
| EO 10634 | submit | 1979-07-15, EO 12148 s.5-106 (effective date stated in the order; signed 1979-07-20) | Three later events now recorded: EO 10773 (1958-07-01), EO 11051 s.601 (1962-09-27), EO 11725 s.3 (1973-07-01), each with the officer before and after. |
| EO 10693 | submit | 1986-02-25, EO 12553 | Report of Emergency Board No. 116 dated 1957-03-15; status-quo period ended 1957-04-14 (inclusive reading); both recorded as spent facts. |
| EO 10843 | submit | 1986-02-25, EO 12553 | Later event EO 10848 (report date moved to 1959-10-19). Presidential termination of the board is not in held evidence and is disclosed. |
| EO 10915 | submit | 1980-06-27 (whole order) | s.2 and s.111 end 1961-09-30 (EO 10973 s.605, effective date in s.607). Inserted s.6 of EO 10900 ends 1980-06-27 (EO 12220 s.1-501). Later events on it: EO 11252 (1965-11-01) and EO 11963 s.2 (1977-01-19), which renumbered it s.5. |
| EO 10989 | submit | 1964-06-22, EO 11157 s.502(k) | Search account corrected: the matching catalog note is on EO 11157, not EO 12553. |
| EO 11013 | submit | 1986-02-25, EO 12553 | Board of inquiry under LMRA s.206. No standstill. Report deadline April 11, 1962; the board continues until the President terminates it, and no termination is in held evidence (disclosed). |
| EO 11026 | blocked | none | EO 11029 (1962-06-13) is an unnamed later amendment. It must be pinned, but it is not an evidence record in this dossier and its source PDF is not retained, so no supplement is possible. |
| EO 11036 | submit | 1980-06-27, EO 12220 s.1-501 | Search account corrected (EO 12220, not EO 12553). EO 12148 citation corrected to s.5-107. |
| EO 11138 | submit | 1986-02-25, EO 12553 | Addresses EO 10804 s.2: the 1959 revocation of the parents EO 9721 and EO 10103, with its saving. The 1964 waiver works within that saved scope; whether Strauss elected coverage under the 1958 Act is not shown. |
| EO 11195 | submit | 1978-05-15, EO 12060 s.3 | Search account corrected: the full read was EO 12060 (1,871 characters), not EO 12553. |

## What took the time (one line per order)

- EO 10319: reading the NMB record, which changed the facts (no board, no report, settlement), and checking the working-text gate.
- EO 10634: EO 10773's held FR text covers only pp. 5061-5062, so the list entry and effective date were checked in the APP text; also reading EO 11051 and EO 11725.
- EO 10693: reading the report front matter and computing the status-quo end; the gate refused the report as a source.
- EO 10843: aligning the EO 12553 page-11 columns by position.
- EO 10915: reconstructing the section numbering of EO 10900 across EO 10915, 11963, 10972, 11036, 11051, 12148, 12163 and 12220.
- EO 10989: verifying the EO 11157 revocation list and the EDGES catalog notes.
- EO 11013: removing template standstill wording; quick.
- EO 11026: testing whether EO 11029 could be pinned (dossier evidence, supplement route, PDF retention).
- EO 11036: checking EO 12148 ss.5-107/5-108 and the EO 12220 re-delegations.
- EO 11138: reading EO 10804 and the EO 12553 rows for 9721 and 10103.
- EO 11195: rewriting the search account; checking the 5 U.S.C. notes in current-law MENTIONS.csv.

## Brief defects: disposition per order

- EO 10319 (non-derogation sentence): confirmed and fixed. The inventory now names the four operative sentences actually held. The NMB record was re-read; it shows no board was named and no report was made, and these facts replace the prior claim's "spent facts not supplied".
- EO 10634 (no later events): confirmed and fixed. Three later events are recorded with before and after officer. EO 10773's list entry (14) and its s.10 effective date are on an unheld FR page; the claim says so and relies on s.3(a) and the signing date.
- EO 10693 (report not recorded): confirmed and fixed. Report date 1957-03-15 and status-quo end 1957-04-14 are recorded and quoted in the claim text. They are not recorded as `later_events` because of the tool limit below. Removed the carried-over sentence about "stipulations approved by the President", which the held report does not contain.
- EO 10843 (APP-row sentence): confirmed and fixed. The APP-only records are the EO 12553 records. The cited source is the held FR text of EO 12553. Removed the unsupported generalization about NMB report coverage.
- EO 10915 (EO 11963 s.2 omitted): confirmed and fixed. EO 11963 is recorded as a later event (renumbered s.5), sourced from the whole actor text. The ACT record's quote is s.1 and was not used.
- EO 10989 (catalog note): confirmed and fixed.
- EO 11013 (standstill wording): confirmed and fixed throughout.
- EO 11026 (EO 11029 unpinned): confirmed. It cannot be resolved with held, citable evidence, so the order is blocked with the precise gap.
- EO 11036 (12553 note; 5-108): both confirmed and fixed. The savings text was also reworded: EO 12220 cites s.104 paragraphs (f) and (j), and the claim no longer asserts these are the same paragraphs as 104(g) and (s).
- EO 11138 (EO 10804 ignored; parent "continues"): both confirmed and fixed.
- EO 11195 (search account): confirmed and fixed. Open point: the Pub. L. 89-554 earlier candidate is pinned only by path, for the same reason as EO 11029. Review did not flag it, but it is the same kind of gap that blocked EO 11026, and the coordinator should decide whether the two orders are treated alike.

## Geddes

lint on applied-v2: 0 defect flags. One coverage gap: EO 11138, `unclassified_instrument_mention` for EO 10103. It is the prior parent and is discussed as such. This is recorded as disputed in `applied-v2/GEDDES_RESOLUTIONS.json`. No crash.

## Tool defects

1. Working-text gate (`jobs/claim-kit/working_text.py` policy): a source-ladder report text registered under the order's own instrument id is treated as a derivative copy of the order. When an official order text is held, the gate refuses it with `working_text:official_copy_available_recheck_required` and `fragment_identity_or_grade_mismatch`. As a result, an emergency-board report cannot be cited as a later-event or source-note source, which the report-deadline ruling expects. Report facts for EO 10319 and EO 10693 are therefore pinned by path and quotation in the reasons.
2. No route exists to pin an unnamed earlier candidate that is held only as text. This applies when the text is not in the dossier and the source PDF is not retained: EO 11029 for EO 11026, and Pub. L. 89-554 for EO 11195.
3. `batch.load_packet` needs `Path` objects; strings fail with a TypeError. The prompt's suggested call with string paths does not work as written.
4. Search entries in the slim view omit `machine_hits_for_this_order`, so hit counts needed the packet.

## Files opened beyond the slim views

- PACKET.json through `batch.load_packet`, for machine-search hit counts and the evidence records of the TERM, ACT and ACTOR_TEXT ids (kind, text, actor).
- No READ.md and no LOOKUPS.details.json.
- Outside the packet: the prior Apollo sheets (g04-g08 `decisions.csv` and `clauses.csv`, used as drafts), `jobs/later-events/output/EDGES.csv` and `CATALOG_INDEX.csv`, `jobs/current-law/output/MENTIONS.csv`, held texts in `jobs/fr-originals`, `jobs/source-ladder` and `jobs/app-executive-orders` (the EO 10773 APP text, as a lead only), and two filed claims in `research/readiness/claims/` (apollo-g06) for format.
- Process note: a repo-wide grep for supplement-declaration examples printed the first entry of `SUPPLEMENT_DECLARATIONS.json` in the r1 and c1 Erasmus batch folders. They concern NRA orders, not these orders, and nothing from them was used.

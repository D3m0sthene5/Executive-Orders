# Producer report, packet r01 (agent bartolus)

Start 2026-11-25T00:57:42Z. End 2026-11-25T01:07:30Z.

Final applied directory: `applied-v1` (3 claims proposed, 2 blocked). `applied-v2` is a failed experiment (see tool notes) and is not the result.

## Outcome per order

- EO:8341, submit, status no. One self-executing revocation of EO 8323, performed on signing 1940-02-08. Filing (02-09) and issue (02-10) dates disclosed as alternative readings. No later event; searches and bounded name search return zero hits.
- EO:8613, submit, status no. Paragraph 1 (one-day closure and excusal) ends 1940-12-24, inclusive, exclusive reading disclosed. Paragraph 2 (publication) ends by performance 1940-12-18 (issue masthead); filing line 12-17 disclosed. Whole order ends 1940-12-24.
- EO:8639, submit, status no. Revocation of the Unalaska port designation, effective at the close of business 1941-01-15 by the order's own terms.
- EO:10570, blocked. The own-terms end exists (standstill ends 30 days after the board made its report; the held PEB-107 report is dated 1954-11-20, so about 1954-12-20), but no packet evidence record covers the cover or transmittal-letter span (PDF pages 1-2) of PEB-107-Report.pdf (sha256 841bb65f01dee3a98ee4723200aebe1989141a7113b86d2e1555f6e9edc2adaa). The packet's TERM records for that text cover only the introduction and later pages. A source supplement or reviewed FACT record is needed. The earlier claim ended the order on the 1986 revocation by EO 12553 under the superseded report-deadline ruling; under the 2026-10-28 ruling that revocation (1986-02-25) is a formal disposition and an upper bound, not the first end. The dispatch check reported the report bytes as held (held_bytes_verified), so the instruction that NMB PDFs are custody-only did not match this checkout.
- EO:14012, blocked. Formally revoked 2025-01-20 (EO 14148 sec. 2(w); EO 14159 sec. 3(a)). The plans, reports and strategy in secs. 3(b),(c), 4(b), 5(a),(b),(d) have 60/90/180-day deadlines, and no held source shows submission of any of them. A deadline is not an end, so the first end is bounded only as not later than 2025-01-20.

## What took the time

- EO:8341, EO:8639: reading the view and one prior draft; about 2 minutes each.
- EO:8613: two-clause end dates and the FR masthead check; about 3 minutes.
- EO:10570: reading the PEB-107 report text, tracing which packet evidence records cover it, and the EO 12553 text; about 5 minutes.
- EO:14012: 35-clause inventory and the held-text search for performance evidence; about 4 minutes.

## batch-check (applied-v1)

packet_members 5; claims_checked 3; strict_claim_pass 3; strict_claim_fail 0; blocked 2; mechanical failures 0. Two claims (EO:8613, EO:8639) carry "unverified" order_exists warnings (out_of_universe_number_in_verbatim_quote). They come from numbers of neighbouring orders printed in the whole-page original span, for example "Executive Order 85721" (an OCR footnote marker on 8572) and "Executive Order 74581" (7458). Those spans are fixed by the frozen packet. EO:8341 passes with only a footnote_marker_fused_number note (EO 8323).

## Geddes

`applied-v1/GEDDES_LINT.json` (run manually; batch-check did not write it for v1): 3 claims, 0 defect flags, 0 coverage gaps. No GEDDES_RESOLUTIONS.json is needed.

## Files opened beyond the views

- `PACKET.json`, loaded once in scripts for dossier evidence ids, spans and conflicts.
- `DISPATCH_CHECK.json`, for source custody status of the PEB-107 report.
- `READ.md`, lines 1-60 only (source catalogue); no further use.
- Held texts: `jobs/fr-originals/data/full_run/texts/EO_8341.txt`, `EO_8613.txt`, `EO_8639.txt`, `EO_14012.txt`, `EO_12553.txt`; `jobs/fr-originals/output/texts/EO_14148.txt` and `EO_14159.txt` (grep only); the PEB-107 text under `jobs/source-ladder/output/texts/`.
- `jobs/eumenes-nmb-reports/output/SOURCES.jsonl` (one grep line).
- `cruden.py search`, three regex searches (Pullman emergency board; Task Force on New Americans and naturalization working group).
- `jobs/claim-kit/assemble.py` and `jobs/claim-checker/checker.py` (parts, to learn how end sources and quotes are checked).

## Tool defects and notes

- `applied-v2`: pointing the end source at the CLAUSES evidence ids (to avoid the neighbouring-number warnings) is rejected by the gate (`clause_0_first_end`, `whole_order_end_evidence`). The decision sheets were restored to the v1 state, so they match `applied-v1`.
- batch-check wrote no GEDDES_LINT.json into v1 (the v2 run did). The lint was run manually.
- Original page images were not inspected (the PDFs are not held on disk), so `original_pages_confirmed` is false for the three submitted orders; none requires a page check.
- The held OCR text prints the EO 8341 closing number line as "[No. 83411" and omits the number from its heading (a packet segmentation lead). Identity rests on the heading, date, FR Doc. line and page, and this is disclosed in the rationale.

## Follow-up: applied-v3 (coordinator request) — not produced

Request: shorten the quotes for EO:8613 and EO:8639 that carry neighbouring order numbers. Plan (drafted, saved only in scratch at /home/claude/bartolus-scr/work/r01/decisions.v3draft.csv and clauses.v3draft.csv): use inventory_overrides to re-select each clause span (EO:8639 chars 2351-2733; EO:8613 chars 3102-3924 and 3925-4123), cite the derived OVERRIDE evidence ids as end and savings sources, and set EO:8341 to route_owner so it is not re-submitted.

Result: `kit.py apply ... --write applied-v3` stopped with "claim-kit: changed Valla review context; prepare a new version". Per the instructions I did not work around it. No applied-v3 exists. decisions.csv and clauses.csv in the packet were restored to the state that produced applied-v1.

Open issue even with a new packet: original_representation.quote is the whole-page ORIGINAL span, which sheets cannot shorten, so that one unverified entry may remain for EO:8613 and EO:8639. The OVERRIDE spans would remove the other four entries; untested because apply stopped.

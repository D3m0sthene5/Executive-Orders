# Fixed-sample independent AI source audit

This is an independent AI review, not human certification. The legal cutoff is 2026-10-14. Only this review directory was written. No claims, statuses, census, ledger, codebook, job outputs or HANDOFF files were changed. Exact file/record/source hashes and the observed review interval are in `INDEPENDENT_AI_REVIEW.json`. Unavailable billed-token telemetry is null. The first recorded clock reading was 2026-10-18 08:21:26 UTC; earlier kickoff reading is excluded.

## Decision

The new FR receipts for EO 9789 and EO 9818 are accepted as exact media custody matches. A mechanical media-step completion may be reported after the actual tracker confirms it. **A substantive increase in safely completed lifecycle claims is not supported by this audit.** The existing EO 9789 claim passes the structural gate, but its gap-free lifecycle assertion is rejected pending targeted correction and rereview. The kit inventory also contains a material wrong-order match and must not be scaled.

| Prespecified case | Outcome and precise scope |
|---|---|
| EO:9789 | Accepted original identity and media custody; rejected kit inventory and complete-claim approval; first cessation and savings unresolved |
| EO:10209 | Accepted shared Statute 80 media match only; original FR media still absent from selected acquisition batch; no lifecycle conclusion |
| EO:10210 | Accepted shared Statute 80 media match only; correct 1941 table row is on adjacent page; original FR media still absent; no lifecycle conclusion |
| EO::4314 | Unresolved source; reject exhaustion and step-completion inference |
| OFR1989:row:12 | Unresolved identity/possible duplicate; separate editorial witness retained |
| OFR1989:row:71 | Unresolved identity/possible duplicate; separate editorial witness retained |
| LOC:mjm017487 | Unresolved, prespec ID does not exist in retained candidate inventory; no substitution |

These are different kinds of decision units; a pooled legal-claim acceptance rate would be misleading. One existing lifecycle claim was substantively reviewed and was not upheld as complete; two other high-yield controls were media matches only.

## EO 9789: actual source and claim

The reviewer independently recomputed the actual cache PDFs' SHA-256 values: the 1946 issue is `2b7b024da1e6c96030efbb1f98c676da8fa03d4410845c4bc1e4ad554e9570f4` (18,133,827 bytes, 60 pages), and the 1947 issue is `dd7eb50e381aec2c9edd24b7174ecaa3ac4ed58c536ffb2686fa5018affda3e5` (8,617,443 bytes, 24 pages). Both exactly match the expected receipt values. Rendered/read 1946 PDF pages 1 and 3, and 1947 pages 1–3, using Poppler at 120 dpi.

The images confirm EO 9789's heading, nine paragraphs and signature on printed 11981/11983. Paragraph 9 explicitly makes it effective October 14, 1946. The same page's left-column EO 9788 instead terminates the Office of Alien Property Custodian and transfers functions to the Attorney General, effective October 15, 1946. The kit `EO_9789.json` inventories that **EO 9788** lead and five paragraphs. Its source pointer contains both orders, but its selected clauses are the wrong identity. Claude's claim at `claude-2026-10-18-codif-b2.jsonl`, line 15, instead inventories the correct EO 9789 text in ten exact held OCR spans (paragraph 2 is split into two records). Its canonical Stage 19 claim hash is `fcabadd3f7937bf11fd701b2dfaf3694b505fd0a9f6a07362bfa433095fdc45b`; structural gate returns no errors. Exact spans and structural success do not establish legal correctness.

EO 9818 paragraph 9, printed 135/PDF page 3, clearly names **9789** in the image, along with October 14, 1946 and its exact title. The held OCR's `928.9` is a recognition error. Formal supersession identity is supported. The date line is January 7, 1947; filing January 8 and publication January 9 are different events. No explicit effective-date clause appears in EO 9818. January 7 is a reasoned signing-date inference, not quoted effective wording.

The existing claim assigns January 7, 1947 as every clause's first end. The sources alone do not establish that uniform result. Paragraph 2 presently vests/transfers functions; paragraph 7 both amends EO 9142 and authorizes litigation appearances; paragraph 8 protects past acts against a jurisdictional challenge; paragraph 9 fixes commencement. These need separate explanation of executed effects, retained commands and legal cessation. Paragraphs 3 and 5 require actual transfers, and paragraph 5 also requires reimbursement. No administrative performance evidence is cited. The absence of evidence of earlier completion does not prove that every command first ceased at supersession. This review does not invent replacement first-end dates.

Savings treatment also needs a clause-specific account of accrued property/results, civil-service protection, reimbursement, litigation amendment and no-challenge protection. EO 9818 reissues the administration with changes: paragraph 1 adds employee protections, paragraph 2 lists source authorities, paragraph 5 changes transferred items/reimbursement and paragraph 6 adds budget and Congressional controls. Its broadly similar functions do not alone resolve all residual effects. The claim acknowledges accrued transfers and restated paragraph 7; that is useful but insufficient to close the identified distinctions. Supported formal supersession and incomplete per-clause first-end proof can coexist.

Supplementary bounded scan read 6,652 current held `full_run/texts/*.txt` files for `(?<!\d)9[\s,]*7[\s,]*8[\s,]*9(?!\d)`, producing 22 hits. Contexts were original/metadata/codification references and unrelated FR page, docket and salary numbers. July 1947 guide entries in the EO 9870/9871 extracts accompany Reorganization Plan 1, not a newly found operative supersession sentence. This scan cannot exclude unheld, unnumbered or OCR-corrupted material. Claude's recorded 6,497-text scope differs from this current 6,652-file scope and must not be silently relabeled. The current-law retained rows corroborate the historical supersession note at 22 USC 1382; the USC edition is only current through October 9, 2026, as the claim discloses.

## EO 10209 / EO 10210: media controls and adverse statutory text

Independently recomputed full PDF hash `7b418d69527a803abc2a760f1ac80881a8e2cc4e27de0ae6e24a3061d1c86fbf` (48,781,096 bytes, 286 pages) matches the upstream expected document. This is not the archived excerpt member hash `7d978b72aeabbf14b0a6ec3f51190e6cec14d2ac9e51e392af8e18812c7d56f8`. They must remain different source objects. The held excerpt text was read as corroboration, not used as proof of identical upstream bytes.

Rendered/read PDF 273 (printed 650), 274 (printed 651), and 254–255 (printed 631–632). The acquired source-ladder text stops after page 40; it does not include the cited page 273. This is a content-extraction gap, not a failure of full-PDF custody.

Page 273 contains the July 8, 1940 / 54 Stat. 743 schedule row, relevant to EO 10209's cited authority. EO 10210's 1941 source row is on the adjacent printed 651/PDF 274. A page-273-only legal citation is too narrow for that proposition. Neither table segment establishes an EO lifecycle conclusion.

The adverse statutory provisions are essential: section 7(a) says the recodification restates without substantive change; 7(b) redirects references; 7(c) continues covered orders/rules/regulations under corresponding provisions until repealed, amended or superseded; 7(d) preserves actions. Section 8(a) excepts matured rights/duties, incurred penalties and begun proceedings and incorporates section 7; 8(c) disclaims an inference about whether a provision was in effect before repeal. Therefore a repeal-table hit cannot automatically become an executive-order first end. Held EO 10789 paragraph 14 also preserves prior actions under EO 10210. No new legal conclusion for either control is proposed.

The separate original FR URLs for EO 10209 (`FR-1951-02-03.pdf`, expected `2c0345bac4d3db3667041f79dfea6e488d3f15d15c06a7876f753ba086cea769`) and EO 10210 (`FR-1951-02-06.pdf`, expected `00a337af22427fdc00b8b08907529219cf7829a3bd0dd1bf81cb1477fa943e12`) are outside the twelve selected actions. Acquiring only the shared statute does not complete either order's entire media step.

## Difficult controls

EO::4314's only attempt was Wikisource `Executive_Order_4314`, returning HTTP 404. Its proposed exhaustion explicitly says **WEAK** and that no official route was known. No original was acquired. Reject any inference of adequate exhaustion, source identity or shared-source completion. Retain a request for official register/archive or government compilation research.

OFR rows 12 and 71 correspond to page 1032/printed 1021 and page 1033/printed 1022. The held OCR and coordinate chunks show the same August 8, 1914 date, EO 8507 amendment and public-lands disposition. They are two located editorial witnesses, not proof of two instruments, nor proof of one. No signer, title or property scope was supplied. The retained provenance declares the underlying PDF hash `6c760d36b1d22350dc22890bbf31afb0a67911c3bc295abd567cc0e706fe2ccd`, but that full PDF/page images were unavailable here; OCR/layout records were read, not falsely described as image verification. Retain both witnesses pending the original instruments and EO 8507. No census admission, duplicate deletion, merger or legal date follows from this audit.

The exact prespecified `LOC:mjm017487` is absent from `DISCOVERY.jsonl`, underlying `ITEM_CANDIDATES.jsonl` and the retained LOC candidate CSVs. Discovery has 67 LOC records. This is a prespec identifier error. No convenient substitute was selected.

## Stop and next work

The wrong EO 9789 inventory is a material unsupported identity match and triggers the prespecified stop on scaling. Correct and independently rereview the inventory before scaling; revisit the existing claim's first cessation/savings before promoting substantive readiness. Source receipts can still demonstrate mechanical acquisition benefit. Proposed missing-source/review work is recorded separately in `PROPOSED_SOURCE_AND_REVIEW_QUEUE.jsonl`; the production fetch queue was not changed.

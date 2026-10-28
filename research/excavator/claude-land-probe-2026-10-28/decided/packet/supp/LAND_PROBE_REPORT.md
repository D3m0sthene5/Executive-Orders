# Land probe: 18 decided land orders, 1924–1936

Producer: Claude. Start 2026-10-28T20:00:18Z; end 2026-10-28T20:31Z (UTC).

**Result.** Two claims were submitted and assembled: EO 4109 and EO 4430, both ended by EO 8861 on 1941-08-20. Sixteen orders are blocked. Batch-check on `applied-v2` reports no errors and no mechanical failures. Its only findings are the expected `custody_record_only` flags on the APP capture of EO 8861. The rest of the blocked work comes down to one practical fact. Twelve of the sixteen blocked orders ended through a Public Land Order (PLO), which the Secretary of the Interior issues and publishes in the Federal Register, and the project holds the text of none of those PLOs. Finding which PLO ended each order took about a minute per order once the right index was found. The real constraint is getting the PLO texts.

## Folder layout

The parent packet is `decided/packet`, and it holds only the prepared files plus `SUPPLEMENT_DECLARATIONS.json`. The final packet is `decided/packet/supp`, which is the source-supplemented packet. It holds `applied-v1` (both submissions were rejected there by the official-copy gate, described below), `applied-v2` (the current version, with batch-check output), `LAND_LOG.jsonl` and this report. Scratch scripts and rendered page images are kept outside the repository.

## Per-order outcomes

| Order | Subject | Outcome | End, or the state of the current basis | What blocks it |
|---|---|---|---|---|
| 4109 | Florida islands withdrawal | **submit** | EO 8861, 1941-08-20 | none |
| 4430 | Michigan and Wisconsin shore lands | **submit** | EO 8861, 1941-08-20 | none |
| 4262 | Coastal lands in Ala., Fla. and Miss., plus a townsite | blocked | EO 8861, 1941-08-20 (held) | The held OCR text drops one printed line. The inventory has to be split into two clauses. Whether the townsite lots were sold before 1941 is unknown. |
| 4872 | Air-navigation sites, Nevada | blocked | PLO 4620, 34 FR 6689 (1969) | No text of EO 4872 is held; the dossier "original" is a 1928 statute. PLO 4620 is not held. |
| 5038 | Pinnacles classification withdrawal | blocked | PLO 1397 (1989 table) | The texts of PLO 1397 and Proc. 2528 are not held. |
| 5214 | Alaska naval areas | blocked | PLO 945, 19 FR 1583 (1954) | PLO 945 is not held. |
| 6143, 6276 | New Mexico exchange withdrawals | blocked | PLO 6459, 48 FR 40724 (1983) | PLO 6459 is not held. |
| 6604 | Soil-classification withdrawal, Neb. and S.D. | blocked | PLO 711, 16 FR 3348 (1951) | PLO 711 is not held. |
| 6910 | General withdrawal pending the Taylor Grazing Act (hub) | blocked | Provisional YES; current basis not held | No held current-law text and no held evidence of an active withdrawal in 2026. |
| 7185, 7212, 7452 | Additions to the Upper Mississippi refuge | blocked | PLO 936, 19 FR 769 (1954) | PLO 936 is not held. EO 7452 also needs an inventory override. |
| 7373 | Desert Game Range | blocked | PLO 4079 (1966) | The original is held only at a non-working-text grade. PLO 4079 is not held. |
| 7435 | Winnemucca bird refuge | blocked | PLO 2690, 27 FR 5504 (1962) | The dossier original is the wrong FR page. Page 5504 of the held issue was not extracted. |
| 7504 | Arizona experiment station | blocked | PLO 1149, 20 FR 3439 (1955) | PLO 1149 is not held. |
| 7509 | Fort Peck Game Range | blocked | Provisional YES, contradicted by the 1989 table | The dossier original is the wrong document (WRDA 2000). The status conflict is unresolved. |
| 7510 | Lenore Lake bird refuge | blocked | PLO 1249, 20 FR 8471 (1955) | The dossier original is the wrong document. PLO 1249 is not held. |

Notes on the two submitted claims:

- **EO 4109.** The claim cites three partial events: EO 4372 (1926), EO 4485 (1926), and EO 8725 (1941, which takes precedence over EO 4109 without revoking it).
- **EO 4430.** The claim cites one partial event, EO 4446 (1926).
- **Uncited partial events.** These are disclosed in each claim's rationale rather than cited, for gate reasons explained under tool defects: for EO 4109, EOs 7993 and 8508; for EO 4430, EOs 5366, 5386, 7795, 7814, a revocation printed at 3 FR 2800, and Proc. 2318. Each released only named lands before the whole revocation, so none of them changes the end date or the status.
- **Source checks.** The ProQuest originals and partial orders were checked against page images rendered from the PDFs held in `ProQuest Pre-1937 Orders/` at the repository root. Two OCR misreadings were corrected from the images: EO 4430 is dated April 23, 1926 (the OCR reads "28"), and EO 4321 is dated October 13, 1925 (the OCR reads "18"; the WPA list agrees with the image).

### EO 7509: contrary evidence on status

The held 1989 Office of the Federal Register (OFR) disposition table, and the NARA page held with it, say "Revoked by PLO 4588", yet the provisional status is YES. Two web sources point toward YES:

- Wikipedia describes PLO 4588 (March 25, 1969) as establishing the UL Bend National Wildlife Refuge, which would make it a partial revocation.
- The BLM PLO table lists PLO 5635 (April 25, 1978, 43 FR 19046) as "amending EO No. 7509". An order cannot be amended after it has been revoked in whole, so this suggests EO 7509 was still in force in 1978.

Neither source is held. The conflict stays open until the texts of PLO 4588 and PLO 5635 are held.

### EO 6910 (hub)

About 4 minutes of logged time went to this order, well under the 60-minute cap. Every later-actor record examined names particular lands: 53 distinct records in the dossier, out of the roughly 210 events in the later-events data. None is a whole revocation. The 1989 table classes the order as "Public lands", meaning not ended. The machine current-law leads are 43 CFR 2520.0-8(c), which still treats unsurveyed land withdrawn by EOs 6910 and 6964 as closed to desert-land appropriation, plus 43 CFR 2300.0-3(b), 43 CFR 2400.0-3 and 16 U.S.C. 460y-6. These leads support a YES, with section 701 of the Federal Land Policy and Management Act (FLPMA) as a continuity point. However, the project holds no text slice of any of them.

A claim needs four things:

1. A held eCFR title 43 slice of 43 CFR 2520.0-8 and 2300.0-3.
2. The text of 16 U.S.C. 460y-6 and of FLPMA section 701.
3. One record showing an active EO 6910 withdrawal in 2026, such as a BLM land-status record or a recent Federal Register document.
4. A rule for hub orders on whether a YES claim must list all ~210 partial events or may cite the event export.

## Where the time went

**Observed.** Wall-clock time was about 31 minutes from start to end, including this report. The session's token counter showed about 0.4 million tokens consumed by the end of production. The kit's own runs took real time: preparing the supplement took 32 seconds, each `apply` took 62 seconds, and `batch-check` took 82 seconds. There were about 60 tool calls before the report was written.

**Estimated.** The per-order minutes in `LAND_LOG.jsonl` are my estimates, scaled so that they add up to the ~22 minutes of order-specific work. The remaining ~8 minutes were shared setup: reading the protocol, decoding the packet, writing helper scripts and running the kit.

| Phase | Minutes, all 18 orders (est.) | Share |
|---|---|---|
| Finding later instruments | 5.1 | 25% |
| Getting instrument texts, including page-image and APP checks and the supplement | 5.1 | 25% |
| Reading text and clauses | 4.8 | 24% |
| Writing decisions and rationales | 3.9 | 19% |
| Savings and contrary evidence | 1.3 | 6% |

By type (estimated): the 11 general withdrawals took 13.8 minutes, about 2.5 minutes per order for the two submitted claims and under 1 minute per blocked order. The 5 bird refuges took 2.1 minutes. The hub took 3.8 minutes. The one order typed as a mineral withdrawal, EO 6604, took 0.5 minutes; its text is in fact a soil-classification withdrawal, so the machine type is wrong.

**Interpretation (estimate).** The 3,900 agent-hour projection assumes about 1.3 hours per order. That is far above what this batch needed to identify the ending instrument. Most of the remaining cost is not research. It falls on three things: acquiring PLO texts, re-preparing packets whose original was misselected, and a second short pass on each order once its PLO is held. I estimate that second pass at 2–4 minutes per order, plus independent review. These figures come from one batch of 18 orders. Hubs like EO 6910 and refuges with a current YES status will cost more.

## Recurring sources and instruments

- **BLM Public Land Order tables** (web, not held). This is a set of 24 PDFs covering PLOs 1–7898. Each row gives the PLO number, the signature date, a subject heading that names revoked orders by number and date, and the FR citation. They located the ending PLO, with its date and citation, for 10 of the 16 blocked orders, plus many partial PLOs. Listing: https://www.blm.gov/programs/lands-and-realty/land-tenure/withdrawals/public-land-orders
- **1989 OFR codification disposition table** (held: `jobs/ofr-codification-1989/output/DISPOSITION_1989.csv`), with the NARA online copy held in `jobs/hathi-gpo-orders/output/discovery/nara_executive-orders-0[23].html`. It named the ending instrument for 12 of the 18 orders and gave the complete partial-amendment list for EOs 4109, 4262 and 4430. Packet preparation does not surface it as a later-event lead.
- **Instruments shared by several orders:**
  - EO 8861 ends EOs 4109, 4262 and 4430.
  - PLO 936 ends EOs 7185, 7212 and 7452 (and EO 8331).
  - PLO 6459 ends EOs 6143 and 6276 (and EO 6583).
  - The EO 6910 partial events touch EOs 7373, 7504 and 7509.
- **FR daily contents pages** (held). The source-ladder job keeps PDF pages 1–6 of each issue, and those pages list entries such as "4872 (revoked by PLO 4620) ... 6689". That is a free index from orders to PLOs to pages for the issues already downloaded.
- **OFR API disposition notes** (held). For orders from 1937 onward they give the PLO with its FR citation, for example "Revoked by: Public Land Order 1149, May 11, 1955 (20 FR 3439)".

## Missing sources that would unblock the most orders

1. **PLO 936, 19 FR 769** (February 4, 1954): unblocks 3 orders (7185, 7212, 7452).
2. **PLO 6459, 48 FR 40724** (August 16, 1983), with PLO 6589 at 50 FR 9428: unblocks 2 orders (6143, 6276).
3. **Re-preparation with the already-held APP transcriptions as originals**: 7435, 7509, 7510 and 7373. This needs no new sources. Of these, 7435 also needs page 5504 extracted from FR-1962-06-09.pdf, and 7510 needs PLO 1249.
4. **One PLO each:** PLO 945 (19 FR 1583) for EO 5214, PLO 711 (16 FR 3348) for EO 6604, PLO 1149 (20 FR 3439) for EO 7504, PLO 1249 (20 FR 8471) for EO 7510, PLO 4079 for EO 7373, PLO 4620 (34 FR 6689) for EO 4872, and PLO 1397 for EO 5038.
5. **A local re-OCR** of `ProQuest Pre-1937 Orders/PT1-1925-EO-4262.pdf` for EO 4262. No web source is needed.
6. **EO 4872's own text**, from ProQuest t67.d72.1928-eo-4872.
7. **EO 7509:** PLO 4588 and PLO 5635, plus a current Fish and Wildlife Service basis.
8. **EO 6910:** the eCFR, U.S. Code and FLPMA slices listed above.

Each order's exact list is in `decisions.csv` under `unresolved_material_gaps` and in `LAND_LOG.jsonl`.

## Tool defects hit

1. **Wrong originals selected.** Four of the 18 dossiers carry a different document as the original. EO 4872 carries a 1928 statute page. EO 7435 carries the wrong FR page. EO 7509 carries the text of the Water Resources Development Act of 2000, which produced 1,987 machine "clauses". EO 7510 carries Treasury income-tax regulations, which produced 99 clauses. For three of these four, a correct APP transcription is held but was not chosen. EO 7373's original was chosen at grade `held_text_lead`, which the assembler does not accept as a working text.
2. **Page-neighbour artefacts.** The FR page texts in fr-originals and source-ladder attribute neighbouring documents to an order. Examples are EOs 8858–8860 attached to EO 4109, EO 7794 to EO 4430, and EOs 7796, 7815 and 8014 to EO 4430. The ACT record for EO 7795 in fr-originals is sliced from the contents page and quotes no operative text.
3. **Propagation through a parent order.** Because EO 7373 "amended EO 6910", 83 EO 6910 and EO 6964 events were attached to it as `whole_via_parent`. Only three later records actually name EO 7373.
4. **The official-copy gate conflicts with what the dossier offers.** `apply` v1 rejected both submissions with `working_text:official_copy_available_recheck_required`. The cause was that official FR copies of EOs 7993, 8508, 7795 and 7814 are held, but the dossier offers only their APP transcriptions as citable sources (or a mis-sliced FR record). The supplement route cannot fill the gap either. It registers an FR text as official only when the raw issue PDF is held, so the fix belongs in packet preparation: offer the official FR record with a correct span.
5. **Ambiguous registrations leave excerpts ungraded.** The supplement's excerpts of EOs 5366 and 5386 came out ungraded and could not be cited. The registry has both a live and a mirror registration of the same text, and `source_supplement.registered()` returns no grade when it finds more than one.
6. **Machine inventory errors.** EO 7452's land-description section numbers ("Sec. 7:", and "Sec. 32:" twice) became 19 clauses. EO 4262's single clause merges two commands with different legal bases.
7. **Partial page extraction.** source-ladder extracts only PDF pages 1–6 of each FR issue ("PARTIAL: other pages not extracted"), so the PLO pages of issues it has already downloaded are missing.
8. **Network limits in this session.** Bash cannot reach govinfo.gov, blm.gov or archives.federalregister.gov; the proxy refuses the connection. WebFetch can read blm.gov, but it truncates the large BLM tables at about 90,000 characters. The PLO 695–2250 table stopped at PLO 1307, and the other tables stopped at 2938, 5685, 6507 and 680. WebFetch also could not open pre-1994 FR issue PDFs on govinfo (client_error).
9. **Wrong type.** EO 6604 is typed `mineral_withdrawal`, but its text is a soil-classification withdrawal.
10. **Coverage gap in the 1989 table.** It has no rows for EOs 5214, 6604, 7185, 7212 and 7452, even though the BLM table shows they were revoked by PLOs between 1951 and 1954.

## Recommendations

1. **A PLO citation index job (runner, no model tokens).** Download the 24 BLM PLO table PDFs, run pdftotext (or OCR where needed), and parse each row into four fields: PLO number, signature date, subject and FR citation. Then extract every "EO No(s). NNNN of DATE", together with "revoking", "revoking in part" or "amending", as later-event edges. Merge in the 1989 table's `acting_documents` and the OFR API PLO notes. In this batch, those three sources together named a candidate ending instrument for 17 of the 18 orders, every order except the hub; for EO 7509 the named instrument is contested. Across ~3,000 land orders this replaces the "finding later instruments" phase almost entirely.
2. **An FR page fetcher.** Given an FR volume and page, find the issue date (from govinfo FR volume page ranges or the PLO index), download the issue PDF from govinfo or archives.federalregister.gov/issue_slice, and extract only the pages needed, registered at a working-text or official grade. Feed it the PLO index. Once this exists, most blocked land orders become a 2–4 minute second pass.
3. **Packet preparation fixes:**
   - Choose the original by verified identity: number, date and heading must match.
   - Offer an official FR alternative for every actor that has one, sliced to the right span.
   - Drop page-neighbour and `whole_via_parent` artefacts unless the text names the target.
   - Surface the 1989 disposition row and the BLM PLO rows as leads.
4. **A refuge and range history list.** For orders with a current YES status (EO 7509 and the other game ranges), compile the Fish and Wildlife Service establishing-document records and the later PLOs naming each refuge. This settles whether an editorial "revoked by PLO" was partial.
5. **A hub rule.** Decide whether a YES claim for EOs 6910 and 6964 may cite the event export instead of enumerating ~210 partial events. Hold the eCFR and U.S. Code slices that the current-law job already locates.
6. **Batch by ending instrument.** Group land orders by the instrument that ends them, as with EO 8861, PLO 936 and PLO 6459. One acquisition and one reading then serve every order in the group.

Certified count unchanged at 0. Nothing here adopts or changes a provisional status.

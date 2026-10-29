# Producer brief: NIRA code-approval orders (reusable for every batch)

This is the operational path for producing lifecycle claims for executive orders that approve, prescribe,
amend, modify, stay or exempt from a NIRA code of fair competition. It reuses the ordinary claim-kit route; the
only addition is a shared, independently reviewed legal analysis and seven shared source excerpts attached to
every packet.

## Coordinator steps (per batch, about 1 minute of machine time)

```text
python3 jobs/claim-kit/kit.py prepare EO:A EO:B ... --agent claude --write research/excavator/claude-nira-sweep-2026-10-29/<batch>/packet
python3 -I research/excavator/claude-nira-sweep-2026-10-29/make_declarations.py <batch>/packet <batch>/packet/SUPPLEMENT_DECLARATIONS.json
python3 jobs/claim-kit/source_supplement.py --repo . prepare --parent <batch>/packet --sources <batch>/packet/SUPPLEMENT_DECLARATIONS.json --agent claude --write <batch>/packet/supp
python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py lookups <batch>/packet/supp
```

Do not commit a packet folder until its batch is completed. A committed `RATIONALES.json` joins the tracked
package inventory that every packet's Valla context pins, so a mid-batch commit stales every packet in flight
("changed Valla review context").

Controls: keep the private control key and the seed receipts outside every path a reviewer is given (not in
the review-set folder and not in the packet) until the blind review is written; then copy the seed receipts
into `completion/`. One reviewer that read a key in the same folder as its review set had to be re-run.

Select members from provisional-NO orders that X1 types `nra_code_approval` and whose titles name a code
(`COHORTS.json` records the rule). Exclude the outliers listed in SHARED_ANALYSIS.md section "What each order
still needs", item 5. A producer (a cheaper model is suitable, per the 2026-10-29 tiered-delegation rule)
fills the sheets; a separate reviewer reviews blind with planted controls; `kit.py complete` files.

## Producer rules

0. Start from `LOOKUPS.md` in the packet: register and WPA rows, the APP page check, own-text wording signals,
   and held texts that cite the order or name its code. It replaces writing your own search and page-check
   scripts. For any other search use `python3 -I research/excavator/claude-nira-sweep-2026-10-29/cruden.py search REGEX`.
   Do not read claim-kit source code to learn the sheet format; the example below passed every check.
1. Read `SHARED_ANALYSIS.md` and `review-shared/ADJUDICATION.json` first. Apply the
   reviewed analysis; do not re-derive it. If an order's text or a held source contradicts it, block that order
   and say why.
2. For each order: read its held text in full; do the APP page check (AGENT_PROTOCOL.md, working-text paragraph)
   or the printed-copy check; confirm identity against the census register and the WPA 1944 list; list every
   operative clause, correcting the machine inventory where it is wrong.
3. Own terms and section 10(b): look for a stated period, condition, "until", "for a period of", "pending", or a provisional
   approval. An own-terms end before 1935-06-14 is the first end.
4. Earlier government action: search held order texts (`jobs/*/output/texts`, census register titles, the WPA
   list) for the code's name and the order's number. A cancellation or modification under section 10(b), a superseding
   code, revocation or suspension before 1935-06-14 is the first end of what it reaches. Amendments are later events, not ends.
5. Independent commands: anything that does not depend on the code (appointments, directions to agencies,
   delegations under other statutes) needs its own end or a block.
6. For a code-dependent clause with no earlier end: `state` terminated, `end_id` `SUPPLEMENT:SJRES113`,
   `effective_date` 1935-06-14, `effective_date_confirmed` true, mechanism
   `statutory_repeal_of_code_approval_and_enforcement_provisions`; cite `SUPPLEMENT:NIRA3` for the legal effects
   that were repealed. In `source_notes`, record `SUPPLEMENT:SCHECHTERJDG` (and, if quoted, `SCHECHTERDEL`)
   with date qualification "1935-05-27: date the section 3 delegation was declared unconstitutional; validity
   characterization (void from issuance under then-prevailing doctrine), not an end date". Say in
   `earlier_end_check` that no held record shows this code cancelled or suspended before June 14, 1935, and
   that June 16, 1935 is not an end (section 1 replaced that expiry with April 1, 1936).
7. Savings: `transferred_or_accrued`, source `SUPPLEMENT:NIRA5` or `SUPPLEMENT:SJRES113`; acts and liabilities
   before the repeal are accrued; the section 5 exemption for completed action is accrued; nothing continues the
   approval.
8. Shared wording may be referenced as `@rationale:KEY` from RATIONALES.json; every order still gets its own
   earlier-end, scope, independent-command and savings explanation.
9. Set the `agent` column to the packet's preparing agent (`claude` for packets prepared as above); completion
   refuses a claim whose agent differs from its packet's. Name yourself in PRODUCER_REPORT.md instead.
10. Record start and end UTC, and per order one line on what took the time. Run apply and batch-check in the
   background; never overwrite an applied directory.

## Sheet fields for a plain code approval (this combination passed batch-check and the actual checker)

`decisions.csv`: `outcome` submit; `approved` true; `original_confirmed` false; `original_pages_confirmed` true
(after the page check); `inventory_confirmed` true; `savings_state` transferred_or_accrued; `savings_source_id`
SUPPLEMENT:SJRES113 or SUPPLEMENT:NIRA5; `search_ids` ["current-law:usc","current-law:ecfr","later-events:ofr_catalog"]
after reading their coverage notes; `conflict_resolutions` {}; `unresolved_material_gaps` [];
`working_text` {"confirmations":[{"complete_text_confirmed":true,"grade":"mirror_transcription","identity_confirmed":true,
"instrument_id":"EO:N","pages_confirmed":true,"sha256":"<original sha256>","text_path":"<registered text path>",
"text_sha256":"<text sha256>"}],"quotation_recheck_required":true,"replacement_required":true,
"ruling":"research/readiness/owner_rulings/2026-10-21-transcription-as-text.md","standing_note":"original not yet held;
replace and re-check quotes when an official copy is retrieved."}; `source_notes`
[{"id":"SUPPLEMENT:SCHECHTERJDG","reason":"...","date_qualification":"1935-05-27: ..."}].

`clauses.csv`: `state` terminated; `end_id` SUPPLEMENT:SJRES113; `effective_date` 1935-06-14;
`effective_date_confirmed` true; `mechanism` statutory_repeal_of_code_approval_and_enforcement_provisions;
`later_event_ids` [] and `later_events` [] unless a held later order applies; `reason` in full sentences quoting
the order and S.J. Res. 113 section 2. For an inventory correction fill `inventory_source_id` (the ORIGINAL id),
absolute `inventory_char_start` / `inventory_char_end` and `inventory_reason`, with a new `scope_id` per clause.

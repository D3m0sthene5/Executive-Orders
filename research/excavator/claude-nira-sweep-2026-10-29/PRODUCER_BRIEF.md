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
```

Select members from provisional-NO orders that X1 types `nra_code_approval` and whose titles name a code
(`COHORTS.json` records the rule). Exclude the outliers listed in SHARED_ANALYSIS.md section "What each order
still needs", item 5. A producer (a cheaper model is suitable, per the 2026-10-29 tiered-delegation rule)
fills the sheets; a separate reviewer reviews blind with planted controls; `kit.py complete` files.

## Producer rules

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
9. Record start and end UTC, and per order one line on what took the time. Run apply and batch-check in the
   background; never overwrite an applied directory.

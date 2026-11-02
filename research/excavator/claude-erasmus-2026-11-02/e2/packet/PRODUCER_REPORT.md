# Producer report, Erasmus batch e2 (claude)

Start 2026-11-02T04:24:09Z; end 2026-11-02T04:29:30Z (UTC). Final applied directory: `applied-v2`.

## Outcome

EO:11303 (kind `filed_claim_correction`): submitted as a corrected replacement proposal. Status no; first end and whole-order end unchanged at 1986-02-25, express revocation by number in EO 12553 (held FR text, 51 FR 7237, table row "11303 Modifying provisions for transfer of personnel to certain public international organizations"). The order is one paragraph with one command (a one-person leave waiver and deeming for Reginald C. Price), so the single-clause inventory is complete. The disclosed alternative end (exhaustion on the order's own date, 1966-09-12) is kept as a disclosure and not adopted. Savings: transferred_or_accrued (credited leave and accrued benefits), source EO 12553.

What took the time: reading EO 10804 section 2 in both held texts and deciding how it bears on an order issued seven years later.

## Brief defect

- `unaddressed_citing_instrument` (EO 10804): confirmed and fixed. Held EO 10804 (1959-02-12; FR text `jobs/fr-originals/data/full_run/texts/EO_10804.txt`, 24 FR 1147; APP text) revokes EO 9721 and EO 10103. On the coordinator's question I read the limiting phrase "insofar as it affects any employee covered by section 6 (a) ..." (singular "it", placed after the EO 10774 item only) as limiting EO 10774 alone, so EO 9721 and EO 10103 were revoked generally, kept in effect only for non-electing employees serving on the Act's enactment date and "for the purposes of any rights and benefits vested under each such order prior to the date of the enactment" of the Federal Employees International Organization Service Act. The claim now says this in the rationale, the earlier-end check and the clause reason; it states that EO 10804 precedes EO 11303 and cannot be its end, that no held source shows EO 10804 extinguished it, and that the held texts do not say whether the 1966 waiver was treated as within the vested-rights saving or as a fresh grant (either way the end date does not move). EO 10804 is not in later_events because it is earlier than the order; it is not a frozen packet source, so it is cited by path and sha256 in prose only.
- Carried-over errors found on recheck and fixed: the prior wording "EO 9721, which stayed in force until EO 12553 revoked it" and "the parent order ended the same day" ignored EO 10804; both now state that EO 9721 survived after 1959 only within EO 10804's saving and that EO 12553 revoked what remained (it lists 9721 and 10103) on the same day as EO 11303. The prior single-quoted fragment of the order now uses double quotes on a fragment matching the held bytes on one line ("of all rights and benefits provided by Executive Order No. 9721").
- Rechecked and unchanged: EO 12553 quotes ("any amendments thereto, are revoked:", the 11303 row), absence of effective-date or savings wording in EO 12553, filing 1986-02-26, 31 FR 11963 identity and date. Added: a Cruden regex search of held texts (order-number forms, bare table form "11303 Modifying", and "Reginald C. Price") found only this order's own texts and copies of EO 12553. All quotations in the new prose were machine-checked against the held bytes.

## Checks

batch-check on applied-v2: 1 assembled proposal; actual checker 1 checked, 1 all checks passed, 1 mechanical pass, 0 unverified, 0 fail, 1 gate passed.

Geddes: applied-v1 had 1 flag (`reference_instrument_does_not_cite_order`: the rationale listed EO 10804 among full-read references though it does not contain 11303). Fixed in applied-v2 by stating why EO 10804 was read and that it does not name the order; resolution recorded in `applied-v1/GEDDES_RESOLUTIONS.json`. applied-v2 lint: 0 flags, 0 coverage gaps.

## Files beyond the view

None from the full packet. Outside the packet I read the prior claim line (`research/readiness/claims/claude-2026-10-31-apollo-g08.jsonl` line 9) and the prior sheet rows in `research/excavator/claude-apollo-2026-10-31/g08/packet/` as a draft, plus the held texts of EO 10804, EO 10103 and EO 12553.

## Tool defects

None blocking. Geddes `view` printed the whole view to stdout as well as writing it with `--write`. The `geddes lint` JSON has no flat summary key; counts are top-level fields.

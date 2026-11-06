# Crosswalk: Lowande and Poznansky and Thrower variables against the project's codebook

A crosswalk, not a change. The frozen codebook 2.0.0 (`research/production/codex-swarm-20261021/producer/verification/codebook/CODEBOOK_2.0.0_UNCHANGED.json`,
SHA-256 `a312fa9ccef9841da512307e567d200bc73d6fc2bd0132141e94a8aaca180b20`, rules TC01 to TC16) is untouched.
Claim vocabulary (`formal_disposition`, `first_cause_type`, `mechanism`, `date_kind`) is from
`research/stage19/CLAIM_SCHEMA.md` and the draft projection `research/stage15/LEGAL/OPERATIONAL_STATE_CODEBOOK_DRAFT.json`,
which says the frozen codebook 2.0.0 "remains controlling". All entries are in `CROSSWALK.csv`; this note explains the
differences that matter.

## The central difference

Neither prior dataset records whether an order still had operative effect, or when it stopped operating. Both record
one formal event from the National Archives disposition tables: a revocation (Thrower also supersession, partial
revocation, substantive amendment), with a year. In the project's terms that is the `formal_disposition` axis only.
TC01 says formal disposition, operative effect, cessation cause, judicial enforceability and evidence sufficiency "are
distinct" and that current force is never derived "from formal label alone". The project's headline,
`present_normative_effect` rolled up by TC03, has no counterpart in either dataset. Two consequences for any use of
their data:

1. A prior-art `revoked = 0` says "no formal act recorded", never "in force". A `revoked = 1` gives the latest date the
   order can have been in force by formal act, which is at most the latest cessation (TC13), not the first.
2. The project's derived field `formal_revocation_after_earlier_cessation` cannot be computed from their data: it needs
   an evidenced first end, which they do not have.

## Variable by variable

| Prior-art variable | Project term | Relation | Differences to remember |
|---|---|---|---|
| L&P `revoked_next_term` | `formal_disposition` + date, windowed | narrower | A 1 to 7 year indicator, non-ceremonial, formal act only. Later revocations (in Thrower's list a median of 7 years and a quarter 19 or more years after issue) are outside it by design. |
| L&P `immutable` | none; nearest TC06 durable_status, TC07 spent dispositive acts | different axis | Irreversible outcomes in the world, coded from the title. TC07 excludes completed pure dispositive acts (a land sale, a transfer, an appointment) from operative force unless an independent continuing norm or status is shown. So immutable = 1 neither implies nor excludes operative effect. TC06 needs an identified continuing legal status attributable to the order; L&P require no such status. |
| L&P and Thrower `ceremonial` | none; nearest `ever_operative_states` = `hortatory_only`, TC07 | no counterpart | The project decides effect clause by clause. A ceremonial order is excluded from L&P's models but is an ordinary census row with a status to determine. |
| Thrower `revoked`, `revoke_year` | `formal_disposition.instrument`, `.date`, mechanism `express_revocation` | narrower in time (year not date) | Revocation year is the year of a formal act and, for EO 12553 (377 orders with revocation year 1986 in Thrower's list), says nothing about when each order ceased. Project: TC13 cleanup dates supply "at most latest cessation". |
| Thrower `superseded` | mechanism `express_supersession` or `implied_supersession` | equivalent in kind | L&P drop it from their outcome; the disposition tables treat it as interchangeable with revocation (SI-2); ESTIMAND.md counts revoked, superseded or rescinded as formal disposition. |
| Thrower `partrevoked`, `substantive_amended` | clause-level `later_events`; TC02, TC09 | narrower | Partial changes do not support whole closure; amendment is an event on a clause, not an end. |
| Thrower revocation-type flags (`reject_revoke_eo`, `transfer_rv`, `abolish_rv`, `amend_rv`, `other_auth_rv`) | `mechanism`, actor | partial | Classify the revoking order's purpose, not the first end. |
| Thrower `revokedbyotherthaneo` (CSV) vs `revokedbyeo12553` (PDF) | `first_cause_type` | unresolved | The CSV header and the PDF codebook name different things. 140 rows flagged in the CSV, 98.6% of them revoked; only 1 of 377 orders revoked in 1986 is flagged. I cannot say which is meant. |
| L&P "nullified" (37 cases excluded) | `mechanism` other plus `mechanism_note` | no clean mapping | Not a listed mechanism. |
| Thrower `eonumber`, `year` | `instrument_id`, `date` | equivalent for numbered orders | Lettered orders are separate rows; Thrower's `year` is a president-coded year for orders in January of inauguration years (106 differ from the register's calendar year), while L&P's `year` matches the calendar. |
| L&P `foreign`, Thrower topic dummies, political covariates | none | no counterpart | Regression controls and subject tags; no legal-status content. |

## Where the definitions pull in opposite directions

- **Immutability versus spent dispositive acts.** L&P count extension of trust periods, pay raises, sales and
  designations as outcomes that are hard to undo. The project's primary convention treats a completed dispositive act as
  not having current operative effect (TC07; `primary_convention` in the frozen codebook) while preserving a
  `durable_disposition` tag and an alternate-convention sensitivity. An analysis that joins the two must not read
  `immutable = 1` as a lead for operative force; the variable may be better treated as a stratifier for TC06/TC07 review.
- **Revocation as end.** L&P and Thrower treat the revocation year as the event of interest and use survival or
  next-term models on it. The project's thesis is that this date often is only the latest cessation (TC13). The
  crosswalk gives no way to test that from their data (BASELINE.md, section 5).
- **Supersession and nullification.** L&P note that these terms are used at presidents' discretion (SI-2) and that
  inactive orders need not be formally ended; the project agrees in principle (TC01) and records the mechanism.
- **Partial versus whole.** The prior datasets carry an order-level partial flag; the project's whole-order end is
  "the latest clause first end" (ESTIMAND.md), so a partially revoked order is not an ended order.

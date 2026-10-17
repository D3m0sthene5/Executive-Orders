# Stage 12 independent legal ontology supplement (PROPOSAL; codebook 2.0.0 unchanged)

## A. Define estimands in terms of legal objects

A historically meaningful presidential executive-order census counts **an issuance of an executive-order instrument attributable to a U.S. President under the specified document-authorship convention**, rather than a number, table row, subject, legal provision, publication, or downstream administrative action. A single signed instrument can contain multiple discrete provisions; multiple documents can cite the same instrument; one document can have an appendix with separately numbered subjects. Preserve separate entities for **document**, **issuance**, **canonical label**, **editorial appearance**, and **operative clause**. Add fields `issuer_person`, `signer_person`, `presidential_direction_express`, `delegation_instrument_id`, `formal_heading_in_original`, `series_number_issued_at_time`, `retrospective_identifier`, `evidence_of_presidential_assent`, `original_bytes_locator`, and `document_identity_confidence`.

Clifford Lord's preface (PDF pages 11, 14–18) expressly reports that early Orders could consist of a President's endorsement on a subordinate's recommendation, and that the compilation included certain presidential regulations, express-direction departmental orders and administrative orders, but excluded distinct military orders and ordinarily excluded private presidential letters. These are **historical editorial inclusion rules**, not necessarily the contemporary legal definition. Label ambiguous document classes rather than forcing them all into one EO count. **EO 3016C, 3016K and 3016N** must be reviewed as part of the Polk-delegation class, under *United States v. Chemical Foundation*, 272 U.S. 1 (1926), which upheld certain acts undertaken through Frank Polk under valid delegated presidential authority. Validity of a delegated legal act and whether it belongs in a presidentially signed-instrument denominator are separate questions.

## B. Do not collapse these four outcome variables

1. **Current operative norm/status attributable to original instrument** (`currently_applicable_norm`): at least one command, permission, office/land status, legally available authority, or amendment-origin norm meeting stated attribution conditions applies in October 2026. TC07's completed one-time disposition may be considered spent if no independently persistent original norm exists.
2. **Historical legal consequences traceable to issuance** (`surviving_legal_consequence`): an original disposition is a necessary legal predicate for a current person's/property's rights even though no current command is being executed. Under this convention, a completed transfer or repeal may continue to matter. This should NOT be added to the active order count without stating the estimand because almost every former legal act has descendants.
3. **Formal text status** (`formally_revoked` / amended / suspended / superseded / unrepealed / indeterminate): ministerial publication/revocation event graph; separate from current operation.
4. **Policy similarity/lineage** (`policy_continuity`): substantive government policy pursued under independent successor authority. Must not be silently attributed to a legally spent predecessor.

Report both primary and alternative results for a diverse validation panel. If one can prove the alternatives generate materially different national distributions, publish multiple measures rather than one grand number.

## C. Operative episode state machine

A provision can take states: **issued/not-yet-effective**, **conditionally authorized but trigger unproved**, **currently operative**, **dormant but legally available**, **never became operative or legally invalid**, **spent by condition or completed performance**, **terminated by later government action**, **judicially limited by scope**, and **historical cause indeterminate**. Episodes can repeat after revival. Each episode needs `effective_interval`, `scope`, `actor`, `underlying_legal_basis`, `terminal_event`, `cause_class`, `first_end_date` or bounded interval, `source_interval`, `review_grade`, and `certainty`.

The **instrument** is substantive YES if any qualifying original norm/episode continues under chosen legal theory; it is substantive NO if all its original substantive scopes are demonstrably spent, and UNKNOWN otherwise. Because orders with continuing scope may also have three expired provisions, **the dataset must research first causes at the provision level for both YES and NO orders**. Order-level first cessation is ambiguous unless defined, e.g. the date the *last* substantive scope ceased versus the first of several provisions to cease. Record both.

## D. Pre-registered adversarial legal cases

- **Pure mass repeal, EO 12553**: does a persistent legal prohibition count as original current effect or as a completed disposition? Measure convention sensitivity.
- **Amender EO 13708 and host EO 12829**: record exact host provision/version; if host remains operative after amender revoke, specify attribution graph rather than casual lineage.
- **EO 3461 and EOs 2596/2602**: the successor revokes several wartime civil-service exceptions and protects incumbents. EO2602 itself conferred rights on appointees. Determine whether original terms, vested rights or only a successor saving clause supply present law. A 1921 revocation date is not automatically each predecessor's first cessation event.
- **EO 3016C/K/N (Polk)**: signature, presidential direction, delegation, sale/assignment execution and judicial ratification. The Supreme Court's 1926 decision addresses C/K's delegated legal authority; it does not prove the original instrument remains independently operative in 2026.
- **Land reservation and one-time transfer**: consistent theory of enduring constitutive property statuses versus completed dispositions.
- **EO 13174**: date conflict between printed 3 CFR / APP (October 27, 2000) and NARA 2000 disposition table (October 31); the commission's self-termination also requires proof of report, and later EO 13218 expressly revoked it.
- **Tax return access**: differentiate permission-to-inspect expiry from confidentiality duties and pre-1976 source claims.
- **Wartime workday suspension**: an old Comptroller General opinion might be nonbinding for private-rights carryovers; distinguish suspension expiration from entitlement survival.

## E. Pilot and statistical safeguards

The audit sample is **stratified and deliberately disproportionate** (more YES per unit than exists in the population); weight estimates by stratum size. Blinded reviewers independently retrieve full original and later chain **before seeing the project's current answer or selected excerpts**. Also perform a separate purposefully biased 'break the machine' challenge of the highest-risk clusters. No confidence interval about population legal accuracy is legitimate before independent human-source re-adjudication actually occurs.

A credible longitudinal analysis should follow issuance cohorts over calendar time. Treat continuing norms as right-censored at the 2026 cutoff; allow competing natural/affirmative/judicial causes, unknown terminal dates, changing original scope, and revivals/multiple episodes. **Do not perform survival analysis on the 2,322 NO records alone**, since that conditions on an observed terminal outcome and excludes still-active right-censored durations.

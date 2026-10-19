# T3 source-attribution defect routed to the job owner

`reviewer_role: ai_review`. Astra, 2026-10-18 ET. No job or legal claim changed.

In the pinned EO11022 and EO11256 claim-kit dossiers, multiple chain entries give
EO12379's revocation provisions to other actor IDs and attach those IDs' signing
dates. Exact entries, dossier hashes and fingerprints are preserved in
`CHAIN_ATTRIBUTION_EXAMPLES.json`.

Example: `CHAIN:EO:11022#2` names actor `EO:11654`, signing date `1972-03-13`, while
its source is the 1982-08-19 Federal Register issue and its provision is EO12379
section 12 revoking EO11022. EO11654 is separately a *target* of EO12379 section 19.
This cannot establish an EO11654 revocation of EO11022 in 1972.

Read source: `jobs/family-rule-sources/output/texts/queue_EO_12379_EO_12379_0b10726a10.txt`,
full held text, SHA-256 `ace4c68f1a5d2e44012894279ab3f38a0c8a08841bebe361d6eb39ae09b2d9bd`.
Its source PDF is https://www.govinfo.gov/content/pkg/FR-1982-08-19/pdf/FR-1982-08-19.pdf,
SHA-256 `5432431cc09039ad5672f86f17e1fb6dddf44075581197caa24cd70f1448da4a`,
47 FR 36099–36100, PDF pages 9–10. The header identifies EO12379 of August 17,
1982; section 12 addresses EO11022, section 18 EO11256, and section 19 EO11654.
This is an extract-based attribution check; no claim of viewing absent PDF images.

The two producers independently flagged the pattern while reading individual
dossiers. The coordinator inspected the saved source and exact chain fields.
Do not copy these generated event dates into first_end or later_events. Read the
actual actor's text and preserve unknown earlier cessation as a gap.

@Codex: investigate source-to-actor association before regeneration, preserving
these pinned examples. Enforce that actor metadata comes from the instrument
containing the operative provision, not another EO mentioned in a multi-order
source. Add regression examples for both targets and independently check any
affected accepted claims. This note is a repair request, not a change to your lane.

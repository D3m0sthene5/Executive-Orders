# MAITLAND: reviewed provision histories at a requested date

MAITLAND extends claim-kit using Stage 17's provision/transition vocabulary. It
does not rebuild the archived Stage 17 database or treat its old research rows
as executable legal approval. A bounded source-reviewed JSON bundle supplies
stable provisions and exact changes; the ordinary CLI validates and queries it.

```sh
python3 jobs/claim-kit/kit.py history-check research/progress/maitland/native/BUNDLE.json
python3 jobs/claim-kit/kit.py history-at research/progress/maitland/native/BUNDLE.json --provision P:13934:sec3c-chapeau --on 2025-02-01
python3 jobs/claim-kit/kit.py history-at research/progress/maitland/native/BUNDLE.json --provision P:10900:food-for-peace-coordination --on 1978-01-01 --write research/progress/my-history.json
python3 jobs/claim-kit/kit.py history-impact research/progress/my-history.json --changed research/progress/changed-hashes.json
```

Source, record, review and method hashes appear in every answer. The impact
command accepts a map from those dependency IDs to their current hashes (null
for deletion), and invokes existing Valla dependency closure. Include current
`membership:<provision_id>` pins from `membership_fingerprints(repo,bundle)` when
comparing bundles: those catch added/deleted/moved transitions and scoped reviews
that a prior answer could not otherwise observe. Unknown changes stay explicitly
unexamined. A revalidation report supplies no corrected answer or approval.

## Two different questions

`text_version` reconstructs the exact text supported by reviewed operations.
`operative_state` separately describes the state implied by supplied reviewed
legal effects. The latter requires a separate scope review, supported effective
timing and source-based examination. Neither is a complete historical interval,
whole-order status, cutoff-wide search result or human-certified finding.

Signing, publication and effective dates remain separate. A retrospective query
may use an instrument signed after the effective date; that is disclosed and is
not an answer about what someone could have known at the time. Unknown effective
dates do not acquire signing dates by default. Unsupported scope, savings,
conditional expiry or revival questions remain local unresolved questions.

The source proposal deliberately preserves fourteen unknown effective dates.
The native example includes only seven selected provisions and sixteen changes;
it is not a complete history of the named orders or of the entire corpus.

## Bundle and review contract

The `eo-provision-history/v1` bundle contains `producer`, `provisions`,
`transitions`, and `review_file:{path,sha256}`. Provisions retain Stage 17 fields
`provision_id`, `instrument_id`, `scope`, `norm_text`, `valid_start`,
`known_sunset_end_exclusive`, `source_id`. Transitions retain `transition_id`,
`affected_provision_id`, `actor_id`, `event_date`, `kind`, `old_rule` and `new_rule`.
Every record has an exact held text path, SHA-256, Unicode half-open character
span and quotation. Optional raw-file pins verify bytes, not original identity.
Auxiliary effective-date and savings witnesses are also checked and pinned.
Initial documentary chronology uses explicit `signing_date`, `text_date` or
`publication_date`, separately from normative `valid_start`. The pilot retains
the original proposals and a separately reviewed typed-date revision; inherited
date values or English metadata phrases do not silently date undated text.

The separately held `eo-provision-history-review/v1` ledger has exact record
hashes, exact provision scopes, distinct producer/reviewer identities, explicit
independence, verdict, and separate `text` and `legal_effect` rows. The pilot
retains full blind and after-reveal reviews separately; its derived accepted
ledger selects only exact upheld scopes. Missing or unresolved scopes supply no
approval. Independent AI review is not human or different-family certification.

Supported operations are explicit establishment, amendment, revocation,
supersession, reinstatement, renumbering and transfer. An amendment requires the
exact expected base version, unique old wording and the expected full result.
Restoration selects an explicit earlier version including its amendment ancestry.
Renumbering changes a label while keeping provision identity; transfer changes
the reviewed responsible officer without pretending the command ended.

Same-date operations need explicit sequencing. Cycles, wrong bases, ambiguous
substitutions, conflicting dates, stale sources/reviews and impossible episodes
fail closed. A reinstatement creates no continuous interval through revocation
and resets no expired clock. A reviewed expired period cannot become a negative
or fictional new episode. These are computational checks, not legal judgments.

## Production and evidence boundaries

The helper makes no network/model calls and writes no source requests, claims,
statuses, census identities, holdings or certifications. CLI output files must
be new JSON files under `research/progress`; canonical stores are outside that
route. Existing claim-kit `prepare/apply/batch-check/complete` remains the route
for any later claim proposal and its independent whole-case review.

Changing extraction/runtime code invalidates packets as usual. Keep runtime
integration between production waves; never patch a running wave or renew its
pins to make this feature available. The PR is isolated and unmerged during the
active Tribonian work. Integrate with the separate dispatch-preflight PR before
starting fresh packets, and run combined checks.

Current limitations: this is a bounded derived-research mode, not a corpus-wide
search or general legal interpreter. Exact review-file pins can conservatively
require broader revalidation than changed scoped record hashes alone. Source
extraction may retain incidental-citation false leads outside the repaired
reinstatement route. See the retained audit and native examples in
`research/progress/maitland/`.

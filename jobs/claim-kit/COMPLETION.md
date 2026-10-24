# Finish an independently reviewed batch

`kit.py complete COMPLETION.json --write research/excavator/RUN/complete-v1`
uses existing gates and the actual checker/tracker. It never repairs claims or
interprets legal/reviewer prose. The output directory must be new. Publication
requires explicit `--publish`; otherwise it prepares exact bytes and destination.
No command here changes provisional statuses, identities, holds or human reviews.

## Explicit manifest

All paths below are relative to the repository, including selectors. Every
`sha256` pins the complete raw file, while `claim_sha256` uses Stage 19 canonical
JSON (sorted keys, UTF-8, no spaces, ensure_ascii=False). Selection does not mean
the newest file or last review. One member per identity, 1–50 members, including
blocked/unresolved/owner-routed attempts. A producer claim selector must name a
physical JSONL `line` and preserve its terminating newline. JSON review records
may use `pointer` (RFC 6901) instead of `line`; omit both for a whole JSON object.

```json
{
  "schema": "eo-claim-kit-completion/v1",
  "agent": "producer",
  "producer_model_family": "OpenAI",
  "independence_requirement": "same_family_separate_context",
  "publication": {
    "mode": "own_claims",
    "path": "research/readiness/claims/producer-2026-10-24.jsonl"
  },
  "members": [{
    "instrument_id": "EO:123",
    "outcome": "submit",
    "claim_sha256": "CANONICAL_CLAIM_SHA256",
    "claim": {"path": "research/excavator/RUN/CLAIMS.proposed.jsonl", "sha256": "FILE_SHA256", "line": 1},
    "publication_kind": "whole_case",
    "review": {"path": "research/excavator/RUN/REVIEW.json", "sha256": "FILE_SHA256", "pointer": "/claims/0"},
    "after_reveal_review": {"path": "research/excavator/RUN/AFTER_REVEAL.json", "sha256": "FILE_SHA256", "pointer": "/claims/0"},
    "packet": {"path": "research/excavator/RUN/packet/PACKET.json", "sha256": "FILE_SHA256"}
  }, {
    "instrument_id": "EO:124",
    "outcome": "blocked",
    "reason": "Requested complete source is still absent."
  }],
  "controls": [{
    "instrument_id": "EO:123",
    "planted_claim_sha256": "CANONICAL_PLANT_SHA256",
    "seed": {"path": "research/excavator/RUN/SEED_RECEIPT.json", "sha256": "FILE_SHA256"},
    "review": {"path": "research/excavator/RUN/BLIND_REVIEW.jsonl", "sha256": "FILE_SHA256", "line": 1},
    "adjudication": {"path": "research/excavator/RUN/CONTROL_ADJUDICATION.json", "sha256": "FILE_SHA256"}
  }],
  "receipts": [{"path": "research/excavator/RUN/PRODUCER_TELEMETRY.json", "sha256": "FILE_SHA256"}]
}
```

`packet` is required for claims with `claim_kit` metadata. Completion repeats
the existing packet/source/prior-research and direct code fingerprints, plus
exact dossier checks. Ordinary claims without that metadata use the existing
strict source-span checks and actual Stage 19 gate/checker. Existing claims of
another owner require `mode: replacement_proposal` and an isolated destination
under research outside readiness; this prepares a proposal for that owner.
No filename overwrite or implicit owner acceptance is supported. Own canonical
filing must use an agent-prefixed new filename that is not shadowed by its prior
canonical filename.

## Recorded review decisions

Each selected review object must expressly contain:

```json
{
  "instrument_id": "EO:123",
  "claim_sha256": "CANONICAL_CLAIM_SHA256",
  "reviewer": "separate-reviewer",
  "model_family": "OpenAI",
  "independent": true,
  "separate_context": true,
  "review_kind": "independent_ai_source_review",
  "scope": "whole_case",
  "verdict": "upheld"
}
```

The reviewer differs from the producer. `different_family` additionally requires
distinct recorded model-family names; a family name or independent flag is an
explicit provenance assertion, not proof inferred by software. Retain the actual
source reasoning and evidence in the same record or pinned receipts. These
machine fields never replace source review. Historical records may be cited in
a new explicit attestation; do not rewrite historical verdicts to fit the format.

For ordinary partial research, use `publication_kind` and review `scope` equal
to `partial_research`. The reviewer additionally records `expected_gate_errors`
as the explicit, nonempty complete Stage 19 error list for this version. Completion preserves
those gaps and requires the actual mechanical checker to pass. Non-gate strict
span/provenance errors still block. A partial claim supplies no complete-history
or ready credit of its own; the actual tracker retains all remaining blockers.
An empty-gap partial review or a partial result that the actual tracker would
mark ready stops filing and requires whole-case review instead.
`pass_with_unverified` is retained as an exception, not silently promoted.

## Planted controls and after-reveal review

Ordinary completion requires a nonempty `controls` list. Each control contains
`instrument_id`, `planted_claim_sha256`, a pinned safe `seed` receipt, a pinned
`review` ref, and a pinned `adjudication` ref. Raw planted claims and the private
mutation key stay outside the repository; never include them among receipts.
The seed reference must select a standalone JSON object, without line/pointer
selectors, so retaining its complete bytes cannot copy an enclosing private key.
The seed object has exactly these fields: `schema: eo-claim-kit-control-seed/v1`,
`instrument_id`, `planted_claim_sha256`, `genuine_claim_sha256`, and `seeded_by`.
It records exact version provenance without exposing the planted content. The control
review has the same independence fields above, its planted claim hash, and the
recorded verdict. The semantic adjudicator's object must contain:

```json
{
  "instrument_id": "EO:123",
  "planted_claim_sha256": "CANONICAL_PLANT_SHA256",
  "review": {"path": "research/excavator/RUN/BLIND_REVIEW.jsonl", "sha256": "FILE_SHA256", "line": 1},
  "adjudicator": "semantic-reviewer",
  "caught": true,
  "scoring": "strict",
  "rationale": "Recorded judgment explaining whether the review identified the planted defect."
}
```

`scoring` is `strict` or `lenient`. Completion never searches the rationale for
field names or keywords. `caught: true` also requires a recorded rejected
control verdict. Missing or false control adjudication stops this batch's filing
and retains the exception. All planted versions are excluded regardless of
their verdicts. A genuine claim for any planted identity requires an exact
`after_reveal_review` selector in its member, with verdict `upheld_after_reveal`
for the **genuine selected hash**; blind review cannot approve another version.
That reviewed genuine version may be a correction after seeding; the seed's
original genuine hash is historical provenance, not an implicit approval.

## Outputs and limits

`CLAIMS.selected.jsonl` retains the pre-check selection, while
`CLAIMS.publishable.jsonl` contains only eligible, byte-identical producer lines.
`TALLY.json` counts every attempted member, outcomes, controls and exceptions;
`EXCEPTIONS.json` identifies exact failures. `PUBLICATION.json` records the
artifact hash, destination, proposal/owner limits and whether filing occurred.
`receipts/` and `INPUTS.json` preserve consumed producer/reviewer inputs verbatim.
Frozen packet/dossier and source files are pinned in place, not duplicated.
List producer logs, usage, blocked-work and acquisition receipts in `receipts`.
No fetch request is enqueued here; the existing request-contract command handles
that separately. Preserve source receipts through the existing source workflow.

`checker/` retains the actual offline checker audit and run log. Relevant source
bytes, custody manifests, direct policy code and tracker inputs are hashed before
use and rechecked before filing; new canonical files or holds invalidate a run.
`tracker-before/`,
`tracker-after/` and `TRACKER_REPLAY.json` preserve actual tracker results with the
selected claim/checker inputs substituted only for the proposed comparison. No
canonical output is overwritten. Missing required tracker inputs are exceptions.
The replay is proposed readiness, never a newly published corpus generation.
An exact unresolved `SOURCE_AUDIT_HOLDS.jsonl` version cannot file. Old holds and
their review bytes stay intact when a different corrected version is selected.

Each run reports elapsed time and explicit unknown model tokens/cash. Mansfield's
`TALLY_PROMPT.md` is the clerical precedent: file selection, exact copying, checks,
receipt retention and arithmetic belong here. Its semantic plant scoring remains
an independent recorded judgment. The `COST.md` transcript-token and cost estimates
are historical assumptions, not measured token savings from this implementation.

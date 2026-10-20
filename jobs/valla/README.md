# Valla

Valla traces reasoning premises and prepares targeted corrections within claim-kit.
Its unit is a frozen claim, an exact rationale span, and the particular conclusions
that an independently examined problem affects. It never changes claims, provisional
statuses, the codebook, readiness rules, human certifications or ownership.

```text
python jobs/valla/valla.py build --output <derived-output>
python jobs/valla/valla.py build --output <new-output> --package research/PATH/packet
python jobs/valla/valla.py correction EO:13792 --agent NAME --write research/RUN/correction-v1
python -m unittest discover -s jobs/valla
python jobs/valla/pilot.py --output <new-output> --run-id UNIQUE
```

The GitHub runner discovers `job.py`, input declarations and triggers through its
existing interface. Claim-kit orders Valla before itself when both are selected.
Valla reads claims, explicit review records and source dependencies; it never reads
claim-kit generated output. Batch preparation loads fresh bounded Valla context
from those inputs, seals it in `PACKET.json`, and renders it in `READ.md` and `view`.
Changed claims, evidence, review records, method files or compiler code require a
new packet. Existing packet source and assembler checks remain in place. There is
no job dependency cycle, network acquisition, model call or new source store.

## What the index establishes

Claims use the existing filename/line winner convention and Stage 19 canonical
claim hash. Older version references remain visible. Each producer rationale,
mechanism or reason has an exact JSON pointer, original text and hash. Normalization
changes case, punctuation and space only, retaining identity numbers and a map
back to original Unicode character offsets. `premises.json` is a small versioned
retrieval library. It covers categorical revocation reasoning, deadlines as
completion, silence as continuation and automatic duty succession. Negative or
quoted uses can match; even identical normalized text establishes no legal
identity, dependency or error. Source quotation text is excluded from reasoning
matching. Inspect unmatched cases as well as matches.

Source dependencies retain exact claim pointers, source-object hashes and existing
held-text/artifact references. Producer and explicit template metadata are indexed;
missing template lineage is reported as unknown, never inferred from a filename.
`--package` indexes exact `@rationale:KEY` references in existing CSVs and
`RATIONALES.json`. Those observed references do not establish that a published
claim was derived from that package. The compiler also indexes up to 100 tracked packages under research/excavator
and research/production, reporting any unmaterialized paths. Runtime correction
packets are excluded; --package permits additional explicit bounded selection.
Protocol files and the available operational draft are hashed. These pins describe
the current revalidation contract; producer-time protocol versions absent from
claims remain unknown. The controlling
frozen codebook was not separately located; the draft is not substituted for it.

## Explicit revalidation and component reviews

`research/readiness/method_reviews/*.jsonl` contains owner-routable review queue
entries, schema `eo-method-dependency-review/v1`. Each entry pins the actual claim,
exact rationale pointer/span, named producer and different reviewer, dated method
review, source/rule dependencies, and **specific** conclusion pointers. It must
state applicability, earlier-ending inquiry, scope, independent commands, savings,
analysis and the unresolved question separately. `review_ref` names a separately
held research record, hash and record ID; every asserted field must match that
record. Merely setting `independent` or matching a phrase does nothing. An accepted
entry requests revalidation, never a reversal or approval. A changed first-end also
invalidates support for the derived whole-order maximum date in the correction
context. It does not alter the production tracker or decide a replacement date.

`research/readiness/component_attestations/*.jsonl` uses
`eo-component-attestation/v1`. An attestation pins an actual reviewed claim version
by path, JSONL line and canonical hash, a component selector and value hash, method,
date, producer/reviewer identities, dependencies and a separate
`eo-component-review/v1` record. The review must explicitly uphold that component
with a substantive rationale. An overall upheld verdict or silence cannot supply
it. AI component review never becomes independent human review.

Allowed selectors are source identity (requires the exact original artifact path
and hash), exact quotation at a named clause scope, clause inventory (scope, original
words and sources only), and explicit factual findings under
`claim_kit.factual_findings`. Legal first-end, current-predicate and savings fields
cannot be relabeled as factual components. Every held source and at least one
versioned method must be an explicit dependency. Exact quotations additionally
re-slice the held UTF-8 text and verify its hash. Dependencies on changed fields,
parent objects, source bytes, methods, or revalidated conclusions refuse reuse.
Unknown dependency kinds fail closed. A changed producer or ending theory can
retain a sound quotation after those checks. This retains reviewed preparation,
not the old claim's whole-case approval.

The pilot records demonstrate these schemas without fabricating field approvals
from the existing Lambertini overall reviews. Component values do not confer
permissions: decision sheets still start unapproved, existing reservations remain
controlling, and existing claims require explicit replacement proposals and owner
acceptance. Every proposed correction still requires independent whole-case review.
After independent source-backed examination, the pilot adds five exact-claim
records to the existing SOURCE_AUDIT_HOLDS workflow. The matcher cannot create
these holds. The existing tracker withholds those cases pending correction and
ordinary whole-case review, retaining completed preparation steps.
The packet's invalidation list is a review aid; it is not another legal-status
or certification authority.

## Bounded pilot and efficiency limits

`research/valla/pilot-2026-10-20/` freezes five seed cases, three matched controls and
a separate eight-case sample selected after freezing the patterns. It contains
exact review records, source-backed alternatives, outcomes, failure history and
measurement limitations. Recovering the seed examples is not general accuracy.

`pilot.py` replays the existing baseline batch compiler pinned at PR #40 head and
the assisted compiler on three identical real correction tasks, alternating arm
order. Failed attempts and blocked members remain. It then prepares the five-case
owner-routed correction packet, validates reuse boundaries and runs the actual
claim-checker on the frozen existing claims and the actual readiness tracker.
Generated runtime packets remain in the existing claim-kit format under ignored
`research/valla/pilot-runtime/`; GitHub uploads them as review artifacts. The script
creates no attestations or legal decisions. Both arms retain the actual-event gaps
and independent whole-case review requirement. It measures machine preparation,
correction and integration; active producer/reviewer/coordination time and model
costs are unavailable. These timings cannot establish total rework savings.

The current smoke run records each component's actual validation result in
`CURRENT_CORRECTION_SAFETY.json`. Later changes to a pinned protocol can refuse
reuse of a historical attestation; this run does not renew it or alter the frozen
experiment. Every selected claim must retain an unresolved exact-claim hold with
its review artifact verified, start unapproved, and remain blocked in the actual
tracker. Refused reviews remain explicit in the current packet and report.

Junto receives only the concrete owner-seeded `valla_rework_salvage` hypothesis.
It remains unverified until complete matched correction tasks have measured
session totals and review outcomes. Failed work, review, correction, coordination,
integration and implementation costs belong in that test. A suspicious-claim count
or a quality correction is not a saving. Valla adds no price model or score rule.
Mountweazel's `pairs` command provides controlled fictional reasoning tests; answer
keys stay outside production. Blinding under the same account is **not technically
enforced**, and a test-harness roundtrip is not a reviewer-sensitivity result.

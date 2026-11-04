# Proposed versioned legal timing extension — not adopted

The October 28 ruling permits supported intervals. The immutable Stage19 v1
contract still requires exact first-ending and whole-ending dates. This branch
implements usable *factual* intervals through partial research; it deliberately
does not turn those observations into legal first ends. This document specifies
the remaining scientific-contract choice without changing v1 or the codebook.

## Proposed representation

Create a separately versioned legal-claim contract only after owner approval.
Retain every v1 exact-date field and its current gate. In the new version, exactly
one of the following representations would be required for each established
legal ending:

```json
{"timing":{"kind":"exact","date":"2017-12-10"}}
```

```json
{"timing":{"kind":"bounded","earliest":"2017-12-01","latest":"2017-12-31",
 "bounds":"inclusive_civil_dates","occurrence":"established"}}
```

These examples illustrate syntax, not EO13792 legal findings. Both require a
separately examined legal mechanism and target scope; affirmative evidence of
the ending event; source-bound reasons for both limits; inventory coverage;
earlier-ending, savings and residual-duty examination; independent exact-version
scope review; and the existing control and completion requirements. An occurrence
review never supplies legal-effect review. A known latest possible end with no
affirmative occurrence cannot use this bounded representation. Unknown timing,
uncertain occurrence and uncertain legal effect remain distinct unresolved fields.

The interval describes the **first legal ending**, not merely one later event.
An earlier unexcluded ending prevents claiming these are first-ending bounds.
Do not derive either limit just from a deadline, an order's signing date, a
document's publication, silence, an individual's presumed lifespan or an
unexamined general rewrite. Exact claims must not be converted to intervals to
avoid their existing obligations. One-day bounded records must use exact timing.

## Queries and whole-order aggregation

Civil-date queries have an explicit end-of-day convention. Given an independently
upheld first-ending interval [L,U], the ending has not occurred at dates < L; its
occurrence by the queried day is unknown on L <= day < U; it has occurred by the
end of U. This says nothing about reinstatement, other duties or operative state
without their separately reviewed transitions. Documentary chronology stays separate.

Only complete reviewed state histories establishing a common cessation permit a
whole-order ending envelope. The following formula is restricted to monotone
cessation: each complete-inventory clause has a supported first ending and remains
ended through the last such ending; added and successor operative duties are also
accounted for. To call this the *first* whole-order ending, the reviewed joint
history must also exclude every earlier whole-order cessation, including gaps
before later or conditional duties activated. Determine whether a latent command
legally persisted separately; do not equate nonactivation with no command. Without
that exclusion, label the result only a latest-clause-first-ending envelope.
Under these restrictions the enclosing whole-order ending bounds are:

`[max(clause earliest), max(clause latest)]`.

This is an enclosing bound, not an assertion that every day inside it is feasible
or that clause timings are independent. Common-source correlations are retained;
any more precise result needs independently supported joint constraints. An
unknown, surviving or unexamined clause prevents that aggregation. A clause
that ends, restarts, and stays active before another clause first ends defeats
this aggregation. Refuse the whole-order ending inference unless separately
reviewed state histories establish simultaneous cessation; without that, the
formula is only a latest-clause-first-ending envelope. Restorations and continuing
legal consequences require separate history treatment. No midpoint
or upper bound may populate a v1 exact-date field.

## Adoption and migration gates

1. Owner selects whether to authorize this versioned legal representation. No
   historical review or present proposal substitutes for that decision.
2. Publish the new schema, validator and frozen examples as a separate scientific
   change; retain the immutable v1 checker and an explicit version discriminator.
3. Implement bounded historical queries, strict source/review binding, whole-order
   aggregation and complete/refusal fixtures together. Reject missing occurrence,
   conflicting bounds, stale reviews, earlier-ending gaps and incomplete inventories.
4. Prepare fresh packets and obtain new legal-effect and whole-case reviews. Never
   migrate an old factual record or v1 review by changing hashes.
5. Report interval-ready research separately until the approved reporting contract
   expressly defines its readiness category. Human certification stays separate.

This branch supplies no estimate of affected orders or automatic unlocks. Apollo's
exclusion establishes production impact, not a supported ending for every waiver.
The reviewed EO13792 submission month illustrates useful retained factual knowledge;
its receipt, exact version/routing, first legal end and whole lifecycle remain open.

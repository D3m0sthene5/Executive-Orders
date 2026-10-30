# Effective-claim census and bounded ProQuest restoration

The census demonstrates **two additional custody beneficiaries: two effective
claims, two PDFs, ten cited source references, 84,609 retained bytes**. EO4782
becomes ready for human review in the native isolated replay. EO1547's bytes are
verified, but its existing working-text mismatch still blocks readiness. The
original PR105 three-case repair and retained evidence remain intact.

## Pinned scope and prior run

The census starts from PR105 source commit
`77abf218aa88ed89f4a16f4c93ed1baaf29098e0`, whose research inputs match main
`f9c6d806ad059dcad7875ab3708715f20ea386df`. Main was rechecked before publication;
no merge or main write was made. This substantial follow-on uses separate branch
`codex/proquest-custody-census-20261029` and only changes the helper, focused
tests, this additive evidence directory, its existing report link and own Kean/
Codex handoff records. Sol owns runner/dependencies, the lifecycle-assurance
swarm owns wider checker/tracker assurance, and Opus owns claim-kit/Valla.

Before further execution, PR105's Linux, Windows, Kean and security checks were
inspected and found successful. Its existing native branch run
[40976840282](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/40976840282)
also succeeded, publishing checker results at
`e87c9ad658a6708705f83a6dd43fd238f472926d`. That run checked 613 filed rows,
restored the original three sources, and did not refresh the tracker. No new
heavyweight workflow was dispatched here. The full fresh checker generation,
rather than older main receipts, is the census receipt basis.

## Census and eligibility

`CLAIM_CENSUS.json` and `EFFECTIVE_REFERENCES.json` enumerate 76 claim files,
613 valid rows, **612 effective claims** and **one superseded row excluded**.
They preserve 10,928 effective source references and 802 distinct explicitly
cited source hashes. These are source artifacts, not 802 PDFs. Selection follows
the actual checker/tracker convention: sorted filename and physical line,
last valid object for an instrument wins. All 612 effective versions match the
fresh e87c9ad checker receipt hashes; the independent reviewer compared every
effective claim key/hash and all 10,928 source-reference tuples.

The fresh checker reports 17 `custody_record_only` references across six
effective claims. Ten belong to the two additional ProQuest cases; seven belong
to four Federal Register cases described below. The original three no longer
have that failure in the fresh branch run. The nonpass CSV omits successful
per-reference rows; absence of a row is not fabricated into a new byte-check
receipt. The full source-association census keeps that coverage distinction.

| Case | Exact cited PDF SHA-256 | Bytes | Effective cited refs | Additional? |
|---|---|---:|---:|---|
| EO254 | `63a96efb348908966e3769b300d93b2a2cefd10dacdcee9bd8bf33f1f6748732` | 78,595 | 5 | No: PR105 |
| EO2171 | `6887d2296a53d1b5bafe5a40f11399a1a7b2d87331a6349ed220129a0112a4b7` | 42,225 | 5 | No: PR105 |
| EO4354 | `98b1a107e723aa5f9fc91a3f66c08c722b3377aaf24d4339320acf99da3ea3da` | 66,513 | 5 | No: PR105 |
| EO1547 | `2e446a8148b78c1398a3d3a90c3cdce3887444eadc3abe69942b84d67afb198e` | 33,614 | 5 | Yes |
| EO4782 | `cf42ef50a95da80b5cb6109bcb93716da0d9556124f75635e213bbe19f807138` | 50,995 | 5 | Yes |

The additional paths are `ProQuest Pre-1937 Orders/PT1-1912-EO-1547.pdf` and
`ProQuest Pre-1937 Orders/PT1-1927-EO-4782.pdf`. All five are regular Git blobs
at the pinned source tree and match their exact cited SHA-256 and PDF signature.
Inventory duplication of EO254 is not another artifact or claim beneficiary.
The current production selection has no shared PDF across these five claims;
shared-PDF deduplication and preservation of every reference are regression-tested.

The standard workflow checks out `jobs/`, `.github/`, `HANDOFF/` and declared
needs. It omits these root ProQuest PDFs. Pinakes retains their path/hash/text
associations, but the ordinary source adapter has no readable PDF to rehash in
that checkout. PR105 resolves the former 32 MB aggregate metadata abort for
its three hardcoded IDs; it does not select EO1547/4782. That is the demonstrated
remaining infrastructure failure, not a new legal or source-grade finding.

At the census's pre-restoration observation all five exact ProQuest Git blobs
were absent from the local checkout; their source paths were also outside the
standard checkout contract. Two objects were initially absent from the local
promisor object cache. A no-fetch object lookup is not evidence of absence from
the pinned tree: the worker corrected that provisional classification, fetched
only those two exact retained objects (84,609 payload bytes), then verified their
hashes. No whole PDF collection was checked out and no website was visited to
reacquire a document. The subsequent replay materialized the same retained bytes.

`SOURCE_ASSOCIATIONS.json` provides the complete artifact/reference join and
per-category distinct claim counts, distinguishing the initial ProQuest state
from post-restoration local availability. Counts of claims in different source
categories overlap. Metadata that does not establish current bytes is explicitly
unresolved, not counted as missing, as a conflict, or as an additional beneficiary.
Source-grade or legal equivalence is not inferred from file presence.

The final metadata census distinguishes these current observation classes:

| Observation class | Distinct artifacts | References | Distinct effective claims |
|---|---:|---:|---:|
| Exact local bytes rehashed after restoration | 5 | 25 | 5 |
| Repository copy reported by checker/source metadata, not rehashed here | 26 | 622 | 35 |
| LFS/separate-release metadata, not archive extraction | 3 | 243 | 91 |
| Metadata insufficient to establish current byte availability | 768 | 10,038 | 596 |
| Current transient-cache bytes established | 0 | 0 | 0 |
| Conflicting identity/path/hash established | 0 | 0 | 0 |

Artifact/reference columns partition 802/10,928; claim counts overlap. The five
first-row artifacts were instead **five retained regular Git blobs absent from
checkout** in the recorded pre-restoration census. No additional exact retained
candidate remained absent after replay. Zero established missing artifacts or
transient caches is not proof of corpus-wide absence: the four FR missing-path
exceptions and other insufficient records stay in the unresolved class. These
limits prevent sparse local metadata from becoming a fabricated defect count.

The four other current custody-only claims are EO10622, EO10631, EO10926 and
EO12743: four distinct PDF hashes and seven source references. Their historical
FR cache records do not establish a currently existing transient cache, and no
matching retained repository/release copy was identified in the existing source
contracts. Their registered cache paths are absent from both checkout and pinned
tree. EO10622's cited later EO12553 PDF is 47,814,063 bytes; the other originals
are 18,283,585 / 65,095,378 / 281,399,854 bytes. A different later-order PDF in
EO12743's dossier is not a substitute for its missing original. No consequential
equivalent retained-copy failure was established for another provider, so no
provider extension or acquisition was implemented. These four remain exceptions
requiring their own source-retention/research resolution, not inferred fixes.

## Smallest implementation and its limits

`proquest_inputs.py` now selects effective cited source hashes joined to the
existing instrument-specific Pinakes association and unchanged evidence grade.
It supports an explicit ID subset, with `DEFAULT_IDS` retained for reproducing
the original repair. PDF paths must be confined to the existing ProQuest roots
and point to regular blobs at the pinned Git version. Exact SHA-256, PDF
signature, LFS distinction, no-overwrite and pinned-blob checks remain mandatory.
An already-present PDF also has to match the pinned Git object.

Selection is deduplicated by artifact hash while retaining each affected claim
and reference. Conflicting identity/path/hash associations are refused. Metadata
is streamed with the existing per-file bound, without a growing corpus cutoff.
Each invocation is bounded to eight attempted artifacts, 8 MB per PDF and 24 MB
of payload reads. Smaller caller-selected batches and byte budgets are allowed;
larger caps are not. Deferred work has an explicit cursor tied to HEAD, metadata
hashes and selection. Stale cursors fail before writes. A resumed prefix is
explicitly not reverified and never presented as fresh success.

The native replay exercises three batches of 2 / 2 / 1 artifacts, reading
112,209 / 108,738 / 50,995 bytes. Three are `already_held`; two are
`restored_exact_blob`. Tests cover larger-than-three selections, shared PDFs,
wrong hashes, conflicting associations, missing objects, LFS pointers, symlinks,
per-file corpus growth, byte deferrals and resumption, and changed-selection
refusal. Restoration establishes availability only; the checker performs all
ordinary checks independently.

The existing single `job.py` call covers all five demonstrated artifacts.
**Automatic runner resumption for a future selection exceeding one batch remains
an explicit integration item owned by Sol**; a repeated default call would revisit
the same prefix. `RUNNER_CONTRACT.md` gives the exact API, required inputs/output,
cursor behavior and required declaration/invocation changes. No sparse-checkout
redesign is hidden in this patch. Git transport/pack bytes are not measured by
the payload-read bound; a retained promisor object fetch is recorded separately
from source acquisition.

## Verified native outcomes

`replay.py` uses the historical PR105 helper to establish the original three-case
baseline, selects the five effective claims through the ordinary checker, and
runs native checker and tracker gates unchanged. Only the two additional PDFs
are absent in the baseline, asserted before and after checking. Text inputs are
the exact retained Pinakes text blobs; no OCR or substantive research was repeated.

The tracker receives an isolated overlay of these five checker receipts onto
the full fresh e87c9ad generation. Every other receipt is preserved verbatim.
Overlay hashes, 699 checked-out input hashes and exact source/replay receipts
are in `replay/RESULT.json`. Claims, scientific reviews, gates, source metadata
and canonical checker/readiness outputs were unchanged. Full tracker execution
is used to obtain the five rows, not to publish a new global total.

| Case | Source custody, before → after | Checker, before → after | Human-review readiness |
|---|---|---|---|
| EO254 / EO2171 / EO4354 | Verified → verified | Pass → pass | Yes → yes |
| EO1547 | 5 record-only → 5 byte-verified refs | Fail → fail | No → no |
| EO4782 | 5 record-only → 5 byte-verified refs | Pass with unverified → pass | No → yes |

All 30 quotations across the five cases remain exact matches. EO4782's custody
was its last readiness blocker. EO1547's five working-text references still
produce `working_text_fragment_identity_or_grade_mismatch`: the claim declares
text hash `ba9127150a42a4ea81ddbc6e2b04ec70390e5d19e738088aaeb0707a4792115a`,
while the matching Pinakes fragment/text has
`537c53c6d0a9cea85bd02b9d633aad5d1bdb78a390184c5ff5e1ce5d6f2e2bc7`.
The mismatch is recorded, not mechanically rewritten or treated as reviewed.
Its tracker retains `NO_OFFICIAL_SOURCE_LOCATED`,
`ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK`,
`WORKING_TEXT_REVIEW_OR_DISCLOSURE_REQUIRED`, and failed clause-inventory,
ending/current-basis, savings/residuals and counterevidence steps.

All five remain `transcription_dependent`, with original-copy replacement and
quotation recheck required. No authenticity, legal applicability, page confirmation,
scientific review or certification was inferred from restoration. No isolated
gain was added to the published global ready count.

## Review, failures and adoption

69 checker/materializer tests (40 checker, 29 focused restoration) and 36 tracker
tests pass. `ENGINEERING_REVIEW.json` records a fresh separate engineering review,
exact file hashes, independent comparison of all effective references, rehashing
of the five Git objects, all 699 replay pins and native outcomes. Review found a
malformed instrument-ID crash and a hash-normalization incompatibility; both were
fixed with regressions. The review explicitly retains the runner-resume limit.

Failures were preserved: the obsolete three-ID-cap test initially failed after
the intentional scope change; a BOM-only first line exposed a parser issue and
was fixed. The first native follow-on replay rejected concurrent test-file input
drift. The second was rejected because source files reappeared during concurrent
work, invalidating its baseline; the actor was not established. Both rejected
replay logs and directories remain. A final exclusive replay with explicit source
absence assertions and frozen input hashes passed. None of the rejected runs is
used to claim readiness gains.

The metadata enumeration and source-association workers were fresh configured
`gpt-6-luna` contexts; the independent engineering reviewer was a fresh inherited
GPT-6-family context. This is engineering review, not a different-family legal
review. Token/cash telemetry and exact exclusive worker elapsed time were not
available, so no productivity or savings estimate is invented. Native logs and
test runtimes are retained; concurrent machine times are not added as labor.

Adopt PR105 independently if desired. The separate follow-on supplies Sol a frozen
source pin for combined integration; it does not merge, broaden source grades,
replace claim content or publish canonical readiness. The historical parent
`validate.py` remains reproducible at PR105's frozen commit; use this directory's
new replay for the expanded helper. Kean finding: `F-20261029-codex-proquest-census`.

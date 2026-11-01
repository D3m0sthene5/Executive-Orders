# Geddes repair, 2026-11-01

Geddes now catches **20/40 exact Apollo review defects**, up from 9/40. It flags
**18/254 filed claims**, down from 55. Independent inspection supports all 18
current warnings: 16 source-wording discrepancies and 2 missing-event-record
inconsistencies. The bounded audit found **0 false flags and 0 indeterminate
flags** among those 18; it does not certify any whole claim.

The original conservative comparison counted *every* flagged filed claim as a
false positive. That unchanged total-warning metric is 18, still above 5. It is
reported separately from the source-adjudicated false-positive measure; the
repair does not suppress genuine quotation problems to obtain a smaller count.

## What changed

- Complete own-order text is located with the existing clause-drafts locator,
  including recitals, heading and signature while excluding neighboring orders.
  APP items additionally bind the retained publisher ID/title/date/URL/node and
  text hash; URL slugs need not repeat suffixes. Native validated inventory
  overrides are respected. Unresolved boundaries abstain explicitly.
- Concepts tolerate OCR whitespace/soft hyphens. Verbatim quotations retain
  their case and punctuation and are compared to their own cited spans,
  including first-ending sources. A paraphrase is not rejected merely because
  it differs from literal source wording.
- Acting-order suffixes in reasoning bind the dated subject to a hash-pinned
  lookup candidate and retained APP record. The six missed suffix/FR cases now
  flag. FR volume/page/issue dates are compared to the identified own or actor
  source, never to unrelated signing or filing dates.
- Later-event checks preserve grammatical actor/object roles and treat explicit
  other-section discussion as a scope gap, rather than an automatically missing
  event. Distinct declared later events still require source-backed records.
- Name checks search literal names over an exact Git-retained jobs/**/texts TXT
  inventory, excluding clause-drafts. 'This code' is an unresolved antecedent,
  not a proper name. Publisher identities, dates and exact text spans bind
  positive counterexamples. Missing corpus members prevent negative conclusions;
  equal counts never substitute for equal membership. Snapshot bytes are
  reverified before output, including same-size/restored-mtime mutations and
  changes between source capture and verification.

The documented mandatory pre-handback lint step remains advisory. Claim-kit's
frozen review contract is unchanged; no lint output adopts a status or review
verdict. No claims, statuses, codebook, source grades or human reviews were
changed. No new claim was filed; certified remains 0. This follow-up repairs
Geddes only; the separately requested Sonnet/Opus resubmission remains unrun.

## Evidence and comparison

`repair/EVALUATION.json` verifies exact rejected-version and canonical-filed
claim bytes, physical records and packet inputs. It pins all five implementation
modules, not merely the CLI wrapper. `repair/INPUT_PINS.json` separately binds
newly consulted retained publisher metadata and unchanged helper code to base
`b37dcc438c62d2cc159081a1d5a01d44b63a9981`. These are additional present-corpus
inputs, not retrospectively invented Apollo review dependencies.

`repair/review/FINAL_EXACT_CORRELATION.json` independently matches 20 flags to the
exact historical defects. `repair/review/FINAL_FILED_FLAG_AUDIT.json` contains
all 18 filed-version warning examinations, exact source/claim hashes and spans.
Five recommendation-line absences and 11 exact quotation/punctuation mismatches
are source-supported. EO10010 and EO6539A explicitly describe later events that
have no later_events records. External EO10015/7020 passages corroborate those
examples; EO6900 is classified only for the internal reason/empty-list
inconsistency, not a newly verified legal proposition. No other claim is
silently corrected or rejected.

All 42 unit tests and 29 independent adversarial/collision probes pass locally.
The independent source/body coverage gap count fell 81→10→4. The four filed
own-body abstentions are EO6206A, EO6964B, EO12176 and EO12189. Rejected EO12891
also abstains on this check. None is a clean result.
The tests preserve neighboring-order, legitimate-recital, original/actor quote,
wrong-identity, suffix-collision, source mutation and snapshot-race refusals.

The local checkout verifies all 1,346 Apollo-held text pins, but it is sparse
relative to the full tracked name-search corpus. The local name check reports
39,770 members, 1,074 verified and 38,696 missing. That local result proves no
all-held-text negative. A PR benchmark workflow now materializes the retained
text corpus (without PDF collections), reruns the exact 294-version comparison
and uploads pinned results. Its result must be recorded separately from this
local comparison.

## Cost and retained history

New source-correct g03 views total 646,575 bytes for 24 orders versus 8,842,721
bytes for the prior whole bundle. This is a static payload measurement, not
actual cache-token or research-cost savings. No live producer experiment ran.
The cost report still reproduces the four Apollo track/role groups and keeps
missing usage unknown. `repair/TELEMETRY.json` records the two configured
gpt-6-sol workers and gpt-6-astra independent reviewer, prospective times and
unavailable token/active-time values. No usage totals were fabricated.

The earlier failed 9/40 and 55/254 comparison remains intact in the original
artifacts and `repair/baseline/REPORT_before.md`. `DIAGNOSTICS.tar.gz` and its
index retain the original large diagnostics losslessly. Intermediate repaired
comparisons, fixture corrections and failures are retained under repair/;
known-development-set performance is not held-out validation or scientific
review. One superseded local-v1 derived evaluation was overwritten before
checkpointing; its old seal remains explicitly superseded, without a claim of
byte-exact recovery. Current and future evaluations are checkpointed by SHA256. PR122 stays on claude/geddes-resubmit; no merge is authorized here.

# Geddes and Apollo retries — incomplete, 2026-11-01

This follow-up files **0 new claims**. Apollo's 254 filed claims are unchanged.
Geddes is an experimental advisory implementation, and its requested accuracy
targets are **not met**. The 40 rejected genuine versions are reconciled into
fresh-assignment inputs, but no fresh packet was prepared and no Sonnet
production, Opus review, new control experiment, or publication was performed.
The certified whole-lifecycle count remains **0**.

## Base and scope

PR121 was open and unmerged when checked. Work branches from
`claude/apollo-moon`, commit `40eb4b561ad657413169dae72bc0262efd4b119d`,
and the follow-up PR targets that branch. The required Kean/handoff/AGENTS and
CLAUDE instructions were read, then
`python3 -I jobs/kean/kean.py search lint telemetry resubmit apollo` was run.
No existing Apollo packet, canonical claim, status, codebook or human review
was edited. No packet folder was committed while another was in flight.

## Geddes implementation and limits

`jobs/geddes/geddes.py` provides `lint`, `view` (stdout or `--write`) and `cost`.
The implementation reuses claim-kit's existing packet decoder. It verifies
held-text hashes, keeps source/integrity gaps distinct from advisory flags,
preserves the target clause envelope rather than trusting an EO filename,
and checks quotation case and spans against their own cited source.
Missing actor sources and literal-name searches are disclosed. Corpus caches
are scoped and invalidated on observed file changes; conflicting pins are
reported. A job adapter, dependencies, README and GitHub Actions test workflow
are supplied. No readiness-tracker job-name registration list was found;
the tracker was not changed.

The documented producer handback step is `batch-check`, then `geddes lint`,
inspection/correction or disclosure of its output, then ordinary blind review.
This option was chosen instead of modifying batch-check because an advisory
development tool must not change claim-kit's frozen review dependency contract,
status, review verdict, eligibility or publication gates. The linter never reads
the review records. The separate evaluation harness uses them only as labels.

The minimum requested coverage is not fully delivered: arbitrary prose
attributions remain heuristic; structured source/actor checks do not reliably
bind every suffix or FR detail in free-form reasoning (including Apollo's three
known suffix and three FR-detail cases); some quoted/paraphrased source claims
are missed. Literal-name scans cover the verified Apollo packet-held union,
not the entire held corpus. Recitals outside the proven clause envelope remain
unchecked or flagged for inspection; legitimate recitals and inventory overrides
can therefore receive scope flags. These limitations matter to routine use.
Do not treat a clean result as completed source examination or deploy this as
an automatic rejection rule.

## Retrospective results

`evaluate.py` verifies the exact historical claim files, records and packets
against the Apollo commit. It compares 40 genuine rejected versions and the
actual 254 canonical filed versions, with filed/proposed equality checks.
All 1,346 unique held-text pins were restored and independently rehashed with
zero conflicts, missing bytes or mismatches. This is byte integrity, not original
authentication or new legal review.

| Measure | Result | Requested target |
|---|---:|---:|
| Exact recorded review defects caught | **9/40 (22.5%)** | At least 12/40 |
| Rejected versions with any flag | 15/40 | Not a recall measure |
| Filed claims with flags | **55/254 (21.7%)** | At most 5/254 |

The nine defect matches are EO6875, 10634, 11013, 11314, 11329, 11431, 12095,
12398 and 12429. Unrelated flags on six other rejected versions receive no
recall credit. `DEFECT_CORRELATION.json` records the coordinator's comparison
to each exact reviewer defect; it is not a new whole-case review. For the
requested filed-set metric all flagged filed claims count as comparator false
positives. They have not each been newly adjudicated, so this is not a claim
that every old filed claim or every Geddes warning is substantively correct.
Both requested thresholds fail.

This is retrospective work on a known development set, not held-out validation.
Initial failed comparisons and the corrections they motivated are retained in
`measurements/DEVELOPMENT_FAILURES.json` and review records. No per-EO allowlist
or review verdict is used by the implementation.

Two large raw diagnostics are retained losslessly in `DIAGNOSTICS.tar.gz`;
`DIAGNOSTICS_INDEX.json` records each original path, size and SHA256. Extract
from this report directory with `tar -xzf DIAGNOSTICS.tar.gz` to restore the
referenced raw paths. The archive was reopened and every member byte-compared.

## Payload and cost measurements

The real g03 batch has 24 packet members. Its READ.md, LOOKUPS.json and
LOOKUPS.details.json total **8,842,721 bytes**. All 24 Geddes order-view files
together total **634,144 bytes**, a **92.8% smaller payload** than reading that
whole bundle once. `measurements/PAYLOAD_SIZE.json` pins the inputs and every
view output. Rereading the whole bundle once per order would be 212,225,304
bytes; that is an explicit hypothetical read pattern, not observed usage.

**Actual cache-read tokens saved: unknown. Actual tokens/time saved per new
filed claim: unknown.** There was no Track B model run. Byte counts and bytes/4
display estimates are not Sonnet cache telemetry, money saved, or proof that
Geddes reduces total research cost. The false flags also create correction work.

`measurements/APOLLO_COST.json` reproduces the retained CSV's four track/role
groups, with 127 filed claims per track:

| Track and role | Output tokens/filed | Cache-read tokens/filed | Active seconds/filed |
|---|---:|---:|---:|
| NRA producer | 5,202.58 | 816,905.33 | 79.14 |
| NRA reviewer | 1,621.50 | 312,930.80 | 36.15 |
| General producer | 9,274.57 | 2,171,291.19 | 147.28 |
| General reviewer | 2,857.17 | 607,146.66 | 45.72 |

This is independent arithmetic over the retained CSV, not a re-audit of its
unavailable private transcripts. `cost` supports explicit future filed-count
sidecars and preserves missing usage as null, including fractional active time.

## Track B: exact inputs, execution blocked

`inventory/build_inventory.py` reconciles 35 blind genuine rejections plus
five rejected genuine after-reveal versions: EO6876, 8163, 10103, 10915 and
12095. Assertions enforce 40 distinct exact versions, 6 NRA/34 general, source
file/record hashes, the five after-reveal identities, control exclusion and
owner holds. The output batches are NRA6, general20 and general14, with every
prior claim and exact reviewer defect retained.

EO6471A and 7016 remain excluded under open A-20261031-1. The six original
completion drops remain excluded; restoring working text here did not establish
their missing PDF/mirror custody or resolve quote/checker OCR mismatches.

The available collaboration runtime exposes OpenAI agents, with no configured
Sonnet/Opus route in this workspace. No models were relabeled or substituted
for the required scientific roles. Fresh prepare also needs the retained
compiled outputs and complete preparation context materialized and validated
on the intended base; absence in this sparse checkout does not establish that
the repository lacks those outputs or that regeneration is necessary.

Resume by fixing the lint precision/coverage gaps, making the required execution
route available, validating prepare dependencies and preparing three **new**
packets. Give each Sonnet producer its exact retry row, require source-based
correction or a named block, retain pre-handback lint and then use fresh Opus
blind reviewers. Reuse Apollo's plant/reveal/finish tools with current paths,
keep control adjudication with the coordinator, publish sequentially under the
lock only with zero misses, and commit only once no packets remain in flight.
Historical Apollo controls confer no control credit on these unrun retries.

## Verification and worker costs

Exact implementation SHA256:
`3472f558def50808177602e7e86472e156286c32aa2fed460e2563d3e94f398b`.
Independent engineering evidence is in `review/FINAL_REVIEW.json` and
`review/REVIEW_OUTCOME.json`: 20 independent/targeted probes, 14 unit tests,
18 acceptance checks, actual retained CLI, source boundaries, supplementary
lookup fallback, actual shared memo/hash, cost arithmetic and unchanged
claim-kit contract. These engineering checks pass; they do not overcome the
failed accuracy comparison or approve any claim.

| Worker | Configured model | Tokens / active time | Measured time |
|---|---|---|---|
| Geddes engineering | gpt-6-luna | Unavailable | Full session unavailable |
| Rejection inventory | gpt-6-luna | Unavailable | Full session unavailable |
| Independent engineering review | gpt-6-astra | Unavailable | 1,099.014s prospective wall including waits; final check 0.766s |

The same workers resumed after hydration interruptions; no duplicates were
started. `TELEMETRY_AVAILABILITY.json` distinguishes unknown measurements from
zero. Apollo's `tools/moon_telemetry.py` was inspected, but these collaboration
tools supply neither its required per-worker transcript files nor per-message
usage records. No fabricated transcript adapter or token totals were created.
Coordinator, hydration and correction costs are not measured, and no net saving
is claimed.

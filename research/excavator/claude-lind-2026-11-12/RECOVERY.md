# After stage 0: recovery of EO 12753, an earlier check, and what to buy next (2026-11-12)

The stage-0 result stays **0 ready of 30**. Everything below is a later repair, with its own incremental and
cumulative cost. Per-order diagnosis: `FAILURES.md`.

## 1. EO 12753 recovered to "eligible" (not yet ready)

- **Failure:** EO 12753 was upheld by both blind arms on claim sha256 `47f70df6…`. At completion, the actual
  checker graded its ending source `custody_record_only`. That source is the APP page of EO 12791, sha256
  `576b4755…`, captured by Common Crawl on 2025-11-11.
- **Authorized route:** `jobs/cotton-capture-custody`. Its README defines it for exactly this case: it re-fetches the
  exact recorded WARC byte range and keeps the bytes only if the hash matches.
  1. Wanted line added (PR #305).
  2. Run 43324287671: succeeded, bytes kept (`captures/576b4755….bin`, `SOURCES.jsonl`).
  3. The outputs were copied onto this branch without the claim-kit code change, so completion ran on the kit the
     reviews were made under.
- **Re-completion** (`completion/complete-v2`): `kit.py complete` with the unchanged members and receipts.
  - **eligible 1 (EO 12753), exceptions 0**, control still caught;
  - published only as an isolated replacement proposal (owner acceptance false).
- **Validity:** the claim, the evidence version, the status review and both blind reviews are unchanged and remain
  valid. The claim hash did not change, and only the custody of bytes it already cited was added.
- **Reviews:** none renewed, and no attestation was created.
- **To reach ready (6/6),** one owner decision is needed: adopt provisional NO for EO 12753 (ask
  A-20261112-lind-adopt-12753). After it, the route is deterministic, as for D-20261110-papinian-adopt:
  1. an `ADOPTION_ROWS.csv` row;
  2. the claim filed under `research/readiness/claims/`;
  3. a readiness-tracker run.
- **Incremental cost of this recovery:** coordinator session time only (included in section 4); runner minutes
  unpriced; $0 producer or review tokens.

## 2. The earliest place for the cheap checks

| Check | Earliest stage possible | Existing tool | In this pilot |
|---|---|---|---|
| Mandatory original and clause source held | before producer work | dispatch check (already run) | 7 orders stopped; cost only an assessment row |
| The overlay validator's original rule (`acceptable_as_original` or an F6 `working_text_basis`) | before producer work | the frozen evidence fields | The brief reused from Papinian predates F6 and told producers to block replicas the validator now accepts (EO 1957, 4193; both also lacked an ending source) |
| Selected source bytes held (custody), quoted spans, identities, dates, structure | **after drafting, before blind review** | the actual claim checker, offline as completion runs it | Not run before review: undecided drafts reach the actual checker only at completion (`batch-check` checks 0 claims on this route) |

- **Change made:** `kit.py overlay-check` now runs that same checker offline via `batch.actual_check_offline` and
  fails a draft it does not fully pass (PR #305; kit suite 801 pass).
- **Completion still re-checks** the final artifact.
- **What it catches on the pilot's 7 drafts** (re-run, 16 s, no model tokens):
  - EO 12753: custody, the completion failure;
  - EO 12701: two custody-only sources;
  - EO 13476: two quotations too short to verify.
- **What it does not catch:** the five substantive defects that blind review found. They need source-based judgment.
- **Costs it could have avoided here:** in review dollars, about **$0**.
  - EO 12753's reviews stayed valid after custody was added.
  - EO 12701 and 13476 also had substantive errors that still needed review.
  - Its value is ordering: retain bytes before review, and do not send a draft whose sources cannot be kept. It also
    removes a completion failure and its diagnosis.
- **Avoided, gross:** the diagnosis of a completion custody failure. In this session that took about 12 coordinator
  calls, not separately priced. **Net saving:** not established. The change cost part of section 4's diagnosis
  work.

## 3. Ranking the other repairs (from the recorded defects; none started)

| Rank | Order | Defects to fix | Unresolved substantive risk | Why |
|---:|---|---|---|---|
| 1 | EO 12437 | one sentence (a false "no other citation" claim) | low: both arms agree on the spent-on-issue reading; B upheld | the cheapest and clearest |
| 2 | EO 11943 | one sentence (EO 12010's effective date) | low: A upheld | the same shape |
| 3 | EO 13476 | the count, the sec. 4(a) date and two short quotes | medium | several edits |
| 4 | EO 12701 | the identity of EO 12334, plus two custody retentions | medium | Cotton plus edits |
| 5 | EO 11294, EO 9447 | each clause's first end under ruling P2 | high: a legal reading | needs judgment, not text fixes |

- **Next justified repair, if bought:** ranks 1 and 2 together.
  1. One producer correction of the two sentences (about $0.5).
  2. `overlay-check` (now including the offline checker).
  3. One small blind review set with both arms and one planted control (about $3-5).
  4. Completion.
- **Cap:** **$8**, all-in, in a fresh coordinator context.
- **Expected result:** 0-2 more eligible claims, each still needing owner adoption.
- **Recommendation:** buy it only if a correctly filed dossier at about $3-6 marginal is worth it to you; that range
  is an estimate. The substantive ranks 3-5 are not worth buying before ranks 1 and 2 show that corrected claims
  pass.

## 4. Costs (list-price allowance; cash $0)

| | USD |
|---|---:|
| Optimization analysis before the pilot (from the $3,727 question to the approved plan) | about 39 |
| Stage-0 pilot, Bentham usage | 23.07 (producers 5.79, reviewers 7.12, coordinator 10.16) |
| Coordinator after the pilot: publication and debugging, diagnosis, the earlier-check change, recovery | in the PR description (measured from the transcript) |

- **The pilot's coordinator cost, by measured time window** (an observed split, not an allocation):

  | Window | USD |
  |---|---:|
  | Setup | 3.48 |
  | Routine coordination | 6.25 |
  | Publication and debugging | 2.02 |

- **Cause:** the coordinator is a long-context session (each call re-reads it).
- **Next paid phase:** start it from the compact handoff in `HANDOFF/notes-claude.md`, in a fresh context.
  Repetitive steps are scripted: `research/lind/stage0/draw.py`, the kit commands, and the overlay review prep and
  finish adapted from Papinian.

## 5. The group comparison

The hard-only group did worse at every intermediate stage:
- dispatch-blocked: 5 vs 2;
- producer-blocked: 9 vs 6;
- submitted: 1 vs 6.

Both groups produced 0 ready dossiers. It is a provisional scheduling signal (work the all-gates pool first). It is
not evidence that soft-filtered orders have no value, and it is no reason to exclude them permanently.

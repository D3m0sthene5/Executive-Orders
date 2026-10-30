# Native full-code production rehearsal (packet-friction branch), batch r1

Engineering validation of the repaired claim-kit/Valla code on a real batch. The packet and its supplements
were freshly prepared, the claims were assembled against that exact packet, and independent review and
completion used the native path throughout. It ran in an isolated replay tree (a copy of the
`opus/packet-friction` commit `71b06f9`, whose claim-kit outputs match current compiler code). Its publication
went into that tree only. **No canonical claim, status or authoritative record changed in the repository.**

## Batch and outcomes

| Order | Outcome | Basis |
|---|---|---|
| EO 6242-B, 6309, 6310, 6311, 6314 | submitted; independently upheld; eligible | Plain section 3 code approvals. Single command. No own terms. No held later order names the code. Ended 1935-06-14 by S.J. Res. 113 section 2, under the shared, independently reviewed NIRA analysis. |
| EO 6254 | blocked (hold retained) | Held EO 6730 (supplemented via `SUPPLEMENT:EO6730`) supports both a supersession reading (end 1934-06-11) and an amended-code reading (1935-06-14). No held source decides, and the shared analysis leaves the question open. |
| EO 6438 | blocked (hold retained) | The only held text of the order is a Wayback-only capture, which fails offline custody. Held EO 6620-B (`SUPPLEMENT:EO6620B`) is evidence of an earlier end for conditions 2 and 3 (1934-02-26) once custody is met; it was not the reason for the block. |

- **Selection.** A Sonnet screening worker narrowed the 198 untried NRA pool orders to 106 plain candidates.
  The five plain orders came from that list. EO 6254 and 6438 are the t5 orders whose held later orders (the
  H13 examples) could not be cited before; both now enter through the existing source-supplement route. No
  undecided order is included: a different-family status reviewer is not available in this session, and a
  same-family review would not satisfy that requirement.
- **Producer.** A fresh-context Sonnet producer filled the sheets. `apply` and `batch-check` gave 5 strict
  passes, 5/5 actual claim-checker passes and 2 blocks.
- **Reviewer.** A fresh-context Opus reviewer (same family, separate context, the requirement for these
  statused orders) reviewed a blind set of five lines. One line was a planted control: EO 6310 with both end
  dates moved to 1935-06-16. The reviewer upheld the four genuine lines and rejected the plant, citing exactly
  the two changed fields. After the reveal it upheld the genuine EO 6310 version, recorded its own control
  adjudication (caught, strict) and found both blocks supported.
- **Completion.** `kit.py complete --publish` with the full repaired code selected 5 claims, kept 2 blocked,
  recorded 1/1 controls caught and wrote 5 claims (isolated tree; see `complete-v2/ISOLATED_PUBLICATION_NOTE.json`). Adoption-ready artifacts:
  `r1/packet/supp/completion/COMPLETION.json` and `r1/packet/supp/complete-v2/`. The packet verifies on the
  branch checkout, so the same manifest can be completed after merge. No attestation was copied or
  re-targeted.
- **Adoption dry run.** `kit.py complete` without `--publish` on the branch checkout at `d13766a` reproduced the
  same 5 eligible claims in 55.8 s. Its publishable bytes have sha256 `9ddb845b…`, identical to the isolated
  publication. Nothing was written to `research/readiness/claims`. Receipts: `adoption-dryrun-d13766a/`.

## Measured cost of the bounded path

**Machine** (each native step its own process; seconds and bytes read; repaired code):

- prepare 2.1 s
- declarations 0.1 s
- source-supplement prepare 15.9 s (cold cache)
- `cruden.py lookups` 113.6 s (NRA research tool, outside claim-kit, see limits)
- view 2.9 s
- apply about 5 s
- batch-check with actual checker 25 s
- complete 60.8 s

**Same inputs, both code arms** (`machine_path.py`, one tree, cold caches; prepare through batch-check, without
lookups or completion):

| Code | Total | Supplement | Each view | Apply | Batch-check |
|---|---|---|---|---|---|
| Baseline | 214.0 s | 26.8 s | about 18.4 s | 60.6 s | 80.2 s |
| Repaired | 53.5 s | 16.4 s | 2.5 s | 4.8 s | 25.1 s |

Claims and outcomes were identical in both arms, except the expected `dossier_sha256` re-version.

**Model work** (harness totals per context; cache read/write split and cash cost are not exposed here):

| Role | Model | Tokens | Tool calls | Wall |
|---|---|---|---|---|
| Screen (one-time selection) | Sonnet | 123,374 | 32 | 944 s |
| Producer, 7 orders | Sonnet | 111,493 | 16 | 207 s (producer clock 21:17:34–21:20:52Z) |
| Blind reviewer, 5 lines | Opus | 130,996 | 27 | 218 s |
| After-reveal review, control adjudication and block check | Opus | 54,881 (cumulative 185,877) | 20 | 187 s |
| Coordinator (selection, preparation, plant, manifest, diagnosis) | Opus | not exposed | — | about 50 min |

These figures do not support a token-saving claim. The NRA batches' costs were reported as weighted totals
that include cache reads, which is a different metric from these harness totals. The machine speedup is not
evidence of a model-token saving.

## False invalidations, retries and the one process error

- **One refused completion, caused by a coordinator process error.** The coordinator first placed the blind
  review set under `research/` outside the packet folder. Its copies of the batch's own claims were correctly
  discovered as new versions, and completion refused the packet ("changed prior research").
  - Cost: 27.3 s of machine time, plus about 5 minutes of diagnosis.
  - The failure cost one packet verification, not one per member (fixed this session).
  - Fix: in the run, the file was moved byte-identically into the packet folder.
  - On review, a set that contains a plant belongs outside the repository entirely, as the planted-controls rule
    already said. `jobs/claim-kit/COMPLETION.md` now states both rules.
  - Refused receipts: `complete-v1-refused-review-set-outside-packet/`.
- **Producer.** No retries: one apply and one batch-check.
- **Reviewer.** No re-runs and no key exposure. The key stayed outside the review tree throughout. The key and the
  blind review set (which contains the plant) are not committed; their hashes are in `OMITTED_FILES.json`, and
  the seed receipt in `completion/` pins both claim versions.
- **Control adjudication.** Under AGENTS.md ("keep substantive control adjudication ... with reviewers"), the
  reviewer adjudicated its own control. Completion requires only that the adjudicator differ from `seeded_by`.
  Whether a third party should adjudicate is a policy question, flagged and not changed.

## Targeted checks run with this code

- **Concurrency** (`research/progress/opus-packet-friction/receipts/phase2/concurrency_*.json`), all as real
  `kit.py complete` processes:
  - **Production's disjoint race.** The real t5 and t6 completions, run concurrently, both publish. Their
    bytes are identical to production's, and t6 receipts t5 as a disjoint concurrent file. Production lost an
    803 s run and a serial retry to this.
  - **Same instrument, one checkout.** Exactly one completion publishes and the other is refused at the locked
    recheck. This was shown with t6 and with this r1 batch under the full code.
  - **Separate clones** (own Git directories). Both publish, because the lock is per clone. At merge time:
    - **Same filename:** an add/add conflict.
    - **Different filenames:** a silent clean merge in which the later filename wins.
    - `kit.py publication-audit --base main` now reports that case and exits non-zero.
- **Cache correctness.** Real-tree perturbations matched a fresh index in all 16 states and their reverts:
  provider added or deleted, same-size edits with mtime restored, and a referenced text deleted or created
  (`receipts/phase2/CACHE_CHECK.json`).

## Limits

- 5 reviewed claims are a small engineering sample, not a production rate.
- The publication went only into the isolated tree; adoption into canonical claims is a separate decision.
- `cruden.py lookups` (113.6 s) is now the slowest machine step on this path. It is research tooling in the NRA
  folder, outside this assignment's ownership, and was not changed.
- The undecided route was not exercised end to end (no different-family reviewer).
- Machine numbers come from one 4-CPU container.

# NCSSR reuse candidate stopped at the incremental-work gate

The proposed NORTON acceleration experiment was executed through its first gate and stopped. The existing ordinary explicit batch can already support one investigation of the NCSSR report-submission event across EO12335, EO12397 and EO12402. No additional investigation that NORTON would remove was established. No cost arms, new source research or software change were commissioned.

This is a local decision against investing in this candidate on the available evidence. It is not a measured zero-effect result, a rejection of all NORTON uses, or a demonstration of campaign acceleration. The recommendation should have checked this existing capability before presenting this example as the next intervention.

Main was reverified through the connected GitHub API at `76d256857784621343e13b5f80d8dbeaeccde0ee`; PR60 at `e21be540396c3c4cd5b5d62abc35f4a4aa9b0534` and PR61 at `f8238af3fbbba158101b86e33dd1d6a60b5e7edb` remained open and unchanged. This isolated branch starts from PR61. The three compiled dossiers retain their original generation, whose input commit is `d66f4040`; they are not a new corpus build.

The test compares NORTON to a competent ordinary shared assignment, rather than requiring separate researchers to forget a shared answer. Its originally authorized sequence was: establish actual incremental work, resolve/review a shared fact if justified, measure the entire resulting workflow, and examine eligible scale before expansion. The first condition was not established, so the conditional later stages were not run.

## Evidence from actual inputs

| Check | Observed result | Meaning |
| --- | --- | --- |
| Exact NCSSR registry | One question; four candidate applications across three orders; no producer answers or factual/application reviews | Candidate applications are not observed investigations. |
| Existing canonical research | EO12335 claim, `claude-2026-10-18-codif-b1.jsonl:14`, already connects both reporting amendments and explicitly retains the missing submission date | Prior research already recognizes the common event; no automatic reuse of its legal conclusions. |
| Native ordinary `batch.encode` and `decode` over the three exact dossiers | 19 text blocks, 17 source records, 62 shared objects; 17 source text paths validated; zero codec issues; exact roundtrip | The actual evidence is shareable through the existing implementation. This is a metadata/span check, not source authentication or legal review. |
| Same native functions with NORTON factual context omitted in memory | Same 19 text blocks and 17 source records; 54 shared objects; zero issues; exact roundtrip | Ordinary source sharing does not depend on adding a NORTON answer. This is a capability probe, not a historical control arm. |
| Native `family_groups` | 13 singleton groups, zero multi-order groups in both variants | Automatic actor grouping misses this event-based group. Explicit three-order preparation remains supported; a routing/discovery improvement is possible but unmeasured. |
| Separate methodological reviewer | Agrees that no incremental substantive investigation is established against the competent shared assignment | Method review only; no independent factual or lifecycle approval. Same model family, separate context. |

`EVIDENCE.json` retains the exact question/application identifiers, source-sharing matches, prior claim gap and rationale, native results and 95 input SHA-256 pins. The separate [methodological review](method-review/INDEPENDENT_BASELINE_REVIEW.md) includes its own focused observations, source-code line references, input pins, scope and elapsed interval.

Documentation alone cannot establish actual researcher behavior. We found neither a measured repeated NCSSR investigation nor a measured once-only NCSSR production run. The ordinary workflow permits and supports a single investigation; its original and actor-source contexts visibly connect these orders. The experiment therefore lacks a defensible incremental research operation to remove. Four applications cannot be converted into a three-investigation saving.

NORTON could still help discover connections between independent assignments, reconcile an answered question, or enforce exact factual identity and review pins. Those mechanisms would require their own concrete failure/repetition evidence. The present registry counts do not establish their costs or campaign reach. PR60's competent comparison concerns other orders; it corroborates retained analysis as actual possible behavior, not an NCSSR baseline.

## Cost and outcome

The root preflight marker spans 343.568 elapsed seconds. The separate review marker spans 178.461 seconds, partly concurrent with root. These are worker elapsed spans including tool waits, not active labor or model bills. Shared work is charged once across the three downstream orders using the existing NEYMAN effort reader; `EFFORT.json` and `EFFORT_SUMMARY.json` retain integration markers and missingness. Initial setup before the first marker, final publication, reviewer final verification and complete session usage remain outside measured intervals. Root's canceled broad blob-size inventory is retained as a failed setup action in `FAILURES.json`; it is not credited as research or savings.

No NORTON production-attempt or native completion receipt is manufactured for this methodological screen. The NEYMAN effort function reads its actual shared effort events directly; no three-order legal-production run is implied.

| Outcome | Result |
| --- | --- |
| Additional substantive investigations demonstrably removed | 0 established; actual arm counts unmeasured |
| Full cost experiment | Not run: first gate failed |
| New factual answers/applications, claims, complete histories or ready dossiers | 0 |
| New primary-source acquisitions or source requests | 0 |
| Measured net hours/tokens saved | Unknown; no saving claimed |
| Campaign beneficiary population or break-even estimate | Not established |
| Runtime, authority, claim, source-grade, reservation, hold, census, codebook or Junto ledger changes | None |

The existing unresolved source question remains available to its research owner. This run does not declare it exhausted, reject its prior claim, approve a date, transfer ownership, or change its legal status. A later acceleration proposal must identify work that the competent existing route actually still performs and explain which operation would disappear before another implementation or paired research investment.

## Bounded reproduction

Use this branch and materialize the three dossier files plus the 17 text paths pinned in `EVIDENCE.json`. This check calls ordinary functions directly; it is not a full `prepare` run and supplies no new scientific result. It performs no network acquisition or scientific-output writes.

```python
import copy, json, sys
from pathlib import Path
sys.path.insert(0, 'jobs/claim-kit')
import batch

repo = Path('.').resolve()
original = {f'EO:{n}': json.loads(
    (repo / f'jobs/claim-kit/output/dossiers/EO_{n}.json').read_bytes())
    for n in ('12335', '12397', '12402')}
for omit_norton in (False, True):
    dossiers = copy.deepcopy(original)
    if omit_norton:
        for dossier in dossiers.values():
            for key in ('factual_obligations', 'factual_event_ids'):
                dossier.pop(key, None)
            dossier['fingerprint'] = batch.canonical_sha(dossier)
    packet = batch.encode(dossiers, repo)
    assert batch.decode(packet) == dossiers
    assert not packet['codec_issues']
    groups = batch.family_groups(dossiers)
    print(omit_norton, len(packet['text_blocks']), len(packet['sources']),
          len(packet['shared_objects']), len(groups),
          sum(group['orders'] > 1 for group in groups))
```

Expected lines: `False 19 17 62 13 0` and `True 19 17 54 13 0`. Recheck every pinned input before interpreting a later replay; changed corpus or policy inputs require a new assessment.

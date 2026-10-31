# Independent R4 engineering review

Reviewed 2026-10-31 UTC in a separate inherited OpenAI GPT-6-family context. Exact model subvariant, token/cache usage, cash and complete active-labor/session timing are not exposed. This is an engineering review only, with no source, legal, human-review, readiness or savings approval.

## Verdict

No blocking engineering finding in the reviewed change. The native optional handoff is one-way after scientific completion, retains explicit supplied-history scope, appends the exact current receipt without rewriting the supplied history, and preserves the existing import/diagnosis rules. Implementation files were not edited by this reviewer.

Baseline: `88cef0253ed735b2a6e612770f25f9148641ce93` (both local HEAD and origin/main reference). Compared only the requested original blobs with `git show`; no broad diff was used. A preliminary `git status` attempted to materialize an unrelated missing promisor object and failed with HTTP 503. Accordingly this review asserts the pinned baseline and exact local bytes below, not a new live remote-main verification.

## Contract checks

- `jobs/claim-kit/kit.py:136` and `:159`: explicit optional flags reach `complete`; no flags leaves diagnosis disabled. Scientific CLI exit status still depends on scientific exceptions.
- `jobs/claim-kit/completion.py:626` and `:830`: handoff executes after scientific receipt/publication writes and publication-lock release. Diagnostic refusal, missing adapter and timeout produce a separate result/receipt. `TALLY.json` is not rewritten to add diagnostics. Neither successful nor refused diagnostics reselect claims, change checker/tracker results or acquire review authority.
- `jobs/neyman/after_completion.py:27`: only the explicitly supplied pinned history is read; there is no repository-wide inferred attempt scan. `:33` appends current `TALLY.json`, while `:68` preserves the supplied index and writes a new combined index. Duplicate receipt bytes remain aliases of one invocation in the unchanged importer.
- `jobs/neyman/after_completion.py:38` and `:58`: every observed member must have an explicit selected final result or research-attempt receipt. Missing unfinished members refuse diagnosis. Final selection must occur in pinned history; exact claim bytes, scoped source-review flag and isolated replay are checked by the existing importer. Partials and unfinished results retain their original distinctions.
- `jobs/neyman/after_completion.py:61` and `:82`: effort/checkpoint/question references are forwarded to unchanged consumers. Existing effort logic deduplicates shared event/usage IDs and unions overlapping per-worker intervals. Unknown total labor, complete-session cost and savings remain null; no complete-history/population claim is made.
- `jobs/neyman/after_completion.py:19`: diagnostic destinations must be fresh repository-relative descendants of the diagnostic root; existing destinations, absolute paths and repository escapes refuse. `completion.py:650` has a 60-second subprocess timeout. These failures remain diagnostic failures after successful scientific publication.
- Diagnostic output has no producer claim/reviewer schema and does not duplicate claim bytes. A separate probe froze an independent packet after scientific completion but before diagnosis, ran successful diagnosis, and then successfully verified both original and independent packets. Prior-research context and independent packet bytes remained equal. A genuinely relevant review changes context in the supplied positive-control regression.

## Independent execution

| Execution | Result | Observed timing |
| --- | --- | --- |
| `cd jobs/claim-kit && python3 -m unittest -v test_completion_diagnosis test_completion` | 45 tests passed | unittest 3.674 s; subprocess envelope 3.771087 s; started 2026-10-31T04:21:44.139559Z |
| `cd jobs/neyman && python3 -m unittest -v test_after_completion test_production_receipts test_survey` | 53 tests run, 51 passed, 2 existing metadata-dependent skips | unittest 0.316 s |
| Seven independent publication/refusal probes plus packet-isolation probe | All 8 passed | script monotonic interval 0.730464 s |

The seven refusal probes used the actual completion fixture with `publish=True`: missing history, escaping output, absolute output, invalid question, invalid checkpoint, missing adapter, and an injected diagnostic-only subprocess timeout. Each preserved exact producer bytes in the published claim file, `claims_published=1`, scientific `exceptions=0`, an unchanged scientific-only tally schema, and diagnostic `status=refused`. The eighth probe independently checked self-input and frozen-other-packet stability after a successful handoff. These are synthetic engineering probes; checker/tracker fixture substitutions do not establish production scientific validity.

Two command mistakes are retained as execution limits: the initial NEYMAN command also named nonexistent `test_diagnose` (loader error), then was corrected to the existing `test_survey` suite above. The first timeout-probe draft mocked all subprocess calls and accidentally timed out preexisting publication-lock Git discovery; it was corrected to inject timeout only for the diagnostic adapter. No implementation change was needed or made for either error. Two path-reading commands initially used repository-relative names while already in the NEYMAN directory; the reads were repeated from the repository root.

The two skipped tests require retained PR60 research metadata / actual repository outputs not present for the fixture suite. Parent/coordinator owns retained-production data and concrete production examples. No fresh source acquisition, canonical output regeneration or production savings measurement was performed in this review. Full review wall time was not prospectively captured; test and probe times above are machine intervals, not model labor or additive session cost.

## Exact tested SHA-256

| File | SHA-256 |
| --- | --- |
| `jobs/claim-kit/kit.py` | `9f995aad2c6d79766a309d128e5cecc542e5ae4929b710e31b2e3eb136fb4a9a` |
| `jobs/claim-kit/completion.py` | `972b4f5eb756d2ee597f0fe8f0cf9b5037827b5409a525f0dcd9ae85a618c0f6` |
| `jobs/neyman/after_completion.py` | `a158ecc677db31506df49f2d28b18b04ed6f658a09bdf0930064679d90457554` |
| `jobs/claim-kit/test_completion_diagnosis.py` | `92e3c4e1e33dbe496d565961ded4dc7a5a85b9a8720eda9ac03c6b473abf4b6e` |
| `jobs/neyman/test_after_completion.py` | `6124c0e4250cfc11fff46bd8502eeeb569eb7d5ce5d6a513e7fe1993b0c482ca` |
| `jobs/neyman/production_receipts.py` | `b43f5bfffee891afbb8ecd7b1c32a875f33a348b0f28c0b65911ae57f145f0c6` |
| `jobs/neyman/diagnose.py` | `aba82132ad518a3e69a7dceda83d932628b7ef114a470b1de3cf95c72adb96ca` |
| `jobs/claim-kit/prior_research.py` | `971946c180a91015c46904c030ad513e76d81671a6dc9cb49d0788cab3a7cc14` |

Final implementation hash read: 2026-10-31T04:23:12.082807Z. Any later source change requires exact recheck. Only this report is owned/written by this reviewer; coordinator should integrate the review result into its Kean/HANDOFF records under the existing disjoint-file assignment. No new owner question.

## Final bounded-history recheck — 2026-10-31T04:25:54.310342Z

The only implementation change since the review above is the new `after_completion.py:36` requirement that the combined supplied/current reference list has at most 200 entries. This correctly applies the existing ceiling after appending current, before receipt parsing or output creation. No new finding.

Three independent boundary probes passed in 0.139660 s: 199 supplied references plus current succeeds (one unique invocation / 199 aliases); 200 supplied plus current refuses before creating the output directory; 200 supplied without current succeeds (one unique invocation / 199 aliases). `python3 -m unittest test_after_completion` then passed all 13 tests in 0.059 s (subprocess envelope 0.126258 s). These are additional executions, not additional distinct test methods.

Final adapter SHA-256 is **`c8cce77a1cdf6b886fb8322d1d5533309465830372af826578aaeeb489b4236f`**, superseding its earlier row. Re-read hashes for `kit.py`, `completion.py`, `test_completion_diagnosis.py` and `test_after_completion.py` still exactly match the table above. Engineering verdict remains unchanged. The coordinator's retained production replay has a missing-DESIGN scientific exception; the NMB replay is validation only. This engineering review establishes no source-ready new scientific continuation, new successful scientific completion or scientific approval. Model/usage and labor limitations above remain applicable.

# Safe diagnostic of the long-running repair workflow

The original run [39490062770](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39490062770)
completed without cancellation on `codex/repair-integration-20261020`, at code commit
`ec13121674cec5b92d910fe18dd361415e072ee4`. The complete logs show claim-drafts finished after 52 minutes, followed by the remaining jobs. Of 27 jobs, 25 succeeded, portfolio validation failed, and daily-digest was blocked by that failure. The publication step succeeded at output commit `1ebe65b501a886ba959c6c38d214da0cc1e3e9e2`; successful generations and failed attempt receipts are preserved. It was slow and later encountered a validation failure, rather than being permanently stuck in claim drafting. See `PRIMARY_RUN_RESULT.json`.

Independent diagnostic runs use initial committed inputs from that exact code
commit, read-only repository permissions, temporary output outside the checkout,
and separate time limits. They neither cancel the primary run nor publish any
canonical research generation. They cannot reproduce the primary runner's
unpublished outputs from preceding producers.

| Probe | Observation | Limit |
| --- | --- | --- |
| 39498626362 | First two drafts completed in approximately 7.5 seconds. | Neither case made a network request. |
| 39499817449 | All 3,359 drafts completed in 90.519 seconds, about 1.1 GiB maximum RSS; CPU continued advancing. | New downloads disabled; mechanical draft outcomes are not accepted legal findings. |
| 39499817449 | Exact original-representation downloads for EO 13792 and EO 13148 returned HTTP 200 and matched their declared hashes; total 1.309 seconds. | Other URLs or the regenerated primary-run inputs may behave differently. |
| 39501126791 | Full online replay launched with the production 400-request budget, per-request timings, 15-second heartbeats, 45-second stack samples and an eight-minute cap. | The diagnostic copy segfaulted while extracting PDF text after 442 cases; see V3. No such crash occurred in the original run. |

`ISOLATED_STALL_PROBE_V1.json` and `ISOLATED_STALL_PROBE_V2.json` retain measured
summaries. Diagnostic source and workflow are on `codex/stall-probe-20261020`.

The unchanged download verifier permits 120 seconds per request and caches only
successful byte matches. Repeated unsuccessful references are a plausible slow
path, but these observations have not demonstrated that this is the original
run's cause. Do not describe a suspected cause as established.

The transactional runner preserves the preceding published generations and
normal failed-attempt receipts. It has no mid-job remote checkpoint for an
unfinished live generation. Cancelling or timing out the original Actions job
could lose that unpublished work; do not promise otherwise. No cancellation,
restart or repair-branch update was made for this investigation.

`PENDING_FOLLOWUP.patch` checkpoints the eight prepared Valla/configuration/digest
files against ec131216. Three Valla code files are already reviewed in PR #47.
Apply remaining changes only after the primary run's publication, based on the
fresh output commit, and preserve PR #47 as an ancestor. The patch does not
publish itself and excludes generated-output deletions from the local checkout.
The reports in this checkpoint still mark final pipeline validation and merges
pending; none of these diagnostic observations authorizes research claims.

The online diagnostic showed approximately 178 seconds in one GovInfo PDF body read before advancing. Its later segmentation fault remains unproven as a reproducible parser defect; signal-based stack instrumentation was an extra variable. Control replay 39502729089 used Python stack sampling instead and completed all first 500 online cases in 104.964 seconds, including EO 10681 and the same 48-page PDF extraction. The segmentation fault did not reproduce; no production parser defect is established. Probe 39502062499 rebuilt all four deterministic producers and completed all 3,359 cases without new downloads in 183.093 seconds. These runs publish no canonical outputs.

The eight-file checkpoint was applied in cad6e402 and validated in successful followup run 39503891853 (output e643172c). It is a historical recovery checkpoint, not an unapplied change. A later PR #40 head introduced 20 additional commits; its integration is tracked separately in LATE_PRODUCTION_RECONCILIATION.json.

# Safe diagnostic of the long-running repair workflow

The original run [39490062770](https://github.com/D3m0sthene5/Executive-Orders/actions/runs/39490062770)
remains untouched on `codex/repair-integration-20261020`, at code commit
`ec13121674cec5b92d910fe18dd361415e072ee4`. GitHub still reports the Run the jobs
step in progress. Its last observed inner stage was claim-drafts. This is not
proof of a hang: the original process does not emit a regular heartbeat, and its
unpublished filesystem, CPU counters and live Python stack cannot be inspected
through the available workflow API.

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
| 39501126791 | Full online replay launched with the production 400-request budget, per-request timings, 15-second heartbeats, 45-second stack samples and an eight-minute cap. | Pending at this checkpoint; its timeout affects only the diagnostic replay. |

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

# Thompson, 2026-11-12: the claim-kit citation-list regex

Named for Ken Thompson, whose 1968 regular-expression construction matches without backtracking. Repair PR #302;
Kean F-20261112-claimkit-regex-runaway.

## What happened

- **The hang:** claim-kit's build (run 43220124126) located every provision pair, then ran 4 h 20 min at full CPU
  with no output, until the runner's 350-minute wall. No build had published since 2026-11-10 10:36 UTC, so the
  merged Accursius fixes F3-F7 never reached the compiled output.
- **Cause:** in `build.py`, the pattern `_PRECEDES` backtracked exponentially on spaced-digit runs.
  - 8 digits took 0.005 s, 12 took 0.26 s and 14 took 2.4 s.
  - The old code hangs inside one call on 4 Federal Register texts and on 122 census-actor pairs.

## The checks (every input real; generated pickles are not committed)

| Script | What it does | Result |
|---|---|---|
| `prof.py` | Times the non-census acting-text loop | Old code: stuck in one call for more than 15 minutes. Fixed code: 7,217 pairs in 11 s. |
| `dump_pairs.py`, `dump_census.py` | Dump the real pairs and texts as the build selects them | 7,217 non-census pairs; 15,326 census pairs |
| `compare*.py`, `diff*.py` | Old code (killed after 20 s per call) against the rejected separator-requiring version | The rejected version lost 18 real citation spans on 15 orders |
| `v2check.py` | The final fix against the old code | Identical on all 22,413 pairs the old code finishes. Slowest call 0.04 s. |
| `oracle.py` | The old pattern translated to GNU `grep -E` (no backtracking) | Agrees with the old Python engine on 4,365 of 4,365 validation windows, and with the fix on 242 of 242 windows from the 130 unfinishable pairs |

## Fresh build on the repair branch

Run 43287422922:
- claim-kit succeeded in 32 minutes;
- larrey-triage succeeded and read the new claim-kit summary (sha256 `1873a582…`).

Avoided time per rebuild: the build now finishes in about 32 minutes instead of running into the 6-hour wall. That
is runner time, not a measured saving in the cost of a completed dossier.

The pilot evaluated **50 orders** and has **10 accepted frozen candidates**. They are not counted here as committed claims; root final checks still govern commitment. Initial independent AI review accepted 9 and rejected 1 (**10%**); corrected EO:13028 subsequently passed a separate rereview.

| Recorded phase | functions.exec | Nested commands, separate | Collaboration, separate |
|---|---:|---:|---:|
| Initial 50-evaluation recorded floor | 204 | 223 | 37 |
| Known categorized producer freeze increments | 19 | 19 | 2 |
| Frozen reviewer increments, six batches | 44 | 44 | 6 |
| Producer11948 cumulative across both phases, added once | 12 | 14 | 4 |
| All-phase recorded floor | **279** | **300** | **49** |

The floor is **27.9 function calls per frozen candidate**, or **5.58 per evaluated order**. Nested commands are never added to their wrappers. Producer11948's cumulative counter spans both phases and was absent from the initial 204 floor. Producer13385's ambiguous incremental9/cumulative23 totals are excluded from categorized totals. Other unrecorded collaboration/correction calls and root orchestration remain missing, not zero. Family review counters repeated in two candidate rows count once.

The full machine cold run took **280.517 seconds**. Full pilot elapsed wall time is unavailable; partial task clocks, shell execution durations and parallel task intervals cannot establish it. Model new-input, cached/reread, output and total-token metrics remain unavailable.

The target of **50 committed claims with a substantial cost reduction was not met**. The baseline was approximately 8 calls, 33,000 new input tokens and 2.1 million cached/reread input tokens per accepted claim, with 10.7% rejection (about11%). This snapshot evidences ten frozen AI acceptances and incomplete cost counters; neither a like-for-like efficiency improvement nor token savings is established.

`FINAL_TELEMETRY.json` separates the two phases, enumerates available and missing counters, reconciles changed initial evidence paths, and pins current source-file bytes. Historical old hashes are not presented as current-file verification.

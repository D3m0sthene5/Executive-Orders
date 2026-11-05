# Windows source-read stability: final diagnosis and acceptance

The failed full Windows jobs were not resolved by the earlier access-time correction. A temporary instrumented, read-only Windows workflow retained the original rejection and recorded 44 failures. Every failure had stable descriptor metadata and exact byte length; all eight common identity fields agreed between the descriptor and pathname. Only cross-API ctime differed. Raw JSONL preserves the original 64-bit integers.

CPython 3.12 Windows pathname stat reports creation time in st_ctime while descriptor fstat reports change time on this runner. Primary implementation references:
- https://github.com/python/cpython/blob/v3.12.7/Modules/posixmodule.c#L2135
- https://github.com/python/cpython/blob/v3.12.7/Python/fileutils.c#L1117
- https://github.com/python/cpython/issues/157671

The final reader retains the file descriptor through final pathname revalidation. All nine metadata fields, including ctime, must remain stable within each observation API; eight shared identity fields bind pathname and descriptor observations. Atime is excluded. Source confinement, no-follow behavior, regular-file requirement, exact byte/hash/span checks are unchanged. No source-validation retry or failure suppression was introduced.

Actual Windows full-suite acceptance: https://github.com/D3m0sthene5/Executive-Orders/actions/runs/41952239653/job/126998662848 at 1335e6ff0231b1b1c47326b64d148ab88153ceb7. 657 tests passed, six explicit skips, including all 29 blind-verification tests and 27 descriptor-field mutations plus nine final-path mutations. Independent exact-blob review is adjacent. This targeted acceptance does not substitute for final integration-head Road and Valla checks.

Source SHA256 from Windows checkout:
- blind_verify.py a431646cd94da3b511dff9c00b871e6f2b03da94c104bdb110846301e87e86c1
- test_blind_verify.py a794076d92805bf3222619a25caff0740c1a456a8b53bf58535b325b6b1cd38e

Earlier NORTON_WINDOWS_FIX and SOURCE_READ_STABILITY_FIX reports document intermediate hypotheses and independent semantic improvements; this report supersedes their Windows root-cause inference. No claim, source seal, legal conclusion or readiness count is changed by this patch.

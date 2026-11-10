# Recovery record for deleted WIP.patch

**Reconstruction, not the original file.** The original `WIP.patch` was removed with `Remove-Item` after the final P4 patch was written. It was an untracked 17,233-byte `git diff` of the first seven edited runtime files. Its exact bytes are not available from Git, and this record does not claim to reproduce them.

The parked patch captured the first P4 implementation before the later regression tests and conflict/completeness refinements. It covered:

- `jobs/readiness-tracker/tracker.py` and `test_tracker.py`: Photius-only checked-replica route, exact grade and false-original flags, `check.final=pass`, and pass/fail/unsure/forged-producer tests.
- `jobs/claim-kit/working_text.py`: exact Photius declaration check, checked-replica reference match and informational claim flag.
- `jobs/claim-kit/fragment_cache.py`: cache field for the checked-replica marker.
- `jobs/claim-kit/inputs.py`: registered checked-replica grade lookup.
- `jobs/claim-kit/build.py`: checked-replica text ranking and disclosure text.
- `jobs/claim-kit/assemble.py`: narrow checked-replica original path and claim flag.

The later, complete code state is preserved separately in `P4.patch` with its SHA-256 in `RESULT.json`. That final patch supersedes the WIP design but does not restore the WIP bytes. No frozen runtime code was changed during this recovery.

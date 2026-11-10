# P4 focused test log

Run in `C:\Users\danie\eo-wt\mommsen-4` with `C:\Users\danie\AppData\Local\Programs\Python\Python312\python.exe -I` on 2026-11-10. No production claim was filed.

| Command suffix | Result |
| --- | --- |
| `-m unittest discover -s jobs/readiness-tracker -p test_tracker.py` | 62 passed, 11.058 s; existing unclosed-file ResourceWarnings |
| `-m unittest discover -s jobs/claim-kit -p test_assemble.py` | 54 passed, 2.519 s, including exact pass, false original, ending-source flag, fail, unsure, explicit incompleteness, outstanding page debt, conflicting same-version declarations and forged provenance |
| `-m unittest discover -s jobs/claim-kit -p test_lachmann_reuse.py` | 8 passed, 0.467 s; asserts exact historic non-Photius `prior_confirmation.fragments` object shape through direct and cached indexes, plus existing policy stability |
| `-m unittest discover -s jobs/claim-kit -p test_inputs.py` | 30 passed, 1.185 s |
| `-m unittest discover -s jobs/claim-kit -p test_build.py` | 18 passed, 2.942 s |
| `-c "import sys,unittest;sys.path.insert(0,'jobs/claim-kit');import test_working_text_index;unittest.main(module=test_working_text_index,argv=['x','IndexCacheTests'])"` | 16 passed, 1.403 s, including pass versus unsure cache parity |
| `-c "import sys,unittest;sys.path.insert(0,'jobs/claim-checker');import test_checker;unittest.main(module=test_checker,argv=['x','CheckerTests.test_checked_replica_passes_existing_checker_without_original_upgrade'])"` | 1 passed, 0.141 s; source, quote, structural and working-text checks run |
| `git diff --check -- jobs/readiness-tracker jobs/claim-kit jobs/claim-checker/test_checker.py` | passed |

Broader attempts: all 24 `test_working_text_index.py` tests produced 2 Windows symlink privilege errors (`WinError 1314`), with 19 passes and 3 skips. Full `test_checker.py` ran 42 tests with 4 failures and 3 errors. Three errors are existing fixture writes through cp1252 that cannot encode U+FB01 on this Windows host. Four working-text fixture failures show text-hash and quote mismatches from Windows text encoding/newline translation, unrelated to the checked-replica branch; the new P4 checker test passed separately. Raw suite output: `CHECKER_FULL_WINDOWS.log`.

Read-only real-data probe: `working_text.Index` recognized 2,544 checked-replica declarations from the pinned Photius fragment file; first parsed row is EO:4. This is provenance recognition, not readiness or claim certification.

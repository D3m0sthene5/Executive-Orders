# H10 result freshness traversal

## Change

`result_freshness.py` now derives conservative literal Git pathspec prefixes from each declared root and pattern. It batches scoped `ls-tree` and `ls-files` requests, then applies the existing `select()`/`fnmatch` filter as the authority. A partial filename prefix such as `HANDOFF/notes-*.md` is widened only to `HANDOFF`; `*` still has the existing cross-directory fnmatch behavior. `tracked_entries(ref, declared)` exposes exact tracked `path -> mode:oid` metadata, and `tracked_paths()` exposes its path list for sparse materialization consumers.

Manifest schema and public CLI are unchanged. Working-tree detection still overlays modified files, removes deleted paths, includes untracked inputs, and rejects stage conflicts. Output concurrency checks and the captured-base rule for a later producer keep their prior logic, with Git tree reads scoped to the union of manifested scopes and named outputs.

## Pinned comparison

`BASELINE_COMPARISON.json` compares full-tree `select(tree(ref), scope)` at baseline `f9c6d806ad059dcad7875ab3708715f20ea386df` with the scoped tree result. All five entry maps and input SHA-256 digests match. Timing is local cached Git metadata I/O in this checkout; it is not a workflow-level runtime or total-savings claim.

| Job shape | Full tree entries | Scoped candidates | Selected inputs | Full tree ms | Scoped ms |
|---|---:|---:|---:|---:|---:|
| `example-hello` direct roots | 97,160 | 47 | 43 | 294.9 | 2.6 |
| `kean` roots + report patterns | 97,160 | 12,306 | 271 | 371.2 | 47.0 |
| `fr-originals` research roots | 97,160 | 13,665 | 7,003 | 273.8 | 25.9 |
| `claim-kit` dynamic jobs/research globs | 97,160 | 94,286 | 85,222 | 524.4 | 436.0 |
| `daily-digest` dynamic jobs/notes globs | 97,160 | 80,592 | 12,444 | 592.8 | 437.3 |

The two broad dynamic declarations remain broad in candidate count. Full-tree Git output was 12.31 MB per read; scoped output ranged from 4.1 KB to 12.02 MB. These are local command output bytes, not remote transfer. No network request or remote bytes were involved. Child Git CPU was measured in the JSON receipt. The captured input files themselves are hashed using existing Git object IDs when unchanged.

The checkout is sparse and omits some declared research inputs. A direct baseline `capture()` therefore stopped at `research/gap-census/census.csv` before code changes. The comparison uses pinned Git tree metadata for baseline/after input maps; it does not claim a full checkout or materialize the missing corpus.

## Checks

- Four focused tests passed after the change: full-tree manifest digest parity; fnmatch patterns crossing directories with partial basenames, `[]`, `?`, and a leading wildcard; modified/deleted/untracked detection; unmerged-stage rejection.
- Five existing acceptance/rejection tests passed in the focused run: manifest capture, same-run predecessor chain acceptance, changed declared input rejection before push, concurrent output advance rejection, and later-producer base snapshot acceptance. The final additional concurrent-advance test began but did not return before its command yield; it is not counted as a pass.
- The parent reports the pinned pre-change suite passed 33 tests in 112.478 seconds. No post-change full-suite result is claimed here.

## Limits and cost

The metadata-prefix comparison is not a live workflow run and does not test network acquisition, a full corpus checkout, or undeclared reads. Broad declarations still require nearly full jobs/research catalog traversal. Current model: `gpt-6-luna`; token and cash telemetry unavailable. Local elapsed time for this worker was not exposed as an authoritative labor measurement.

Coordination correction: after an execution wrapper yielded without showing its session ID, I stopped PID 10133 to avoid duplicate work. The parent later reported its baseline suite had completed and said unidentified PIDs must not be killed; I cannot establish whether PID 10133 was that process. I will use retained execution session IDs only.

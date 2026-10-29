# 2. Restore the three cited ProQuest scan inputs

Stack parent: Cotton repair. Default targets are EO254, EO2171 and EO4354, whose published claims retain byte-verification holds. This is a checker input repair, not substantive review or readiness adoption.

The existing checker already indexes Pinakes FRAGMENTS.data.file. Its sparse checkout omits the scan files. proquest_inputs.py now intersects those exact replica records with hashes actually cited by the three target claims, resolves regular Git blobs at one pinned commit, and writes only absent matching PDF bytes at their recorded repository paths. Existing local files are never overwritten. Both known ProQuest roots are supported. No full-folder checkout, source website acquisition, LFS download or grade change occurs.

Bounds: three identities, three distinct source versions, 8 MB per blob and 24 MB total; input metadata is bounded. Missing metadata, mismatched hashes, symlinks, path escapes, unavailable Git objects, LFS pointers and oversized files remain explicit holds in PROQUEST_MATERIALIZATION.json. The ordinary checker independently rehashes and evaluates the restored sources afterward. Git may fetch a missing repository blob in a partial clone.

Ten local tests pass using temporary real Git repositories, including matching restoration, idempotent reuse, uncited exclusion, wrong bytes/hashes, traversal, symlink, byte limits, absent tracked files, LFS and target-count bounds. Reproduce with `python -m unittest discover -s jobs/claim-checker -p test_proquest_inputs.py`.

The native job runs these tests alongside test_checker and performs materialization immediately before checker.main. No scientific output has been edited and no increase of three ready cases is claimed. Repository-wide source/claim execution must establish the actual result on the PR branch before adoption. Leave unmerged.

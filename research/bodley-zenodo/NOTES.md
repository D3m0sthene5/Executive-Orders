# NOTES: Bodley Zenodo design stream (enc/zenodo)

For the coordinator to record in Kean. Nothing was published; no Zenodo account or deposit was created; no record, status, codebook, census, claim or readiness file was changed. Writes are only under `research/bodley-zenodo/`.

## Findings worth a Kean entry

1. **Universe mismatch on main (measured at e146fa4b):** `jobs/domesday-register/output/REGISTER.csv` has 14,972 rows; the census projection and the readiness tracker have 14,998 (27 admitted orders missing from the register, one renamed id EO:7933a to EO:7933A). `build_release.py` refuses to build until the three agree. The daily register job needs to run after the 2026-11-06 admissions.
2. **`jobs/domesday-register/output/UNNUMBERED_SUMMARY.json` is not on main** though the README and tracker point to it; the release's second denominator is blocked on it.
3. **Filed claims carry verbatim text:** 76.8 MB of 115.8 MB of raw lines in `research/readiness/claims/` is quotation text, including text from ProQuest scans (30 references graded `archival_replica_scan_pending_codebook`) and compilations. A public release needs the quotations replaced by hash and length (done in the drafted build) or an owner/counsel decision (OWNER_DECISIONS D5).
4. **Manifest coverage:** 1,705 of the 1,732 distinct source hashes cited by filed claims appear in the SOURCES.jsonl files merged by the build; 27 do not (list them with `cited_by_a_filed_claim`).
5. **Re-verification recipe tested** on 72 claim references (text sha256 matches, slice equals stored quote in 72 of 72).
6. `CITATION.cff` validation with cffconvert 2.0.0 caught a real error (`type: dataset` is not allowed inside `references`; use `data`). Fixed.

## Measured numbers

Release built offline to a scratch folder (not committed): 26 files, 21.84 MiB, reproducible (two builds give identical hashes apart from `MANIFEST.json`'s timestamp), SHA256SUMS verified. With the three pending items and generated files: 33 files, about 26.9 MiB. Zenodo limits: 100 files, 50 GB.

## Files

`DESIGN.md`, `OWNER_DECISIONS.md`, `.zenodo.json`, `CITATION.cff`, `zenodo_metadata.schema.json` (local schema, not Zenodo's), `validate_metadata.py`, `CONTENTS.csv`, `build_release.py`, `DRYRUN_OUTPUT.txt`.
Validate: `C:/Users/danie/eo-venvs/zen/Scripts/python.exe -I research/bodley-zenodo/validate_metadata.py` (venv has cffconvert, jsonschema, PyYAML).
Dry run: `MSYS_NO_PATHCONV=1 py -I research/bodley-zenodo/build_release.py --repo <worktree> --commit origin/main`.

## Not done

Pending inputs (Pergamon manifest, prior-art crosswalk, unnumbered summary); README, RELEASE_NOTES and licence texts (wait for owner decision D1); a sandbox deposit (owner's account).

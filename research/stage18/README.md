# Stage 18 — primary-page recovery and causal pilot

Read [scientific findings](SCIENTIFIC_FINDINGS.md) first. This is an **additive research layer** over immutable Stage 17 and the separate complete Opus reconciliation. It does not alter the canonical SQLite, legacy labels, working denominator, or human review state.

## Contents

| Artifact | Purpose |
|---|---|
| [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json) | Official source URLs; full-publication and local-excerpt SHA-256/size/page provenance; source-grade caveat |
| [sources/](sources/) | Thirteen Federal Register page excerpts for 14 pilot orders; Washington letterbook copies; St. Clair *American State Papers* excerpt; 1789 Knox pension broadside and 1 Stat. 95 date check; Lincoln secretarial copy; 1866 statute image; official Supreme Court opinion |
| [PRIMARY_SOURCE_CASE_AUDIT.json](data/PRIMARY_SOURCE_CASE_AUDIT.json) | One-to-one source crosswalk for 14 Stage 17 pilot instruments, 13 scoped clauses, 26 event records; two corrected source readings |
| [EO1_CAUSAL_HISTORY.json](data/EO1_CAUSAL_HISTORY.json) | EO 1's creation, rejected end dates, statutory transfer, and surviving consequences |
| [EARLY_SOURCE_CANDIDATES.csv](data/EARLY_SOURCE_CANDIDATES.csv) | Five 1789–90 Lord leads and one 1862 Lincoln candidate, all uncounted |
| [build_source_bundle.py](code/build_source_bundle.py) | Recreate the local excerpts from downloaded official publications and LOC images |
| [build_case_audit.py](code/build_case_audit.py) | Regenerate the Stage 17 to Stage 18 case source crosswalk |
| [verify_stage18.py](code/verify_stage18.py) | Check every published source hash and the structured identity/event invariants |

## Reproduce

From the repository root, gather the exact complete official issues and images at the URLs recorded in `SOURCE_MANIFEST.json`, naming the downloads as in `build_source_bundle.py`. Place the Federal Register files under `INPUT_ROOT/fr_issues/`, the LOC JPGs under `INPUT_ROOT/loc_early/`, and the PDFs at `INPUT_ROOT/American_State_Papers_Indian_Affairs_1.pdf`, `INPUT_ROOT/STATUTE-1-Pg95-3.pdf`, and `INPUT_ROOT/Burke_v_Miltenberger_86US519.pdf`. Then run:

```sh
python research/stage18/code/build_source_bundle.py --input-root INPUT_ROOT
python research/stage18/code/build_case_audit.py
python research/stage18/code/verify_stage18.py
```

`pypdf` and `Pillow` are required. The builder checks EO labels and St. Clair headings at expected pages, then writes source hashes. The verifier checks publication excerpts and locally preserved images; it does **not** establish that a scanned page is an original autograph, that an OCR reading is correct, or that all relevant downstream law has been found. The March 1955 date and 1950 predecessor corrections were also checked against rendered page images. Signed originals, independent legal validation, and all-history census completeness remain open.

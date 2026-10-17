# Full Opus evidence recovery

The code in this directory supports a new reproducible **full-archive** recovery stage. The incomplete Codex session had read enough of the complete Opus archive to identify 844 accepted cases, of which 836 asserted footprint completeness, but had not finished a publicly accessible per-case conversion index.

* `extract_full_opus.py` verifies the complete 207,604,486-byte Opus ZIP SHA-256 and extracts all 844 accepted reviewer records for the Stage 20 compiler.
* `verify_opus_media.py` verifies the 358,846,280-byte original-image companion SHA-256, reconciles the missing 496 PDF/image entries from the Opus manifest, hashes **each** companion member against its manifest, and reports only possible case-shard path associations.
* `.github/workflows/stage20-opus-recovery.yml` retrieves only the two relevant LFS payloads, runs the extractor and media verifier, builds the complete 844-case human workbench, tests the full and original Stage 19 excavators, and commits the evidence products back into `main` on success.

The workflow runs once following the installation commit and can also be started manually from GitHub Actions. It deliberately prevents a mistaken LFS pointer from passing as a full ZIP, stops on any missing or conflicting manifest member, and does **not** change legal determinations. A successfully hashed image still needs legal instrument authentication, exact page identification and human assessment of the clause history.

**Public status convention:** A 844-case conversion index proves prior AI research has been preserved, *not* that 844 full histories have been independently certified. Whole-lifecycle independent human certifications remain zero until review records passing the established claim gate actually exist.

The GitHub workflow depends on Actions being enabled and Git LFS quotas, neither of which can be guaranteed in this chat. If it cannot complete, run the documented scripts on a normal full checkout with `git lfs pull`; the two LFS files and source scripts remain preserved.

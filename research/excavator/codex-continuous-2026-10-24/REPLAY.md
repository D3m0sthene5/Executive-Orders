Run commands from the repository root on PR60's published tree. The historical completion directories are immutable receipts; use a new output directory for any replay. Rechecking mechanically does not constitute renewed independent legal review.

1. Restore the exact compressed consumer snapshots and sparse compiler inputs:

   ```sh
   python research/excavator/codex-continuous-2026-10-24/restore_publication.py
   ```

   `PUBLICATION_STORAGE.json` and `route/compiler-snapshot/MANIFEST.json` pin raw sizes and SHA-256 hashes. The script refuses changed existing files. The compiler snapshot is the actual sparse generation used here, sufficient for these frozen packets; it is not a full corpus refresh or a fresh-selection index.

2. Inspect the selected case's `COMPLETION.v1.json` and final `TALLY.json`, `PUBLICATION.json`, `TRACKER_REPLAY.json`, and source/review receipts. For a new individual mechanical replay, make an explicitly derived manifest retaining the exact input references but naming a fresh proposed publication path that satisfies the same publication-mode rules. The original destination already exists and the command correctly refuses it, even without publication. Then use:

   ```sh
   python jobs/claim-kit/kit.py complete NEW_DERIVED_MANIFEST --write NEW_REPLAY_DIRECTORY
   ```

   Omit `--publish` for replay. Original proposals and own-claim destinations already exist; do not overwrite them. Later source, policy, code or authority changes can correctly invalidate a historical packet. Preserve that exception and reconcile exact differences before a new version and any required renewed review.

3. `run_final_consumers.py` accepts repeated `--completion` arguments naming the seven final completion directories listed in `REPORT.md`, plus a new `--write` directory. It joins only byte-identical successfully filed selections and runs the existing checker and tracker with current authoritative statuses unchanged. It does not file claims, adopt statuses or overwrite canonical consumer outputs.

The competent prechange comparator's four actual PR59 modules are retained in `comparison/prechange-runtime/`. Its historical wrappers reference a sibling `../continuous-prechange` directory. To reproduce that environment, copy those four modules into that sibling directory; keep the historical wrapper and receipt bytes intact. This is an environment reconstruction, not a second baseline investigation. The failed initial import and corrected freeze remain recorded.

The 28 newly acquired raw PDFs are in the standard `jobs/astra-source-retention/output/` tree, with exact custody hashes. Additional case-local cache paths reuse those same Git blobs. Do not substitute the accidental broad-run outputs, custom source indexes, or synthesized empty compiler shards. Private planted candidates and mutation keys intentionally are not repository artifacts; safe seeds, exact reviewer verdicts and semantic adjudications establish their limited audit trail.

Historical completion runs and `final-consumers-v1` used the catalog archived as `source-retention/CONSUMED_SOURCES.before_remote.jsonl`. The successful remote retention run has the same 157 raw-source hashes but 44 metadata records differ (including extraction paths and retrieval timestamps). `SOURCE_CATALOG_RECONCILIATION.json` records every difference. The published standard output keeps the actual remote catalog; `final-consumers-v2` is the combined replay against that version. To reproduce the earlier exact environment, use an isolated checkout and explicitly restore the archived catalog there. Do not silently replace a later live catalog or reinterpret a changed fingerprint as approval.

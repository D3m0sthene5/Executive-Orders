# Restore retained source bytes

Five unchanged raw PDFs are stored as 28 exact parts. Forty-eight ZIP bundles store 698 unique PNG bodies at 719 declared target paths. This packaging accommodates observed 64 MiB transport and 16 MiB request limits; it changes no source text or pixels, source grade, custody contract, or scientific gate.

From the repository root, run:

```bash
python3 research/excavator/machiavelli-modern-undecided-20261105/continuation-20261105/materialize_large_sources.py --repo .
```

The offline materializer verifies every part, bundle, restored PDF and PNG against the recorded SHA-256 and byte size. It refuses conflicting existing bytes and writes atomically. Read the final native source paths only after restoration succeeds. `--skip-images` restores PDFs only and leaves image-dependent checks blocked. No guard is relaxed for absent artifacts.

`ASSET_MATERIALIZATION_REPLAY.transport-v2.json` records exact replay of the current five-PDF/48-bundle representation. Earlier transport manifests/replays are historical; they are not the selected current representation. Failed oversized transfers are preserved in the research record; the discarded intermediate ZIP containers were reproducible copies, not original source bodies.

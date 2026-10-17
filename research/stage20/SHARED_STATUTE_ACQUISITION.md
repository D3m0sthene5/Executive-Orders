# High-fanout statutory source acquisition

The complete Opus reviewer records contain ten repeatedly cited **Statutes at Large** references shared across two or more order dossiers. [The ranked reference queue](output/SHARED_SOURCE_REFERENCE_QUEUE.csv) is a textual co-mention inventory, not a legal relationship graph.

`code/acquire_shared_statutes.py` converts those precise printed page citations into constrained official GovInfo PDF endpoints, attempts to download each one, requires a PDF header and EOF marker, caps response bytes at 18 MB, rejects redirects, preserves untouched successful responses as individual local files, and records SHA-256 and failures. The accompanying GitHub Action has a 20-minute cap and commits both successful files and the retrieval report to the canonical GitHub repository.

Successful bytes establish a reproducible source-response trail, **not** that the referenced statute affected any particular EO, nor when and how a clause stopped operating. The first printed page is only a source location; some statutes continue across multiple pages, contain deferred effective dates, or preserve earlier accrued rights. Do not count an authentic GovInfo PDF as a qualifying whole-lifecycle finding. The original strict claim and independent-human review gates remain in force.

Use `python research/stage20/code/acquire_shared_statutes.py --offline-check` to confirm the archived PDFs still have their recorded sizes and hashes. Repeated runs reuse existing verified file bytes rather than modifying source originals.

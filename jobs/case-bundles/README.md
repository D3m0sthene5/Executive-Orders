# One-fetch order startup packets

Fetch `output/bundles/<first-two-digits-of-zero-padded-number>/EO_<number>.json`.
For example EO 9830 is `output/bundles/09/EO_9830.json`. `output/INDEX.csv` contains
all decided orders, paths, byte lengths and SHA-256 hashes. Every packet is below
30,000 UTF-8 bytes, with LF endings and stable field/order serialization.

Packets include provisional status, readiness and blockers, the claim draft and
gate errors, every fragment with sources, saved-text pointers with up to 1,500
characters each, later events, current-law leads, and conflicts. They are startup
contexts rather than accepted claims. Under the strict 30 KB cap, complete large
texts cannot all fit: overflow sections retain explicit full-record pointers,
line numbers and canonical record hashes, with previews. Nothing is silently
reported as complete. Follow those pointers when reviewing legal evidence.

The daily job writes fresh packets and measured cl100k input-payload comparisons
to `METRICS.json`: equivalent assembled evidence before the compact budget and
emitted packet after it, excluding tool wrappers and model reasoning. Fetch-count
comparisons count distinct required record files plus saved text files.

Tests: `python -m unittest discover -s jobs/case-bundles -v` (no network).

# Bounded diagnosis

At `2c85459cf38b08dc1eea6d7c84a74268fa45c28e`, ordinary apply and batch-check
load and validate packets through `batch.load_packet`. Each source confirmation
and working-text policy check can call `fragment_cache.shared`, which re-globs
and hashes the entire provider inventory and verifies path witnesses. That
rehashing is intentional dependency validation, distinct from the earlier fix
that eliminated repeated index reconstruction. It was not removed here.

Completion's `pin_checker_inputs` builds a source index; `run_checker` then
starts a separate checker process whose Context builds another source index.
The independent process, custody checks, pinning and final packet recheck remain
unchanged. Neither sharing across reviewer contexts nor a new cache was proposed.

The observed opportunity was `sources.load_job_sources`: full JSON dictionaries
survived for the manifest while index entries accumulated. The retained native
comparison records one `load_job_sources` and one `build_index` call in each
ordinary checker process. Read counts stay approximately equal. The resulting
improvement is smaller transient memory, with no repeated-call reduction.

Retained state commit `2bc32c6d4ea87abf969c406dd4049dc3dddcc3c7` has o27's initial
unresolved root sheets, not its final submitted sheets. The initial native apply
correctly assembled nothing. The later demonstration uses the existing exact
filed claims as mechanical inputs through ordinary batch-check and does not
manufacture old producer/reviewer state. No 10–30 minute apply round or complete
reviewed completion was reproduced. The fresh prepare's dispatch cost and actual
checker cost remain separate in the receipts.

Mandatory Kean searches covered memory, runtime, packet friction and fallback;
the tool disclosed roughly 1,290 sparse-excluded historical reports. Relevant
existing packet-friction, Cruden, integration and Tribonian records were read.
The retained source inventory is deliberately partial; missing unrelated corpora
and the Opus text pack remain visible in checker notes. This is not full-corpus
runtime attribution or an eligibility census.

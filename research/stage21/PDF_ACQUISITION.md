# Stage 21: bounded original-PDF acquisition

The Stage 14 official URL reuse has produced 386 literal GovInfo PDF candidate links for provisional executive orders. This fetcher runs up to 40 previously unattempted sources per invocation, with a 12 MB per-document ceiling and a 90 MB per-run ceiling.

Only exact GovInfo HTTPS document links already listed in Stage 14 are allowed. Unexpected redirects, response types, non-PDF bytes, and oversized documents are rejected and recorded, never substituted with guessed mirrors. On success, the untouched PDF is stored in research/stage21/original_sources, with SHA-256 and byte-count custody records. All records, including failed requests, remain visible.

Run python research/stage21/code/acquire_official_pdfs.py --fetch --limit 40, or use the dedicated GitHub Actions workflow. Rerun --check to verify stored source bytes and summary output. Each later run skips already attempted identities, so it can continue through the 386-candidate manifest without repeated downloads.

Successful download does NOT establish that the PDF's pages refer to the EO it was associated with in upstream metadata, the exact operative clause footprint, effective loss of legal operation, residual legal effects or independent human review. It is source custody and acquisition infrastructure only.

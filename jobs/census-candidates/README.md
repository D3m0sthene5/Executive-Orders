# Historic executive-order candidate census: ranger integration

This runnable GitHub job joins Stage 18/22 ranger outputs by **exact LOC item identifier**, and preserves original-page hashes, transcriptions and source provenance. Date-only or similar-title matches NEVER identify a historical instrument. Existing 14,972 census identities are unchanged.

Run via GitHub Actions "Run jobs" with name \`census-candidates\`, or set OUTPUT_DIR and REPO_ROOT and run job.py. The job requires the real prior inputs and fails when any critical source is missing. Outputs:
- ITEM_CANDIDATES.jsonl / ITEM_CANDIDATES.csv — deduplicated LOC item *candidates*, never EO identities.
- UNLINKED_EARLY_REPRESENTATIONS.json — other authoritative historical sources not forced into LOC-ID crosswalks.
- SUMMARY.json / CENSUS_READINESS.md — separate candidate progress track including unverified Lord appearances, with source hashes.

The job cannot admit a new executive order, change any status, or issue human approval. A reviewer must separately authenticate physical content, issuer capacity, duplicates, legal inclusion, and chronology before a candidate can enter the principal census. Original pages are linked to their already preserved repository paths; this job does not refetch or redistribute them.

# Stage 21 mass-review workbench and research batches

**Purpose:** turn the entire 3,359-record provisional inventory into bounded, resumable, verifiable research assignments while sharing source acquisition across overlapping executive-order references. All source co-mentions, cause guesses, and prior AI footprint flags remain *unverified leads*. **No record is automatically promoted to a legal conclusion.**

Inputs are existing committed Stage 20 research outputs: the complete 3,359-case conversion index, 352 shared-source case links, 42 statutory citation case-links (18 downloaded PDF candidates across 14 distinct EOs), and 844 case-specific causal cue priorities. Each input is SHA-256 fingerprinted; identities, status and source-edge relations are checked. A case with multiple shared authorities belongs to exactly one review batch but retains every relevant reference. Batch sizes are capped at **20 cases**.

Outputs under [batches/](batches/), produced by the [builder](code/ofr_batch_forge.py):
- **BATCH_ASSIGNMENTS_3359.csv:** auditable case→batch assignment and linked candidate sources. Exactly one row per case.
- **BATCH_REVIEW_PACKETS.jsonl:** per-batch source custody candidates, case statuses, existing research hints and individual uncompleted legal-verification gates.
- **BATCH_RESEARCH_WORKBENCH.html:** offline, searchable, interactive workbench; enter shared-source research memos once, record *different* clause histories for every case, export all or one batch to JSON, and import later to continue.
- **BLIND_PILOT_QUEUE.csv:** stratified initial assignments for two independent reviewers, including minutes and disagreements. In-progress reviews are not prefilled or represented as completed.
- **BATCH_METRICS.json:** reproducible cohort, lane, and source-availability counts; zero certifications.

From repository root run:

\`\`\`sh
python -m unittest discover -s research/stage21/code -p 'test_batch_forge.py' -v
python research/stage21/code/ofr_batch_forge.py
python research/stage21/code/ofr_batch_forge.py --check
\`\`\`

GitHub Actions [builds and commits the outputs](../../.github/workflows/stage21-batchforge.yml) on change.

## Verifying fast without confusing counts

First, a researcher authenticates original instrument pages and identifies every operative clause, preferably by reusing the same obtained original source across affected orders. Second, inspect shared successor statutes or EOs once per source, record exact text and effective-date provisions, and ask an independent, **case-specific** question: did that source end, narrow, extend or leave untouched this particular operative clause? Third, check alternative earlier ending causes, later amendments, savings and continuing residual authority per case. Fourth, create strict Stage 19 claim records and have a genuinely independent reviewer verify the frozen source citations; only then count it as a complete human-reviewed dossier.

In addition to fully human-certified cases, publish transparent *separate* metrics for source bytes verified, full original clauses reconstructed, mechanically passing claim-gate drafts, independent machine reconstructions, and blind human-sample error rates. We can validate population-level machine accuracy statistically without pretending that a sampled audit certifies every individual case. Calibration requires actual reviewer times and disagreements; do not promise 100 cases/hour until measured.

### Pilot

Have two reviewers independently inspect the initial stratified pilot queue with the same frozen original evidence. Track total minutes, first-ending mistakes, incomplete-clause mistakes, savings omissions, and disagreements *by legal mechanism family*. Only after obtaining measured pass rates should the system schedule batches across more humans or AI agents. Batch exports are **research-only**, lack individual reviewed-claim fingerprints, and never modify the certified ledger.

## Current source-custody acceleration

The builder now also incorporates the frozen Stage 14 official-URL overlay (402 provisional case candidates, 386 PDF links) and the growing bounded Stage 21 PDF-custody manifest. Captured original PDF bytes are prioritized as an early review lane, with individual GitHub source links and byte SHA-256 directly in the case workbench. Future pushes of the source-custody CSV trigger deterministic republishing of batch workbooks. A downloaded document remains **unverified** for EO identity, page, clause completeness and legal effect. Earlier Stage 20 research notes remain accessible across the same 3,359 unique cases.

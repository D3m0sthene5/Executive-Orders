# PR60 production-receipt import

Pinned integration cohort: PR60 at `e21be540396c3c4cd5b5d62abc35f4a4aa9b0534`.
`IMPORT.json` selects actual research metadata; `observed-v2/` is the final reproducible output.
This convenience cohort tests ingestion and diagnosis, not population cost or acceleration.

The tool distinguishes two ready replay cases, six reviewed proposals awaiting status adoption,
and EO10030's unresolved event/application evidence. The source checkpoint is linked to its exact
selected partial claim. Its no-route records do not establish archival exhaustion.
`QUESTION_10030.json` is a new, attributed research recommendation based on that checkpoint;
it neither establishes a new factual event nor changes a claim.

Thirteen completion invocations, including three failures, sum to 451.304060458 machine seconds.
Their occupied wall-time union is 357.881309 seconds. Shared two-order runs count once.
Producer/reviewer effort, full session cost and savings remain unknown. The EO13975 completion
transition has sixteen changed declared dependencies; the tool correctly refuses a single-change
causal conclusion.

Run the command in `jobs/neyman/README.md` with a new output directory. Compare the resulting
`DIAGNOSIS.json` with `observed-v2/DIAGNOSIS.json`. All input and implementation hashes are retained.
The earlier prototype `observed-v1` output is not part of this published integration.

For a new real assignment, preserve the ordinary claim-kit receipts (including unsuccessful
runs). A blocked/censored producer can supply the short `neyman.research-attempt/1` record described
in the job README. Optional phase receipts record observed intervals and measurement methods;
this importer cannot discover task timings that were never recorded. Supply the original NEYMAN
sample manifest for probability-sampled work; unobserved members stay explicit. No new full
production sample or independent legal review was performed to build this read-only adapter.

Validation: 39 passed and one pre-existing corpus-dependent frame test skipped. New tests include
real nine-order metadata, partial-vs-whole separation, shared and overlapping costs, copied receipts,
source/version/identity mismatches, censored attempts, sample nonresponse, repair confounding,
path escapes, missing bytes and protected output refusal. See `VALIDATION.json`.

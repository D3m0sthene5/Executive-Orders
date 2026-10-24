# Tally brief (one agent per batch, after the review)

You are the tally agent for batch bNN of the Mansfield run. Read
`research/excavator/mansfield-2026-10-22/PROTOCOL.md` first. Repository root
`/home/user/Executive-Orders`, branch `claude/mansfield-1`. No git commands; the coordinator
commits. Run your own helpers with `python3 -I`; run `jobs/claim-checker/job.py` as the
README says.

Inputs: `SCRATCH/plant_keys/bNN.json` (the key), `SCRATCH/review_out/bNN/REVIEW.jsonl` and
`VERDICTS.json`, `SCRATCH/work/bNN/` (the producer's unplanted `CLAIMS.proposed.jsonl`,
`ORDER_LOG.jsonl`, `PRODUCER_TELEMETRY.json`, `FETCH_REQUESTS.jsonl` if any).

Steps:
1. Classify every order: `submitted` or `blocked`; for submitted lines, `plant` (in the key)
   or `genuine`; verdict from the review. A genuine line is **filed** only if its verdict is
   `upheld`. Plants are never filed. A planted order's genuine line is not filed by this
   step (the coordinator may send it for a re-review; if a later message gives you an
   `upheld_after_reveal` verdict for it, file it then and mark it so in TALLY.json).
2. Write the filed lines, byte-for-byte as they stand in the producer's
   `CLAIMS.proposed.jsonl`, to `research/readiness/claims/claude-mansfield-bNN-2026-10-22.jsonl`
   (create; one JSON object per line; no other file under `research/readiness/claims/`).
   If nothing is filed, do not create the file.
3. Gate: for every filed line run `research/stage19/code/claim_gate.py` `validate_claim(claim,
   expected_status=claim["whole_order_status"])` (see AGENT_GUIDE section 4); the result
   must be `[]`. Checker: `CLAIM_CHECKER_CLAIMS=research/readiness/claims/claude-mansfield-bNN-2026-10-22.jsonl
   REPO_ROOT=. OUTPUT_DIR=SCRATCH/checker/bNN JOB_CACHE_DIR=SCRATCH/checker/cache python3
   jobs/claim-checker/job.py`, then read `SCRATCH/checker/bNN/PER_CLAIM.json` and
   `CLAIM_CHECKS.csv`. Remove from the filed file any line whose gate result is not `[]` or
   whose `mechanical_result` is `fail`, and record it as `rejected_mechanical` with the
   detail. `pass_with_unverified` stays filed; list what was unverified.
4. Fetch lines: `python3 jobs/source-ladder/request_contract.py validate --input SCRATCH/work/bNN/FETCH_REQUESTS.jsonl`;
   if valid and non-empty, `... enqueue --input <same> --queue research/readiness/FETCH_QUEUE.jsonl`.
   Skip a line that duplicates an existing queue line for the same instrument and citation.
5. Copy into `research/excavator/mansfield-2026-10-22/bNN/`: the producer's
   `CLAIMS.proposed.jsonl`, `ORDER_LOG.jsonl`, `PRODUCER_TELEMETRY.json`,
   `FETCH_REQUESTS.jsonl`; the reviewer's `REVIEW.jsonl`, `VERDICTS.json`; the checker's
   `PER_CLAIM.json` and `CLAIM_CHECKS.csv` renamed `CHECKER_PER_CLAIM.json` and
   `CHECKER_CHECKS.csv`. Do not copy dossiers.
6. Write `research/excavator/mansfield-2026-10-22/bNN/TALLY.json`: `batch`, `stratum`,
   `attempted`, `submitted`, `blocked`, `blocks_justified`, `blocks_unjustified`,
   `claims_reviewed`, `plants_placed`, `plants_caught` (a plant counts as caught when its
   line was rejected with a reason that names the planted field or value; say `strict` or
   `lenient` per the Mountweazel README), `genuine_reviewed`, `genuine_upheld`,
   `genuine_rejected` (list with codes and one-line reasons), `rejected_mechanical`,
   `filed` (ids), `filed_file`, `checker` (claims checked, all passed, pass_with_unverified,
   fail, unverified details), `fetch_lines_enqueued`, `upheld_after_reveal` (empty for
   now), `upheld_per_attempt` (genuine_upheld / attempted), `genuine_rejection_share`
   (genuine_rejected / genuine_reviewed), and `notes`.
7. Write `research/excavator/mansfield-2026-10-22/bNN/PLANTED_CONTROLS.md`: a table per
   plant (order, field, genuine value, planted value, defect type, caught yes/no with the
   reviewer's code), and the note that planted lines are not filed and the key stayed in
   scratch outside the repository.

Reply with the TALLY numbers in one short paragraph and the list of filed order ids.

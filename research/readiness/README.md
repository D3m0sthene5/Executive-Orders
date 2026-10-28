# Readiness: getting orders ready for human review

The [readiness tracker](../../jobs/readiness-tracker/output/TRACKER.md) counts how many
orders the machines have finished: every research step the order needs is done
or recorded as searched to the end, so only human verification remains. It
reruns within minutes of any change to this folder, and daily.

## Standard procedure for research agents (Opus, Astra, Codex, Claude)

The point is economy of scale: machines do the finding, downloading,
transcribing and checking; agents spend tokens only on legal judgment, and on
work that clears many orders at once.

1. **Pick work from the top of the tracker's list.** Open
   `jobs/readiness-tracker/output/SHARED_UNLOCKS.csv` (or the "Do these first" table
   in `TRACKER.md`). Each row is one action that unblocks many orders. Do
   `machine_job` rows by queueing them (step 2), and `agent_check` rows yourself.
2. **Never fetch a source by hand.** Add a line to `FETCH_QUEUE.jsonl` in this
   folder and commit it: `{"instrument_id": "EO:1234", "urls": ["https://..."], "citation": "66 Stat. 259", "step": "original_text", "requested_by": "Astra"}`.
   The source-ladder job runs within minutes and daily, walks every route, and
   records the result in `jobs/source-ladder/output/RESULTS.csv` and `SOURCES.jsonl`
   (url, sha256, retrieval time). Use those records in claims. If you know a
   route it lacks, add that URL to the queue line.
3. **Start every order from its draft.** `jobs/claim-drafts/output/DRAFT_CLAIMS.jsonl`
   has one pre-filled claim per decided order: the original text and clauses
   with sources (from fr-originals, opus-media-match, clause-drafts), candidate
   later events and endings (later-events, current-law), conflicts, and the
   exact gate errors still open. Follow `jobs/claim-drafts/AGENT_GUIDE.md`: fill
   only the judgment fields, check the cited sources, and never copy a
   candidate into a claim without reading its source.
4. **Work in families.** When several orders share a source, a revoking order or
   a legal rule, do them together and cite the same source record. One proven
   rule should cost one analysis plus a short case-specific check per order.
5. **Finish independently reviewed batches with `kit.py complete`.** Follow
   [the batch contract](../../jobs/claim-kit/BATCH.md): pin exact producer lines,
   explicit independent verdicts, semantic control adjudications and required
   after-reveal reviews. The command selects eligible versions, runs existing
   gates/checker/tracker, preserves receipts and prepares the publication. Use
   its explicit publication option only for an authorized own-agent file or
   isolated replacement proposal. Models resolve substantive exceptions; do
   not assign a separate copying/tally/filing agent. Partial research retains
   its exact disclosed completeness gaps and receives no complete-history
   credit. Existing replacement ownership and human review remain unchanged.
6. **Record a step as exhausted only with evidence** (see below), never because a
   site was slow, blocked or rate-limited.
7. **Report telemetry in your HANDOFF note:** orders worked, steps lit, agent
   tokens and wall time per order, so the project can see which methods pay.

Do not hand-edit any `jobs/*/output/` folder (jobs rewrite them), commit drafts
as claims unchanged, or treat any machine output as a legal conclusion.

## claims/

One JSON object per line, in any `*.jsonl` file here. The format is the Stage 19
whole-lifecycle claim (`../stage19/CLAIM_SCHEMA.md`), checked by the project's own
`claim_gate.py`. **Partial claims are welcome**: a step counts once its part
passes the gate **and** claim-checker has passed that step for that exact version
of the claim (an edited claim waits for the next check, shown as
`CLAIM_NOT_YET_CHECKED`). If two lines have the same `instrument_id`, the later
one (by file name, then line) wins, so coordinate in HANDOFF before replacing
another agent's claim.

## FETCH_QUEUE.jsonl

Requests for the source-ladder job (format in step 2 above). Append only; the
job keeps its own results and retries `retry_later` items daily.

## EXHAUSTED.jsonl

When a step cannot be finished by machine, record it so the order can still
reach human review with the gap stated. One line per order and step:

```json
{"instrument_id": "EO:1234", "step": "original_text", "searched": ["govinfo FR 1942 vol. 7", "APP", "Wayback id_ for ..."], "recorded_by": "Astra", "recorded_on": "2026-10-17", "note": "never printed in the Federal Register"}
```

Only two kinds of evidence justify a line:

- a source-ladder result of `exhausted_proposed` (copy its line from
  `jobs/source-ladder/output/EXHAUSTED_PROPOSED.jsonl`; never one whose note says
  `WEAK`, and never a `retry_later` or `no_route` result), or
- a search you documented route by route in `searched`, at least as thorough
  as the source ladder.

`step` is one of: `original_text`, `clause_inventory`, `ending_or_current_basis`,
`savings_residuals`, `counterevidence`, `shared_sources`, `opus_media`. List the
gap in the claim's `unresolved_material_gaps` too.

None of these files changes a provisional status or any count in the research ledger.


The model-neutral dossier and decision-sheet interface is documented in [`jobs/claim-kit/AGENT_PROTOCOL.md`](../../jobs/claim-kit/AGENT_PROTOCOL.md).

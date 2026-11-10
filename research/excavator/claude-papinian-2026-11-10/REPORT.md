# Papinian wave, 2026-11-10: the Opus production lane

Named for Aemilius Papinian, the Roman jurist whose opinions the Law of Citations made decisive when authorities
split. This lane ran beside MOMMSEN I-III (Codex) under one shared prompt; it never touched their orders, branches
or files.

**Result: 63 canonical lifecycle claims filed and merged** (PR #257: 48, PR #261: 15). The local tracker replay
moves ready from **1,179 to 1,237**; the published tracker follows the next sweep. 6 more undecided orders are filed
as isolated replacement proposals awaiting owner adoption. No status, census, codebook, source grade or owner ruling
changed. Human-certified: **0**.

Cost **296.95 USD** at API list price (bentham usage: 297.11): workers 246.09 (Sonnet 85.89, Opus 160.20),
coordinator 50.86 (Opus). 18 planted controls, 0 missed.

## By pool (Bentham rank order)

| Pool | Batches | Attempted | Submitted | Filed | Workers USD | Gate |
|---|---|---:|---:|---:|---:|---|
| recovery.custody_stranded | r01b | 7 | 2 | 2 | 6.26 | PILOT (pool exhausted) |
| recovery.working_text_stale | skipped | 0 | | | | Photius-193 recheck, owned by MOMMSEN-I |
| production.one_step_away: board pilot | not run | 0 | | | | blocked: report PDFs custody-only |
| production.one_step_away: own-claim corrections | c01 | 23 | 7 | 6 | 12.75 | PILOT (production-closable orders exhausted) |
| production.claim_ready.yes.fr | y01-y14 | 347 | 90 | 55 | 180.85 | CONTINUE (0.80); every member worked |
| status_assignment.undecided (EO >= 7532) | u01b, u23 | 90 | 17 | 0 (+6 proposals) | 46.23 | STOP (0.12) after u23 |

(PR #257's table gave y01-y09 as 56 submitted; the producers submitted 64. The filed count, 40, is unchanged.)

## Why things were not run

- **Board rule (D-20261108-board-rule).** 101 of the 173 R3 board orders now have a held NMB report text, but every
  report PDF (191.8 MB) lives only in source-ladder's runner cache, so the checker grades it custody_record_only on
  GitHub and source_supplement cannot cite it. The rule itself blocks custody-only reports. Ask
  A-20261110-papinian-board-bytes; finding F-20261110-papinian-board-custody.
- **working_text_stale.** All 26 are Tribonian claims awaiting the Photius-193 recheck, which the owner assigned to
  MOMMSEN-I (D-20261110-mommsen-i-owner-assignment). F-20261110-papinian-photius-overlap.
- **Other one_step_away orders.** The rest need an Opus-media refetch, sit under a quarantine or open source audit,
  or belong to Justinian or Dorotheus (replacement proposals only).

## Route

1. `kit.py prepare` (reservations in CLAIM_KIT_LOCK.json as agent `papinian`; own-claim corrections as agent
   `claude`, filed as `claude-2026-11-10-papinian-c01.jsonl`, the Cujas precedent), cruden lookups, Geddes views.
2. A Sonnet producer per packet: apply, batch-check with the actual checker, Geddes lint. Where a producer left
   orders undecided, the same producer was resumed to finish them.
3. Two fresh blind Opus arms per batch over separately shuffled review sets with one planted control (every end date,
   or for an all-YES set every later-event date, moved back three years). After-reveal review of the genuine control
   ran only when its sole defect was the plant.
4. `kit.py complete --publish` with the both-uphold rule (`tools/finish_pair.py`; undecided: `tools/overlay_review.py`).
5. Before each PR: the actual checker on this lane's claims only (D-20261109-impact-scoped-checks), joined to main's
   PER_CLAIM, then the tracker, with outputs outside the repository.

## Deviations and defects met

- `claude -p` reports "Not logged in" on this PC, so `jobs/carnot-coordinator/worker.py` could not run; workers were
  Agent-tool subagents with separate contexts. `tools/cost.py` prices each transcript; `WORKERS.json` maps them.
- A sparse-set change after `prepare` changed one packet's Valla context (the scan records unmaterialized packages);
  the packet was re-prepared (r01 kept, r01b used).
- Two completions running at once: one failed with `packet dependencies changed during completion` and passed on a
  serial retry. Completions then ran one at a time.
- The undecided route was refused on the 2026-11-08 claim-kit outputs (`old_compiled_outputs:code_fingerprint`);
  it ran after merging main's 2026-11-10 05:29Z rebuild.
- road-tests had been red on main since #249 (test_mission read an output file the sparse CI checkout lacks). This
  lane's fix #258 was superseded by MOMMSEN's equivalent #253 and closed. GitGuardian flagged a main runner file
  brought into #257 by a merge commit; the branch was rebuilt without it.
- Completion receipts `TRACKER_CLAIMS.jsonl` (about 114 MB each) are stored as lossless `.gz` with a SHA-256 record.

## Biggest unlocks left (acquisition, not production)

- National Emergencies Act continuation notices: about 34+ YES orders blocked only by them
  (F-20261110-papinian-nea-notices).
- An official copy of EO 13286 (68 FR 10619): about 15 YES orders (F-20261110-papinian-eo13286-mirror).
- Report PDF bytes for the board orders (above).
- Owner adoption of the 6 undecided proposals: A-20261110-papinian-adopt-u01b (EO 9674, 11957, 12348) and
  A-20261110-papinian-adopt-u23 (EO 9245, 10679, 11962).

## Files

`BATCHES_*.json` (gate inputs), `DRAW_yes.json`, `DRAW_undecided.json`, `COSTS.log`, `COST_SUMMARY.json`,
`MEASURES.json`, `WORKERS.json`, `telemetry/` (bentham usage), `tools/` (prompts and coordinator scripts). Planted
claims, review sets and control keys stayed outside the repository.

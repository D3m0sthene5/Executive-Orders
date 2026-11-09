# Junto: untested savers, ranked by measured cost at stake

Measured dollars spent in each pattern (cost at stake), from committed Bentham usage. Not a saving; never a Junto score. Only junto.py add-test with two measured arms verifies a saving.

| Saver | Cost at stake | Waves | Test that would settle it |
|---|---:|---|---|
| `lean_coordination`: Main sessions (Bentham's 'coordinator' rows) that do bounded work themselves, poll GitHub, or carry long turns: delegate bounded tasks to cheaper workers, wait with one background watcher, keep turns short. | $693.83 | dorotheus $87.72, gutenberg-2026-11-09 $28.32, justinian $27.67, photius $504.89, haloander-2026-11-07 $45.23 | Unit: filed claim (or completed task). Two comparable waves on the same route (same claim-kit route, same reviewer setup): one run as before, one with the lean-coordination brief. Compare coordinator plus worker dollars per filed claim, and rejects per attempt (quality must not fall). Record with `junto.py add-test`. |
| `revere_phase_handoff`: End a long coordinator context at a phase boundary and continue in a fresh session from the handoff notes (Revere), instead of carrying hundreds of thousands of tokens into every call. | $249.33 | dorotheus $26.72, encyclopedie-2026-11-06 $38.78, gutenberg-2026-11-09 $19.48, justinian $16.00, photius $148.35 | Unit: coordinator call. Same wave phase run twice: once continuing the long session, once handed off to a fresh session at the phase boundary. Compare coordinator dollars per completed batch. Record with `junto.py add-test`. |
| `idle_cache_avoidance`: Do not hold a 1-hour prompt cache across long idle waits; let it lapse or end the turn and resume. | $137.19 | dorotheus $1.78, photius $135.41 | Unit: coordinator hour. Two waits of the same length on the same kind of GitHub run: one holding the session, one ending the turn and resuming. Compare dollars per hour of wait. Record with `junto.py add-test`. |

## Ready two-arm tests (Gutenberg, 2026-11-09)

Each saver below has a tool a wave coordinator uses (`jobs/carnot-coordinator/PROTOCOL.md`) and a test ready to run. No saving is claimed for any of them until its test is measured and recorded.

### `lean_coordination` (C-20261109-1)

- Tool: jobs/carnot-coordinator/PROTOCOL.md sections 1-2 (worker.py, await_run.py)
- Before arm: a wave whose prompt does not include PROTOCOL.md (the Cujas or Haloander shape)
- After arm: the next wave on the same route whose prompt includes PROTOCOL.md
- Matched on: same route (Haloander h01 page check), batch size 25, same producer and reviewer models, planted controls 2 per batch, same budget cap
- Measure: bentham.py usage --wave W --phase P --reported-costs RUN/COSTS.log per arm; units = filed claims; accepted/rejected = blind-review verdicts
- Record: `junto.py add-test --candidate C-20261109-1 --unit-of-work filed_claim --matched-on '<as above>' --before-usd X --before-units N --before-session S --before-accepted A --before-rejected R --after-usd Y --after-units M --after-session T --after-accepted B --after-rejected Q --test-cost-usd 0 --complete-costs`

### `revere_phase_handoff` (C-20261020-1)

- Tool: jobs/carnot-coordinator/handoff.py (context check at 300,000 tokens per call; write packet)
- Before arm: batch k+1 run in the coordinator session that ran batch k (context > 300k per call)
- After arm: batch k+1 run by a fresh coordinator from handoff.py's packet
- Matched on: consecutive batches of one wave, same route and models, same batch size; the fresh arm's setup (reading the packet and checking out inputs) is counted in its cost
- Measure: bentham.py usage with --session-id per arm; units = completed batches (filed or reviewed)
- Record: `junto.py add-test --candidate C-20261020-1 --unit-of-work completed_batch --matched-on '<as above>' --before-usd X --before-units 1 --before-session S --after-usd Y --after-units 1 --after-session T --test-cost-usd 0 --complete-costs`

### `idle_cache_avoidance` (C-20261020-2)

- Tool: jobs/carnot-coordinator/await_run.py (background, ends the turn) and handoff.py for waits over ~55 min
- Before arm: a coordinator that waits on a multi-hour run in its session (checks or a held turn)
- After arm: a coordinator that writes a packet and stops; a fresh session resumes when await_run exits
- Matched on: the same workflow (run-jobs daily selection or a claim-kit rebuild), waits within 20% of each other in length, the same coordinator model
- Measure: dollars from the end of dispatch to the first productive call after the run ends (cache writes and reads of the resume included), per wait hour
- Record: `junto.py add-test --candidate C-20261020-2 --unit-of-work wait_hour --matched-on '<as above>' --before-usd X --before-units H1 --before-session S --after-usd Y --after-units H2 --after-session T --test-cost-usd 0 --complete-costs`


| Wave | Agents | Cost | Main-session share | Large-context main-session calls |
|---|---:|---:|---:|---:|
| dorotheus | 49 | $87.72 | 100% | 182 |
| encyclopedie-2026-11-06 | 19 | $215.46 | 27% | 397 |
| gutenberg-2026-11-09 | 2 | $28.32 | 100% | 269 |
| justinian | 7 | $27.67 | 100% | 241 |
| photius | 289 | $749.24 | 67% | 1518 |
| cujas-2026-11-08 |  | $23.27 | 34% | 0 |
| haloander-2026-11-07 |  | $62.55 | 72% | 0 |

Unpriced models (tokens not counted): ? (3)

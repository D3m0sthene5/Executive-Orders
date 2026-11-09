# Junto: untested savers, ranked by measured cost at stake

Measured dollars spent in each pattern (cost at stake), from committed Bentham usage. Not a saving; never a Junto score. Only junto.py add-test with two measured arms verifies a saving.

| Saver | Cost at stake | Waves | Test that would settle it |
|---|---:|---|---|
| `lean_coordination`: Main sessions (Bentham's 'coordinator' rows) that do bounded work themselves, poll GitHub, or carry long turns: delegate bounded tasks to cheaper workers, wait with one background watcher, keep turns short. | $620.28 | dorotheus $87.72, justinian $27.67, photius $504.89 | Unit: filed claim (or completed task). Two comparable waves on the same route (same claim-kit route, same reviewer setup): one run as before, one with the lean-coordination brief. Compare coordinator plus worker dollars per filed claim, and rejects per attempt (quality must not fall). Record with `junto.py add-test`. |
| `revere_phase_handoff`: End a long coordinator context at a phase boundary and continue in a fresh session from the handoff notes (Revere), instead of carrying hundreds of thousands of tokens into every call. | $229.85 | dorotheus $26.72, encyclopedie-2026-11-06 $38.78, justinian $16.00, photius $148.35 | Unit: coordinator call. Same wave phase run twice: once continuing the long session, once handed off to a fresh session at the phase boundary. Compare coordinator dollars per completed batch. Record with `junto.py add-test`. |
| `idle_cache_avoidance`: Do not hold a 1-hour prompt cache across long idle waits; let it lapse or end the turn and resume. | $137.19 | dorotheus $1.78, photius $135.41 | Unit: coordinator hour. Two waits of the same length on the same kind of GitHub run: one holding the session, one ending the turn and resuming. Compare dollars per hour of wait. Record with `junto.py add-test`. |

| Wave | Agents | Cost | Main-session share | Large-context main-session calls |
|---|---:|---:|---:|---:|
| dorotheus | 49 | $87.72 | 100% | 182 |
| encyclopedie-2026-11-06 | 19 | $215.46 | 27% | 397 |
| justinian | 7 | $27.67 | 100% | 241 |
| photius | 289 | $749.24 | 67% | 1518 |

Unpriced models (tokens not counted): ? (3)

# Effort model for the remaining work

`build_effort.py` gives each open step for each order an estimated number of
AI agent-minutes, from `EFFORT_MODEL.csv`. The tier depends on what the
project's GitHub jobs already hold for that order. Every weight says its basis:

- **measured**: a recorded observation in `HANDOFF/`.
- **calibrated**: split from the one end-to-end measurement the project has.
  In Codex's batch pilot (`research/excavator/2026-10-18/batch-pilot/COST_COMPARISON.json`),
  two arms each ran six complete dossiers from prepared evidence through a
  producer, an independent reviewer and corrections. That took 1,503 s and
  1,584 s, about 4.3 min per attempt, and one of six was upheld in each arm.
  So one finished dossier on a well-tooled modern order costs about 26 agent-minutes
  (about 8.4 M input tokens, mostly cached, and 57 k output tokens per six attempts).
  The tooled tiers CI1 + EB2 + SR2 + CE2 add to 25 minutes.
- **assumed**: a judgment, scaled from the calibrated tiers by how much less the
  tools do. These are the weights to replace first when the instrumented pilot
  that `AUTOMATION_ROI_ESTIMATE_2026-10-17.md` proposes is run.

For the 3,359 orders with a claim draft, the four legal steps (clauses, ending
or current basis, savings, counterevidence) are multiplied by the draft's own
`estimated_effort`: small 0.7, medium 1.0, large 1.4 (assumed).

Orders APP counts that the project does not hold yet take the hardest tier of
every step, plus the admit step.

Agent-minutes are model time with tools, including independent AI review,
excluding human review. Treat the totals as within a factor of two; the
relative sizes are the point of the chart.

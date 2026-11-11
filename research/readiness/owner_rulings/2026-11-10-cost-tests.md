# Owner decisions on the first cost tests (2026-11-10)

The owner (Danny) answered in the coordinating Claude session on 2026-11-10, typing "Yes, yes, yes, no" to these
four questions, which were put to them with the coordinator's recommendations:

1. **D-20261110-smoke-codex-signed: sign the 2-order smoke plan.** The owner signs the Augur plan
   `smoke-codex-2026-11-10` (plan sha256 cb6d88119f5d0a4b318722c7fb6c41918cdd10663fa731ed4eb4c103da346eb4): EO 10057
   and EO 10110 under Bentham action `production.one_step_away`, one lane, through the Maudslay conveyor with Codex
   workers (gpt-6.1-sol, API list prices), chain budget 2,000,000 usage units, filed as replacement proposals only.
2. **D-20261110-nalimov-calibration-signed: sign the Nalimov calibration plan (A-20261110-nalimov-calibration
   part 1).** The owner signs `research/nalimov/calibration/WAVE.json` (plan sha256
   4c19799f9bbcb0cbfc84ee0a7d1303bf2ad79a33851e4679b2389b364d2dde96): EO 10779, 11056, 11232, 11274, 11352, 11361,
   12737 and 13765 under `status_assignment.undecided`, the conveyor with `--producer nalimov`, typed controls and the
   status-overlay stage, budget 600,000 units. Any plan edit needs a new signature.
3. **D-20261110-nalimov-script-producer: accept a script as producer on this route (part 2).** On the Nalimov route
   the producer is a script; its confirmations are mechanical checks. The independent status reviewer and the two
   blind arms are the source review, and Respondendi gives the route its own audit stratum.
4. **D-20261110-no-mechanical-reconfirmation-for-models: decline (part 3).** The conveyor does not give the kit's
   producer reconfirmation mechanically for model producers. It stays limited to the script producer, and only
   where the working dossier equals the base dossier outside the status envelope. The question may be asked again
   once the calibration batch has been measured.

These are run approvals and route rules. They adopt no status and change no count. Human certification stays 0.

## Re-signature of the calibration plan (v3)

Signing the v2 plan exposed two things: Augur required written answers to two Kean lessons merged after the plan was
written (F-20261110-mommsen3-undecided-probe01, F-20261110-mommsen3-codex-core-sandbox), and the plan's reviewers
were Claude models although the run machine has no Claude CLI. The coordinator answered both lessons in the plan and
made the status reader and both blind arms Codex sessions, which changed the plan's hash. The owner then typed
"Yes, sign v3" in the coordinating session (2026-11-10):

5. **D-20261110-nalimov-calibration-v3-signed: sign plan v3.** The owner signs
   `research/nalimov/calibration/WAVE.json` v3, plan sha256
   997f123f47b58335c7b2f2cdd6eb1aaea21c98f930120c0ea7e708b80ec49dce, which replaces the signature in item 2.

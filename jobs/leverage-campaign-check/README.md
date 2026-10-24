# Bounded offline campaign verification

The existing wrapper now executes the actual claim-checker followed by readiness-tracker on one isolated input view, with network acquisition disabled. Their results are retained under output/shared-source/. The earlier full-core outputs remain historical receipts in the output root.

This source-custody repair changes no canonical claims, source versions, legal analysis or population policy. It therefore does not rebuild NORTON, all claim-kit dossiers or Polya. The tracker consumes this execution's actual checker output. All canonical outputs remain unchanged. The unchanged whole-case reviews and exact-version holds remain in force.

Run the existing Run jobs workflow with input leverage-campaign-check, or change only this job's RUN.md. Do not infer execution from an output-only commit. Inspect output/shared-source/VALIDATION.json, COMMAND_RECEIPTS.json, actual checker/tracker outputs and the outer STATUS.json. No legal approval, status adoption or human certification is produced.

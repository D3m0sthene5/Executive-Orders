# Dashboard data snapshot — 2026-10-30 UTC

This directory contains the seven CSV data payloads for the existing Executive Orders Remaining Work dashboard. The refresh is deterministic: it does not change scientific records, tracker gates, status decisions, or certification.

The production checkpoint reports **498 orders ready for human review**: **306 original-supported** and **192 transcription-dependent**, with **612 matching effective-claim receipts** and **0 human-certified orders**. The census denominator is 14,972. Readiness and human certification are separate measures.

The tracker has **75,742 open steps** across current project orders. Remaining-work totals include 1,314 APP-counted orders not yet in the project, adding seven modeled steps each, for **84,940 open steps** overall. The effort model estimates **14,067 agent-hours**; those hours are modeled, not measured. Mission progress is **11.615%**, corresponding to **T+12.707 hours** on the unchanged Apollo 11 clock. Frozen weights and the clock endpoint are preserved.

The Mission log uses official first-parent main history by UTC day. Its Oct 30 checkpoint is the production publication at `35b9a7585d83529cfe7287fb30094273db8cd449` (ready 498), rather than the older local preview of 488 noted in the Oct 29 artifact. The preview is not used as the official history point.

The toolmap was generated using the exact prior dashboard classifier from artifact commit `928962fc44524a7f75a7a279f4484770cb6bdc73`, retaining its Pinakes replica-scan classification and comparable lane counts. Only the pending-policy prose was corrected in the generated CSV: labeled transcriptions may provisionally satisfy the text step, subject to case-level working-text confirmation and page checking. The builder itself and frozen model files remain untouched. The named-tool catalog updates PR103, PR104, PR105, PR106, PR108, PR109, and PR110 from final integration evidence. It records unresolved holds and distinguishes engineering validation, research receipts, and scientific approval.

`MANIFEST.json` records exact payload hashes, byte sizes, row counts, source pins, mission checkpoints, and cost telemetry limits. Elapsed time was not instrumented; tokens and cash are unknown. The catalog and manifest identify the worker model as gpt-6-luna.

The original live-dashboard Mission CSV preview is retained under `history/preview-local-before.csv` with a hash in the manifest. Its 488 preview value is provenance only. It is replaced in the current Mission feed by the 498 first-parent production checkpoint. The toolmap retains the prior classifier so lane counts remain comparable with the Oct 29 snapshot; the current UI's main-branch classifier differs (including transcription leads and Pinakes/no-route handling), so its lane counts are not substituted here.

## Publication verification

All seven CSV feeds were saved in the original artifact and read back after a page reload. Every textarea value matched the corresponding prepared CSV after normalizing CRLF to LF. The Mission view visibly reports **498 complete dossiers, 0 human-certified, 11.62% weighted progress and T+12h42m**. The rocket and existing layout remain intact. The lane query recomputed from the refreshed toolmap.

The artifact still contains older non-editable explanatory prose in its source descriptions and Tool map introduction, including the superseded 488 local preview / pending-recount description and older policy wording. The available controls permit CSV replacement, not source-description or application-code editing. Current CSV records, displayed metrics and the tool catalog supersede those historical sentences. The automatic 21-month pace extrapolation is not a validated completion forecast. Dashboard daily labels remain UTC; the production checkpoint is October 29, 10:18 p.m. in New York.

The [project progress page](../../../README.md) explains all four parallel follow-on sessions, the earlier runner/claim-kit work and final integration in plain English. The current published readiness generation remains `35b9a7585d83529cfe7287fb30094273db8cd449`; this display update does not run new scientific production or change its inputs.

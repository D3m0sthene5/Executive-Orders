# Production flow redesign — November 4, 2026

The owner selected a checkpoint conveyor, led by where orders get stuck, with plain English and click-through detail. Missing costs must be visibly unmeasured. Show actions at each pile and a separate improvement list. Publish only the display; do not interrupt active production.

## Published view

Existing Site, source commit `aac08d6deb6b5eef0c023b2835f7719d0951731f`, saved version 2, deployment `appgdep_6aeaf616ddf08191b70fc2be17f9153a` succeeded. Production URL: https://executive-orders-production-atlas.d3mosth3n3s.chatgpt.site . The Site audience remains owner-only. The EO repository copy is proposed on isolated branch `codex/checkpoint-conveyor-20261104`. The initial public push was blocked by automatic approval review; on November 4 the owner explicitly authorized pushes provided the paused Opus run is protected. Publish this branch with Actions skipped, open a draft PR, and leave main and the protected run unchanged. The separately saved private patch retains the earlier proposal. No research workflow was dispatched and no active checkout, scientific record or native job output was changed.

## Why the earlier view was insufficient

The existing job map, blocker list and tier catalog described capabilities without joining them to the census workload and cost coverage. A job can fetch or package text while legal history remains unfinished. Overlapping blockers cannot be summed into distinct queues. Machine timing, model tokens, cached input and cash also have different scopes. The redesign exposes these distinctions in one view.

## Count contract

Sources: tracker SUMMARY.json, STATUS.json and READINESS_BY_ORDER.csv plus Stage 19 PROGRESS.json, read at main `600ae3018f71025b3e53dc8538b8f92e6e159b76`. The tracker generation finished November 2; checking newer main does not turn that generation into a new scientific result.

Every ready flag goes directly to ready. Otherwise assign the first missing checkpoint in display priority: text; clause inventory; status/ending/residuals; contrary/shared/media; remaining final gates. `done`, `provisional` and `n/a` close the corresponding displayed check. Missing or unknown values stay open. This is a presentation partition, not observed worker assignment or a mandatory sequential workflow. Later checks may be open too.

| Checkpoint | First missing here | Open anywhere (overlapping) |
|---|---:|---:|
| Usable text | 6,228 | 6,228 |
| Command inventory | 7,892 | 14,120 |
| Legal history | 49 | 14,165 |
| Evidence checks | 18 | 12,757 |
| Final gates after listed checks close | 1 | 1 |
| Ready for human review | 784 | 784 |

The first-missing counts sum to 14,972 exactly. The final-gate row is EO 14139 with `unresolved_material_gaps`; it is not assumed to be administrative filing. Separate AI-review, machine-check and filing queue sizes are unavailable. The Stage 19 human-certified total is 0 and has no inferred per-row join. The 67 catalog candidates remain outside the denominator. Text replacement and quotation obligations remain visible in the existing details.

## Cost evidence and omissions

Apollo TELEMETRY.csv: 38 producer/reviewer workers, 496,350,796 cache-read tokens, 13,313,052 cache-creation tokens, 2,407,390 output tokens, 5,466 uncached-input tokens. Coordinator excluded; this is neither total project spend nor dollars. Source: research/excavator/claude-apollo-2026-10-31/TELEMETRY.csv at the main pin above.

Erasmus REPORT.md explicitly did not observe a reduction in per-order cost from slim views. Its one-order producer read 5.2M cached tokens and small fix producers 1.5–2.5M per order; case mix and resubmission prevent causal savings claims. Source: research/excavator/claude-erasmus-2026-11-02/REPORT.md at the same pin.

Historical bounded machine examples are linked to the dated catalog or exact R1 report: claim-kit 214.0→53.5s, Cruden seven-order lookup 71.010→11.569s cold/5.541s warm, Valla warm startup 37.559→11.732s (R1 source 9fc12f9e37780ae5831fce6d698139920bf51589). None establishes model-token or whole-backlog savings.

PR132 and PR133 were open drafts when inspected. The Tribonian branch at `cacfb8f4af6db949476bd7bec8220a464055c931` contained tools but no published report or telemetry CSV. Usage is unreported, never zero. These dated observations are separated from auto-refreshing main counts and the independently refreshed PR listing.

The view lists five missing joins and the decisions each enables: cost by phase/role; repeated evidence reads; work spent before blockers/retries; exact effort-to-readiness linkage; and queue/machine/worker intervals. Reuse Hamilton, NEYMAN, Junto and native receipts. No new collector, dispatcher or scientific approval mechanism is introduced. Complete checkpoint costs, cash and cost per new ready dossier remain unavailable.

## Validation and handoff

Native tally, unique partition, readiness reconciliation, provisional/n/a text, missing-value handling, ready precedence, preserved material gap and qualified blocker deduplication passed. Reproduce with `python3 research/progress/control-center/verify-flow.py`. JavaScript syntax checks pass for app.js, flow-core.js and flow-view.js. Browser preview verified initial render, overlap toggle and final-gate detail. Independent agent reviewed the aggregation and view/event wiring; its Valla citation issue was corrected to the exact R1 source before publication.

Independent read-only audit: approximately 9 minutes for evidence work; review interval and total labor unavailable. Agent model tier and token/cash usage unavailable. Root session tokens/cash/complete labor unavailable. No cost-saving estimate for this redesign.

Keep the production line read-only. The page retains the existing five-minute visible-page refresh and loads native artifacts from one main commit before replacing its generation. Historical costs and improvement hypotheses stay dated; do not relabel them current costs automatically. A future published cost-survey roll-up should replace missing coverage only with validated evidence and explicit denominator/coverage. No change to scientific review obligations follows from a display label.

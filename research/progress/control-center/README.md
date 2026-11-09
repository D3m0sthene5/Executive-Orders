# Executive Orders production control center

[Open the live control center](https://www.dannykind.wiki/eo/dashboard) (public, noindex; relayed from this folder on `main` by DKLA `api/eo-dashboard.js`, so a new file the page loads must also be added to that relay's list) · [older hosted snapshot](https://executive-orders-production-atlas.d3mosth3n3s.chatgpt.site) (owner sign-in) · [Sol production assignment](SOL_SESSION.md) · [Sol observability goals](SOL_OBSERVABILITY.md) · [Canonical tracker](../../../jobs/readiness-tracker/output/TRACKER.md)

Start with **Production flow** for the first-missing-check conveyor, an overlapping-work toggle, checkpoint job/cost detail, recovered campaign/role costs and explicit measurement coverage. See [count and cost contracts](FLOW_REDESIGN.md).

**Mission** (`#mission`) preserves Capcom's Earth-to-Moon flight, rocket, Apollo clock, milestones and checkpoint log. It reads `jobs/daily-digest/output/MISSION.json` and its `MISSION_REFRESH.json` receipt from the checked main commit. The existing frozen effort weights and current census plus the frozen 1,314-order gap define this planning model. Flight distance is effort-weighted completed steps, and the first step represents every modeled order ready for human review. The clock advances when a validated generation changes; it is not elapsed wall time or a completion-date forecast. Human certification comes from the separate published Stage 19 register, with a missing count shown as Unknown.

Mission checks the exact tracker and checker receipts and SHA-256 hashes of the tracker CSV, summary, checker status, census projection, frozen weights and human-review register against the payload. A newer or failed checker and changed census bytes leave the mission pending even when the tracker and older mission still match. Before declaring it current, Mission independently resolves the checked commit's `research` tree and then its `readiness` tree through two small, nonrecursive public GitHub tree requests. That tree must match the consumed `readiness_inputs` witness in both Mission and its ready receipt. A new claim or rule cannot leave an older matching Mission/tracker pair looking current. Unknown tree freshness remains pending, including when the API is unavailable.

A newer tracker, pending refresh receipt, missing source, changed model or failed fetch leaves the last verified flight visible with its generation timestamp and a pending notice. On first load, a source-validated older flight may be retained with that pending label; absent valid sources, the view explains that publication is pending. No readiness counts are inferred from later filings. Immutable source and scoped tree reads are cached by commit/object ID and shared with the other production views; the same research tree is reused across output-only commits. Main checks still run on opening, manual refresh and the existing five-minute visible-page interval.

Run the focused frontend refusal, retention, rendering and cache checks with `node --test research/progress/control-center/mission.test.js`. To produce a self-contained synthetic visual fixture, set `EO_MISSION_PREVIEW=/tmp/eo-mission-preview.html` for that command. The fixture is engineering data, not a current research count. Publishing these assets to the existing Site remains a separate step.

Look up an executive order, inspect its remaining steps, and follow the handoff to the underlying evidence. The map uses the eight Minard stages. The job catalog carries the dated PR #124 tier assessments, including unranked processes. The Next best action view ranks shared blockers by affected orders. Each order may have several blockers.

## Run from a checkout

For MAITLAND's bounded historical provision queries, see the
[reviewed-history protocol](../../../jobs/claim-kit/PROVISION_HISTORY.md) and
[source-reviewed demonstration](../maitland/native/SUMMARY.json). This separate
research mode exposes exact text versions, dated operations and local unresolved
legal-effect questions. It changes no tracker readiness or certification counts.
The hosted dashboard has not been redeployed by this research PR.

From the repository root, run the following command and open [the local center](http://127.0.0.1:8765/). The application uses relative asset paths and needs an HTTP origin.

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory research/progress/control-center
```

Use **Overview → Find an executive order** to inspect a particular record. **Blockers** lists shared failures and dependency declarations. **Next best action** opens the shared recovery queue. The repository copy works with its bundled generation when GitHub is unavailable.

## Source and refresh policy

The bundled tracker generation finished November 2, 2026 and was read at repository commit `600ae3018f71025b3e53dc8538b8f92e6e159b76`. Its order table reuses the exact Git blob of the tracker CSV. The earlier app assets were published as version2 at Site source `aac08d6deb6b5eef0c023b2835f7719d0951731f`; the observability update and exact deployment receipt are recorded in [INTEGRATION.md](../production-observability-20261104/INTEGRATION.md). The job catalog and recovery examples remain dated reference material.

On opening, on manual refresh, and every five minutes while visible, the page checks public GitHub main. When the head changes, it loads the tracker summary, generation receipt, per-order CSV and Stage 19 register from the same commit. It verifies the successful tracker result and reconciles per-order totals before replacing the displayed generation. A failed read leaves the last loaded data and a refresh notice. Pull requests refresh separately. The job tiers, dependency examples and recovery handoffs remain dated reference material.

The records of authority are [the tracker summary](../../../jobs/readiness-tracker/output/SUMMARY.json), [its generation receipt](../../../jobs/readiness-tracker/output/STATUS.json), [per-order readiness](../../../jobs/readiness-tracker/output/READINESS_BY_ORDER.csv), [shared unlocks](../../../jobs/readiness-tracker/output/SHARED_UNLOCKS.csv) and [the Stage 19 human-review register](../../stage19/output/PROGRESS.json). Use these directly in a headless Sol session. A machine-ready dossier can retain original-replacement and quotation-recheck obligations. Stage 19 separately records human certification.

For production triage, read the complete per-order blocker strings. The saved Site's generic advice recognizes some bare codes, while the tracker also emits qualified values such as `OPEN_SOURCE_AUDIT:<hash>` and `CLAIM_CHECK_FAILED:<step>`. Preserve the suffix and inspect the underlying record. For Olney's historical catalog entry, use the [workflow registry](../remaining-work/workflow/WORKFLOW_NODES.json) at the catalog revision if its older source link is unavailable.

## Dated observability snapshots

`observability.json` is generated from exact reviewed recovery outputs by `../production-observability-20261104/build_rollup.py`. It contains58 historical worker rows at two campaign scopes, seven reported role/model rows and five recovered/prospective/unavailable views. These costs do not refresh from main or imply current queue locations. See [measurement contract](OBSERVABILITY_INTEGRATION.md) and [collected evidence and conclusions](../production-observability-20261104/REPORT.md).

Main tracker refresh and optional dated measurement refresh remain independent; invalid or older measurement snapshots preserve the last good generation. Source caches and private transcripts are not deployed.

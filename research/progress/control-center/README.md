# Executive Orders production control center

[Open the hosted control center](https://executive-orders-production-atlas.edgyglove8.chatgpt.site) (owner sign-in) · [Sol production assignment](SOL_SESSION.md) · [Canonical tracker](../../../jobs/readiness-tracker/output/TRACKER.md)

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

The bundled November 2, 2026 generation was read at repository commit `a16ad07f021b2508904c028a7bf48763091c18df`. Its order table reuses the exact Git blob of the tracker CSV. The HTML, JavaScript, styles, illustration and JSON assets match the private Site source version `c7177bfaec26f729c17243bdef46c8487d639214`.

On opening, on manual refresh, and every five minutes while visible, the page checks public GitHub main. When the head changes, it loads the tracker summary, generation receipt, per-order CSV and Stage 19 register from the same commit. It verifies the successful tracker result and reconciles per-order totals before replacing the displayed generation. A failed read leaves the last loaded data and a refresh notice. Pull requests refresh separately. The job tiers, dependency examples and recovery handoffs remain dated reference material.

The records of authority are [the tracker summary](../../../jobs/readiness-tracker/output/SUMMARY.json), [its generation receipt](../../../jobs/readiness-tracker/output/STATUS.json), [per-order readiness](../../../jobs/readiness-tracker/output/READINESS_BY_ORDER.csv), [shared unlocks](../../../jobs/readiness-tracker/output/SHARED_UNLOCKS.csv) and [the Stage 19 human-review register](../../stage19/output/PROGRESS.json). Use these directly in a headless Sol session. A machine-ready dossier can retain original-replacement and quotation-recheck obligations. Stage 19 separately records human certification.

For production triage, read the complete per-order blocker strings. The saved Site's generic advice recognizes some bare codes, while the tracker also emits qualified values such as `OPEN_SOURCE_AUDIT:<hash>` and `CLAIM_CHECK_FAILED:<step>`. Preserve the suffix and inspect the underlying record. For Olney's historical catalog entry, use the [workflow registry](../remaining-work/workflow/WORKFLOW_NODES.json) at the catalog revision if its older source link is unavailable.

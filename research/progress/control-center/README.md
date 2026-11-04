# Executive Orders production control center

[Open the hosted control center](https://executive-orders-production-atlas.d3mosth3n3s.chatgpt.site) (owner sign-in) · [Sol production assignment](SOL_SESSION.md) · [Sol observability goals](SOL_OBSERVABILITY.md) · [Canonical tracker](../../../jobs/readiness-tracker/output/TRACKER.md)

Start with **Production flow** for the first-missing-check conveyor, an overlapping-work toggle, checkpoint job/cost detail, historical token evidence and missing measurements. See [count and cost contracts](FLOW_REDESIGN.md).

Look up an executive order, inspect its remaining steps, and follow the handoff to the underlying evidence. The map uses the eight Minard stages. The job catalog carries the dated PR #124 tier assessments, including unranked processes. The Next best action view ranks shared blockers by affected orders. Each order may have several blockers.

## Run from a checkout

From the repository root, run the following command and open [the local center](http://127.0.0.1:8765/). The application uses relative asset paths and needs an HTTP origin.

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory research/progress/control-center
```

Use **Overview → Find an executive order** to inspect a particular record. **Blockers** lists shared failures and dependency declarations. **Next best action** opens the shared recovery queue. The repository copy works with its bundled generation when GitHub is unavailable.

## Source and refresh policy

The bundled tracker generation finished November 2, 2026 and was read at repository commit `600ae3018f71025b3e53dc8538b8f92e6e159b76`. Its order table reuses the exact Git blob of the tracker CSV. The app assets match private Site source commit `aac08d6deb6b5eef0c023b2835f7719d0951731f` (published version 2). The job catalog and recovery examples remain dated reference material.

On opening, on manual refresh, and every five minutes while visible, the page checks public GitHub main. When the head changes, it loads the tracker summary, generation receipt, per-order CSV and Stage 19 register from the same commit. It verifies the successful tracker result and reconciles per-order totals before replacing the displayed generation. A failed read leaves the last loaded data and a refresh notice. Pull requests refresh separately. The job tiers, dependency examples and recovery handoffs remain dated reference material.

The records of authority are [the tracker summary](../../../jobs/readiness-tracker/output/SUMMARY.json), [its generation receipt](../../../jobs/readiness-tracker/output/STATUS.json), [per-order readiness](../../../jobs/readiness-tracker/output/READINESS_BY_ORDER.csv), [shared unlocks](../../../jobs/readiness-tracker/output/SHARED_UNLOCKS.csv) and [the Stage 19 human-review register](../../stage19/output/PROGRESS.json). Use these directly in a headless Sol session. A machine-ready dossier can retain original-replacement and quotation-recheck obligations. Stage 19 separately records human certification.

For production triage, read the complete per-order blocker strings. The saved Site's generic advice recognizes some bare codes, while the tracker also emits qualified values such as `OPEN_SOURCE_AUDIT:<hash>` and `CLAIM_CHECK_FAILED:<step>`. Preserve the suffix and inspect the underlying record. For Olney's historical catalog entry, use the [workflow registry](../remaining-work/workflow/WORKFLOW_NODES.json) at the catalog revision if its older source link is unavailable.

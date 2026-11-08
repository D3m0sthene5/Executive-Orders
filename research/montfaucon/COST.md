# Montfaucon cost ledger

## m001 — 50 official-page targets, 2026-11-08

| Model tier | Work charged to this batch | Input tokens | Output tokens | API-equivalent USD |
|---|---|---:|---:|---:|
| gpt-6.1-sol | Ten independent accepted reader contexts across Federal Register July/November, GPO Indian Reservations 1912, GPO Panama Canal 1922, and GPO Trading with the Enemy Act 1920; one separate Indian discrepancy adjudication | unknown | unknown | unknown |
| gpt-6-luna | Quarantined Panama and Federal Register control attempts; no verdict from these attempts was accepted | unknown | unknown | unknown |
| Coordinator | Source inventory, image rendering, record assembly, source checks, and integration | unknown | unknown | unknown |

The platform exposed no per-context/model token or dollar telemetry for this
batch. The Codex goal's aggregate token counter covers research, tools,
coordination and code work across this wider session; it is not a model-level
bill and cannot be assigned to m001. No cost has been entered as zero.

The Bentham checkpoint uses the plan's **$0.38 per attempted order** planning
proxy, not measured batch spend. Its displayed `spent_usd: 0` reflects the
gate parser's handling of an unknown `usd` cell and must not be read as actual
spend. The ranking's page-check action has no measured prior rate, so
`bentham.py gate` cannot run on it directly; the direct gate run uses a declared
uniform Beta(1,1) prior. See `GATE_M001.json` and `GATE_M001.md`.

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

## m002 — 50 Federal Register targets, 2026-11-08

| Model tier | Work charged to this batch | Input tokens | Output tokens | API-equivalent USD |
|---|---|---:|---:|---:|
| gpt-6.1-sol | Two independent 50-order reader contexts, five separate third-reader adjudications, and two supplemental EO:7624 crosswalk examinations by the original readers | unknown | unknown | unknown |
| Coordinator | PDF and page-image acquisition, GPO crosswalk retrieval, record assembly, validation, and integration | unknown | unknown | unknown |

Both readers caught all three planted controls before their production review.
There was no quarantined m002 model output. Each sealed review file has its
SHA-256 in `REPORT_M002.md`; initial EO:7624 uncertainty was retained in both
sealed files, with later supplements recorded separately in its final record.

The platform again exposed no per-context/model token or cash telemetry.
`jobs/bentham/sessions.py` reads local Claude Code transcript usage and cannot
account for this Codex run. The aggregate Codex goal counter is not a
per-model bill. The m002 Bentham checkpoint uses the planning proxy
$0.38/attempt, not measured spend. Its `spent_usd: 0` is a parser artifact for
unknown `usd: null`, not zero cost. See `GATE_M002.*`.

## m003 — 50 Federal Register targets, 2026-11-08

| Model tier | Work charged to this batch | Input tokens | Output tokens | API-equivalent USD |
|---|---|---:|---:|---:|
| gpt-6.1-sol | Two independent controlled 50-order readers and one separate blind third reader for EO:10020 and EO:10214 | unknown | unknown | unknown |
| Coordinator | GovInfo issue retrieval, page rendering, manual boundary examination, assembly, validation and integration | unknown | unknown | unknown |

Both readers caught all three controls before production. No m003 reader
output was quarantined. Their sealed 50-row files and control answers are in
`reviews/m003/`; the two original scope judgments remain visible beside the
adjudicator's decisions. No per-context/model token or cash telemetry was
exposed. The $0.38/attempt Bentham input is a planning proxy. `usd: null` in
the ledger means **unknown**; the gate's `spent_usd: 0` is a parser artifact.
See `GATE_M003.*`.

## m004 — 50 Federal Register targets, 2026-11-08

| Model tier | Work charged to this batch | Input tokens | Output tokens | API-equivalent USD |
|---|---|---:|---:|---:|
| gpt-6.1-sol | Two independent controlled 50-order readers and a separate blind third reader for four OCR-substitution disagreements | unknown | unknown | unknown |
| Coordinator | GovInfo retrieval, image rendering, source/hash checking, record assembly and integration | unknown | unknown | unknown |

Both readers caught all three controls before production. No m004 output was
quarantined. All four third-reader findings include the exact printed and
held glyphs and the reason the discrepancy is recognition noise. There is
no per-context/model token or cash telemetry. The Bentham $0.38/attempt
figure is a planning proxy; the ledger's `usd: null` is **unknown**, not
zero. See `GATE_M004.*`.

## m005 — 50 Federal Register targets, 2026-11-08

| Model tier | Work charged to this batch | Input tokens | Output tokens | API-equivalent USD |
|---|---|---:|---:|---:|
| gpt-6.1-sol | Two independent controlled 50-order readers and a separate blind third reader for EO:11974 and EO:12279 | unknown | unknown | unknown |
| Coordinator | GovInfo retrieval, SHA-256 checks, page rendering, source and held-text pinning, record assembly and integration | unknown | unknown | unknown |

Both readers caught all three controls before production. No m005 model
output was quarantined. Actual per-context/model token and cash telemetry was
unavailable. `usd: null` in the ledger means **unknown**; the Bentham
$0.38/attempt input is a planning proxy and its `spent_usd: 0` a parser
artifact, not measured spend. See `GATE_M005.*`.

## m006 — 50 Federal Register targets, 2026-11-08

| Model tier | Work charged to this batch | Input tokens | Output tokens | API-equivalent USD |
|---|---|---:|---:|---:|
| gpt-6.1-sol | Two independent controlled 50-order readers and a separate blind third reader for EO:8269 and EO:12705 | unknown | unknown | unknown |
| Coordinator | GovInfo issue retrieval, SHA-256 checks, page rendering, source and held-text pinning, record assembly and integration | unknown | unknown | unknown |

Both readers caught all three controls before production. No m006 model
output was quarantined. Actual per-context/model token and cash telemetry was
unavailable. `usd: null` in the ledger means **unknown**; the Bentham
$0.38/attempt input is a planning proxy and its `spent_usd: 0` a parser
artifact, not measured spend. See `GATE_M006.*`.

## m007 — 50 Panama GPO-volume leads, 2026-11-08

| Model tier | Work charged to this batch | Input tokens | Output tokens | API-equivalent USD |
|---|---|---:|---:|---:|
| gpt-6.1-sol | Two independent controlled 50-order page readers | unknown | unknown | unknown |
| Coordinator | Public GPO PDF acquisition, SHA-256 and page-image checks, negative-record assembly and integration | unknown | unknown | unknown |

Both readers caught all three controls and agreed on all 50 production
findings. The source-locator lane stopped at its Bentham gate. Actual model
tokens and cash telemetry were unavailable. `usd: null` means **unknown**;
$0.38/attempt is a planning proxy, and the direct gate's `spent_usd: 0` is a
parser artifact, not measured spend. See `GATE_M007.*`.

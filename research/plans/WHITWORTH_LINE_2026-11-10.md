# Whitworth: one production line, its interfaces and its cost target (2026-11-10)

Named for Joseph Whitworth, whose standard screw thread (1841) let parts made in different shops fit together. On
2026-11-10 the owner asked the coordinating session to "make extra sure that the machinery for making the next push
cost far far less actually happens". Six sessions are each building one part. The risk is that every part lands and
they still don't fit, or that they fit and nobody measures whether the cost fell. This file fixes the interfaces,
the target, the stop rule and the proof, before any part merges. The coordinating Claude session owns integration
and keeps this file current.

## The line

```
census + acquisition         Linnaeus (bulk sources, table reconciliation), Accursius (CURRENT, OWN_TEXT, ACTOR_TEXT, working texts)
        |
   triage gate               Larrey: an order enters only if every input its route needs is held (zero tokens)
        |
   script draft              Nalimov: a complete claim drafted from held, hashed evidence (zero tokens)
        |
   conveyor                  Maudslay (merged #269): small verification packets, two blind arms, typed planted controls
        |
   checker + kit complete    unchanged: claim-checker and kit.py complete are the only way a claim files
        |
   adoption                  Respondendi v2 lots (+ Ulpian life-bound lot): audits first, then the ledger; owner merges
        |
   measure                   MEASURES.json per batch -> Bentham -> next plan
```

## Interfaces (each part must meet these; the coordinator reviews every PR against them)

| # | From -> to | Contract |
|---|---|---|
| I1 | Larrey -> conveyor `reserve`, claim-kit admission, Bentham | A committed per-order gate file, one JSON line per (order, route): `instrument_id`, `route`, `pass` (bool), `missing` (gate ids), `gates_commit`. The conveyor's reserve stage and `kit.py next` take only `pass: true` orders for the action. Bentham ranks on the gated pool, not the raw pool. The `missing` tally is published as the acquisition to-do list. |
| I2 | Accursius -> Larrey, Nalimov | New basis records (`CURRENT:`, `OWN_TEXT`, routed `ACTOR_TEXT`, credited working texts) appear in the claim kit's existing outputs, so the gate and the drafter read them without code of their own. Each Accursius PR lists the files and fields it adds. `CURRENT:` is compiled (`STATUS_LEADS.jsonl` `current_law_leads`). `OWN_TEXT`, `PARENT_END` and `working_text_basis` are built at freeze time; readers compute them with the pure functions `own_text.records(...)` and `status_overlay.working_text_basis(...)` over compiled `OVERLAY_INPUTS.selected` plus `CLAUSES`, whose signatures stay stable (coordinator decision 2026-11-10: no compiled projection, which would cost another compiler-pin rebuild). |
| I3 | Linnaeus -> Nalimov, Larrey | Bulk-source records use the shared `SOURCES.jsonl` format (hash, locator, explicit number match). Reconciliation records (two or more independent official tables agreeing on a later event) carry every table's locator and hash and are documented in the job README. Silence in a table is never evidence. |
| I4 | Nalimov -> conveyor | The drafter plugs into the Maudslay conveyor as a route (script draft in place of the producer stage), not a second pipeline. Its claims pass the same `kit.py apply`, `batch-check`, blind review, control and `complete` stages unchanged. Verification packets carry typed planted controls (removed later event, partial end as whole, wrong order's text, date shift). Packets are grouped by acting instrument and ordered parent before amendment-only child. |
| I5 | conveyor completions -> Respondendi v2 | Status proposals from a completed batch are exactly the input `respondendi.py plan` reads. Every lot kind Nalimov drafts has a matching Respondendi v2 lot with a zero-token predicate. Adoption writes nothing before the lot's cross-family audits. |
| I6 | every batch -> Bentham | `MEASURES.json` reports, per batch: orders reserved, gated out, drafted, upheld, filed and adopted; tokens and dollars by stage (draft, verify arms, reveal, repair, adjudication); dollars per filed claim and per adopted status, at the prices in `jobs/necker-costs/PRICES.json`. |

## The cost target (a forecast, registered before any run)

Baselines, measured:

| Route | Cost | Source |
|---|---|---|
| Undecided status, per adopted status | 7.71 USD (Papinian), 4.04 (Haloander) | Respondendi report, wave cost records |
| Lifecycle claim, per filed claim | 4.71 USD (Papinian, 297 USD / 63 filed) | F-20261110-codex-token-split |
| Fully successful order, any route | 3.92 USD (n = 15) | F-20261105-herschel-survey |

Target for the first integrated calibration batch (about 30 orders, one lane, Augur-gated):

- **Cost:** at most 1.00 USD per filed claim and per adopted status, a cut of at least 4x.
- **Quality:** every planted control caught by both arms, the checker passing every filed claim, no regression in the
  share of arm disagreements against Papinian.
- **Stop rule:** above 2.50 USD per filed claim or adopted status, or any control missed, stops the line. No larger
  batch runs until the coordinator has diagnosed the cause by stage from `MEASURES.json` and recorded it in Kean.
- **Scoring:** the batch result is recorded in Kean against this forecast (hit or miss, by how much), whatever it is.

These are forecasts. Nothing here is a measurement until the batch runs.

## The proof: an end-to-end gauge test

Before the calibration batch, the coordinator adds a road test that runs the whole line on fixtures with the
conveyor's fake workers: gate file -> draft -> verification packets -> two arms -> controls -> `complete` -> a
Respondendi dry-run plan -> `MEASURES.json`. It fails if any interface above breaks. It runs in road-tests on every
PR that touches any part, so a later change cannot silently disconnect the line.

## Order of landing

1. Accursius F3 and F7 (independent), then F5 and F6 (both touch `status_overlay.py`).
2. Larrey gate (I1). Linnaeus jobs and reconciliation (I3).
3. Nalimov rebased on Accursius, plugged into the conveyor (I4).
4. Respondendi v2 lots matching Nalimov's kinds (I5).
5. Gauge test green. Calibration batch plan passes Augur, with the owner's or a different model family's review
   signature. Run. Score. Then, and only then, a larger batch.

Every merge is the owner's. Human-certified stays 0. AI statuses stay provisional hypotheses.

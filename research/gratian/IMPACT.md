# Gratian impact: what each product moves, measured on `main`

**No product of the night wave moves any order to ready for human review in the tracker. One order, EO 10926, should
become ready at the next claim-checker run, because Ptolemy now holds the bytes its claim cites.** The tracker counts
an order as ready only when it has a claim that passes the claim gate and claim-checker, plus a source or a recorded
exhaustion for every step. Tonight's products supply sources and leads. So they move orders toward ready in four
places:

- the text step, measured;
- the claim-ready group (text and counterevidence done, only a drafted claim missing), measured;
- the claim kit's reach into undecided orders, counted from the kit's compiled inputs;
- the custody of cited bytes, projected from the checker's rows.

Human certification stays at 0.

## Method

`research/gratian/ablate.py` runs the unchanged `jobs/readiness-tracker/tracker.py` `build()` on `main` at `b561d57a`,
offline, once per variant. Each variant changes only the tracker's table of job outputs it reads (`J`). Mabillon's held
printings are on unmerged branches, so their `FRAGMENTS.jsonl` and `texts/` were copied from
`claude/mabillon-register` into the working tree for the run and removed afterwards. Mabillon is measured as PR #164
would register it. Raw results: `ablation/SUMMARY.json`, `ablation/CONTRIBUTIONS.json` (the order ids gained and
lost by each product) and `ablation/FINAL_ORDERS.csv` (every decided order under all products, with its open steps
and blockers). One full tracker build takes about 40 seconds.

The local baseline counts 1,323 ready. The last published tracker counts 1,309, from commit `6cff8ce9`. The 14-order
difference comes from inputs merged since then, not from this branch, which changes no tracker input.

## Results

| Variant | Ready | One step away | Claim-ready group | Decided orders with text step satisfied |
|---|---:|---:|---:|---:|
| `main` | 1,323 | 40 | 1,299 | 3,096 |
| `main` without Tischendorf | 1,323 | 40 | 1,299 | 3,098 |
| `main` without Lachmann | 1,323 | 40 | 1,290 | 2,935 |
| `main` without both | 1,323 | 40 | 1,290 | 2,930 |
| `main` plus Mabillon (PR #164) | 1,323 | 40 | 1,357 | 3,225 |
| all products, plus Ptolemy credited for Opus re-fetches | 1,323 | 40 | 1,357 | 3,225 |

"One step away" uses Bentham's rule: a claim is present and exactly one applicable step is open. The claim-ready group
uses Bentham's `in_claim_ready_stratum` rule without its hold exclusions.

| Product | To ready | To one step away | Into the claim-ready group | Text step (decided orders) | Why |
|---|---:|---:|---:|---|---|
| Mabillon (with #164) | 0 | 0 | +58 | +146, −17 | 1,771 proved printings satisfy the text step. Its 244 leads awaiting a page check reopen 17 provisional Lachmann texts (`tracker.py:135`, `547`). |
| Lachmann | 0 | 0 | +9 | +161 | Confirmed working texts make the step provisional. |
| Tischendorf | 0 | 0 | 0 | +3, −5 | 37 strong finds; its leads awaiting a page check reopen 5 provisional texts. |
| Ptolemy | +1 projected | 0 | 0 | 0 | Its 1,390 kept files reach the tracker only through claim-checker, which last ran before they were committed. 4 of the 7 custody-only rows in filed claims cite bytes it holds. EO 10926's only open step is one of them; EO 10622's is also under an open source audit. Crediting Ptolemy in the Opus-media step moves no order. |
| Niebuhr | 0 | 0 | 0 | 0 | Date leads for Lewis (56 numbered orders gain a date); never a tracker input. |
| Selden | 0 | 0 | 0 | 0 | No job output committed yet; when it lands, the kit and later-events read it (CONCORDANCE). |
| Pothier | 0 | 0 | 0 | 0 | No leads or sources yet. |
| claim-drafts, status-history empty histories | 0 | 0 | 0 | 0 | They act in the claim kit: 10,628 undecided orders have drafts, and 5,918 undecided orders with compiled overlay inputs and no dated history can now be prepared for a status decision. |
| Clark web stage | 0 | 0 | 0 | 0 | Hands 55 orders to Lewis. |

A product's effect is the difference between the variants with and without it. Effects can overlap, so they are not
summed.

## What still blocks the decided orders

After all products, 2,968 of the 4,291 orders with a provisional status are not ready:

- 1 has every step done but a claim-level error;
- 40 have one open step;
- 31 have two open steps;
- 2,896 have three or more.

The blockers held by the most orders:

| Blocker | Orders |
|---|---:|
| No clause inventory | 2,786 |
| Savings and residuals not closed | 2,786 |
| First end unproved | 2,408 |
| Machine later-source search incomplete (no OFR catalog entry) | 1,245 |
| Only a compiled transcription found | 915 |
| No official source located | 848 |
| Opus media re-fetch needed | 431 |
| Current basis unproved | 378 |
| Official copy found, page check needed | 218 |

The 2,786 orders with no claim yet account for the first three rows and for "Current basis unproved" (2,408 NO plus
378 YES orders). Each order's own blockers are in
`ablation/FINAL_ORDERS.csv`.

## NEXT-DOSSIER queue

[`NEXT_DOSSIER.csv`](NEXT_DOSSIER.csv) ranks the orders closest to ready after all products and names what closes each
gap, cheapest first. [`NEXT_DOSSIER.txt`](NEXT_DOSSIER.txt) lists tier 1 in rank order, one id per line, the format of
`jobs/bentham/output/strata/production.one_step_away.txt`. `research/gratian/next_dossier.py` rebuilds both.

Tier 1 holds 41 orders: the 40 one-step orders and EO 14139, whose steps are all done but whose claim still lists
material gaps. They split by what closes the gap:

- **Machine, 4 orders, no tokens.**
  - EO 10926: the next claim-checker run.
  - EO 12743: Ptolemy holds nothing for its cited Presidency Project page of EO 13286 (sha256 `1cc5a246…`), so the page
    needs a fetch request.
  - EO 10110 and EO 11931: their Opus Federal Register files were left out of the release as too large, and neither
    source-ladder nor Ptolemy has requested them.
- **Producer, 24 orders.**
  - 20 claims leave a first end or current basis open. The ending instrument is already held for every one (Selden's
    `ORDER_NEEDS.csv` shows no unheld ending instrument for them), so the gap is a date or a scope question, or else an
    exhaustion record with the gap disclosed.
  - EO 10494 has quotations that do not match the held text.
  - 2 orders have partly resolved Opus media.
  - EO 14139 needs its material gaps closed or disclosed.
- **Reviewer, 9 orders.** Each has an open source audit to reconcile.
- **Person, 4 orders.** Each has a quarantined relationship conflict to settle.

Tier 2 holds the 58 orders that enter the claim-ready group when #164 merges. They need a drafted claim, and Bentham
prices them in its `production.claim_ready` strata.

## Limits

These are tracker counts on one commit. The claim-checker's effect is projected from its last rows, not rerun, because
a full run takes about 25 minutes on a runner and was not repeated here. The claim kit was not rebuilt, so the
reach into undecided orders is counted from its compiled inputs. It does not show how many of those orders pass
`dispatch-check`.

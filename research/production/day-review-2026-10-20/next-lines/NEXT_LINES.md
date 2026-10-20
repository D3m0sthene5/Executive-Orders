### Next lines after Lambertini IV and R9830 (Tycho II, 2026-10-20)

Screen: `lambertini build` at ed5c29ef9 (scratch output), readiness tracker 14:20Z (230 ready), claim-kit dossiers, ACTING_PROVISIONS and OWN_TERMS. Every pool below is decided NO, not ready, has its original text step done, and has no claim. No id appears in any Llull batch pool, any day-review ids file, any `research/excavator/*-2026-10-20` record, any claim file, any act_overrides file or the Astra reservation.

The screen dropped the following:
- emergency boards and boards of inquiry (49)
- report-tied own ends, and amendments of report-tied parents (EO 12097, 12397, 12060, 12307, 12987, 13032)
- contrary current-law leads (8 + 2)
- quarantined, transcription-only and page-check originals
- EO 11012 targets (external regulations date)

None of the remaining orders needs a pending owner ruling. Nothing is committed, and certified stays 0.

Llull rank ran on a scratch ledger copy, with Lambertini III and IV base rates added from O-35 and O-56. The ending gate is left out of the strict ceiling because the method itself produces the ending record (LAMBS2 had strict 0 and upheld 20 of 24).

| # | Pool (ids file) | Size | Method | Base rate | E ready | Cost | Ready per $ | Main risk |
|---|---|---|---|---|---|---|---|---|
| 1 | VIAPAR (`VIAPAR_ids.txt`) | 22 | Lambertini per instrument. The ending is the whole revocation of the parent "as amended", from claim-kit `whole_via_parent` ACT leads.<br>EO 12076 ×12 (amendments of EO 11861, the Executive Schedule; the reading `LSP-EO_12076` already exists from Lambertini III i08). Also EO 12379 ×5, 12220 ×2, 12610 ×2 and 13062 ×1. | Lambertini IV 0.5625 (9/16); III 0.634 | 11.3 | $31 | 0.36 | Later amendments replaced or deleted items, so some items need per-item first ends (D6).<br>Any strike-and-reinsert falls under the EO 14052 ruling; block it, do not decide it.<br>Precedent: 19 via-parent orders are already ready (codif, Lambertini s01, Lamm s04). |
| 2 | R12553NB (`R12553NB_ids.txt`) | 52 | Rastell ACT records for EO 12553 (all 52 numbers appear in the held 51 FR 7237 text), then claims on the orders those records enable | ACT 0.90 (108/120, EO 12553 subline); claims 0.60 (R12553C); enabled share assumed 0.65 (boards were 0.83) | 18.4 | $99 (probe of 10: $19) | 0.19 | These are not boards, so earlier ends are likelier. Examples: the oil-decontrol orders (EO 12153, 12186, 12187, 12189, 12209) may have ended under EO 12287 in 1981, and 8 orders have their own dated sunsets. In those cases EO 12553 is only an upper bound, which lowers the enabled share. |
| 3 | PAGECHK3 (`PAGECHK3_ids.txt`) | 11 | Page-check the 3 held official FR scans of the ending EOs (12319, 12919, 12692), then run Lambertini on their targets | Lambertini IV 0.5625 × 0.8 assumed page-check pass | 4.5 | $24 | 0.19 | A page check could fail, or the wrong pages could be held. The page-check pass rate is unmeasured. |
| — | F11490 (`F11490_ids.txt`, not ranked) | 20 | Clean single-instrument supersession: EO 11490 superseded EO 10997–11005, 11087–11095 and 11310 | — | — | $0 first | — | Fails test (b) today. The ladder holds FR-1969-10-30 PDF pages 1-40, but the order is on pages 63-95. A zero-agent ladder fix or re-extraction of pages 63-95 comes first; after that, it is a Lambertini pool. |

Launch order:
1. VIAPAR: an EO 12076 probe of 8, then scale.
2. R12553NB: a probe of 10. Make Rastell ACT records with the D6 earlier-end test, then claims.
3. PAGECHK3 after both.

Gates must be enforced in code. Use a planter step that plants into a scratch copy, and an independent Opus reviewer with the held sources and the D6 step. Register forecasts before production.

Scratch: `/tmp/claude-0/-home-user-Executive-Orders/357394c8-997b-5c91-82db-c4517632e70c/scratchpad/tycho2/` (`actions.json`, `output/RANK.json`, `ledger/`, `screen.json`, `tools/`).

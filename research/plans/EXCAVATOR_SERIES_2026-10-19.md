# Excavator series: cutting the agent-hours left (2026-10-19)

Selection made before implementation, in the format of `research/stage19/FUNNEL.md` and
`EXCAVATOR_FUNNEL_2026-10-18.md`. That funnel cut the cost of one claim on modern orders; this one
targets **where the remaining hours are**, measured by the effort model in
`research/progress/remaining-work/` (`EFFORT_MODEL.csv`, `EFFORT_NOTES.md`).

## Where the 17,144 agent-hours sit

`excavator_scenarios.py` sorts every open step by era and, for orders before 1937, by type. The type
comes from the WPA 1944 summary hint or, for EO 5076-7531, from APP's title.

| Group | Open orders | Agent-hours |
|---|---:|---:|
| Before 1937, type not yet known | 5,854 | 7,065 |
| Before 1937, land (withdrawals, forests, reserves, refuges, Indian and military reservations) | 2,240 | 3,218 |
| 1937 and later | 6,806 | 2,961 |
| Before 1937, spent on issue (one-person civil-service waivers, retirement exemptions, fund allotments, closings) | 1,738 | 2,608 |
| Before 1937, swept by one later event (WWI emergency, NRA codes, Canal Zone) | 828 | 1,292 |

The group sizes count orders with an open ending step, plus the 1,314 orders APP counts that the
project does not hold yet; those are counted as land because the books that list them (General Land
Office, Indian and military reservation compilations) are mostly land orders.

**Diagnosis.** About 83% of the hours are pre-1937 orders, where the tools hold almost nothing.
There are no disposition tables before 1937, no Federal Register, often no text, and no machine history.
Modern orders are already cheap, at about 25 agent-minutes each. Cutting hours means building for the
old orders, and above all for **classes** of them, since most are repetitive.

## C. Ten ways to cut the agent-hours left

"Hours saved alone" is that idea by itself against the 17,144-hour baseline. Coverage sets are computed
from committed data. Hit rates and new minutes are assumptions written in `excavator_scenarios.py`.

| # | Distinct concept | Where its leverage comes from | What it removes | Principal limit | Hours saved alone |
|---:|---|---|---|---|---:|
| 1 | **Type tribunal** | The order's own nature | Decide the ending pattern once per type of spent-on-issue order (a one-person civil-service waiver is exhausted on appointment, the appointment surviving as an accrued effect; an allotment is exhausted when funds are obligated or lapse; a closing ends that day). Each order then needs a row check, not a research job. | Only for types whose orders really are uniform; outliers must drop out. | 1,245 |
| 2 | **Extinction-event mapper** | One external event that ends many orders | Registers mass-ending events once, as shared sources, and maps candidate orders to them: the war-emergency joint resolution of March 3, 1921; the NRA's collapse after *Schechter* (1935); the end of the Canal Zone (1979); Philippine independence (1946); FLPMA (1976) for withdrawal authority. | An event is a candidate end; scope, savings and earlier ends still need checking. | 442 |
| 3 | **Public Land Order harvester** | Interior's own revocation record | Reads every Public Land Order (BLM index from June 1942; Federal Register on govinfo). PLOs revoke old land orders by date and reserve name, sometimes a dozen at once (PLO 7465 revoked 13 Montana orders). It resolves those to EO numbers and emits later-event edges. | Orders revoked before 1942 or by statute are missed; date-only references need careful matching. | 784 |
| 4 | **Living-law back-propagation** | The present, searched backward | Turns "search later law for contrary sources" for old orders into a fixed check against a closed set of current registers (U.S. Code tables and notes, eCFR, PLO index, refuge and forest establishment lists), recorded automatically per order; agents read only hits. | Proves "not cited in current law", not "never revived". | 1,122 |
| 5 | **Reel-to-text bulk acquisition** | One institutional source instead of 6,000 hunts | Full texts of EO 1-7403 exist as one microfilm set, "Executive Orders (1845-1936; nos. 1-7403)" (Harvard Lamont Library, Film S 1130; one bibliography attributes the filming to the Library of Congress). The WPA's 1944 list and Lord's indexes are on HeinOnline. One acquisition, then OCR and splitting by number, gives every old order a graded copy and a machine clause draft. | Needs the owner to obtain the reels or library access; typescript copies are not originals. | 2,409 |
| 6 | **Editorial annotation miner** | Notes editors already wrote | Turns the WPA 1944 summaries, Lord, Richardson, APP footnotes and U.S. Code notes into amend and revoke edges. Measured coverage is low: 8% of the WPA summaries held mention a revocation. | Annotations are leads, often silent. | 365 |
| 7 | **Risk-tiered review** | Review effort spent where risk is | Rows that match a reviewed exemplar exactly get a 20% independent-AI audit sample instead of full re-review; any deviation gets full review. Reviewers are about 30% of agent time (Astra swarm). | Changes the project's review standard: **needs the owner's OK**. Human review is unaffected. | 1,747 |
| 8 | **Look-alike template cloning** | Textual near-duplicates | Clusters near-identical texts (forest boundary changes, water reserves, waivers, NRA approvals; modern actor families of 5+ in claim-kit) and clones the exemplar's clause inventory and claim skeleton, re-verifying exact spans per text. | Clones can hide a one-word difference; the span re-check must be strict. | 2,021 |
| 9 | **Census gap admission line** | Lists that already name the missing orders | Builds admission packets (date, signer, text, page) for the 1,314 orders APP counts and the project lacks, from Lord's unnumbered list, census-completeness clusters and early-orders-hunt texts. | Admission stays a human identity decision; the codebook is unchanged. | 475 |
| 10 | **Negative-search automaton** | Proving absence cheaply | For orders with no copy, runs a fixed, fully logged search ladder over every repository the project uses and writes a proposed exhaustion record; an agent signs off in minutes instead of hunting for 25. | Network failures must never count as exhausted (ROI estimate warning); an exhausted text is a weaker dossier. | 2,433 |

Ideas the funnel left out: a model cascade (cheap model drafts, strong model on disagreement) cuts
tokens more than agent-hours; the context-lean protocol from yesterday's funnel is already adopted.

## Selected series

Five excavators, combining the best features of all ten, in build order. Savings are **marginal**: each
counts only what the ones before it did not already save. The series as a whole takes the estimate from
**17,144 to about 9,100 agent-hours (47% less)**.

| Excavator | Combines | Marginal hours saved | Hours left after |
|---|---|---:|---:|
| X1 Lifecycle class engine | 1, 2, 8, 7 | 4,134 | 13,010 |
| X2 Land ledger excavator | 3 | 441 | 12,569 |
| X3 Reel-to-text excavator | 5, 10 | 2,424 | 10,146 |
| X4 Living-law counter-search | 4, 6 | 925 | 9,220 |
| X5 Census gap admission line | 9 | 138 | 9,082 |

### X1 Lifecycle class engine (zero-token job, then batch review sheets)

1. **Classify** every pre-1937 order by type from the WPA hint, APP title and text keywords. The
   7,065 hours in "type not yet known" are the biggest pool; every share of it classified moves
   into the cheaper paths below. This step is cheap and comes first.
2. **Type rule book** (extends `jobs/family-rules`, 25 rules today): one reviewed rule per type, with its
   ending pattern, savings pattern and the facts that would make an order an outlier.
3. **Extinction-event register**: each mass-ending event fetched once into shared sources and mapped to
   candidate orders by type, date and keywords. A candidate, never a decision.
4. **Look-alike clusterer**: shingle-hash near-duplicate texts; exemplar plus per-order diff; exact-span
   re-verification.
5. **Batch sheets** of 50-100 rows feed the existing claim-kit decision-sheet assembler, with
   risk-tiered review (owner's OK first).

### X2 Land ledger excavator

Every Public Land Order since 1942 from the Federal Register, plus BLM's PLO index. Extract
references to executive orders by number, date and reserve name (Public Water Reserve No. 107,
Power Site Reserve No. 15), resolve them to EO numbers through the WPA dates, and emit
`later-events`-shaped edges. Also read current refuge, forest and reservation registers to mark
**still-in-force candidates**: many land orders are YES orders, and those need a current basis, not an end.

### X3 Reel-to-text excavator

- **Owner action, with lead time:** a sanctioned route to one full-text source for EO 1-7403 (the
  microfilm set, Film S 1130 at Harvard's Lamont Library or its source; HeinOnline's Lord volumes
  through a law library; or Columbia's WPA typescripts). The CIS Index to Presidential Executive
  Orders & Proclamations (1789-1983) is a cross-check.
- **Then the machine work:** OCR, split by order number, hash, grade as a government or WPA copy
  (`acceptable_as_original=false`), and run clause-drafts.
- **For what remains:** the negative-search automaton writes proposed exhaustion records with every
  query and response.

### X4 Living-law counter-search

A recorded, bounded later-law search for every old order against the closed register set (current-law
job, eCFR, X2's PLO edges, APP footnotes, WPA and Lord annotations). Agents read only the hits.

### X5 Census gap admission line

Admission packets for the 1,314 missing orders; the hours that move are mostly the "admit" and
text steps. Its marginal saving is small because X1-X4 already cover these orders' legal steps.

## Why this cut

- It aims at the 83% of hours in pre-1937 orders, and at classes of orders rather than single ones.
- Three excavators (X1 classification and rule book, X2, X4) are zero-token jobs on public sources;
  X3 needs one owner decision; only risk-tiered review changes a review standard.
- Every output is a lead, candidate or packet. No excavator fills a judgment field, admits an order,
  changes a count or touches the human-certified numerator (still 0).
- **What is left after the series (about 9,100 hours)** is mostly legal judgment on old orders whose
  type stays unknown, and modern dossiers. Classifying the unknown pool is the main upside beyond this
  estimate.

## Success test before scaling

For each excavator, pilot 50 orders and record agent-minutes per step and tier (the instrumentation
`AUTOMATION_ROI_ESTIMATE_2026-10-17.md` asks for). Keep it only if:

- minutes per accepted claim fall;
- the reviewer rejection rate stays at or below the claim swarm's 11%;
- under risk-tiered review, the audit sample finds no more errors than full review did.

Replace the assumed hit rates and minutes in `excavator_scenarios.py` with the measured ones and rerun.

## Sources consulted

- BLM, Public Land Orders index: https://www.blm.gov/programs/lands-and-realty/land-tenure/withdrawals/public-land-orders
- PLO 7465, revocation of 13 executive orders, Montana (2000): https://www.federalregister.gov/documents/2000/10/16/00-26427/public-land-order-no-7465-revocation-of-13-executive-orders-montana
- PLO 7390 (1999), revoking a 1922 reservoir site reserve order: https://www.govinfo.gov/content/pkg/FR-1999-04-20/pdf/99-9888.pdf
- Harvard Library guide, executive orders (microfilm of EO 1-7403, Film S 1130; HeinOnline; CIS Index): https://guides.library.harvard.edu/uspresident/execorders
- Columbia, WPA typescript copies of executive orders 1862-1938: https://findingaids.library.columbia.edu/archives/cul-4079616
- Lawfare, the March 3, 1921 joint resolution ending war-emergency measures: https://www.lawfaremedia.org/resources/lawfare-news/when-did-world-war-i-end

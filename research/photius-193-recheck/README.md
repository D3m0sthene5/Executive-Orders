# The 193 orders that left ready on 2026-11-07: transcription vs. official printing

On 2026-11-07, 193 orders (EO 8032-9208) left ready: Photius had added an official GPO printing for each, which made their filed working-text confirmations stale. Kean records the finding as F-20261107-ready-drop-193-photius-witness and the owner question as A-20261107-photius-193-recheck.

`compare_193.csv` is a machine comparison, with no model tokens, of each order's confirmed transcription with its Photius GPO printing (`jobs/photius-gpo-volumes/output/texts/EO_<n>.txt`). Both texts are lower-cased, words split across line breaks are rejoined, and the texts are reduced to letters and digits. The coverage figure is the share of the transcription's words that appear, in order, in the printing's OCR text. The printing's pages also hold neighbouring documents, so only the transcription's coverage is measured.

| Band | Orders |
|---|---:|
| 99% or more | 40 |
| 95% to 99% | 146 |
| 80% to 95% | 7 |

**What this is not.** It is not a page check, a confirmation or a readiness step, and no status, claim or count changes. OCR noise in the printing explains most gaps below 100%. The bands only order the paid page-check wave: start with the 7 lowest, and expect the 40 at 99% or more to pass quickly.

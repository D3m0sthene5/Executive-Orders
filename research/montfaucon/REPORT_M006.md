# m006: 50 Federal Register original-page checks, 1937–1994

**Result:** 50 distinct current `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` targets:
26 pass, 18 fail, 6 unsure, 0 invalid. Both blind gpt-6.1-sol readers caught
all three planted controls before production. A fresh blind third reader
resolved two verdict disagreements. EO:8269 fails because the held OCR loses
operative exchange-rate table row associations. EO:12705 passes because its
wrong worklist title is metadata; the source and held text have the correct
order number, date, signer and operative words. Both initial assessments
remain visible. Local assembly accepts all 300 m001–m006 records, derives
205 official fragments and rejects none.

The immutable source fragment, held OCR and public GovInfo issue PDF are
pinned by SHA-256. Passing records retain all 41 actual target-page images.
A pass establishes the complete printed order in the cited source scope and
the held text comparison, allowing specified mechanical OCR noise. It does
not certify a clean transcription, every glyph, human review, physical
location or a legal conclusion. No source fragment, held OCR, claim, status,
census, codebook or restricted ProQuest file was changed. All 193 Cujas
Photius-stale identities were excluded.

## Passing orders

EO:8054, 8102, 12141, 12319, 12678, 12688, 12692, 12705, 12710,
12716, 12751, 12758, 12781, 12782, 12789, 12790, 12791, 12800,
12805, 12821, 12825, 12845, 12863, 12883, 12893, 12903.

## Failed sources, spans or text

| Order | Exact failure |
|---|---|
| 7647 | Cited PDF 5 / 2 FR 1315 is FTC notices; EO 7647 is absent, and its claimed June 28 signature postdates the June 26 issue. |
| 7698 | Actual order is PDF 11 / 2 FR 2071; cited and held PDF 1 is Panama Canal proclamations. |
| 7909 | Cited PDF 10 / 3 FR 1422 is SEC material; EO 7909 is absent. |
| 8269 | Printed PDF 1 / 4 FR 4241 has the full order, but held OCR fuses and drops operative exchange-rate table country, unit and rate associations. |
| 8361 | Cited PDF 25–46 / starting 5 FR 851 is distilled-spirit regulation; issue opens with EO 8355, not 8361. |
| 8847 | Cited PDF 22 / 6 FR 4020 is Bituminous Coal Division material; target absent. |
| 9274 | Cited PDF 25 / 7 FR 4647 is petroleum material in a June issue, while the claimed order is dated November 1942. |
| 9356 | Cited PDF 39 / 8 FR 8771 is agency material; target absent. |
| 9546 | The cited issue opens with EO 9545 / 10 FR 4685; target absent. |
| 9567 | Cited PDF 7–8 / 10 FR 9617–9618 is War Production Board material; target absent. |
| 9579 | Cited PDF 124–125 / 10 FR 9186–9187 is OPA coal-price material; issue opens with EO 9589. |
| 9582 | Cited PDF 135 / 10 FR 9197 is OPA material; target absent. |
| 9623 | Cited PDF 81 / 10 FR 1205 is January price regulation, months before the September order. |
| 10417 | Cited PDF 3–4 is a letter discussing EO 10417; the order itself is absent. |
| 12768 | Held/cited July 2 issue PDF 4–9 contains a proclamation; the target is in the July 1 issue, PDF 422 / 56 FR 30302. |
| 12829 | Held PDF 297–299 stops mid-section 201(e); sections 202–203 and closing continue on PDF 300–301 / 58 FR 3482–3483. |
| 12886 | Printed order begins PDF 215 / 58 FR 68709, not cited 68708; ends PDF 218 / 68712. |
| 12906 | Printed order begins PDF 229 / 59 FR 17671, not cited 17670; ends PDF 232 / 17674. |

## Unsure dense schedules

EO:12698 (54 FR 53473–53492), 12767 (56 FR 30284–30301), 12777
(56 FR 54757–54770), 12826 (57 FR 62909–62919), 12888
(58 FR 69153–69168) and 12902 (59 FR 11463–11471) have identified
source spans, but their held numerical annexes, tables or long amendments
could not be fully certified against the images. The precise uncertainty is
in each sealed review; none receives pass credit.

## Controls, receipts and gate

The challenges placed EO:12903 on the adjacent contents page, changed its
heading to EO:12904, and changed the operative extension year from 1995
to 1996. Both readers rejected all three. Blind challenges, answer key,
answers, sealed 50-row reviews and two blind adjudications are under
`reviews/m006/`.

| Receipt | SHA-256 |
|---|---|
| Reader A | `3c1a8a3ac84ef44a8a86eda29acc3746b5227744506f0588ade317bdba0e1ef4` |
| Reader B | `6758eb4dfad58184513b435fc8bd30ff11757b94b013946414727808e3382aab` |
| Third reader | `b4da7aa78ba6376709560912030dc1d407145628b0738d4669192cac2fb66ca7` |
| Reader A controls | `0c1b009599c559e9cb45c7a712f33869b8271a36e9afdd3b75dbbc595be5d976` |
| Reader B controls | `cd412e82fb4609a6b68fc1124fd1c1adc252ecbea9139d31fe7247cb908fcb14` |

`BATCHES.jsonl`, `GATE_M006.*` and `COST.md` preserve the checkpoint and
unknown actual spend. This source-family PR carries no generated job outputs.

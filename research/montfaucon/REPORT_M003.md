# m003: 50 Federal Register original-page checks, 1941–1951

**Result:** 50 distinct current `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` targets,
36 pass, 14 fail, 0 unsure, 0 invalid. Two blind gpt-6.1-sol readers caught
all three planted controls before the real work. They agreed on 48 verdicts.
A fresh blind third reader adjudicated the two prescribed-manual scope
disagreements, both fail. Local `page_check.assemble` accepts all 150
m001–m003 checks, derives 102 official fragments, and rejects none.

Each source is a public GovInfo Federal Register issue PDF pinned by SHA-256.
Every passing record retains images of all actual order pages and their
hashes. The two manual disputes retain images of the held cutoff and the
terminal publication page. The page check establishes source identity,
location and complete-order coverage while recording observed OCR errors;
it does not certify a glyph-perfect transcription, human review, physical
location, or a legal finding. No source fragment, held text, claim,
provisional status, census, codebook or restricted ProQuest file changed.
The 193 Cujas Photius-stale identities were excluded.

## Passing orders

EO:8634, 8642, 8647, 8681, 8694, 8861, 9095, 9150, 9216, 9257, 9337,
9412, 9418, 9448, 9479, 9499, 9532, 9556, 9586, 9636, 9678, 9721,
9730, 9733, 9747, 9769, 9801, 9846, 9881, 9921, 9947, 9971, 9988,
9993, 10001, 10199.

## Failed held or cited spans

| Order | Actual target PDF / printed pages | Exact failure |
|---|---|---|
| 8800 | 1 / 6 FR 3097 | Held/cited PDF 3, printed 3099, contains aviation regulations, not the one-paragraph order. |
| 9004 | 2–10 / 7 FR 2–10 | Held PDF 2 ends in Schedule A; omits the remaining schedules and closing on PDF 10. Intermediate pages were not glyph-collated after the decisive truncation. |
| 9005 | 10 / 7 FR 10 | Held PDF 26–29 contain other regulations; the complete order is on PDF 10. |
| 9215 | 2 / 7 FR 6158 | Cited printed 6157 is wrong; PDF 2 contains the complete order on 6158. |
| 9360 | 1 / 8 FR 9437 | Held PDF 37, printed 9473, contains Alien Property orders, not EO:9360. |
| 9459 | 6 / 9 FR 9878 | Cited printed 9879 is wrong; the complete order is on 9878. |
| 9461 | 7 / 9 FR 9879 | Held PDF 27–29 contain other regulations; complete EO:9461 is on PDF 7. |
| 9600 | 4–5 / 10 FR 10158–10159 | Held PDF 4 stops in the opening; replacement section, wage list and closing on PDF 5 are missing. |
| 9655 | 1–14 / 10 FR 14121–14134 | Held PDF 2–14 omits the opening on PDF 1, including identity, prescribing clause and definitions. |
| 9763 | 1 / 11 FR 8141 | Held PDF 4–6 contain unrelated regulations; the order is complete on PDF 1. |
| 9779 | 1 / 11 FR 10575 | Cited source has only a heading and filing notice for F.R.Doc.46-17004, not operative text or signature. An official full-text source is still needed. |
| 9966 | 1 / 13 FR 3193 | Cited source has only a heading and filing notice; held PDF 1–3 contain unrelated regulations. An official full-text source is still needed. |
| 10020 | 57–167 / 13 FR 7519–7629 | Held PDF 57–59 ends in Chapter IV of the Manual for Courts-Martial that the order expressly prescribes. Missing PDF 60–167 / 13 FR 7522–7629. |
| 10214 | 41–207 / 16 FR 1303–1469 | Held PDF 41–43 ends in manual paragraph 4g(3). Missing PDF 44–207 / 16 FR 1306–1469. |

For EO:10020, the terminal PDF page 167 contains appendices and the
F.R.Doc.48-10746 filing line; for EO:10214, terminal PDF page 207 contains
Appendix 19 and F.R.Doc.51-2131. The signed prefatory orders prescribe the
following manuals. The first readers disagreed whether to judge only the
signed preface or the prescribed content. The third reader independently
inspected opening, held cutoff and terminal images and found both held texts
incomplete. A complete signature on the preface does not make the abruptly
cut manual complete. Both conflicting initial assessments and final reasons
remain in the JSONL record.

## Controls, receipts and limits

The planted challenges were EO:8634's missing closing page, its closing
number changed to neighboring 8635, and “six months” changed to “six years.”
Both readers rejected all three. Their control answers and sealed 50-row
reviews are under `reviews/m003/`.

| Receipt | SHA-256 |
|---|---|
| Reader A 50-row review | `746dade966f29f9ee7ea8ea45ec7a2bef5cce4bc89ee57263deb6e525e333ec7` |
| Reader B 50-row review | `23f2c06635d0dfb15fd9637d403f817bd5bfc569541ce14c72b4880fb211ba37` |
| Reader A controls | `fc02c99b558c0236f782de8e582b098f4dd8d06ebb942d6b32f179f1cb612fcc` |
| Reader B controls | `02f89c92f4bb5e0739c7766376a2d891d3c433bc0bfedb030901a7013241ecab` |

`BATCHES.jsonl`, `GATE_M003.*` and `COST.md` retain the checkpoint and
explicitly distinguish the planning proxy from unavailable actual spend.

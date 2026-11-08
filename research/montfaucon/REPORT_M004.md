# m004: 50 Federal Register original-page checks, 1951–1967

**Result:** 50 distinct current `ORIGINAL_FOUND_NEEDS_PAGE_CHECK` targets,
42 pass, 8 fail, 0 unsure, 0 invalid. Two blind gpt-6.1-sol readers caught
all three planted controls before production and agreed on 46 verdicts.
A fresh blind third reader adjudicated four plausible OCR substitutions,
all pass under the explicit recognition-noise allowance; the conflicting
initial assessments remain visible. Local `page_check.assemble` accepts all
200 m001–m004 records, derives 144 official fragments, and rejects none.

Each source is a public GovInfo Federal Register issue PDF pinned by SHA-256.
Each passing record retains all actual target-page images and hashes. The
checks establish source identity, exact printed pinpoint, complete target
coverage within the cited PDF range, and comparison of held OCR to the
printed order. They do not certify a clean transcription, every glyph,
human review, physical location, or a legal finding. Extra neighboring
PDF pages alone did not defeat an otherwise complete, correctly pinpointed
order; the actual narrow target span is recorded. The immutable fragments,
held text, claims, statuses, census, codebook and restricted ProQuest files
were not changed. All 193 Cujas Photius-stale identities were excluded.

## Passing orders

EO:10230, 10280, 10281, 10287, 10292, 10486, 10490, 10495, 10590,
10607, 10761, 10819, 10841, 10854, 10881, 10905, 10922, 10941,
10987, 11025, 11043, 11060, 11062, 11066, 11072, 11080, 11081,
11116, 11143, 11146, 11147, 11155, 11156, 11159, 11177, 11194,
11208, 11255, 11306, 11344, 11359A, 11375.

## Failed held or cited spans

| Order | Actual complete PDF / printed pages | Exact failure |
|---|---|---|
| 10246 | 1 / 16 FR 4743 | Held/cited PDF 5–7 contains other material; the entire order is on omitted PDF 1. |
| 10427 | 3–4 / 18 FR 407–408 | Held PDF 3 ends in §9; omits continuation, §10 and Truman's closing on PDF 4. |
| 10524 | 3–4 / 19 FR 1809–1810 | Held PDF 3 stops mid-word; PDF 4 has remainder of §§2–3 and closing. |
| 10588 | 1–3 / 20 FR 361–363 | Held PDF 1 stops in §2; PDF 2–3 contain remaining operative sections and closing. |
| 10827 | 1–3 / 24 FR 5233–5235 | Held PDF 1 stops in §4(a)(3); PDF 3 has remainder, revocation and closing; PDF 2 is contents. |
| 10833 | 3–4 / 24 FR 6867–6868 | Held PDF 3 has the preamble only; PDF 4 has numbered provisions, land description and closing. |
| 10850 | 1–5 / 24 FR 9559–9563 | Held PDF 1 stops mid-preamble; PDF 3–5 contain land provisions, savings and closing; PDF 2 is contents. |
| 11030 | 3–4 / 27 FR 5847–5848 | Coverage is complete, but source/held signed date June 19, 1962 contradicts fragment's expected June 15, 1962. |

For EO:10486 and EO:10881, the held OCR reads 10436 and 10831 in the
headings where the images print 10486 and 10881. For EO:10922, the scanned
signature is John F. Kennedy while OCR reads John P.; for EO:11255, the
scanned date is November 1, 1965 while OCR reads November 7. The independent
third reader inspected all four complete originals and classified these as
single-glyph recognition mistakes, including the italic 1-to-7 shape, not
substituted source text. All exact printed/held mismatches and the initial
reader B failures are retained in the JSONL records. The passing result
still does not authenticate the OCR transcription for quotation.

## Controls, receipts and limits

The challenges were an EO:10230 claim limited to its first page although
it continues to printed 2907, a neighboring order number 10231 in place
of printed 10230, and “Selective Service Act of 1949” in place of the
printed 1948. Both readers rejected all three. Blind challenges, key,
control answers, sealed 50-row reviews and the four blind adjudications
are under `reviews/m004/`.

| Receipt | SHA-256 |
|---|---|
| Reader A 50-row review | `b009dbf8b923183b3a8116c4188eda2c2d1a0e49f13871f0a646dedd9d0fb4e8` |
| Reader B 50-row review | `1af77ccd739577686ae034da20969816d2e0d6dfea2443bb6a05bbc9278abf8b` |
| Third-reader four-row finding | `8a3c8232969ce373184cbe1d607328e78924477354b541cc44d532be670d7197` |
| Reader A controls | `9f331d91c305e3a687c4a88a06ea06464c2bbb2cc8aefb509d6fae73df490ad1` |
| Reader B controls | `2cbacbfaa0a6eb508f74174f47e000e015ae561a8c583e7061eddfc8d7b13528` |

`BATCHES.jsonl`, `GATE_M004.*` and `COST.md` preserve the checkpoint and
unknown actual spend. This PR carries no source-data or legal-status edits.

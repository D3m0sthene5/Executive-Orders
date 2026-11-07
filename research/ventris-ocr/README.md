# Ventris OCR pilot (Encyclopedie campaign, OCR stream)

Question: is GPO's OCR text layer on scanned Federal Register, Statutes at Large and Serial Set pages good enough, and if
not, does a voting protocol over other readers fix it? Design: `research/peiresc-tool-survey/04-ocr.md` (branch
`claude/peiresc-tool-survey`). Everything below was measured on this PC (DANSRIG, Windows 11, RTX 5080 16 GB, driver 610.88)
on 2026-11-06. Nothing here is a legal or status finding; it is a measurement of readers on 58 crops.

## Headline

1. **The pipeline works end to end for four readers plus Claude**: GPO layer, Tesseract 5.4, Surya 2.5 (surya-ocr 0.23.0),
   PaddleOCR 3.7 (PP-OCRv5), and Claude (claude-sonnet-5-5). 58 passages x 6 readings (Tesseract twice, psm 6 and psm 3) =
   348 readings in `READINGS.jsonl`. PaddleOCR-VL was **not** attempted (see "Not done").
2. **There is no reference text yet, and the owner's agreement rule leaves almost nothing.** Of the 43 non-owner passages,
   **1 (P020) has GPO's layer and Surya identical** after whitespace folding; 42 disagree and are left out, as instructed.
   Loosening "exactly" would keep 8 (CER <= 0.5%), 18 (<= 1%), 25 (<= 2%), 34 (<= 5%) of 43 (strict; lenient folding: 2, 10, 19,
   27, 34). Not used, information only. So the spot-check section of the worksheet has 1 passage, not 10, and the adoption
   test's "invents nothing on clean" arm has **1 clean passage**. **Decision for the owner / coordinator** (see
   `NOTES.md`): accept a looser agreement rule, enlarge the owner set, or use a 2-of-3 agreement that includes Claude.
3. **Reference-free preview** (labelled PREVIEW in `SCORES.json`; no reference exists, so none of this is accuracy):
   on the 15 passages whose land descriptions contain fractions (335 quarter/half glyphs as Claude read them), the glyphs each
   reader produced: **GPO layer 0, Tesseract 0 (both psm), PaddleOCR 22, Surya 134, Claude 335**. The GPO layer never
   contains a fraction glyph; it writes "NE^4", "S ^ N E ^", "SE14NW 1/" instead. Section signs: GPO 16, Surya 16, Claude 16,
   Tesseract 11-12, PaddleOCR 10.
   Mean CER of each reader taking **Claude's reading as the yardstick** (Claude is not a reference; this only shows distance):
   hard passages GPO 0.169, Tesseract psm6 0.220, PaddleOCR 0.233, Surya 0.245, Tesseract psm3 0.251; clean passages
   PaddleOCR 0.012, Tesseract psm6 0.015, Tesseract psm3 0.017, GPO 0.033, Surya 0.034. (On clean prose GPO and Surya are the
   farthest from Claude; both differ from it on punctuation, curly apostrophes, hyphen joins, a stray "credit., Each".)
4. **What is waiting on the owner**: type the 15 passages in `reference_entry.html` (section 1) and spot-check section 2;
   export the two CSVs into this folder; run `py -I score.py` (it prints the adoption test).

## What the owner decided (Kean D-20261106-encyclopedie-ocr-reference) and how it is built

* Owner transcribes 15 hard passages: `OWNER_SET.json` (rule inside it; chosen from `PASSAGES.csv` metadata before any
  reading was compared: 7 fractions, 3 section symbols, 3 digit-heavy tables, 2 two-column crops, no crop with ink on its left or
  right edge, at most 2 per source file). One local worksheet, `reference_entry.html`: for each passage the crop image, its
  GPO text (read-only, folded away) and a blank box with buttons for the fractions and symbols, local autosave, CSV export.
  The 15 are P032 P033 P034 P036 P037 P043 P046 P047 P048 P050 P052 P054 P055 P056 P058.
* All other passages: reference = text on which GPO's layer and **Surya** (the best non-Claude engine that installed; PaddleOCR
  is the other) agree exactly (`score.py: build_agreed`). Disagreements are left out and counted: **42 of 43**.
  **On agreed passages GPO's layer and Surya score 100% by construction, so those passages measure only the other readers
  (Tesseract, PaddleOCR, Claude and the voting rules that are not just GPO or Surya).** They say nothing about whether GPO
  or Surya is right, and the agreeing text could be wrong in the same way in both (the spot-check exists for that).
* Spot-check: `make_reference_page.py` puts up to 10 agreed passages in section 2 (all of them: 1).
* `score.py` adoption test: halving uses only owner passages; "invents nothing" uses only agreed clean passages.

## Setup (venv `C:/Users/danie/eo-venvs/ocr`, Python 3.12.10; full list `ENV_pip_freeze.txt`)

| Piece | Version | Notes |
|---|---|---|
| PyTorch | 2.14.1+cu130 (torchvision 0.29.1+cu130) | `--index-url https://download.pytorch.org/whl/cu130`; arch list includes sm_120; CUDA matmul verified on the 5080 |
| Surya | surya-ocr 0.23.0 (checkpoint datalab-to/surya-ocr-2.5, Qwen3.5-based 0.69B VLM), transformers 5.22.2 | installed from PyPI; see "Surya on Windows" |
| PaddlePaddle | paddlepaddle-gpu 3.4.0 (cu129 index `https://www.paddlepaddle.org.cn/packages/stable/cu129/`) | `paddle.utils.run_check()` passes on GPU (compute capability 12.0) |
| PaddleOCR | paddleocr 3.7.0, paddlex 3.7.2, PP-OCRv5 (`en`, mobile rec) | |
| Tesseract | v5.4.0.20240606 (already installed), `eng.traineddata` as installed | psm 6 is the project's setting (`jobs/_lib/eo_pdf.py`); psm 3 also run |
| PDF | pypdfium2 5.15.0 (render and text layer), numpy 2.3.5, Pillow 10.4.0 | |

Nothing outside the venv, no driver, PATH or system setting was changed. No docker, vllm or llama.cpp binary was installed.

**Surya on Windows.** Surya 2.5 needs a vllm (docker) or `llama-server` backend, neither present. `engines/surya_hf.py` is a
`Backend` subclass that loads the same checkpoint with transformers (bfloat16, greedy) and feeds Surya's own prompts, image
scaling, parser and `RecognitionPredictor` (full-page mode, one VLM call per crop). Two things to know: the transformers
tokenizer's ByteLevel decoder turns the model's single-character tokens for the quarter/half fractions into U+FFFD although the
model emitted the right token. The first Surya run therefore had 0 fractions; `decode_ids()` fixes it and Surya was re-run on all
58 crops. The superseded first run is kept in `SUPERSEDED_READINGS.jsonl`, not scored. Also, without flash-linear-attention and
causal_conv1d (not installed) transformers uses reference kernels, so Surya is slower than its own docs suggest.

**PaddleOCR next to torch.** paddlepaddle-gpu bundles cuDNN 12 and torch cu130 bundles cuDNN 13 under the same DLL names;
importing both in one process fails (WinError 127). `run_paddle.py` hides torch (`sys.modules["torch"] = None`) because
PaddleOCR only imports it via modelscope for logging. Run the engines as separate processes.

## Cost per engine (this PC)

Per crop (58 crops, median crop 724 x 361 px at 300 DPI, range 607-1633 x 307-593) and per full page (FR 1949-03-10 PDF p.8, 2574 x 3368 px, one run):

| Reader | s per crop (mean / median / max) | s per full page | GPU memory |
|---|---|---|---|
| GPO layer | 0 (copied from PDF) | 0.017 | none |
| Tesseract psm 6 / psm 3 | 0.32 / 0.30 / 0.63 ; 0.31 | 3.7 / 3.6 (1 thread) | none |
| PaddleOCR (PP-OCRv5, GPU) | 0.08 / 0.07 / 0.49 | 0.98 (after warm-up) | 2,012 MiB reserved on crops; 11,708 MiB on the full page |
| Surya 2.5 (transformers, GPU) | 6.4 / 5.3 / 16.1 | 71.5 | 1,523 MiB peak allocated (1,674 reserved) on crops; 2,344 / 2,522 on the full page |
| Claude (claude-sonnet-5-5) | not timed per crop | not run | n/a |

Model load: Surya about 25 s. All of it fits in 16 GB with room to spare; PaddleOCR-VL was not tried.

## The 58 passages (`PASSAGES.csv`)

* 28 hard (12 land-description fractions, 6 section symbols, 6 digit-heavy tables or schedules, 4 two-column crops) and 30
  clean prose (12 Federal Register, 9 Statutes at Large, 9 Serial Set). 17 Federal Register issues (1941, 1946, then 1949-1971; land orders
  1949-1971 as asked), 7 Statutes granules and 5 Serial Set documents, 29 distinct source PDFs. Target was about 60; the snap and edge rules below dropped some candidates.
* Sources are pages the project already holds or cites: FR issues from `jobs/fr-pages` (15 used) and `jobs/fr-originals` (2 used),
  Statutes at Large granules from `jobs/selden-statutes` (7 used), Serial Set documents whose page URLs appear in the case bundles (5).
  All 38 PDFs were downloaded from govinfo.gov (robots.txt honoured, 3 s pacing, `fetch.py`, 746 MB under `C:/Users/danie/eo-ocr-work/pdf/`,
  outside git). **For all 33 FR and Statutes files downloaded (25 issues, 8 granules) the project already held a SHA-256, and the new download matched it byte for
  byte**; no file mismatched. Serial Set files had no earlier hash. URL, final URL, SHA-256, size and time are in
  `SOURCES_MANIFEST.jsonl`.
* Page images: 300 DPI PNG per page (hashes in `PASSAGES.csv: page_png_sha256`); crop box in pixels on that image; crop PNG hash. GPO layer =
  pdfium bounded text inside the crop (`gpo_text_layer_json`, JSON-escaped so its CR LF line ends survive; never edited).
* **Selection bias, stated plainly.** Hard passages were chosen by features read from the text layer (fraction-like tokens, the
  section sign, digit share) and clean ones by word-like text, so "hard" is enriched for places where GPO's layer has such
  tokens (right or wrong). It is not enriched for places where GPO is known to be wrong. Windows are column or page-width line
  blocks found by ink projection; tops and bottoms snap to ink-free rows; FR columns cut at gutters, which clips a few line ends:
  P038 and P039 lose the last characters of 3 lines each (Claude transcribed what is visible); P023 has right-margin note fragments, omitted.
  Serial Set and Statutes crops can contain marginal notes (transcribed on their own lines, rule below).
* Scans: the FR pages are about 150 ppi colour JPEGs inside the PDF (2,400 px wide at 300 DPI render is an upsample), as the survey suspected.

## Claude readings

* Reader: claude-sonnet-5-5 (this session's model), each crop PNG opened with the Read tool and transcribed by hand; stored via
  `ingest_claude.py` (hash of image, crop, prompt, output). 58 of 58 done in batches of up to 5 crops per turn (the brief asked
  for one at a time; batches kept each transcription independent of the others' text but not of the previous images).
  Raw text: `CLAUDE_TRANSCRIPTS.txt`. Sampling settings are not controllable on this path; output is not reproducible.
* Prompt, identical for all 58 (full text also in every record): "Transcribe all printed text in this image exactly as it appears,
  character for character, line by line. Keep each line break where the image breaks the line. Write fractions such as one-quarter as
  the single character [quarter sign] (and half, three-quarters); keep the section sign, degree, minute and second marks, and the printed
  spelling, punctuation, capitalization and hyphenation. Do not correct errors, expand abbreviations or complete cut-off words. If a line
  is cut off at the top or bottom edge of the image, omit it; if a character cannot be read, write [illegible]. Write small capitals as
  capital letters and a row of leader dashes, underscores or dots as '...'. Where the image has several columns, transcribe the left
  column completely, then the next. A marginal note goes on its own line(s) just before the main-text line it sits beside. Output only the
  transcription." The prompt was fixed in writing after the transcriptions were done. Its conventions for marginal notes (first needed at P022-P024)
  and for small capitals and leader rows (first needed at P033) were adopted when those features first appeared; P001-P021 contain
  none of them. The owner worksheet carries the same rules.
* **Smoke test (first 5 crops, P001-P005)**: no refusal, no hedging, no commentary, no "[illegible]". Same on all 58. These are
  government land orders and statutes, so a content filter was never plausible; no test was made on sensitive material.
* Known weak spots in the Claude text: P044 (not in the owner set; the bracketed document number printed as "[1506978]" is uncertain,
  and Claude omitted the half-cut last line), P048 and P057 (low-resolution fractions), leader rows and small caps follow the stated
  convention. Where a line is partly cut at an edge Claude's omit/include choice is a judgement, so Claude's CER against a reference that
  includes or omits such a line is slightly unfair either way. The owner's rule is the same, which should cancel most of it.

## Scoring (`score.py`, tests `test_score.py`: 16 tests, all pass, `py -I test_score.py`)

* Strict normalisation (NFC, whitespace folded, nothing else) and a lenient one (curly quotes, dashes, primes, soft hyphen, space before
  punctuation) are both reported; the adoption test is printed for both.
* Per reader: exact-match rate, failures with Wilson 95% interval, mean CER, invention count, on `owner_hard`, `agreed_hard`, `agreed_clean`.
* Rules: single readers, `majority-exact` (>= 3 of GPO/Tesseract/Surya/PaddleOCR identical, else abstain), `medoid`,
  `agree3-else-claude` (Surya = PaddleOCR = GPO, else Claude), `claude-judge` (the non-Claude reading nearest Claude's, so it cannot
  invent text no engine produced), `surya+gpo-else-claude` (circular on agreed passages; meaningful on owner passages only).
* **Invention** = the minimum-edit alignment of reading to reference has a run of >= 6 consecutive inserted characters (a fabricated
  or duplicated word with no counterpart in the reference). Why: noise gives isolated insertions and a mangled glyph gives a
  substitution plus one or two insertions (a quarter sign read as "y4"), both below 6; a made-up or repeated word or sentence tail is
  6 or more. 6 is the shortest word-sized run (5 letters and a space). It is a threshold I chose and tested on synthetic cases
  only; change `INVENT_RUN` to move it.
* **Adoption**: a rule is adopted only if (a) on owner passages exact-match failures <= half of GPO's (GPO must fail at least 2)
  and (b) on agreed clean passages it invents on none. Fifteen passages is small: a Wilson interval is reported next to each failure
  rate, and a rule that halves 15 failures to 7 is not clearly better than GPO.
* Pairwise engine agreement without references: `SCORES.json: PREVIEW_pairwise_cer_NO_REFERENCES` (labelled; strict and lenient).
* `SCORES.json` in this commit has no owner references (none exist yet), so only the preview, the agreement counts and the
  sensitivity table are meaningful.

## Files

`fetch.py select_targets.py TARGETS.json SOURCES_MANIFEST.jsonl` sources; `pagetools.py build_candidates.py select_passages.py
choose_owner_set.py finalize_passages.py PASSAGES.csv OWNER_SET.json` passages; `run_gpo.py run_tesseract.py run_surya.py
run_paddle.py engines/surya_hf.py ingest_claude.py readings.py READINGS.jsonl SUPERSEDED_READINGS.jsonl CLAUDE_TRANSCRIPTS.txt
bench_page.py BENCH.jsonl` readings; `make_reference_page.py reference_entry.html REFERENCE_SHEET.csv AGREED.json` worksheet;
`score.py test_score.py SCORES.json` scoring; `ENV_*.txt` environment. Page and crop PNGs and PDFs stay in
`C:/Users/danie/eo-ocr-work/` (not in git). The worksheet loads crops from there by absolute path, so it opens correctly only on this PC.

## Not done

* PaddleOCR-VL (not installed; classical PP-OCRv5 only), Gemini, olmOCR, Chandra, Azure: not in this brief.
* Claude was not run on whole pages or timed; no token count was kept. Tesseract was not tuned (no upscaling, no `tessdata_best`).
* Full-page Surya and PaddleOCR numbers are one page, one run each.
* 1936-1949 Federal Register pages are thin in the sample (1941, 1946, 1949 only), and no typescript EO or ProQuest scan was included.

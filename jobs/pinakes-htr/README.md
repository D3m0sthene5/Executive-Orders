# Pinakes HTR: new readings of the scans the text screen rejects

Pinakes (`jobs/pinakes-proquest-ingest`) gives every ProQuest order a text, from the PDF's own layer or from tesseract.
About 310 orders still fail its quality screen (`text_usable: no`), mostly handwritten originals, where tesseract writes
word-shaped nonsense. This job reads those scans again, **on the owner's PC only**: it needs a GPU and has no `job.py`
or `job.sh`, so the GitHub runner never picks it up, and nothing is sent off the machine.

## The design: two independent readers, compared word by word

A model that reads with the sense of the sentence fails differently from one that reads only the ink. Where two
independent readings agree, the reading is likelier right; where they disagree is exactly where a person should look.
On handwriting, the literal engines turned out to be too weak to serve as a check (see the bake-off), so the two
readers are two vision-language models, both Qwen-derived. Their agreement is not independent-family verification:

| Reading | Script | Model | Role |
|---|---|---|---|
| `vlm_qwen3` | `vlm.py` | `Qwen/Qwen3-VL-8B-Instruct`, 4-bit NF4 (about 7.6 GB VRAM) | backbone: best recall on faded pages, fastest, readiest to write `[illegible]` instead of guessing |
| `vlm_chandra` | `vlm.py` | `datalab-to/chandra-ocr-2` (Qwen 3.5 based, OCR-trained), bf16 (about 10 GB) | cross-check: lowest character error on clean pages, but invents signatures and dates |
| `tess300` | `htr.py` | tesseract 5.4, 300 dpi, contrast-stretched, despeckled, `--psm 3` | literal check, meaningful on typed pages only; never confirms a word alone |

`compare.py` aligns each backbone word with the cross-check's reading. Words the cross-check did not also read are
marked ⟦like this⟧ in `texts/EO_<n>.compare.txt`; `COMPARE.csv` lists the orders least confirmed first, as the queue
for a person's page check. Both models are prompted to transcribe literally (no corrections, no modernizing, `[illegible]`
for unreadable words). A page where a model loops is retried once with a stronger repetition penalty; if it still loops
the repeats are collapsed and counted in `degenerate_pages`.

TrOCR line-by-line reading is still in `htr.py` but off by default (`HTR_TROCR=1` turns it on).

## Bake-off (2026-10-21)

Three sample pages, scored against a reading made only for choosing a model (it is not evidence and is not in the repo):
EO 12 and EO 14 are clean 1874 clerk's hands; EO 23 is a faded, speckled 1884 page whose lower half is barely legible.

| Reader | EO 12 CER | EO 14 CER | EO 23 readable part recovered | Seconds per clean page (RTX 5080) |
|---|---:|---:|---:|---:|
| Qwen3-VL-8B, 4-bit | 3.5% | 0.6% | 87% | 8-9 |
| Chandra OCR 2 | 6.0% | 0.2% | 87% | 12-17 |
| Qwen3-VL-8B, 8-bit | 3.5% | 1.4% | 80% | far slower (8-bit kernels) |
| Qwen3-VL-4B | 5.3% | 0.5% | 78% | 6-7 |
| Qwen2.5-VL-3B | 2.5% | 1.4% | 73% | 5-10 |
| CHURRO 3B (historical-text model) | 10.3% | 1.1% | 82% | slow; loops |
| TrOCR large handwritten | 87.6% | 51.3% | 18% | |
| tesseract, 300 dpi | 86.4% | 69.5% | 21% | |

On the faded page every model invented words where the ink fails (one wrote "Laboratory Exhibition, at Chicago", another
a cabinet roll with a Secretary of Labor), each different ones. This matches WildHandBench (2026), which attributes
63-91% of model errors on handwriting to language priors. Hence two models and a comparison, never one model alone.

## What the texts are

Machine hypotheses for searching and routing, never source texts. They do not replace the Pinakes texts, the
readiness tracker does not read them, there is no fragment for them, and they do not move the certified count
(`acceptable_as_source_text: false`, `needs_page_check: true`, `counts_toward_certification: false` in the provenance
and summary files). Agreement between the models is not proof.

## Outputs (`output/`)

| File | What it is |
|---|---|
| `texts/EO_<n>.vlm_qwen3.txt`, `texts/EO_<n>.vlm_chandra.txt`, `texts/EO_<n>.tess300.txt` | The three readings. |
| `texts/EO_<n>.compare.txt` | The backbone reading with unconfirmed words marked ⟦like this⟧. |
| `COMPARE.csv` | Per order: words, share confirmed, share also read by tesseract, unconfirmed words, words only the cross-check read, `[illegible]` marks, pairwise similarity; least confirmed first. |
| `VLM.csv`, `VLM_PROVENANCE.json` | Per order and model: characters, `[illegible]` marks, retried and degenerate pages, seconds; model ids, revisions, quantization, prompt. |
| `HTR.csv`, `PROVENANCE.json` | The tesseract reading per order, with word-shape scores and confidence; tesseract and poppler versions. |
| `SAMPLE_FOR_PAGE_CHECK.csv` | Ten orders spread across the years, with blank columns for a person to record page kind and words wrong per reading. |
| `REPORT.md`, `SUMMARY.json` | Counts. |

## Running

```powershell
powershell -ExecutionPolicy Bypass -File jobs\pinakes-htr\run_on_pc.ps1            # all orders below the screen
powershell -ExecutionPolicy Bypass -File jobs\pinakes-htr\run_on_pc.ps1 -Limit 10  # trial
```

The script uses the tesseract and pdftoppm that Pinakes's `run_on_pc.ps1` installs (or a Tesseract unpacked into
`%USERPROFILE%\Tesseract-OCR`), creates a private Python environment in `%USERPROFILE%\.pinakes-htr\venv5` (PyTorch
2.7.1 with CUDA 12.8, transformers 5.20.2, bitsandbytes 0.50.2), downloads the two models on first use (about 27 GB),
runs `test_htr.py`, then `htr.py`, `vlm.py` and `compare.py`, and commits and pushes `output/`. Reruns skip what was
already read with the same method key; `VLM_READERS=vlm_qwen3` runs one model only.

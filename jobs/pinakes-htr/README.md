# Pinakes HTR: a second reading of the scans the text screen rejects

Pinakes (`jobs/pinakes-proquest-ingest`) gives every ProQuest order a text, from the PDF's own layer or from tesseract.
About 310 orders still fail its quality screen (`text_usable: no`), mostly handwritten originals, where tesseract writes
word-shaped nonsense. This job reads those scans again, **on the owner's PC only** (it needs a GPU and has no `job.py`
or `job.sh`, so the GitHub runner never picks it up), and nothing is sent off the machine. That keeps the
ProQuest-licensed scans local; cloud handwriting services were ruled out for that reason.

Three readings per order, then a word-by-word comparison (the idea: a literal reading and a contextual one fail differently,
so where they agree the reading is likelier right, and where they disagree is exactly where a person should look):

| Method | What it does | Helps with |
|---|---|---|
| `tess300` | pages rendered at 300 dpi, contrast-stretched, despeckled, tesseract with automatic layout (`--psm 3`) | faint typewriting, carbon copies |
| `trocr` | the same pages cut into text lines (tesseract's line boxes, or an ink projection profile where tesseract finds too few), read by `microsoft/trocr-large-handwritten` on the GPU with a beam-search confidence per line | handwriting |
| `vlm` (`vlm.py`) | each whole page read by a local vision-language model (`Qwen/Qwen2.5-VL-3B-Instruct`, `VLM_MODEL` to change), told to transcribe literally and write `[illegible]`; a page where the model loops is retried with a stronger repetition penalty, and if it still loops the repeats are collapsed and the page counted in `vlm_degenerate_pages` | context: what the sentence says |

`compare.py` takes the fullest reading (the VLM's) as the backbone and aligns every other reading against it word by word.
Each backbone word no other engine confirms is marked ⟦like this⟧ in `texts/EO_<n>.compare.txt`; `COMPARE.csv` gives per
order the share confirmed, the share confirmed by tesseract (the most literal reading) and the similarity of every two
readings, least-confirmed orders first, as the page-check queue. On handwriting the literal engines are weak, so low
agreement there mostly says the literal readings failed, not that the VLM did; agreement is never proof.

## What the texts are

Machine hypotheses for searching and routing, never source texts. They do not replace the Pinakes texts, the
readiness tracker does not read them, there is no fragment for them, and they do not move the certified count
(`acceptable_as_source_text: false`, `needs_page_check: true`, `counts_toward_certification: false` in
`PROVENANCE.json` and `SUMMARY.json`). A handwriting model's decoder writes fluent English even where it misreads,
so passing the word-shape screen is weak evidence for TrOCR. Its confidence is better, and a person's page check
settles it.

## Outputs (`output/`)

| File | What it is |
|---|---|
| `HTR.csv` | One row per order: file, hash, the Pinakes text's source and scores, then per method the text path, length, word-shape quality, common-word share, confidence, whether it passes the Pinakes screen; segmentation used; error. |
| `texts/EO_<n>.tess300.txt`, `texts/EO_<n>.trocr.txt` | The two readings. |
| `LINES.jsonl` | Every TrOCR line: order, page, box (300 dpi pixels), segmentation, confidence, text. |
| `SAMPLE_FOR_PAGE_CHECK.csv` | Ten orders spread across the years, with blank columns for a person to record page kind and words wrong per reading. |
| `PROVENANCE.json` | Program versions, model id and revision, GPU, settings, status flags. |
| `VLM.csv`, `texts/EO_<n>.vlm.txt`, `VLM_PROVENANCE.json` | The VLM reading: characters, `[illegible]` marks, retried and degenerate pages, seconds; model, revision, prompt. |
| `COMPARE.csv`, `texts/EO_<n>.compare.txt` | The comparison (above). |
| `REPORT.md`, `SUMMARY.json` | Counts. |

## Running

```powershell
powershell -ExecutionPolicy Bypass -File jobs\pinakes-htr\run_on_pc.ps1            # all orders below the screen
powershell -ExecutionPolicy Bypass -File jobs\pinakes-htr\run_on_pc.ps1 -Limit 10  # trial
```

The script uses the tesseract and pdftoppm that Pinakes's `run_on_pc.ps1` installs (or a Tesseract unpacked into
`%USERPROFILE%\Tesseract-OCR`), creates a private Python environment in `%USERPROFILE%\.pinakes-htr\venv`
with PyTorch (CUDA 12.8) and transformers on first use, downloads the model (about 2.2 GB, cached by Hugging Face),
runs `test_htr.py`, reads the orders, then commits and pushes `output/`. Reruns skip orders already read with the same
method key (`METHOD_KEY` in `htr.py`); change the model (`HTR_MODEL`) or the settings and they are read again.

## Next

The page check on the ten sample orders gives an error rate per method. If TrOCR's off-the-shelf model is not good
enough on these 19th-century hands, the next step is a model fine-tuned on a few dozen pages a person has
transcribed (eScriptorium/Kraken, or TrOCR fine-tuning), still local.

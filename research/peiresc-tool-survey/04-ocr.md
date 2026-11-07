# OCR and document extraction for scanned US government publications, 1789-1993

Research date: 2026-11-06. Scope: Federal Register (FR) daily issues 1936-1993, Statutes at Large, Serial Set, typescript and microfilm executive orders, some handwriting.

Terms used here. CER = character error rate (share of characters wrong; lower is better). VLM = vision-language model (a model that reads an image and writes text; includes Gemini, Claude, GPT and the open "OCR VLMs" such as olmOCR). "Text layer" = the invisible OCR text embedded in a PDF. olmOCR-Bench = Allen AI's benchmark of 1,400 documents with about 7,000 pass/fail unit tests, split into categories including "old scans," "old math scans," and "multi-column."

## Bottom line

1. **A modern VLM re-OCR will beat GPO's text layer on specific failure classes, and probably not on ordinary prose lines.** I checked one 1955 FR page held in the repo (`jobs/fr-pages/output/captures/be83647478...pdf`, 8471, a Public Land Order). The scan is legible. The GPO text layer garbles every quarter-section fraction in the legal land descriptions ("NE¼NE¼" comes out as "NEy4NEi4", "S& N W ^"), spaces out bold headings ("C o n tin u o u s"), and joins lines from adjacent columns on one line in the default `pdftotext` output. Tesseract 5.3.4 run on a 2.5x-upscaled crop of the same land-description column produced equally bad fractions ("NEYWZNW%4", "SW48E%"). So classical engines will not fix this; a VLM that reads the ¼ glyph is the plausible fix. I could not run a VLM (no API key and no sign-ups allowed), so "VLM fixes it" is an inference from the literature below, not something I measured.
2. **No published benchmark compares any model against GPO's FR text layer.** GPO says only that the issues "were scanned using Optical Character Recognition" and names no engine, resolution or error rate ([FR digitization project notice](https://www.federalregister.gov/reader-aids/office-of-the-federal-register-announcements/2017/01/federal-register-digitization-project)). The decision has to be made by a pilot on the project's own pages (design at the end).
3. **Do not treat VLM output as a replacement text. Treat it as a second, independent voter.** Peer-reviewed and HN evidence agrees that VLMs sometimes rewrite or invent text in legible regions, which barely moves CER but breaks a verbatim-quotation standard (details under "Hallucination" below).
4. **Cost is not the constraint.** For targeted passages (a few thousand pages at most), every option below costs under about $100 total. Only whole-corpus runs (hundreds of thousands to millions of pages) make the model choice matter financially.
5. **The one scan-quality caveat:** the embedded page image in the held capture is a 150 ppi color JPEG (1211x1623). `pypdf` page extraction does not normally resample, so this is probably GPO's own image, but I did not confirm that against the govinfo original (the session proxy refused govinfo.gov). 150 ppi caps what any re-OCR can do on small print such as fractions. Check the resolution of the original issue PDFs before the pilot.

## Published numbers that matter

### olmOCR-Bench, "old scans" and "multi-column" categories (pass rate %, higher is better)

Source: [olmOCR 2 paper, Table 3](https://arxiv.org/pdf/2510.19817) and the [olmOCR demo paper, ACL 2026](https://aclanthology.org/2026.acl-demo.62.pdf). Asterisk = reported by the model's authors, not reproduced by Allen AI.

| System | Old scans | Multi-column | Overall |
|---|---|---|---|
| Chandra OCR 2 (vendor table, [GitHub](https://github.com/datalab-to/chandra)) | 51.1 | 82.1 | 85.8 |
| Chandra OCR 0.1.0* | 50.4 | 81.2 | 83.1 |
| olmOCR 2 | 47.7 | 83.7 | 82.4 |
| GPT-4.1 | 41.4 | 72.5 | not given |
| dots.OCR* | 40.9 | 82.4 | 79.1 |
| Nanonets-OCR2-3B | 40.9 | 81.9 | 69.5 |
| PaddleOCR-VL* | 37.8 | 79.9 | 80.0 |
| MinerU 2.5.4* | 33.7 | 78.2 | 75.2 |
| Marker 1.10.1 | 33.5 | 80.0 | 76.1 |
| DeepSeek-OCR | 33.3 | 66.4 | 75.7 |
| Mistral OCR API (the 2025 version) | 29.3 | 71.3 | 72.0 |

Reading: every system scores 51% or below on "old scans," while the same systems score 80%+ on multi-column modern pages. Either the old-scans tests are hard or noisy, or nobody is good at old scans. The paper does not say which, and I could not find what fraction of failures are scoring artifacts. A Qianfan-OCR entry at 73.1 on old scans appears on a CodeSOTA aggregator page, but the page itself flags inconsistent category values for that model, so I discard it. Gemini 3.x, Claude and Mistral OCR 3/4 have no old-scans number in any source I opened. Mistral OCR 4 is reported at 85.20 overall by a secondary article ([DEV post](https://dev.to/aarhamforensics_eb3c024eb/mistral-ocr-4-document-intelligence-pricing-api-competitor-comparison-knk)); the same article says Mistral itself flags "known scoring limitations." Unsiloed claims 88.0 overall ([Show HN](https://hn.algolia.com/api/v1/items/48271937)), a vendor claim with no old-scans breakdown. Surya OCR 2 lists 83.3 overall at 0.65B parameters ([model card](https://huggingface.co/datalab-to/surya-ocr-2)).

Use olmOCR-Bench as a rough ranking of open models only. It is mostly modern PDFs plus a slice of Library of Congress, Internet Archive and National Archives scans, and HN commenters note olmOCR-Bench and OmniDocBench "have known limitations" ([HN, Mistral OCR 4](https://news.ycombinator.com/item?id=48645152), read through a mirror).

### OmniDocBench

The [CodeSOTA leaderboard](https://www.codesota.com/ocr/benchmark/omnidocbench) (page dated 2026-05-21, many rows fetched 2026-04-20) ranks GLM-OCR 94.62, PaddleOCR-VL-1.5 94.50, DeepSeek-OCR 2 91.09, MinerU 2.5 90.67, Gemini 3 Pro 90.33, dots-ocr-3b 88.41, olmOCR 81.79, Mistral OCR 3 79.75 (composite). Mistral OCR 3 has the best text edit distance (0.099). This benchmark is mostly modern document types, so it says little about 1936-1993 print; I did not verify its document mix beyond my prior knowledge that it includes some newspapers. PaddleOCR-VL-1.5 reports 93.43% on Real5-OmniDocBench "scanning" and 91.25% on "warping" ([paper](https://arxiv.org/pdf/2601.21957)), the closest published proxy for physical scan degradation.

### Historical-document studies (the most relevant evidence)

- **Typewritten microfilm (closest match to the project's typescript EO problem).** [Uruguayan dictatorship-era typewritten documents, 175 binary microfilm images](https://arxiv.org/pdf/2607.24077): Tesseract mean CER 20.92%, EasyOCR 25.41%, Surya-OCR 8.87% (best mean), Qwen 3.6 reasoning mode best median CER 1.72% but mean 11.17% (occasional collapses). The authors list failure modes CER hides: invented names in name lists, spurious text in unreadable regions even when told to write [illegible], and name-for-name substitutions in legible regions that "barely raise CER."
- **Historical newspapers, line and paragraph level.** [Luxembourg pre-1878 newspapers](https://arxiv.org/pdf/2604.00725): Gemini paragraph CER 6.06% versus Tesseract 12.12% and PERO-OCR 12.58%; on Fraktur lines Gemini 10.50% versus Tesseract 21.42%. Models trained on 33,000 in-domain lines reached about 2% on Antiqua lines. Takeaway: general Gemini roughly halves Tesseract's error on old newsprint, and in-domain training beats both. The Gemini version is not stated in what I read.
- **Eighteenth-century printed English lines.** [Qwen2.5-VL-7B CER 0.60% versus TrOCR 1.05%](https://arxiv.org/html/2602.14524); black-and-white scans were worse (0.77% vs 1.46%).
- **Handwriting.** [Humphries, Gemini 3 Pro on 50 documents, 100,000 words](https://generativehistory.substack.com/p/gemini-3-solves-handwriting-recognition): strict CER 1.67% and WER 4.42%, Claude Opus 4.5 CER 4.28%, Claude Sonnet 3.7 10.45%, an OpenAI model 16.81%, Transkribus about 8% CER on raw English without fine-tuning. 61% of Gemini's errors were "correcting" old spelling or punctuation. Minimum thinking scored best. Small, bespoke sample by one author.
- **Faithfulness.** [Amazon's FaithC4 (summarized by Unite.AI)](https://www.unite.ai/even-leading-language-models-are-prone-to-interpretive-transcription/): on 1,455 pages with deliberately damaged words, general VLMs rewrote up to about 65% of scrambled words, and errors spread to untouched words by up to 10x over baseline. Tesseract and docTR degraded least, OCR-specialized models fell in between, and Gemini-3-Flash behaved much more like conventional OCR. Telling the model not to correct reduced but did not eliminate rewriting. Directly relevant to verbatim legal quotation.
- **Newspaper pipelines.** [American Stories](https://arxiv.org/abs/2308.12477) ran layout detection, legibility classification, custom OCR and article linking on nearly 20 million Chronicling America scans; the abstract gives no accuracy figure. The Library of Congress [reprocessed 170,000+ of 23 million pages with Tesseract plus custom post-processing](https://blogs.loc.gov/headlinesandheroes/2025/04/ocr-reprocessing/) (no accuracy numbers, no cost). A [Show HN pipeline over 600,000 Chronicling America pages](https://hn.algolia.com/api/v1/items/47984614) used PaddlePaddle layout models plus OCR plus LLM cleanup; its author and a commenter agreed layout and reading order was the hardest part and remains imperfect.
- **Layout and reading order.** [Historical Armenian newspapers](https://arxiv.org/pdf/2607.00596): DocLayout-YOLO with synthetic pretraining mAP50 0.847 versus 0.739 for default YOLOv11x; geometric reading-order methods struggle on irregular multi-column pages; an LLM comparing the ends of adjacent blocks cut order error sharply (Gemini 3.0 Flash Kendall tau 0.03). For FR's regular three-column grid this machinery is probably unnecessary; fixed column cropping suffices except on full-width tables.

## Tool blocks

### Gemini API (Gemini 3 Flash, 3.5 Flash, 3.1 Pro) for document images
- What: Google's multimodal models called by API; accept page images or PDFs and return transcription.
- Cost ([official pricing page](https://ai.google.dev/gemini-api/docs/pricing), fetched 2026-11-06, no date shown on page), per million tokens, standard / batch (batch = half price, results within 24 hours): Gemini 3 Flash preview $0.50 in, $3.00 out / $0.25, $1.50; Gemini 3.5 Flash $1.50, $9.00 / $0.75, $4.50; Gemini 3.1 Pro preview $2.00, $12.00 / $1.00, $6.00; 2.5 Flash-Lite $0.10, $0.40 standard. [Image token counts](https://ai.google.dev/gemini-api/docs/media-resolution): 1,120 per image at `high`, 2,240 at `ultra_high`; Google says `medium` saturates for ordinary PDFs. The docs also mention "Gemini 4"; I found no pricing or OCR numbers for it, so recheck before the pilot. My arithmetic, assuming 3,500 output tokens for a dense FR page: Gemini 3 Flash batch about $5.5 per 1,000 pages, 3.5 Flash batch about $17, 3.1 Pro batch about $22.
- Evidence: best single-vendor results on historical text in the studies above (Humphries handwriting; Luxembourg newspapers; "behaves like conventional OCR" in FaithC4). HN: a 1755 Portuguese registry where Mistral was unusable and Gemini Thinking got 70-80% right ([thread](https://hn.algolia.com/api/v1/items/46313390)); "best at OCR and document extraction so far" for insurance documents ([thread](https://hn.algolia.com/api/v1/items/49288889)); the OmniAI benchmark thread praised Gemini 2.0 Flash on cost ([thread](https://hn.algolia.com/api/v1/items/43118514)). Bad: skipped lines and weaker marginalia on handwriting (Humphries' commenters); one commenter saw Gemini keep inventing a folk tale on old Gaelic; "1.001E-04" for "1.001E-11" in an OCR Arena test ([thread](https://hn.algolia.com/api/v1/items/46006104)). Gemini Flash 2 scored only 57.8-63.8 on olmOCR-Bench, so older Flash versions are not evidence for the 3.x line.
- Fit: second voter on known-page crops, run as a batch from a GitHub Actions job (submit in one run, collect in another, because batches can take up to 24 hours and Actions jobs stop at 6). Needs an API key, a prompt that demands verbatim text with [illegible] markers, temperature 0, and a stored output hash.
- Verdict: **TRY (pilot)**. Best-supported candidate for a verbatim second reading; unmeasured on FR pages.

### Claude vision (Sonnet 5.5, Opus 5.5) as OCR
- What: Anthropic models reading page images.
- Cost ([pricing page](https://platform.claude.com/docs/en/about-claude/pricing), fetched 2026-11-06): Sonnet 5.5 $2 in / $10 out per million tokens ($1 / $5 batch); Opus 5.5 $4 / $20 ($2 / $10 batch); Haiku 5.5 $0.10 / $0.50 for prompts under 100k tokens. [Images](https://platform.claude.com/docs/en/build-with-claude/vision) cost ceil(w/28) x ceil(h/28) tokens; models from 4.7 on accept up to 2,576 px on the long edge (4,784 tokens). My arithmetic for a dense page on Sonnet 5.5 batch: about $22 per 1,000 pages; Opus 5.5 batch about $45.
- Evidence: Claude Opus 4.5 CER 4.28% against Gemini 3 Pro's 1.67% on Humphries' handwriting. No printed-page benchmark found. HN anecdotes: Claude "absolutely better" than Mistral OCR 4.0 and "dominated" one handwriting benchmark, but "Claude refuses to transcribe copyrighted or certain public-domain content and sometimes ends the turn with a content-filter error" ([thread](https://hn.algolia.com/api/v1/items/49288889)); a GPT-5 vs Opus test where GPT-5 invented the end of a cut-off sentence and Opus showed it truncated ([OCR Arena thread](https://hn.algolia.com/api/v1/items/46006104)). The refusal claim is anecdotal and the project's material is US government text, but test it before building around it.
- Fit: the project already pays for Claude sessions, so an Opus reviewer that looks at the image crop beside the candidate text is the natural adjudicator for disagreements between engines. Using it as the primary OCR is 4x the cost of Gemini 3 Flash for no measured gain.
- Verdict: **TRY (as adjudicator on disagreements only)**; not as bulk OCR.

### olmOCR (Allen AI), v0.4.0 / olmOCR 2
- What: open 7B VLM plus a pipeline that turns PDFs into plain text, trained with reinforcement learning on unit-test rewards; training data included 10 million scanned historical documents from the Internet Archive, Library of Congress and National Archives ([paper](https://aclanthology.org/2026.acl-demo.62.pdf)).
- Cost and maturity: Apache-2.0, 19.8k GitHub stars, v0.4.0 released 2025-10-21 ([repo](https://github.com/allenai/olmocr)). Needs an NVIDIA GPU with at least 12 GB VRAM (tested on RTX 4090, L40S, A100, H100) and 30 GB disk. Ai2 claims under $200 per million pages and 3,400 output tokens per second on one H100 with the FP8 weights ([blog](https://allenai.org/blog/olmocr-2)). Hosted endpoints listed in the README, per million tokens in/out: Cirrascale $0.07/$0.15, DeepInfra $0.09/$0.19, Parasail $0.10/$0.20. My arithmetic (about 1,500 image tokens in, 3,500 out) gives about $0.80 per 1,000 dense pages through DeepInfra, with no GPU administration.
- Evidence: 82.4 overall, 83.7 multi-column, 47.7 old scans. [HN, 313 points](https://hn.algolia.com/api/v1/items/43174298): one user called it "the only AI Vision toolkit so far that actually recognizes Latin and medieval scripts"; others reported dropped table rows and misaligned fields; the Marker developer disputed the benchmark and said olmOCR ran at about 0.4-4 pages per second on an H100 against 20-120 for Marker. Those speed numbers are for the first release.
- Fit: the cheapest open second voter, usable without owning a GPU through a hosted endpoint, and its training included the same kinds of archives (National Archives, LoC) the project reads. Does not return confidence scores.
- Verdict: **TRY (pilot)**. Best open candidate on cost and licensing.

### Chandra OCR 2 (Datalab)
- What: about 5B-parameter open OCR VLM (March 2026), outputs markdown, HTML or JSON with layout.
- Cost and maturity: 12.0k stars. Code Apache-2.0; weights under a modified OpenRAIL-M that is free for research, personal use and startups under $2M funding or revenue, and "cannot be used competitively with our API"; other commercial self-hosting needs a license ([repo](https://github.com/datalab-to/chandra), [model card](https://huggingface.co/datalab-to/chandra-ocr-2)). Throughput 1.44 pages per second on one H100 with vLLM (authors' figure), so about 5,200 pages per hour; at RunPod's H100 rates below that is roughly $0.50-0.80 per 1,000 typical pages, several times that for very dense pages. Datalab's hosted API price was not on the pages I opened.
- Evidence: highest open-weights old-scans score (51.1) and overall 85.8 in the vendor's own table. No independent reproduction found. It was among the models in the Uruguayan typewriter study, but I only have the abstract-level result that VLMs beat classical OCR on average, not a Chandra-specific number.
- Fit: second open voter from a different model family than olmOCR, so disagreements between the two are informative. License is fine for an academic project; confirm if the dataset or tooling is ever sold.
- Verdict: **TRY (pilot)**.

### Mistral OCR (3, 4, 4.1)
- What: Mistral's hosted OCR API. Weights not downloadable per an HN commenter; self-hosting is described as an enterprise offer.
- Cost: $4 per 1,000 pages, about $2 batch, for OCR 4 released 2026-06-23 per a secondary article ([DEV](https://dev.to/aarhamforensics_eb3c024eb/mistral-ocr-4-document-intelligence-pricing-api-competitor-comparison-knk)); HN commenters put OCR 4.1 at about 3.5 euros per 1,000 pages, and said price roughly doubled with each release ($1, then $2, then $4). Mistral's own pricing page did not list OCR rates when I opened it.
- Evidence: best text edit distance on OmniDocBench v1.0 (0.099) but weak on olmOCR-Bench old scans (29.3 for the 2025 API). HN reports on historical material are bad: 1755 Portuguese registry "butchered the whole text"; Danish historical text "wasn't even recognizably Danish"; Mistral OCR 4.0 "invented whole sentences mid-page" ([OCR 3 thread](https://hn.algolia.com/api/v1/items/46313390), [OCR 4.1 thread](https://hn.algolia.com/api/v1/items/49288889)). Good: handled a dense tabular handwritten form better than vision LLMs and Textract in one report; the OCR 1 thread has a user whose measured accuracy was 72.2% against Mistral's advertised 95% ([thread](https://hn.algolia.com/api/v1/items/43282905)).
- Fit: none beyond a third voter. A model that invents sentences is the wrong risk profile for verbatim quotation.
- Verdict: **SKIP** (revisit only if a pilot shows it winning on FR crops).

### Marker and Surya (Datalab)
- What: Marker is a PDF-to-markdown pipeline; Surya OCR 2 is a 0.65B VLM that does layout, reading order, OCR and tables.
- Cost and maturity: Surya code Apache-2.0, weights modified OpenRAIL-M (free for research and startups under $5M). RTX 5090 with vLLM: 5.35 pages per second; Apple Silicon: 0.108 pages per second ([model card](https://huggingface.co/datalab-to/surya-ocr-2)).
- Evidence: Surya OCR 2 83.3 overall, top under 3B parameters. Marker 1.10.1: 76.1 overall, 33.5 old scans, 80.0 multi-column. Surya had the best mean CER (8.87%) in the typewritten-microfilm study, though that was the earlier Surya-OCR, not version 2.
- Fit: Surya OCR 2 is the cheapest way to run a fast local model on a consumer GPU or one L4/L40S; useful if the project wants a high-volume pass. Marker is superseded by Chandra 2 for this purpose.
- Verdict: Surya OCR 2 **WATCH** (fold into the pilot only if there is spare effort); Marker **SKIP**.

### dots.ocr / dots.mocr (Xiaohongshu rednote-hilab)
- What: 1.7B (dots.ocr) and 3B (dots.mocr, renamed 2026-03-19) open OCR VLMs. MIT-licensed repo plus a separate license agreement file whose terms I could not read; 9.2k stars ([repo](https://github.com/rednote-hilab/dots.ocr)).
- Evidence: 79.1 (dots.ocr) and 83.9 (dots.mocr) overall on olmOCR-Bench, self-reported; old scans 40.9 for dots.ocr. An HN commenter claims about 3.8 seconds per page.
- Verdict: **WATCH**. Similar tier to olmOCR, no old-scans edge.

### PaddleOCR-VL / PaddleOCR-VL-1.5, GLM-OCR, DeepSeek-OCR 2, MinerU 2.5, Qwen3-VL
- What: open document models. PaddleOCR-VL-1.5 is 0.9B with a separate layout model (PP-DocLayoutV3); GLM-OCR and PaddleOCR-VL-1.5 lead OmniDocBench composite (94.62, 94.50); DeepSeek-OCR (MIT) scored 75.7 on olmOCR-Bench with the weakest multi-column result (66.4); MinerU is AGPL-3.0 per the olmOCR paper's license table; Qwen3-VL-4B scored 79.2 on olmOCR-Bench via CodeSOTA, and Qwen 3.6 had the best median CER on the typewritten microfilm.
- Evidence: leaders on modern-document benchmarks, no old-scans or 1936-1993 data. PaddleOCR-VL-1.5's robustness numbers on scanning and warping are the most relevant, and it is tiny (0.9B), so it runs on any 8-12 GB GPU. HN commenters call PaddleOCR, MinerU and Baidu's OCR "strong, cheaper options."
- Verdict: **WATCH**. Add PaddleOCR-VL-1.5 to the pilot only as a cheap extra voter.

### Hosted document services: Google Document AI, AWS Textract, Azure Document Intelligence
- Cost ([secondary comparison, updated 2026-09-17](https://imagetotable.ai/blog/google-vs-aws-vs-azure-ocr-2026)): basic OCR is about $1.50 per 1,000 pages at all three (Textract and Google drop to $0.60 per 1,000 at high volume); layout or table features cost $10-65 per 1,000.
- Evidence: the same source cites Textract falling to about 76% on low-quality scans and Azure about 96% on clean print; the OmniAI HN benchmark found traditional OCR stronger on dense pages than VLMs, with the best system about 91.7% and the worst about 60% on field extraction ([thread](https://hn.algolia.com/api/v1/items/43118514)). A commenter on the Mistral thread found Azure and Textract cost under half of Mistral 4.1.
- Fit: these are classical engines tuned for forms and modern print. They may match GPO's layer (which is probably a classical engine) but unlikely beat it on fractions and symbols. A third voter at $1.50 per 1,000 pages is nearly free, and a different engine family from both the VLMs and GPO's.
- Verdict: **WATCH**. Add Azure Read to the pilot only if cheap to wire; do not expect gains.

### LlamaParse, Reducto, Unstructured
- LlamaParse ([pricing page](https://developers.llamaindex.ai/python/cloud/general/pricing)): credits at $1.50 per 1,000 (pay as you go); Fast $1.50, Cost-effective $4.50, Agentic $15, Agentic Plus $37.50 per 1,000 pages. These wrap other models and add markup. I did not open Reducto or Unstructured pricing or find a historical-document evaluation for either. Reducto is described on its own marketing pages only.
- Verdict: **SKIP**. They sell RAG ingestion convenience; the project needs verbatim spans and can call the underlying models directly.

### Tesseract 5 and OCRmyPDF
- What: the classical open engine and a wrapper that adds a text layer to a PDF.
- Evidence: my test on the FR land-description crop (no better than GPO's layer); CER 20.9% on typewritten microfilm; 12.1% paragraph CER on Luxembourg newspapers; the Library of Congress still uses it with post-processing for Chronicling America. HN: "awful for scientific papers," poor reading order.
- Fit: free CPU voter that runs on GitHub Actions, useful only as a cheap tiebreaker and as the baseline in the pilot.
- Verdict: **WATCH** (baseline only).

### Transkribus, Kraken, eScriptorium (handwriting and typescript)
- Transkribus ([plans](https://www.transkribus.org/plans)): Scholar EUR 99 per year with 900 credits; handwriting recognition costs 1 credit per page, API jobs half; top-up 250 credits for EUR 59.50 (about EUR 0.24 per page). Humphries measured about 8% CER raw and about 3% CER after training on dozens of sample pages. HN commenters still recommend it for historical handwriting.
- Kraken ([repo](https://github.com/mittagessen/kraken)): Apache-2.0, 1.1k stars, trainable layout and recognition, ships print models but I found no typewriter model; eScriptorium is its web front end. Needs training data and hours of annotation per script.
- Fit: the project's handwriting is incidental (annotations, some pre-1937 material). Gemini 3 beat Transkribus on handwriting in Humphries' test at a fraction of the effort. Fine-tuning Kraken only makes sense if typescript EO microfilm turns out to be the bulk workload and general VLMs fail on it.
- Verdict: Transkribus **SKIP** for now; Kraken **WATCH**.

### Layout models for column segmentation (DocLayout-YOLO, PP-DocLayout, Surya layout)
- Evidence: DocLayout-YOLO mAP50 0.847 on Armenian newspapers after synthetic pretraining; the American Stories and SNEWPAPERS builders both report layout and reading order as the hard part of newspapers. FR pages are three regular columns with occasional full-width tables, so a fixed-grid column crop (whitespace profile with a page-by-page fallback) is far cheaper than a trained layout model. In my one-page test, a naive whitespace scan on the text layer found no clean gutters, so grid detection should run on the image, not on the layer's coordinates.
- Verdict: **SKIP** a trained layout model until column cropping demonstrably fails on a sample.

### Considered and rejected
- **GPT vision / GPT-5.x for OCR:** one HN comment says it "invented the end of a cut-off sentence"; Humphries measured an OpenAI model at 16.81% CER on handwriting; no printed-page data. Not worth a separate pilot arm.
- **Nougat, GOT-OCR 2.0:** built for arXiv-style papers and superseded on every benchmark above; no old-scan evidence.
- **Docling (IBM), Unstructured:** I found no number for either on olmOCR-Bench, OmniDocBench-style old-scan tests or historical material. They are parsing frameworks; treat as unmeasured.
- **Mistral OCR 3/4/4.1, Marker, Unsiloed, LlamaParse, Reducto:** see blocks above.
- **Training an in-domain model (the BnL approach):** about 2% CER came from 33,000 manually transcribed lines plus pseudo-labels. Only justified if the pilot finds a systematic failure class that prompts cannot fix.

## Running it cheaply

- **GitHub Actions:** CPU only, 6-hour job limit. Fine for submitting and collecting batch API jobs, cropping pages with OpenCV or pdfplumber, and running Tesseract. Do not try to run a VLM on it.
- **Hosted open-model endpoints (DeepInfra, Parasail, Cirrascale):** olmOCR runs against these with `pip install olmocr` (remote inference), so no GPU management at all; about $0.80 per 1,000 dense pages by my estimate.
- **Modal:** per-second billing; base rates about $1.95 per hour L40S and $3.95 per hour H100 as of July 2026 per a [secondary article](https://www.spheron.network/blog/modal-gpu-pricing-2026-per-second-billing/) (updated 2026-10-19; region pinning multiplies by 1.5-1.75; functions are preempted by default). Best when running Chandra 2 or Surya 2 from a script without owning a pod.
- **RunPod:** per-second billing, no commitment ([pricing page](https://www.runpod.io/gpu-cloud/pricing), updated 2026-11-04): L40S $1.09 per hour, RTX 4090 $0.89, A100 80GB $1.79, H100 PCIe $2.89 (community from $1.99), H100 SXM $3.99 (community from $2.69). An RTX 4090 or L40S meets olmOCR's 12 GB minimum, so a few thousand pages cost a few dollars.
- **Batch APIs:** Gemini and Claude batch are both half price, asynchronous, up to 24 hours. Use them for the pilot and any bulk pass.
- **Scale arithmetic (my estimates, 3,500 output tokens per dense page):** 1,000 pages cost about $5.5 (Gemini 3 Flash batch), $22 (Sonnet 5.5 batch or Gemini 3.1 Pro batch), $45 (Opus 5.5 batch), about $0.80 (olmOCR on DeepInfra), $1.50 (Azure/Textract/Google basic OCR). If the project ever re-OCRs a million pages, the spread is roughly $1,000 to $45,000, which is when model choice starts to matter.

## How to make re-OCR fit the project's evidence standard

- Treat a re-OCR as a new derived artifact: store the page image's sha256, the crop box, model id and version, prompt, sampling settings, and the output hash. Never re-run and overwrite; VLM output is not reproducible run to run (an HN commenter calls nondeterminism multimodal OCR's "biggest flaw").
- Pass crops, not whole pages: one column or one passage with a few lines of context, upscaled to what the source resolution supports (Claude's docs also advise pre-cropping because large images are downscaled; Claude's 2,576 px cap and Gemini's token tiers both reward cropping).
- Use at least two different-family engines plus the GPO layer as a third voter. Align them at the character level; accept text only where all agree, and send disagreements (fractions, numerals, section symbols, names) to an adjudicator that sees the image crop, with a human spot-check. The Uruguayan and FaithC4 papers both recommend targeted checks of names, dates and identifiers instead of whole-page CER, and several HN commenters suggest "run two systems and flag only disagreements."
- Require [illegible] markers and reject any output longer than the aligned source by more than a small margin (both the Uruguayan paper and HN reports describe invented additions).
- Reviewers in the claim kit should receive the image crop beside the candidate span, not text alone.

## Pilot design (about one day, under $30)

1. Sample about 60 passages across: FR 1936-1950, 1951-1970, 1971-1993; Statutes at Large; a typescript EO from the ProQuest or Commons slip volumes; Serial Set. Include at least 15 passages with land descriptions, fractions, tables or section symbols, since that is where GPO's layer fails.
2. Make gold transcriptions from the images (human, or Opus plus human check on the hard 15).
3. Run: GPO layer, Tesseract 5, olmOCR 2 (DeepInfra), Chandra 2 (RunPod L40S or Modal), Gemini 3 Flash batch, Gemini 3.5 Flash batch, Sonnet 5.5. Optionally PaddleOCR-VL-1.5 and Azure Read.
4. Score passage-level exact match, CER, and a separate count of errors in numerals, fractions, symbols and names. Count invented or dropped words separately.
5. Decision rule: adopt a two-engine plus GPO voting protocol if the best engine pair cuts exact-match failures on the hard passages by at least half versus the GPO layer and shows no invented text on the clean passages. Otherwise keep the GPO layer and spend the effort on custody.

## Ranked top 5 for this scope

1. **Run the pilot above** (a measurement, not a tool). No published number compares anything to GPO's layer; the one page I checked shows a specific, fixable failure.
2. **Gemini 3 Flash batch on column crops (TRY).** Best historical-text evidence of the hosted options, about $5.5 per 1,000 dense pages, simple batch workflow from Actions.
3. **olmOCR 2 through a hosted endpoint (TRY).** Apache-2.0, about $0.80 per 1,000 pages, trained on National Archives and LoC scans; no GPU administration.
4. **Chandra 2 on RunPod or Modal (TRY).** Highest open old-scans score (51.1, vendor-reported); different family from olmOCR, so disagreement is informative; license is fine for research.
5. **Claude Opus 5.5 as image-aware adjudicator of engine disagreements (TRY).** Uses the existing Claude workflow; test for content-filter refusals on transcription first.

Items 2-4 are voters, item 5 is the tiebreaker; none of them should replace the GPO layer as the held source without the voting protocol.

## Gaps in this research

- No VLM was run on project pages (no keys, no sign-ups); all VLM-versus-GPO claims are inferred.
- I could not open the govinfo original PDFs or the HN site directly (HN read through the Algolia mirror and a Vercel mirror, which may omit threads' later comments).
- Pricing for Datalab's API, Mistral OCR 4/4.1 (primary source), Reducto, Unstructured, and Gemini 4 was not found on primary pages.
- Several benchmark figures are vendor-reported or from aggregator pages (CodeSOTA) with mixed dates; marked where used.

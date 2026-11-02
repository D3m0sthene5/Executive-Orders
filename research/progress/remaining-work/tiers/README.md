# Job tiers — November 2, 2026

85 editorial assessments at main `b3fc50647cfc6f153ac2497ad2e172de69213295`: 82 workflow records plus two historical production families and one explicitly failed savings experiment. The assessment is within each role, using demonstrated outputs, integration and evidence quality; it is not a computed ROI score. Authority gates and unsupported outcomes are unranked. Historical results stay dated and overlap.

`JOB_TIERS.json` holds the judgments; `build_job_tiers.py` checks coverage and embeds the JSON into the existing dashboard source. Run the builder after changing ratings. Source facts and history for workflow jobs come from `../workflow/WORKFLOW_NODES.csv`. Extra assessments carry their own evidence records. The page renders text safely and links exact source pins.

The current main tracker reports 498 ready (306 original-supported, 192 transcription-dependent), 194 original replacements and 194 quotation rechecks. Its latest run finished October 31; `READINESS_BY_ORDER.csv` is the exact same Git blob as the October 30 dashboard input. Stage19 still records zero human-certified whole histories. Apollo's 254 filings and Erasmus's 52 filings (32 recovered rejects and 20 corrections) are later than that generation and cannot be added to it.

The October 29 audit is retained as historical evidence, not silently overwritten. Its stronger failure grades sometimes scored a production shortcut rather than all uses of the job. This assessment separates the tested compact-packet savings failure (F) from the broader working claim-kit workflow. Family-rule and Craigellachie conversion remain poor (D); missing prerequisites are not evidence that every possible future use fails.

The bounded read-only assessment worker used configured gpt-6-sol; exact tokens, active time and cash are unavailable. Root retained editorial judgments and integration. No new scientific production, status adoption, evidence-grade change or certification occurred.

Local QA uses an isolated temporary dataset host, not a new hosted dashboard. Syntax and six existing workflow-builder checks passed; search, evidence dialog, Escape and F filtering were exercised in a browser. Final publication and independent review status are recorded in the dated snapshot README. The real host requires one executable script: the builder now replaces comment-delimited JS literal data, not a separate application/json element. Final live page v15 passed all six tabs and new interactions.

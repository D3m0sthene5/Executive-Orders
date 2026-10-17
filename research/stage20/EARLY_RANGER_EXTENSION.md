# Stage 20 early-century source-excavation extension

The Stage 19 ranger has 1,041 source leads/survey cells and 3,403 planned query routes. The Stage 19 systematic *blank-year* survey covers only 1789–1800. That is an avoidable blind spot for the 1801–1861 period when bibliographic EO numbering begins in 1862.

This extension adds a **73-year audit grid** for 1789–1861, explicitly including the **61 previously unsurveyed years** 1801–1861. Each year has six different search families in `output/ARCHIVAL_SURVEY_ROUTES_1789_1861.csv`: LOC presidential correspondence, LOC “by command” publications, NARA recipient/department records, LOC printed ephemera, congressional reprints, and Internet Archive downstream institutional effects. The 438 routes are *planned*, not searched or successful.

Existing date hints are counted separately as unverified OCR, curated primary-source representations, and survey cells. A year with zero hits or leads remains **unknown**, not a historical count of zero. Humans or bounded research agents should run the routes, preserve result bytes and exact URLs, verify originals versus later transcriptions, differentiate secretary-signed by-command orders from independent agency instructions, and test same-date document splits.

`output/ARCHIVAL_COVERAGE_GRID.csv` and `output/ARCHIVAL_COVERAGE_WORKBENCH.html` prioritize the gaps without asserting new census members. Logs should include date, query, filters/pagination, bytes SHA-256 and explicit negative evidence limitations. The new workbench opens search URLs but never changes the census or legal status. `output/ARCHIVAL_GRID_SUMMARY.json` measures route generation; no live retrieval was attempted here.

Rebuild from repository root with Node 18+:

```sh
node research/stage20/code/extend_early_ranger.mjs
node research/stage20/code/extend_early_ranger.mjs --check
```

This extension complements, rather than silently altering, the Stage 19 ranger whose frozen 1,041/3,403 metrics and seven tests remain intact. Further automation should batch actual multi-repository requests with respectful limits, cache untouched responses by SHA-256, and log every attempted failure; an HTTP result cannot authenticate a legal instrument.

# Domesday register: every order the project knows was signed, and what it holds for each

> **Census audit, 2026-11-12** (Kean F-20261112-graunt-census-audit, `research/graunt-census-audit-2026-11-12/`): the numbered census is 29 catalog labels short (EO 36-49, 51-53, 92, 2103, 2539, 2703, 3493, 3733, 6585 and 130A, 2687A, 5151A, 7010F, 8606A, each with a cited source), and 1,405-1,816 unnumbered orders are individually identified. The `catalogued_unnumbered` capture-recapture interval in `UNNUMBERED_SUMMARY.json` is a model output, not a national estimate: Lord compiled from the same sources used as its second list, so the lists are not independent. Seeding the unnumbered series from the audit waits for owner ask A-20261112-graunt-unnumbered-seed.

One table, `output/REGISTER.csv`, with one row per order in the 14,972-order census: number, date, title and
president from the best index the project has; every source held by class (official original, archival replica
scan, compiled or volunteer transcription) and how many text files are on disk; the readiness tracker's
provisional status, `original_text` step and blockers; the ProQuest state (link supplied, PDF in the repository
with its SHA-256); Lewis's route, status and next action; Clark's class; and the best web page either tool has
found that names the order, with its score. `best_held` is the strongest class of document on file.

A second table, `output/CANDIDATES_NOT_IN_REGISTER.csv`, lists order numbers that are **not** in the census but
that something names: a number gap with index evidence, a citation in a saved text, a list page on the web, a page
read during a web search. Each row says who names it, the dates and titles seen beside it, and a strength. These
are leads for census intake (`jobs/census-candidates`, the Stage 15 identity layer) and never become register rows
on their own.

Like the Domesday survey it is named after, the register records what is held, not what is true: nothing here
authenticates an identity, assigns a custody grade or changes a readiness count. The census file stays the only
universe and the tracker the only count.

Runs daily and after `lewis-originals`, `clark-discovery` and `readiness-tracker` when they run together, so it
always shows their latest results. `job.py` runs `test_register.py` first. Locally:

```sh
REPO_ROOT=. OUTPUT_DIR=/tmp/domesday python jobs/domesday-register/job.py
```

# Domesday register: every order the project knows was signed, and what it holds for each

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

# app-transcriptions: American Presidency Project records in the pipeline's input shapes

`jobs/app-executive-orders/` harvests the American Presidency Project (APP) order pages, live and from
public web-archive captures. Its archive lane writes `MIRROR_FRAGMENTS.jsonl` and `MIRROR_SOURCES.jsonl`.
claim-kit discovers only `output/FRAGMENTS*.jsonl` and `output/SOURCES.jsonl`, and later-events reads
only a job's `output/SOURCES.jsonl`, so without this job about 9,400 archive-lane texts were invisible to the
pipeline. This job converts their shape; it never edits `jobs/app-executive-orders/` and never fetches anything.

## Outputs

| File | What it is |
| --- | --- |
| `FRAGMENTS.jsonl` | The archive-lane `original_representation` records, unchanged except that `data.text_path` points from this folder to the held APP text (`../../app-executive-orders/output/texts/...`). The live lane's `FRAGMENTS.jsonl` is already discovered by claim-kit and is not repeated. |
| `SOURCES.jsonl` | One source record per numbered order (live lane first, then the newest capture), for jobs that scan other jobs' `SOURCES.jsonl` texts (later-events). |
| `CATEGORIES.csv` | APP categories and attributes per page, one row per page. |
| `PROBLEMS.csv` | Records refused, with the reason (unnumbered pages naming no single order; a text file that holds another capture's text; a record not marked lead-only). |
| `SUMMARY.json` | Counts, refusals, category/attribute tables. |

## What it does not do

Every record stays what app-executive-orders made it: grade `mirror_transcription`, representation
`secondary_compilation_transcription`, `acceptable_as_original=false`. A record claiming anything else is
refused. An APP page is an editorial transcription read from the web or from an archive capture of the web:
historical-document discovery, not identity authentication, original custody or a legal finding. The
readiness tracker counts it as a lead only (`ONLY_COMPILED_TRANSCRIPTION_FOUND`); nothing here changes a
census, ledger, codebook or certified count.

## Running

`REPO_ROOT=. OUTPUT_DIR=jobs/app-transcriptions/output python jobs/app-transcriptions/job.py` (about 3 s;
runs `test_convert.py` first, including a round trip through claim-kit's real loader). Rerun it whenever
app-executive-orders commits new outputs: committed outputs do not trigger jobs.

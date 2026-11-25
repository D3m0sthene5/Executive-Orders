# montfaucon-m011-pages

Renders the PDF pages that a Montfaucon page check (batch m011) needs and pins them with SHA-256. It makes no judgement about page content and uses no model.

For each of the 58 source PDFs in `plan.json` (57 govinfo Federal Register daily issues, 1937-1994, and the 1911 Isthmian Canal Commission compilation held in Git LFS) the job:

1. downloads the PDF with 4 worker processes (`JOB_WORKERS` overrides), or pulls the LFS file `releases/source_books/Isthmian_...pdf`;
2. checks the file's SHA-256 against the value pinned in the register fragment; on mismatch it renders nothing and records the actual hash in `MANIFEST.json` (`status: sha_mismatch`);
3. renders each listed PDF page (the cited pages plus one neighbor each side) to JPEG, 1800 px tall, quality 75, the same convention as `research/montfaucon/images/`;
4. writes `images/<source-id>/page-NNN.jpg` and `MANIFEST.json` (per image: sha256, bytes, size, `image_url` = source URL + `#page=N`; per source: status, bytes, actual sha256, timings, orders served).

Negative statuses (`download_failed`, `sha_mismatch`, `error`) are results, not job failures. Stop-in-time: no new source starts after `runner_limits.past_safe_stop()`.

Estimated run: 2.04 GB across 58 sources (largest 339 MB), 252 images (about 100 MB of JPEG). Download at the measured parallel rate of 45 MB/s takes under 1 minute; at one stream (3.5 MB/s) it would take about 10 minutes; at an assumed 10 MB/s about 4 minutes. Rendering measured locally at 0.06-0.24 s per page: about 1 minute. Expect 5-15 minutes in total. Unmeasured: govinfo's rate for large issue PDFs from the runner.

Output goes to `jobs/montfaucon-m011-pages/output/`. The coordinator then copies images to `research/montfaucon/images/m011/` (about 100 MB; commit size matters) and pins them in the records.

Local test: `JOB_LOCAL_SOURCES=<json of url->local path>` substitutes local files for downloads (used to test with cached PDFs).

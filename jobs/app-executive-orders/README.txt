American Presidency Project (APP) executive-order harvest

Explicit local invocation only; no job.py, so pushing does not start a GitHub
run (a runner and a local PC must never crawl APP at the same time).

Source: https://www.presidency.ucsb.edu/documents/app-categories/written-presidential-orders/presidential/executive-orders
        https://www.presidency.ucsb.edu/statistics/data/executive-orders

Politeness: APP's robots.txt asks every crawler for Crawl-delay: 10 and warns
about site stability. app_harvest.py uses the shared FetchPool with one worker
and >= 10 s between requests, identifies itself as EO-Historical-Research/1.0,
and stops (no retry) on 401/403/408/425/429/5xx, Retry-After, a challenge
page or a response slower than 60 s. Do not parallelise requests to APP;
parallel work belongs downstream (matching, review). Rerunning resumes.

Phases (run from the repo root; --cache-dir holds raw pages, not committed):
  python jobs/app-executive-orders/app_harvest.py statistics --download --cache-dir <dir>
  python jobs/app-executive-orders/app_harvest.py index      --download --cache-dir <dir>
  python jobs/app-executive-orders/app_harvest.py documents  --download --cache-dir <dir> [--ids-file data/PRIORITY.txt] [--max-new N]
Offline: python jobs/app-executive-orders/test_app_harvest.py
         python jobs/app-executive-orders/app_harvest.py parse-test <saved.html>...

Timing: statistics 1 request; index about 110 requests (about 18 min);
documents one request per order (about 10,900; about 30 h at 10 s). Stop
with Ctrl-C at any time; the next run skips everything already saved.

Archive lane (app_mirror.py): most APP order pages were captured by Common
Crawl (2025 and earlier crawls; APP's robots.txt now disallows CCBot, so 2026
crawls hold nothing) and by the Wayback Machine. Reading those captures loads
the archives, not APP, so this lane runs several workers and finishes in
minutes. It never sends a request to APP.
  python jobs/app-executive-orders/app_mirror.py cc-index      --download --cache-dir <dir> [--crawls 32]
  python jobs/app-executive-orders/app_mirror.py wayback-index --download --cache-dir <dir>
  python jobs/app-executive-orders/app_mirror.py documents     --download --cache-dir <dir> [--ids-file data/PRIORITY.txt] [--workers 4]
It walks the queue in the opposite order to the live lane and re-reads
DOCUMENTS.jsonl every minute, so both can run at once. Afterwards rerun the
live documents phase with --audit-every 50: it skips every path in
MIRROR_DOCUMENTS.jsonl except every 50th, which it fetches live and compares
in MIRROR_AUDIT.jsonl (text and page hash agreement, capture date), so the
captures carry a measured staleness rate. A capture is the APP page as of
its capture date; every record names the archive, crawl and capture date.

output/
  STATISTICS.json/.csv     APP table "Executive Orders by President" plus its
                           methodology text, notes, sources and last-updated
                           date. Editorial counts (pre-1945 include unnumbered
                           orders): a comparison source, not a census finding.
  STATISTICS_PAGE.txt      the whole statistics page as text.
  INDEX.jsonl/.csv         every listed document: instrument_id (EO:<n>[suffix]
                           or null when unnumbered), date, title, president,
                           APP path/URL, listing page.  INDEX_SUMMARY.json counts
                           and per-page SHA-256.
  DOCUMENTS.jsonl          per order page: heading, date, president and byline,
                           APP footnote (often the Federal Register publication
                           note), APP citation and node, categories, attributes,
                           raw page SHA-256, text path/hash.
  texts/<slug>.txt         full order text (UTF-8, LF), APP footnote excluded.
  SOURCES.jsonl            source records (route mirror/american-presidency-project).
  FRAGMENTS.jsonl          claim-kit producer records for numbered orders, only
                           when listing and page headings agree on the number.
  STATE.json, ATTEMPTS.jsonl, FAILURES.jsonl   progress and individual failures.
  MIRROR_INDEX.jsonl       one capture per path and archive (crawl, timestamp,
                           WARC file/offset/length or Wayback timestamp).
  MIRROR_DOCUMENTS/SOURCES/FRAGMENTS/ATTEMPTS/FAILURES.jsonl, MIRROR_STATE.json
                           the archive lane's records, same shape as the live
                           lane's plus route archive/<archive> and a capture
                           block (archive, crawl, captured_utc, WARC record).
  MIRROR_AUDIT.jsonl       live-vs-capture comparisons for the audit sample.
  MIRROR_AUDIT_SUMMARY.md  the audit result (method, agreement by archive and
                           capture year, disagreements if any).
  texts/<slug>.live.txt    live text of an audited page (the capture's text
                           stays in texts/<slug>.txt).

Every representation is grade mirror_transcription, representation_type
secondary_compilation_transcription, acceptable_as_original=false. APP is an
editorial compilation: it is historical-document discovery, not identity
authentication, and asserts no legal status. Nothing here changes census,
ledger, codebook or the certified whole-lifecycle count.

Wikisource volunteer-transcription acquisition

Explicit local invocation only; no scheduled job.py, trigger, or status update.
The fixed data/PLAN.json comes from the successful collection title inventory
and exactly matches the 1,639 IDs in research/pre-1937-sources/COVERAGE.json.

harvest.py orchestrates the existing FetchPool and source-ladder extract_text /
write_text_lf functions. It requires their exact tested hashes, one worker,
one request at a time, at least one second between starts, and robots rules.
Only en.wikisource.org is allowed. No API, alternate site, retry, or backoff.
Blocking/throttling, Retry-After, a server error, or a response exceeding 20
seconds stops acquisition. The first 200 new order requests must have no more
than 40 failures. Cached pilot pages are reused without hiding new failures.

Example first gate:
python jobs/wikisource-texts/harvest.py --download --seed-pilot --max-new 200 --cache-dir /path/to/cache
Continue only after checking output/STATE.json and the stop conditions:
python jobs/wikisource-texts/harvest.py --download --cache-dir /path/to/cache

output/texts/ contains UTF-8 LF plain text. output/originals/ retains the exact
HTML response. SOURCES.jsonl preserves page and revision URLs, source/text
hashes, acquisition times, and volunteer-transcription labels. FRAGMENTS.jsonl
uses the normal producer schema discovered by claim-kit's existing loader.
Every representation has acceptable_as_original=false and mirror_transcription
grade; no legal status, authoritative original, or legal conclusion is asserted.
ATTEMPTS.jsonl and FAILURES.jsonl preserve individual failures. STATE.json is
acquisition progress only, not an order-status record. A prior site/quality
stop prevents resumption. The supplied extractor's headings and notes remain.

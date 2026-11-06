# Owner ruling, 2026-11-05: Brave Search API is paid, so use it only when needed

**What the owner said (in chat, 23:00–23:09 ET):** he bought about $29 of Brave Search API credit and asked for it to be wired in
"but be judicious in its use since its paid per query. like only use it if you need to use it". He then added the repository
secret `BRAVE_SEARCH_KEY` himself ("just did it"). The key was never written into the repository or any log.

**What this means for the tools**

- Brave's price is about $4–5 per 1,000 queries, so the credit covers roughly 5,800–7,000 queries.
- `jobs/_lib/eo_websearch.py` marks every keyed, billed engine `paid` (brave_api; also google_cse, bing_api, serpapi_google
  if keys are ever added). For each search step the free engines run first. A paid engine is asked only when they found
  nothing worth reading.
- Caps: 100 paid queries per job run, 2,500 per job over its lifetime, and 5,000 across every job ledger in the checkout
  (env `EO_PAID_SEARCHES_PER_RUN`, `_PER_JOB`, `_TOTAL`). Each run writes `output/PAID_SEARCH.json`, which carries the count forward.
- Secret values are redacted from every logged URL and error.
- Do not raise the caps or add other paid consumers without asking the owner.

# Historical gate evidence

`forecasts.jsonl` is an exact byte copy of `jobs/llull/ledger/forecasts.jsonl`
at commit `835f58d2ede7d93b80904bbd5ad1b876554f5201` (original PR #44).
Its SHA-256 is `4969c431a71f67bb3db9c5dafef63e4d9d4efeed7aa5a665a1f927a9d0902920`,
the hash already sealed in the historical Lambertini gate observation.

The merged live ledger contains later forecasts. The validation replays the old
gate against its original evidence in a temporary directory outside the checkout,
records the current/historical comparison, and still requires exactly the original
stopped, untested receipt. It never changes the live ledger, historical observation
or gate thresholds. This snapshot is not a new preregistration or a current result.

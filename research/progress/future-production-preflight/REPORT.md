# Check sources and frozen inputs before production dispatch

Base: main `600ae3018f71025b3e53dc8538b8f92e6e159b76`.

The active Tribonian run reported source-byte gaps after review (23 of 29 o04
claims awaiting custody) and nine packets invalidated by a new shared ruling.
Its producer prompt also warns of 10–30 minute deterministic apply/check waits.
These observations motivate preventing avoidable assignments and model polling;
they do not measure a token-saving percentage. Existing slim views, shared family
briefs, source acquisition, semantic checkpoint/resume, and Geddes telemetry
already exist and are retained rather than replaced.

## Existing gap and repair

`batch.prepare` already recorded held text/span diagnostics but explicitly left
raw custody to the actual checker; preparation could return success before a
producer encountered missing raw bytes. Ordinary preparation now emits a
`DISPATCH_CHECK.json` with mandatory-source blockers, optional source gaps,
explicit member lists, exact packet/code pins, source-index coverage notes,
unique-check counts and machine duration. The CLI returns nonzero when any
mandatory source is unusable. `--research-only` deliberately exports the same
blocked packet for acquisition/research, without production eligibility.

`kit.py dispatch-check` reuses the existing packet/source/research/Valla
freshness checks plus the same runtime-pin validator as `apply`. Re-run it
immediately before each explicit producer assignment. It checks required
original/inventory source custody through the actual checker's unchanged status
policy; the only checker API extension is `allow_download=False`, which bypasses
live/archive fallback regardless of global download-budget state. One source
index and deduplicated reference checks serve a packet. It rehashes required
text and verifies exact spans. No source catalogue, claim, request, reservation,
status, review or certification is written by the screen.

Mixed packets retain every member; explicit repeated `--order` selects which
members are being assigned while the entire seal/context remains checked.
Optional actor/current-law/contrary leads remain diagnostics, not mandatory legal
choices. Provisional working texts remain researchable with their disclosures;
source screening authenticates no original and approves no inventory or law.
Every source actually selected later still needs the full ordinary claim checks,
independent review and completion. Missing later evidence remains a real block.

The operator protocol now requires a fresh screen, stable inputs during a wave,
existing checkpoint/resume for unchanged blocks, deterministic waits without
model polling, and existing Geddes token/cost reporting with an explicit roster.
There is no model-launcher endpoint in this repository to intercept: preparation
is automatically screened, while the immediate pre-launch recheck is an explicit
coordinator obligation. Low-level Python callers must inspect the returned gate.

## Validation and limits

- Claim-kit suite: 536 reported test cases, 70.711 seconds, success with 7 skips.
- Claim-checker suite: 69 reported test cases, 2.967 seconds, success.
- Eleven new dispatch regressions use native build/prepare/freshness and actual
  custody code in bounded synthetic repositories: missing/corrupt raw bytes,
  retained exact bytes reopening work, packet/text/runtime/ruling changes,
  mixed/subset behavior, optional gaps, provisional texts, network refusal,
  no repository writes, and immutable/contained receipts.
- Separate-context OpenAI engineering review: seven further probes, approval,
  exact code hashes in `INDEPENDENT_REVIEW.json`. This is engineering review,
  not independent human or different-family scientific certification.

Reproduce from the repo root with `python3 -m unittest discover -s jobs/claim-kit
-p 'test_*.py' -q` and `python3 -m unittest discover -s jobs/claim-checker
-p 'test_*.py' -q`. Logs and final code checksums are retained alongside this
report. Historical failed local batch tests were missing sparse Valla fixtures;
materializing the declared fixture corrected the environment without runtime
changes. An attempted `python3 -I jobs/claim-kit/kit.py` invocation exposed its
existing isolated-mode sibling-import limitation; documented commands use
ordinary Python, as the existing batch protocol does.

The full-corpus source-index overhead and end-to-end token savings are unmeasured.
Root/worker token usage, cash and complete active labor are unavailable, not zero.
The receipt is point-in-time evidence, not a persistent dispatch authorization.
No model API was called by this screen; `model_tokens` remains null rather than
invented metering. Existing telemetry's missing-usage coverage must be inspected
before treating zero transcript totals as measured zero usage.

## Production isolation and integration

Work is on a separate branch from main, without altering or fetching into the
active Tribonian workspace. No current packet, source, claim, generated output,
codebook or human review is edited. The code-bearing publication is marked
`[skip actions]` to avoid starting compiler/acquisition jobs; a later metadata-only
PR update can trigger existing read-only tests without a job-folder push.

Keep this PR unmerged while the current run depends on its frozen runtime.
Changes to batch.py deliberately invalidate packets when integrated; that guard
must not be waived. After the current wave finishes, reconcile with the final
Tribonian checker changes, rerun combined tests, merge through ordinary review,
then prepare fresh future-run packets. Do not cherry-pick this runtime into the
ongoing run or renew old packet hashes. No automatic production launch or GPU
migration is part of this repair.

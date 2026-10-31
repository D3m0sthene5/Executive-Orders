# Lachmann

Named for Karl Lachmann, who established texts by collating independent witnesses. This job collates the held
working texts of every order whose original-text step is still open because only a compiled transcription or the
owner's ProQuest replica scan is held, and records a conservative machine confirmation (right order, complete
text, pages checked) pinned to the exact fragment.

A confirmation is a working-text confirmation under `research/readiness/owner_rulings/2026-10-31-jacquard-and-working-texts.md`
(quoted by path, not read). It never authenticates an original: every record carries `acceptable_as_original: false`
and the standing note from `jobs/claim-kit/working_text.py`, and the tracker may count the result only as a
provisional text step, separately from an original.

## Scope

Tracker rows (`jobs/readiness-tracker/output/READINESS_BY_ORDER.csv`) with `step_original_text = open` and blocker
`ONLY_COMPILED_TRANSCRIPTION_FOUND` or `ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK`, excluding any row that also carries
`ORIGINAL_FOUND_NEEDS_PAGE_CHECK`. Identity references: `jobs/domesday-register/output/REGISTER.csv` and the Pinakes
`ORDERS.csv` / `INVENTORY.csv`.

## Method

Witnesses are the fragment declarations that `working_text.Index` loads (read-only import) for the order, with a grade in
`working_text.GRADES`, an existing text file, and bytes that hash to `text_sha256`. Others are skipped and counted.
Producer wrappers (comment headers, Wikisource page chrome) are removed before any test, because they name the order.
One representation is chosen: government_printed_copy, machine_read_government_printed_copy,
government_printed_reproduction, archival_replica_scan_pending_codebook, compiled_transcription, mirror_transcription,
compiled_transcription_lead; ties go to the longest text.

- **identity_confirmed**: (a) the chosen text names the register number as an order number and the register's full date
  appears; or (b) an unnumbered order whose date appears, whose title-word overlap is at least 0.6 and which has an
  agreeing independent witness; or (c) an agreeing independent witness satisfies (a); or (d) "source heading", for the
  chosen text of an American Presidency Project page (producers app-executive-orders, app-transcriptions) or a Wikisource
  page (wikisource-texts) whose own heading record names "Executive Order" with exactly this order's number (and letter
  suffix): the APP page record's heading in `DOCUMENTS.jsonl` / `MIRROR_DOCUMENTS.jsonl` (same instrument, sha256 and
  `text_sha256` as the witness), or the Wikisource page title line that `body_of` strips as chrome. The register is never
  the source of the heading. Route (d) also needs the register's full date in the body, title-word overlap of at least
  0.6 between the register title and either the first 600 characters of the body or the heading, and no heading of
  another order in the body. Routes are tried in the order (a), (c), (d), so earlier confirmations keep their route.
  Evidence records `identity_route: "source_heading"` and `source_heading` (at most 120 characters).
- **complete_text_confirmed**: the text opens with the order (number heading, the register date, or title words; for
  unnumbered orders a recognizable opening), has a closing cue in its last 500 characters (a president's name on its own
  line, THE WHITE HOUSE, or a short dated line past 30 percent of the text) and no heading of a different order after the
  first cue; or an agreeing independent witness passes that test.
- With route (d), the start test has one alternative rule: the first 400 characters hold the register date or have
  title overlap of at least 0.6 with the register title. For numbered orders this is already one of the ordinary start
  tests, so it adds no confirmations by itself; all other completeness checks apply unchanged.
- **Agreement**: word 3-gram Jaccard at least 0.80 and normalized length ratio between 0.85 and 1.15. Independent means a
  different `produced_by`, `sha256` and `text_sha256`. Independence is by hash and producer, not provenance: a
  Wikisource page that copied the APP text still counts as independent here.
- **pages_confirmed**: null unless a matched fragment requires a page check. ProQuest: the PDF is the per-order Pinakes file
  (ORDERS and INVENTORY agree on instrument and sha256), page count known, text non-empty and not flagged low quality or
  probably handwritten, and the number (or date) is in the first 1,500 characters. No per-page text is held, so the
  fallback in the brief is used. American Presidency Project texts: the page record in `DOCUMENTS.jsonl` or
  `MIRROR_DOCUMENTS.jsonl` with the same sha256 has a heading naming the number, the register date, the held `text_sha256`,
  and subject words found in the text (the check in `jobs/claim-kit/AGENT_PROTOCOL.md`). Other producers have no page rule
  and stay false, so a Wikisource text that requires a page check stays unconfirmed even when route (d) holds.
- A partial register date (year only or year and month) cannot be matched and fails with `identity:register_date_incomplete`.

## Outputs

`CONFIRMATIONS.jsonl` (one line per in-scope order, schema `eo-lachmann-confirmation/v1`), `RESIDUAL.csv` (orders not
confirmed, with reasons, for agent review), `SUMMARY.json`, `tests.txt`.

## Blinded audit sample

```
python3 jobs/lachmann/lachmann.py audit-sample --confirmations OUT/CONFIRMATIONS.jsonl \
    --packets DIR/packets --key DIR/keys/KEY.json [--n 59] [--seed lachmann-2026-10-31] \
    [--only-route source_heading] [--exclude-from KEY1.json KEY2.json ...]
```

`--only-route` restricts the pool (genuine items, defect sources and donors) to confirmations with that identity route.
`--exclude-from` takes earlier key files and leaves out the instrument ids of their genuine (non-defect) items.

Draws `n` confirmed orders (deterministic from the seed) plus `max(4, round(0.08 n))` extra defective items, half a header
over another confirmed order's text (same year when possible) and half a text cut to its first 60 percent. Packets hold an
opaque item id, the register's number, date and title, the wrapper-free text and a page count (ProQuest only). The key file
must lie outside the packet directory. Items are drawn only from confirmed orders whose text and title contain none of the
words a reviewer must not see, so every packet passes the leak check that the command runs.

## Run

`OUTPUT_DIR=... REPO_ROOT=... python3 jobs/lachmann/job.py` (runs the tests first). Standard library only, about 15 seconds.

# Owner rulings given with the Photius prompt (2026-11-06 evening), as recorded in Kean

Source: the owner's prompt "Photius: close the originals hole for EO 1–7315", sections "Authority", "The facts this
session rests on" (F1–F7) and "Rulings (record as D-20261106-photius-*)". The owner is present but will not answer
questions; the session holds full merge permission on `main`, including count-changing pull requests, on condition
that each count-changing merge records before, after and PR number in Kean before the next merge. Every open question
is decided by the rule: advance the goals, stay reversible by a later PR, never change codebook text or the
human-certified count (0). Decisions the prompt did not make are marked "owner-delegated, reversible".

## Rulings in the prompt

- **R37 Official printing.** A full-text printing of an order in an official government publication (GPO slip, GPO
  bound volume, Serial Set document, departmental compilation printed by the GPO or the department, the Official U.S.
  Bulletin) is an official original witness of grade `official_printing`, equal to Mabillon's held-printing grade,
  once a page check confirms the order number or dateline and the signature block. A page check may be performed by an
  Opus worker reading the page image or text layer, recorded with the page reference; a human page check is not
  required for provisional status. This changes no codebook text; it applies the codebook's existing printing grade to
  sources it had not been applied to.
- **R38 Microfilm witness.** The LC/NARA film of the numbered series (HeinOnline title "Presidential Executive Orders",
  NARA M1118) is an official witness of the State Department file copy. An order whose only witness is the film is
  `microfilm_pending` until the project holds M1118 bytes; a HeinOnline page viewed by the owner may be recorded as a
  page-check fact (number, date, signatory, first and last words) but never as held bytes.
- **R39.** Mabillon's `none` / "signed original at NARA, not digitized, only witness" route is withdrawn for every
  numbered order 1–7403; those rows become `microfilm_pending` (R38) or move to a printing route found tonight.
- **R40.** Free sources in F6 (Internet Archive items) are admitted as routes; HathiTrust login-gated volumes in F6 are
  owner downloads, listed for him, never fetched by automation (robots and the project's standing stop).
- **R41.** Nothing tonight changes any provisional status, the certified count (0), or the codebook text. Readiness
  may change only through the text step; every count movement is recorded.

## Standing limits restated in the prompt

- No script, worker, fetcher or browser automation touches heinonline.org or access.heinonline.com, ever. Nothing from
  Hein is placed in the public repository; bytes stay in `research/owner-inbox/` (ignored by git) or the private data
  repo; only hashes, page references and extracted facts go public.
- Google-digitized HathiTrust PDFs (the twelve GPO volumes) stay private the same way; extracted text and hashes go
  public.
- Nothing under `ProQuest Pre-1937 Orders/`, `research/pre-1937-sources/ProQuest*` or `jobs/pinakes-proquest-ingest/`
  is touched. No history rewrite.
- A Hein-dependent closure is never described as public-domain custody; that label belongs to M1118.

## Decisions this session made under the delegation (owner-delegated, reversible)

- **P1 Workers run through the Agent tool, not `claude -p`.** The desktop-app CLI reports "Not logged in" for
  headless runs on this PC (its auth is supplied by the app to the attended session only). Workers therefore run as
  in-session subagents with the model chosen per task (Opus for grading and page checks, Sonnet for parsing and
  alignment), fresh context each, at most twelve at once. Model, tokens, tool uses and wall seconds are recorded in
  `research/photius/WORKERS.csv` from the harness's per-agent usage line.
- **P2 Private bytes location.** `research/owner-inbox/` is added to `.gitignore`; the twelve GPO PDFs sit in
  `research/owner-inbox/hathi-gpo/` with `SHA256SUMS.txt` and `MANIFEST.json`; the public manifest (htid, range,
  pages, sha256, rights, URL) is `jobs/photius-gpo-volumes/data/VOLUMES.json`.
- **P3 Registration shape.** Lane outputs are producer `FRAGMENTS.jsonl` files in the schema the tracker already reads;
  `needs_page_check: false` only after the identity test and the page check both pass; `acceptable_as_original`
  stays `false` on every record (a printing or a checked replica is a witness, not an authenticated signed original).
  Registration in `jobs/readiness-tracker/tracker.py` happens in the count-changing PR of each lane.
- **P4 Checked replica credit.** A ProQuest replica that passes the Lane 4 check is written with grade
  `archival_replica_checked` and credits the original-text step; the tracker row carries the informational flag
  `REPLICA_CHECKED_PROQUEST_BYTES` so the ProQuest dependence stays visible until M1118 or the owner's Hein facts
  re-point it.
- **P5 M1118.** The 2026-10-19 rule against planning around a reel set is superseded for M1118 by F4 of this prompt
  (the public-domain witness copy the project will hold); NYU Film 709 and HeinOnline remain under the Dagron ask and
  the Hein rules above.

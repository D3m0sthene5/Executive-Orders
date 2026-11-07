# Encyclopédie campaign report

Coordinator: Claude Opus 5.5, desktop session on the owner's PC, 2026-11-06 22:00 UTC to 2026-11-07. Campaign log:
`LOG.md` beside this file. Owner rulings: `research/readiness/owner_rulings/2026-11-06-encyclopedie-campaign.md`.
Nothing here changes a status, the codebook, the census or the certified count (still 0).

## Conclusions first

1. **The repository's growth is stopped at its two largest sources, and raw bytes are moving out of git.**
   - Ptolemy is paused: it had committed 2.17 GiB of raw source bytes since 2026-11-05.
   - Failed job runs no longer commit their whole output (PR #188, merged): about 740 MB on 2026-11-06 alone.
   - A byte store outside git (Pergamon: GitHub Release assets now, Cloudflare R2 by configuration later) holds all
     3,691 Ptolemy and Selden raw files (3.18 GB), each re-downloaded without a token and matched to its SHA-256; the
     manifest is in git (`storage/PERGAMON_MANIFEST.jsonl`). Only a history rewrite, which the owner decides, shrinks the
     repository itself.
   - GitHub's 10 GB figure is a recommended limit; the enforced limits are 2 GB per push and 100 MB per file.
2. **The thesis has evidence, but not yet a rate.**
   - 59 orders were formally revoked after an evidenced earlier end of operative force. For 34 of them, the official
     texts on both sides are held and hash-verified. Gaps run from 31 days to 24.8 years.
   - That proves the pattern exists. It does not show it is common: in 59% of the 810 formally revoked orders with filed
     claims, the revocation itself was the end.
   - The better-supported half of the thesis is the converse: 1,135 orders stopped operating and were never formally
     revoked.
3. **Prior art is integrated and cited, and it is not independent of the project.**
   - Thrower's 2017 list agrees with the project's formal revocations on 1,578 orders. Both derive from the same Office
     of the Federal Register notes.
   - Lowande and Poznansky's 2024 baseline reproduces, but their deposit has no order numbers and their error cases are
     not public; a request email is drafted.
   - Both datasets are cited separately from their articles in `research/REFERENCES.md`.
4. **A reviewer from a different model family is complementary.**
   - Codex caught 8 of 8 planted controls; Claude reviewers caught 17 of 22 reviewer-control pairs.
   - Codex caught every control that some Claude reviewer missed, at no metered cost.
   - The sample is too small for a rate, and the filing rule is unchanged.
5. **Free sources cover most of what licensed databases would give.**
   - govinfo has the Federal Register from 1936 to 2026, the Statutes at Large, the Serial Set (1817-1998) and the bound
     Congressional Record, free.
   - The Library of Congress copies of pre-1996 CFR and the U.S. Code tables are HeinOnline scans with a no-bulk term,
     so their use is an owner decision.
   - No free editorial citator exists. The CourtListener job derives one from bulk case text.
6. **Costs are now measured in dollars.** Bentham's price table is about twice too high (Tribonian: 419 USD, not 815).
   Scripted `claude -p` under the owner's plan draws on plan limits, not metered dollars. The campaign spent 0 of its
   100 USD API ceiling.

## What shipped (merged to main unless noted)

| PR | Stream | What it gives the project |
|---|---|---|
| #188 | Runner | Failed-run receipts kept small; large files go to the 90-day run download with their SHA-256 |
| #189 | Kean leases | `jobs/kean/lease.py`: atomic claims on a shared `kean-leases` branch; `kit.py dispatch-check` refuses a batch another holder leases |
| #190 | Hollerith | Driver scripts for claim-kit stages (schema, caps, cost log, mechanical blinding; 33 tests); sourced billing facts |
| #191 | Necker | Dollar cost per worker and per batch at list prices, checked against the CLI's own totals |
| #192 | Bodley | Zenodo release design (about 33 files, 27 MiB; certified = 0 stated four ways); nothing published |
| #193 | Playfair | Observable Framework trial for one site section; the site is on Vercel (about 759 MiB) |
| #195 | Nihil obstat | Human certifier page (byte-span highlighting, in-browser SHA-256, Krippendorff's alpha) and a costed NYU recruiting plan |
| #196 | Naudé | Survey of 27 free routes to material otherwise in licensed databases |
| #200, #202 | Bayle | Lowande-Poznansky and Thrower integration, corrected after an independent check |
| #201 | Thesis measure | The report summarized in conclusion 2, and a proposed tracker fix |
| #203 | Ventris | OCR pilot: 58 passages, 6 readers, the owner's reference worksheet |
| #204 | Pergamon | Byte store, byte budget, Ptolemy routing (not live) |
| #205 | Septuagint | Cross-family reviewer pilot |
| #206 | Runner | `COURTLISTENER_TOKEN` and `API_DATA_GOV_KEY` reach jobs (owner merged) |
| #208 | Fix | Formulario's missing trigger, which had kept main's road tests red since PR #184 |
| #209 | Integration | This log, the owner rulings, Kean records, references |
| #210 | Dashboard | Every tab of the remaining-work dashboard refreshed on current main; new Trajectory tab; 33 tools added (79 tools, 118 tier ratings, 115 workflow nodes) |
| #211 | Repetita | LSA 1997-2026: 357 issues, 16,396 Title 3 and EO rows (696 revocation, supersession or termination entries), 5,104 later-event leads, controls 0 errors; pre-1997 manifest of 471 sources |
| #213 | Fix | Repetita's missing trigger (road test) |
| #214 | Duodecim | U.S. Code Table IV, 16 editions 2009-2025: 46,954 EO rows, 2,909 orders, 1,391 with an Elim. marker (leads only); joined to current-law notes; 96 controls, 0 errors |
| #217 | Youngstown | Derived citator from CourtListener's public bulk opinions: 14,203 opinions cite register orders; 19,867 order-case pairs over 2,541 orders; 865 with an enjoined, vacated or invalidated holding cue; all 8 planted opinions recalled |

Every campaign PR is merged except #207, closed unmerged because it would have deleted files. The two dashboards
(https://claude.ai/artifact/531KGTebdrgdeUitKhp8du and https://claude.ai/artifact/BZJxATqRtwrtBbuBy2UZpc) are refreshed.

## Measured results

- **Repository:** 9,751,377 KB on GitHub (2026-11-07).
  - Main added 85,531 blobs (4.37 GiB packed) between 2026-11-05 and 2026-11-06.
  - Top sources: Ptolemy 2.17 GiB, failed-run receipts 0.74 GiB, `research/excavator` 0.61 GiB, Selden 0.50 GiB.
- **Cross-family review** (four exactly rebuilt Dorotheus batches, eight plants, blind adjudication):

  | Reviewer | Caught, strict | Caught, lenient | Wilson 95% interval, strict |
  |---|---|---|---|
  | Codex | 7 of 8 | 8 of 8 | 0.53-0.98 |
  | Claude | 16 of 22 | 17 of 22 | 0.52-0.87 |

  One contestable Codex rejection of a genuine claim, no false alarms. The blind re-scoring matches the original
  scoring in 21 of 22 cells.
- **Thesis measure** (main at `857313b455`): 59 / 2,610 / 1,135 / 837 / 10,357 orders in the categories revoked after an
  earlier end / revoked with no earlier end / earlier end never revoked / blocked / neither.
- **OCR preview:**
  - On 15 fraction passages, the count of ¼ ½ ¾ glyphs produced was GPO layer 0, Tesseract 0, PaddleOCR 22, Surya 134,
    Claude 335.
  - Exact GPO-and-engine agreement leaves only 1 of 43 reference passages, so the owner's reference rule needs a
    decision.
- **Source jobs:** LSA 357 of 357 issues, 0 failed; Table IV 16 editions; CourtListener 206 of 206 bulk segments (56.1 GB),
  0 failures. Every row each job writes is a lead until its primary page is held.
- **This campaign's own cost:** 19 agents (4 Opus, 15 Sonnet) and 2,433 model calls in this session, about 215 USD at API
  list prices (Necker), all on the owner's subscription; metered spending 0 of the 100 USD ceiling. The Codex reviewer ran
  on the owner's ChatGPT plan. Usage: `research/bentham/usage/encyclopedie-2026-11-06/`.
- **Cost:**
  - Local transcripts priced at 1,008.58 USD as API-price estimates, not bills. Cache reads are 46% of dollars but 96%
    of tokens.
  - Bentham's figures recomputed: about 0.33 USD per attempted order, 0.70 per filed dossier.

## What each change saves or unlocks

- **Size:** the pause and the receipt fix remove the two sources that added about 2.9 GB a day. The store makes R2 a
  one-line switch.
- **Leases:** stop sessions starting the same batch or job; the `kean-leases` branch has been in live use since
  2026-11-06.
- **Dollar costs:** let Bentham rank work by real prices (its table is about 2x high). Proposal in
  `jobs/necker-costs/PROPOSAL.md`.
- **Thesis measure:** names three unlocks.
  - Parsing list-form revocations would upgrade 706 orders whose revocation is known only from tables.
  - 251 unclaimed cleanup-revoked orders are the best next claim batch.
  - The owner's answer to A-20261106-1 decides 209 NIRA-code orders.
- **Cross-family reviewer:** a likely cheap way to catch defects that same-family pairs miss.
- **Free-source map:** removes most reasons to touch licensed databases; the librarian letter is kept only as a last
  resort.

## Deferred, and why

- **R2 and B2:** they need a payment card (owner). The code path is built and tested against a fake.
- **History rewrite:** owner decision (A-20261106-2). The plan follows once the uploaded bytes are verified.
- **Tracker fix for the thesis column:** it changes counts, so it needs the owner (A-20261107-tracker-thesis-fix).
- **Checker adapter for store locators:** it changes counts. The patch and a design note are in
  `research/encyclopedie-campaign/storage/`.
- **Agent HQ trial:** Copilot Pro+ not confirmed. Dynamic workflows were not used; ordinary subagents sufficed.
- **Driver scripts live run:** the owner must choose subscription token or API key.

## Problems in this campaign, owned

1. The first line-ending command given to workers emptied files; two streams rebuilt theirs. It was replaced by
   `tools/lf.py`.
2. My tip sent the CourtListener worker to `static.case.law`, whose robots.txt forbids crawling. The few requests made
   there were deleted and are disclosed.
3. Creating Release tags on ordinary commits started every push workflow: about 870 runs, and five bot commits to main.
   Stopped by pointing new tags at a workflow-free commit. The bot commits were kept under the owner's "remove nothing"
   rule.
4. The first prior-art results had a NaN bug and a definitional error. An independent check caught both before
   anything was recorded.
5. Two workers made one-off research requests to robots-disallowed hosts (static.case.law; about 30 webharvest.gov
   pages) before reading the whole robots.txt; nothing from either is used. The shared fetch pool cannot read wildcard
   robots rules, a gap that affects every job (owner question A-20261107-fetchpool-wildcards).
6. Merging new jobs twice turned main's road tests red (a job that imports `jobs/_lib` must list it in `triggers.txt`);
   both fixed within the hour (#208 for an older gap, #213).
7. Branches that had run jobs carried stale copies of other jobs' outputs; before merging, each was brought up to main and
   those outputs restored, so no merge rolled main back.

## Decisions the owner must make

The Kean ask ids are in `HANDOFF/KEAN_ASKS.md`.
- **Hein-origin Library of Congress scans:** allow targeted pulls (A-20261107-loc-hein)?
- **Hugging Face mirror of Harvard's case law:** acceptable (A-20261107-cap-mirror)?
- **OCR references:** choose the reference rule (A-20261107-ocr-reference-rule) and type the 15 hard passages.
- **Tracker fix for the thesis column:** apply it (A-20261107-tracker-thesis-fix)?
- **Lowande email:** send it (A-20261107-lowande-email)?
- **A-20261106-1:** confirm or change the provisional answer.
- **A-20261106-2:** the history rewrite, after reading the plan.
- **Mountweazel PLANTS.csv check:** decide the policy (A-20261107-mountweazel-plants-leak).
- **Faculty sponsor and certifier pilot:** faculty sponsor, and pilot option A (about 6,500 USD), from `RECRUITING.md`.
- **Filing rule:** whether to make one blind reviewer a different-family model.
- **CourtListener cross-check:** run the 40 token calls despite the robots.txt 403 (A-20261107-courtlistener-robots)?
- **Court leads in the claim kit:** wire them (A-20261107-claimkit-court-fragments)?
- **Shared fetch pool:** fix wildcard robots handling (A-20261107-fetchpool-wildcards)?
- **History rewrite:** read `storage/HISTORY_REWRITE_PLAN.md` (recommended option B: about 9.35 GiB to about 4.0 GiB).

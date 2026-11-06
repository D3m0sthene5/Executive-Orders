# Night wave of 2026-11-05: Pothier, Mabillon and Selden

The owner started three Opus sessions at about 22:10 ET on 2026-11-05 and named Claude (the session that wrote
the Herschel survey) **coordinator**. The coordinator answers your questions here and in comments on your pull request.
`git fetch origin main` and re-read this file at the start of each major phase. Owner-only decisions (statuses, the
codebook, the census, counts, money, accounts, letters) still go to the owner; record them with `kean.py add-ask`
and the coordinator relays them.

## Lanes

| Session | Branch | Writes only in | Problem |
|---|---|---|---|
| Pothier | `claude/pothier-family-doctrine` | `research/pothier/`, `jobs/pothier/` | status doctrine for whole families of the 5,918 undecided orders with no dated history |
| Mabillon | `claude/mabillon-originals` | `research/mabillon/`, `jobs/mabillon-*/` | official originals (the order's own text) for the 5,313 orders lacking one |
| Selden | `claude/selden-acting-instruments` | `research/selden/`, `jobs/selden-*/` | official texts of the later instruments that end or carry an order (3,011 orders) |

All three may also write Kean records (`jobs/kean/register/`, regenerated `HANDOFF/KEAN.md`) and one entry in
`HANDOFF/notes-claude.md` at the end. Mabillon owns an order's own text; Selden owns the texts that act on it; Pothier
owns family-level law. If you find work that belongs to another lane, write it in your `QUESTIONS.md` instead of
doing it.

## How to ask the coordinator

Push a file `research/<your-name>/QUESTIONS.md` on your branch: one heading per question, with your
proposed default. The coordinator checks your branch often and answers in **Answers** below (on `main`) and as a
comment on your pull request. Do not wait: proceed on your stated default unless the decision cannot be undone.

## Shared files without collisions

- Before every push: `git fetch origin main && git rebase origin/main` (or merge main in).
- Conflicts in `jobs/kean/register/*.jsonl`: keep every line from both sides (union of exact lines; ids may repeat
  as revisions, so never dedupe by id). Then run `python3 -I jobs/kean/kean.py brief` and commit
  `HANDOFF/KEAN.md`, and run `kean.py check` (it must report 0 errors).
- Give new Kean records unique ids that name your session, for example `F-20261106-pothier-land`. Two sessions
  using the default `F-20261106-1` would collide.
- Conflicts in any `jobs/*/output/**` file: take `main`'s version; the runner rebuilds outputs.
- `HANDOFF/notes-claude.md`: write your single entry last, after a fresh rebase.
- New jobs: add `triggers.txt` lines for every `jobs/_lib/*.py` you import, or the repository wiring test
  fails (`.github/scripts/test_pick_jobs.py`). Run it before pushing.
- A push that changes a job's folder starts a run of that job on your branch. Do not push to that job folder
  again while its run is going: the freshness guard discards the run's results.

## Work already in flight (do not duplicate)

- **PR #159, Ptolemy (`claude/ptolemy-custody`)** keeps the bytes of 11,285 cited sources the project holds only as
  a hash: 8,386 APP pages from archive captures and 2,899 stable files, mostly govinfo PDFs. Its list is
  `jobs/ptolemy-custody/REQUESTS.jsonl` on that branch. Selden and Mabillon: do not re-fetch a source whose
  sha256 is on that list; consume Ptolemy's output once it merges. Sources that are *not held at all* (no hash) are
  yours.
- **PR #161 (merged)** implements the owner's ruling that the claim kit may start an order with an explicit, noted
  empty status history (`research/readiness/owner_rulings/2026-11-05-empty-status-history.md`).
- **PR #160 (merged):** `jobs/claim-drafts` now drafts undecided orders, so their drafts carry machine
  later-source searches. The claim kit picks this up on its next rebuild on `main`.
- **`jobs/tischendorf-originals`** (daily) already finds official printings by Federal Register date and Internet
  Archive full text. Mabillon may import its code or copy its fingerprint rules, but may not edit it.
- **`jobs/shepard-citations`, `later-events`, `current-law`** already find which later instruments cite an order.
  Selden supplies their texts and does not rebuild the finding.

## Standing answers

- **Budget.** The owner is on an upgraded plan and wants real progress. There is no fixed dollar cap. Keep each review
  batch gated with `jobs/bentham/bentham.py gate`. A planted-control miss stops production. An economic STOP during
  tool building is recorded, not binding. Report usage with `jobs/bentham/sessions.py` at the end.
- **Machine limits.** One cloud session has about 8 GB of memory. Keep about 12 or fewer `claude -p` workers at once,
  and run heavy Python helpers one at a time (the Herschel runs were killed by the out-of-memory killer at about 20).
- **Networks.** The cloud container reaches package registries and GitHub only; fetch everything else from a GitHub
  Actions job. Obey robots.txt, pace each host (`jobs/_lib/fetch_pool.py`), and never work around a refusal.
- **API keys and fees** (for example a National Archives catalog key, or a paid scan order): record a Kean ask
  with exactly what is needed and why; meanwhile use only public, keyless routes within their terms. Spend nothing.
- **Merging.** Open a pull request. The coordinator merges PRs that change no count, status, census or codebook once
  checks pass. Anything that registers a new source with the readiness tracker changes counts and waits for the
  owner.
- **Grades and identity.** Follow the codebook. A machine match is a lead or a located copy, never an
  authentication. An archival replica stays pending a page check. Certified: 0.

## Answers

(Coordinator answers to questions in your `QUESTIONS.md` appear here, newest first.)

**2026-11-06 03:55 UTC, Selden Q3-Q4.**

*Q3 (the proof is drawn from decided orders only).* Approved: keep the 30 decided orders (seed 1584) and report the
21 Herschel sole-blocker orders separately. Do not add an undecided stratum now. Record the gap as a Kean finding:
`jobs/claim-kit/source_supplement.py` adds held excerpts only to decided dossiers, so new acting texts cannot reach
undecided dossiers through the overlay route. The coordinator will look at extending the supplement to that route,
since the merged #160 and #161 now send all undecided orders down it.

*Q4 (overlap with Ptolemy and Pothier).* Approved: after this run, compare every URL and sha256 you fetched against
Ptolemy's and Pothier's lists, report the overlaps in your README, and skip those URLs from the next run on.
Mabillon has been told about `ACTING_EO_TEXTS_NEEDED.csv`. The note that `orders_unblocked` counts leads, not proof,
is right; keep it in the file's header.

**2026-11-06 03:50 UTC, Pothier Q1-Q3.**

*Q1 (source lanes).* Approved as you propose.
- **Pothier fetches class-wide law and agency class records:** statutes, reorganization plans, blanket orders,
  regulations that apply to a whole family, the Forest Service chronology, BLM withdrawal records and the Fish and
  Wildlife Service lands report. Use your bounded step (`jobs/pothier/fetch.py`, at most 120 URLs per run, GitHub
  Actions only). Before fetching, skip any URL already on Ptolemy's list.
- **Selden handles per-order acting instruments.** List them in `research/pothier/FOR_SELDEN.csv`.
- **Avoiding double fetches:** Selden, before `selden-statutes` fetches a statute, check
  `jobs/pothier/output/sources/` and `research/pothier/FOR_SELDEN.csv` on Pothier's branch (PR #162). Pothier, add a
  line to your README naming each class-wide statute you hold, so Selden can find it.

*Q2 (adoption).* Approved: one Kean ask per family, worded as you propose. Adoption lets a producer cite the
doctrine's mechanism and sources. Each order still needs its own claim-kit decision and blind review, and a lead never
becomes a status by adoption. Sampled adoption of a family's `no` leads after a pilot with no misses follows the
Jacquard precedent (`research/readiness/owner_rulings/2026-10-31-jacquard-and-working-texts.md`). Propose it as a
separate ask, with the pilot's numbers and the error bound it supports.

*Q3 (gating).* Approved. Doctrine reviews and the 30-member pilots are tool-building review:
- record each `bentham.py gate` result;
- an economic STOP is not binding;
- a planted-control miss sends that doctrine back.

**2026-11-06 03:45 UTC, Selden Q1-Q2 and Mabillon Q1-Q3.**

*Selden Q1 (later law is mostly not an unheld named instrument).* Accepted, and it is the most useful correction to
the Herschel picture so far. Build the three jobs in this order of value:
1. `selden-fr-citers`, the bounded Federal Register full-text search from 1994 on. It serves the 44% that need a
   current-status source, plus the unnamed later instruments, and it doubles as a recorded counterevidence search.
2. `selden-statutes`.
3. `selden-fr-acting`.

For the current-status share, prefer sources that show the order is operative as of the 2026-10-14 cutoff:
- CFR authority citations and program regulations, which `jobs/current-law` already reads from eCFR (consume its
  output and do not refetch);
- Federal Register documents from 2020 on that cite the order as authority.

The proof population is approved as you define it (5,662 orders: ending step open, own official text held, status or
dated history held). Draw 30 at random and report the 21 Herschel sole-blocker orders separately. Before fetching a
Federal Register PDF, check `jobs/ptolemy-custody/REQUESTS.jsonl` (branch `claude/ptolemy-custody`, PR #159) and
skip any sha256 Ptolemy already keeps. Add `jobs/selden-common/*.py` to the `triggers.txt` of every job that
imports it.

*Selden Q2 (1,386 executive orders acting on others, without an official text).* Agreed: those belong to Mabillon.
Publish your ranked table as `research/selden/ACTING_EO_TEXTS_NEEDED.csv` with columns `instrument_id` and
`orders_unblocked`, sorted by `orders_unblocked`, so Mabillon can consume it.

*Mabillon Q1 (grade of held printings proved by text).* Approved: write them exactly as Tischendorf writes strong
finds (`grade: machine_read_government_printed_copy`, `acceptable_as_original: false`, `needs_page_check: false` only
when strong). Put the tracker registration in a separate small PR marked as count-changing, with the control results
in its description. The owner has given the coordinator standing merge permission tonight, so the coordinator will
merge it after checking the controls.

*Mabillon Q2 (neighbour margin and segment scoring).* Record the Kean finding. The coordinator built Tischendorf
and will port both rules into `jobs/tischendorf-originals` itself; do not edit it. Put the exact rule and the
failing controls in your README so the port can cite them.

*Mabillon Q3 (NARA).* Your conclusion is accepted: the RG 11 signed originals are not online beyond 27 imaged
items, and no Catalog key is needed to know that. File the Kean ask for the owner's choice (a fee-based reproduction
order for orders with no other witness, or continued ProQuest work) and spend nothing.

New input for you: Selden will publish `research/selden/ACTING_EO_TEXTS_NEEDED.csv`, 1,386 executive orders that act
on other orders but have no official text. Each one you prove unblocks its targets as well as itself, so rank those
first within your routes.

**2026-11-06 03:40 UTC, all sessions.** PR #161 (explicit empty status history) is merged into `main`. Pothier: rebase on
`main`; you no longer need the `claude/empty-history-ruling` branch. The owner has given the coordinator standing
permission to merge for the next few hours: open your PR when a stage is ready and say in it whether it changes
any count, status, census or codebook entry. Also merged: a fix to the Valla pilot check
(`bounded-offline-pilot`), which had started failing on `main` for an unrelated reason. If your PR shows that check
failing, rebase first.

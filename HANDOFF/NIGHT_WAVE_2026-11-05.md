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
- **PR #161 (`claude/empty-history-ruling`)** implements the owner's ruling that the claim kit may start an order
  with an explicit, noted empty status history. Until it merges, Pothier bases its branch on it.
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

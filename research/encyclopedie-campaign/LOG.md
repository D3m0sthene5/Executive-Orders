# Encyclopédie campaign log

Campaign to adopt the 2026-11-06 Peiresc tool survey (`research/peiresc-tool-survey/` on branch
`claude/peiresc-tool-survey`). Coordinator: Claude Opus 5.5, desktop session on the owner's PC (DANSRIG). Integration
branch: `encyclopedie-diderot` (only the coordinator writes Kean, `HANDOFF/notes-claude.md` and this log). Each stream has
its own branch, folder, Kean lease (`kean-leases` branch, holder `claude-encyclopedie`) and sparse worktree under
`C:\Users\danie\eo-wt\enc-*`.

## Owner answers (2026-11-06, about 22:00 UTC)

Recorded as Kean decisions D-20261106-encyclopedie-campaign, -budget, -xfamily, -installs and -ptolemy-pause
(`research/readiness/owner_rulings/2026-11-06-encyclopedie-campaign.md`).

| Question | Answer |
|---|---|
| Owner-directed, outside Bentham? Coordinator merges count-neutral PRs? | Yes, owner-directed. **Do not merge**: every PR stays open for the owner. |
| Paid API ceiling | **$100 total** for the campaign. Spent so far: $0. |
| Cross-family reviewer pilot | Approved, run autonomously from this session. |
| Installs on DANSRIG | Yes: venv and GPU OCR models. |
| Ptolemy | Paused by a direct push to main (`0ed4bd6a95`). |
| Interim byte store | GitHub Release assets, sharded by hash prefix; manifests in git. |

### Still unanswered (defaults in force)

| Item | Default taken |
|---|---|
| CourtListener token | Jobs read the GitHub secret `COURTLISTENER_TOKEN`; without it they use anonymous endpoints only and say so. |
| api.data.gov key for govinfo | Secret `GOVINFO_API_KEY`, falling back to `DEMO_KEY` with pacing. |
| OpenAI / Gemini API keys | None. The cross-family pilot uses the Codex login already on this PC if it works; otherwise it waits. |
| Cloudflare R2 / Backblaze B2 accounts | None. The store's R2 backend is built and tested against a local fake, and is switched on by configuration. |
| Copilot Pro+ | Assumed no; the Agent HQ trial is skipped. |
| OCR reference transcriptions: who makes them? | The packet is prepared; scoring waits for the owner's choice. |
| Faculty supervisor? | Unknown; the librarian letter asks both ways. |
| A-20261106-1 (unnamed abolishing statute dates an end?) | Default no (unchanged). |
| A-20261106-2 (how to shrink the repo) | New bytes stopped; any history rewrite or new repository is left to the owner. |
| The two ZIPs | `Downloads\dataverse_files.zip` (12,943 bytes) and `Downloads\dataverse_files (1).zip` (8,080,973 bytes), both saved 2026-11-06 16:12-16:13 local. The brief said over 100 MB; they are much smaller. |

## Repository size (measured 2026-11-06 22:05 UTC)

**What the limit is (read 2026-11-07 from docs.github.com, repository-limits):** "On-disk size: 10 GB" is listed under
limits GitHub "recommend[s] staying within"; the enforced limits on that page are 2 GB per push and 100 MB per object.
What GitHub does above 10 GB is not documented. Size at 2026-11-07 00:20 UTC: 9,751,377 KB, still rising from other
sessions' jobs.

- GitHub API: 9,717,466 KB (about 9.95 GB) against the 10 GB limit.
- Main's tree at `410a1ffc43`: 186,256 files, 22.94 GiB uncompressed (identical blobs at several paths count once in git).
- Largest folders in the tree: `jobs/_attempts` 8.2 GiB, `research/excavator` 4.5 GiB, `jobs/ptolemy-custody` 2.6 GiB,
  `jobs/astra-source-retention` 1.5 GiB, `jobs/claim-kit` 1.5 GiB.
- New blobs on main since 2026-11-05 00:00 UTC: 85,531 blobs, 16.0 GiB uncompressed, 4.37 GiB packed (local pack sizes).
  Top packed contributors: `jobs/ptolemy-custody` 2.17 GiB, `jobs/_attempts` 0.74 GiB, `research/excavator` 0.61 GiB,
  `jobs/selden-fr-acting` 0.31 GiB, `jobs/claim-kit` 0.24 GiB, `jobs/selden-statutes` 0.14 GiB.

## Streams

| # | Stream | Lease | Branch | Worker | Status | Next |
|---|---|---|---|---|---|---|
| 1 | Repository size: pause, byte budget, Pergamon store | stream:enc-storage | enc/storage | coordinator + Sonnet | Ptolemy paused and verified (run 42303303375: 0 bytes kept, 3,060 carried) | Store library, push budget check |
| 2a | Prior art: Thrower (Bayle) | stream:enc-prior-art | enc/prior-art | Sonnet; Opus check | running | |
| 2b | Prior art: Lowande-Poznansky (Bayle) | stream:enc-prior-art | enc/prior-art-lp | Sonnet; Opus check | running | |
| 3 | Kean leases | stream:enc-leases | enc/leases-wire | coordinator | built and wired into `kit.py dispatch-check`; 12 tests pass; 12 live leases | PR |
| 4 | Cost per batch and worker (Necker) | stream:enc-cost | enc/cost | Sonnet | running | |
| 5 | Librarian questions (Panizzi), last resort only | stream:enc-librarians | encyclopedie-diderot | coordinator | draft done (`panizzi-librarians/LETTER.md`) | Send only for what Naudé cannot find |
| 5b | Free routes to licensed material (Naudé) | stream:enc-librarians | enc/naude | Sonnet | running | |
| 6 | LSA job (Repetita) | job:repetita-lsa | enc/lsa | Sonnet | running | |
| 7 | U.S. Code Table IV time series (Duodecim) | job:duodecim-tableiv | enc/tableiv | Sonnet | running | |
| 8 | CourtListener (Youngstown) | job:youngstown-courts | enc/courts | Sonnet | running; told to try Caselaw Access Project bulk | Token for full CourtListener run |
| 9 | Claim-kit driver scripts, billing check (Hollerith) | stream:enc-drivers | enc/drivers | Sonnet | running | |
| 10 | Cross-family reviewer pilot (Septuagint) | stream:enc-xfamily-review | enc/xfamily | Sonnet rebuild; Opus adjudication | rebuilding the 6 Dorotheus review sets | **Owner: re-login to Codex** (token expired, 401) |
| 11 | OCR pilot (Ventris) | stream:enc-ocr-pilot | enc/ocr | Sonnet | running | |
| 12-15 | Certifier page, Zenodo design, Observable trial, Agent HQ | stream:enc-tier4 | enc/tier4-* | Sonnet | queued | |

## Archives (verified 2026-11-06)

| Archive | File | Bytes | SHA-256 | Dataverse | Licence |
|---|---|---:|---|---|---|
| Lowande and Poznansky | `Downloads/dataverse_files.zip` | 12,943 | `7c51d513fe68ec0b8ca0843a2dd28ec053e03b0d7093e0174cd3fba99c7e8d41` | doi:10.7910/DVN/TZ2QKY, V1, released 2023-12-12 (survey's guess confirmed) | CC0 1.0 |
| Thrower | `Downloads/dataverse_files (1).zip` | 8,080,973 | `c641a12e2dbf8e827999cbb531dabbe7fcc402f20488c93da4847a95eda3f9a2` | doi:10.7910/DVN/LZGQOH, V1 (API 1.1, released 2018-12-11) | CC0 (stated "additional terms" are empty) |

Every file's MD5 matches Dataverse's listing. Unpacked with a path-checked extractor into empty scratch folders.
Lowande and Poznansky's `orders.Rda` has 6,536 orders (1937-2021) and 14 variables but **no order numbers**, and the
listed `codebook.pdf` is missing; their readme says the order-level dataset is "provided upon request". Thrower's
`eo_original_list.csv` has 6,157 orders (1937-2013) with numbers.

## Byte budget for campaign streams

No campaign stream commits PDFs, large texts or archives. Per job run: committed `output/` at most 20 MiB, and no single
file over 5 MiB. Per push: at most 25 MiB of new blobs, checked with
`git rev-list --objects origin/<base>..HEAD | git cat-file --batch-check` before every push.

## Rules learned

- The first CRLF one-liner in WORKER_RULES.md opened each file for writing before reading it and emptied files; two
  streams lost and rebuilt their files. Replaced by `tools/lf.py` (reads first, refuses to empty) at 23:40 UTC.
- My first lease tip went to the wrong agent id; resent to Youngstown.
- **Robots breach, disclosed.** My tip pointed Youngstown at static.case.law before the Naudé survey found its
  robots.txt is `Disallow: /`. Before the correction arrived, the worker made one-off requests there from the owner's PC
  (robots.txt, two metadata JSONs, CasesMetadata in part, three case JSONs, one case HTML, one 4.1 MB volume zip,
  directory pages). Two saved files were deleted; nothing from that host is in any job, fixture, output or commit; the
  job's README discloses it and the job makes no request to the host. Lesson: verify robots.txt and terms before
  suggesting a source to a worker.

- A push that changes an existing job's folder starts that job on the branch. The lease-wiring push started claim-kit
  (run 42306096793); it was cancelled within a minute, before committing. Rule added to `WORKER_RULES.md`.
- The tracker's `formal_revocation_after_earlier_cessation` column is blank for all 14,998 orders: the project does not
  yet compute its own thesis measure (matters for the prior-art baseline).

## Pull requests (all left open for the owner)

| PR | Branch | What | Counts |
|---|---|---|---|
| #188 | enc/attempt-trim | Runner keeps failed-attempt receipts small (urgent: about 740 MB/day) | neutral; **merged by owner 2026-11-06 23:33 UTC** (`299d161209`) |
| #189 | enc/leases-wire | Kean leases; dispatch-check honours them | neutral |
| #190 | enc/drivers | Hollerith driver scripts and billing facts | neutral |
| #191 | enc/cost | Necker dollar costs | neutral |
| #192 | enc/zenodo | Bodley Zenodo design | neutral |
| #193 | enc/observable | Playfair Observable trial | neutral |
| #195 | enc/certifier | Nihil obstat certifier page | neutral |
| #196 | enc/naude | Naudé free-source survey | neutral |
| #200 | enc/prior-art-lp | Bayle: Lowande-Poznansky | neutral |
| #201 | enc/thesis-measure | Thesis measure report | neutral (report only) |
| #202 | enc/prior-art | Bayle: Thrower | neutral |
| #203 | enc/ocr | Ventris OCR pilot | neutral |
| #204 | enc/storage | Pergamon store | neutral |
| #205 | enc/xfamily | Septuagint cross-family pilot | neutral |

## Workers

| Worker | Model | Task | Tokens | Time |
|---|---|---|---:|---:|
| Pergamon | Sonnet | storage | 246,158 | 16.7 min |
| Hollerith | Sonnet | drivers, billing | 368,590 | 16.8 min |
| Necker | Sonnet | cost | 281,245 | 19.6 min |
| Bayle-LP | Sonnet | Lowande-Poznansky | 330,144 | 20.4 min |
| Bayle-Thrower | Sonnet | Thrower | 345,345 | 21.9 min |
| Bodley | Sonnet | Zenodo | 248,393 | 16.5 min |
| Playfair | Sonnet | Observable | 163,244 | 21.5 min |
| Nihil obstat | Sonnet | certifier | 337,261 | 22.5 min |
| Naudé | Sonnet | free sources | 262,697 | 32.7 min |
| Ventris | Sonnet | OCR pilot | 371,095 | 56.4 min |
| Septuagint | Sonnet | rebuild + Codex arm | 317,801 | 59.7 min |
| Thesis measure | Opus | thesis report | 424,267 | 37.8 min |
| Prior-art check | Opus | independent check | 258,745 | 16.3 min |
| Bayle-LP fixes | Sonnet | corrections | 387,211 total | +5.0 min |
| Bayle-Thrower fixes | Sonnet | corrections | 455,992 total | +10.5 min |
| Youngstown | Sonnet | CourtListener job | 463,227 | 116.6 min |
| Blind adjudicator | Opus | Septuagint scoring | 116,563 | 3.1 min |
| Codex arm (y01-y05) | gpt-6-sol, medium | blind review | 6.03M input (5.82M cached), 39,439 output | 20.2 min |

## Events

- 22:00 UTC. Owner answered the start questions. Repository measured. Ptolemy paused on main.
- 22:20 UTC. Kean leases built (`jobs/kean/lease.py`, 9 offline tests). Shared branch `kean-leases` created on GitHub
  by the first real claim; 12 campaign leases held until 2026-11-07 10:20 UTC.
- 22:30 UTC. Nine Sonnet streams launched (storage, Thrower, Lowande-Poznansky, Necker, Repetita, Duodecim, Youngstown,
  Hollerith, Ventris). Codex CLI 0.165 found and logged in with ChatGPT, but its token cannot refresh (401); owner asked
  to re-login. Septuagint rebuild stream launched.
- 22:40 UTC. Owner: the librarian letter is a last resort; find free routes. Naudé stream launched; Youngstown told about
  the Caselaw Access Project bulk data.
- 22:50 UTC. Leases wired into `kit.py dispatch-check` (branch `enc/leases-wire`, 3 gate tests). Ptolemy pause run
  verified. GitHub size 9,732,031 KB.
- 23:30 UTC. Owner's second answers recorded (D-20261106-encyclopedie-storage, -keys, -ocr-reference,
  -thesis-measure; A-20261106-1 provisional answer recorded, ask kept open; A-20261106-2 lives only on the unmerged
  survey branch, so its answer is in the decision). Thesis-measure stream (Opus) launched.
- 00:00 UTC Nov 7. `jobs/_attempts` found to be the next grower (failed runs commit whole outputs); PR #188.
  Migration of 3,695 Ptolemy and Selden raw files (3.2 GB, 3,691 unique) to the Release store started: three uploaders
  on disjoint folders under `C:/Users/danie/eo-pergamon-stage/`, about 25 s per file. Fresh Opus check of prior-art
  launched. PRs #188-#193 and #195 opened.
- 00:20 UTC. Independent Opus check of both prior-art streams: outputs reproduce byte for byte, but it found a NaN bug
  dropping 75 undated edges, about 70 "Thrower silent" leads that are amending orders revoked with their parent, a
  confounded lineage 2x2, a wrong EO 12656 diagnosis, 377 vs 372 for EO 12553, two formal-versus-operative wording
  errors, and a wrong pronoun in the Lowande email. Both workers sent back to fix and record CHECK_2026-11-07.md.
  Naudé finished (PR #196): govinfo is free for FR 1936-2026, Statutes, Serial Set, bound Congressional Record; LOC's
  CFR/FR/USC scans are Hein-origin with a no-bulk term (owner decision); static.case.law is robots-disallowed.
- 01:30-02:40 UTC Nov 7. Owner authorized merging what removes nothing (D-20261107-encyclopedie-merge). Merged PRs
  #189-#217 after per-file checks; closed #207 unmerged. Dashboards refreshed (tracker with Trajectory tab; Tsiolkovsky).
- 01:20 UTC. Release tags were starting every push workflow (about 870 runs; five bot commits to main, kept). Remaining
  shard tags created on the workflow-free `pergamon-store-root`; uploads resumed.
- 06:31 UTC. Pergamon migration complete: 3,691 files, 3.18 GB, all verified by tokenless re-download. Manifest in git.
  Leases released. Report, handoff note and Bentham usage written. Campaign closed.

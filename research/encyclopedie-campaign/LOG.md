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
| 1 | Repository size: pause, byte budget, Pergamon store | stream:enc-storage | enc/storage | coordinator + Sonnet | Ptolemy paused on main | Store library, push budget check |
| 2 | Prior art: Lowande-Poznansky, Thrower (Bayle) | stream:enc-prior-art | enc/prior-art | coordinator + Sonnet; Opus check | starting | Hash and list the ZIPs |
| 3 | Kean leases | stream:enc-leases | encyclopedie-diderot | coordinator | built, 9 tests pass, 12 live leases claimed | Wire into dispatch-check |
| 4 | Cost per batch and worker (Necker) | stream:enc-cost | enc/cost | Sonnet | queued | |
| 5 | Librarian questions (Panizzi) | stream:enc-librarians | encyclopedie-diderot | coordinator | queued | |
| 6 | LSA job (Repetita) | job:repetita-lsa | enc/lsa | Sonnet | queued | |
| 7 | U.S. Code Table IV time series (Duodecim) | job:duodecim-tableiv | enc/tableiv | Sonnet | queued | |
| 8 | CourtListener (Youngstown) | job:youngstown-courts | enc/courts | Sonnet | queued | Token needed for full run |
| 9 | Claim-kit driver scripts, billing check (Hollerith) | stream:enc-drivers | enc/drivers | Sonnet | queued | |
| 10 | Cross-family reviewer pilot (Septuagint) | stream:enc-xfamily-review | enc/xfamily | coordinator | queued | Find Codex CLI |
| 11 | OCR pilot (Ventris) | stream:enc-ocr-pilot | enc/ocr | Sonnet | queued | |
| 12-15 | Certifier page, Zenodo design, Observable trial, Agent HQ | stream:enc-tier4 | enc/tier4-* | Sonnet | queued | |

## Byte budget for campaign streams

No campaign stream commits PDFs, large texts or archives. Per job run: committed `output/` at most 20 MiB, and no single
file over 5 MiB. Per push: at most 25 MiB of new blobs, checked with
`git rev-list --objects origin/<base>..HEAD | git cat-file --batch-check` before every push.

## Workers

| Worker | Model | Task | Tokens | Time |
|---|---|---|---:|---:|

## Events

- 22:00 UTC. Owner answered the start questions. Repository measured. Ptolemy paused on main.
- 22:20 UTC. Kean leases built (`jobs/kean/lease.py`, 9 offline tests). Shared branch `kean-leases` created on GitHub
  by the first real claim; 12 campaign leases held until 2026-11-07 10:20 UTC.

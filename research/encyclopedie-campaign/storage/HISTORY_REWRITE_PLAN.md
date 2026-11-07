# Plan for one coordinated history rewrite (for the owner's decision; nothing here has been done)

Asked for by the owner on 2026-11-06 (Kean A-20261106-2, D-20261106-encyclopedie-storage): "Once the raw files are in the
Release store and verified, write me a plan for one coordinated history rewrite (git filter-repo, a freeze, and every
session re-cloning). Include the expected size afterwards and the list of open branches it would break." Prepared by the
Encyclopédie coordinator, 2026-11-07. **A rewrite is irreversible for everyone who does not keep a backup, and it
breaks every open branch and clone. Only the owner can start it.**

## The short version

- **Today:** 9.35 GiB of unique packed history (measured locally over all refs on 2026-11-07; GitHub reports 9,776,627 KB,
  about 9.3 GiB, so the figures agree). GitHub recommends staying under 10 GB on disk and "strongly recommend[s]" under
  5 GB; the enforced limits are 2 GB per push and 100 MB per file.
- **Three options, in order of size and effort:**

  | Option | Removes from history | Expected size after | Prerequisite |
  |---|---|---:|---|
  | A. Raw bytes already in the store | Ptolemy `output/raw/` and Selden `captures/` and `pdf/` (2.25 GiB) | about 7.1 GiB | Store migration verified (see "Status"); checker adapter merged |
  | B. A plus every large binary | All PDFs, ZIPs, images and archive parts over 1 MB (5.3 GiB in all), after first moving the still-needed ones into the store | about 4.0 GiB | B's source files uploaded and verified the same way; their SOURCES records switched to store locators |
  | C. B plus superseded generated output | Old generations of `jobs/claim-kit/output`, `jobs/_attempts` large files and similar regenerated outputs (about 1.5-2.0 GiB more, estimate) | about 2.5 GiB | Decide which generated outputs are evidence (keep) and which are regenerable (drop) |

- **Recommendation:** option B, once. It brings the repository under GitHub's 5 GB recommendation with room to grow, keeps
  every byte the evidence chain needs (in the store, hash-verified, with manifests in git), and does not require judging
  which old generated outputs matter. Option C can follow later only if needed; each rewrite costs every session a
  re-clone.

## What breaks

- **Every branch.** 257 branches on GitHub (2026-11-07), including this campaign's 24 `enc/*`, `encyclopedie-diderot`,
  `kean-leases` and `pergamon-store-root`. Branch commits are rewritten too, but any branch someone has locally becomes
  unrelated history and cannot be pushed or merged afterwards.
- **Open pull requests:** #185 (`claude/mabillon-text-hash`, held, count-changing). It must be merged or closed and
  re-opened from a fresh branch.
- **Every clone and worktree**, on the owner's PC (about 25 worktrees under `C:\Users\danie\eo-wt\`,
  `C:\Users\danie\AppData\Local\Temp\eo-*`, `C:\Users\danie\Projects\EO-main` and `.claude/worktrees/`), in Codex and in
  cloud sessions. All must be deleted and re-cloned after the rewrite; pushing from an old clone would put the removed
  history back.
- **Commit hashes** cited in notes, Kean, manifests, receipts and claim records (for example `source_pin`s). After a
  rewrite every old hash is invalid. filter-repo writes a `commit-map` (old -> new); the plan commits it so old citations
  can be translated, and a small script can rewrite pins in-repo.
- **Release tags** `pergamon-xx` point at `pergamon-store-root`, which has no large blobs; they survive unchanged if that
  commit is kept (it is tiny and in no other history).

## Preconditions (all must hold before the freeze)

1. **Store complete and verified.** Every blob to be removed exists in the Pergamon store and re-downloads, without a
   token, with the same SHA-256 (the verify script used for the Ptolemy and Selden migration, `verify_store.py`).
2. **Nothing reads the removed paths.** The claim checker resolves store locators (apply
   `research/encyclopedie-campaign/storage/checker_adapter.patch`, run the full checker and tracker suites, and confirm
   on a branch that the readiness counts are unchanged), and every `SOURCES.jsonl` record whose `cache_path` points at a
   removed file carries a `pergamon` locator instead. This step is count-sensitive and owner-merged.
3. **The tip no longer contains the files** (an ordinary commit deleting them from main after step 2 passes), so the
   rewrite only removes history, never the current evidence.
4. **A full backup:** `git clone --mirror` of the repository kept by the owner off GitHub (about 9.3 GiB), plus a
   `git bundle` of it. Restoring from it is the only undo.
5. **Every open branch either merged or recorded**, with its tip hash, in a list committed before the freeze, so its work
   can be re-applied as a patch afterwards.

## The procedure

1. **Freeze (owner announces; about 2-4 hours).** Post a freeze note at the top of `HANDOFF/KEAN.md` and `CLAUDE.md`;
   disable the scheduled workflows (Actions -> each workflow -> Disable) so no bot pushes during the rewrite; stop every
   agent session.
2. **Backup:** `git clone --mirror https://github.com/D3m0sthene5/Executive-Orders.git eo-backup.git`, then
   `git -C eo-backup.git bundle create eo-backup.bundle --all`; verify with `git bundle verify`.
3. **Rewrite a fresh mirror** with git-filter-repo (pip install git-filter-repo):
   - Option A: `git filter-repo --invert-paths --path-glob 'jobs/ptolemy-custody/output/raw/*' --path-glob 'jobs/selden-fr-acting/output/captures/*' --path-glob 'jobs/selden-statutes/output/pdf/*'`
   - Option B: build `strip-ids.txt`, the blob ids of every file over 1 MB whose SHA-256 is in a verified store manifest,
     and run `git filter-repo --strip-blobs-with-ids strip-ids.txt`. Stripping by blob id, not by path, guarantees only
     bytes held in the store are removed.
   - Keep `.git/filter-repo/commit-map` and `ref-map`.
4. **Check the rewritten mirror:** `git count-objects -vH` (expected size), the full road and checker test suites on a
   checkout, and a script that confirms every removed blob's SHA-256 is in a verified store manifest.
5. **Push:** `git push --force --mirror` to GitHub. Then ask GitHub Support to run garbage collection and drop cached
   views; the reported size only falls after GitHub's own GC (documented in "Removing sensitive data from a repository").
6. **Re-clone everywhere** and delete every old clone and worktree. Re-enable workflows. Lift the freeze.
7. **Record:** commit the commit-map and a Kean finding; translate `source_pin`s and cited hashes with the map.

## Cost and risk

- Owner time: about half a day, mostly waiting; agent time: one session to run and check it.
- Main risk: a removed blob that something still reads by path. Preconditions 2 and 3, and stripping by verified blob id,
  are there to make that impossible; the backup is the fallback.
- Not affected: Git LFS objects (stored separately; they are pointers in history), release assets, Zenodo plans.

## Status at writing

- Ptolemy and Selden raw files: 3,691 unique files (3.2 GB) being uploaded to `pergamon-xx` releases; the verification
  result is recorded in `research/encyclopedie-campaign/storage/MIGRATION.md` when complete.
- Checker adapter: written and tested in isolation, not applied (count-sensitive; owner).

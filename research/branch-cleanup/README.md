# Branch cleanup, 2026-11-07

`DELETE_2026-11-07.txt` lists 187 remote branches whose work is already on main. Each one is a branch whose tip is a merged PR's head, or that head followed only by runner result commits, `Restore ...` commits or merges of main; or a branch contained in main. Deleting them loses nothing: every merged PR keeps its commits, and GitHub can restore a deleted branch from its PR page.

These are kept:
- the open draft PR #185;
- the running Haloander batch (`claude/haloander-2026-11-07`);
- `encyclopedie-diderot`, the Encyclopedie coordinator's branch;
- `claude/lucid-planck-8pbn2t`;
- 67 older branches that hold commits no merged PR carries, listed in `KEEP_2026-11-07.txt`.

Run from any clone:

    git push origin --delete $(cat research/branch-cleanup/DELETE_2026-11-07.txt)

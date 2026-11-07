# Septuagint: cross-family replay of the Dorotheus review batches (Kean D-20261106-encyclopedie-xfamily)

An OpenAI-family reviewer (Codex) replays claim batches that Claude reviewers reviewed with planted controls on
2026-11-06, so the two families' catch rates can be compared on identical inputs. This folder holds the exact
rebuild method, the gate that proves the rebuilt inputs equal the originals, the harness that runs the Codex arm, and
the run logs. Nothing here records a verdict, a plant key or a plant's identity; those stay under
`C:/Users/danie/eo-septuagint-private/` (never committed) until the coordinator adjudicates.

## Source commit

`a8dd983983` (main, 2026-11-06T09:18:46Z), the `main_commit` that `research/excavator/dorotheus-yesprobe-2026-11-06/DRAW.json`
records for the wave's start (10:00Z). It is consistent with every fingerprint the wave committed:
the `code_pins` in each committed `DISPATCH_CHECK.json` (`dispatch.py` 19167f9d, `checker.py` 2e834806, `sources.py` 7bb63fdb)
hold from `a8dd983983` through `5af12d6af8` and break at the 10:19Z merges (`checker.py` changes), and the dossier
`fingerprint` carried by the filed claims (EO 10057: 852ee54c) is the one written by commit `227b2e08b3` (08:34Z).
The decisive check is the packet itself: every rebuilt `PACKET.json` has the SHA-256 recorded in the committed
`DISPATCH_CHECK.json` (`packet_sha256`), see below. The commit sits before the first review launch (2026-11-06T10:35:55Z for
y02/y05, 10:40Z for y01, 10:51Z for y03); no producer claim existed on main then (they were filed after 11:20Z).

## Rebuild method (what each Claude arm saw, per batch y01, y02, y03, y05)

Work tree: `C:/Users/danie/eo-wt/enc-septuagint-src`, detached at `a8dd983983`, sparse (everything except `jobs/_attempts/`;
widened for the rebuild because `kit.py prepare`'s prior-research scan reads every JSON file under `research/`, then narrowed, see
Blinding). Steps, in order:

1. Checkout with the LFS files left as pointers (the wave's Linux clone had pointers; with real files the dispatch check reports
   "complete Opus zip on this machine" and the packet hash differs). All 23 LFS paths were reset with `GIT_LFS_SKIP_SMUDGE=1`.
2. `kit.py prepare <IDS> --agent dorotheus --write research/excavator/dorotheus-yesprobe-2026-11-06/<batch>/packet` exactly as
   `prepare.sh` ran it (IDs and order from the committed `tools/batches.json`), through `rebuild/posix_run.py`. That wrapper only makes
   `pathlib` print forward slashes: on Windows the packet's `input_pins[*].path` held backslashes, which JSON-escapes to 24 extra bytes
   for y01 and changes the hash. Nothing else differs from a Linux run.
3. Copy the committed final `decisions.csv`, `clauses.csv`, `RATIONALES.json` of the batch from main into the rebuilt packet and run
   `kit.py apply <packet> --write <packet>/applied-rebuild`. This regenerates `CLAIMS.proposed.jsonl`, the producer's submitted claims
   (the originals stayed in the container scratch).
4. `rebuild/review_prep_port.py BATCH CLAIMS MWCODE ABC`: the committed `review_prep.py` (SHA-256 05ccfedf86001de8935eb042f1b944e867612669ed664d850566d0bd5dfcbd39)
   with only these changes: `REPO` and `E` read from environment variables, `python3` becomes `sys.executable`, and `read_text` /
   `write_text` default to UTF-8 with LF. Seeding is untouched (date-shift rule and seed `dorotheus-controls:<batch>`; Mountweazel
   `seed --track C --n 2 --share 0.5 --codes D3|D6|D7|D5 --seed dorotheus-2026-11-06-<batch>` with the wave's exclusion list from the committed
   `tools/batches.json`, pool = `research/readiness/claims/*.jsonl` at `a8dd983983`; arm shuffles `dorotheus-<batch>-<arm>`).
5. `gate.py` compares, per batch and per arm.

## Gate results

| Batch | Packet SHA-256 equals committed `packet_sha256` | Claims in review set | Hash matches, arm A / B / C | Result |
|---|---|---|---|---|
| y01 | yes (62d5de0e) | 5 (3 producer, 2 Mountweazel) | 5/5, 5/5, 5/5 | PASS |
| y02 | yes (42a4d884) | 3 (1 producer, 2 Mountweazel) | 3/3, 3/3, 3/3 | PASS |
| y03 | yes (74f1f261) | 5 (3 producer, 2 Mountweazel) | 5/5, 5/5, n/a | PASS |
| y05 | yes (e18afaa1) | 3 (1 producer, 2 Mountweazel) | 3/3, 3/3, 3/3 | PASS |
| ux1 | not rebuilt | 7 (5 producer, 2 Mountweazel) | 3 of 5 producer claims not reproducible | DROPPED |
| ux2 | not rebuilt | 7 (5 producer, 2 Mountweazel) | 1 of 5 producer claims not reproducible | DROPPED |

Every claim in each rebuilt review set has the canonical SHA-256 recorded by every original arm for that instrument, the sets are
equal, and the rebuilt per-arm shuffles reproduce the line order of the original arms' files. `GATE.json` holds the counts, hashes and the
two drop reasons (full text there):

* ux1: EO:5857, EO:5866 and EO:10513 are in no committed file; the overlay claims came from LLM-written status-review sheets that stayed in
  the container scratch. The overlay bundles the ux reviewers read (`DOSSIER.json`) cannot be rebuilt exactly either.
* ux2: EO:13362's reviewed version was corrected before filing and is not committed (the filed hash differs from the reviewed hash). The
  EO:10994 plant does reproduce from the filed claim, and EO:10901, EO:11218, EO:13348 match, but a batch with one irreproducible claim is dropped.

## Codex arm: runs of 2026-11-06 (23:12-23:32Z)

Codex CLI 0.165.0-alpha.1.2, model `gpt-6-sol`, reasoning effort medium, `--ignore-user-config`, one batch at a time, arm X. Token counts are what
Codex reported (summed `turn.completed` usage); the logs are `runs/<batch>.json`.

| Batch | Claims | Wall seconds | Input tokens (cached) | Output tokens (reasoning) | Output validated | Suspect commands in event log |
|---|---|---|---|---|---|---|
| y01 | 5 | 360 | 1,819,551 (1,764,864) | 10,136 (3,082) | yes, 5 lines | 0 |
| y02 | 3 | 272 | 1,298,549 (1,249,536) | 9,217 (2,278) | yes, 3 lines | 0 |
| y03 | 5 | 323 | 1,862,394 (1,794,048) | 11,550 (3,267) | yes, 5 lines | 0 |
| y05 | 3 | 255 | 1,051,999 (1,010,432) | 8,536 (2,146) | yes, 3 lines | 0 |

Verdict files: `C:/Users/danie/eo-septuagint-private/verdicts/<batch>/BLIND_REVIEW_X.jsonl`, unread by the builder, awaiting adjudication.

## Blinding

The Claude arms were blinded by instruction. The Codex arm is blinded by absence as well:

* The reviewer works in `C:/Users/danie/eo-septuagint-review/<batch>/work` (only writable folder: the output file and `scratch/`), reads
  `<batch>/inputs/` (exactly `REVIEW_SET.jsonl` and `packet/PACKET.json`) and the read-only source worktree.
* The source worktree is narrowed so these do not exist in it: `research/excavator/dorotheus-sample-2026-11-06/`,
  `.../dorotheus-yesprobe-2026-11-06/`, `.../claude-icecore-2026-11-05/` and every other `research/excavator/*` folder except the two
  the prompt names (`claude-nira-sweep-2026-10-29`, `claude-production-2026-10-28`, top-level files only); `jobs/_attempts/`; and, beyond what the
  Claude arms had, `HANDOFF/`, `.github/`, `jobs/mountweazel/` (plant operators) and `research/readiness/claims/` (it holds the genuine base claims the
  Mountweazel plants were cut from). PLANTS.csv, REPORT.md, AFTER_REVEAL files and every BLIND_REVIEW file are not in the repository at that commit,
  and later filed claims are not either. All 275 repository paths cited in the four review sets exist in the narrowed tree.
* The worktree's `.git` pointer (which leads to the full object database with later commits) is renamed away for the duration of each run.
* `--ignore-user-config` (no plugins, memories, notify hooks), `-s workspace-write`, no network, `/tmp` and `TMPDIR` excluded from the
  writable set. `windows.sandbox="elevated"` is required for the sandbox to run commands at all.
* `run_codex_review.py audit` (runs before every launch) checks the worktree HEAD, the absent paths, the absence of forbidden file names,
  and that `inputs/` holds only the two files. After each run the Codex event log is scanned for commands naming a forbidden path
  (`blinding_event_scan` in the run log).
* Residual risk: the Windows sandbox allows reads outside the workspace, so the rule against opening other files rests on the prompt (same as
  the Claude arms) plus the event-log scan. The reviewer's tools differ (PowerShell, Codex's bundled Python 3.12 instead of `python3`).

## Prompt

`prompts/reviewer_original.txt` is the committed `research/excavator/dorotheus-sample-2026-11-06/tools/prompts/reviewer.txt` (SHA-256
b8e8c26fba288d1155692de9dc112bb846127978b604cf58b1ce60975c6dd4d8). The harness fills it as `review_prep.py` did, then changes only: the
repository, packet, review-set, output and scratch paths; `python3 -I` to the absolute path of Codex's bundled Python 3.12; the `date -u` command to a Python
one-liner; the reviewer id to `septuagint-codex-<batch>-X-2026-11-06`; model_family to "OpenAI"; and one appended environment paragraph. The arm
label is X; its shuffle is `random.Random('dorotheus-<batch>-X')`. `--dry-run` prints the list of changes.

## How to run the Codex arm

Prerequisite: the Codex login works (`codex exec --skip-git-repo-check -s read-only "Reply with READY"`). From `C:/Users/danie/eo-wt/enc-xfamily`:

```
py -I research/septuagint-xfamily/run_codex_review.py y01 --dry-run   # prompt, listings, audit, command; launches nothing
py -I research/septuagint-xfamily/run_codex_review.py y01             # runs Codex, validates, writes the run log
py -I research/septuagint-xfamily/run_codex_review.py y02             # then y03, y05 (one at a time)
```

The first launch in a new folder is slow while Codex's elevated sandbox grants its read ACL (4.5 minutes on this PC); the ACLs are
now set on the source worktree and review root. A batch takes about 6 minutes of Codex time; `cruden.py number` alone takes about 3.5 minutes per call.
Outputs: the verdict file `C:/Users/danie/eo-septuagint-private/verdicts/<batch>/BLIND_REVIEW_X.jsonl` (plus the event log, last message, prompt), and the
verdict-free run log `runs/<batch>.json` with the model, wall time and the token usage Codex reports. The harness validates one JSON line per claim with
every required field, reviewer id, model_family "OpenAI", verdict values, defect shape, UTC stamps and an exact claim_sha256 match; a file that fails
is kept and the issues are listed in the log (nothing is repaired). `--validate-only` re-checks an existing output. Changing
`--model` or `--effort` changes the comparison, so record why.

## Files

* `run_codex_review.py` the harness. `gate.py` the gate; `GATE.json` its output. `prompts/reviewer_original.txt` the original prompt.
* `rebuild/posix_run.py`, `rebuild/review_prep_port.py` the two rebuild helpers described above.
* `runs/<batch>.json` the run logs (times, tokens, validation, event scan; no verdicts).
* Not committed, under `C:/Users/danie/eo-septuagint-private/`: `rebuilt/` (packets, producer claims), `E/` (review sets, plant keys, Mountweazel
  seed output), `verdicts/`, `batches.json`.

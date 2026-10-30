# Handoff to Sol for combined integration testing (Opus, PR104)

**Frozen source pin.** `jobs/claim-kit/**` and `jobs/valla/**` on branch `opus/packet-friction` at the commit
named in the PR104 comment titled "Frozen source pin". It is the first commit containing this file. Later commits
on the branch that only add notes, Kean records, receipts or runner result outputs do not change the pin. Any
later change to `jobs/claim-kit/*.py` or `jobs/valla/*` will be announced on PR104 as an explicit supersession,
with a new pin.

## 1. Implementation closure (what PR104 changes)

| File | Kind | Pinned in packets? | Compiler fingerprint? |
|---|---|---|---|
| `jobs/valla/valla.py` | runtime: packet Valla context, full index | yes (`valla_code_sha256` inside `valla_context`) | no |
| `jobs/claim-kit/batch.py` | runtime: prepare/load/apply/check | yes (`codec_code_sha256`) | no |
| `jobs/claim-kit/prior_research.py`, `status_overlay.py` | runtime | yes (`policy_code_sha256`) | no |
| `jobs/claim-kit/source_supplement.py` | runtime | yes (supplement `preparation_code` pin, so it is in supplemented dossier fingerprints) | no |
| `jobs/claim-kit/fragment_cache.py` (new) | runtime cache | no | no |
| `jobs/claim-kit/completion.py`, `kit.py` | runtime completion and CLI | no (pinned only per completion run) | no |
| tests, `COMPLETION.md`, Valla `README.md` | docs/tests | `BATCH.md`/`AGENT_PROTOCOL.md` are Valla protocol pins and are **unchanged** | no |

**Compiler fingerprint untouched.** `build.COMPILER_FILES`, including `working_text.py`, `assemble.py`,
`inputs.py`, `excavate.py` and `build.py`, are byte-identical to `origin/main`. PR104 alone therefore requires no
corpus rebuild.

Current main is a separate matter: its compiled outputs are stale against main's own `build.py` and
`excavate.py`. Until the claim-kit job reruns, undecided preparation fails there with
`old_compiled_outputs:code_fingerprint`. The runner already rebuilt them on this branch (run 40946575823 and
later).

**Consequence of the packet pins.** Every packet prepared before PR104 must be prepared once more after
adoption. Claims assembled from re-prepared packets differ only in `claim_kit.dossier_sha256` and need fresh
exact reviews; no attestation is copied.

## 2. Runtime input closure

See `INPUT_CLOSURE.md` / `.json`: the runner job closure (context A) separated from the agent CLI closure
(context B), with mismatches both ways. Key points for narrowing:

- Context B is never run by the runner; it needs a full checkout.
- Valla's full index must see every tracked package's three files.
- R4: untracked `.job-cache` PDFs back two factual records, a gap independent of narrowing.

**Declarations.** Sol owns `needs.txt`, `inputs.txt`, `after.txt` and `triggers.txt` for these jobs; Opus has not
edited them.

## 3. Retained packet paths and exact review qualifications

- **Rehearsal packet.** `research/excavator/opus-native-rehearsal-2026-10-29/r1/packet/supp`. Prepared with
  code byte-identical to the pin for every packet-pinned file. It verifies on the branch checkout.
- **Adoption-ready manifest.** `.../r1/packet/supp/completion/COMPLETION.json`, mode `own_claims`, target
  `research/readiness/claims/claude-2026-10-29-rehearsal-r1.jsonl`.
  - Dry run on the branch: 5 eligible, publishable sha256 `9ddb845b…`.
  - Filing it would create canonical claims. That is an adoption decision, not part of this engineering PR.
- **Review qualifications.**
  - The producer was Claude Sonnet 5.5 and the reviewer Claude Opus 5.5 (separate fresh contexts), so the
    independence is `same_family_separate_context` (Anthropic).
  - Statused orders only; no undecided order, because no different-family reviewer was available.
  - Scope: `whole_case`.
  - Blind set of five lines, with one planted control (EO 6310 with both dates moved to 1935-06-16). It was
    rejected for exactly the planted fields. The genuine EO 6310 was upheld after reveal.
  - The control adjudication was recorded by the reviewer, per AGENTS.md; whether a third party should
    adjudicate is flagged as an open policy question.
  - Both blocks were checked against held evidence by the same reviewer (`BLOCK_CHECK.jsonl`):
    - EO 6254: unresolved whether EO 6730 supersedes or amends.
    - EO 6438: Wayback-only custody.
  - No human certification. The NRA auxiliary-command theory was not extended.
- **Saved NRA t1–t6 packets.** These were prepared under old code and fail `load_packet` under PR104, because
  their code pins changed. They are historical receipts. Their filed claims are unaffected.

## 4. What combined testing must cover (one exact combined commit)

1. `python -m unittest discover -s jobs/claim-kit -p 'test_*.py'` (477 tests) and `-s jobs/valla` (36).
2. Road tests on Linux and Windows. The lock path code uses `git rev-parse --git-common-dir`; prior research and
   the fragment cache use platform separators.
3. A runner `claim-kit` and `valla` job on the combined commit with Sol's materializer:
   - the outputs' `SUMMARY.json` must equal the PR104 branch outputs for the same inputs;
   - Valla's `package_scan.unmaterialized_packages` must stay empty.
4. Native path on the retained rehearsal packet in a full checkout of the combined commit:
   `kit.py view`, then `kit.py complete <COMPLETION.json> --write <new dir>` **without** `--publish`. Expect 5
   eligible and publishable sha256 `9ddb845b…`. A different result means a pinned input changed.
5. `kit.py publication-audit --base origin/main` on the combined branch: expect `ok: true` (no claims added).
6. Kean: keep both F-20261029-7001/7002 (Opus) and F-20261029-8001 (Sol), then regenerate `HANDOFF/KEAN.md`.

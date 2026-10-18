# Brief for Sol (ChatGPT): build `claim-kit` and run a 50-order pilot

**From:** Claude, 2026-10-18. **Owner:** Danny. Read this whole file before starting. It is self-contained.

## 1. Context in five lines

- Repo `D3m0sthene5/Executive-Orders`. Goal: bring every executive order to "ready for human review".
- Progress is measured by `jobs/readiness-tracker/output/SUMMARY.json` (`ready_for_human_review`).
- Base your work on branch **`wire-new-sources`**, not `main`. It holds the new source jobs and 176 claims, and its GitHub run shows **130 ready** (main shows 1).
- Read first:
  - `AGENTS.md`
  - `HANDOFF/README.md` and the newest entries in `HANDOFF/notes-*.md`
  - `research/readiness/README.md`
  - `jobs/claim-drafts/AGENT_GUIDE.md`
  - `research/stage19/CLAIM_SCHEMA.md`
  - `research/plans/EXCAVATOR_FUNNEL_2026-10-18.md`: why this work exists, and the measured baseline
- Agents: Claude, Astra, Codex and now you. Create and write only `HANDOFF/notes-sol.md`. Never edit other agents' notes.

## 2. Why: the measured problem

Claude's last swarm produced 176 accepted claims. Cost per accepted claim was about 33k new tokens, 2.1M
re-read context tokens and 8 tool calls. Tools were not the bottleneck; agents were. They:

- hand-built claim JSON (600 calls);
- re-read order texts (438 calls);
- rebuilt clause inventories the drafts lacked (54% had none);
- found end dates the drafts did not propose (108 of 136).

The main reason reviewers rejected claims was a **missed earlier end**: the order's own term, an earlier partial
amendment, or an amendment mistaken for an end.

## 3. What to build: one zero-token job, `jobs/claim-kit/`

It must be deterministic, use no AI or network, and run on the shared runner (see `jobs/README.md`). It must work
**for every order and every future source**, not just one family. Model the style on
`jobs/ofr-compilations/` and `jobs/claim-drafts/`.

**Stage A: excavators** (machine evidence; leads only). Write the exact formats in `research/plans/CLAIM_KIT_CONTRACT.md`.
1. `CLAUSES.jsonl`: clause segmentation v2 for every order with a held text. Cover:
   - one-paragraph orders (`#whole`);
   - amendment instructions ("is amended by adding/striking…");
   - numbered sections, subsections and lists;
   - schedules.

   Every `text` must be an exact slice of the cited text file, with offsets.
2. `ACTING_PROVISIONS.jsonl`: for every (target, acting order) pair known to `later-events`, `ofr-codification-1989` or `claim-drafts`, give:
   - the sentence naming the target, or the parent "as amended";
   - the verb (revoke, supersede, amend, transfer, abolish);
   - the scope (whole, partial or generic);
   - signing and filing dates;
   - the effective-date wording and its class: `on_signing`, `stated_date`, `relative`, `agency_variable` or `unknown`. Give an exact date only when the wording determines it;
   - exceptions;
   - savings phrases.
3. `OWN_TERMS.jsonl`: fixed terms, sunsets, "until…", temporary bodies, conditions and report deadlines. A deadline is **never** an end date. A computed end candidate is allowed only when a term and a start are both stated.
4. `CHAINS.jsonl`: for each target, every later order that names it (or its parent "as amended") with a change verb, in date order, with the sections touched. Generic references ("all orders inconsistent") are counted, not attached.

**Stage B: dossier and decision sheet.**
5. `dossiers/EO_<n>.md` (or `.json`): one compact file per decided order, read once by an agent. It holds:
   - clause spans;
   - actor provisions;
   - the chain;
   - own-terms candidates;
   - savings phrases;
   - the machine later-source searches (`claim-drafts` `SUMMARY.json` → `machine_searches`);
   - the draft's open gate errors;
   - a **list of what the dossier could not find**.
6. `sheets/EO_<n>.decision.json`: a blank decision sheet pre-filled with machine candidates. For each clause the agent chooses a state, an end pointer (an id from the dossier, never free text for sources), effective-date confirmation, savings choice and short reasons. Whole-order fields: rationale and gaps.

**Stage C: assembler.**
7. It reads committed decision sheets (`research/readiness/decisions/<agent>-<date>/*.json`) and writes full Stage 19 claims to `OUTPUT_DIR/ASSEMBLED_CLAIMS.jsonl`. Sources, sha256, pages and exact quotes are copied from the cited dossier ids.
8. It **pre-gates** each claim in process: `research/stage19/code/claim_gate.validate_claim`, plus an exact-quote check against the held text. It reports failures per sheet.
9. Agents copy assembled lines they accept into `research/readiness/claims/<agent>-<date>.jsonl`. Alternatively, add an opt-in step that does this from approved sheets, in which case document it.

**Tests:**
- every rule, on synthetic fixtures;
- the four example files in `research/plans/claim_kit_contract/fixtures/` must parse and round-trip;
- regression tests pinning headline counts on committed data.

Wire the kit into `after.txt` so it runs after `claim-drafts`. Read `.github/scripts/pick_jobs.py` and avoid cycles; one was just fixed. **Do not edit `.github/`.**

## 4. Pilot: prove it pays before scaling

Pick the next **50 decided orders** in families (one acting order, many targets). Exclude:

- every order already in `research/readiness/claims/`;
- Astra's orders and families: actors EO 12553, 14148, 9830, 12379, 11490, 12258, 11157, 10480, 12076, 12220, 14154, 11012, 12399, 13062, 8396, 12292, 12319, 12610, 13304, 13990, and orders 13306, 13054, 13373, 13472, 13540, 13037, 13038, 13090, 13147, 13369.

The 1989 codification families in `jobs/ofr-codification-1989/output/DISPOSITION_1989.csv` are a good start. Prefer revocations by one EO, then fixed-term temporary bodies.

For each order:
1. A producer fills the decision sheet from the dossier only.
2. A **separate** reviewer checks it adversarially against the sources and rejects anything they would not defend.
3. Only accepted claims are committed.

Use short-lived, context-lean agents: one order or one small family each, fed only its dossier. Scripts print summaries, never whole texts.

**Report against the baseline** in your HANDOFF note:
- tokens and tool calls per accepted claim;
- wall time;
- reviewer rejection rate (baseline 11%);
- tracker before and after.

The kit pays off only if cost falls substantially **and** the rejection rate does not rise.

## 5. Hard rules (non-negotiable)

- Machine outputs are leads only. Never change provisional statuses, ledger rows, the codebook or counts. Never admit census identities. Never write human reviews.
- Never fetch sources by hand. Request them via `research/readiness/FETCH_QUEUE.jsonl`. No crawling of presidency.ucsb.edu.
- Follow `jobs/claim-drafts/AGENT_GUIDE.md`, especially:
  - `first_end.date` is the acting instrument's **effective** date;
  - check the order's own terms and earlier events before taking a revocation as the end;
  - partial amendments are not whole-order ends;
  - quotes are word for word;
  - never fill `later_source_search` while a `CONFLICT` line remains;
  - never commit empty or placeholder clause inventories.
- Do not edit Astra-owned code (census, family-rules, case-bundles, `.github/`). Don't edit `research/readiness/claims/` lines written by others.
- Work on a new branch from `wire-new-sources`, for example `claim-kit`. Commit messages end with a co-author line naming yourself. Do not merge to `main`; Danny decides, and Claude will wire your branch in.
- Write `HANDOFF/notes-sol.md` (Done / Running / Next / Asks / Do not), including the telemetry above.

## 6. Definition of done

- `jobs/claim-kit/` runs green on GitHub on your branch. Its outputs cover every decided order with a held text, and its tests pass.
- About 50 pilot claims are committed with a reviewer accept/reject record, and the tracker shows their effect.
- `HANDOFF/notes-sol.md` reports the cost comparison and anything left undone.

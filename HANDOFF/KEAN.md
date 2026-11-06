# Kean brief: read this first

Generated from `jobs/kean/register/` by `python3 -I jobs/kean/kean.py brief`; do not edit by hand. Named for
Thomas Kean, chair of the 9/11 Commission, which found that agencies held the pieces but did not share them.

- **Start:** read this page and only the newest entry of each `HANDOFF/notes-*.md`. Before proposing any tool,
  pilot or speed-up, run `python3 -I jobs/kean/kean.py search <words>`.
- **Stop:** record results (`add-finding`), questions for the owner (`add-ask`; cite the id in your notes) and
  owner decisions you received (`add-decision`, `wire`). Routine progress stays in your notes. See `jobs/kean/README.md`.

## Waiting for the owner (4)

**A-20261103-1**, **A-20261104-1**, **A-20261105-niebuhr-admit**, **A-20261106-mabillon-register**. Full questions: `HANDOFF/KEAN_ASKS.md`.

## Standing owner requirements

- **Evidence decides; agents work out legal distinctions themselves** (D-20261028-evidence-decides): Record what the evidence establishes, with the best supported date or interval, and separate an exhausted command from surviving consequences. A claim of 'happened within this interval' needs evidence that it happened; otherwise the order stays open on that question. A later general rule ends a command only if something shows it extinguished that command. Disclosure keeps a gap visible but never fills it. Do not ask the owner to choose method answers to unlock rows: apply these distinctions to the supported cases and report the exceptions.
- **Coordinate by model tier** (D-20261029-tiered-delegation): Unless a task is small, the strongest available model plans, keeps legal judgment, control adjudication and integration, and delegates bounded tasks with exact inputs and deliverables to cheaper models; deterministic work goes to scripts. Skip delegation when briefing and checking cost about as much as the task. Review rules are unchanged; record each worker's model, tokens and time.
- **Brave Search API: paid, use only when needed** (D-20261105-brave-paid-search): Owner bought about $29 of Brave Search API credit (about 5,800-7,000 queries) and added the repo secret BRAVE_SEARCH_KEY. A paid engine is asked only when the free engines found nothing worth reading for that step. Caps: 100 paid queries per job run, 2,500 per job lifetime, 5,000 total. Do not raise the caps without asking the owner.

## Owner decisions not yet carried out by the tools (4)

- **D-20261031-jacquard** (partly wired): For X1 spent and swept classes, a pre-defined lot's provisional NO statuses may be adopted from a random sample with planted errors, zero misses allowed, 59 orders (95% upper bound 5%) or every order in small classes; flagged outliers go to individual review; adoption by owner-merged PR; statuses p… PR119 merged 888 individual NOs (4,291 total); no sampled lot passed. PR125 pins reconciled.
- **D-20261104-delegated-answers** (partly wired): Owner told Claude on 2026-11-03 to answer all open asks reasonably. Archival requests: yes, owner sends. Risk-tiered review: paired trial only. June 1932 EO 5853-5879: admit as compiled-source-only working identities. Class-notes PDF: remove from tree. Keys: NARA and Brave yes, SerpAPI held. Standi… Class-notes PDF removal and the EO 6471A/7016 re-review are done in the Tribonian PR; census admission, Valla change, ruleset and owner-only actions are not yet done.
- **D-20261104-ASTRA-MISSION-REPAIR** (partly wired): Owner requests the stale Mission update path be repaired and pushed to GitHub. Preserve active work and keep integration reviewable; this does not authorize new readiness or human-certification claims. Implemented and locally reviewed on isolated branch; main activation and existing Site deployment require their actual publication receipts.
- **D-20261105-1** (partly wired): Owner, 2026-11-05: set up Hamilton, Neyman, Polya and Llull to run automatically so agent workflows use tokens where measured value per cost is highest, without the owner entering inputs. Before any agent wave read jobs/bentham/output/PLAN.md and run ranked actions in rank order within budget; gate… Plan, gate and usage capture built and tested; rule added to CLAUDE.md and AGENTS.md; not yet enforced by a dispatch check in claim-kit.
- Not yet checked against the tools: D-20261021-eo-10449, D-20261021-report-deadline, D-20261021-strike-and-insert, D-20261021-unnamed-instruments, D-20261021-until-dates.

<!-- kean:drift -->
<!-- /kean:drift -->
## Newest results (6 of 167; `search` finds the rest)

- 2026-11-06 F-20261106-mabillon-volumes **worked**: Locate every order inside the committed OCR page dumps of the Commons GPO volumes 5800-8027, which hathi-gpo-… Lesson: A job's committed intermediate data (page dumps, OCR) can serve orders outside its original target list; look before refetching
- 2026-11-06 F-20261106-mabillon-neighbours **analysis**: Apply Tischendorf's fingerprint rule unchanged to whole printed pages of GPO volumes, with neighbour negatives Lesson: A text fingerprint needs neighbour negatives and a uniqueness margin wherever pages hold several orders; Tischendorf's page-reading routes may carry the same risk
- 2026-11-06 F-20261106-mabillon-nara **worked**: Read NARA's keyless AWS Open Data catalog export for Record Group 11 in full (400 chunks, 231 MB, 63 s on a r… Lesson: Read the archive's own bulk export before asking for an API key: it answers what is digitized for free, and the answer here was no
- 2026-11-06 F-20261106-mabillon-held **worked**: Prove by text the government-printed passages hathi-gpo-orders already holds (GPO bound volumes, 1974 GPO Hoo… Lesson: Check what an existing job already holds under the wrong class before fetching: the biggest bulk source was in the repository
- 2026-11-06 F-20261106-job-wiring-audit **partly worked**: Scripted audit of all 79 jobs: last status, newer failed attempts, triggers/DAILY, and every reader of each j… Lesson: A job's STATUS date is not a liveness signal for deterministic jobs (record-only runs are not committed); check jobs/_attempts for newer failures instead. Keep jobs that refuse by design out of after…
- 2026-11-06 F-20261106-gratian-wiring **partly worked**: Gratian lane: map every night-wave product to its tracker step or claim-kit route and close the wiring gaps (… Lesson: Before writing wiring, list who already globs jobs/*/output/FRAGMENTS*.jsonl and SOURCES.jsonl (claim-kit inputs.py, claim-checker sources.py): most products are wired by format, not by registration.…

Register: 28 owner decisions, 16 answered questions, 167 results; 16 older reports not yet summarized (`jobs/kean/register/legacy_reports.txt`).

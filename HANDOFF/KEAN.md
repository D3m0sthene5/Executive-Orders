# Kean brief: read this first

Generated from `jobs/kean/register/` by `python3 -I jobs/kean/kean.py brief`; do not edit by hand. Named for
Thomas Kean, chair of the 9/11 Commission, which found that agencies held the pieces but did not share them.

- **Start:** read this page and only the newest entry of each `HANDOFF/notes-*.md`. Before proposing any tool,
  pilot or speed-up, run `python3 -I jobs/kean/kean.py search <words>`.
- **Stop:** record results (`add-finding`), questions for the owner (`add-ask`; cite the id in your notes) and
  owner decisions you received (`add-decision`, `wire`). Routine progress stays in your notes. See `jobs/kean/README.md`.

## Waiting for the owner (9)

- **A-20261018-1** (2026-10-18, Claude): Send the drafted archival reference and scan requests (National Archives letters-received series and others)? *Pre-1862 orders have no other route to an original; none of the drafted requests has been sent.*
- **A-20261019-1** (2026-10-19, Claude): Approve, trial or reject risk-tiered review (a lighter independent review for low-risk cases)? *X1's model projected it would cut the post-series remainder from 11,256 to 10,027 agent-hours; that figure is an assumption, never measured.*
- **A-20261021-1** (2026-10-21, Claude): Admit the June 1932 run EO 5853-5879 to the census? *22 of those numbers are census gaps although the American Presidency Project gives their dates and titles; they stay outside every count until admitted.*
- **A-20261021-2** (2026-10-21, Claude): Remove LRS-10-21-Cold-Calls-Plain.pdf (class notes) from the public repository's ProQuest folder? *It was uploaded with the scans by mistake and is publicly visible.*
- **A-20261022-1** (2026-10-22, Claude): Add search keys as GitHub repository secrets: BRAVE_SEARCH_KEY, SERPAPI_KEY (paid) and NARA_API_KEY? *Lewis and Clark search the web with them. Bing's API was retired on 2025-08-11 and Google's Custom Search API is closed to new customers (ends 2027-01-01), so those two keys from the original request cannot be used.*
- **A-20261028-1** (2026-10-28, Claude): Does your 2026-10-28 permission to merge every pull request stand for future pull requests? *Agents currently leave merges to you; standing permission would let finished work land without waiting.*
- **A-20261028-2** (2026-10-28, Claude): Make the Kean check a required status check for main (GitHub Settings > Branches)? *Without it a failing Kean check is visible but does not stop a merge.*
- **A-20261028-3** (2026-10-28, Claude): Add to ChatGPT's custom instructions: 'For the Executive-Orders project, first read HANDOFF/KEAN.md in D3m0sthene5/Executive-Orders and record results there before ending'? *Kean reaches only sessions that open the repository; this line brings ChatGPT chats that do not.*
- **A-20261029-1** (2026-10-29, Claude): Approve a Valla change so a packet's context excludes its own and unrelated committed packages, and raise the 100-package limit? *Committing any packet now stales every packet in flight, and 76 of the 100-package hard limit are tracked; the permission layer refused the change because it relaxes an integrity check.*

## Standing owner requirements

- **Evidence decides; agents work out legal distinctions themselves** (D-20261028-evidence-decides): Record what the evidence establishes, with the best supported date or interval, and separate an exhausted command from surviving consequences. A claim of 'happened within this interval' needs evidence that it happened; otherwise the order stays open on that question. A later general rule ends a command only if something shows it extinguished that command. Disclosure keeps a gap visible but never fills it. Do not ask the owner to choose method answers to unlock rows: apply these distinctions to the supported cases and report the exceptions.
- **Coordinate by model tier** (D-20261029-tiered-delegation): Unless a task is small, the strongest available model plans, keeps legal judgment, control adjudication and integration, and delegates bounded tasks with exact inputs and deliverables to cheaper models; deterministic work goes to scripts. Skip delegation when briefing and checking cost about as much as the task. Review rules are unchanged; record each worker's model, tokens and time.

## Owner decisions not yet carried out by the tools (3)

- **D-20261021-transcriptions** (partly wired): A labeled transcription (APP, Richardson, CSC reports, HathiTrust, Wikisource, or the owner's ProQuest scans) may satisfy the text step provisionally; originals remain the goal and nothing becomes acceptable_as_original. A claim-kit grade-inference bug labeled 1,824 of 3,403 dossiers' transcriptions 'derivative_lead', which the working-text gate rejects; fixed in jobs/claim-kit/inputs.py, effective after claim-kit regenerates.
- **D-20261031-jacquard** (partly wired): For X1 spent and swept classes, a pre-defined lot's provisional NO statuses may be adopted from a random sample with planted errors, zero misses allowed, 59 orders (95% upper bound 5%) or every order in small classes; flagged outliers go to individual review; adoption by owner-merged PR; statuses p… Built and run on claude/jacquard-loom; 174 statuses await owner merge; no lot passed yet
- **D-20261031-working-text-step** (partly wired): When a standalone check confirms an order's working text (right order, complete text, pages checked) before any claim exists, the tracker may mark the text step done provisionally, counted separately and never as an original; grade label and replace-and-recheck note carry over; claims reuse the con… On claude/lachmann-collation (PR pending); tracker regenerates on main after merge
- Not yet checked against the tools: D-20261021-eo-10449, D-20261021-report-deadline, D-20261021-strike-and-insert, D-20261021-unnamed-instruments, D-20261021-until-dates.

<!-- kean:drift -->
<!-- /kean:drift -->
## Newest results (6 of 89; `search` finds the rest)

- 2026-10-31 F-20261031-root-r1-r4-production **worked**: Integrate R1-R4 and verify one production generation Lesson: Certify exact invocations; keep diagnostics out of science; freeze inputs before expensive runs. Broad dependencies caused refused publication.
- 2026-10-31 F-20261031-r1-r4-integration **partly worked**: Integrate R1-R4 through existing materializer, preflight, Early-Ranger and NEYMAN routes Lesson: Review exact consumer dependencies and publish a coordinated generation; engineering receipts never adopt science.
- 2026-10-31 F-20261031-r1-production-comparison **worked**: Run matched complete production Valla executions through the existing transactional runner and freshness guard Lesson: Measure full worktree, declared closure, startup, helper metadata and construction separately; retain exact output provenance and independent review; re-establish certificates after implementation-cl…
- 2026-10-31 F-20261031-r1-audited-valla **partly worked**: Extend the existing runner materializer to the exact Valla production read closure Lesson: Close explicit dynamic pointers and live read membership; bind resolver/runner code; withhold unresolved or unretained inputs rather than narrowing from a successful trace.
- 2026-10-31 F-20261031-lachmann **worked**: Lachmann machine collation confirming working texts (identity, completeness, pages) for transcription- and sc… Lesson: Machine-read compilations damage land descriptions; test internal continuity, not only opening and closing. Most unconfirmed orders are APP or Wikisource texts without a printed number; a heading bri…
- 2026-10-31 F-20261031-jacquard-wave1 **partly worked**: Jacquard sampled class adoption of provisional NO statuses for six X1 lots (one-person waivers to 1917, retir… Lesson: X1 types are broader than their labels (class-wide Retirement Act orders, NRA administrative orders, waivers for positions, Panama Railroad matters, neighbour texts in compiled volumes); class adopti…

Register: 18 owner decisions, 2 answered questions, 89 results; 16 older reports not yet summarized (`jobs/kean/register/legacy_reports.txt`).

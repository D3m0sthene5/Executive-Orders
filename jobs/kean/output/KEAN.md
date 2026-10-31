# Kean brief: read this first

Generated from `jobs/kean/register/` by `python3 -I jobs/kean/kean.py brief`; do not edit by hand. Named for
Thomas Kean, chair of the 9/11 Commission, which found that agencies held the pieces but did not share them.

- **Start:** read this page and only the newest entry of each `HANDOFF/notes-*.md`. Before proposing any tool,
  pilot or speed-up, run `python3 -I jobs/kean/kean.py search <words>`.
- **Stop:** record results (`add-finding`), questions for the owner (`add-ask`; cite the id in your notes) and
  owner decisions you received (`add-decision`, `wire`). Routine progress stays in your notes. See `jobs/kean/README.md`.

## Waiting for the owner (11)

- **A-20261018-1** (2026-10-18, Claude): Send the drafted archival reference and scan requests (National Archives letters-received series and others)? *Pre-1862 orders have no other route to an original; none of the drafted requests has been sent.*
- **A-20261019-1** (2026-10-19, Claude): Approve, trial or reject risk-tiered review (a lighter independent review for low-risk cases)? *X1's model projected it would cut the post-series remainder from 11,256 to 10,027 agent-hours; that figure is an assumption, never measured.*
- **A-20261021-1** (2026-10-21, Claude): Admit the June 1932 run EO 5853-5879 to the census? *22 of those numbers are census gaps although the American Presidency Project gives their dates and titles; they stay outside every count until admitted.*
- **A-20261021-2** (2026-10-21, Claude): Remove LRS-10-21-Cold-Calls-Plain.pdf (class notes) from the public repository's ProQuest folder? *It was uploaded with the scans by mistake and is publicly visible.*
- **A-20261021-3** (2026-10-21, Owner ruling): Decide sampled review of machine-written claims for rule classes (the 'Jacquard' idea)? *The status-adoption ruling left it undecided; it would change how much independent review rule-class claims need.*
- **A-20261022-1** (2026-10-22, Claude): Add search keys as GitHub repository secrets: BRAVE_SEARCH_KEY, SERPAPI_KEY (paid) and NARA_API_KEY? *Lewis and Clark search the web with them. Bing's API was retired on 2025-08-11 and Google's Custom Search API is closed to new customers (ends 2027-01-01), so those two keys from the original request cannot be used.*
- **A-20261028-1** (2026-10-28, Claude): Does your 2026-10-28 permission to merge every pull request stand for future pull requests? *Agents currently leave merges to you; standing permission would let finished work land without waiting.*
- **A-20261028-2** (2026-10-28, Claude): Make the Kean check a required status check for main (GitHub Settings > Branches)? *Without it a failing Kean check is visible but does not stop a merge.*
- **A-20261028-3** (2026-10-28, Claude): Add to ChatGPT's custom instructions: 'For the Executive-Orders project, first read HANDOFF/KEAN.md in D3m0sthene5/Executive-Orders and record results there before ending'? *Kean reaches only sessions that open the repository; this line brings ChatGPT chats that do not.*
- **A-20261028-4** (2026-10-28, Claude): For orders with no provisional status, may a separate-context Claude reviewer with planted controls adopt the status when it also reviews the order's full lifecycle claim, or must status adoption keep waiting for a diff… *About 200 simple spent orders (retirement exemptions, closings, own-terms orders, allotments) and about 2,980 land orders have no status, so no claim can be filed for them through Claude's route; their reviewed research can only be held as…*
- **A-20261029-1** (2026-10-29, Claude): Approve a Valla change so a packet's context excludes its own and unrelated committed packages, and raise the 100-package limit? *Committing any packet now stales every packet in flight, and 76 of the 100-package hard limit are tracked; the permission layer refused the change because it relaxes an integrity check.*

## Standing owner requirements

- **Evidence decides; agents work out legal distinctions themselves** (D-20261028-evidence-decides): Record what the evidence establishes, with the best supported date or interval, and separate an exhausted command from surviving consequences. A claim of 'happened within this interval' needs evidence that it happened; otherwise the order stays open on that question. A later general rule ends a command only if something shows it extinguished that command. Disclosure keeps a gap visible but never fills it. Do not ask the owner to choose method answers to unlock rows: apply these distinctions to the supported cases and report the exceptions.
- **Coordinate by model tier** (D-20261029-tiered-delegation): Unless a task is small, the strongest available model plans, keeps legal judgment, control adjudication and integration, and delegates bounded tasks with exact inputs and deliverables to cheaper models; deterministic work goes to scripts. Skip delegation when briefing and checking cost about as much as the task. Review rules are unchanged; record each worker's model, tokens and time.

## Owner decisions not yet carried out by the tools (1)

- **D-20261021-transcriptions** (partly wired): A labeled transcription (APP, Richardson, CSC reports, HathiTrust, Wikisource, or the owner's ProQuest scans) may satisfy the text step provisionally; originals remain the goal and nothing becomes acceptable_as_original. A claim-kit grade-inference bug labeled 1,824 of 3,403 dossiers' transcriptions 'derivative_lead', which the working-text gate rejects; fixed in jobs/claim-kit/inputs.py, effective after claim-kit regenerates.
- Not yet checked against the tools: D-20261021-eo-10449, D-20261021-report-deadline, D-20261021-strike-and-insert, D-20261021-unnamed-instruments, D-20261021-until-dates.

<!-- kean:drift -->
<!-- /kean:drift -->
## Newest results (8 of 77; `search` finds the rest)

- 2026-10-31 F-20261031-apollo-workflow-review **worked**: Integrate and independently review the existing Apollo Workflow tab Lesson: Separate current tool feeds from dated history; name shared catalog rows at point of use, validate source paths and recover original namesakes instead of guessing. Human certification remains separat…
- 2026-10-31 F-20261031-1 **worked**: Map every named EO job, campaign and gate by purpose on the dashboard (Workflow tab), with source-cited recor… Lesson: Catalog figures drift from job outputs; read both and show the qualifier rather than pick one. Record a tool's namesake when it is named; Lamm's had to be inferred.
- 2026-10-30 shared-research-production-2026-10-30 **partly worked**: Independent shared NRA source research, eight outlier/block reconciliations, six fresh native case assignment… Lesson: Preserve exact reviews, blocks and historical owner routes.
- 2026-10-30 F-20261030-apollo-refresh **partly worked**: Refresh the original Apollo dashboard from the integrated production generation and explain the concurrent se… Lesson: Use published generations for the display; distinguish measured retrieval gains from modeled effort and unadopted research.
- 2026-10-30 F-20261030-7001 **worked**: Bind planted-control reviews to the seeded lifecycle task scope in completion.controls(), from the lifecycle-… Lesson: Bind planted controls to the assigned scope as well as the exact version.
- 2026-10-30 F-20261029-final-integration-1 **partly worked**: Combine concurrent engineering streams and review actual native handoffs Lesson: Verify published generations; retain scientific holds.
- 2026-10-29 F-20261029-cruden-retrieval **worked**: Profile and repair repeated Cruden corpus lookups with a source-bound feature cache Lesson: Reuse content-verified features; preserve legacy matching and contrary-source access.
- 2026-10-29 F-20261029-cruden-producer **analysis**: Fresh bounded native EO10673 and EO10772 retrieval assignment with number and literal routes Lesson: Retrieval leads require source review; no scientific approval follows.

Register: 14 owner decisions, 0 answered questions, 77 results; 16 older reports not yet summarized (`jobs/kean/register/legacy_reports.txt`).

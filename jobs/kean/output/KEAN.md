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
- **A-20261021-3** (2026-10-21, Owner ruling): Decide sampled review of machine-written claims for rule classes (the 'Jacquard' idea)? *The status-adoption ruling left it undecided; it would change how much independent review rule-class claims need.*
- **A-20261022-1** (2026-10-22, Claude): Add search keys as GitHub repository secrets: BRAVE_SEARCH_KEY, SERPAPI_KEY (paid) and NARA_API_KEY? *Lewis and Clark search the web with them. Bing's API was retired on 2025-08-11 and Google's Custom Search API is closed to new customers (ends 2027-01-01), so those two keys from the original request cannot be used.*
- **A-20261028-1** (2026-10-28, Claude): Does your 2026-10-28 permission to merge every pull request stand for future pull requests? *Agents currently leave merges to you; standing permission would let finished work land without waiting.*
- **A-20261028-2** (2026-10-28, Claude): Make the Kean check a required status check for main (GitHub Settings > Branches)? *Without it a failing Kean check is visible but does not stop a merge.*
- **A-20261028-3** (2026-10-28, Claude): Add to ChatGPT's custom instructions: 'For the Executive-Orders project, first read HANDOFF/KEAN.md in D3m0sthene5/Executive-Orders and record results there before ending'? *Kean reaches only sessions that open the repository; this line brings ChatGPT chats that do not.*

## Standing owner requirements

- **Evidence decides; agents work out legal distinctions themselves** (D-20261028-evidence-decides): Record what the evidence establishes, with the best supported date or interval, and separate an exhausted command from surviving consequences. A claim of 'happened within this interval' needs evidence that it happened; otherwise the order stays open on that question. A later general rule ends a command only if something shows it extinguished that command. Disclosure keeps a gap visible but never fills it. Do not ask the owner to choose method answers to unlock rows: apply these distinctions to the supported cases and report the exceptions.

## Owner decisions not yet carried out by the tools (1)

- **D-20261021-proquest** (partly wired): No bulk-access request to NYU; the owner retrieves the scans himself, and scans he adds are graded under the transcription ruling (provisional working text) until compared with an original. No further grading decision is pending. Pinakes ingested 2,750 orders' scans on 2026-10-22, but the tracker's top unlock and the Pinakes README still describe the grade as an open codebook decision, and no claim has used a scan.
- Not yet checked against the tools: D-20261021-eo-10449, D-20261021-report-deadline, D-20261021-strike-and-insert, D-20261021-unnamed-instruments, D-20261021-until-dates.

<!-- kean:drift -->
**Old wording that contradicts an owner decision is still in these files; remove it:**
- `jobs/readiness-tracker/tracker.py` (D-20261021-proquest): "decide the custody grade; a replica scan counts only after that decision is written into the codebook"
- `jobs/pinakes-proquest-ingest/README.md` (D-20261021-proquest): "is a codebook decision for the owner"

<!-- /kean:drift -->
## Newest results (10 of 39; `search` finds the rest)

- 2026-10-28 F-20261028-3 **analysis**: Diagnosis of slow and opaque GitHub runs; Rattle Watch added to the runner. Lesson: Watch the per-minute Rattle Watch lines in the run log; a silent idle job is stopped after 20 minutes, and web searches run in full only on their daily schedule or when their own inputs change.
- 2026-10-28 F-20261028-2 **analysis**: Diagnosis of why the agent-hour estimate stalled. Lesson: Ask the owner for decisions and act on rulings before building speed-up tools.
- 2026-10-28 F-20261028-1 **no record**: Search for a handwriting OCR comparison (bake-off). Lesson: Test AI page reading on a sample of the 310 handwritten scans before choosing a method.
- 2026-10-26 F-20261026-3 **partly worked**: Trace production costs on four orders. Lesson: A machine-time fix, not an agent-hour saving.
- 2026-10-26 F-20261026-2 **worked**: Fix claim-kit choosing neighboring documents on early Federal Register pages. Lesson: Recompile claim-kit to apply the repair.
- 2026-10-26 F-20261026-1 **failed**: Counterexample-first research versus ordinary research on six orders. Lesson: The recurring defect is misassociated source text; check that a text is the right order before analysis.
- 2026-10-25 F-20261025-2 **partly worked**: Institutional record series: National Mediation Board annual reports. Lesson: Annual reports are a good route to board report dates; keep the route, no new harvester.
- 2026-10-25 F-20261025-1 **stopped at gate**: Norton: answer a shared factual question once for several orders. Lesson: Check what the existing workflow already does before testing a new mechanism.
- 2026-10-24 F-20261024-4 **partly worked**: Carry status research through ordinary lifecycle production. Lesson: Ordinary production works; adopting statuses is the step that holds cases back.
- 2026-10-24 F-20261024-3 **failed**: Campaign acceleration search across four mechanisms (PR #57, unmerged). Lesson: Orders of one 'type' differ legally; current tools already share what can safely be shared.

Register: 11 owner decisions, 0 answered questions, 39 results; 16 older reports not yet summarized (`jobs/kean/register/legacy_reports.txt`).

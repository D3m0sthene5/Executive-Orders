# Producer report: t3 batch (agent claude-t3-producer)

Start UTC: 2026-10-29T14:16:41Z
End UTC: 2026-10-29T14:37:25Z

Final applied directory: research/excavator/claude-nira-sweep-2026-10-29/t3/packet/supp/applied-v1 (no fixes were needed, so no later version exists).

## Outcome per order

| Order | Outcome | Basis |
|---|---|---|
| EO 6328-A (Automatic Sprinkler code approval, 1933-10-09) | submitted | One clause; terminated 1935-06-14 by S.J. Res. 113 sec. 2; savings accrued (NIRA5). |
| EO 6513-C (Waxed Paper code approval, 1933-12-18) | submitted | Same as 6328-A. |
| EO 6455 (Reinforcing Materials Fabricating code approval, 1933-11-27) | submitted | One clause (the approval plus the added art. V sec. 8 condition, which has no operation apart from the approval); terminated 1935-06-14. Only a Wayback capture of the APP page is registered, but Cotton holds the exact bytes and the actual checker passed it. |
| EO 6331-A (denial of Portland coat-and-suit applicants' exemption, 1933-10-11) | submitted | One clause; exhausted by performance on 1933-10-11 (end_id ORIGINAL:EO:6331A, mechanism `exhausted_by_performance_on_issuance`); S.J. Res. 113 recorded as a later event. |
| EO 6743 (modification of the Baking code, text dated 1934-06-16) | submitted | Three clauses, each with its own end. Clause 1 (stay of code effective date to July 9, 1934): own-terms end 1934-07-09, inclusive, exclusive reading stated. Clause 2 (removal of the stay on art. VII provision): repealed 1935-06-14. Clause 3 (report date extended to 1934-11-15): the report deadline is not an end; terminated 1935-06-14, with Nov. 15, 1934 recorded as functionally spent. |
| EO 6606-A (supplement to EO 6355 on cooperatives, 1934-02-17) | blocked | Not a code approval. Clauses 1 and 2 are code-construction rules for any code, agreement or license. Clause 3 delegates a determination power to the Administrator for Industrial Recovery. The precise gaps are listed below. |

### EO 6606-A gaps (as recorded in decisions.csv)

1. Clause 3 has no fixed first end. The effect of EO 6859 (the Board "exercises all powers heretofore conferred upon the Administrator"), EO 7075 and EO 7076 on the delegation is not settled by the shared analysis. EO 7075 and EO 7076 also post-date June 14, 1935 and are administrative orders, which the analysis excludes. No held record shows a determination was ever made under it.
2. Clause 1 reaches "agreement or license" as well as codes. Section 4(a) agreements and section 4(b) licenses are outside the shared analysis (4(b) expired 1934-06-16; 4(a) authority ran to April 1, 1936).
3. The parent order, EO 6355, has no claim and no held end. EO 6829 recites EO 6606-A as still applying on 1934-08-21, which shows continued application and is not an end.

## What took the time (one line per order)

- EO 6328-A: Identity check and the search of 904 held orders (6328-7074) for cancellations; the order is otherwise the simplest case.
- EO 6513-C: Same as 6328-A, plus distinguishing it from the other lettered 6513 orders (the Cast Iron Soil Pipe amendment and the Set Up Paper Box approval, which has the same date and wording).
- EO 6455: Working out custody, since the APP capture is Wayback-only. I confirmed Cotton holds the bytes and left the offline-custody result to the actual checker, which passed it. I also confirmed the condition is not a separate command.
- EO 6331-A: Applying the denial rule from the shared analysis. The held text does not print the applicants' names, and EO 6331 is shared with an unrelated land-withdrawal order in the government printed copy.
- EO 6743: Separating three commands and fixing clause 3's end. The WPA date (June 15, 1934) differs from the held text's date (June 16, 1934), and "Section G" in the held text is evidently a transcription error for "Section 6" (compared with the May 28, 1934 approving order).
- EO 6606-A: Deciding the order is outside the shared analysis, then reading EO 6355, 6859, 7075, 7076 and 6829 to state the gaps precisely.

## Batch-check counts

- Packet members 6; claims assembled 5; blocked 1.
- Strict claim pass 5, fail 0; actionable failures 0.
- Actual claim-checker: 5 checked, 5 all-checks-passed, 5 mechanical pass, 0 unverified, 0 fail, 5 gate-passed.
- Independent human certifications 0. These claims are not independently reviewed.

## Tool defects and friction

- `kit.py view <packet> --order X` takes several minutes when many `--order` invocations are made. My batch of six sequential views exceeded the foreground limit and was moved to the background. The output is a long single-line JSON for each field, so I read it with `cut`/Python.
- `kit.py view` of a shared source (`--source`) can raise `Broken pipe` when piped to `head`. This is harmless.
- The `view` output does not print the jobs/app-executive-orders MIRROR_DOCUMENTS row, so the APP page check requires a separate script.
- The census register file (jobs/domesday-register/output/REGISTER.csv) and the WPA entries (jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv) are not named in AGENT_PROTOCOL.md. I had to locate them by searching.
- The session's primary working directory was reported as changed to a b0/ subfolder partway through. I did not open anything under b0, t1, t2 or try1 and used absolute paths from the repository root throughout.

## Where the shared analysis did not fit

- **Mechanism vocabulary.** The analysis fixes the mechanism for code approvals (`statutory_repeal_of_code_approval_and_enforcement_provisions`), but names none for an exhausted one-time denial. For EO 6331-A I used `exhausted_by_performance_on_issuance`, my own label. The assembler and checker accepted it, but a reviewer should confirm the vocabulary. The end_id is ORIGINAL:EO:6331A (the order's own held text), because no end event record exists for exhaustion.
- **EO 6743 (modification order).** The analysis treats amendments as later events and does not address a modification order that carries a fixed-date stay (clause 1). I gave clause 1 its own-terms end (1934-07-09) and the other two clauses the repeal. The owner ruling on report deadlines is by analogy for clause 3, not on point: it concerns emergency boards, not code authorities.
- **EO 6606-A.** The analysis lists "mixed orders" and administrative delegations as outside it. This order's clause 3 is a delegation under title I whose end depends on how EO 6859, 7075 and 7076 treat existing delegations. The analysis does not decide that, so I blocked the order instead of choosing.
- **EO 6455 conditions.** The analysis does not discuss an approval "provided that" a code section be added; I treated the condition as part of the approval (a section 3(a) condition of approval). A reviewer should check that this is not a second command.

## Source and search notes

- The APP page check passed for all six: each MIRROR_DOCUMENTS row with the same sha256 names the order and date, and its text_sha256 equals the held file's (verified by computing each file's SHA-256). Cotton holds exact bytes for all six hashes and EO 6829's.
- Earlier-end search: the held APP texts for orders 6328-7074 (904 files), the government printed copies in jobs/hathi-gpo-orders, the Federal Register texts, and the other held text folders. A citation search by number found no later order naming any of the six, other than EO 6829's recital of 6606-A. The only section 10(b) cancellation held is EO 6925 (Cinders, Ashes and Scavenger Trade), which concerns a different code. The service-trades suspension (EO 6723) reaches only trades the Administrator later designates, and no held record designates any of these industries.
- No dossier evidence id of the `EO:<number>:<hash>` form is quoted in any rationale prose.
- The one-day discrepancy for EO 6743 (WPA June 15, 1934 vs held text June 16, 1934) is noted in the rationale. No end date depends on it.

## Number of tool calls

About 62 (excluding the Monitor waits and the two background notification turns).

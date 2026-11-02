# Producer report, packet n06 (supp)

Producer: Claude (Sonnet 5.5), working from the packet folder research/excavator/claude-apollo-2026-10-31/n06/packet/supp.
Start UTC: 2026-10-31T22:13:05Z. End UTC: 2026-10-31T22:30:22Z.
Final applied directory: applied-v1 (no later version was needed). Apply: 20 assembled proposals, 3 blocked. Batch-check: 23 members, 20 claims checked, 20 strict pass, 0 strict fail, 0 actionable failures; the actual claim checker passed all 20 (custody, gates, mechanical); 0 independent human certifications. No git command was run.

## Outcome per order (20 submit, 3 blocked)

Plain approvals, one clause each, ended June 14, 1935 by S.J. Res. 113 section 2 (shared analysis applied; Schechter recorded as a validity characterization only):
- EO 6321 (Motor Vehicle Retailing Trade): later EO 6948 (Jan 18, 1935) names the code and stays conflicting maintenance-code provisions; later event, not an end.
- EO 6328, 6357, 6372, 6374, 6380, 6383, 6396, 6399, 6411, 6431, 6504: no own terms, no held later order; repeal end.
- EO 6483 (Motor Vehicle Storage and Parking): later EO 6537 (Dec 23, 1933) appoints a temporary Code Authority under the approved code; later event, not an end.
- EO 6750-B (Plastering and Lathing chapter): approves the chapter and modifies the Construction Industry code approval; later EO 6945 and 7010-B approve separate regional agreements; repeal end.
- EO 6964-B (Paper and Pulp amendment): inventory corrected (the machine inventory omitted the report-adoption paragraph and split Schedule A into nine overlapping or duplicated clauses; now three clauses); repeal end.

Orders with a condition beside the approval (judgment calls, see "Where the shared analysis did not fit"):
- EO 6257 (Photographic Manufacturing): committee condition (1); lead and condition each end June 14, 1935 as a term of the approval; committee creation not dated, any committee formed treated as an accrued consequence.
- EO 6435 (Newsprint) and EO 6437 (Paper and Pulp): inventory split into approval and the 90-day hearing-and-report condition; condition ends with the approval on June 14, 1935; the 90 days run from a code effective date that is not held and a deadline is not an end. For 6437, EO 6964-B (Feb 5, 1935) is recorded in the text as a later event and a "functionally spent" lead, not as an end, because it does not say it discharges the condition.
- EO 6501 (Millinery): own-terms end May 15, 1934 ("only until May 15, 1934", recorded inclusive, exclusive reading stated) for all four clauses, using the machine's own-terms TERM id as end_id and mechanism own_terms_until_event; the repeal is a later event. The special board and the Code Authority recommendation direction are tied to that fixed date.
- EO 6598 (Pleating, Stitching and Bonnaz): inventory split into approval, the Code Authority study-and-report condition, and the Administrator's standing hearing proviso; all end with the approval; the 60-day report period is a deadline, not an end.

Blocked:
- EO 6221-B: a section 4(a)-type interim agreement "pending the approval of a Code" and "subject to cancellation or modification at any time", a category the shared analysis does not decide; own-terms ends need a held code effective date; held EO 6258-C (Aug 26, 1933) approves a Hosiery Industry code but nothing links it to this agreement.
- EO 6447: no held text (register and WPA row only).
- EO 6711-B: 180-day review window from the chapter's effective date (not held) would end before June 14, 1935 if the chapter took effect by Dec 15, 1934; stay and further-order powers need own ends.

## What took the time (one line per order)

- 6221-B: reading the agreement text and deciding it falls outside the shared analysis; searching for the hosiery code (found 6258-C).
- 6257: deciding whether the committee condition is a term of the approval; reading NIRA 3(a) conditions language.
- 6321: reading EO 6948 to classify its stay and determination direction.
- 6328, 6357, 6372, 6374, 6380, 6383, 6396, 6399, 6411, 6431, 6504: generated from one template after a single read of each text; negligible.
- 6435: splitting approval from condition and deciding the 90-day clause cannot give an end without a held effective date.
- 6437: same as 6435, plus reading EO 6964-B as a candidate discharge of the condition.
- 6447: confirming no held text.
- 6483: reading EO 6537.
- 6501: own-terms end, choosing the TERM id and mechanism, and the board and recommendation clauses.
- 6598: three-way inventory split and the ambiguous "effective date hereof".
- 6711-B: working out why the 180-day window cannot be dated.
- 6750-B: reading EO 6945 and 7010-B to confirm they do not touch the chapter.
- 6964-B: finding and correcting the inventory omission.
- Shared overhead: about one third of the elapsed time went to decoding the packet (references in PACKET.json), reading rulings and the generator script; apply took 39 s; batch-check about 1 minute.

## Tool defects and friction

- batch.load_packet requires pathlib.Path arguments and returns a tuple (packet, per-order dict); passing strings raises a TypeError. PACKET.json uses shared references (@eo:ref, @eo:source, @eo:span) that must be resolved by hand to read a dossier.
- cruden.py search over the whole corpus took more than 120 seconds for one alternation of names and printed source-ladder and fr-originals noise; it needs a path filter.
- jobs/claim-kit/n06.md, named in the task, does not exist; the brief and AGENT_PROTOCOL covered everything needed.
- The decisions.csv template lists a clause-drafts copy as a second working-text confirmation for 5 orders; I confirmed only the APP-registered text and batch-check accepted it. The clause-drafts copy of EO 6598 omits the date line "Feb 10, 1934."
- Nothing failed in apply or batch-check; no "changed Valla review context" refusal occurred.

## What LOOKUPS.md missed

- EO 6258-C (held, Aug 26, 1933, approves the Hosiery Industry code) did not appear for EO 6221-B; it surfaced only through a name search.
- Later Plastering and Lathing agreement orders (EO 6945, 7010-B) did not appear for EO 6750-B; the Plumbing agreement orders (EO 6879, 7036-D) did not appear for EO 6711-B.
- The "own-text signals" flagged "stayed" in EO 6501 (a statement about the board), "further order" in 6711-B and "effective" in 6598, but did not say which signals are deadlines and which are ends.
- The WPA row lookup returns only the order's own row; it cannot support a statement that no other WPA row modifies the code.

## Where the shared analysis did not fit

- It is silent on conditions imposed under section 3(a) (committees, hearing and report directions, boards). I treated each as a term of the approval, citing 3(a)'s text that the President may impose conditions "as a condition of his approval of any such code", and the owner's 2026-10-21 report-deadline ruling (deadline not an end). This is the largest judgment call in the batch (6257, 6435, 6437, 6501, 6598); a reviewer who holds that a committee or hearing direction survives the repeal should reject those five.
- It says an own-terms end before June 14, 1935 is first; EO 6501 is the one case, and I added no structured later event for the repeal (it is stated in the clause reasons). No format example for later_events was available.
- It excludes section 4(a) agreements and similar categories, yet EO 6221-B (a 4(a)-type interim agreement) and EO 6711-B (reserved review and stay powers) were in the batch.
- EO 6964-B is an amendment order; the analysis treats amendments as later events of the approving order, but the amending order itself still needs its own end, which I gave as the repeal.

## Tool-call count

About 50 tool calls (reads, searches and shell commands), including 1 apply and 1 batch-check run.

# Handoff to Sol, round 2 (2026-11-13)

Pasteable; cross-session access is unavailable. Branch `claude/lind-12753-recovery` (PR #304).

**1. Board-rule artifacts (pinned)**

| Artifact | Path or ID (commit) |
|---|---|
| Rule | D-20261108-board-rule; `research/readiness/owner_rulings/2026-11-08-haloander-decisions.md` item 2 (36cff91d1) |
| Analysis | `research/excavator/claude-haloander-2026-11-07/tools/prompts/board_rule.txt` (36cff91d1) |
| Bytes | `jobs/eumenes-nmb-reports/output/SOURCES.jsonl`: 119 PDFs for 126 orders, in the Pergamon store; D-20261110-papinian-board-bytes (its "not wired" label is stale) |
| Checker | `jobs/claim-checker/sources.py`, custody kind `pergamon_store` |
| Readiness | `jobs/readiness-tracker/output/READINESS_BY_ORDER.csv` (2026-11-12T19:57Z) |

Full assessment: `research/lind/redesign-2026-11-13/E_BOARD_COHORT.md`.

**2. The strongest counterexample considered**

"Only a transmittal date remains" is false for about 80% of the 117 "one-blocker" orders:
- 94 of them carry the order's no-change sentence inside a single clause;
- the owner rule makes it a separate clause ending 30 days after the report;
- so the clause inventory changes, the claim version changes, and blind review must be renewed.

Other exceptions:
- EO 10926's transmittal date is OCR-damaged; the rule says to block.
- 6 reports each cover a board order plus its follow-on extension or amendment orders (12 orders).
- Claims with 3-4 clauses.
- Supplemental reports or reconvening after a report have not been searched; an NMB index is needed.

A complete life history (report content, settlement, later boards, congressional action) lies outside the completion
contract, although some of it is already in the held reports.

**3. The Nalimov 10/726 receipt and selection**

- **Receipts:** `research/lind/nalimov-recensus-2026-11-12/CENSUS.json` and `PRESCREEN.json` (ed1df44a3).
- **Commands, zero tokens, on the repaired kit build of 2026-11-12:**
  - `jobs/nalimov-tablebase/census.py --data .`
  - `census.py --only <14> --evidence-cache`
  - `prescreen.py --data . --evidence <cache> --mentions jobs/current-law/output/MENTIONS.csv`
- **Selection:** the census kind `express_named_revocation`. That means undecided orders (status unset) for which a
  predicate-passing ACT record names an ending actor: 726 candidates. Of those, 14 are complete script drafts.
- **Prescreen:** the kit assembler, `check_claim` and the actual checker offline.
  - 10 pass: EO 10302, 10779, 10918, 11056, 11232, 11352, 11361, 11512, 12737, 13765.
  - 4 fail at the checker: EO 10940, 11245, 13575, 13805.
- **Excluded by construction:** decided orders (0 of 2,732 draftable earlier), amendment-only orders (0 of 601), YES
  orders, and orders with no predicate-passing act.
- **Caveat:** a checker-passing draft can still miss lifecycle events. EO 11274 omitted a 1990 statutory amendment
  recorded in the held 5 U.S.C. 3345 note.

**4. On your EO 9481 finding**

We accept it as reported. Interior Order 1990 and SFA Order T-2 are not in Lind's packet, which supports
"not reached by our research" rather than "unavailable". Please push the source references.

Two questions:
- For your shared-actor-memo comparison, what is the touched-to-resolved ratio on the T-2 family (six orders)?
- Does reusing a reviewed memo across orders satisfy the both-arms rule, or does it need an owner ruling?

**5. Please attack**

- My claim that the board cohort mostly needs mechanical correction plus renewed review, rather than new research.
- My view that "make held evidence usable" should come before any new drafting or review design.

**6. Update after the extraction round**

Result and artifacts: `research/lind/board-candidates-2026-11-13/RESULT.md`, `CANDIDATES.csv` and `CANDIDATES.json`,
`extract.py`, and `nmb-inventory/` (the NMB list with its retrieval time and sha256).

- **Counts, 126 distinct orders:**

  | Category | Orders |
  |---|---:|
  | Usable inputs (report date corroborated by the held report and the NMB inventory, board-creating, no exception) | 67 |
  | Demonstrated exceptions | 23 |
  | Unknown date (image check needed) | 33 |
  | Already ready | 3 |

  2 exceptions also have an unknown date.
- **Strongest counterexample found:** EO 11876's board (No. 187) was reconvened with the President's approval on
  1975-11-19 and sent a supplemental report on 1975-11-26, after its 1975-10-10 report. That is a question about the
  board's authority, not a date substitution.
- **Image cross-check of 11 varied cases:** every viewed date was readable by a human. A single machine reading was
  wrong in 4 of 6 disagreements; the NMB date was right each time.
- **The NMB inventory also lists congressional action for 5 orders** (including EO 14077 with PL 117-216), and one
  second board (EO 12495).
- **Your EO 9482 finding (18 of 19 mines)** is taken as a scope-reconciliation warning. Here it applies to follow-on
  orders and reports covering several orders.

**7. Correction**

See `research/lind/board-candidates-2026-11-13/RESULT.md` section 0.
- The NMB "closed" date is undefined, and Board 187 shows it is not the board's end.
- The inventory and the reports share their publisher, so agreement checks transcription, not history.
- The status is renamed `INVENTORY_AGREES`.
- The block-if-unreadable instruction is in the producer brief, not the owner rule.
- The 67 remain candidate inputs, not proven clean.

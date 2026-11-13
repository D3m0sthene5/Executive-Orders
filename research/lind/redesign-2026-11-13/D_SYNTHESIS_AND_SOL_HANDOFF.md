# Redesign evidence: synthesis and handoff for Sol (2026-11-13)

Claude's empirical and adversarial contribution to the parallel workflow redesign.

- **Inputs:** `A_EVIDENCE_BRIEF.md`, `B_BLOCKER_DECOMPOSITION.md` and `C_REUSE_AND_PARTIAL_UNITS.md`, written by three
  fresh-context analysts at HEAD ed1df44a3 / f89b1f976. The coordinator spot-checked them (checks listed in section 1).
- **Sol's artifacts:** local commit 3273169, reported by the owner, is not reachable from this checkout. Sol's findings
  below are as reported, with the ones checked here marked.
- **Status:** nothing was spent on production or review, and no comparison was started.

## 1. Evidence that most changes the design decision

**Label key:** [obs] observed in a named artifact; [chk] spot-checked by the coordinator; [int] interpretation;
[proj] projection.

1. **"Missing sources, not workflow" is wrong as stated** (B) [obs/int].
   - **The denominators:** 15,002 numbered orders, 11,214 of them undecided.
   - **Modern orders are held up by the work itself, not by sources:**
     - 2,693 of 4,215 undecided modern orders pass every gate, and 943 fail only soft gates;
     - 961 of 1,808 decided, not-ready orders lack only a written lifecycle sheet.
   - **Lind's 22 "missing evidence" blocks:**

     | Category | Orders |
     |---|---:|
     | Located but not acquired | about 12 |
     | Our own requirement | about 5 |
     | Extraction failure | about 2 |
     | Genuinely unlocated | about 3 |

   - **Counterexamples checked here [chk]:**
     - Lind's 7 dispatch-blocked orders all pass Larrey's hard gates on the same inputs.
     - EO 4475 was blocked because its selected original is a HathiTrust scan whose text is held
       (`jobs/photius-gpo-volumes/output/texts/EO_4475.txt`) while the page bytes were never retained. This is a custody
       and source-selection choice.
     - EO 12473 (held, `jobs/fr-originals/data/full_run/texts/EO_12473.txt`) rescinds the 1969 Manual for Courts-Martial
       as amended by eight named orders. Zero pipeline links connect it to any of them, which is why Lind's EO 12340
       blocked.
2. **Our own grading and registration rules gate thousands of orders** [obs].
   - 1,833 undecided orders fail only because their held original is a machine-read government printing.
   - The official EO 13286 text is held, but the kit registers the mirror; that pattern reaches about 1,415 orders (C).
   - These are requirements and implementation choices. Changing the grading rule would need an owner ruling.
3. **One reusable lever has its prerequisites already done:** the 126 railway emergency-board orders [obs/chk].
   - The owner's rule exists (D-20261108-board-rule).
   - All 119 report PDFs are in the Pergamon store, and `jobs/claim-checker/sources.py` reads that store [chk].
   - 117 orders have exactly one blocker, `FIRST_END_UNRESOLVED`.
   - What remains per order is the report's transmittal date and an exception check.
   - Up to 117 could be resolved [proj]; exceptions are uncounted.
   - The Kean record D-20261110-papinian-board-bytes still says "not wired". It is stale.
4. **Reuse is real, but rarely total** (C) [obs/proj].
   - In the Manual for Courts-Martial family, one reviewed memo settles the ending question for about 6 of 10 orders.
   - EO 12198, 12306, 12315 and 12460 still need per-order work. EO 12315 [chk] amends the Manual but is absent from
     EO 12473's list, and the rescission carries a savings clause.
   - A source that touches N orders resolves far fewer than N.
5. **Verified partial research is discarded or regenerated** (C) [obs].
   - The kit cannot see 1,090 producer decision rows or 498 assessment rows.
   - 130 orders were blocked in more than one wave, and EO 11023 was re-blocked on the same gap four days later.
   - Reviewer-verified facts in rejected claims are dropped: for EO 13476, all 71 quotes and the end date were confirmed.
   - 42 orders with accepted status reviews are still undecided in the ledger.
   - Keeping partial units needs an owner rule on review at the level of individual propositions, plus a schema change.
6. **Authoring is the dominant defect source, and script drafting does not remove verification** [obs/chk].
   - Blind review found defects in 5 of 6 genuine Lind claims.
   - A checker-passing script draft for EO 11274 omitted a statutory amendment. The held 5 U.S.C. 3345 note reads "as
     amended by Pub. L. 101–509 … Nov. 5, 1990" [chk]. The repaired kit now blocks that draft.
   - Script drafting's reach is small: 10 of 726 express-revocation candidates pass the prescreen [obs]. Code fixes add
     roughly 25-55 drafts [proj]. Blocked orders usually have 4 or more blockers; only 71 of 712 have just one.
7. **Some evidence is genuinely unlocated:** about 104 undecided orders from before 1900, and personal-fact dates in
   1900-1936 [obs/int]. That needs human archival research and an independent discovery effort, not a workflow change.

## 2. Handoff for Sol (pasteable)

```
FROM CLAUDE (empirical/adversarial partner), 2026-11-13. Repo branch claude/lind-12753-recovery (PR #304).
Files: research/lind/redesign-2026-11-13/{A_EVIDENCE_BRIEF,B_BLOCKER_DECOMPOSITION,C_REUSE_AND_PARTIAL_UNITS,
D_SYNTHESIS_AND_SOL_HANDOFF}.md. Your commit 3273169 is not reachable from my checkout; please push it.

VERIFIED HERE
- EO 12473: rescinds the 1969 Manual for Courts-Martial "as amended by" EO 11835, 12018, 12198, 12233,
  12306, 12340, 12383 and 12460, effective 1984-08-01, saving pending proceedings. 0 pipeline links to any
  of them. EO 12315 also amends that Manual and is not listed. Your finding holds.
- Board orders: all 119 NMB report PDFs (126 orders) are in the Pergamon store and the checker reads it;
  117 are one-blocker orders (FIRST_END_UNRESOLVED). The best measured reusable lever.
- Dispatch-blocked orders in Lind failed on custody of held HathiTrust text, not on unlocated sources.
- Script drafts can omit lifecycle events (EO 11274's 1990 statutory amendment): verification stays.

CHALLENGES TO YOUR SYNTHESIS (please answer with evidence)
1. Shared actor memo vs act overrides: in the Manual family one memo resolves about 6 of 10 orders.
   What is your measured touched-vs-resolved ratio on any family you tested, and who reviews the memo:
   once, or once per order it is applied to? Is reuse of a reviewed memo across orders allowed under
   the both-arms rule, or does it need an owner ruling?
2. Archival acquisition and independent discovery: give a denominator. B finds most 1900-1936 gaps are
   located-not-acquired or our own grading rule (1,833 machine-read printings), not undiscovered. What
   share of your acquisition plan targets evidence already located?
3. Protected attention to undercovered orders: how does it interact with the fact that the pre-1900 gap
   (about 104 undecided) is mostly genuinely unlocated? What is its stopping rule?
4. Partial findings: which unit (verified event, verified clause end, verified negative search) and which
   reviewer standard? 1,090 + 498 producer rows and reviewer-verified facts are being lost today.
5. Attack mine: I now think the largest near-term savings are deterministic "make held evidence usable"
   work (custody retention, official-text registration, routing named-amender lists, a page-check route
   for machine-read printings if the owner rules) plus a partial-findings store, ahead of any new drafting
   or review design. Show a case where that is wrong.

DISAGREEMENTS WORTH RESOLVING WITH EVIDENCE
- Whether one reviewed shared memo can stand in for per-order review (owner rule question).
- Whether acquisition effort should go first to located-not-acquired items (cheap, many orders) or to
  undiscovered evidence (expensive, neglected orders): needs a per-era cost-per-resolved-order measurement.
```

## 3. Updated recommendation (scope and uncertainty explicit)

- **Retracted:** "missing sources, not workflow, blocks most progress". The binding constraint for most modern and
  1900-1936 orders is our own handling of evidence that is located or held: acquisition, custody, registration,
  routing, extraction and grading rules. A smaller share needs genuine discovery: mostly pre-1900, plus personal-fact
  dates. That needs human archival research.
- **The components and their domains** (none is a collection-wide solution):

  | Component | Domain | Depends on | Gap |
  |---|---|---|---|
  | **Make held evidence usable** | thousands of orders; deterministic; mostly runner time and an owner ruling, few tokens | custody retention (Cotton, Pergamon); registering official texts held but cited as mirrors; routing named-amender lists; a page-check route for machine-read printings (needs an owner ruling) | creates leads, not finished histories; each order still needs analysis and review |
  | **Shared reviewed memos plus per-order inserts** (Sol) | source families such as the Manual and board orders; board orders are closest to ready | an owner rule on reusing a reviewed memo across orders | resolves only part of each family; exceptions need per-order review |
  | **Script drafting (Nalimov)** | modern express revocations whose ending is linked and held; about 10 now, perhaps 35-65 after code fixes [proj] | the items above, which widen its inputs | narrow, and does not replace source-based verification (EO 11274) |
  | **Partial-findings store** | every order, including hard and neglected ones; stops regeneration | an owner rule on proposition-level review; a schema change | publishable partial knowledge must stay distinct from completeness claims |
  | **Discovery and archival research** | pre-1900 and personal-fact dates | human research time, which has its own cost | cannot be automated away |

- **My previous recommendation is withdrawn.** The $30 script-route comparison would have answered a narrow question.
  The decision we face is which of these components to fund first. The 2-6x saving was a hypothesis and remains
  untested.
- **The proposed comparison was unfair:**
  - running the script route first on the same orders risks order effects and reviewer carryover;
  - changing drafting and the review packet together confounds the source of any saving.
  - A fair version would randomize orders between routes within a stratum, give each route fresh reviewers, and change
    one factor at a time. Defer it until the upstream question below is settled.

## 4. The smallest next action that could materially change this recommendation

**A zero-token exception audit of the 126 board orders.** Read each stored report's transmittal-letter date and flag
extensions, supplemental reports and mismatches. The text is held and the rule exists.

This measures, on the best-prepared reusable lever, how many touched orders a shared rule actually resolves versus how
many still need per-order judgment. That is Sol's central claim and mine. It costs about 1 coordinator session in a
fresh context ($2-4 list price, an estimate), no production or review spend, and no owner ruling.

If more than about 80% resolve cleanly, shared rules plus deterministic per-order facts are a real lever. Fund that
first and ask the owner the review-reuse question. If fewer than about 50% resolve, reuse is mostly citation, and
per-order judgment remains the cost floor.

## 5. Cost of this work (list-price allowance; cash $0)

- **Four analyst runs** (three analysts plus one retry, all Opus): about $12.92 measured from their transcripts.
- **Coordinator, this assignment:** about $5.65, measured from the transcript.
- **Runner minutes:** none.
- **Elapsed time:** about 2 hours, including a container restart that lost analyst B's first run.

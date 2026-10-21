# Blackstone: the strike-and-insert question (2026-10-20)

Named after Blackstone, whose *Commentaries* set out the old common-law rule on repeal and re-enactment: a later act that repeals a clause and re-enacts it in the same words does not interrupt it. This folder is an owner question packet. It is not a ruling, writes no claims, and changes no codebook, status or certified count (still 0).

## The question for Danny

A later order **strikes** an item or subsection of an order and **inserts replacement text**, under the same number or a new one. Which of these is right?

- The struck clause **ends** on that date, with the amending order as its `first_end` actor.
- The clause **continues, amended,** until the parent ends, with the amendment recorded as a `later_event`.

## Is there an existing rule? No.

I searched the codebook and claim guides. None of them decides this question.

- `jobs/claim-kit/AGENT_PROTOCOL.md` step 3 only says to "explain why earlier ends, partial amendments and savings do or do not control." It does not say which way to decide.
- `research/stage19/CLAIM_SCHEMA.md`: "Every later event requires an effective date, actor, mechanism and source." It does not say when an amendment counts as an end.
- `research/stage15/LEGAL/OPERATIONAL_STATE_CODEBOOK_DRAFT.json` lists `first_cause_type` values `"later_amendment_imposed_condition"` and `"later_presidential"`, and a required field `"revisions_and_revivals"`. It has no strike-and-insert rule.
- `research/stage12/METHODOLOGY_CODEBOOK_SUPPLEMENT_PROPOSED.md` is proposed and not adopted. It says: "Episodes can repeat after revival."
- The only operative instruction is a workflow rule in `research/production/day-review-2026-10-20/next-lines/NEXT_LINES.md`: "Any strike-and-reinsert falls under the EO 14052 ruling; block it, do not decide it."

## 1. Orders blocked on this question

`AFFECTED.jsonl` has one row per order. Each row quotes the striking sentence verbatim from the held FR text (`jobs/fr-originals/output/texts/`), with char offsets, the text sha256 and the downloaded-PDF sha256.

| Order | Struck by (date) | Pattern | Other block |
|---|---|---|---|
| EO 14052 sec. 3(d)(xii) | EO 14082 sec. 4(c) (2022-09-12) | Strikes (xii) and re-adds **the same words** as (xiii) | none |
| EO 11898 (sole clause, item (15)) | EO 11983 sec. 1(c) (1977-05-04) | "revising subsection (15) to read" a new title | none |
| EO 11877 sec. 1(b), 1(c) | EO 12035 (1978-01-20); EO 11908 (1976-03-18) | Inserted item text replaced "in lieu"; deleted item later re-added | sec. 2 supersedes EO 11864 (not reached by EO 12076) |
| EO 11908 | (EO 11877 had struck item 2(7) earlier) | Re-adds the struck item; nothing later strikes this order's text | none (the block looks over-broad; a reviewer should confirm) |
| EO 11983 | (is the striking actor) | Its own inserted text is never struck | sec. 2 revokes EO 11872 (primary block) |
| EO 12581 (new, from the VIAPAR screen) | EO 12584 (1987-02-19) | Its inserted deadline "February 19, 1987" is replaced by "February 26, 1987" | report-deadline ruling (under B only) |
| EO 11927 (probe, rejected) | EO 12060 (1978-05-15) | Its inserted word "Counselor" is replaced "in lieu" | needs re-production for other defects |

**How the remaining VIAPAR ids were screened.** I checked the 14 unattempted ids against their dossier chains and held texts. Only EO 12581 has its own inserted text struck and replaced later.

- EO 11999, 12025, 12035 and 12069: nothing later strikes their text before EO 12076.
- EO 12121: EO 12156 only adds members.
- EO 12921: EO 12970 amends sec. 4(b), not 1(a).
- EO 11036, 11963, 11547, 11853, 12100, 12317 and 12584: no later strike of their text.

Several of these orders are themselves the striking actor (12025, 12035, 12069, 11853, 12100). The ruling therefore affects their **parents' claims**, not their own.

**Adjacent orders, not counted.** Y2LEAD blocked EO 8809, 11830, 12163, 12293 and 12898 on a related question: whether a YES claim can rest on text that replaced the original in full. Any option chosen here still leaves that model question open.

## 2. Current practice in committed claims (it is split)

**Precedent i08** (`research/readiness/claims/claude-lambertini-i08-2026-10-20.jsonl`, EO 11861 and EO 12076) treats delete-and-insert-in-lieu of a list item as the **end** of the struck item, with the amender as actor. Three examples:

- `EO:11861#sec1-12` ends 1977-12-01 by EO 12025 ("deletes 'Associate Attorney General ...' in subsection (12) and inserts ...").
- `EO:12076#1-101f` ends 1979-02-14 by EO 12119.
- `EO:12076#1-102e` ends 1978-11-17 by EO 12099. EO 12099 deletes 'Director of Policy Review' from 1-102(e) and inserts **the same title** as 1-101(r). This is the closest analogue to EO 14052. Note that the position also moved from level V to level IV.

The same claim file keeps word swaps as continuing. For example, `EO:12977#sec1` treats EO 13286's "striking 'the Administrator of General Services' ... and inserting 'the Secretary of Homeland Security'" as a `later_event` ("amendment of the order's text, not an end of the order").

I ran a mechanical scan of every git-tracked file in `research/readiness/claims/` (scratch output, not committed):

- **The struck text ENDS (amender is `first_end`): 43 clauses in 26 orders.**
  - codif-b0: 9 orders (Executive Schedule item replacements).
  - codif-b4: 3 orders.
  - codif-b7: 9 orders ("amended to read" restatements, including the report-deadline restatements EO 11832 sec. 2(h) and EO 11971 sec. 3(a)).
  - i06: EO 11868.
  - i08: EO 11861 and EO 12076.
  - rastell-c01: EO 10587 secs. 2 and 3.
  - bowditch-y2-02: EO 12150.
- **The struck text CONTINUES (amendment is a `later_event`): 28 clauses in 11 orders.**
  - codif-b4: EO 8546.
  - codif-b5: EO 10529.
  - i05: EO 10204 paras. 3-5 "amended to read", EO 10618 item 2(e), EO 10821 secs. 2(a)(2) and 7.
  - i08: EO 11958 and EO 12977.
  - iv01: EO 12743.
  - p1: EO 12089.
  - rastell-c01: EO 10587 sec. 1 (restated in the same words) and EO 10906.

The most common deciding factor in practice is whether the replacement changes substance. Renamings and verbatim restatements tend to continue, and new offices and new rules tend to end. The split is not consistent, though. "Amended to read" rewrites of substance continue in i05 (EO 10204, EO 10821) but end in codif-b7 and i06.

## 3. Options

| Option | Rule | Blocked orders claimable now | Committed clauses to re-check |
|---|---|---|---|
| **A** | The struck item ends on the amendment's effective date, and the replacement is a new clause of the amending order. Item level only: striking a bare "and" (EO 14052 (xi)) does not end the item. | **4**: EO 14052, 11898, 11908, 12581 | 28 "continues" clauses in 11 orders |
| **B** | The item continues as amended until the parent ends, and the amendment is a `later_event`. | **3**: EO 14052, 11898, 11908. EO 12581 would be a 4th only if AGENT_PROTOCOL's "A report deadline is never an end" settles the pending report-deadline ruling; its end would then be EO 12610, 1987-09-30 | 43 "ends" clauses in 26 orders |
| **C** | Continues only if the replacement is verbatim, or differs only in numbering, punctuation or a renaming of the same office or function. Otherwise it ends as in A. | **3**: EO 14052 (verbatim re-add), 11908, 12581 (a date change is substantive). EO 11898 needs a same-office finding first | Both lists, clause by clause (about 71 clauses); most already fit C, and the clear exceptions are i05's EO 10204 and 10821 |

Under every option, EO 11877 and EO 11983 stay blocked by their independent sec. 2 commands, and EO 11927 needs re-production.

Under every option there is also a sub-question: does re-adding a deleted item end the earlier deletion clause? This affects EO 11877 sec. 1(c) and EO 11908.

These are AI hypotheses only. Not decided. Certified whole-lifecycle count: 0.

# Prompt for the different-family status review (Sol, OpenAI GPT family)

You are Sol, an independent reviewer from the OpenAI GPT model family, working on the GitHub repository D3m0sthene5/Executive-Orders (branch main). The project records the full lifecycle of every U.S. executive order. Your job is the different-family review that the owner's ruling requires before AI-proposed provisional statuses can be adopted: research/readiness/owner_rulings/2026-10-21-status-proposal-adoption.md. Read that ruling and research/readiness/owner_rulings/2026-10-28-evidence-not-convenience.md first.

WHAT TO REVIEW
research/excavator/claude-status-proposals-2026-10-28/batch-1/PROPOSALS.jsonl: 143 status proposals, one per line, written by a Claude (Anthropic) producer. The orders are pre-1937 retirement exemptions, office-closing or mourning orders, and orders extending a time limit to a stated date. Each proposes "no" (no operative part in force at the 2026-10-14 cutoff), "yes", or "needs_research", and quotes its basis from a held text by path and character offsets. Some proposals contain deliberately planted errors; you are not told which or how many. Review every one on its merits.

METHOD (the same lean method as the earlier Sinclair cross-family review)
Use the fixed checklist Q1–Q7 in research/excavator/sinclair-2026-10-20/lean-review-2026-10-22/CROSS_FAMILY_REVIEW.json ("fixed_checklist"); that file also shows the expected verdict format. For each proposal:
- Q1: the identity is right and the proposal is internally consistent.
- Q2: open text_path and confirm that the quote is exactly the text at char_start–char_end, that the file's SHA-256 equals text_sha256, and that the held text is this order (number, date, subject). For American Presidency Project texts, the page record with the same sha256 is in jobs/app-executive-orders/output/MIRROR_DOCUMENTS.jsonl or DOCUMENTS.jsonl.
- Q3: the basis covers the whole order, not one clause.
- Q4: exceptions, savings and accrued effects are distinguished from operative commands.
- Q5 (D6): check later events in jobs/later-events/output/EDGES.csv (both target_id and acting_id) and jobs/claim-kit/output/CHAINS.jsonl. For retirement exemptions, check whether later orders of the same type name the same person; an extension is a later event, not this order's end, and it does not keep this order in force past its own stated period.
- Q6: signing, stated effect and end dates are distinguished. Every stated date must match the quoted held text. A stated "until" date is recorded inclusive, with the exclusive reading noted (ruling 2026-10-21-until-and-further-exempt.md).
- Q7: errors, assumptions and gaps are disclosed. "no" needs the order's own held text stating a period that ended before the cutoff, or a held later instrument ending it. An open-ended exemption with no stated period, or a standing or recurring closing rule, cannot be "no" without held evidence.
Use only sources held in the repository; do no new research or acquisition.

VERDICTS
For each proposal, give exactly one verdict:
- "uphold": every question passes, possibly with disclosures;
- "needs_research": the held evidence does not settle the status;
- "reject": the proposal misstates its source, date, identity or status. Name the field, what the proposal says and what the source says.
A proposal that itself says "needs_research" is upheld only if that is the correct reading.

OUTPUT
Write two files in research/excavator/claude-status-proposals-2026-10-28/batch-1/:
- CROSS_FAMILY_REVIEW.json, shaped like the Sinclair file. Include:
  - schema "eo-cross-family-status-review/v1", recorded_date, base_commit;
  - reviewer "Sol / OpenAI GPT family", review_kind "independent_cross_family_lean_AI_status_review";
  - the fixed_checklist;
  - a summary with counts;
  - verdicts: one entry per proposal, with instrument_id, verdict, proposal_line, proposal_record_sha256 (SHA-256 of the exact line bytes without the newline), and answers to q1–q7, each with a short reason and the held source path you relied on;
  - start_utc and end_utc.
- CROSS_FAMILY_REPORT.md: the counts, every reject and needs_research with its reason, material corrections, and what you could not check.

Do not edit any other file. Do not edit PROPOSALS.jsonl, the status ledger research/progress/DECIDED_CASE_COMPLETENESS_RECONCILED.csv, or anyone's handoff notes. The coordinator scores the planted controls and prepares the adoption pull request; adoption takes effect only when the owner merges it. Commit your two files on a new branch named sol/status-review-batch-1 and open a pull request titled "Sol cross-family status review, batch 1". Your verdicts are provisional AI review, not human certification. The certified count stays 0.

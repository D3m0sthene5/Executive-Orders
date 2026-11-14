# Corrected metadata for PR D3m0sthene5/Executive-Orders#304

**Title:** Lind stage 0: failure table, conveyor fix and audit; EO 12753 stopped at producer reconfirmation (stacked on #303)

**Body:**

**Stacked on #303** (the stage-0 results). The stage-0 result stays **0 ready of 30**. No new production or review was
run for this PR.

- **The eligibility and adoption claim is withdrawn.**
  - EO 12753's `completion/complete-v2` reports eligible. But its claim was assembled after my coordination
    reconfirmed the model producer's lifecycle approval by script. D-20261110-no-mechanical-reconfirmation-for-models
    declines that (Kean F-20261113-lind-mechanical-reconfirmation).
  - The adoption ask A-20261112-lind-adopt-12753 is withdrawn.
  - EO 12753 is **stopped at producer reconfirmation.** The open ask is A-20261113-lind-12753-reconfirm. Its paid
    reconfirmation is **not approved**. No adoption, no owner exception.
- **Failure table:** `research/excavator/claude-lind-2026-11-12/FAILURES.md`. All 30 orders, built from existing
  artifacts.
- **Earlier recovery work:** `RECOVERY.md`. The Cotton custody result and the offline-check analysis stand. The
  optional $8 repair ask A-20261112-lind-repair-12437-11943 is not approved.
- **Conveyor fix:** `jobs/maudslay-conveyor/conveyor.py` keeps the blank STATUS_DECISION copy under the scratch root.
  The kit's prior-research scan reads `research/`, so `kit apply` refused on the undecided route.
- **Audit:** `research/lind/conveyor-audit/AUDIT.md` (Kean F-20261113-conveyor-audit), recomputable with
  `usage_audit.py`.
  - **Aligned boundary** (Augur → overlay proposals, 30 orders): the manual coordinator used 48 requests, $5.78 list,
    with a mean prompt of about 490k tokens. At most 33 requests ($4.03) are conveyor-removable.
  - **The conveyor replay of the same 30 orders and saved outputs:** 70–192 s, 0 coordinator calls, 7 proposals. These
    are the same 7 orders the pilot took to blind review. The evidence and status decisions are identical, and it stops
    at producer reconfirmation.
  - **Corrections:** the earlier $6.59 / 51-call comparison spanned the whole batch. Break-even is about 2–3 Lind-like
    batches, not 1–2.
  - **Untested:** the later stages, worker cost under per-order producers, research quality.
- **Costs** (list price; cash $0 under the subscription):
  - pilot: $23.07;
  - post-pilot coordination: $13.86;
  - efficiency work and replay: about $7.5;
  - this audit: AUDIT.md section 6. Runner minutes are unpriced.

Human-certified count: 0.

---
🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_014fYW9sr2dy6LgPUuFSYP58

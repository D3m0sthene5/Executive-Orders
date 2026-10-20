# VIAPAR outcome (Lambertini per instrument), 2026-10-20

Pool VIAPAR has 22 amending orders. Each one ends when its parent order is revoked "as amended" (mostly EO 12076 revoking EO 11861).

- **Probe `p` (first 8):** 4 orders were BLOCKED on the pending EO 14052 strike-and-reinsert ruling (EO 11877, 11898, 11908, 11983). 4 were produced and reviewed by an independent Opus reviewer that ran a D6 step.
- **Upheld 2:** EO 11976 and EO 11986.
- **Rejected 2:**
  - EO 11885 carried the planted first-end date, which was caught. The reviewer also found a whole-file quote.
  - EO 11927 did not give per-item first ends (D6).
- **Savings overturned:** 0.
- **Gate:** at least 5 of 8 effective upheld was required. The probe reached **2/8, so the gate FAILED**. Scale batches s1 and s2 were not run.
- **Claims:** 2 lines in `research/readiness/claims/claude-viapar-p-2026-10-20.jsonl`. They passed kit check and the claim-checker. That file is not committed by this outcome commit.
- **Plants:** 1 of 1 caught.

Lesson: the EO 11861 schedule was struck and reinserted many times, so the EO 14052 ruling blocks half the pool. Per-item first ends must be separate clauses.

All results are AI hypotheses. Certified count stays 0. No codebook or status changes.

## Mend (2026-10-20)

- **EO 11908 was re-examined.** The probe had blocked it on the strike-and-reinsert ruling. Blackstone noted that this block looked over-broad, because no later order strikes EO 11908's own text.
  - The new claim does not decide the pending ruling. It names the EO 11877 sec. 1(c) re-addition sub-question as pending and outside the claim.
  - The independent Opus reviewer ran a D6 step. It read EO 11927, 11976, 11983, 11986, 11995, 11999, 12025, 12035, 12060 and 12069 in full. None of them ends level IV item (16) or level V item (7) earlier.
  - Both items therefore first end at EO 12076 sec. 1-202, dated 1978-08-18. Savings were upheld under sec. 1-201.
- **Upheld 1:** EO 11908. The reviewer's only defect was the planted override span (char_end 1063 changed to 1067), and the reviewer caught it. The genuine line, with char_end 1063, is in `research/readiness/claims/claude-viapar-m-2026-10-20.jsonl`. It passes `kit.py check` (0 errors) and the claim-checker (1/1 passed, 9 exact quotes, 7 GPO hash matches). That file is not committed.
- **Still blocked:** EO 11927. It was rejected because it gives no separate first end per item, and it was not re-produced in this mend.
- **Plants:** 1 of 1 caught.
- **Open item:** a page check of the EO 11986 sec. 2 OCR "( J)" would remove a small residual doubt.

All results are AI hypotheses. Certified count stays 0. No codebook or status changes.

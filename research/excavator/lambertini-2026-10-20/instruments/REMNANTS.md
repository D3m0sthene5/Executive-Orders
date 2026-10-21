# Lambertini III remnants: EO 10169 and EO 10390 (blocked)

Date: 2026-10-20. These are AI review hypotheses, not certifications. The certified count stays 0. This file changes no status, no codebook entry and no claim file.

In batch 04 the independent reviewer (`claude-lambertini-i04-reviewer`, Opus, Mountweazel configuration with held sources and a D6 step) rejected two claims that were not plants. For both, the reviewer wrote `should_be: "blocked"`. They are recorded here as **blocked**, not rejected: neither claim misreads its source. Each states an end date while an earlier end, resting on a text we do not hold, is still open. Neither claim was copied to `research/readiness/claims/`. Source: `04/reviews/VERDICTS.json`.

## EO 10169: National Advisory Committee on Mobilization Policy

- **Recorded end:** superseded by EO 10480 sec. 607(2), 1953-08-14, on signing. The claim calls this an upper bound.
- **Reviewer's reason (D6 failure):** all four clauses run through the National Security Resources Board (NSRB):
  - the Committee advises the NSRB;
  - the NSRB Chairman appoints its members;
  - the NSRB pays its expenses.

  Reorganization Plan No. 3 of 1953 reorganized mobilization under the Office of Defense Mobilization (ODM). It took effect 1953-06-12, according to Defense Mobilization Order VII-9 as printed in the held FR text of EO 10610. The claim itself says it is unknown whether the plan displaced the NSRB, and the Committee with it. That is a material later event, and possibly an earlier end, before 1953-08-14. Even so, `unresolved_material_gaps` is empty. Under the brief, a first end that depends on an external instrument we do not hold means the claim is blocked. The producer applied the same standard to EO 10359.
- **Now waits on:**
  1. The official text of Reorganization Plan No. 3 of 1953, at least the parts on the NSRB and on references to it, with a retained copy and sha256. This is `FETCH_QUEUE.jsonl` line 315 (`claude-lambertini-i04-producer`). That line is worded "Lead, not a block"; per this review it now gates the claim.
  2. An official-text ACT record for the pair EO 10169 > EO 10480. The current record is an APP transcription (`custody_record_only`). The held official FR text of EO 10480 fails `order_exists` because the OCR contents column reads "E. O. 1C480". This is the same gap as EO 10324 and EO 10467; see the `claude-lambertini-remnants` lines in `FETCH_QUEUE.jsonl`.
  3. A refiled claim with the plan's effect stated, or entered in `unresolved_material_gaps`, followed by a new independent review.

## EO 10390: alternate members of the Wage Stabilization Board (sec. 403 of EO 10161)

- **Recorded end:** superseded by EO 10480 sec. 607(11), 1953-08-14. The reviewer accepted this reading. The reviewer also accepted that EO 10434 (held) is ruled out: it suspends wage-stabilizing orders but does not touch the alternate-member paragraph.
- **Reviewer's reason:** the claim itself says the Wage Stabilization Board's Title IV wage-stabilization functions may not have been continued by the Defense Production Act Amendments of 1953, whose text we do not hold. EO 10467 sec. 1 (held) continues delegation orders only for functions that were continued, from 1953-07-01. So the claim calls its 1953-08-14 end an "upper bound, not a certified end", yet `unresolved_material_gaps` is empty. Under the brief, an earlier end that rests on statute text we do not hold means the claim is blocked. Refile once the Amendments are held.
- **Now waits on:**
  1. The enacted text of the Defense Production Act Amendments of 1953, with its approval date and the titles it continued (Title IV in particular), with a retained copy and sha256. This is `FETCH_QUEUE.jsonl` line 317, which points to line 316 (EO 10373). Line 317 is worded "Lead, not a block"; per this review it now gates the claim.
  2. An official-text ACT record for the pair EO 10390 > EO 10480. This is the same APP `custody_record_only` gap as items 2 above.
  3. A refiled claim with any earlier statutory end stated, or entered in `unresolved_material_gaps`, followed by a new independent review.

## Related

- **EO 10373 (batch 04).** Rejected for the planted date. With the plant removed, the reviewer says it should also be blocked, for the same reason as EO 10390: whether DPA Title VI was continued is open (`FETCH_QUEUE.jsonl` line 316).
- **EO 10324 and EO 10467 (upheld; checker unverified).** The ending source is the same EO 10480 text. The official text is held and GPO-hash-matched, but the ACT record is APP-sourced.
- **EO 12977 (upheld; checker unverified).** EO 13286 sec. 23 is held in official text, but the later events cite the APP ACT record.
- **Why no act_overrides records for these three.** `jobs/claim-kit/act_overrides.py` accepts only pairs the scanner reports as "target provision not located", and it requires a committed independent `REVIEW.jsonl`. These pairs are already located from APP text, so a record would be refused with `pair_not_unlocated`. Three precise `FETCH_QUEUE.jsonl` lines were appended instead, marked "Dossier gap, not a missing source".

## Re-sourced (2026-10-20)

EO 10324, EO 10467 and EO 12977 were refiled against official held texts: `EO_10480.txt` (GPO hash match; sec. 607 items (7) and (13)) and `EO_13286.txt` (sec. 23). An independent reviewer then checked them, including the D6 step.

- **Plant score: 1 of 1 caught.** The plant changed "February 6, 1952" to "February 8, 1952" in the EO 10324 sec1 first_end quote. The reviewer rejected EO 10324 for that defect alone and raised nothing else.
- **EO 10324:** rejected because of the plant only. Every other check held, including the end at EO 10480 sec. 607(7) on 1953-08-14, savings under sec. 606, and the D6 by-number scan. The genuine line is now filed in `claims/claude-lambertini-i04-2026-10-20.jsonl`, line 1.
- **EO 10467:** upheld. Item (13), sec. 606 savings, and D6 are clean. Filed in i04, line 2.
- **EO 12977:** upheld. Seven clauses carry the EO 13286 sec. 23 event dated 2003-03-01 (sec. 92). The order was revoked by EO 14111 on 2023-11-27, and D6 is clean. Filed in i08, line 11. The later events still cite the APP ACT record (custody only), as the claim discloses.
- **Claim checker** on i04 and i08 (21 claims): 21 mechanical pass, 0 unverified, 0 fail, 21 gate passed. This replaces the "checker unverified" note under Related.
- AI status hypotheses only. Nothing is adopted. The certified whole-lifecycle count stays 0.

# Producer report (u302, undecided route)

Start 2026-11-06T10:17:12Z; end 2026-11-06T10:23:11Z. Final applied dir: applied-v1.

## Outcomes
- EO:13348: submit; status "no". Revoked, with the emergency terminated, by EO 13710 (effective 2:00 p.m. EST Nov 12, 2015). Basis ACT:EO:13348>EO:13710 and ACTOR_TEXT:EO:13710 (official FR text). Inventory corrected: the mechanical split broke section 1(a) mid-sentence and omitted the preamble declaration. 14 replacement scopes, all ended 2015-11-12.
  Caveat: sec. 10 (effective time) and sec. 11 (transmit/publish) are ended at the revocation, with reasons given. Publication on 2004-07-27 is shown; the date of transmittal to Congress is not held. A reviewer may prefer an earlier performance end for sec. 11. The whole-order end date is unaffected.
- EO:13362: submit; status "no". Revoked by name in EO 13442 sec. 2, Aug 13, 2007 (on signing). Confirmed by the 6 U.S.C. 111 note. The 5-clause inventory was kept as is.
- EO:13489, 13534, 13600, 13737: dispatch-blocked, not researched. The rows are left as prepared (unresolved), and the assessment rows are from the views only. Each lacks a held original (custody_record_only) and none carries a STATUS_DECISION.

## Time
- 13348: reading the 13710 text, correcting the inventory and checking the continuation notices.
- 13362: short; one revocation, one search.

## Checks
- apply: 2 awaiting_status_review (expected), 4 unresolved.
- batch-check: 0 claims checked, 0 actionable failures.
- _decision_errors returned [] for both STATUS_DECISION files.
- Geddes: 0 flags, so no GEDDES_RESOLUTIONS.json.
- Undecided members are never assembled by apply, so the clause sheet was not checked by the assembler or the actual checker.

## Other
- Opened beyond the views: nothing from READ.md, PACKET.json or LOOKUPS.details.json. Read EVIDENCE.json records and held texts directly, plus cruden.py scratch output in /tmp/claude-0/dorotheus-wave/work/u302/.
- pages_confirmed is false for all confirmations: no page images were inspected.
- Tool defects: none.

## Reconfirmation
- EO:13348: assembled and overlay-check passed (0 failures). Fix: the 14 clauses' end_id changed from ACT:EO:13348>EO:13710 (APP mirror) to ACTOR_TEXT:EO:13710 (the held official FR text), and the working_text disclosure emptied. The reason wording was left as written; the quoted words are the same in the FR text.
- EO:13362: assembled and overlay-check passed (0 failures), no change besides approved=true.
- Both: LIFECYCLE_DECISION.reconfirmed.json and CLAIMS.working.jsonl written under overlay/EO_N/proposal-v1/.

## Correction (EO:13362)
The heading "Sec. 2. Exceptions." (19 characters) was not an operative command. The v2 sheet LIFECYCLE_DECISION.reconfirmed-v2.json uses inventory_overrides to fold it into the span of paragraph (a) and drops the separate sec2 scope. It leaves 4 disjoint clauses: lead, sec1, sec2-a (from the heading) and sec2-b (trimmed to end at "acting Secretary."). The other fields are unchanged. overlay-assemble wrote CLAIMS.working-v2.jsonl and overlay-check reported 0 failures. Canonical sha256 of the claim: 242bebb5f55439b357b373bd978c36222e5957471709356ad741a384df1daecc. CLAIMS.working.jsonl was not touched.

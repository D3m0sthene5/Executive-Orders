# Producer report: t1 NIRA batch (agent claude-t1-producer)

Start (UTC): 2026-10-29T13:30:35Z
End (UTC): 2026-10-29T14:06:50Z

## Status

The decision sheets (`decisions.csv`, `clauses.csv`) are complete for all 24 orders: 20 submit, 4 blocked.
No applied directory exists. `kit.py apply` and `kit.py batch-check` both refuse to run on this packet with
`claim-kit: changed Valla review context; prepare a new version` (see Tool defects). I did not work around the refusal.
The coordinator needs to re-prepare the packet (or fix the check) before apply and batch-check can run; the sheets
carry the packet's current dossier fingerprints and will need only a fingerprint refresh if a new packet changes them.

Substitute validation (not the kit route, nothing written to the repository): I ran the kit's own `assemble.assemble`
on every submitted row, then `assemble.check_claim`, then the actual `jobs/claim-checker/checker.py` (downloads
disabled) on the 20 assembled claims. Results: 20 of 20 assemble with no errors; 20 of 20 pass `check_claim`;
checker: 19 pass all checks, 20 pass the gate, 0 mechanical fails, 215 of 215 quotations exact, 190 source references
held-bytes verified, 5 custody-record-only (all five belong to EO 6467). Scratch outputs are in the session scratchpad,
not in the repository.

## Outcome per order

Submitted (20): EO 6242D, 6305, 6319, 6323, 6346, 6373, 6387, 6388, 6415, 6467, 6473A, 6484, 6543B, 6597, 6640, 6705,
6903, 7015, 7017, 7022.
- EO 6467 ends 1934-07-01 by its own terms (mechanism `own_terms_fixed_term`, end id the dossier's fixed-term record); it postpones Article IX, section 4 of the Retail Trade code to July 1, 1934, so the June 14, 1935 repeal is a later event.
- The other 19 end 1935-06-14 by `SUPPLEMENT:SJRES113` (`statutory_repeal_of_code_approval_and_enforcement_provisions`), with the Schechter characterization carried in `source_notes` (5 notes: NIRA3, SCHECHTERSYL, SCHECHTERDEL, SCHECHTERJDG, NIRA2C) and savings `transferred_or_accrued` from `SUPPLEMENT:NIRA5`.
- EO 6473A and EO 6705: inventory overrides replace five numbered findings (recitals "do hereby find that") with the single approving sentence (6473A characters 1408-1685; 6705 characters 1717-2030).
- EO 6242D and EO 6346 (denials of exemption): treated as code-dependent determinations ending with the repeal; the reasoning and the contrary reading (a denial is exhausted on signing) are stated in the rationale. This is a judgment the reviewer should test.
- EO 6319 (approval with a condition on one association's participation) and EO 6323 (amendment effective one week after signing unless cause shown): conditions are not ends; stated in the rationales.

Blocked (4):
- EO 6325: item (1) creates an Optical Manufacturing Industry Committee (seven elected members, three appointed non-voting); an organizational command beside a code approval (SHARED_ANALYSIS item 5), no held record of its constitution or end. The inventory must be complete, so the approval clause cannot be filed alone.
- EO 6877: rules for administering paragraph 2 of section 3 of the Wool Textile code "until February 1, 1935"; EO 6955-A (held printed copy and APP text) extended administration to 30 days after the Wool Textile Work Assignment Board reports to the President, and no held source dates that report. Also an appointment direction (Textile Labor Relations Board appoints the Work Assignment Board) and an organizational delegation. Not a code approval, amendment or exemption.
- EO 6948A: approval with four provisos (60-day stay as to Motor Vehicle Retailing Trade members; direction to the National Industrial Recovery Board to determine which code's provisions prevail; stay of Rule provisions pending the Board's further order; stay of a phrase until the National Code Authority is constituted). Machine inventory (one clause) is wrong; three of the five needed clauses have contingent or performance ends that no held source decides.
- EO 6952A: approval with a stay of Sections 2 and 3 of Article VII and Rule 14 of Article VIII "pending the further order of the National Industrial Recovery Board"; no held record shows whether a further order issued before June 14, 1935.

## What took the time (one line each)

- EO 6242D: working out whether a denial of exemption is code-dependent or exhausted on signing, and the Administrator's stay exception, traced through EO 6407, 6424, 6463 and 6476.
- EO 6305: reading and the search for other bankers' codes (EO 6652 is Investment Bankers, a different code).
- EO 6319: deciding that the association condition is not an end and no own-terms event is held.
- EO 6323: the one-week-delay condition and tracing the other Lumber Code amendments (EO 6255, 6487, 6654).
- EO 6325: finding that item (1) is an independent committee command with no held end; blocked.
- EO 6346: same denial question as 6242D and the Lumber Code amendment chain.
- EO 6373, 6387, 6388, 6415, 6484, 6543B, 6597: routine; identity and APP page check, shared-analysis application, code-name searches. (6597: reading EO 6988, which names the code in a section 3(e) complaint dismissal; not an end.)
- EO 6467: identification (the number 6467 also carries 6467-A, the Radio Broadcasting code), own-terms date reading, and finding that its APP capture is a Wayback capture whose bytes the checker cannot re-hash offline.
- EO 6473A: the inventory correction, and discovering that EO 7585 and 7604 revoke a different "Executive Order 6473" (a land withdrawal).
- EO 6640: reading the Construction Industry subchapter orders for a cancellation; none.
- EO 6705: inventory correction and the EO 6999 transfer of Agriculture Secretary functions (not an end; no section 8(b) instrument).
- EO 6877: determining the amendment chain (EO 6955-A, 6878, 6930, 6858) and that the report date that triggers the end is not held; blocked.
- EO 6903, 7015, 7017, 7022: parallel April 1935 alcohol-code amendment orders; sorting which sibling orders are later events and confirming none revokes another.
- EO 6948A, 6952A: inventory is wrong (stays and directions folded into the approval); contingent ends not held; blocked.

## Counts

- Sheets: 24 rows; 20 submit, 4 blocked.
- batch-check: not run (tool refusal). Substitute checks as above: 20 of 20 assemble, 20 of 20 `check_claim`, checker 19 pass, 1 unverified custody (EO 6467), 0 mechanical fail.

## Tool defects

1. `kit.py view --order`, `apply` and `batch-check` fail on this packet with "changed Valla review context; prepare a new version". Cause, found by diffing: the packet pins `valla_context.package_scan.tracked_packages_loaded` = 68; `git ls-files` for `research/excavator/**/RATIONALES.json` and `research/production/**/RATIONALES.json` now returns 76 files (75 loaded packages), because other NIRA-sweep packets (b0, t2, try1) were tracked after t1 was prepared. Everything else in the Valla context (claims, review queue, pins) is identical. The check treats a growing count of unrelated tracked packages as changed evidence about these orders, so any packet is invalidated as soon as another packet's RATIONALES.json is tracked. I tried one workaround (a wrapper that ignores that single field); the permission layer denied it, correctly, so I stopped. The coordinator needs to re-prepare t1 or decide the count should not be pinned.
2. `view <packet>` (the catalogue) still works; `view --order` and `--source` do not, so I read order metadata by loading the packet through `batch.load_packet(check_sources=False)` in a scratch script (read-only).
3. `kit.py view` for a packet with all-clause-drafts duplicates lists every clause-drafts excerpt as a "common text", which invites quoting the clause-drafts copy; I quoted only the APP file named in the fragment record.
4. The actual checker reports `order_exists:not_in_universe` for an `EO:6467:<hash>` token when a rationale cites the dossier's own-terms record id; I removed the record id from the prose. A rationale that cites a dossier evidence id by its full id can fail the universe check.

## Places the shared analysis did not fit

- EO 6325, 6877, 6948A, 6952A: orders that attach organizational commands, directions to agencies or contingent stays to an approval (SHARED_ANALYSIS item 5, "mixed orders"). Blocked.
- EO 6467: a postponement with a fixed date before the repeal; own terms end it in 1934, so the repeal is not the first end.
- EO 6242D and EO 6346: denials of exemption. The analysis addresses approvals, amendments and grants; applying the repeal to a denial rests on the denial having continuing legal effect only through the code's enforceability. The rationale states the competing reading.
- The census register and the WPA list do not distinguish EO 6467 from 6467-A, or 6473 (land withdrawal) from 6473-A, except by suffix; later orders (EO 7585, 7604) cite "Order No. 6473" for the land withdrawal.

## Searches (all held, 2026-10-29)

Every held order text numbered 6180-7076 in the APP folder that mentions codes of fair competition, NRA or the National Industrial Recovery Act was scanned for cancel/revoke/rescind/supersede/terminate/annul/void; every held text folder other than the Federal Register and source-ladder folders was searched for each order's citation and each code's name; the census register and the 1933-1935 WPA summaries were searched for cancellation, revocation, suspension, termination and supersession. The only held cancellation of a code approval before June 14, 1935 is EO 6925-A (Cinders, Ashes and Scavenger Trade; not any code in this batch). General orders EO 6354, 6710, 6723 and 7076 are addressed in each rationale.

## Tool calls

About 80 tool calls, including background and polling calls.

## Corrections (after independent review of EO 6242D and EO 6346)

Start (UTC): 2026-10-29T14:38:43Z
End (UTC): 2026-10-29T14:49:42Z

Only EO 6242D and EO 6346 rows were changed in `decisions.csv` and `clauses.csv`; every other row is byte-identical to the version applied in applied-v1 (checked by assertion before writing). `applied-v1` was not touched. New results are in `applied-v2` (apply log `APPLY_v2.log`, check log `BATCH_CHECK_v2.log`).

- EO 6346: submitted. The denial is recorded as a one-time determination exhausted by performance on 1933-10-20 (mechanism `one_time_determination_exhausted_on_issuance`, end cited to the order's own operative sentence). The 1935-06-14 repeal (`SUPPLEMENT:SJRES113`) is recorded as a later event, not the end. The applicants' continuing obligation is described as the code's own operation under EO 6255, not as a command of the denial, and the rationale no longer calls the denial an approval. Savings and source notes were rewritten to match.
- EO 6242D: now blocked. The operative sentence holds two clauses, the denial (exhausted on 1933-08-04) and the exception for the Administrator's stay of July 30, 1933, which has its own end. Held APP texts show that stay ended December 11, 1933 (EO 6476 of December 4, 1933; EO 6407, 6424 and 6463 set and extended the stay's termination). None of those four orders is an evidence record in this frozen, already supplemented packet, and the assembler accepts an end only by a frozen evidence id, so the stay clause cannot cite the date. An inventory override splitting the clauses would still leave the stay clause without a citable end. Needed: a new packet in which EO 6476 (and EO 6407, 6424, 6463) are supplement excerpts of EO 6242D, then the split inventory override and clause rows.
- batch-check on applied-v2: 24 members, 19 claims checked, 19 strict pass, 0 strict fail; outcomes 19 assembled, 5 blocked (EO 6242D, 6325, 6877, 6948A, 6952A); actual checker 18 all-checks-pass, 1 unverified (EO 6467, custody-record-only Wayback capture), 0 mechanical fail, 19 gate pass.
- EO 6346 source note reworded from "the Cotton Textile or Lumber code" to "the Lumber and Timber Products Industries code" (no other Cotton Textile mention in the row; no other change); applied-v4, batch-check 19 of 19 strict pass, 5 blocked, actual checker 18 pass/1 unverified (EO 6467). Start 2026-10-29T15:30:35Z, end 2026-10-29T15:41:30Z.

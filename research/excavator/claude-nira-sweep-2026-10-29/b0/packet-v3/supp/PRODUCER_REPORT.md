# Producer report: claude-b0-producer, NIRA code sweep, batch b0

Start UTC: 2026-10-29T13:27:32Z
End UTC: 2026-10-29T14:08:47Z

Final packet: research/excavator/claude-nira-sweep-2026-10-29/b0/packet-v3/supp (parent: packet-v3, with SUPPLEMENT_DECLARATIONS.json beside it).
Final applied directory: research/excavator/claude-nira-sweep-2026-10-29/b0/packet-v3/supp/applied-v2 (applied-v1 kept; see below).
The original packet (b0/packet) and packet-v2 were not used for submission: their Valla review context went stale (see tool defects). Their dossiers are byte-identical to packet-v3's inherited dossiers.

## Outcomes

| Order | Outcome | Claim |
|---|---|---|
| EO:6331B | submitted | Approval of the Compressed Air code. First end 1935-06-14, S.J. Res. 113 section 2 (49 Stat. 375). |
| EO:6370 | submitted | Approval of the Fertilizer code. Same end and reasoning. |
| EO:6530 | submitted | Two scopes (inventory corrected): approval, ends 1935-06-14; overtime stay condition, ends by own terms 1934-03-01 (inclusive, exclusive reading stated). |
| EO:6242E | submitted | Two scopes (inventory corrected): denial of exemption, exhausted by performance 1933-08-04; exception for the Administrator's stay, ends 1933-12-11 (EO 6476). EO 6407 recorded as later event. |
| EO:6320 | blocked | Effective date of the new section 12 is not shown by held evidence: whether just cause was shown before noon Oct 13, 1933. Both components (amendment, 30-day sale proviso) depend on it. Needed: the NRA code compilation, vol. I p. 703 (code as amended), or an NRA notice disposing of a showing. |
| EO:6730 | blocked | Statements 1 (FTC/NRA basing-point study, six-month report) and 2 (undertaking to provide employee elections) have no held ending or completion evidence; a report deadline is not an end. Inventory also omits the approval paragraph (chars 0-1365). Sources needed are named in the decision row. |

Submitted: 4. Blocked: 2.

Why June 14, 1935 for the plain approvals: the Act (48 Stat. 195, held) made an approved code the enforceable standard (sections 3(b), 3(c)) and made the approval revocable (10(b)); the resolution repealed the approval and enforcement provisions together with no saving clause. This is the reason the general repeal extinguished the approval (owner ruling 2026-10-28). Disclosed alternatives in every row: Schechter (1935-05-27, earlier, not shown to reach each code), EO 7076 (1935-06-15, later, continues orders only so far as consistent with the amended Act and disclaims code approval and enforcement), and the section 5 antitrust exemption running to April 1, 1936 plus 60 days (a statutory consequence, not a command). A reviewer who disagrees with the judgment should look at those three. EO 7076 and EO 7075 are cited in prose only, not as evidence references: the held APP text of EO 7075 has elisions (not a complete text) and EO 7076's transcription lacks its signature and date lines, so complete-text confirmation would have been untrue.

## Where the time went (one line per order)

- EO:6331B: identity and page check, then the shared NIRA end-source work (finding and excerpting 49 Stat. 375, 48 Stat. 195, Schechter) that all plain approvals reuse.
- EO:6370: same; plus checking the only other corpus hit (an unrelated 1940 Federal Register contents line).
- EO:6530: deciding the inventory split (approval vs. overtime stay), the inclusive/exclusive stay reading, and confirming nothing modified the stay.
- EO:6730: reading EO 6751, 7085 and 7010-H to test whether the statements could be shown performed; they could not, and the inventory gap needed spelling out.
- EO:6320: trying to find any held record of whether cause was shown against the amendment before Oct 13, 1933; none exists.
- EO:6242E: reconstructing the stay chain (EO 6407, 6424, 6463, 6476), deciding the exception's end (Dec 11 vs. Dec 4), and handling the one source whose page bytes are not committed.

Shared time: roughly the first third on reading the route documents and rulings and on the full-corpus citation search (51,237 files); about a quarter lost to the Valla pin failures and the re-preparations (below).

## Batch-check counts

applied-v1 (first run): apply 4 assembled, 2 blocked. batch-check: strict_claim_pass 4, fail 0; actual checker 4 checked, 3 all-checks-passed, 1 mechanically unverified (EO:6242E later event EO 6463: "source_held:custody_record_only", the page bytes for that sha256 are a custody record only), gate_passed 4. Exit code 1 because of that actionable item.

applied-v2 (final): I dropped EO 6463 as a pinned later event (its content stays in the prose, flagged as not pinned) and removed its working-text confirmation. apply: assembled_proposal 4, blocked 2. batch-check: packet_members 6, claims_checked 4, strict_claim_pass 4, strict_claim_fail 0, actionable_failures 0; actual checker claims_all_checks_passed 4, mechanical_pass 4, unverified 0, fail 0, gate_passed 4. independent_human_certifications 0 (this is a mechanical gate, not review).

## Tool defects hit

1. Valla context pin instability. load_packet compares jobs/valla `attach()` output, which includes the count of tracked RATIONALES.json package folders under research/excavator and research/production (`git ls-files`). That count changed three times during my session (68 at preparation, then 75, then 76) as other sessions' packets (t1, t2, try1) and then my own packet-v2 were committed/staged. Result: `view`, supplement `prepare` and `apply` fail with "changed Valla review context; prepare a new version", and re-preparing is itself invalidated if anyone stages a new package folder before the next step (my packet-v2 became stale because its own folder was committed after it was prepared). Workaround: prepare a fresh parent and immediately run the supplement prepare in one command, then do not let anything add tracked packages until apply and batch-check finish. A packet should not pin a global package count that concurrent work changes.
2. The supplement and `kit.py view` need an absolute repo path internally in some calls (`batch.load_packet(folder, repo)` with a relative repo raised "path outside repository"); CLI use with `--repo .` works.
3. `kit.py apply` prints nothing until it finishes (about 50 s here) and the exec harness blocks foreground sleeps; waiting needed an until-loop.
4. Held-source quality notes (not tool bugs): APP page for EO 6424 carries the title of a different order (Imported Date Packing) around the text of the stay extension, which is why I did not use it as a registered text; APP EO 7075 text has elisions; APP EO 7076 text lacks the signature and date lines; the raw page bytes for the EO 6463 sha256 are a custody record only.
5. No tool defect in `batch-check` beyond the exit code rule above.

## Notes for the owner and later reviewers

- Working-text confirmations (identity, complete text, pages) are set true only for the APP texts I read in full and page-checked and that the claims cite: each order's own text, plus EO 6407 and EO 6476 for EO:6242E. All carry the standing note: original not yet held; replace and re-check quotes when an official copy is retrieved.
- Possible follow-ups that would unblock the two blocked orders: the NRA "Codes of Fair Competition" compilation (vol. I p. 703, Oil Burner code as amended) for EO 6320; the FTC-NRA basing-point report (late 1934) and a record of the iron and steel employee elections for EO 6730.
- EO 6242E's denial clause uses an "exhausted by performance" end dated at the order itself (owner ruling 2026-10-28, standing application 1). Please check the reviewers accept that mechanism string for a denial.
- Worth remembering: a producer who needs a supplement should run `kit.py prepare` and the supplement `prepare` back to back (see defect 1).

Tool calls made: approximately 125 (an estimate; the session was resumed from a compacted context and no counter is available).

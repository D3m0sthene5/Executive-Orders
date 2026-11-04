# Producer report, packet a01 (Tribonian)

Start 2026-11-04T04:48:13Z. End 2026-11-04T04:58:55Z.

## Outcome

No decision sheet was filled and no applied directory exists. 0 orders submitted, 0 blocked by research, 33 unprocessed.

Every claim-kit command that reads the packet refuses with `claim-kit: changed prior research; prepare a new version`. This covers `kit.py view`, with or without `--order`, and `kit.py apply <packet> --write <packet>/applied-v0test`. Nothing was written by the failed apply. The refusal is not the "changed Valla review context" message named in the instructions, but it is the same kind of stop: the packet's frozen prior-research fingerprint no longer matches the repository. No file in this packet folder is newer than the packet preparation time (2026-11-03 23:44:42 -0500), and no file under `research/` or `jobs/` outside the sibling batch folders is newer than 04:40Z on 2026-11-04. The most likely cause is that other batch packets in this lot (for example o11, o14 and o25) were prepared after a01 and add files under `research/` that the prior-research discovery now counts. I did not open sibling batch folders to confirm this. A coordinator must re-prepare a01 (or rerun preparation for the lot in one pass) before any sheet can be applied or checked. A sheet filled against the current dossier hashes would be refused anyway.

`decisions.csv` and `clauses.csv` are unchanged. Reading the prebuilt views, I found the following leads. They are not decisions and have not been through apply or batch-check.

## Leads from the prebuilt views and held texts (not decisions)

- EO 9830 (12 FR 1259), preamble "it is hereby ordered as follows, effective May 1, 1947:", Part III, "The following Executive orders are hereby revoked:", lists 8214, 8257, 8283, 8937, 9027, 9052, 9333, 9405, 9644, 9653 and 9691. EO 9815 is not in the list. The packet has citable EO 9830 revocation records only for 9027, 9052, 9405, 9644 and 9691. For 8214, 8257, 8283, 8937, 9333, 9653 and 9815 the dossier says "target provision not located: EO:9830" or leaves the actor text as unloaded overflow, so those orders cannot cite the revocation from this packet. The EO 9830 PDF is not stored under `jobs/fr-originals`, so a source supplement from it looks unavailable. The held EO 9830 text records the same 1947-05-01 effective date for EO 7975-A in `research/excavator/counterexample-first-2026-10-26/packet`.
- EO 9333 says "For the duration of the war and six months thereafter". An own-terms end before 1947-05-01 is a candidate that must be tested before EO 9830 is accepted as its first end.
- EO 9644 section 2 applies only "During the period the Civil Service Commission is operating under the War Service Regulations". Its own end depends on EO 9691. EO 9691 has 16 inventory rows with transitional windows and a July 1, 1946 report date, so it needs clause-level work. EO 9815 amends section 7 of EO 9691 and depends on that analysis.
- EO 9653 amends about twenty Schedule A and B paragraphs and runs onto page 13621. The machine inventory has duplicate scopes and needs correction before any claim.
- EO 9067: the view's `own_original_text` is bounded to a clause envelope and shows EO 9066 (military areas) text, with `verified_whole_order` false. The real order (7 FR 1407, sections 1 to 6) needs an inventory override. EO 9243 section 3 revokes it "effective on the fifteenth day following the date of this order" (September 12, 1942, so September 27, 1942) with a proviso saving reemployment rights already acquired. EO 9695 (1946-02-08) later revoked EO 9243, and EO 9994 deals with surviving reemployment rights.
- EO 8751 is revoked by EO 8926 section 5 (1941-10-28), and EO 9301 by EO 9607 (signed 1945-08-30, no delayed effective date). Both have citable ACT records. EO 8226 is superseded by EO 8384 section 21. That section is effective "as of March 2, 1940" and EO 8384 is dated 1940-03-29, so the effective date needs a decision.
- EO 8168 has two commands: revocation of the 1898 order (performed on signing) and a reservation of the lands. EO 8854 (1941-08-16) revokes EO 8168 and re-reserves the lands. The inventory should be split.
- EO 8402, 8497 and 8538 are one-year exemptions with own-terms ends of 1941-09-30, 1941-10-31 and 1941-09-30. Each has held TERM evidence and a held "further exempt" order (8896 for 8402, 8905 for 8538, 8904 and 9238 for 8497). The extensions are later events, not ends.
- EO 10480 section 607 (1953-08-14, no separate effective-date clause) "superseded or revoked" 10161, 10169, 10193, 10200, 10223, 10359, 10373, 10377 and 10433. Section 605 continues the Economic Stabilization Agency to October 31, 1953, and section 606 saves prior actions. Orders touching Part IV of EO 10161 (the agency and the Wage Stabilization Board) have an open question about whether the agency and board clauses ended on that date.
- EO 10223 was already revoked by EO 10281 (1951-08-28) in its section 404 trailing sentence. EO 10161 Part IV sections 403 and 404 were revoked and replaced by EO 10233, and sections 403 to 410 were revoked by EO 10377, so some clauses of EO 10161 have earlier partial ends. EO 10433 mixes one-time commands (sections 1(a) and 1(b)) with continuing ones.
- EO 10685 is superseded by EO 10900 (1961-01-05), and section 1 was revoked earlier by EO 10827 (1959-06-25). EO 10483 and its amendment EO 10598 were followed by EO 10700 (1957-02-25), which needs reading as a possible supersession. EO 10700 was revoked by EO 10920.
- Corpus searches found no held text that names the National Advisory Committee on Mobilization Policy (EO 10169) other than EO 10480. A search for the Schedule A subdivision phrases of EO 9027, 9052 and 9405 found no later order rewriting the same paragraph.

## What took the time (one line per order)

Reading was limited to the views and a few actor texts. No per-order time was recorded for the 33 orders because none was processed.

## batch-check counts

Not run, because apply refused.

## Geddes

Not run. No applied directory exists. There are no flags and no `GEDDES_RESOLUTIONS.json`.

## Full-packet files opened beyond the views

- `PACKET.json` (read in part, for EO 9830 evidence ids and one TERM record)
- `decisions.csv` and `clauses.csv` (headers and sample rows)
- `LOOKUPS.md` (first 3000 characters)

I did not open `READ.md` or `LOOKUPS.details.json`.

## Tool defects

1. `kit.py view`, `kit.py view --order` and `kit.py apply` all fail with `changed prior research; prepare a new version` on a packet that is unchanged since preparation. Preparing sibling packets in the same lot may invalidate earlier ones.
2. The views for EO 9067 and EO 9333 carry bounded or mis-identified own text (EO 9067 shows EO 9066 text).
3. The EO 9830 revocation is citable for 5 of the 12 orders it names, because the dossier builder did not locate the rest.

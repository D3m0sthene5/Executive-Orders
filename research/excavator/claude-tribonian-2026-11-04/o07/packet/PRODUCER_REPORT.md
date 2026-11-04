# Producer report, packet o07 (Tribonian)

Start UTC 2026-11-04T05:21:16Z. End UTC 2026-11-04T06:16:02Z. Final applied directory: `applied-v2` (applied-v1 was a mechanics test of the same 21 claims before the 9 blocks were recorded).

## Outcomes

Submitted 21, blocked 9, unresolved 0.

Submitted (all `no`, one terminated clause each, `transferred_or_accrued` savings, APP mirror transcriptions with the standing note):
- Own-terms end, inclusive last day (exclusive reading disclosed): 8796 (1942-07-31), 8801 (1942-07-31), 8804 (1941-09-30), 8805 (1942-06-30), 8810 (1942-06-30), 8825 (1942-08-31), 8828 (1942-09-30), 8829 (1942-08-31), 8835 (1942-10-31), 8836 (1942-08-31), 8866 (1942-09-30), 8873 (1942-08-31), 8896 (1942-09-30), 8897 (1942-09-30), 8899 (1942-09-30), 8901 (1942-09-30), 8903 (1942-11-30), 8905 (1942-09-30).
- 8904 (1942-10-31): EO 9238 of 1942-09-03 further exempts the same person; recorded as a later event, not an end.
- 8827 (1942-10-31): EO 8844 (1941-08-08) amended the period before the original last day, 1941-10-31; recorded as a later event with before and after text under the strike-and-insert ruling.
- 8844 (1942-10-31): the amending sentence's own period.

Blocked (held text is only the OCR layer of the Federal Register issue, or the inventory or end is not supportable):
- 8799, 8822: no page image of 6 FR 3049 and 6 FR 3529. The 8822 inventory span also runs into EO 8821. Which of EO 9134 (April 15, 1942) or EO 9562 (June 4, 1945, effective June 30, 1945) first ended the amended command cannot be settled without the official EO 9134 text.
- 8815, 8845, 8846, 8885: no page image. The 8845, 8846 and 8885 inventories are mis-segmented. 8815 and 8845 also need a Customs regulations history.
- 8853: EO 9720 (1946-05-08) discontinued the area. Its effective date needs the 11 FR 5105 image.
- 8887: the dossier inventory omits the operative sentence and the 20 names. The end depends on a Civil Service Commission notification that is not held.
- 8888: the appointment's exhaustion and the authority's end are held only as OCR or APP text.

## What took the time
- Whole run: the packet's `apply` takes 3 to 6 minutes (source hashing). The number search over 33k held texts takes about 2 minutes.
- 8796 through 8905 simple exemptions: scripted generation with exact-quote assertions, so little per-order time.
- 8827, 8844, 8904: reading the amendment and extension texts.
- Blocked orders: confirming the text grade and inventory defects.

## Checks
- batch-check on applied-v2: 30 members, 21 claims checked, strict pass 21, strict fail 0, outcomes 21 assembled and 9 blocked. Actual checker: 21 `claims_gate_passed`, 0 mechanical failures, 21 mechanical-unverified. Every unverified item is `source_held:custody_record_only` or the known `date_valid` evidence note. The coordinator is retaining those bytes.
- batch-check exits 1 because it counts those unverified items as "actionable". No assembly errors remain.
- Geddes: 21 claims, 0 defect flags, 2 coverage gaps (EO 8844, `order_heading_unresolved`), recorded as disputed in `applied-v2/GEDDES_RESOLUTIONS.json`.

## Full-packet files opened beyond the views
None of LOOKUPS.details.json or READ.md. I loaded PACKET.json once through `load_packet(check_sources=False)`, a pickle copy of which is under /tmp/claude-0/tribonian-work/o07/. I read the packet's decisions.csv and clauses.csv, since I edited them.

## Tool defects
- `cruden.py search` has no `--help`. It prints scan results only after 2 minutes.
- `batch-check` exits non-zero when the only findings are custody_record_only unverified items.

# Producer report, Erasmus batch e3 (claude)

Start 2026-11-02T04:25:55Z; end 2026-11-02T04:31:42Z. Final applied directory: `applied-v1`.
Two orders, both submitted; none blocked.

## Outcomes

**EO 12121 (Energy Coordinating Committee), submit, terminated 1982-08-17.** The order's only command adds two
members to section 1-102 of EO 12083. The first and whole-order end is EO 12379 section 20, which revokes
"Executive O rder No. 12083, as amended" (held FR text, 47 FR 36099-36100). EO 12379 has no effective-date or
savings wording. EO 12156 is recorded as a later amendment event. The Community Services Administration abolition
and the Council on Wage and Price Stability are disclosed as earlier candidate ends under the unnamed-instruments
ruling.

**EO 11436 (suspension of 10 U.S.C. 6372), submit, terminated 1986-02-25.** The order is one sentence resting on
10 U.S.C. 6386(c). EO 12553 revokes it by number in its table (held FR text, 51 FR 7237). The National Emergencies
Act (its section 502(a)(8) excludes section 6386(c)) and the Pub. L. 96-513 repeal of sections 6372 and 6386
(section 335, effective 1981-09-15 under section 701(a)) are disclosed as earlier candidates that do not name the
order. The page citation 33 FR 17943 is not printed in the extracted text, so `original_pages_confirmed` stays false.

## Brief defects

- EO 12121, second-review defect (USC "no hit"): **confirmed and fixed.** `jobs/current-law/output/ORDERS_CURRENT_LAW.csv`
  records usc_mentions=1 and ecfr_mentions=0 for this order. MENTIONS.csv usc:23f802d2b69d is the OLRC note under
  42 U.S.C. 7101. earlier_end_check and research_rationale now quote that note ("as amended by Ex. Ord. No. 12121,
  Feb. 26, 1979, 44 F.R. 11195"; "was revoked by Ex. Ord. No. 12379, § 20, Aug. 17, 1982, 47 F.R. 36100") and
  state that the eCFR search records no mention. The two eCFR rows containing "12121" are page citations
  ("27 FR 12121") naming EO 7233.
- EO 12121, first-review defect (unnamed earlier candidates): already fixed in the second attempt. I rechecked it
  against the held EO_12344, EO_12160 and EO_12154 codification notes and the held EO 12288 text, and every quote matches.
- EO 11436, second-review defect (63-character hash): **confirmed and fixed.** Running sha256sum on the held
  NEA text gives `9af91c5062c556d26e97baaad68d89a4aa6cbfbb51937898bc13ef801d78a350`, which is now used in all three places.
- EO 11436, first-review defect (5711(b)): already fixed in the second attempt. I confirmed that the order cites
  only section 6386(c).

## Other corrections found on recheck

- EO 12121: the second attempt named Pub. L. 97-35 as "the Omnibus Reconciliation Act of 1981". That name is not
  in any held source and is inexact, so I removed it in three places.
- EO 12121: "EO 12083 (held FR text of September 27, 1978)" is now "signed 1978-09-27; held Federal Register text,
  43 FR 44813, issue of September 29, 1978". The FR issue is dated September 29.
- EO 12121: the EO 12156 later-event mechanism now explains that EO 12148 section 5-211, as first issued (held FR
  text), added "(x) the Director of the Federal" Emergency Management Agency. That reused the letter EO 12121 had
  given the Community Services Administration Director, and EO 12156 corrected it to (z). Neither EO 12148 nor
  EO 12156 removes EO 12121's entries.
- I re-verified everything else against held bytes and changed nothing else. This covers the EO 12379, EO 12553,
  EO 12156 and EO 12121 quotes, the NEA section 502(a)(8) quote, and Pub. L. 96-513 sections 335 and 701(a)-703.
  It also covers the savings-word scans of EO 12553 and EO 12379, the OFR catalog note "Revoked by: EO 12379,
  August 17, 1982", and the absence of any sunset in EO 12083.

## Checks

batch-check on applied-v1: 2 checked, 2 strict pass, 0 fail, 0 actionable failures. Actual checker: 2 of 2 passed
all checks. Geddes lint: 0 defect flags and 0 coverage gaps (GEDDES_LINT.json), so no GEDDES_RESOLUTIONS.json was
needed. The apply/batch-check console log is `applied-v1/RUN.log`.

## Time per order

- EO 12121: most of the time went into checking the current-law mention files and the EO 12148/12156 lettering.
- EO 11436: most of the time went into re-verifying the NEA and Pub. L. 96-513 provisions and the EO 12553 savings scan.

## Tool notes and full-packet files

I opened no full-packet files (PACKET.json, READ.md, LOOKUPS.details.json) beyond the views. The views and LOOKUPS
were enough. The current-law mention rows are not in the view, so I read `jobs/current-law/output/*.csv` directly.
A view field showing each order's current-law mention counts would have caught the EO 12121 defect.
No tool defects. My first console redirect wrote the log to `e3/` outside the packet; I moved it into
`applied-v1/RUN.log`.

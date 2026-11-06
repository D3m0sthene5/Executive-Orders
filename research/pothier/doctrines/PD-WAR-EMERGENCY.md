# PD-WAR-EMERGENCY: war and emergency orders

This family doctrine covers 263 orders. X1 typed them as `alien_property_sale` (158), `wwi_emergency` (97), `labor_hours_suspension` (7) and `defensive_sea_area` (1). The machine form is `research/pothier/doctrines/PD-WAR-EMERGENCY.json`. Both forms apply the coordinator's rulings P1-P8 (`research/pothier/COORDINATOR_RULINGS.md`). Status leads are proposals for the owner, not statuses. Nothing here changes a status, the codebook, the census or the certified count (0).

## Conclusions

The doctrine proposes these leads:

- **`no` for 35 members**: the order ended before the cutoff of 2026-10-14. Eighteen rest on the order's own terms (`TERM`). Seventeen rest on a later order or statute whose words reach the member (`ACT`).
- **`yes` for no member**: no current statute, regulation or official record shows any of these orders in force today.
- **`open` for 228 members.**

The engine reports 0 contradictions. Twenty-nine members carry held later-event edges; section (e) explains each kind and why none changes a lead.

The 35 decided members end in one of six ways.

1. **Spent on issue, or merged into the order they amend (13 members, `TERM`).**
   - Four orders only rescind another order, dissolve a body another order created, or restore powers (B03, ruling P1).
   - Eight orders only amend another order or rule (B03B and B03D, ruling P2). Each one's text continues as part of the parent order until the parent ends; the parent's lifecycle carries it.
   - EO 3176 itself takes title to all seized enemy vessels, a single act done on issue (B03C).
2. **Exhausted by performance (1 member, `TERM`).** EO 3259 authorized one sale of 4,505 shares of the First Reinsurance Company. EO 3265 of April 29, 1920 corrects its schedule to match "the terms of the actual sale made by the Alien Property Custodian", so the sale was made between April 16 and April 29, 1920 (B03E).
3. **The order's own stated end (4 members, `TERM`).**
   - EO 3233 ran until midnight on April 30, 1920.
   - EO 6023 closed the air over Washington from 9 a.m. to 5 p.m. on March 4, 1933 (inauguration day). It is not a defensive sea area.
   - EO 2929 ran for the war and six months after a peace treaty was proclaimed, so it ended no later than June 20, 1922.
   - EO 2652 ran "for the duration of the war", so it ended no later than December 20, 1921.
4. **A later order abolished by name the only thing the member created or commanded through (6 members, `ACT`, ruling P7).** EO 3320 of August 21, 1920 abolished the Food Administration (created by EO 2679-A) and the office of Wheat Director (created by EO 3087). It also confined the Grain Corporation to liquidation. Four orders that commanded only through those offices end with them: EO 2736, 2884, 3100 and 3143.
5. **A later order revoked the member (2 members, `ACT`).** EO 2952 revoked EO 2913, and EO 3180 rescinded EO 2837.
6. **A delegation of statutory powers that the statute itself ended (9 members, `ACT`, ruling P8).** Each of these orders does nothing but hand on powers that one statute granted, and rests on that statute alone. The statute's own words then ended those powers:
   - the Lever Act, 4 members: "the provisions of this Act shall cease to be in effect";
   - the emergency shipping fund, 2 members: "All authority granted to the President herein, or by him delegated, shall cease";
   - the Overman Act, 3 members: "any authorization of the President under this Act to the contrary notwithstanding".

The 228 open members fall into these groups:

| Branch | Members | Why open |
|---|---|---|
| B18 | 153 | Alien Property Custodian sale, rejection, resale and release orders. Whether and when each act was done is in the Custodian's reports, which are not held. No class-wide event ends an unexercised authorization. |
| B21 | 19 | Single acts and transfers with no record of performance. |
| B99 | 14 | Other members (catch-all). |
| B19 | 8 | Other delegations under the Trading with the Enemy Act. |
| B20 | 7 | Eight-hour suspensions and waivers. |
| B11 | 5 | Orders for one named person. These follow PD-CS-ONE-PERSON. |
| B13X | 5 | Orders resting on the Lever Act or the shipping fund that do more than delegate, or that also invoke other powers. |
| B09 | 4 | Orders of the Committee on Public Information. The Committee's end depends on a transfer that no held record dates. |
| B15X | 4 | Overman Act orders that also invoke "any and all other Acts of Congress" or "all other powers". |
| B14X | 2 | Shipping fund delegations under 1918 Acts not yet read. |
| B16 | 1 | EO 2868, the War Industries Board order: the Board was dissolved with continuations whose ends are not held. |
| B01, B02 | 6 | Five members whose held text belongs to another order (families named), and one number with no order on record. |

The most valuable acquisitions are the Custodian's reports (they would decide most of the 153 sale orders) and the texts of the 1921 peace treaties and the Overman Act (they would fix dates for several open and decided members).

## (a) Mechanisms

Three terms recur. A **delegation** is an order that hands a power the President holds to an officer or agency. A **candidate end** is a date on which an order may have ended, disclosed so the owner can see it, but not claimed as an end because no held evidence shows that the event reached the order. An **authorization exhausted by performance** is an order permitting one act, which has nothing left to command once the act is done.

**M1. Spent on issue, or merged into the parent (own terms).**

- Under P1, an order whose only operative content rescinds another order, dissolves a body another order created, or restores powers is spent on its date. What it changed belongs to the lifecycle of the order it acted on.
- Under P2, an order whose only operative content amends another order merges into that parent on issue. The doctrine recognizes such an order by its operative amending words ("is hereby amended", "I do hereby amend", "is hereby revoked; and in place thereof"), not by the word "amendment" in a recital of authority. Each such lead carries the disclosure "its text continues as part of the parent until the parent ends; the parent's lifecycle carries it". If the owner prefers to treat an amending order as living as long as the amended text lives, these leads become `open` pending the parent.
- EO 3176 says "the possession and title of the United States in all such vessels is taken over". That single act is done by the order itself. The title is a surviving consequence.

**M2. A stated end (own terms).** A stated day is read inclusively: the order runs through the end of that day, under the owner's ruling of 2026-10-21. The exclusive reading is noted. Two orders key their end to the war:

- EO 2652 runs "for the duration of the war". Three later instruments bear on the war's end:
  - the Knox-Porter Resolution (42 Stat. 105) declared the state of war with Germany at an end on July 2, 1921;
  - the treaty with Germany, proclaimed November 14, 1921 (42 Stat. 1939), closed the war;
  - the last 1921 treaty, with Hungary, was proclaimed December 20, 1921 (42 Stat. 1951).

  On any reading, the stated period was over by December 20, 1921.
- EO 2929 runs for the war "and for six months after the termination thereof by the proclamation of a treaty of peace". That ends no later than June 20, 1922.

The joint resolution of March 3, 1921 does not supply these dates. It governs "Acts of Congress, joint resolutions, or proclamations", not the words of an executive order.

**M3. Abolition by EO 3320 of the member's only subject (later instrument, ruling P7).** EO 3320 of August 21, 1920 did four things:

- It declared "said United States Food Administration, and all remaining divisions and branches thereof" terminated and abolished. It describes the Food Administration as "a Government agency organized and conducted pursuant to Executive Orders and Proclamations of the President"; EO 2679-A is the order that organized it.
- It terminated and abolished "the executive administration and office created by said Executive Order of May 14, 1919". That is EO 3087, which created the Wheat Director.
- It kept the Grain Corporation alive only as "continuing to act as a governmental agency for this purpose only", meaning liquidation.
- It saved sugar licenses and sugar regulations.

EO 3087 also let the Grain Corporation buy and sell 1919 wheat, but only "with the approval of the United States Wheat Director"; its other provisions (closing the Corporation's books, changing its name, raising its capital) were completed acts. The four orders that command only through these offices (EO 2736, 2884, 3100, 3143) end no later than August 21, 1920.

**M4. The Committee on Public Information (lead only).** EO 3154 ordered the Committee's papers and property transferred to the Council of National Defense. It provided that "upon such relinquishment and transfer the Committee on Public Information shall cease and be at an end". So the end is conditional on a transfer, and no held record shows that transfer. The National Archives entry ("Abolished: By EO 3154, August 21, 1919") restates the order's issue date and does not record the transfer, so it supports the date only weakly. A record of the transfer itself would decide the four orders creating the Committee and its divisions.

**M5. The Lever Act's provisions ceased (statute, ruling P8).** Section 24 of the Act of August 10, 1917 (40 Stat. 276, 283) provides that "the provisions of this Act shall cease to be in effect when the existing state of war between the United States and Germany shall have terminated, and the fact and date of such termination shall be ascertained and proclaimed by the President". It saves only acts already done, rights and obligations already accrued, pending suits and prosecutions.

The joint resolution of March 3, 1921 (41 Stat. 1359-1360) fixes the date. For any Act whose provisions depend on when the war ended, it treats the resolution's effective date as that date, "notwithstanding any provision in any Act of Congress or joint resolution providing any other mode of determining the date of such termination". That displaces the Lever Act's own mode of fixing the date by proclamation. The resolution does not except the Lever Act, so the date is March 3, 1921.

Some orders' only operative content is a delegation of the Act's powers, or a direction on how the delegate is to use them, and they rest on the Lever Act alone. Those orders end with the powers: the ceasing words reach the very provisions delegated, so the delegate has nothing left to exercise. An order that also invokes "other powers vested in me by law" (EO 3235, 3240) is not reached as a whole and stays open.

A repeal of the authority to make new orders works differently; the standard example is FLPMA section 704(a). Existing orders keep operative effect of their own after such a repeal.

**M6. The Overman Act terminated (statute, ruling P8).** The Act of May 20, 1918 was to remain in force "during the continuance of the present war and for six months after the termination of the war by the proclamation of the treaty of peace, or at such earlier time as the President may designate" (40 Stat. 556). It then provides: "Upon the termination of this Act all executive or administrative agencies ... shall exercise the same functions, duties, and powers as heretofore or as hereafter by law may be provided, any authorization of the President under this Act to the contrary notwithstanding" (40 Stat. 557).

Those words reach only authorizations under the Act. An order whose only operative content is a reassignment of functions under the Act, and which rests on the Act alone, ends with it. An order that also invokes "any and all other Acts of Congress" or "all other powers thereto me enabling", or that rests on another statute, is not reached as a whole; the Act's end is a candidate end for it. The Act's end date has three readings:

| Reading | End date |
|---|---|
| Under the 1921 resolution | September 3, 1921 |
| Six months after the German treaty | May 14, 1922 |
| Six months after the Hungarian treaty | June 20, 1922 |

The lead claims an interval from the order's date to June 20, 1922.

**M7. The emergency shipping fund ceased (statute, ruling P8).** The Act of June 15, 1917 (40 Stat. 182, 183) provides: "All authority granted to the President herein, or by him delegated, shall cease six months after a final treaty of peace is proclaimed between this Government and the German Empire". That date is May 14, 1922. It would be September 3, 1921 if the 1921 resolution governs the clause.

The section was later amended or enlarged:

- The Act of April 22, 1918 (ch. 62, 40 Stat. 535) amends the section "by adding a new provision" (clause (f), on street and interurban railways) and adds words to its paragraph (b). It has no end of its own, so its powers are part of the section the cessation sentence calls "herein".
- The Act of October 6, 1917 only raises the section's cost limits.
- The "Emergency shipping fund" sections of the Acts of July 1, 1918 and November 4, 1918 have not been read.

An order whose only operative content is a delegation of the section's powers, as amended, ends with them (EO 2664, 2888). An order that also delegates powers under the two unread 1918 sections stays open (EO 3018, 3064).

**M8. The War Industries Board was dissolved, with continuations (lead only).** EO 3019-A orders the Board and its subordinate bodies to "terminate and dissolve on January 1, 1919". Four exceptions survive that date:

- officials continued "for such limited period after January 1, 1919 as may be necessary ... but in no event longer than the proclamation of peace";
- the Price Fixing Committee, until prices it had already fixed expired;
- the Planning and Statistics and Wool Division functions, transferred to other bodies until completed;
- the Board itself, "for the sole and only purpose of winding up".

EO 3019-A rests on the Overman Act "as well as ... any and all other Acts of Congress", so the Overman Act's end does not reach it as a whole. Its own "proclamation of peace" cap covers only the first exception and depends on a treaty proclamation that is not held. EO 2868, which made the Board a separate agency, rests on the Council of National Defense provisions of the Act of August 29, 1916. The dissolution is a candidate end for both orders.

**M9. Revocation by a later member (later instrument).**

- EO 2952 (September 6, 1918) revokes "the Executive Order issued July 15, 1918" on Squares 229 and 230. That order is EO 2913.
- EO 3180 (November 25, 1919) rescinds "the Executive Order of April 11, 1918", which is EO 2837, "as of the 14th day of July, 1919". EO 2837 had forbidden certain licenses "until further order".

**M10. The War Trade Board (lead only).** The held EOs 3059 and 3086-A only authorize the transfer of the Board's work to the State Department "whenever ... expedient". The National Archives records the Board as abolished effective June 30, 1919, but that finding aid is not held. So June 30, 1919 is disclosed as an earlier candidate end, and no lead rests on it. EOs 3059 and 3086-A are decided under M6 as Overman Act reassignments.

**M11. The joint resolution of March 3, 1921 (class event, lead only).** The resolution ends no order directly. It reaches an order only through a statute the order rests on, and only if that statute's force depends on the war. It does not govern executive-order wording. It excepts:

- the Trading with the Enemy Act and its amendments;
- the Liberty Bond Acts;
- titles 1 and 3 of the War Finance Corporation Act;
- Pub. Res. 55;
- Title 2 of the 1919 Food Control and District of Columbia Rents Act.

**M12. The Custodian's functions continued (continuity only).** Five instruments moved the Custodian's functions:

- EO 6694 (May 1, 1934) moved them into the Department of Justice.
- EO 9095 (March 11, 1942) created a new Office of Alien Property Custodian.
- EO 9142 (April 21, 1942) gave that office the functions, personnel and property of the Justice Department's Alien Property Division.
- EO 9788 (October 14, 1946) terminated that office. It vested "all authority, rights, privileges, powers, duties, and functions", and all property still held, in the Attorney General.
- EO 11281 (May 13, 1966) recites that the Office of Alien Property would be abolished by June 30, 1966. It moves only the blocking controls of EO 8389.

None of these extinguishes an authorization already given. Section 5 of the Knox-Porter Resolution retained enemy property. The Trading with the Enemy Act, including section 12 (now 50 U.S.C. 4312), is still law.

**M13. Sale authorizations used up by performance (lead only).** Each sale, rejection, resale or release order is used up when its act is done. The date of that act comes from the Custodian's reports. No order sets a deadline; a search of all 158 texts found none.

**M14. Eight-hour suspensions and waivers (lead only).** A suspension or waiver for named work ends on completion of the work, on its own term, or by a further order. Two authorities are used:

- Section 2 of the Act of June 19, 1912 (37 Stat. 137, 138) lets the President waive the eight-hour law "as to any specific contract" "during time of war or a time when war is imminent". That power depends on war. EO 2663 rests on it alone, and EO 2678 rests on it together with the 1917 proviso.
- The proviso of the Act of March 4, 1917 (39 Stat. 1192) lets the President suspend the law "in case of national emergency".

The 1921 resolution governs how Acts "containing provisions contingent upon the duration" of the 1917 war, or of the "present or existing emergency, meaning thereby the war", are construed. Whether it reaches either power is unsettled. Even if it does, its words say nothing about waivers already granted for specific contracts. A waiver once granted is an exercise of the power, not a delegation of it, so ruling P8 does not apply. March 3, 1921 is therefore a candidate end only.

**M15. Named persons (ruling P4).** An order whose operative content is one appointment of, or designation to act by, one named person follows PD-CS-ONE-PERSON.

**M16. Performance recorded in a held later order (own terms).** A single sale authorization is exhausted when a held later instrument records that the authorized sale was made. EO 3265 does this for EO 3259. The lead is an interval from the authorizing order's date to the recording order's date. The family texts were searched for other such recitals:

- EO 3227 (February 13, 1920) authorizes the Custodian to confirm "sales heretofore made by him" under Frank L. Polk's orders of February 26 and April 5, 1919 (EO 3016C and 3016K). It speaks of such sales only conditionally ("in the case of sales heretofore made") and names no property, so it does not show any particular sale.
- EO 3016J recites an earlier sale of Locomotive Superheater stock, but that is not the sale it authorizes.

## (b) Sources

The member's own text is source S0 under ruling P6; the engine records its path, sha256 and grade on every lead.

Sources held in the repository. Each was opened and its pin phrase found (some only with whitespace collapsed, as the engine reads text):

| Id | Source | Held path | sha256 (text) | Pin |
|---|---|---|---|---|
| S1 | Joint Resolution of Mar. 3, 1921, ch. 136, Pub. Res. 64, 41 Stat. 1359-1360 | `jobs/astra-source-retention/output/pages/d811bcf2.../dc025512.../selected-pages.txt` | 881d541d4c87f4a2c0e7a0bcd000c6b72af47116ccc5cff57f073a81e6e4870c (PDF d811bcf2c2b5...) | "shall be construed and treated as the date"; "excepting, however, from the operation"; "the Act known as the Trading with the Enemy" |
| S8 | EO 3320, Aug. 21, 1920 (APP transcription) | `jobs/app-executive-orders/output/texts/executive-order-3320-liquidation-united-states-grain-corporation.txt` | 8ebf01ab5fdd0fc79e7d6d9e9ef7d2056a163608a68d0c0dc906eb5a28182d98 | "the executive administration and office created by said Executive Order of May 14, 1919, is hereby terminated and abolished"; "continuing to act as a governmental agency for this purpose only" |
| S9 | EO 3154, Aug. 21, 1919 (Wikisource) | `jobs/wikisource-texts/output/texts/EO_3154.txt` | 9aa1c85c957633b283a3cbfaa4494dfaa64cd2a7ac7370d908e3d760a2d370b4 | "the Committee on Public Information shall cease and be at an end" |
| S12 | EO 3019-A, Dec. 1918 (page-scan OCR) | `jobs/pinakes-proquest-ingest/output/texts/EO_3019A.txt` | 88a3dffe27403c0e0dfe0a11b193f4a1f35f06e8f5ed9f0e4221a351385c49e2 | "terminate and dissolve on"; "for the sole and only purpose of winding"; "in no event longer than the proclamation of peace" |
| S13 | EO 2952, Sept. 6, 1918 (page-scan OCR) | `jobs/pinakes-proquest-ingest/output/texts/EO_2952.txt` | 8be021dd8b7b244d803dbb7cad0c94fa23f6beed7d14bc8443f55aa092a99bf4 | "Squares 229 and 230" (revoking words in OCR: "revoke and rescind the Executive Order issued July i 5, 1918") |
| S14 | EOs 3059 and 3086-A (page-scan OCR) | `jobs/pinakes-proquest-ingest/output/texts/EO_3059.txt`; `.../EO_3086A.txt` | 7b82fcbe2dc279ed6594589ebd25cdd92f9ba502e73cb395e634f845fa9f769e; fb7663ad5710690828ecda41e651e602719c26c6c3a0096e2150152f3d5ca076 | EO 3059: "to the Department of State"; EO 3086-A: "relinquish and transfer to the Department" (its OCR reads "Department ox State") |
| S15 | EO 9788, Oct. 14, 1946, 11 FR 11981 | `jobs/source-ladder/output/texts/EO_9788_2e0f1ac5d8.txt` | e6cb1640b3fc2a6adfe4ec97275f17148e5994c690bb12a33ae16b718c33f648 | "All property or interests vested in or transferred to the Alien Property Cus" |
| S20 | EO 3180, Nov. 25, 1919 (page-scan OCR) | `jobs/pinakes-proquest-ingest/output/texts/EO_3180.txt` | 37081abdcee20404fee36ee13a15ec4c8de1044e6b2cb749ecea921bc6fa3cf0 | "as of the 14th day of July, 1919" |
| S21 | EO 3265, Apr. 29, 1920 (page-scan OCR) | `jobs/pinakes-proquest-ingest/output/texts/EO_3265.txt` | a214dc90ee5f2914ee59121395c238a6be3a4b434821201581a6815c9028581d | "actual sale made by the Alien Property Custodian" (OCR "thte actual sale"); "Executive Order No. 3259" |
| S22 | EO 5427, Aug. 20, 1930 (APP transcription) | `jobs/app-executive-orders/output/texts/executive-order-5427-waiver-or-reduction-application-and-visa-fees-for-nonimmigrants.txt` | 44146be590569293ed270e736bd99b16af14866874b11b453e4ebe6cb16fe6f5 | "shall supersede the Executive Order No. 4224½ of May 15, 1925" |
| S23 | EO 3247, Mar. 19, 1920 (Wikisource) | `jobs/wikisource-texts/output/texts/EO_3247.txt` | 481abad0fcc8bf3e2e4e82db1a7d69b4a1b6e50943e37a5d1e0fc18cb032d810 | "except the Executive order of February 25, 1920"; "shall be suspended until otherwise ordered" |

EO 9095 (7 FR 1971) is also held, at `jobs/source-ladder/output/texts/queue_EO_6694_EO_9095_4f3b011a51.txt`, as context for M12. It creates the 1942 office; it does not transfer the Alien Property Division.

Sources read on the web and still to be acquired. All are listed in `FETCH_PROPOSED.jsonl`:

| Id | Source | URL |
|---|---|---|
| S2 | Lever Act, ch. 53, sec. 24, 40 Stat. 276, 283 | https://www.govinfo.gov/content/pkg/STATUTE-40/pdf/STATUTE-40-Pg276.pdf |
| S3 | Overman Act, ch. 78, 40 Stat. 556 (duration), 557 (termination paragraph) | https://www.govinfo.gov/content/pkg/STATUTE-40/pdf/STATUTE-40-Pg556.pdf |
| S4 | Act of June 15, 1917, ch. 29, emergency shipping fund, 40 Stat. 182, 183 | https://www.govinfo.gov/content/pkg/STATUTE-40/pdf/STATUTE-40-Pg182.pdf |
| S5 | Treaty with Germany, proclaimed Nov. 14, 1921, 42 Stat. 1939 | https://www.govinfo.gov/link/statute/42/1939 |
| S6 | Treaty with Hungary, proclaimed Dec. 20, 1921, 42 Stat. 1951 | https://www.govinfo.gov/link/statute/42/1951 |
| S7 | Knox-Porter Resolution, July 2, 1921, ch. 40, 42 Stat. 105 | https://www.govinfo.gov/link/statute/42/105 |
| S10 | National Archives Guide, Record Group 63 (Committee on Public Information) | https://www.archives.gov/research/guide-fed-records/groups/063.html |
| S11 | National Archives Guide, Record Group 182 (War Trade Board) | https://www.archives.gov/research/guide-fed-records/groups/182.html |
| S16 | EO 11281, May 13, 1966, 31 FR 7215 | https://www.archives.gov/federal-register/codification/executive-order/11281.html |
| S17 | Alien Property Custodian Report, 1918 to Feb. 15, 1919, and the annual reports 1919-1934 | https://catalog.hathitrust.org/Record/001756793 |
| S18 | Trading with the Enemy Act sec. 12 (40 Stat. 411, as amended Mar. 28, 1918), now 50 U.S.C. 4312 | https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title50-section4312&num=0&edition=prelim |
| S19 | Act of Mar. 4, 1917, ch. 180, eight-hour proviso, 39 Stat. 1192 | https://www.govinfo.gov/link/statute/39/1192 |
| S24 | Act of June 19, 1912, ch. 174, sec. 2, 37 Stat. 137, 138 (eight-hour waiver) | https://www.govinfo.gov/content/pkg/STATUTE-37/pdf/STATUTE-37-Pg137.pdf |
| S25 | Act of Apr. 22, 1918, ch. 62, 40 Stat. 535 (shipping fund amendment) | https://www.govinfo.gov/link/statute/40/535 |
| S26 | Urgent Deficiency Act of Oct. 6, 1917, "Emergency shipping fund" section (page unverified) | https://www.govinfo.gov/link/statute/40/374 |
| S27 | National Archives Guide, Record Group 131 (Office of Alien Property) | https://www.archives.gov/research/guide-fed-records/groups/131.html |
| S28 | Public Land Order 369, May 15, 1947, 12 FR 2038, as listed in BLM's table of PLOs 1-694 | https://www.blm.gov/sites/blm.gov/files/uploads/programs_lands-and-realty_land-tenure_withdrawals_public-land-orders_1-694.pdf |

Also proposed for acquisition:

- the Settlement of War Claims Act of 1928 (https://www.govinfo.gov/link/statute/45/254, page unverified), which would show which property was returned rather than sold;
- the "Emergency shipping fund" sections of the Sundry Civil Appropriation Act of July 1, 1918 (40 Stat. 634, as EO 3248-A cites that Act) and of the First Deficiency Appropriation Act, 1919 (November 4, 1918, page unverified);
- the text of EO 2687-A (August 21, 1917).

## (c) Decision procedure

Branches are tried in order, and the first branch whose conditions all hold decides. Every branch giving a `no` lead requires two things: the instrument id, and a phrase from the member's operative text. If the held text lacks that phrase, the member falls through to an `open` branch. The Lever Act and Overman Act branches also require that the member's text not invoke "any and all other" Acts or "other powers". Leads built on a scan or transcription carry the gap that the text is not an authenticated original. The engine flags every lead built on an unheld source.

| Branch | Members | Lead | Basis | Date rule | Rule |
|---|---|---|---|---|---|
| B01 | 5 | open | NONE | none | The held text is another order. EO 3042 and 3085 go to PD-NATIONAL-FOREST, EO 3060A to PD-CS-ONE-PERSON, EO 3097 to PD-CUSTOMS-CONSULAR. EO 4224's held text is EO 4224½ (visa fees), while its WPA summary describes a sale; the sale order's text is not held. |
| B02 | 1 | open | NONE | none | EO 3087-A: the held National Archives transcription says "There is no record in Archives or State Department of any Executive Order bearing this number. See No. 3086-A". |
| B03 | 4 | no | TERM | order date | P1 `spent_on_issue`: EO 3094-B, 3132, 3180, 3374. |
| B03D | 1 | no | TERM | fixed 1918-09-26 | P2 `merged_into_parent_on_issue`: EO 2967, dated from its printed date because the census gives only the year. |
| B03B | 7 | no | TERM | order date | P2 `merged_into_parent_on_issue`: EO 2743-A, 2801, 2940, 3030, 3049, 3099, 3265, with the P2 disclosure. |
| B03C | 1 | no | TERM | order date | EO 3176 takes title on issue. |
| B03E | 1 | no | TERM | interval 1920-04-16 to 1920-04-29 | EO 3259, `exhausted_by_performance`: EO 3265 records the actual sale. |
| B04 | 1 | no | TERM | fixed 1920-04-30 | EO 3233's stated end. |
| B05 | 1 | no | TERM | fixed 1933-03-04 | EO 6023's stated period. |
| B06 | 1 | no | TERM | interval 1918-07-31 to 1922-06-20 | EO 2929: war plus six months after a treaty. |
| B11 | 5 | open | NONE | none | One act for one named person (EO 2907-A, 2997, 3024-C, 3024-A, 3057), routed to PD-CS-ONE-PERSON. Candidate ends: EO 3320 (Aug. 21, 1920) for the acting Food Administrators; the National Archives' June 30, 1919 for the War Trade Board seats. |
| B07 | 2 | no | ACT | fixed 1920-08-21 | EO 2679-A and 3087, `ended_by_express_abolition_of_its_subject` (P7): EO 3320 abolished their offices by name. |
| B08 | 4 | no | ACT | interval to 1920-08-21 | EO 2736, 2884, 3100 and 3143 command only through offices EO 3320 abolished (P7). |
| B09 | 4 | open | NONE | none | EO 2594, 2708, 2774-A, 2822-A: the end is conditional on the EO 3154 transfer. |
| B10 | 1 | no | ACT | fixed 1918-09-06 | EO 2913, revoked by EO 2952. |
| B10A | 1 | no | ACT | interval 1919-07-14 to 1919-11-25 | EO 2837, rescinded by EO 3180 as of July 14, 1919. |
| B13 | 4 | no | ACT | interval to 1921-03-03 | EO 2690, 2694-A, 2765, 3173 only delegate Lever Act powers and rest on that Act alone (`ended_with_delegated_statutory_power`). |
| B13X | 5 | open | NONE | none | EO 3247, 2825-A and 3063 do more than delegate; EO 3235 and 3240 also invoke other powers. The Lever Act's end is a candidate end. |
| B14 | 2 | no | ACT | interval to 1922-05-14 | EO 2664 and 2888 only delegate the shipping fund powers of the 1917 section as amended (`ended_with_delegated_statutory_power`). |
| B14X | 2 | open | NONE | none | EO 3018 and 3064 also delegate powers under the 1918 shipping fund sections, which have not been read. |
| B15 | 3 | no | ACT | interval to 1922-06-20 | EO 3059, 3086-A and 3091 only reassign functions under the Overman Act and rest on it alone (`ended_with_delegated_statutory_power`). |
| B15X | 4 | open | NONE | none | EO 3019-A, 3161, 3248-A and 3249 also invoke other Acts or powers. The Overman Act's end is a candidate end. |
| B16 | 1 | open | NONE | none | EO 2868: the Board it made a separate agency was dissolved by EO 3019-A with continuations whose ends are not held. |
| B17 | 1 | no | TERM | interval 1917-07-03 to 1921-12-20 | EO 2652: "for the duration of the war". |
| B18 | 153 | open | NONE | none | Custodian sale, rejection, resale and release orders, including Frank L. Polk's orders under EO 3016 and EO 4224-A. |
| B19 | 8 | open | NONE | none | Other Trading with the Enemy Act orders. |
| B20 | 7 | open | NONE | none | Eight-hour suspensions and waivers. |
| B21 | 19 | open | NONE | none | Single acts and transfers with no record of performance. |
| B99 | 14 | open | NONE | none | Catch-all. |

The `try` run found 263 members: 35 decided (18 `TERM`, 17 `ACT`), 228 open, 0 contradicted.

Three census dates disagree with the held texts, and the leads use the printed dates:

- EO 2652: census 1917-06-03; the text is signed July 3, 1917.
- EO 2929: census 1918-07-30; the text is signed July 31, 1918.
- EO 2967: census "1918"; the text is signed September 26, 1918.

The `no` branches carry these gaps:

- B13, B14, B15, B06 and B17 rest on statute and treaty texts that are not yet held.
- B14 assumes no later statute extended the fund's authority. EO 3549 (held) quotes section 17 of the Merchant Marine Act of June 5, 1920, which moved the piers acquired under the fund to the Shipping Board on January 1, 1921. Its effect on the delegated authority has not been read. An earlier end would still fall inside the interval; an extension would not.
- B14's lead for EO 2888 relies on the ordinary reading that text inserted into a section by amendment becomes part of that section, and so falls within its "herein".
- B15 assumes the President designated no earlier end for the Overman Act. An earlier end would still fall inside the interval.
- B03E's exact sale date is in the Custodian's reports, not held.

## (d) Members the procedure cannot decide

The 228 open members are:

- **153 Custodian orders (B18).** Performance needs the Custodian's reports (S17).
  - EO 2832 is a general rule for lots worth no more than $10,000, not a single authorization.
  - Property returned under the 1928 Settlement of War Claims Act made the authorization moot. That needs its own evidence.
  - An order covering several lots needs one end per lot.
  - EO 4224-A's only operative clause authorizes a quit-claim deed for Cook County real estate. Amending EO 4073-A appears only among its stated reasons, so it is its own authorization, like EO 3923 and EO 4045.
  - EO 3183 authorized rejection of all bids at the September 17, 1919 auction of the First Reinsurance shares. EO 3259 recites that the shares had been "thrice offered at public auction and no satisfactory bid has been received", and EO 3265 records their private sale to another buyer by April 29, 1920. That shows the property was gone by then, but no held text shows the rejection itself. The coordinator may decide whether disposal of the subject ends an unexercised rejection authorization.
- **19 single acts and transfers (B21).** No held record shows performance. EO 2859-A has no held text.
- **14 catch-all members (B99).**
  - The Grain Corporation and the U.S. Housing Corporations (EO 2681, 3320, 2985-A, 3408): their dissolution records are not held.
  - Radio and cable control (EO 2585, 2605-A, 2604).
  - EO 2826: its "during the continuance of the war and until further orders" may run past the war.
  - EO 2687 is a mixed order. Its delegation of shipping fund powers ended under M7 (no later than May 14, 1922), but its delegation of the naval emergency fund powers of the Act of March 4, 1917 needs that section's terms, which have not been read.
  - EO 3017 needs the termination clause of the Act of July 18, 1918.
  - EO 2645: a Wikisource editor's note says EO 2687-A (August 21, 1917) superseded it, but EO 2687-A's text is not held. Under P3 the supersession must be read in EO 2687-A's own words; August 21, 1917 is a candidate end.
  - Other continuing war orders: EO 2616, 2874, 3053-A.
- **8 Trading with the Enemy Act delegations (B19).** The Act is excepted from the 1921 resolution and still in force, so each delegation's revocation or supersession must be found and read; EO 6694's text, for example, is not held. EO 2729-A is a multi-part order:
  - its Censorship Board part ended under EO 3132;
  - its War Trade Board part has a candidate end of June 30, 1919 (National Archives, not held);
  - its other parts remain open.
- **7 eight-hour suspensions and waivers (B20).** Three things are missing:
  - completion records for the covered work;
  - a settled reading of whether the 1921 resolution reaches the 1912 and 1917 powers, and whether a waiver already granted lapsed with them;
  - an instrument ending the "present national emergency" named in EO 2864 and 2928, and a revocation of EO 3015, which runs "until further order".
- **5 named-person orders (B11).** These follow PD-CS-ONE-PERSON.
- **5 orders resting on the Lever Act or the shipping fund (B13X).**
  - EO 3247 suspends the coal orders.
  - EO 2825-A adopts earlier takings and directs compensation.
  - EO 3063 directs a transfer of contracts.
  - EO 3235 and 3240 also rest on "other powers vested in me by law" and "all other powers me hereto enabling"; EO 3247 suspended both from April 1, 1920.
- **4 Committee on Public Information orders (B09).** These need a record of the transfer that EO 3154 made its condition.
- **4 Overman Act orders that also invoke other authority (B15X):** EO 3019-A, 3161, 3248-A and 3249. Each needs evidence that the other authority it invokes was spent. EO 3019-A also needs the treaty texts for its own "proclamation of peace" cap.
- **2 shipping fund delegations (B14X):** EO 3018 and 3064. The 1918 sections they also rest on must be read.
- **1 War Industries Board order (B16):** EO 2868. It needs the completion of the winding-up and the treaty texts.
- **6 members in B01 and B02.** Four are misclassified, with their families named. EO 4224's held text is another order's. EO 3087-A is a number with no order on record.

## (e) Held later-event edges

Twenty-nine family members carry held later-event edges in `jobs/pothier/output/MEMBERS.jsonl`. Most are cross-references (one order mentioning another), which are not acts. The engine flags a contradiction only when a held edge disagrees with a lead. It flags none, for these reasons.

Edges on `no` leads:

- **EO 3259:** a modification edge from EO 3265 (April 29, 1920). That edge is the evidence on which B03E rests.
- **EO 2664:** an extension edge from EO 3018 (December 3, 1918), which falls inside B14's interval.
- **EO 3091:** an amendment edge from EO 3222 (February 3, 1920). EO 3222 extends EO 3091 to the Panama Canal under the Overman Act alone, so it merges into EO 3091 and falls inside B15's interval.
- **EO 2679-A:** partial modification edges from EO 2694-A (September 2, 1917, "so far as it is inconsistent herewith"), which fall before the end.
- **EO 3233:** suspension and restoration edges from EO 3247 (March 19, 1920). EO 3247's words except EO 3233 ("except the Executive order of February 25, 1920"), so the edges misread it, and they fall before the stated end.

Edges on `open` leads:

- **EO 3923 (B18):** a revocation edge from PLO 369 (May 15, 1947), taken from BLM's table: "revoking EO Nos. 2247, 2658, and 3923; withdrawing lands for Agriculture experimental station". EO 2247 and 2658 are Alaska agricultural-experiment-station orders. The held EO 3923 is a Custodian sale of Stoehr & Sons shares and has no land to revoke. This is a number collision, so the edge does not decide this member. The PLO's "3923" should be traced in the census.
- **EO 4224 (B01):** a supersession edge from EO 5427 (August 20, 1930). EO 5427 supersedes "the Executive Order No. 4224½ of May 15, 1925", the visa-fee order whose text is held under this number, not the sale order.
- **EO 2645 (B99):** a supersession edge to EO 2687-A. It rests on a Wikisource editor's note, and EO 2687-A's text is not held.
- **EO 2729-A (B19):** revocation edges from EO 2801, 2837, 3016 and 3180. By their own words these reach only parts of EO 2729-A:
  - EO 2801 revokes paragraph XXX and substitutes a new one;
  - EO 2837 revokes one licensing power under section XI;
  - EO 3016 vests the President's section 12 powers in Frank L. Polk;
  - EO 3180 rescinds EO 2837.

  EO 2729-A also has amendment and supplementation edges (EO 2744, 2770, 2796, 2940, 4862). None ends the order as a whole.
- **EO 3016 (B19):** "amendment" edges from EO 3016F, P, Q, S, T and X. These are Polk's orders reciting EO 3016 as his authority; they exercise the delegation rather than amend it.
- **Others:** EO 2744 has an amendment edge from EO 3016, and EO 4001 one from EO 4045. EO 2604 has amendment edges from EO 2967 and 3030, which are decided under P2. EO 3249 has a cross-reference from EO 3283, which suspends one of its provisions until the Anthracite Coal Commission's work ends. EO 3017 has an amendment edge from EO 3800 that is spurious: EO 3800 concerns the Mount McKinley National Park and amends an order of January 13, 1922.

No held whole-order revocation names any member by number in words that reach that member, and no `no` lead rests on a `partial_` edge.

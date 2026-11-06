# PD-CLASS-EVENTS: orders ended by a class-wide event (NRA, Canal Zone, Philippines)

Doctrine version 1, 2026-11-05. Machine form: `PD-CLASS-EVENTS.json` (schema `pothier-family-doctrine/v1`). These are
status leads for the owner, not statuses. Certified count: 0.

## Conclusions

The family has 185 members that X1 typed `nra_code_approval` (95), `canal_zone` (82) and `philippines` (8). The
doctrine proposes a `no` lead (ended before the cutoff of October 14, 2026) for **91** members and leaves **94**
`open`. It proposes no `yes` lead: no member has a current-law predicate, and the class events all end orders rather
than keep them alive.

The X1 labels are much broader than their names. Almost none of the 95 "NRA code approvals" here approves a code (the
code approvals went through the 2026-10-29 NIRA sweep); they are NRA administrative orders, labor-board orders,
Reemployment Agreement orders, petroleum orders, public-works allotments and corporation charters. The Canal Zone
members are mostly the orders that failed Jacquard review (wave 1 lot L5, wave 2 lot L5R): Isthmian Canal Commission
appointments and salaries, general civil-service rules that mention the Isthmus, quarantine rules for the harbors of
Panama City and Colon, Panama Railroad employee rules, and truncated texts. Five of the eight Philippine members have
no Philippine subject at all. The branches are therefore defined by what the order's text does, not by its X1 type.

| Group | Members | `no` | `open` | Main basis for `no` |
|---|---:|---:|---:|---|
| NRA-typed | 95 | 61 | 34 | EO 7076 and NIRA sec. 2(c) as amended end every Title I order by April 1, 1936 |
| Canal Zone | 82 | 27 | 55 | appointments and amendments spent on issue; express revocations; end of the Canal Zone |
| Philippines | 8 | 3 | 5 | Philippine independence (July 4, 1946); an express rescission |
| **Total** | **185** | **91** | **94** | |

Branch counts from `python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-CLASS-EVENTS.json --hints`:
R1 2, R2 1, R3 1, N1 5, N2 3, N3 2, N4 1, N5 2, N6 45, N7 2, C1 17, C2 5, C3 3, P1 2 (all `no`); O1 34, O2 55,
Z9 5 (`open`). The engine flags 2 contradictions, both on branch C1 (EO 1320 and EO 577½): the appointee is named in
a later order. That is expected for an appointment that is spent on issue (the later order concerns the person, not
the appointing order), but a reviewer should look at the two later orders.

## (a) How members end

A **status lead** is the doctrine's proposal on one question: was the order as a whole still in force on
October 14, 2026? A `no` lead needs an ending basis that is the order's own terms (`TERM`) or a later instrument or
statute that by its terms reaches the order (`ACT`). An **accrued consequence** (an appointment made, money paid, a
penalty incurred) can outlive the order without keeping it in force. A **validity characterization** is a court's
holding that the authority for an order was unconstitutional; this doctrine records it but never uses it as an end
date, following the NIRA sweep's reviewed analysis (`research/excavator/claude-nira-sweep-2026-10-29/SHARED_ANALYSIS.md`).

**M1. Expiry of NIRA Title I (statute).** Section 2(c) of the National Industrial Recovery Act provided that Title I
"shall cease to be in effect and any agencies established hereunder shall cease to exist" two years after
enactment. Section 1 of S.J. Res. 113 (approved June 14, 1935) replaced that expiry with "on April 1, 1936". Title I
contains sections 1 to 10, including the code power (sec. 3), agreements and licenses (sec. 4), labor provisions
(sec. 7), the petroleum provision (sec. 9(c)) and the rule-making power (sec. 10); Title II (public works) begins at
section 201 and is not affected. The date is fixed: April 1, 1936 at the latest. June 16, 1935, the original expiry,
is not an end date, because the resolution moved it before it arrived.

**M2. EO 7076 (later instrument).** On June 15, 1935 the President ordered that "all existing Executive Orders
heretofore issued under and by virtue of the authority vested in me by Title I" be amended "so as to continue them in
effect and to extend their operation, and also to extend the authority and activities of any agency created
thereunder until April 1, 1936", subject to earlier limitation or cancellation and without any code-approval or
code-enforcement power. EO 7076 thus wrote an outer end date into every Title I order issued before June 15, 1935.
This is what lets M1 decide orders rather than merely remove their authority: the owner rule
(D-20261028-evidence-decides) says that repealing an order's authority does not by itself end the order, but EO 7076
names the whole class of Title I orders and fixes their period, and EO 7084 later describes a Title I board as
"continued by Executive Order No. 7076", which shows the government read it that way. Date rule: an interval from the
order's date to April 1, 1936.

**M3. Repeal of the code provisions (statute).** Section 2 of S.J. Res. 113 repealed "all the provisions of Title I
of such Act delegating power to the President to approve or prescribe codes of fair competition and providing for
the enforcement of such codes" on June 14, 1935. A command that worked only through a code (a code amendment, a stay,
a code authority appointment, a work assignment board under a textile code) ended that day. Because June 14, 1935
lies inside the M1/M2 interval, the doctrine does not use it as a separate date; it is stated so that the interval is
not misread as a claim that code commands lasted until 1936.

**M4. Schechter and Panama Refining (validity notes only).** *A. L. A. Schechter Poultry Corp. v. United States*,
295 U.S. 495 (May 27, 1935), held the section 3 code-making delegation "an unconstitutional delegation of legislative
power"; *Panama Refining Co. v. Ryan*, 293 U.S. 388 (January 7, 1935), held the same of section 9(c). Neither
judgment cancelled any order, and no branch dates an end by them.

**M5 to M7. Termination of named NRA bodies (later instruments).** EO 7075 (June 15, 1935) terminated the National
Industrial Recovery Board created by EO 6859. EO 6771 (June 30, 1934) ordered the National Recovery Review Board
discontinued "prior to July 1, 1934" and that it "shall cease to exist on that date". EO 7252 (December 21, 1935,
effective January 1, 1936) terminated "The National Recovery Administration and the office of Administrator
thereof" and required the divisions it moved to Commerce to end their functions by April 1, 1936. Each fixes the end
of an order whose operative content is the body it terminated.

**M8. Single act performed (own terms).** An order whose only command is a single act is spent when it issues: an
appointment or designation of named persons, a dismissal of a complaint, or an order that only amends or revokes
another order (the author brief states the last as an owner rule). The appointee's tenure, the dismissal's result
and the amended text are consequences or evidence for another order. Date: the order's date.

**M9. EO 7076's own period.** EO 7076's only command ran "until April 1, 1936".

**M10. Express revocation (later instrument).** A held later order that names the member and revokes or rescinds it:
EO 7234 (November 25, 1935) revoked EO 2040 and EO 3761; EO 6064 (March 3, 1933) rescinded EO 5143; EO 6344
(October 20, 1933) revoked EO 6223. The date is the acting order's date as printed in its held text. (The project's
edge records carry no date, so the doctrine names these members and dates explicitly.)

**M11. End of the Canal Zone (class event).** The Panama Canal Treaty of 1977 entered into force October 1, 1979. On
that date it terminated the 1903 Isthmian Canal Convention (art. I(1)); the Panama Canal Company and the Canal Zone
Government "shall cease to operate within the territory of the Republic of Panama" (art. III(10)); and Panama
reassumed "plenary jurisdiction over the former Canal Zone", with transition provisions for thirty calendar months
(art. XI(1)). The Panama Canal Act of 1979 took effect the same day (sec. 3304). It kept "the Canal Zone Code and
other laws, regulations, and administrative authority of the United States applicable in the Canal Zone" in force
only "for the purpose of the exercise by the United States of law enforcement and judicial jurisdiction during the
transition period" (sec. 2101), and it re-read "Canal Zone" in surviving laws and regulations as "the areas and
installations in the Republic of Panama made available to the United States" under the Treaty (sec. 3(b)). The
Treaty terminated "at noon, Panama time, December 31, 1999" (art. II(2)); 22 U.S.C. 3602(d) calls that day the
"Canal Transfer Date". After it no area answering to "Canal Zone" remained, so an order whose operative content
governs only the Zone had no object. The 1979 Act is therefore not by itself an end: it continued Zone rules for
limited purposes. The doctrine uses the outer bound, an interval from the order's date to December 31, 1999. Civil
government ended on October 1, 1979 and transition-period courts and police thirty months later, but those
narrower dates are not applied.

**M12. Philippine independence (class event).** Section 10(a) of the Philippine Independence Act of March 24, 1934
directed the President, on the July 4 after ten years of the Commonwealth, to "withdraw and surrender all right of
possession, supervision, jurisdiction, control, or sovereignty" over the Islands. Proclamation 2695 (July 4, 1946)
did so: "The United States of America hereby withdraws and surrenders" those rights. An order whose operative
content is United States supervision of the Islands' government has no object after that date. Earlier ends exist
(the Governor General's office ended with the Commonwealth's inauguration on November 15, 1935; the Bureau of
Insular Affairs moved to Interior in 1939), but their sources are not held, so the doctrine uses the interval from
the order's date to July 4, 1946. The Japanese occupation of 1942 to 1945 is not an end.

## (b) Primary sources

| Id | Source | Held? | Held path (sha256 of the held text) | Pin |
|---|---|---|---|---|
| S1 | NIRA, ch. 90, tit. I, sec. 2(c), 48 Stat. 195, 196 (1933) | held | `jobs/astra-source-retention/output/pages/c9fcb191.../selected-pages.txt` (56151e98...521c9) | "(c) This title shall cease to be in effect and any agencies established" |
| S2, S3 | S.J. Res. 113, Pub. Res. No. 26, 74th Cong., ch. 246, secs. 1-2, 49 Stat. 375 (June 14, 1935) | held | `jobs/astra-source-retention/output/pages/98e35c56.../selected-pages.txt` (0e3a91da...e3b60) | "of the National Industrial Recovery Act is amended by striking out"; "All the provisions of Title I of such Act delegating power" |
| S4 | EO 7076, June 15, 1935 | held (APP mirror) | `jobs/app-executive-orders/output/texts/executive-order-7076-extending-the-activities-the-nra.txt` (3bf1b52a...1eeb1169d) | "to extend the authority and activities of any agency created thereunder until April 1, 1936" |
| S5 | Schechter, 295 U.S. 495, 541-542 (1935) | held | `jobs/astra-source-retention/output/pages/88185924.../selected-pages.txt` (0aab4caf...e66f37) | "is an unconstitutional delegation of legislative power." |
| S6 | Panama Refining Co. v. Ryan, 293 U.S. 388 (1935) | acquire | https://www.govinfo.gov/content/pkg/USREPORTS-293/pdf/USREPORTS-293-388.pdf | validity note only |
| S7 | EO 7075, June 15, 1935, sec. 1 | held (APP mirror) | `jobs/app-executive-orders/output/texts/executive-order-7075-reorganizing-the-nra.txt` (e37e1c2d...919bd) | "is hereby terminated, and to provide for the continuing administration" |
| S8 | EO 6771, June 30, 1934 | held (APP mirror) | `jobs/app-executive-orders/output/texts/executive-order-6771-abolishing-the-national-recovery-review-board.txt` (b49b21ec...593c9d) | "it is hereby ordered that the said Board shall cease to exist on that date" |
| S9, S10 | EO 7252, Dec. 21, 1935, secs. 1 and 6 | held (APP mirror) | `jobs/app-executive-orders/output/texts/executive-order-7252-terminating-the-national-recovery-administration-and-transferring.txt` (d8eb6a71...a00f) | "...office of Administrator thereof are hereby terminated."; "This Order shall become effective on January 1, 1936." |
| S11 | EO 7234, Nov. 25, 1935, sec. 7 | held (APP mirror) | `jobs/app-executive-orders/output/texts/executive-order-7234-deposit-money-orders-issued-the-canal-zone-postal-service.txt` (3e63f165...cd6d3) | "No. 3761, of December 6, 1922, and No. 6608, of February 20, 1934, are hereby revoked" |
| S12 | EO 6064, Mar. 3, 1933 | held (APP mirror) | `jobs/app-executive-orders/output/texts/executive-order-6064-rescinding-the-executive-order-restricting-the-transportation.txt` (b7a1880d...0b3) | "Executive Order No. 5143, dated June 21, 1929" |
| S13 | EO 6344, Oct. 20, 1933 | held (APP mirror) | `jobs/app-executive-orders/output/texts/executive-order-6344-authorization-and-allocation-funds-for-purchase-lands-for-forest.txt` (e2d678f1...bcb12741) | "This order supersedes Executive Order No. 6223 of July 27, 1933, which is hereby revoked." |
| S14-S16 | Panama Canal Act of 1979, Pub. L. 96-70, secs. 2101, 3(b), 3304, 93 Stat. 452, 455, 493, 500; 22 U.S.C. 3831, 3602 | held | `jobs/source-ladder/output/texts/queue_EO_9293_..._93_Stat._452_instr_8d101fb40b.txt` (2128a639...10f) | "enters into force shall continue in force for the purpose of the exercise"; "(1) \"Canal Zone\" shall be deemed to refer to the areas and"; "Panama Canal Treaty of 1977 enters into force." |
| S17 | Panama Canal Treaty, Sept. 7, 1977, in force Oct. 1, 1979, 1280 U.N.T.S. No. 21086 | acquire | https://treaties.un.org/doc/Publication/UNTS/Volume%201280/volume-1280-I-21086-English.pdf | read on the web only |
| S18 | 22 U.S.C. 3602(d), added by Pub. L. 105-85, sec. 3512, 111 Stat. 2063 (1997) | acquire | https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title22-section3602&num=0&edition=prelim | read on the web only |
| S19 | Philippine Independence Act, ch. 84, sec. 10(a), 48 Stat. 456, 463 (1934) | held | `jobs/astra-source-retention/output/pages/2900efa1.../selected-pages.txt` (636fc717...6f70) | "withdraw and surrender all right of possession, supervision, juris-" |
| S20 | Proclamation 2695, July 4, 1946, 60 Stat. 1352 | held | `jobs/astra-source-retention/output/pages/c493d8ef.../selected-pages.txt` (5fdd7738...27c1) | "The United States of America hereby withdraws and surrenders" |

The JSON carries every full path and full sha256. Seventeen of the twenty sources are held and their pins were found
in the held text. Every EO used as an acting instrument (S4, S7 to S13) is held only as a mirror transcription from
the American Presidency Project, not as an authenticated original; for EO 7076, a Wikisource copy agrees. Section 10(a)
of the Philippine Independence Act is printed at 48 Stat. 463 and section 7(4) at 48 Stat. 461, as the running heads
of the held copy show.

## (c) Decision procedure

Branches are tried in order; the first whose conditions all hold decides. "Text" means the member's primary held
text (first 12,000 characters).

**R1-R3. Express revocations** (4 members, `no`, `ACT`). The member is EO 2040 or EO 3761 with a held revocation edge
(EO 7234, fixed date 1935-11-25); EO 5143 with a held rescission edge (EO 6064, 1933-03-03); or EO 6223 with a held
revocation edge (EO 6344, 1933-10-20). Gaps: the acting orders are mirror transcriptions; deposits or funds handled
before revocation are accrued consequences.

**N1. Section 3(e) complaint dismissals** (5, `no`, `TERM`, order date). NRA-typed text that recites "a complaint
under Section 3(e)" and directs "that no further action be taken with regard to said complaint" (or dismisses it).
The determination is performed on issue. Gap: a reviewer should confirm there is no second operative clause.

**N2. National Industrial Recovery Board orders** (EO 6859, 6993, 7025; `no`, `ACT`, fixed 1935-06-15). Each
creates, reconstitutes or fills the Board that EO 7075 section 1 terminated.

**N3. National Recovery Review Board orders** (EO 6632, 6637; `no`, `ACT`, interval to 1934-07-01). Each creates or
funds the Board that EO 6771 abolished.

**N4. EO 7076 itself** (`no`, `TERM`, fixed 1936-04-01). Gap: both held copies say the orders' period was limited to
"June 26, 1935", probably a transcription of June 16; immaterial to the end date.

**N5. EO 7075 and EO 7159** (`no`, `ACT`, interval to 1936-04-01). They create the office of Administrator and the
NRA divisions and appoint an Acting Administrator; EO 7252 terminated the NRA and the Administrator's office from
January 1, 1936 and required the divisions' functions to end by April 1, 1936, and NIRA sec. 2(c) as amended made
every Title I agency cease to exist that day. Gap: the Division of Review's work was taken up by a new committee
under the Emergency Relief Appropriation Act (EO 7323), a separate basis not traced here.

**N6. Title I orders issued before June 15, 1935 that cite no other statute** (45, `no`, `ACT`, interval from the
order's date to 1936-04-01). Conditions: NRA-typed; dated before 1935-06-15; text held; text names a Title I power
("title I", a "Code of Fair Competition", section 9(c) or its petroleum wording, the President's Reemployment
Agreement, section 2(b) or 10(a)); and text names none of Title II, a section 20x, Public No. 5 (March 31, 1933), the
Fourth Deficiency Act, the Agricultural Adjustment Act, the Federal Emergency Relief Act, an emergency appropriation
act, Public Resolution 44, the Reconstruction Finance Corporation, the Federal Trade Commission Act, a corporation
charter or the Bituminous Coal Conservation Act. Basis: EO 7076 limited every such order to April 1, 1936, and Title
I ended that day; code-dependent commands ended earlier, on June 14, 1935, and dismissals, denials, appointments and
amendments were exhausted on issue. This branch reaches the orders that Jacquard rejected from lot L4 as "not a code
or agreement approval": that rejection was right about the type, but the type was never the basis here. Agreements
under section 4(a) (the President's Reemployment Agreement and the interim agreements of July 1933), petroleum orders
under section 9(c), labor-board orders resting on Title I, delegations, rules and NRA staff orders all fall within
EO 7076's terms. Gaps: EO 7076 is held only as a mirror transcription; orders citing Title I "and otherwise" might
rest partly on unnamed general authority; the "no other statute" test is a text pattern.

**N7. Amendments of Title I orders** (EO 6612-A, EO 6836; `no`, `TERM`, order date). Text begins "Executive Order
No. ... is hereby amended" (or "Paragraph numbered ... of Executive Order No. ..."), with no Title II or
establishment wording. The amendment is spent on issue; the inserted text lives or dies with the amended order
(EO 6580 is on N6; EO 6770 is open).

**C1. Canal Zone appointments of named persons** (17, `no`, `TERM`, order date). Title begins "appointing", or the
WPA summary says a named person was "appointed" or "designated" as member, justice, chairman or judge; not a board,
regulation or civil-service order. The appointment is a single act; a stated term or fixed salary limits the
appointee's tenure, a consequence. Gaps: tenures are not traced (the Isthmian Canal Commission's discontinuance under
the Panama Canal Act of August 24, 1912 is not held); several designations are ProQuest scans whose identity a reader
must confirm.

**C2. Canal Zone orders that only amend or revoke another order** (5, `no`, `TERM`, order date). Title begins
"amending order" or "revoking order", or the summary says the order corrects a typographical error; not a
civil-service amendment; not an order that "revoked, and it is ordered" new content (EO 418, which re-fixes salaries,
is excluded).

**C3. Canal Zone government orders confined to the Zone, whole text read** (3: EO 1231, 1860, 2907; `no`, `ACT`,
interval to 1999-12-31). Text graded official or mirror transcription, contains "for the Canal Zone", "Canal Zone
Government", "courts of the Canal Zone" or "territory and waters of the Canal Zone", reaches a White House
signature within the window, and contains none of: a truncation marker, Panama Railroad, Panama City or Colon or the
Republic of Panama, civil service or Schedule A/B, compensation, salary, annuity, estates, a Washington office, an
appointment. Basis: M11. Gaps: the Treaty and 22 U.S.C. 3602(d) are not held; earlier ends are not dated.

**P1. Philippine government supervision** (EO 2456, EO 7447; `no`, `ACT`, interval to 1946-07-04). Philippine-typed
text naming the "Governor General of the Philippine Islands" or the "High Commissioner to the Commonwealth of the
Philippine Islands". Basis: M12. Gaps: EO 2456's held text is dated September 19, 1916 against a claimed September
16; EO 7447 also authorizes U.S. diplomats and consuls abroad to act on Commonwealth extradition requests, an
authority that existed only for the Commonwealth.

**O1, O2, Z9. Open** (34 NRA-typed, 55 Canal Zone, 5 Philippine-typed; `open`, basis `NONE`). See (d).

## (d) Members the procedure cannot decide (94)

**NRA-typed, 34 (O1).** (1) Orders resting wholly or partly on another statute: Title II public works and its
allotments (EO 6209, 6343, 6470, 6575-A, 6929, 6983, 7064), Public No. 5 and appropriation-act allotments (EO 6237,
6296-A, 6660, 6718, 6749), the Central Statistical Board under Titles I and II (EO 6225), the Executive Council and National Emergency Council resting on several recovery statutes (EO 6202-A, 6433-A,
6513, 6561, 6889-A), the Industrial Emergency Committee (EO 6770, 6860), Public Resolution 44 (EO 6858), the
Agricultural Adjustment Act (EO 6551), the Federal Trade Commission Act (EO 6569), the Special Adviser on Foreign
Trade (EO 6651), the Emergency Relief Appropriation Act of 1935 (EO 7120, 7323). (2) Corporation charters, whose
corporations outlived Title I: the Commodity Credit Corporation (EO 6340) and the Export-Import Banks (EO 6581, 6638;
the engine records a U.S. Code predicate lead, 12 U.S.C. 635 note). The order that authorized a corporation may be
spent on incorporation, but whether the corporation's later life rests on the order or on later statutes is not
decided here. (3) Orders after June 14, 1935
that EO 7076 does not reach: EO 7192 (a delegation to the Federal Trade Commission whose end would rest only on the
Title's expiry, the case the owner rule leaves open) and EO 7252 (whose section 3 moved the Consumers' Division to
Labor with no end date). (4) No held text: EO 6786-A, 7010-P. Several of these may be decided under PD-ADMIN's
fund-allotment and organization rules or with the statutes listed in `FETCH_PROPOSED.jsonl`.

**Canal Zone, 55 (O2).** The Jacquard failure reasons hold up on reading: general civil-service rules or schedules
that mention the Isthmus (EO 273, 274, 289, 370, 394, 946, 967, 1246, 1964, 4691, 4928, 7404, 7405; these belong to
PD-CS-RULES); quarantine and harbor rules reaching Panama City and Colon (EO 1761, 2020, 2118, 3255); Panama Railroad
employee or corporate matters and continuing individual rights (EO 1002, 1468, 1751, 1755, 1902, 2455, 2475, 3031,
5381); Commission organization, salary and Washington-office orders whose end needs the 1912 Act (EO 317-A, 335-A,
348-C, 418, 474, 527, 663, 664, 665, 680½, 725, 1897, 1944); truncated, scanned or mismatched texts (EO 1295, 1351,
1990, 2527, 2867, 3434, 3917, 3938, 4276, 6219); and orders whose subject is not Zone government (EO 1286 reaching
lands outside the Zone, 2185 renaming Culebra Cut, 2692 defensive sea areas, 3222 extending a general order, 3332
Hoboken piers, 3562 U.S. entry rules). A narrower branch could decide the truncated Zone regulations once full texts
are held, and the Commission orders once 37 Stat. 560 is held.

**Philippine-typed, 5 (Z9).** EO 2448 (foreign-built ship registry), EO 2877 (federal law officers, which excepts the
Philippines), EO 4102-A, 4102-B and 4572-A (Alien Property Custodian). Philippine independence does not reach them;
they belong to PD-WAR-EMERGENCY or PD-ADMIN.

## Decisions for the owner

1. Whether EO 7076, read with NIRA sec. 2(c) as amended, is an instrument that "by its terms reaches" each Title I
   order (branch N6, 45 members). The doctrine says yes, because EO 7076 amends the whole named class and fixes its
   period; the alternative reading (expiry of authority only) would move these 45 members to `open`.
2. Whether appointments of named persons are spent on issue (C1, 17 members), consistently with PD-CS-ONE-PERSON.
3. Whether the end of the Canal Zone may be dated by the outer bound of December 31, 1999 (C3) before the Treaty and
   22 U.S.C. 3602(d) are held; the engine already marks those leads with the missing sources.

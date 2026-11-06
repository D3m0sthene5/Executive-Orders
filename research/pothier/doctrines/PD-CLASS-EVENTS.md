# PD-CLASS-EVENTS: orders ended by a class-wide event (NRA, Canal Zone, Philippines)

Doctrine version 3, 2026-11-05. Machine form: `PD-CLASS-EVENTS.json` (schema `pothier-family-doctrine/v1`). It applies
the coordinator rulings in `research/pothier/COORDINATOR_RULINGS.md` (P1 to P8). These are status leads for the
owner, not statuses. Certified count: 0.

## Conclusions

The family has 185 members that X1 typed `nra_code_approval` (95), `canal_zone` (82) and `philippines` (8). The
doctrine proposes a `no` lead (ended before the cutoff of October 14, 2026) for **72** members and leaves **113**
`open`. It proposes no `yes` lead: no member has a current-law predicate, and the class events end orders rather than
keep them alive. The engine reports **0 contradictions** with held evidence: no `no` lead rests on a `partial_` edge,
and no member decided `no` has a held later edge or named-person hit dated after its lead's end.

The X1 labels are broader than their names. Almost none of the 95 "NRA code approvals" here approves a code (the code
approvals went through the 2026-10-29 NIRA sweep); they are NRA administrative orders, labor-board orders,
Reemployment Agreement orders, petroleum orders, public-works allotments and corporation charters. The Canal Zone
members are mostly the orders that failed Jacquard review (wave 1 lot L5, wave 2 lot L5R): Isthmian Canal Commission
appointments and salaries, general civil-service rules that mention the Isthmus, quarantine rules for the harbors of
Panama City and Colon, Panama Railroad employee rules, and long or scanned texts the machine cannot test. Five of the
eight Philippine members have no Philippine subject. The branches are therefore defined by what the order's text
does, not by its X1 type.

| Group | Members | `no` | `open` | Main basis for `no` |
|---|---:|---:|---:|---|
| NRA-typed | 95 | 56 | 39 | EO 7076, an express class instrument reaching every Title I order, limits them to April 1, 1936 |
| Canal Zone | 82 | 13 | 69 | express revocations by number or class; revoking and amending orders; end of the Canal Zone |
| Philippines | 8 | 3 | 5 | Philippine independence (July 4, 1946); an express rescission |
| **Total** | **185** | **72** | **113** | |

Branch counts from `python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-CLASS-EVENTS.json --hints`
(185 members; decides 72; contradicted 0), in the order the branches are tried:

| Branch | Members | Lead | Branch | Members | Lead |
|---|---:|---|---|---:|---|
| R1 | 2 | no | N7 | 1 | no |
| R2 | 1 | no | C1 | 16 | open |
| R3 | 1 | no | C2a | 1 | no |
| R4 | 1 | no | C2b | 3 | no |
| R5 | 1 | no | C3 | 3 | no |
| R6 | 1 | no | P1 | 2 | no |
| R7 | 1 | no | O1c | 1 | open |
| R8 | 1 | no | O1 | 27 | open |
| N1 | 5 | no | O2a | 12 | open |
| N2 | 2 | no | O2b | 6 | open |
| N3 | 2 | no | O2 | 35 | open |
| N4 | 1 | no | Z9a | 3 | open |
| N5 | 1 | no | Z9 | 2 | open |
| N5b | 1 | no | | | |
| O1a | 4 | open | | | |
| O1b | 7 | open | | | |
| N6 | 41 | no | | | |

Of the 113 open members, 50 are open because another family's rule governs them: one-person appointment and pay
orders follow PD-CS-ONE-PERSON (29: C1, O1b, O2b), civil-service rule orders follow PD-CS-RULES (12: O2a), fund
allotments and general administrative orders follow PD-ADMIN (6: O1a, Z9), and Alien Property Custodian orders
follow PD-WAR-EMERGENCY (3: Z9a).

## (a) How members end

A **status lead** is the doctrine's proposal on one question: was the order as a whole still in force on
October 14, 2026? A `no` lead needs an ending basis that is the order's own terms (`TERM`) or a later instrument or
statute whose words reach the order (`ACT`). Words reach an order when they name it by number or by its date and
subject, describe expressly a class that the order's own text, date or authority places it in (ruling P3), abolish
by name the one thing the order created or governed (ruling P7), or declare that the statutory powers the order only
delegates cease (ruling P8). A lapse or repeal of the authority to make orders, an "inconsistent herewith" clause, or
a statute occupying the field does not end an order by itself; such events are disclosed as candidate earlier ends.
An **accrued consequence** (an appointment made, money paid, a penalty incurred) can outlive the order without keeping
it in force. A **validity characterization** is a court's holding that the authority for an order was
unconstitutional; the doctrine records it but never uses it as an end date, following the reviewed NIRA sweep
analysis (`research/excavator/claude-nira-sweep-2026-10-29/SHARED_ANALYSIS.md`).

**M1. Expiry of NIRA Title I (statute).** Section 2(c) of the National Industrial Recovery Act provided that Title I
"shall cease to be in effect and any agencies established hereunder shall cease to exist" two years after
enactment. Section 1 of S.J. Res. 113 (approved June 14, 1935) replaced that expiry with "on April 1, 1936". Title I
contains sections 1 to 10, including the code power (sec. 3), agreements (sec. 4), labor provisions (sec. 7), the
petroleum provision (sec. 9(c)) and the rule-making power (sec. 10); Title II (public works) begins at section 201.
The lapse of Title I as an authority does not by itself end an order. The statute's words do end two kinds of member:
an order whose only content delegates Title I powers, which has nothing left to exercise once the Title's provisions
cease (ruling P8, mechanism M13), and an order whose only subject is an agency established under Title I (ruling
P7). Every other Title I order is reached through EO 7076 (M2). June 16, 1935, the original expiry, is not an end
date, because the resolution moved it before it arrived.

**M2. EO 7076, an express class instrument.** On June 15, 1935 the President ordered "that all existing Executive
Orders heretofore issued under and by virtue of the authority vested in me by Title I of the National Industrial
Recovery Act be, and they are, hereby amended so as to continue them in effect and to extend their operation, and
also to extend the authority and activities of any agency created thereunder until April 1, 1936", subject to "any
limitation, modification, or cancellation the President may hereafter make" and without any power "to approve or
prescribe codes of fair competition, to provide for the enforcement of such codes". Those words describe a class
(every existing order issued under Title I) and amend each member of it to run no later than April 1, 1936. A member
belongs to the class when its own authority clause places it under Title I alone and it is dated before June 15,
1935. Date rule: an interval from the order's date to April 1, 1936.

**M3. Repeal of the code provisions (disclosed candidate only).** Section 2 of S.J. Res. 113 repealed "all the
provisions of Title I of such Act delegating power to the President to approve or prescribe codes of fair
competition and providing for the enforcement of such codes" on June 14, 1935. That is a repeal of authority, so
under ruling P3 it is a disclosed earlier candidate end for code-dependent commands, not an end, and no branch dates a
lead by it.

**M4. Schechter and Panama Refining (validity notes only).** *A. L. A. Schechter Poultry Corp. v. United States*,
295 U.S. 495 (May 27, 1935), held the section 3 code-making delegation "an unconstitutional delegation of legislative
power"; *Panama Refining Co. v. Ryan*, 293 U.S. 388 (January 7, 1935), held the same of section 9(c). Neither
judgment cancelled any order, and no branch dates an end by them.

**M5 and M6. Boards abolished by name (ruling P7).** EO 7075 section 1 (June 15, 1935): "The National Industrial
Recovery Board created by Executive Order No. 6859 of September 27, 1934, is hereby terminated." That Board is the
only subject of EO 6859, which created it, and of EO 6993, which "reconstitute[s] the National Industrial Recovery
Board created by Executive Order no. 6859". EO 6771 (June 30, 1934) identifies the National Recovery Review Board as
established "by Executive Order of March 7, 1934" (EO 6632), orders it discontinued "prior to July 1, 1934" and
"that the said Board shall cease to exist on that date". EO 6771's own only command is that abolition.

**M7. Termination of the NRA (later instrument).** EO 7252 (December 21, 1935, effective January 1, 1936): section 1
terminated "The National Recovery Administration and the office of Administrator thereof"; section 2 transferred
"The Division of Review, the Division of Business Cooperation, and the Advisory Council, as constituted by Executive
Order No. 7075 of June 15, 1935" to Commerce and directed the Secretary "to terminate the functions and duties of the
said agencies not later than April 1, 1936".

**M8. Single act on issue (own terms).** An order whose only operative content revokes another order, or dismisses a
complaint, does one thing when it issues and is spent (ruling P1; lead kind `spent_on_issue`). An order whose only
operative content amends other orders merges into the parents on issue (ruling P2, owner decision
D-20261021-strike-and-insert; lead kind `merged_into_parent_on_issue`), and every such lead carries the disclosure:
its text continues as part of the parent until the parent ends; the parent's lifecycle carries it. If the owner
prefers to treat an amending order as living as long as the amended text lives, those leads become `open` pending
the parent. An order whose operative content is one act for one named person follows PD-CS-ONE-PERSON instead
(ruling P4), even when it is an amendment in form (EO 595, EO 6836).

**M9. EO 7076 as an amending order.** EO 7076's only operative content amends the existing Title I orders, so under
ruling P2 it merged into them on issue (June 15, 1935); its extension to April 1, 1936 lives and ends with them.

**M10. Express revocation by number, by date and subject, or by class.** A held later order names the member and
revokes, rescinds, repeals or supersedes it:

- EO 7234 (November 25, 1935), sec. 7: "Executive Orders No. 2040, of September 5, 1914, ... No. 3761, of December 6,
  1922, and No. 6608, of February 20, 1934, are hereby revoked."
- EO 6064 (March 3, 1933): "Executive Order No. 5143, dated June 21, 1929, ... hereby is rescinded."
- EO 6344 (October 20, 1933): "This order supersedes Executive Order No. 6223 of July 27, 1933, which is hereby
  revoked."
- EO 6575 (January 24, 1934): "Executive Order No. 6237, of July 28, 1933, ... be, and it is hereby, revoked."
- EO 4006 (May 7, 1924): "The Executive Order No. 3985, dated April 3, 1924, ... is hereby rescinded".
- EO 2907 (July 9, 1918): "This order supersedes Executive Order Number 2867 dated May 28, 1918."
- EO 393 (January 12, 1906): "Executive Order of November 15, 1905, as to appointments to positions in the service of
  the Isthmian Canal Commission upon the Isthmus of Panama, is hereby repealed." EO 370 is that order (its date and
  subject).
- EO 3027 (January 25, 1919), an express class revocation (ruling P3): "All Executive Orders heretofore issued for the
  establishment of Defensive Sea Areas are hereby revoked." EO 2692's own title and text, "Establishing Defensive Sea
  Areas for Terminal Ports of the Panama Canal", place it in that class.

The date is the acting order's date as printed in its held text; the engine's edge records give the same dates.

**M11. End of the Canal Zone (ruling P5).** The Panama Canal Treaty of 1977 entered into force October 1, 1979. It
terminated the 1903 Isthmian Canal Convention (art. I(1)); the Canal Zone Government ceased to operate "within the
territory of the Republic of Panama" (art. III(10)); Panama reassumed "plenary jurisdiction over the former Canal
Zone", with transition provisions for thirty calendar months (art. XI(1)). The Panama Canal Act of 1979, effective
the same day (sec. 3304), did not end Zone rules. It continued them "for the purpose of the exercise by the United
States of law enforcement and judicial jurisdiction during the transition period" (sec. 2101), and, subject to
subsection (c), provided that "'Canal Zone' shall be deemed to refer to the areas and installations in the Republic of
Panama made available to the United States pursuant to the Panama Canal Treaty of 1977 and related agreements"
(sec. 3(b)). The end therefore rests on the Treaty: "This Treaty shall terminate at noon, Panama time, December 31,
1999" (art. II(2)); 22 U.S.C. 3602(d) calls that day the "Canal Transfer Date". After it no area answering to "Canal
Zone" remained. Under ruling P5 that termination is the latest bound for Canal Zone orders, and the lead is the
interval (order date, 1999-12-31]. The Treaty and 22 U.S.C. 3602(d) are not yet held. Civil government ended on
October 1, 1979 and transition-period courts and police thirty months later; those are disclosed earlier candidates,
not applied.

**M12. Philippine independence (ruling P5).** Section 10(a) of the Philippine Independence Act of March 24, 1934
(48 Stat. 456, 463) directed the President to "withdraw and surrender all right of possession, supervision,
jurisdiction, control, or sovereignty then existing and exercised by the United States in and over the territory
and people of the Philippine Islands, including all military and other reservations of the Government of the United
States in the Philippines (except such naval reservations and fueling stations as are reserved under section 5)".
Proclamation 2695 (July 4, 1946, 60 Stat. 1352, 1353), acting "in accord with and subject to the reservations
provided for in the applicable statutes", declared: "The United States of America hereby withdraws and surrenders all
rights of possession, supervision, jurisdiction, control, or sovereignty now existing and exercised by the United
States of America in and over the territory and people of the Philippines". Those words describe a class, every
right of United States supervision, jurisdiction or control over the Islands, and an order whose operative content is
such supervision falls in it. The excepted reservations are not reached by M12 and no member here concerns them.
Section 7 of the Act, which governs the Commonwealth period and under which the High Commissioner served, opens
"Until the final and complete withdrawal of American sovereignty". The date the instrument fixes is July 4, 1946.
Earlier ends exist (the Governor General's office ended with the Commonwealth's inauguration on November 15, 1935; the
Bureau of Insular Affairs moved to Interior in 1939), but their sources are not held, so the lead is the interval
(order date, 1946-07-04]. The Japanese occupation of 1942 to 1945 is not an end.

**M13. Delegation of a statutory power that ceased (ruling P8).** When a member's only content delegates powers that
Title I conferred, NIRA sec. 2(c) as amended ("This title shall cease to be in effect ... on April 1, 1936") leaves
the delegation nothing to exercise after that date. This differs from a repeal of the authority to make new orders,
after which existing orders keep effect of their own.

## (b) Primary sources

| Id | Source | Held? | Held path (sha256 of the held text) | Pin |
|---|---|---|---|---|
| S0 | The member's own order text (ruling P6) | member text | recorded per lead by the engine | the member's operative words |
| S1 | NIRA, ch. 90, tit. I, sec. 2(c), 48 Stat. 195, 196 (1933) | held | `jobs/astra-source-retention/output/pages/c9fcb191.../selected-pages.txt` (56151e98...79521c9) | "(c) This title shall cease to be in effect and any agencies established" |
| S2, S3 | S.J. Res. 113, Pub. Res. No. 26, 74th Cong., ch. 246, secs. 1-2, 49 Stat. 375 (June 14, 1935) | held | `jobs/astra-source-retention/output/pages/98e35c56.../selected-pages.txt` (0e3a91da...e3b60) | "of the National Industrial Recovery Act is amended by striking out"; "All the provisions of Title I of such Act delegating power" |
| S4 | EO 7076, June 15, 1935 | held (APP mirror) | `jobs/app-executive-orders/output/texts/executive-order-7076-extending-the-activities-the-nra.txt` (3bf1b52a...aeeb1169d) | "to extend the authority and activities of any agency created thereunder until April 1, 1936" |
| S5 | Schechter, 295 U.S. 495, 541-542 (1935) | held | `jobs/astra-source-retention/output/pages/88185924.../selected-pages.txt` (0aab4caf...e66f37) | "is an unconstitutional delegation of legislative power." |
| S6 | Panama Refining Co. v. Ryan, 293 U.S. 388 (1935) | acquire | https://www.govinfo.gov/content/pkg/USREPORTS-293/pdf/USREPORTS-293-388.pdf | validity note only |
| S7 | EO 7075, June 15, 1935, sec. 1 | held (APP mirror, abridged) | `jobs/app-executive-orders/output/texts/executive-order-7075-reorganizing-the-nra.txt` (e37e1c2d...bd919bd) | "is hereby terminated, and to provide for the continuing administration" |
| S8 | EO 6771, June 30, 1934 | held (APP mirror) | `jobs/app-executive-orders/output/texts/executive-order-6771-abolishing-the-national-recovery-review-board.txt` (b49b21ec...593c9d) | "it is hereby ordered that the said Board shall cease to exist on that date" |
| S9, S10 | EO 7252, Dec. 21, 1935, secs. 1, 2 and 6 | held (APP mirror) | `jobs/app-executive-orders/output/texts/executive-order-7252-terminating-the-national-recovery-administration-and-transferring.txt` (d8eb6a71...73da00f) | "...office of Administrator thereof are hereby terminated."; "This Order shall become effective on January 1, 1936." |
| S11 | EO 7234, Nov. 25, 1935, sec. 7 | held (APP mirror) | `jobs/app-executive-orders/output/texts/executive-order-7234-deposit-money-orders-issued-the-canal-zone-postal-service.txt` (3e63f165...bcd6d3) | "No. 3761, of December 6, 1922, and No. 6608, of February 20, 1934, are hereby revoked" |
| S12 | EO 6064, Mar. 3, 1933 | held (APP mirror) | `jobs/app-executive-orders/output/texts/executive-order-6064-rescinding-the-executive-order-restricting-the-transportation.txt` (b7a1880d...683fc0b3) | "Executive Order No. 5143, dated June 21, 1929" |
| S13 | EO 6344, Oct. 20, 1933 | held (APP mirror) | `jobs/app-executive-orders/output/texts/executive-order-6344-authorization-and-allocation-funds-for-purchase-lands-for-forest.txt` (e2d678f1...bcb12741) | "This order supersedes Executive Order No. 6223 of July 27, 1933, which is hereby revoked." |
| S14-S16 | Panama Canal Act of 1979, Pub. L. 96-70, secs. 2101, 3(b), 3304, 93 Stat. 452, 455, 493, 500; 22 U.S.C. 3831, 3602 | held | `jobs/source-ladder/output/texts/queue_EO_9293_..._93_Stat._452_instr_8d101fb40b.txt` (2128a639...e10f) | "enters into force shall continue in force for the purpose of the exercise"; "(1) \"Canal Zone\" shall be deemed to refer to the areas and"; "Panama Canal Treaty of 1977 enters into force." |
| S17 | Panama Canal Treaty, Sept. 7, 1977, in force Oct. 1, 1979, 1280 U.N.T.S. No. 21086 | not yet held; acquire | https://treaties.un.org/doc/Publication/UNTS/Volume%201280/volume-1280-I-21086-English.pdf | read on the web only |
| S18 | 22 U.S.C. 3602(d), added by Pub. L. 105-85, sec. 3512, 111 Stat. 2063 (1997) | not yet held; acquire | https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title22-section3602&num=0&edition=prelim | read on the web only |
| S19 | Philippine Independence Act, ch. 84, secs. 7, 10(a), 48 Stat. 456, 461, 463 (1934) | held | `jobs/astra-source-retention/output/pages/2900efa1.../selected-pages.txt` (636fc717...6f70) | "withdraw and surrender all right of possession, supervision, juris-" |
| S20 | Proclamation 2695, July 4, 1946, 60 Stat. 1352, 1353 | held | `jobs/astra-source-retention/output/pages/c493d8ef.../selected-pages.txt` (5fdd7738...27c1) | "The United States of America hereby withdraws and surrenders" |
| S21 | EO 6575, Jan. 24, 1934 (revoking EO 6237) | held (APP mirror; Hathi copy agrees) | `jobs/app-executive-orders/output/texts/executive-order-6575-revocation-executive-order-no-6237-july-28-1933.txt` (c12de946...6e0e8b9) | "be, and it is hereby, revoked." |
| S22 | EO 4006, May 7, 1924 | held (ProQuest scan text) | `jobs/pinakes-proquest-ingest/output/texts/EO_4006.txt` (ed86bf79...fae6bd72) | "is hereby rescinded" |
| S23 | EO 2907, July 9, 1918 | held (Wikisource) | `jobs/wikisource-texts/output/texts/EO_2907.txt` (90b60943...755a923b) | "This order supersedes Executive Order Number 2867 dated May 28, 1918." |
| S24 | EO 393, Jan. 12, 1906 | held (1911 GPO compilation OCR; Wikisource copy agrees) | `jobs/isthmian-canal-1911/output/texts/EO_393.txt` (ce7758a2...278fbbe4a) | "is hereby repealed." |
| S25 | EO 3027, Jan. 25, 1919 | held (Wikisource) | `jobs/wikisource-texts/output/texts/EO_3027.txt` (0bc00bca...61dda0433e) | "All Executive Orders heretofore issued for the establishment of Defensive Sea Areas are hereby revoked." |
| S26 | EO 7084, June 24, 1935 | held (APP mirror) | `jobs/app-executive-orders/output/texts/executive-order-7084-continuing-the-textile-labor-relations-board-until-july-1-1935.txt` (197db25f...4d434792) | "continued by Executive Order No. 7076" |

The JSON carries every full path and full sha256. Twenty-three of the twenty-six external sources are held and their
pins were found in the held text; S6, S17 and S18 are to be acquired
(`research/pothier/work/PD-CLASS-EVENTS/FETCH_PROPOSED.jsonl`). Every executive order used as an acting instrument
(S4, S7 to S13, S21 to S26) is held only as a transcription (APP, Wikisource, ProQuest scan OCR or the OCR of the
1911 GPO compilation), not as an authenticated original. Section 10(a) of the Philippine Independence Act is printed
at 48 Stat. 463 and section 7 at 48 Stat. 461, as the running heads of the held copy show.

## (c) Decision procedure

Branches are tried in order; the first whose conditions all hold decides. "Text" means the member's primary held
text (first 12,000 characters, the window the engine reads).

**R1-R7. Express revocation by number, or by date and subject** (8, `no`, `ACT`, fixed date of the acting order).
Each names explicit members and requires the matching held edge: R1 EO 2040 and 3761 (EO 7234, 1935-11-25); R2 EO 5143
(EO 6064, 1933-03-03); R3 EO 6223 (EO 6344, 1933-10-20); R4 EO 6237 (EO 6575, 1934-01-24); R5 EO 3985 (EO 4006,
1924-05-07); R6 EO 2867 (EO 2907, 1918-07-09, lead kind `superseded_by_named_order`); R7 EO 370 (EO 393, 1906-01-12).
Every edge is a whole-order act; none is `partial_`. Gaps: the acting texts are transcriptions; deposits, funds or
appointments handled before revocation are accrued consequences; EO 370's identity rests on its date and subject; if
the owner does not accept a supersession without the word "revoked" as an end, R6 is `open`.

**R8. EO 2692, revoked as a class by EO 3027** (`no`, `ACT`, `ended_by_express_class_instrument`, fixed
1919-01-25). Member test: held revocation edge by EO 3027 and the words "Defensive Sea Areas" in the member's text.
Gap: EO 3027 is held only as a Wikisource transcription.

**N1. Section 3(e) complaint dismissals** (5, `no`, `TERM`, `spent_on_issue`, order date). NRA-typed text that
recites "a complaint under Section 3(e)" and directs "that no further action be taken with regard to said complaint"
(or dismisses it). The determination is performed on issue. Gap: a reviewer should confirm there is no second
operative clause.

**N2. EO 6859 and EO 6993** (`no`, `ACT`, `ended_by_express_abolition_of_its_subject`, fixed 1935-06-15). Their only
subject is the National Industrial Recovery Board, which EO 7075 section 1 terminated by name (M5). The appointments
of named members are consequences.

**N3. EO 6632 and EO 6771** (`no`, `ACT`, `ended_by_express_abolition_of_its_subject`, fixed 1934-07-01). EO 6632's
only subject is the National Recovery Review Board; EO 6771's only command abolishes it; the Board ceased to exist
July 1, 1934 (M6).

**N4. EO 7076** (`no`, `TERM`, `merged_into_parent_on_issue`, order date 1935-06-15). Its only operative content
amends the existing Title I orders (M9). Disclosure: its text continues as part of the parent until the parent ends;
the parent's lifecycle carries it. Gap: both held copies recite that the orders' period was limited to "June 26,
1935", probably a transcription of June 16; immaterial.

**N5. EO 7075** (`no`, `ACT`, `ended_by_express_abolition_of_its_subject`, interval [1936-01-01, 1936-04-01]). Its
operative content is the NRA's administration under Title I as amended: it terminates the old Board (spent on issue),
creates the office of Administrator, the Division of Review, the Division of Business Cooperation and the Advisory
Council, and appoints their heads (consequences). EO 7252 section 1 terminated the office of Administrator from
January 1, 1936, and section 2 names EO 7075 and requires the functions of the divisions and the Council it
constituted to end "not later than April 1, 1936"; NIRA sec. 2(c) as amended ends every agency established under
Title I on April 1, 1936 (M7, ruling P7). Gap: the held EO 7075 text is an abridged APP transcription ("..." in
sections 2 and 5, no section 6), so "only operative content" was checked on an incomplete text.

**N5b. EO 7192** (`no`, `ACT`, `ended_with_delegated_statutory_power`, fixed 1936-04-01). Its only content delegates
to the Federal Trade Commission authority under "section 2(a) and section 2(b) of Title I", which its own text says
were "extended until April 1, 1936" (M13, ruling P8).

**O1a. NRA fund allotments** (4: EO 6296-A, 6637, 6718, 6749; `open`). Fund allotment; follows PD-ADMIN's
fund-allotment rule. EO 6637's allotment went to the National Recovery Review Board, which ceased July 1, 1934 (a
disclosed bound).

**O1b. NRA named-person orders** (7: EO 6298, 6537, 6538, 6731-A, 6836, 7025, 7159; `open`). One-person order;
follows PD-CS-ONE-PERSON (ruling P4). Disclosed bounds, not applied: EO 7076 limited every Title I order issued before
June 15, 1935 to April 1, 1936; the codes under which EO 6298, 6537, 6538 and 6731-A appointments were made lost their
enforcement provisions on June 14, 1935; EO 7252 terminated the office EO 7159 filled from January 1, 1936; EO 6836
is an amendment of EO 6770 whose only content appoints Donald R. Richberg and fixes his leave "until October 1,
1934".

**N6. Title I orders issued before June 15, 1935** (41, `no`, `ACT`, `ended_by_express_class_instrument`, interval
(order date, 1936-04-01]). Member test: NRA-typed; dated before 1935-06-15; text held; text names a Title I power
("title I", a "Code of Fair Competition", section 9(c) or its petroleum wording, the President's Reemployment
Agreement, section 2(b) or 10(a)); the authority clause (the 350 characters after "authority vested in me" or
"powers conferred on me") names none of Title II, a section 20x, Public No. 5 (March 31, 1933), the Fourth Deficiency
Act, the Agricultural Adjustment Act, the Federal Emergency Relief Act, an emergency appropriation act, Public
Resolution 44, the Reconstruction Finance Corporation, the Federal Trade Commission Act, the District of Columbia
Code or the Bituminous Coal Conservation Act; the authority does not refer back to "the aforesaid legislation" or
"statutes aforesaid"; and the order does not charter a corporation ("an agency, to wit: a corporation") or allocate or
allot funds. A mention of another statute in a recital or descriptive clause does not exclude a member (EO 6551
mentions the Agricultural Adjustment Act only to describe what the Secretary of Agriculture may do under it). The
member is then one of "all existing Executive Orders heretofore issued under and by virtue of the authority vested in
me by Title I", which EO 7076 amended to run "until April 1, 1936". Disclosed earlier candidates: the June 14, 1935
repeal of the code provisions for code-dependent commands; exhaustion on issue for denials of exemption. The branch
reaches the orders Jacquard rejected from lot L4 as "not a code or agreement approval": that rejection was right
about the type, and the type is not the basis here. Section 4(a) agreements (the President's Reemployment Agreement
and the interim agreements of July 1933), petroleum orders under section 9(c), labor-board orders resting on Title I,
delegations, rules and NRA staff orders all fall within EO 7076's words. Gaps: EO 7076 is held only as a mirror
transcription; orders citing Title I "and otherwise" may rest partly on unnamed general authority; the
authority-clause test is a text pattern.

**N7. EO 6612-A** (`no`, `TERM`, `merged_into_parent_on_issue`, order date). Its only content amends EO 6580 (N6) and
acts for no named person. Disclosure: its text continues as part of the parent until the parent ends; the parent's
lifecycle carries it.

**C1. Canal Zone appointments and designations of named persons** (16, `open`). Title begins "appointing", or the WPA
summary says a named person was "appointed" or "designated" as member, justice, chairman or judge. One-person order;
follows PD-CS-ONE-PERSON (ruling P4): the appointment is spent when the person takes office and the tenure is a
surviving consequence. PD-CS-ONE-PERSON selects its members by other X1 types, so its rule does not yet reach these
orders. Disclosed own-terms ends, not applied: EO 4087 designates James W. Blackburn special judge "until Jan. 1,
1926", EO 4567 "until Jan. 1, 1928", EO 4767 "until Jan. 1, 1929" (WPA summaries).
EO 4006 also rescinds EO 3985 (R5). EO 1320 and EO 577½ name persons who appear in later orders.

**C2a. EO 673** (`no`, `TERM`, `spent_on_issue`, order date). Title begins "revoking order", text says "is hereby
revoked", and revoking EO 649's transfer of George S. Fox is its only content.

**C2b. Canal Zone orders that only amend another order and act for no named person** (EO 373-A, 412, 2737; `no`,
`TERM`, `merged_into_parent_on_issue`, order date). Disclosure: its text continues as part of the parent until the
parent ends; the parent's lifecycle carries it. Parents: EO 348-C (open, O2b) for EO 373-A and EO 412, which re-word
the allowance of "each member" of the Board of Consulting Engineers; EO 2692 (R8, revoked 1919-01-25) for EO 2737.

**C3. Canal Zone government orders confined to the Zone, whole text read** (EO 1231, 1860, 2907; `no`, `ACT`,
interval (order date, 1999-12-31]). Text graded official or mirror transcription, contains "for the Canal Zone",
"Canal Zone Government", "courts of the Canal Zone" or "territory and waters of the Canal Zone", reaches a White
House signature within the window, and contains none of: Panama Railroad, Panama City or Colon or the Republic of
Panama, civil service or Schedule A/B, compensation, salary, annuity, estates, a Washington office, an appointment.
Basis: ruling P5 and Treaty art. II(2) (M11); the 1979 Act only confines these rules within the Treaty's life. Gaps:
the 1977 Treaty and 22 U.S.C. 3602(d) are not yet held and should be acquired before these leads are adopted; EO 2907
delegates Espionage Act title II sec. 1 powers that depend on a declared national emergency, and Panama Canal Act
sec. 3302(a) struck the Canal Zone paragraph of 50 U.S.C. 191; both are disclosed earlier candidates.

**P1. EO 2456 and EO 7447** (`no`, `ACT`, `ended_by_express_class_instrument`, interval (order date, 1946-07-04]).
Philippine-typed text naming the "Governor General of the Philippine Islands" or the "High Commissioner to the
Commonwealth of the Philippine Islands". EO 2456 places "all matters pertaining to the Government of the Philippine
Islands" under the War Department and directs the Governor General's reports there; EO 7447 delegates to the High
Commissioner the Commonwealth's extradition business. Both are United States supervision of the Islands, surrendered
in the words quoted under M12. Gaps: EO 2456's held text is dated September 19, 1916 against a claimed September 16;
EO 7447 also authorizes U.S. diplomats and consuls abroad to act on Commonwealth extradition requests, an authority
that existed only for the Commonwealth.

**O1c, O1, O2a, O2b, O2, Z9a, Z9. Open** (`open`, basis `NONE`). See (d).

## (d) Members the procedure cannot decide (113)

**Members of other families (50).**
- One-person appointment and pay orders follow PD-CS-ONE-PERSON (ruling P4): the 16 Canal Zone appointments (C1), the
  7 NRA named-person orders (O1b), and the 6 Canal Zone pay orders for named persons (O2b: EO 335-A, 348-C, 418, 474,
  595, 680½), whose end also needs the Panama Canal Act of 1912 (37 Stat. 560, not held). For EO 418, EO 474 says "All
  orders in conflict herewith are revoked" (implied displacement under P3, disclosed only).
- Civil Service Rules orders typed Canal Zone follow PD-CS-RULES (O2a, 12: EO 273, 274, 289, 394, 946, 967, 1246,
  1964, 4691, 4928, 7404, 7405). They amend or apply the general rules, which operate beyond the Zone.
- NRA-typed fund allotments follow PD-ADMIN (O1a, 4: EO 6296-A, 6637, 6718, 6749).
- Philippine-typed orders with no Philippine subject: the Alien Property Custodian orders EO 4102-A, 4102-B and
  4572-A follow PD-WAR-EMERGENCY (Z9a); EO 2448 (foreign-built ship registry) and EO 2877 (federal law officers,
  which excepts the Philippines) follow PD-ADMIN (Z9).

**EO 6858 (O1c).** Its authority clause cites Title I and "joint resolution approved June 19, 1934 (Public Resolution
44)". EO 7084 (June 24, 1935) names it: "The Textile Labor Relations Board created under Executive Order No. 6858 of
September 26, 1934, and continued by Executive Order No. 7076 of June 15, 1935, is hereby further continued in
existence until July 1, 1935". That limit is disclosed; later extensions of the Board and Public Resolution 44's own
period (48 Stat. 1183, not held) are not traced.

**NRA-typed orders resting on other authority or not reached (27, O1).** Title II public works (EO 6209, 6343, 6470,
6575-A, 6929, 6983, 7064); the Central Statistical Board under Titles I and II (EO 6225, 6700); the Executive Council
and National Emergency Council resting on several recovery statutes (EO 6202-A, 6433-A, 6513, 6561, 6889-A); the
Industrial Emergency Committee (EO 6770, 6860); the Fourth Deficiency Act (EO 6660); the Federal Trade Commission Act
(EO 6569); the Special Adviser on Foreign Trade (EO 6651), whose Title I authority clause is joined by a second
operative clause allocating $100,000 "from the appropriation of $3,300,000,000 authorized by section 220 of the
National Industrial Recovery Act and made by the Fourth Deficiency Act", a Title II appropriation; the Emergency Relief
Appropriation Act of 1935 (EO 7120, 7323); corporation charters whose corporations outlived Title I (the Commodity
Credit Corporation, EO 6340; the Export-Import Banks, EO 6581, 6638, for which the engine records a U.S. Code predicate
lead, 12 U.S.C. 635 note); EO 7252, whose section 3 moved the Consumers' Division to Labor with no end date; and two
orders with no held text (EO 6786-A, 7010-P).

**Canal Zone orders not decided (35, O2).** Every held text is complete; the reasons are the order's reach or the
limits of the machine test:
- Content reaching outside the Zone: quarantine and harbor rules for Panama City and Colon (EO 1761, 2020, 2118,
  3255); safety-appliance rules covering other government railroads (EO 1002); a land office reaching lands outside
  the Zone (EO 1286); deeds and estates reaching Colon and the Republic of Panama (EO 1295, 1468, 1751); U.S. entry
  rules (EO 3562); Hoboken piers (EO 3332).
- Panama Railroad employee or corporate matters and continuing individual rights: EO 1755, 1902, 2455, 2475, 3031,
  5381.
- Isthmian Canal Commission organization and Washington offices, whose end needs the 1912 Act: EO 317-A, 527, 663,
  664, 665, 725, 1897, 1944.
- Not testable by C3: texts longer than the 12,000-character window (EO 1351, 1990, 3434, 3938, 4276, 6219; EO 6219
  also contains "Republic of Panama" and "appoint"); ProQuest scan texts, which C3 does not accept by grade (EO 2527,
  3917, 3938, 4276).
- Subject not Zone government alone: EO 2185 (renaming Culebra Cut), EO 3222 (amending a general order, EO 3091,
  on Navy vessel transfers, which is not a member), EO 3917 (a one-time transfer of buildings, which EO 6072 later re-transferred by reference to
  it).

Full official texts and a wider window would let C3 test the long Zone regulations, and 37 Stat. 560 would date the
Commission orders.

## Choices left to the owner

1. Ruling P2's alternative: if an amending order is treated as living as long as the amended text lives, N4 (EO 7076),
   N7 (EO 6612-A) and C2b (3) become `open` pending their parents.
2. R6 (EO 2867) rests on a supersession by number without the word "revoked".
3. C3 (3) rests on the 1977 Treaty and 22 U.S.C. 3602(d), which are not yet held; the engine marks those leads with
   the missing sources.

# PD-MILITARY-RESERVATION: military and naval reservations (316 members)

Doctrine version 3, 2026-11-06. Machine form: `research/pothier/doctrines/PD-MILITARY-RESERVATION.json`
(schema `pothier-family-doctrine/v1`). Every result below is a status lead proposed to the owner, not a status. The
doctrine applies the coordinator rulings in `research/pothier/COORDINATOR_RULINGS.md` (P1, P2, P3, P5, P6); no
lead rests on P4, P7 or P8.

## Conclusions

The family holds the 316 orders that X1 typed `military_naval_reservation`, dated 1903 to 1936. An executive order
in this family reserves public land for the War or Navy Department (a "reservation": land set apart for a named
federal use and closed to settlement and sale), enlarges, redefines or transfers such a reservation, or gives the
land back. Sixteen members are not land orders at all (fifteen hours, civil-service and wartime orders, and the
Klawak education reservation in Alaska). No member concerns a naval petroleum or oil-shale reserve.

The doctrine decides 164 members as `no` (ended before the cutoff of 2026-10-14), decides none as `yes`, and leaves
152 `open`. The 164 `no` leads rest on these bases:

- **38 members** were revoked, vacated, rescinded, superseded, abolished or relinquished in full by a later
  executive order whose text the project holds and whose words name the member by number or date (branches C01 to
  C32). Each lead cites the later order's held text and a phrase in it, and takes that order's date.
- **23 members** were revoked in full by a Public Land Order (the Interior Department's instrument for withdrawals
  and revocations after 1942) that names the member by number or date in the Bureau of Land Management's official
  Table of Public Land Orders, which the project holds (branches P01 to P22). The PLO texts are not held, so each
  lead carries that gap. Each lead takes the PLO's signature date (for EO 3574, an interval; see below).
- **60 members** only revoke, restore or relinquish (branches B09, B10, B11, B11x). Such an order does one thing and
  does it on issue: it is "spent on issue" (ruling P1), and its effect is evidence about the reservation it acted on.
  The date is the order's date (for EO 5254, the end of its own 91-day entry schedule, 1930-06-02).
- **8 members** only amend another order, mostly by substituting a corrected land description (branches B10m,
  B10p). Under ruling P2 the amending text merges into the parent order on issue: its text continues as part of the
  parent until the parent ends, and the parent's lifecycle carries it. The date is the amending order's date.
- **23 members** are Army reservations in the Philippine Islands at places the United States did not keep after
  independence (branch B20). The Philippine Independence Act, Proclamation 2695, the Treaty of General Relations and
  the 1947 Military Bases Agreement surrendered every such reservation, by words that name reservations and fix what
  was kept. Each lead gives the interval from the order's date to 1952-03-26, the latest date to which the 1947
  agreement let U.S. forces keep temporary installations outside the listed bases.
- **12 members** are reservations in the Canal Zone (branch B21). Each lead gives the interval from the order's date
  to 1999-12-31, when the Panama Canal Treaty of 1977 terminated and with it every U.S. right to use defense sites in
  the former Zone.

Where MEMBERS holds only the year of an order (eight decided members), the lead's date or interval start runs over
that whole year (the branches marked `-y` and a year).

No `yes` lead is possible from the fields held. A `yes` needs a current-law predicate: a statute that names the
reservation, or a current federal land record showing the order's lands still reserved under it. The project holds
no such record for any member, and absence of a revocation is not evidence that a reservation still stands. The 152
open members are 60 continental reservations (B33), 25 in Hawaii (B30), 9 in Alaska (B31), 5 in Puerto Rico (B32),
16 Philippine reservations at places kept as bases under the 1947 agreement (B20r), 7 in the Port of Manila
reservation, which the 1947 agreement kept available with no end date (B20p), 16 restorations that keep a reversion
or other continuing interest (B12), and 14 non-land orders that belong to other families (B01a-c).

Branch counts from `python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-MILITARY-RESERVATION.json --hints`
(year-only twins counted with their parent branch):

| Branch | Members | Lead | What it covers |
|---|---:|---|---|
| C30 | 1 | no | EO 1084 (Saturday hours), superseded by EO 1096 |
| B01a | 8 | open | Not land orders: Saturday hours, Marine Corps duties, Coast Guard prisoners (belong to PD-ADMIN) |
| B01b | 3 | open | Not land orders: Civil Service Rules Schedule A amendments (belong to PD-CS-RULES) |
| B01c | 3 | open | Not land orders: German ship seizure, harbors closed to foreign vessels, "military camps" (belong to PD-WAR-EMERGENCY) |
| C01-C29, C31, C32 | 37 | no | Ended by a later held executive order that names them |
| P01-P22 | 23 | no | Revoked in full by a Public Land Order, per BLM's held table |
| B10p | 2 | no | EO 5174 and EO 456: amend another order only (`merged_into_parent_on_issue`) |
| B11x | 2 | no | EO 3402 and EO 5157: relinquish or restore only (`spent_on_issue`) |
| B09 | 1 | no | EO 5254: revocation plus an entry schedule that ran out on its own terms |
| B10 | 4 | no | Revokes another order only (`spent_on_issue`) |
| B10m (+ B10m-y1919) | 6 | no | Amends another order only (`merged_into_parent_on_issue`) |
| B11 (+ B11-y1906, -y1911, -y1914, -y1919, -y1924) | 53 | no | Restores, relinquishes or disposes of land, with no continuing interest (`spent_on_issue`) |
| B12 | 16 | open | Restoration or relinquishment that keeps a reversion, retained tract, reserved right, purpose restriction or a part held in another reservation |
| B20r | 16 | open | Philippine reservations at places the 1947 Military Bases Agreement retained |
| B20p | 7 | open | Philippine reservations in the Port of Manila reservation |
| B20n | 0 | open | Philippine naval reservations outside the bases |
| B20 (+ B20-y1907) | 23 | no | Philippine Army reservations at places not retained (`ended_by_express_class_instrument`) |
| B21 (+ B21-y1920) | 12 | no | Canal Zone reservations (`ended_by_express_class_instrument`) |
| B30 | 25 | open | Hawaii reservations |
| B31 | 9 | open | Alaska reservations |
| B32 | 5 | open | Puerto Rico reservations |
| B33 | 60 | open | Continental reservations, ranges and departmental transfers |
| B99 | 0 | open | Catch-all |

By WPA family hint the members are: military_reservation 177, other 66, land_withdrawal 51, emergency_war 14,
civil_service_rules 3, indian_reservation 3, canal_zone 2.

**Contradictions.** The engine flags 5 leads where a held later-event edge disagrees with the lead. None changes a
lead:

- EO 2281 (B33, open, lead kind `persistence_lead_but_held_ending_edge`): the three revocation edges come from EO
  5590 (1931), which revokes in part "Executive order of December 6, 1915, creating Petroleum Reserve No. 40,
  Montana No. 1", a different order of the same date as EO 2281 (Alabama military lands). The edges do not reach EO
  2281; it stays open.
- EO 2978 (C03, no, 1919-03-25; flag `acted_on_after_lead_end`): EO 5155 (1929) withdraws part of "the Fort De Russy
  Military Reservation ... set apart by Executive Order (No. 2978) of October 21, 1918". EO 3067 had revoked EO 2978
  in 1919 and withdrawn the tract again "in lieu of" it, so the 1929 recital misdescribes the EO 3067 tract and does
  not revive EO 2978.
- EO 3080 (B11, no, 1919-04-30): EO 5132 (1929) restores another parcel of the Hawaii Arsenal reservation and
  describes its bounds; it does not act on EO 3080's restoration, which was performed on issue.
- EO 3418 (B11, no, 1921-03-08): EO 4131 (1925) excepts from its own relinquishment the part of the Nulato-St.
  Michael right-of-way "turned over to the Department of the Interior for disposition" by EO 3418. The recital
  confirms that EO 3418 had already acted.
- EO 341-A (B11, no, 1905-07-15): EO 477 (1906) redefines the Fort Bayard reservation "declared by Executive Order,
  dated April 19, 1869 ... and modified by Executive Order of July 15, 1905". It acts on the 1869 reservation, which
  EO 341-A had reduced by 28 acres; the 28-acre relinquishment stays spent.

Two edges that would have flagged under a narrower date are also false matches and are disclosed on their branches:
EO 10069 (1949) amends "Executive Order No. 985 of November 25, 1946", a misprinted number for a travel-expense
order, not EO 985 (Camp Overton, 1908); and EO 9836's edges on EO 1248 are a Code of Federal Regulations list of
orders affecting military reservations, not a revocation.

## (a) How members end or persist

**Own terms: orders that only revoke, restore, relinquish or amend (M1).** Many members do one thing: revoke an
earlier order, exclude land from a reservation and restore it to the public domain or to the government of a
territory or of the Philippines, or place reservation lands under the Secretary of the Interior for disposal. Under
ruling P1 such an order's command is exhausted on its effective date; its consequence belongs to the other order's
lifecycle or to the land's history. The doctrine applies P1 only when the order's text shows no continuing clause: no
reversion (a right for the land to return to the United States if a condition fails), no tract "retained" for
military use, no reserved water or right-of-way, no purpose restriction such as "for road purposes", no part that
"shall be held in reservation" under another use, no new reservation of the same or other lands, and no redefinition
of the remaining reservation's boundaries ("so that the reservation will include all public lands, and those only,
within..."). An order that redefines what remains is treated as a reservation order, because the remaining
reservation then rests on its description. EO 1397 (Fort Grant, 1911) is an example of an order kept open on this
test: it relinquishes the reservation but also orders that the part inside the Mount Graham Forest Reserve "shall be
held in reservation and administered as forest reserve lands".

An order whose only content amends another order falls under ruling P2: EO 1080, 1097, 3171, 5044, 5119, 5240 (which
also revokes the earlier correction EO 5174), 5174 (correcting EO 4679's Pupukea description) and 456 (rewriting EO
372-B's Fort St. Michael description "to read as follows"). Under the owner's strike-and-insert ruling the amended
clause continues, amended, as part of the parent order, so the amending order has no command of its own after issue.
Every such lead carries the disclosure "its text continues as part of the parent until the parent ends; the parent's
lifecycle carries it". Later acts on the parents (EO 5240 revoking EO 5174 and amending EO 4679 again; EO 636
rescinding EO 372-B "as amended") are events of the parents. If the owner prefers to treat an amending order as
living as long as the amended text lives, these eight leads become `open` pending their parents.

**Statute: relinquishment under the Act of July 5, 1884 (M2).** Section 1 of that Act (23 Stat. 103) directs the
President, when reservation lands have become useless for military purposes, to cause them "to be placed under the
control of the Secretary of the Interior for disposition". An order made under it ends the military reservation over
the lands it names; later sale or entry happens under the statute and the land laws. Section 1 (former 43 U.S.C.
1071-1073) was repealed on October 31, 1951 (ch. 654, sec. 1(114), 65 Stat. 706). That repeal removed the authority
to make new transfers; under ruling P3 it ends no transfer already made, and the transfers are spent on issue in any
case. Four members show that a transfer could be undone before disposal: EO 1011 vacated EO 803 (Fort Keogh), EO
2377 vacated EO 1422 (Fort Brown), EO 2563 vacated EO 1279 (Fort Ringgold), and EO 636 rescinded EO 372-B (Fort St.
Michael). For those members the end is the vacating order (branches C09, C16, C23, C24). One transfer, EO 3574 (Fort
Davis, Alaska, 1921), was revoked "entirely" by name by PLO 1712 in 1958, which shows that the government treated its
withdrawal as operating until then; its lead is the interval 1921-11-04 to 1958-08-07 (branch P22). The same PLO
revokes "in part" EO 7049 (1935), which placed four Alaska post cemeteries under Interior and is decided `no` on its
own date under P1; the partial revocation is disclosed on branch B11. If the owner reads 1884-Act transfers as
withdrawals that last until disposal, the Alaska transfers on B11 would instead need the instrument that ended each
withdrawal.

**Later instrument naming the member (M3).** A later order that revokes, vacates, rescinds or supersedes a member by
number or date, or that places all of the member's lands under another authority, ends it on the later order's date
(ruling P3: the later instrument's words reach the member). The doctrine uses only later orders whose text the
project holds, so each lead can be checked against a phrase in a held file.

| Branch | Member(s) ended | Later order and date | What the later order does |
|---|---|---|---|
| C01 | EO 1169 | EO 2143, 1915-03-03 | Revokes the Arizona National Guard rifle range |
| C02 | EO 2136 | EO 2405, 1916-06-19 | Revokes the Momungan reservation and re-reserves the tract |
| C03 | EO 2978 | EO 3067, 1919-03-25 | Revokes the Fort DeRussy seaward withdrawal and makes a new one |
| C04 | EO 3293 | EO 3313-A, 1920-07-24 | Revokes the Limbones Island order and re-reserves under another statute |
| C05 | EO 666 | EO 683, 1907-08-19 | Revokes the Malate Barracks enlargement |
| C06 | EO 4393 | EO 5254, 1929-12-31 | Revokes the New Mexico National Guard target range |
| C08 | EO 796 | EO 1282, 1911-01-10 | Places all Biliran Island lands under the Philippine government |
| C09 | EO 803 | EO 1011, 1909-01-22 | Vacates the Fort Keogh transfer to Interior |
| C10 | EO 1011 | EO 3952, 1924-02-02 | Places "all the remaining part" of Fort Keogh under Interior (the eastern part went by the order of July 26, 1922, EO 3711) |
| C11 | EO 2772 | EO 3402, 1921-02-11 | Places all lands in T. 22 S., R. 9 W. reserved by EO 2772 under Interior |
| C12 | EO 2517 | EO 3497, 1921-06-15 | Places the same 720 acres under Interior |
| C13 | EO 1136 | EO 3514, 1921-07-14 | Places the same three sections under Interior |
| C14 | EO 2944 | EO 4062, 1924-08-11 | Returns the same 66.12 acres on Virginia Key to Interior |
| C15 | EO 1423 | EO 3418, 1921-03-08 | Places the Nulato reservation "as set apart by" the 1908 and 1911 orders under Interior |
| C16 | EO 372-B | EO 636, 1907-05-16 | Rescinds the Fort St. Michael transfer before it took effect |
| C17 | EO 2869 | EO 3130, 1919-07-25 | Rescinds the 1918 transfer of part of the Balboa radio station |
| C18 | EO 1948, EO 3848 | EO 4047, 1924-07-08 | Rescinds the Balboa radio station orders and creates a new naval reservation |
| C19 | EO 2275, EO 2385 | EO 7320, 1936-03-19 | Revokes the North Dakota militia target range withdrawals |
| C20 | EO 4047 | EO 7387, 1936-06-15 | Supersedes the 1924 Balboa naval reservation |
| C21 | EO 3202, EO 3386, EO 3428 | EO 7407, 1936-07-06 | Supersedes the Quarry Heights orders |
| C22 | EO 7407 | EO 9293, 1943-01-02 | Supersedes the 1936 Quarry Heights order |
| C23 | EO 1279 | EO 2563, 1917-03-27 | Vacates the Fort Ringgold transfer to Interior |
| C24 | EO 1422 | EO 2377, 1916-05-02 | Vacates the Fort Brown transfer to Interior |
| C25 | EO 1507 | EO 5715, 1931-09-16 | Removes "the restrictions as to use imposed by Executive Order No. 1507", the armory condition and reversion that were EO 1507's only continuing clause |
| C26 | EO 330-A | EO 432, 1906-03-28 | Places "the military reservation of Grass Island ... as reserved by Executive Order, dated June 12, 1905" under Interior |
| C27 | EO 1237 | EO 4204, 1925-04-15 | "The Executive Order (No. 1237) of August 15, 1910 ... is hereby rescinded"; the Cordova Point tract returns to the National Forest |
| C28 | EO 1197, EO 1338, EO 483, EO 1364 | EO 3056, 1919-03-03 | Places the Cotabato reservation (1910, amended 1911) and Torrey Barracks at Malabang (as amended in 1904, 1906 and 1911) under the Philippine government |
| C29 | EO 4671 | EO 4716, 1927-09-12 | Re-issues the Norfolk Supply Base transfer with corrected courses; EO 4814 recites that EO 4716 "was issued, superseding said Executive Order No. 4671" |
| C30 | EO 1084 | EO 1096, 1909-06-25 | "The following order will supersede that of June 8, 1909, as to hours of labor on Saturday during the months mentioned" |
| C31 | EO 1139 | EO 1617, 1912-09-30 | Restores all of Camp Jossman "as reserved ... and modified by Executive Order dated November 22, 1909" to the Philippine government |
| C32 | EO 1579 | EO 3464, 1921-05-17 | Places under Interior the 150 acres of Fort Duchesne that EO 1579 had retained |

Public Land Orders that revoke a member as a whole, as BLM's official table (held) states them. Each row of the table
is a finding aid, not the order; the PLO texts are not held and are proposed for fetch.

| Branch | Member(s) ended | PLO, signature date, Federal Register | Table row |
|---|---|---|---|
| P01 | EO 2353 | PLO 143, 1943-06-18, 8 FR 9429-30 | "revoking EO Nos. 2353, establishing Fort Matanzas military reservation" |
| P02 | EO 1248 | PLO 359, 1947-03-14, 12 FR 1944 | "revoking EO Nos. 771 and 1248" |
| P03 | EO 2533 | PLO 410, 1947-09-17, 12 FR 6362 | "revoking EO No. 2533" |
| P04 | EO 1450 | PLO 833, 1952-05-21, 17 FR 4822 | "revoking EO Nos. 1450 and 9029" (and withdrawing the lands again for the Army) |
| P05 | EO 1920 | PLO 984, 1954-07-22, 19 FR 4632 | "revoking EO No. 1920 of Apr. 21, 1914" |
| P06 | EO 241 | PLO 1224, 1955-09-14, 20 FR 7076 | "revoking EO of Dec. 9, 1903" (by date; EO 241 is the Alaska order of that date) |
| P07 | EO 6851 | PLO 1271, 1956-03-14, 21 FR 1719 | "revoking EO No. 6851 of Sept. 22, 1934" |
| P08 | EO 3684 | PLO 1303, 1956-05-28, 21 FR 3798 | "revoking EO No. 3684 of May 25, 1922" |
| P09 | EO 4682 | PLO 1320, 1956-08-15, 21 FR 6277 | "revoking EO No. 4682 of July 4, 1927" |
| P10 | EO 1315 | PLO 1326, 1956-08-21, 21 FR 6407 | "revoking EO No. 1315 of Mar. 14, 1911" |
| P11 | EO 2233 | PLO 1411, 1957-04-22, 22 FR 2952 | "revoking EO No. 2233 of Aug. 6, 1915" |
| P12 | EO 439 | PLO 1636, 1958-05-14, 23 FR 3388 | "revoking EOs of Apr. 12, 1906 and No. 5562 of Feb. 20, 1931, entirely" (by date; EO 439 is the Mississippi order of that date) |
| P13 | EO 4449, EO 5219 | PLO 1712, 1958-08-07, 23 FR 6197 | "EO Nos. 3574 of Nov. 4, 1921, 4227 of May 16, 1925, 4449 of May 29, 1926, 4546 of Nov. 29, 1926 and 5219 of Nov. 5, 1929, entirely" |
| P14 | EO 5251 | PLO 2252, 1961-01-11, 26 FR 324 | "revoking EO No. 5251 of Dec. 31, 1929" |
| P15 | EO 1262 | PLO 2454, 1961-08-08, 26 FR 7344 | "revoking EO Nos. 1262 of Nov. 2, 1910 and 1510 of Apr. 1, 1912" |
| P16 | EO 2131 | PLO 2504, 1961-09-25, 26 FR 9226 | "revoking EO No. 2131 of Jan. 30, 1915" (PLO 976 of 1954 had revoked it in part) |
| P17 | EO 4762 | PLO 2510, 1961-09-25, 26 FR 9228 | "revoking EO No. 4762 of Nov. 19, 1927" |
| P18 | EO 1238 | PLO 3728, 1965-07-06, 30 FR 8832 | "revoking EO No. 1238 of Aug. 20, 1910" |
| P19 | EO 4962 | PLO 4803, 1970-04-17, 35 FR 6588 | "revoking EO No. 4962 of Sept. 17, 1928" (PLO 2621 of 1962 had revoked it in part) |
| P20 | EO 2295 | PLO 5052, 1971-05-13, 36 FR 8807 | "revoking EO No. 2295" (EO 6971 and PLO 4313 had modified it) |
| P21 | EO 1557 | PLO 6688, 1988-11-04, 53 FR 46871 | "revoking EO No. 1557" |
| P22 | EO 3574 | PLO 1712, 1958-08-07, 23 FR 6197 | as P13 (interval from the order's own date, see M2) |

A PLO that revokes an order by number and withdraws the same land again (PLO 833 for EO 1450, PLO 1326 for EO 1315,
and others) ends the executive order; any later military use rests on the PLO. EO 1920 is not a military
reservation (it set apart the Klawak Reservation for the Bureau of Education and the natives of Alaska); its end by
PLO 984 is the same in any family.

Partial actions are not used as ends: EO 4128 revokes EO 3949 only for one lot, EO 2622 vacates only the
Agriculture tract of EO 2377, EO 4684 restores only the Wailua part of EO 4635, EO 5405 restores most of EO 4760 but
retains a tract, EO 4421 revokes EO 1920 except a school reservation, EO 2167 releases part of EO 1922, EO 4052
restores a strip of EO 2565, EO 5493 transfers parts of Augur Barracks, PLO 1712 revokes EO 7049 only in part, and
PLOs 645, 976, 2621, 5647 and others revoke members "in part". Those members stay on their own branches. EO 3402 and
EO 3078 together relinquish most of EO 2879 (New Mexico artillery range), but the OCR of EO 3402 reads the township
that would complete it as "T. 208. R, 10 W" (EO 2879 reserved T. 21 S., R. 10 W.), so EO 2879 stays open until a
clean copy is read.

**Philippine independence (M4).** These instruments carry words that reach reservations in the Islands.

- Section 5 of the Philippine Independence Act (Act of March 24, 1934, ch. 84, 48 Stat. 456, 459) granted U.S.
  property in the Islands to the Commonwealth, "except such land or other property as has heretofore been designated
  by the President of the United States for Military and other reservations of the Government of the United States".
  This kept reservation lands out of the 1935 grant; it is not an end.
- Section 10(a) (48 Stat. 463) directed the President, on the July 4 after ten years of the Commonwealth, to "withdraw
  and surrender all right of possession, supervision, jurisdiction, control, or sovereignty then existing and
  exercised by the United States in and over the territory and people of the Philippine Islands, including all
  military and other reservations of the Government of the United States in the Philippines (except such naval
  reservations and fueling stations as are reserved under section 5)". Section 10(b) left "the matter of naval
  reservations and fueling stations" in "its present status" pending negotiation.
- The joint resolution of June 29, 1944 (ch. 322, sec. 2, 58 Stat. 626; 22 U.S.C. 1392) authorized the President "to
  withhold or to acquire and to retain such bases, necessary appurtenances to such bases, and the rights incident
  thereto, in addition to any provided for by the Act of March 24, 1934".
- Proclamation 2695 of July 4, 1946 (60 Stat. 1352, 1353), "in accord with and subject to the reservations provided
  for in the applicable statutes", declares that the United States "hereby withdraws and surrenders all rights of
  possession, supervision, jurisdiction, control, or sovereignty now existing and exercised" over the territory and
  people of the Philippines. Printed just before it, Proclamation 2694 of July 3, 1946 designated nine Manila
  properties for U.S. diplomatic and consular establishments under section 10 of the 1934 Act as amended in 1939; it
  continues no military reservation.
- Article I of the Treaty of General Relations (signed July 4, 1946; in force October 22, 1946; 61 Stat. 1174)
  withdraws and surrenders all such rights "except the use of such bases, necessary appurtenances to such bases, and
  the right incident thereto, as the United States of America, by agreement with the Republic of the Philippines, may
  deem necessary to retain for the mutual protection" of the two countries.
- The agreement so made, the Military Bases Agreement of March 14, 1947 (in force March 26, 1947; 61 Stat. 4019,
  T.I.A.S. 1775, 43 U.N.T.S. No. 673), grants "the right to retain the use of the bases in the Philippines listed in
  Annex A" (art. I(1)), with Annex B bases available on military necessity. Annex A lists Clark Field Air Base and
  Fort Stotsenberg (Pampanga), Mariveles Military Reservation (Bataan), Camp John Hay Leave and Recreation Center
  (Baguio), the Army Communications System "with the deletion of all stations in the Port of Manila Area", a U.S.
  Armed Forces cemetery at San Francisco del Monte, Angeles General Depot, Leyte-Samar Naval Base, Subic Bay with "the
  existing Naval reservation at Olongapo and the existing Baguio Naval Reservation", Tawi Tawi Naval Anchorage,
  Canacao-Sangley Point Navy Base (Cavite), Manila-area radio sites, and Loran stations in Palawan and Zambales. Annex
  B lists Mactan Island, Florida Blanca, Camp Wallace (La Union), Puerto Princesa (Palawan), Tawi Tawi Naval Base and
  Aparri.
- Article XXI of the same agreement keeps two further classes outside the listed bases. Paragraph 1: "It is mutually
  agreed that the United States shall retain the right to occupy temporary quarters and installations now existing
  outside the bases mentioned in Annex A and Annex B, for such reasonable time, not exceeding two years, as may be
  necessary to develop adequate facilities within the bases for the United States armed forces. If circumstances
  require an extension of time, such a period will be fixed by mutual agreement of the two Governments; but such
  extension shall not apply to the existing temporary quarters and installations within the limits of the City of
  Manila and shall in no case exceed a period of three years." Paragraph 2: "Notwithstanding the provisions of the
  preceding paragraph, the Port of Manila reservation with boundaries as of 1941 will be available for use to the
  United States armed forces until such time as other arrangements can be made for supply of the bases by mutual
  agreement of the two Governments." (61 Stat. 4028-4029.)
- Note V of the exchange of notes signed with the agreement reads in full: "I have the honor to state, in signing
  the Agreement of March 14, 1947, Between the United States of America and the Republic of the Philippines
  Concerning Military Bases, the understanding of my Government that the question of the adjustment of any rights and
  titles held by the United States pursuant to the provisions of the Act of Congress of March 24, 1934 (48 Stat. 456)
  as amended, specifically Section 10(b) thereof, the Joint Resolution of the Congress of June 29, 1944, and the Act
  of Congress of July 3, 1946, and Treaties and Agreements heretofore entered into between the United States and the
  Philippines, to real property in any of the bases covered by the aforementioned Agreement or any naval reservations
  or fueling stations not so covered is reserved and will be settled subsequently in accordance with the terms of the
  Acts and Joint Resolution of the Congress mentioned above." (61 Stat. 4033.) The Philippine reply, Note VI, concurs
  "without conceding the existence of any rights or titles to the real property therein referred to".

The doctrine draws four consequences under ruling P5 (where a treaty lets the United States keep using property
under a new instrument, members of that class need the instrument that disposes of it, or an upper bound that the
last such instrument fixes):

1. A reservation at a place listed in Annex A or B (B20r) falls within the treaty's exception; its end is the later
   instrument that relinquished the base, which the project does not hold, so those members are `open`.
2. A reservation in the Port of Manila reservation (B20p) was kept available by art. XXI(2) "until such time as other
   arrangements can be made", with no date; the arrangement is not held, so those members are `open`.
3. A naval reservation or fueling station outside the bases (B20n) is the subject of section 10(b)'s "present
   status" clause and of Note V's reservation for later settlement; the settlement is not held, so such a member
   would be `open`. No member reaches this branch: the Philippine members that name a naval reservation or the Navy (EO 1026, 1134, 1215, 1254, 5139) are all at Annex A places and sit on B20r.
4. Every other reservation in the Islands is an Army reservation at a place not retained (B20). Article I of the
   treaty surrendered it except for what the agreement kept, and the only thing the agreement kept outside the bases
   and the Port reservation is a right to occupy "temporary quarters and installations now existing" for at most two
   years plus an extension that "shall in no case exceed a period of three years". The fields held do not show
   whether U.S. forces still occupied an installation on a given member's land in 1947, so the doctrine does not
   exclude art. XXI(1); it bounds it. Read widely (two years plus an extension of up to three, counted from the
   agreement's entry into force), the right ended no later than 1952-03-26; on the narrower reading that three years
   is the whole period, 1950-03-26; for the City of Manila, where no extension was allowed, 1949-03-26. For land that
   held no U.S. installation in 1947 the surrender took effect on July 4, 1946 or October 22, 1946. B20 leads are the
   interval from the order's date to 1952-03-26. Note V reserves title questions for the bases and for naval
   reservations outside them; it does not reserve the possession and control of an Army reservation outside the
   bases. Any U.S. title that outlasted the surrender is a property question, not a continuation of the reservation.

**End of the Canal Zone (M5).** The Panama Canal Treaty (signed September 7, 1977; 1280 U.N.T.S. No. 21086) came into
force on October 1, 1979. On entry into force it terminated and superseded the Isthmian Canal Convention of 1903
(art. I(1)(a)), and Panama reassumed plenary jurisdiction over the former Canal Zone (art. XI). U.S. military forces
kept using defense sites under the separate Agreement in Implementation of Article IV, a new instrument that excepts
that property from the transfer. Article II provides: "This Treaty shall terminate at noon, Panama time, December 31,
1999." The Panama Canal Act of 1979 (held) took effect with the Treaty (sec. 3304, 93 Stat. 500). Its sec. 3(b)(1)
(93 Stat. 455) is a rule of construction: for applying the Canal Zone Code and other laws after that date, "Canal
Zone" is deemed to refer to the areas and installations in Panama made available to the United States. Its sec.
1504(a)(1) (93 Stat. 488) authorized the Secretary of State to convey to Panama property in the former Zone "which is
not within the land and water areas the use of which is made available to the United States". The Act has no words
that end these reservations. Under ruling P5 the bound for every Canal Zone reservation is the Treaty's termination:
interval from the order's date to 1999-12-31, or earlier where a later order superseded the member (C17, C18, C20 to
C22). A member whose land passed to Panama on October 1, 1979, outside the defense sites, ended then; identifying
those needs the Article IV agreement, which is not held.

**Hawaii statehood (M6, lead only).** Section 5(c) of the Hawaii Admission Act (Pub. L. 86-3, 73 Stat. 4, 5) kept as
U.S. property all lands set aside for federal use by Act, proclamation or executive order on the date of admission;
section 5(e) required each agency to report within five years and the President to convey to the State land no
longer needed. The Act neither ends nor confirms any one order; it tells the reader where to look.

**Later revocations, transfers, conveying statutes and surplus disposals not held (M7, lead only).** The open
continental and Alaska reservations ended, if they ended, through a later executive order or Public Land Order not
yet matched, a statute conveying the named reservation, or disposal as surplus property. These reach members tract
by tract and decide nothing for the class. In Alaska, the blanket relinquishments EO 4131 (1925) and EO 7127 (1935)
and the cemetery order EO 7049 (1935) are themselves members; they list reservations by name with exceptions (post
cemeteries, Signal Corps tracts, Alaska Road Commission sites), so matching them to earlier members is a reading
task.

**Continuity only (M8).** The Federal Land Policy and Management Act of 1976 (FLPMA) repealed, from October 21, 1976,
the President's implied authority to make withdrawals and the withdrawal sections of the Pickett Act of June 25, 1910
(36 Stat. 847), under which many National Guard ranges in this family were reserved (sec. 704(a), 90 Stat. 2792).
Section 701(c) (90 Stat. 2786) kept "all withdrawals, reservations, classifications, and designations in effect as of
the date of approval of this Act" in full force until modified. A repeal of authority with a savings clause is not an
end (ruling P3). The Engle Act of February 28, 1958 (72 Stat. 27; 43 U.S.C. 155-158) requires an Act of Congress for
defense withdrawals over 5,000 acres made on or after its enactment; it is prospective and does not reach these
orders.

## (b) Primary sources

The member's own order text is cited as source `S-ORDER` with `"member_text": true` (ruling P6); the engine records
the member's held text path, sha256 and grade on each lead.

Held sources (text file in the repository, opened, pin phrase found, sha256 of the file at `held_path`):

| ID | Citation | Held path | sha256 | Pin |
|---|---|---|---|---|
| S-TM | Philippine Independence Act, Mar. 24, 1934, ch. 84, secs. 5, 10, 48 Stat. 456, 459, 463 | `jobs/astra-source-retention/output/pages/2900efa1.../selected-pages.txt` | 636fc71799d9391051b56054be9bb9ce42ab58d46fa0e458d36c9fc465386f70 | "including all military and other reservations" |
| S-P2695 | Proclamation 2695, July 4, 1946, 60 Stat. 1352, 1353 | `jobs/astra-source-retention/output/pages/c493d8ef.../selected-pages.txt` | 5fdd773800d1210fe04c363d9d4839adc86794bf0b3cded9ba17065b8e1127c1 | "hereby withdraws and surrenders" |
| S-PCA | Panama Canal Act of 1979, Pub. L. 96-70, secs. 3(b)(1), 1504, 3304, 93 Stat. 452, 455, 488, 500 | `jobs/source-ladder/output/texts/queue_EO_9293_Panama_Canal_..._8d101fb40b.txt` | 2128a6390e37a43b60c721f18c5cd3bfb281b65e4e21d3cf0d95feca3680e10f | "shall be deemed to refer to the areas and" |
| S-FLPMA | FLPMA, Pub. L. 94-579, secs. 701(c), 704(a), 90 Stat. 2743, 2786, 2792 | `jobs/astra-source-retention/output/pages/3949c2ad.../selected-pages.txt` | e14185c661715326d9306d39413ea761527b18a9a9335ebcab70e298e459a786 | "in effect as of the date of approval of this Act shall remain in full" |
| S-BLM-1-694, -695-2250, -2251-4975, -4976-5806, -5807-6825 | Bureau of Land Management, Tables of Public Land Orders (official finding aids) | `jobs/shepard-citations/output/texts/blm/plo_<range>.txt` | listed per table in the JSON | one row pin per PLO used, listed in the JSON `row_pins` |
| S-EO… | 32 later orders used in branches C01-C32 (EO 432, 636, 683, 1011, 1096, 1282, 1617, 2143, 2377, 2405, 2563, 3056, 3067, 3130, 3313-A, 3402, 3418, 3464, 3497, 3514, 3952, 4047, 4062, 4204, 4814, 5240, 5254, 5715, 7320, 7387, 7407, 9293) | each order's text under `jobs/pinakes-proquest-ingest`, `jobs/wikisource-texts`, `jobs/app-executive-orders` or `jobs/ofr-compilations` | listed per source in the JSON | listed per source in the JSON |

Full held paths, hashes and pins are in the JSON `sources` array; every held file was re-read, its sha256 recomputed
and every pin (including each BLM row pin) found. The texts of the later orders are transcriptions or page-scan OCR,
not authenticated originals, and some pins carry OCR errors exactly as the file has them (for example "Exeentive
Order No. 2772", "February io, 1915" and "reserved by Hxecutive Order dated").

Sources read on the web and not held (each is in `research/pothier/work/PD-MILITARY-RESERVATION/FETCH_PROPOSED.jsonl`):

| ID | Citation | URL | Used for |
|---|---|---|---|
| S-TGR | Treaty of General Relations, July 4, 1946, art. I, 61 Stat. 1174 (in force Oct. 22, 1946) | https://www.govinfo.gov/link/statute/61/1174 | B20, B20p, B20r |
| S-MBA1947 | Military Bases Agreement with the Philippines, Mar. 14, 1947, arts. I, XXI, XXIX, Annexes A and B, Note V, 61 Stat. 4019, 4028-4029, 4033, T.I.A.S. 1775, 43 U.N.T.S. No. 673 (in force Mar. 26, 1947) | https://treaties.un.org/doc/Publication/UNTS/Volume%2043/volume-43-I-673-English.pdf; https://www.govinfo.gov/link/statute/61/4019 | B20 bound, B20p, B20n, B20r member test |
| S-JR1944 | Joint Resolution of June 29, 1944, ch. 322, sec. 2, 58 Stat. 626 (22 U.S.C. 1392) | https://www.govinfo.gov/link/statute/58/626 | B20: withheld bases |
| S-P2694 | Proclamation 2694, July 3, 1946, 60 Stat. (closing part on the held 1352 page; opening page not verified) | https://www.trumanlibrary.gov/library/proclamations/2694/designating-properties-suitable-diplomatic-and-consular-establishments | B20 disclosure for Manila members |
| S-PCT | Panama Canal Treaty, 1977, arts. I, II, IV, XI, 33 U.S.T. 39, T.I.A.S. 10030, 1280 U.N.T.S. No. 21086 | https://treaties.un.org/doc/Publication/UNTS/Volume%201280/volume-1280-I-21086-English.pdf | B21 bound |
| S-1884 | Act of July 5, 1884, ch. 214, sec. 1, 23 Stat. 103 | https://www.govinfo.gov/content/pkg/STATUTE-23/pdf/STATUTE-23-Pg103.pdf | B11 relinquishments |
| S-1951 | Act of Oct. 31, 1951, ch. 654, sec. 1(114), 65 Stat. 706 (opening page 701 not verified) | https://www.govinfo.gov/link/statute/65/706 | M2 continuity note |
| S-HAA | Hawaii Admission Act, Pub. L. 86-3, sec. 5(c), 5(e), 73 Stat. 4, 5-6 | https://www.govinfo.gov/content/pkg/STATUTE-73/pdf/STATUTE-73-Pg4.pdf | B30 lead |
| S-ENGLE | Engle Act, Pub. L. 85-337, 72 Stat. 27 (43 U.S.C. 155-158) | https://www.govinfo.gov/content/pkg/STATUTE-72/pdf/STATUTE-72-Pg27.pdf | M8 continuity |
| S-PLO-… | 21 Public Land Orders (PLO 143, 359, 410, 833, 984, 1224, 1271, 1303, 1320, 1326, 1411, 1636, 1712, 2252, 2454, 2504, 2510, 3728, 4803, 5052, 6688) | `https://www.govinfo.gov/link/fr/<volume>/<page>?link-type=pdf`, one per PLO in the JSON | P01-P22 |

The `no` leads on B20, B21 and P01-P22 cite unheld sources alongside held ones; the engine therefore adds a "not yet
held" gap to each such lead until the texts are acquired. The 61 Stat. pages of the 1947 agreement were read in a
mirror of the Statutes at Large print and the UNTS copy; the Engle Act pin is the phrase common to the statute and
43 U.S.C. 155 ("the provisions hereof shall apply"), because the Code substitutes "February 28, 1958" for the
statute's "the date of enactment of this Act". Further instruments are needed but have no verified URL: the
Agreement in Implementation of Article IV of the Panama Canal Treaty (for B21 members whose land passed to Panama in
1979), the instruments that relinquished each retained Philippine base (B20r), and the arrangement that ended U.S.
use of the Port of Manila reservation (B20p). A clean copy of EO 3402 is proposed for fetch to settle EO 2879.

## (c) Decision procedure

Branches are tried in order; the first whose conditions all hold decides. "Summary" means the WPA 1944 summary;
"place screen" means a regex on the summary or the title, not the order text, because about half the held texts are
compilations or page scans that can run into a neighbouring order. A branch whose name ends in `-y` and a year is a
twin of the branch named: same conditions and lead, for members whose order date is held only as a year, with the
date (or the interval's start) running over that whole year.

1. **C30, no (ACT).** EO 1084, superseded by EO 1096 on 1909-06-25 (placed before B01a because EO 1084 is a
   Saturday-hours order).
2. **B01a, B01b, B01c, open (out of family).** The title, summary or text names a Saturday four-hour workday, the
   duties of the Marine Corps, or Coast Guard prisoners (B01a, PD-ADMIN); the Civil Service Rules (B01b, PD-CS-RULES);
   or the seizure of German vessels, the closing of harbors to foreign vessels, or the construction of "military
   camps" (B01c, PD-WAR-EMERGENCY). Each lead names the family whose mechanisms should decide it. Several
   Saturday-hours orders were revoked in part by later Saturday-hours orders that revoke "all Executive or other
   orders in conflict herewith", which needs reading there.
3. **C01 to C29, C31, C32, no (ACT).** The member's identifier is one of the targets in the M3 table. Date: the later
   order's date. Gap: the later order's held text is a transcription or OCR.
4. **P01 to P21, no (ACT, `ended_by_public_land_order`).** The member's identifier is one of the targets in the PLO
   table. Date: the PLO's signature date per BLM's table. Gaps: the PLO text is not held; the effective date may be
   the Federal Register publication date.
5. **P22, no (ACT).** EO 3574; interval 1921-11-04 to 1958-08-07.
6. **B10p, no (TERM, `merged_into_parent_on_issue`).** EO 5174 and EO 456, read in full: each only amends its parent.
   Date: the amending order's own date (1929-08-21; 1906-06-08). Disclosure as for B10m.
7. **B11x, no (TERM, `spent_on_issue`).** EO 3402 and EO 5157, read in full: each only relinquishes or restores. Date:
   order date. (B11's screens miss them because EO 3402's summary says "reserved for military purposes by E. O.s 2772
   and 2879" and EO 5157's text recites the part EO 1531 "retained".)
8. **B09, no (TERM).** EO 5254 only, confirmed by the phrase "for a period of 91 days beginning with the 63rd day".
   Date 1930-06-02, the last day of the stated preference period.
9. **B10, no (TERM, `spent_on_issue`).** The summary begins with a citation of an earlier order ("E. O. ..."), says it
   is revoked and does not say it is amended, and neither the summary nor the text adds a new reservation, a placing
   of lands under the War or Navy Department, or a continuation in reservation. Date: order date.
10. **B10m, no (TERM, `merged_into_parent_on_issue`).** As B10, but the summary says the earlier order is amended, and
    the amendment does not enlarge or fix new boundaries. Date: order date. Disclosure: its text continues as part of
    the parent until the parent ends; the parent's lifecycle carries it.
11. **B11, no (TERM, `spent_on_issue`).** The summary says the order restores, diminishes, abolishes, eliminates,
    excludes, relinquishes to a territorial or Philippine government, or places lands under the Interior Department
    for disposal; the summary contains no verb of new reservation (verbs describing an earlier reservation, such as
    "formerly reserved", are excluded from that test); and the text contains no retained-interest phrase, no boundary
    redefinition and no new "hereby reserved / set apart / withdrawn" clause. Date: order date. Gaps: a vacatur by an
    order outside this family would not be detected; OCR may hide a proviso.
12. **B12, open.** As B11, but the text keeps a reversion, a retained tract, a reserved right, a purpose restriction,
    an authority to reserve again, or a part that "shall be held in reservation" under another use, and the place
    screen is not the Philippines or the Canal Zone. What decides it: current title and use of the land, and for
    Hawaii the section 5 conveyance records.
13. **B20r, open.** The place screen finds the Philippine Islands, and the title, summary or text names a place listed
    in Annex A or B of the 1947 agreement (Stotsenburg or Clark, Angeles and Pampanga, Mariveles, Camp John Hay and
    Baguio, Subic Bay, Olongapo and Zambales, Sangley Point, Canacao and Cavite, Leyte and Samar, Tawi Tawi, Mactan and
    Cebu, Camp Wallace and La Union, Palawan, Aparri, Florida Blanca, San Francisco del Monte). Limbones Island off
    Cavite (EO 3313-A) is held here by choice, for its nearness to the Cavite and Manila Bay defenses, though the
    Annexes do not list it. The screen is broad on purpose: a member wrongly caught here stays `open`, which is the
    safe error. What decides it: the instrument that relinquished the base.
14. **B20p, open.** The place screen finds the Philippine Islands, and the title, summary or text names the Port
    Reservation, the reclaimed harbor land of Manila, "plan of reclamation" or Manila Harbor (EO 348-A, 1298, 2838,
    3344, 3500, 4787, 5736). What decides it: the arrangement ending U.S. use under art. XXI(2), and the 1941
    boundary of the Port of Manila reservation.
15. **B20n, open.** The place screen finds the Philippine Islands and the title, summary or text names a naval
    reservation, the Navy Department, naval purposes, or a coaling or fueling station. What decides it: the settlement
    Note V reserves.
16. **B20, no (ACT, `ended_by_express_class_instrument`).** The place screen finds the Philippine Islands and not the
    Canal Zone, and no earlier branch applies. Member test: the reservation lies in the Islands, is an Army
    reservation, and its place is neither an Annex A or B base nor the Port of Manila reservation. Words relied on:
    those quoted under M4. Date: interval from order date to 1952-03-26. Gaps: the treaty and the 1947 agreement are
    unheld; title points under section 5 and Note V; whether a member's land held a U.S. temporary installation in
    1947 is unknown; EO 1437 (Regan Barracks target range) was placed under the Philippine government by EO 3086 in
    1919 "subject to such reimbursement and reservations as may be prescribed by the Secretary of War", and EO 1628
    (Fort Pikit and Fort Reina Regente) appears to be among the reservations EO 3056 transferred in 1919, though the
    OCR gives its order's year as 1913; both keep the class interval.
17. **B21, no (ACT, `ended_by_express_class_instrument`).** The place screen finds the Canal Zone (C.Z., Canal Zone,
    Balboa, Coco Solo, Fort Amador and other named posts, or the Republic of Panama). Words relied on: Treaty art. II,
    quoted under M5. Date: interval from order date to 1999-12-31. Gaps: the Treaty and the Article IV agreement are
    unheld.
18. **B30, open.** The place screen finds Hawaii. What decides it: federal real property and installation records,
    and Hawaii Admission Act section 5(e) conveyances.
19. **B31, open.** The place screen finds Alaska. What decides it: matching to EO 4131, EO 7127, EO 7049 and later
    Public Land Orders, statehood selections and Alaska Native Claims Settlement Act conveyances.
20. **B32, open.** The place screen finds Puerto Rico. What decides it: later transfers to the insular government and
    federal property records.
21. **B33, open.** Every remaining member: continental reservations, National Guard and militia ranges, departmental
    transfers to the Treasury, Veterans' Bureau, Agriculture or Navy, and mixed orders that both restore and reserve.
    What decides it: a revoking order or Public Land Order naming the order or its lands (for `no`), or a statute or
    current BLM withdrawal record or DoD real property record showing the lands still reserved under it (for `yes`).
22. **B99, open.** Catch-all; no member reaches it.

## (d) Members the procedure cannot decide

152 members stay `open`:

- **60 continental, 25 Hawaii, 9 Alaska and 5 Puerto Rico members (B30-B33)** reserve, enlarge, redefine or transfer
  land and have no class-wide end and no held instrument that revokes the whole order. Some may still be federal
  military land (for example the Fort Sill enlargement, EO 685, and Fort Shafter, EO 4545); others were ended in part
  by Public Land Orders the held tables list as partial (EO 1187, EO 2328, EO 6009) or by orders and
  conveyances not yet matched. The missing field is a current-law or land-record predicate per tract (BLM MLRS/LR2000
  withdrawal status, DoD real property inventory, or the revoking instrument). EO 2879 would be decided `no` on
  1921-02-11 if a clean copy of EO 3402 reads "T. 21 S., R. 10 W.".
- **16 Philippine reservations at retained bases (B20r)**: Subic Bay and Olongapo (EO 1026, EO 321-B), Sangley Point
  (EO 1134), Camp John Hay (EO 553, 1610, 1855), the Baguio naval reservation (EO 1254), Camp Stotsenburg (EO 790),
  Mariveles (EO 645, 4112) and Cochinos Point at its edge (EO 3197), Camp Downes on Leyte (EO 612, 1806), Cebu
  (EO 1215), Limbones Island (EO 3313-A), and the 1929 naval reservations whose text names Cavite (EO 5139). The
  project holds none of the instruments that relinquished these bases.
- **7 Port of Manila members (B20p)**: EO 348-A, 1298, 2838, 3344, 3500, 4787 and 5736. The 1947 agreement kept the
  Port of Manila reservation available to U.S. forces with no end date; the later arrangement is not held, and EO
  4787 also covers land in Albay and EO 1298 other Manila reservations.
- **16 restorations with retained interests (B12)**: the restoring command is spent, but a reversion, a retained
  tract, a reserved right or a part held in another reservation may still operate. What decides each is the later
  history of that interest.
- **14 non-land orders (B01a-c)**: outside this family's mechanisms; they belong to PD-ADMIN, PD-CS-RULES and
  PD-WAR-EMERGENCY.

Members that a reviewer should expect to be close calls: EO 220 and EO 3310 (Puerto Rico restorations held open
because the summary or text did not pass the restoration screens); EO 2521 and EO 4179-A (Hawaii diminutions that also
redefine or re-withdraw, held open); EO 3300 (a Puerto Rico conveyance "for school purposes", held open by the
purpose-restriction screen); EO 1105, EO 927 and EO 428 (reservations on "Bata[a]n Island" in Albay, read as Batan
Island rather than the Bataan peninsula and so placed on B20); EO 241 and EO 439 (decided by Public Land Orders that
name them by date, not number); EO 4671 (decided by words of supersession in a later recital); and the B20 place
screen, which depends on WPA summaries naming a Philippine place.

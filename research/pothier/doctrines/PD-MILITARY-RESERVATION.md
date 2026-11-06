# PD-MILITARY-RESERVATION: military and naval reservations (316 members)

Doctrine version 2, 2026-11-05. Machine form: `research/pothier/doctrines/PD-MILITARY-RESERVATION.json`
(schema `pothier-family-doctrine/v1`). Every result below is a status lead proposed to the owner, not a status. The
doctrine applies the coordinator rulings in `research/pothier/COORDINATOR_RULINGS.md` (P1, P2, P3, P5, P6).

## Conclusions

The family holds the 316 orders that X1 typed `military_naval_reservation`, dated 1903 to 1936. An executive order
in this family reserves public land for the War or Navy Department (a "reservation": land set apart for a named
federal use and closed to settlement and sale), enlarges, redefines or transfers such a reservation, or gives the
land back. Fifteen members are not land orders at all. No member concerns a naval petroleum or oil-shale reserve, so
the statutes that later disposed of those reserves are not needed here.

The doctrine decides 143 members as `no` (ended before the cutoff of 2026-10-14), decides none as `yes`, and leaves
173 `open`. The 143 `no` leads rest on these bases:

- **30 members** were revoked, vacated, rescinded, superseded, or relinquished in full by a later order that names
  them and whose text the project holds (branches C01 to C25; 23 of the 25 later orders are members of this family).
  Each lead cites the later order's held text and a phrase in it, and takes that order's date.
- **60 members** only revoke, restore or relinquish (branches B09, B10, B11). Such an order does one thing and does
  it on issue: it is "spent on issue" (ruling P1), and its effect is evidence about the reservation it acted on. The
  date is the order's date (for EO 5254, the end of its own 91-day entry schedule, 1930-06-02).
- **6 members** only amend another order, mostly by substituting a corrected land description (branch B10m). Under
  ruling P2 the amending text merges into the parent order on issue: its text continues as part of the parent until
  the parent ends, and the parent's lifecycle carries it. The date is the amending order's date.
- **35 members** are reservations in the Philippine Islands at places the United States did not keep as bases after
  independence (branch B20). The Philippine Independence Act, Proclamation 2695, the Treaty of General Relations and
  the 1947 Military Bases Agreement together surrendered every such reservation, by words that name reservations
  and fix which bases were kept. Each lead gives the interval from the order's date to 1947-03-26.
- **12 members** are reservations in the Canal Zone (branch B21). Each lead gives the interval from the order's date
  to 1999-12-31, when the Panama Canal Treaty of 1977 terminated and with it every U.S. right to use defense sites in
  the former Zone.

No `yes` lead is possible from the fields held. A `yes` needs a current-law predicate: a statute that names the
reservation, or a current federal land record showing the order's lands still reserved under it. The project holds
no such record for any member, and absence of a revocation is not evidence that a reservation still stands. The 173
open members are 77 continental reservations (B33), 25 in Hawaii (B30), 18 in Alaska (B31), 5 in Puerto Rico (B32),
16 Philippine reservations at places kept as bases under the 1947 agreement (B20r), 17 restorations that keep a
reversion or other continuing interest (B12), and 15 non-land orders that belong to other families (B01a-c).

Branch counts from `python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-MILITARY-RESERVATION.json --hints`:

| Branch | Members | Lead | What it covers |
|---|---:|---|---|
| B01a | 9 | open | Not land orders: Saturday hours, Marine Corps duties, Coast Guard prisoners (belong to PD-ADMIN) |
| B01b | 3 | open | Not land orders: Civil Service Rules Schedule A amendments (belong to PD-CS-RULES) |
| B01c | 3 | open | Not land orders: German ship seizure, harbors closed to foreign vessels, "military camps" (belong to PD-WAR-EMERGENCY) |
| C01-C25 | 30 | no | Ended by a later held order that names them |
| B09 | 1 | no | EO 5254: revocation plus an entry schedule that ran out on its own terms |
| B10 | 4 | no | Revokes another order only (`spent_on_issue`) |
| B10m | 6 | no | Amends another order only (`merged_into_parent_on_issue`) |
| B11 | 55 | no | Restores, relinquishes or disposes of land, with no continuing interest (`spent_on_issue`) |
| B12 | 17 | open | Restoration or relinquishment that keeps a reversion, retained tract, reserved right or purpose restriction |
| B20r | 16 | open | Philippine reservations at places the 1947 Military Bases Agreement retained |
| B20 | 35 | no | Philippine reservations at places not retained (`ended_by_express_class_instrument`) |
| B21 | 12 | no | Canal Zone reservations (`ended_by_express_class_instrument`) |
| B30 | 25 | open | Hawaii reservations |
| B31 | 18 | open | Alaska reservations |
| B32 | 5 | open | Puerto Rico reservations |
| B33 | 77 | open | Continental reservations, ranges and departmental transfers |
| B99 | 0 | open | Catch-all |

By WPA family hint the members are: military_reservation 177, other 66, land_withdrawal 51, emergency_war 14,
civil_service_rules 3, indian_reservation 3, canal_zone 2. The engine reports no contradiction between any lead and a
held later-event edge.

## (a) How members end or persist

**Own terms: orders that only revoke, restore, relinquish or amend (M1).** Many members do one thing: revoke an
earlier order, exclude land from a reservation and restore it to the public domain or to the government of a
territory or of the Philippines, or place reservation lands under the Secretary of the Interior for disposal. Under
ruling P1 such an order's command is exhausted on its effective date; its consequence belongs to the other order's
lifecycle or to the land's history. The doctrine applies P1 only when the order's text shows no continuing clause: no
reversion (a right for the land to return to the United States if a condition fails), no tract "retained" for
military use, no reserved water or right-of-way, no purpose restriction such as "for road purposes", no new
reservation of the same or other lands, and no redefinition of the remaining reservation's boundaries ("so that the
reservation will include all public lands, and those only, within..."). An order that redefines what remains is
treated as a reservation order, because the remaining reservation then rests on its description.

An order whose only content amends another order (EO 1080, 1097, 3171, 5044, 5119 and 5240, which also revokes the
earlier correction EO 5174) falls under ruling P2. Under the owner's strike-and-insert ruling the amended clause
continues, amended, as part of the parent order, so the amending order has no command of its own after issue. Every
such lead carries the disclosure "its text continues as part of the parent until the parent ends; the parent's
lifecycle carries it". If the owner prefers to treat an amending order as living as long as the amended text lives,
these six leads become `open` pending their parents.

**Statute: relinquishment under the Act of July 5, 1884 (M2).** Section 1 of that Act (23 Stat. 103) directs the
President, when reservation lands have become useless for military purposes, to cause them "to be placed under the
control of the Secretary of the Interior for disposition". An order made under it ends the military reservation over
the lands it names; later sale or entry happens under the statute and the land laws. Four members show that such a
transfer could be undone before disposal: EO 1011 vacated EO 803 (Fort Keogh), EO 2377 vacated EO 1422 (Fort Brown),
EO 2563 vacated EO 1279 (Fort Ringgold), and EO 636 rescinded EO 372-B as amended by EO 456 (Fort St. Michael). For
those members the end is the vacating order (branches C09, C16, C23, C24), not the transfer's own date.

**Later instrument naming the member (M3).** A later order that revokes, vacates, rescinds or supersedes a member by
number or date, or that places all of the member's lands under the Interior Department, ends it on the later order's
date. The doctrine uses only later orders whose text the project holds (23 of the 25 are members of this family;
EO 7320, a refuge order, and EO 9293 of 1943 are not), so each lead can be checked against a phrase in a held file.

| Branch | Member(s) ended | Later order and date | What the later order does |
|---|---|---|---|
| C01 | EO 1169 | EO 2143, 1915-03-03 | Revokes the Arizona National Guard rifle range |
| C02 | EO 2136 | EO 2405, 1916-06-19 | Revokes the Momungan reservation and re-reserves the tract |
| C03 | EO 2978 | EO 3067, 1919-03-25 | Revokes the Fort DeRussy seaward withdrawal and makes a new one |
| C04 | EO 3293 | EO 3313-A, 1920-07-24 | Revokes the Limbones Island order and re-reserves under another statute |
| C05 | EO 666 | EO 683, 1907-08-19 | Revokes the Malate Barracks enlargement |
| C06 | EO 4393 | EO 5254, 1929-12-31 | Revokes the New Mexico National Guard target range |
| C07 | EO 5174 | EO 5240, 1929-12-14 | Revokes an earlier Pupukea description correction |
| C08 | EO 796 | EO 1282, 1911-01-10 | Places all Biliran Island lands under the Philippine government |
| C09 | EO 803 | EO 1011, 1909-01-22 | Vacates the Fort Keogh transfer to Interior |
| C10 | EO 1011 | EO 3952, 1924-02-02 | Places "all the remaining part" of Fort Keogh under Interior (the eastern part went by the order of July 26, 1922, EO 3711) |
| C11 | EO 2772 | EO 3402, 1921-02-11 | Places all lands in T. 22 S., R. 9 W. reserved by EO 2772 under Interior |
| C12 | EO 2517 | EO 3497, 1921-06-15 | Places the same 720 acres under Interior |
| C13 | EO 1136 | EO 3514, 1921-07-14 | Places the same three sections under Interior |
| C14 | EO 2944 | EO 4062, 1924-08-11 | Returns the same 66.12 acres on Virginia Key to Interior |
| C15 | EO 1423 | EO 3418, 1921-03-08 | Places the Nulato reservation "as set apart by" the 1908 and 1911 orders under Interior |
| C16 | EO 372-B, EO 456 | EO 636, 1907-05-16 | Rescinds the Fort St. Michael transfer before it took effect |
| C17 | EO 2869 | EO 3130, 1919-07-25 | Rescinds the 1918 transfer of part of the Balboa radio station |
| C18 | EO 1948, EO 3848 | EO 4047, 1924-07-08 | Rescinds the Balboa radio station orders and creates a new naval reservation |
| C19 | EO 2275, EO 2385 | EO 7320, 1936-03-19 | Revokes the North Dakota militia target range withdrawals |
| C20 | EO 4047 | EO 7387, 1936-06-15 | Supersedes the 1924 Balboa naval reservation |
| C21 | EO 3202, EO 3386, EO 3428 | EO 7407, 1936-07-06 | Supersedes the Quarry Heights orders |
| C22 | EO 7407 | EO 9293, 1943-01-02 | Supersedes the 1936 Quarry Heights order |
| C23 | EO 1279 | EO 2563, 1917-03-27 | Vacates the Fort Ringgold transfer to Interior |
| C24 | EO 1422 | EO 2377, 1916-05-02 | Vacates the Fort Brown transfer to Interior |
| C25 | EO 1507 | EO 5715, 1931-09-16 | Removes "the restrictions as to use imposed by Executive Order No. 1507", the armory condition and reversion that were EO 1507's only continuing clause |

Partial actions are not used as ends: EO 4128 revokes EO 3949 only for one lot, EO 2622 vacates only the Agriculture
tract of EO 2377, EO 4684 restores only the Wailua part of EO 4635, EO 5405 restores most of EO 4760 but retains a
tract, and EO 4421 revokes EO 1920 except a school reservation. Those members stay on their own branches.

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
  people of the Philippines.
- Article I of the Treaty of General Relations (signed July 4, 1946; in force October 22, 1946; 61 Stat. 1174)
  withdraws and surrenders all such rights "except the use of such bases, necessary appurtenances to such bases, and
  the right incident thereto, as the United States of America, by agreement with the Republic of the Philippines, may
  deem necessary to retain for the mutual protection" of the two countries.
- The agreement so made, the Military Bases Agreement of March 14, 1947 (in force March 26, 1947), grants "the right
  to retain the use of the bases in the Philippines listed in Annex A" (art. I(1)), with Annex B bases available on
  military necessity. Annex A lists Clark Field Air Base and Fort Stotsenberg (Pampanga), Mariveles Military
  Reservation (Bataan), Camp John Hay Leave and Recreation Center (Baguio), the Army Communications System "with the
  deletion of all stations in the Port of Manila Area", a U.S. Armed Forces cemetery at San Francisco del Monte,
  Angeles General Depot, Leyte-Samar Naval Base, Subic Bay with "the existing Naval reservation at Olongapo and the
  existing Baguio Naval Reservation", Tawi Tawi Naval Anchorage, Canacao-Sangley Point Navy Base (Cavite), Manila-area
  radio sites, and Loran stations in Palawan and Zambales. Annex B lists Mactan Island, Florida Blanca, Camp Wallace
  (La Union), Puerto Princesa (Palawan), Tawi Tawi Naval Base and Aparri.

The doctrine draws two consequences under ruling P5. A reservation at a place the 1947 agreement does not list was
reached by the surrender: an Army reservation on July 4, 1946 (section 10(a) and Proclamation 2695); a naval
reservation, or any base withheld under the 1944 resolution, no later than the agreement's entry into force on March
26, 1947, because the treaty's only exception is for bases retained by agreement and the agreement retained only the
listed bases. Those members (B20) are `no`, with the interval from the order's date to 1947-03-26. A reservation at a
listed place (B20r) falls within the treaty's exception; its end is the later instrument that relinquished the base,
which the project does not hold, so those members are `open`. Two property points are disclosed rather than decided:
section 5 kept title to reservation lands out of the 1935 grant, and Note V of the 1947 agreement reserved
"adjustment of U.S. rights and titles to real property" for later settlement. The surrender reaches the possession,
control and jurisdiction that a reservation commands; any U.S. title that outlasted it is a property question, not a
continuation of the reservation.

**End of the Canal Zone (M5).** The Panama Canal Treaty (signed September 7, 1977; 1280 U.N.T.S. No. 21086) came into
force on October 1, 1979. On entry into force it terminated and superseded the Isthmian Canal Convention of 1903
(art. I(1)(a)), and Panama reassumed plenary jurisdiction over the former Canal Zone (art. XI). U.S. military forces
kept using defense sites under the separate Agreement in Implementation of Article IV, a new instrument that excepts
that property from the transfer. Article II provides: "This Treaty shall terminate at noon, Panama time, December 31,
1999." The Panama Canal Act of 1979 (held) took effect with the Treaty (sec. 3304, 93 Stat. 500) and treats "Canal
Zone" thereafter as the areas in the Republic of Panama made available to the United States (sec. 3(b)(1), 93 Stat.
455), but contains no words that end these reservations earlier. Under ruling P5 the bound for every Canal Zone
reservation is the Treaty's termination: interval from the order's date to 1999-12-31, or earlier where a later order
superseded the member (C17, C18, C20 to C22). A member whose land passed to Panama on October 1, 1979, outside the
defense sites, ended then; identifying those needs the Article IV agreement, which is not held.

**Hawaii statehood (M6, lead only).** Section 5(c) of the Hawaii Admission Act (Pub. L. 86-3, 73 Stat. 4, 5) kept as
U.S. property all lands set aside for federal use by Act, proclamation or executive order on the date of admission;
section 5(e) required each agency to report within five years and the President to convey to the State land no
longer needed. The Act neither ends nor confirms any one order; it tells the reader where to look.

**Later revocations, Public Land Orders, transfers, conveying statutes and surplus disposals (M7, lead only).** Most
continental and Alaska reservations ended, if they ended, through a later executive order or Public Land Order (the
Interior Department's instrument for withdrawals and revocations after 1942), a statute conveying the named
reservation, or disposal as surplus property. These reach members tract by tract and decide nothing for the class. In
Alaska, the blanket relinquishments EO 4131 (1925) and EO 7127 (1935) and the cemetery order EO 7049 (1935) are
themselves members; they list reservations by name with exceptions (post cemeteries, Signal Corps tracts, Alaska Road
Commission sites), so matching them to earlier members is a reading task.

**Continuity only (M8).** The Federal Land Policy and Management Act of 1976 repealed, from October 21, 1976, the
President's implied authority to make withdrawals and the withdrawal sections of the Pickett Act of June 25, 1910 (36
Stat. 847), under which many National Guard ranges in this family were reserved (sec. 704(a), 90 Stat. 2792). Section
701(c) (90 Stat. 2786) kept "all withdrawals, reservations, classifications, and designations in effect as of the date
of approval of this Act" in full force until modified. A repeal of authority with a savings clause is not an end
(ruling P3). The Engle Act of February 28, 1958 (72 Stat. 27; 43 U.S.C. 155-158) requires an Act of Congress for
defense withdrawals over 5,000 acres made on or after that date; it is prospective and does not reach these orders.

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
| S-EO… | 25 later orders used in branches C01-C25 (EO 683, 636, 1011, 1282, 2143, 2377, 2405, 2563, 3067, 3130, 3313-A, 3402, 3418, 3497, 3514, 3952, 4047, 4062, 5240, 5254, 5715, 7320, 7387, 7407, 9293) | each order's text under `jobs/pinakes-proquest-ingest`, `jobs/wikisource-texts`, `jobs/app-executive-orders` or `jobs/ofr-compilations` | listed per source in the JSON | listed per source in the JSON |

Full held paths, hashes and pins are in the JSON `sources` array; every held file was re-read, its sha256 recomputed
and every pin found. The texts of the later orders are transcriptions or page-scan OCR, not authenticated originals,
and some pins carry OCR errors exactly as the file has them (for example "Exeentive Order No. 2772" and "February io,
1915").

Sources read on the web and not held (each is in `research/pothier/work/PD-MILITARY-RESERVATION/FETCH_PROPOSED.jsonl`):

| ID | Citation | URL | Used for |
|---|---|---|---|
| S-TGR | Treaty of General Relations, July 4, 1946, art. I, 61 Stat. 1174 (in force Oct. 22, 1946) | https://www.govinfo.gov/link/statute/61/1174 | B20 and B20r |
| S-MBA1947 | Military Bases Agreement with the Philippines, Mar. 14, 1947, arts. I, XVII, XXIX, Annexes A and B, Exchange of Notes, 43 U.N.T.S. No. 673 (in force Mar. 26, 1947; Statutes at Large citation not verified) | https://treaties.un.org/doc/Publication/UNTS/Volume%2043/volume-43-I-673-English.pdf | B20 bound and B20r member test |
| S-JR1944 | Joint Resolution of June 29, 1944, ch. 322, sec. 2, 58 Stat. 626 (22 U.S.C. 1392) | https://www.govinfo.gov/link/statute/58/626 | M4: withheld bases |
| S-PCT | Panama Canal Treaty, 1977, arts. I, II, IV, XI, 33 U.S.T. 39, T.I.A.S. 10030, 1280 U.N.T.S. No. 21086 | https://treaties.un.org/doc/Publication/UNTS/Volume%201280/volume-1280-I-21086-English.pdf | B21 bound |
| S-1884 | Act of July 5, 1884, ch. 214, sec. 1, 23 Stat. 103 | https://www.govinfo.gov/content/pkg/STATUTE-23/pdf/STATUTE-23-Pg103.pdf | B11 relinquishments |
| S-HAA | Hawaii Admission Act, Pub. L. 86-3, sec. 5(c), 5(e), 73 Stat. 4, 5-6 | https://www.govinfo.gov/content/pkg/STATUTE-73/pdf/STATUTE-73-Pg4.pdf | B30 lead |
| S-ENGLE | Engle Act, Pub. L. 85-337, 72 Stat. 27 (43 U.S.C. 155-158) | https://www.govinfo.gov/content/pkg/STATUTE-72/pdf/STATUTE-72-Pg27.pdf | M8 continuity |

The `no` leads on B20 and B21 cite these unheld sources alongside held ones; the engine therefore adds a "not yet
held" gap to each such lead until the treaty texts are acquired. Two further instruments are needed but have no
verified URL and are not proposed for fetch: the Agreement in Implementation of Article IV of the Panama Canal Treaty
(for B21 members whose land passed to Panama in 1979), and the instruments that relinquished each retained Philippine
base (for B20r).

## (c) Decision procedure

Branches are tried in order; the first whose conditions all hold decides. "Summary" means the WPA 1944 summary;
"place screen" means a regex on the summary or the title, not the order text, because about half the held texts are
compilations or page scans that can run into a neighbouring order.

1. **B01a, B01b, B01c, open (out of family).** The title, summary or text names a Saturday four-hour workday, the
   duties of the Marine Corps, or Coast Guard prisoners (B01a, PD-ADMIN); the Civil Service Rules (B01b, PD-CS-RULES);
   or the seizure of German vessels, the closing of harbors to foreign vessels, or the construction of "military
   camps" (B01c, PD-WAR-EMERGENCY). Each lead names the family whose mechanisms should decide it. Several
   Saturday-hours orders were revoked in part by later Saturday-hours orders that revoke "all Executive or other
   orders in conflict herewith", which needs reading there.
2. **C01 to C25, no (ACT).** The member's identifier is one of the targets in the table under (a). Date: the later
   order's date. Gap: the later order's held text is a transcription or OCR.
3. **B09, no (TERM).** EO 5254 only, confirmed by the phrase "for a period of 91 days beginning with the 63rd day".
   Date 1930-06-02, the last day of the stated preference period.
4. **B10, no (TERM, `spent_on_issue`).** The summary begins with a citation of an earlier order ("E. O. ..."), says it
   is revoked and does not say it is amended, and neither the summary nor the text adds a new reservation, a placing
   of lands under the War or Navy Department, or a continuation in reservation. Date: order date.
5. **B10m, no (TERM, `merged_into_parent_on_issue`).** As B10, but the summary says the earlier order is amended, and
   the amendment does not enlarge or fix new boundaries. Date: order date. Disclosure: its text continues as part of
   the parent until the parent ends; the parent's lifecycle carries it.
6. **B11, no (TERM, `spent_on_issue`).** The summary says the order restores, diminishes, abolishes, eliminates,
   excludes, relinquishes to a territorial or Philippine government, or places lands under the Interior Department
   for disposal; the summary contains no verb of new reservation (verbs describing an earlier reservation, such as
   "formerly reserved", are excluded from that test); and the text contains no retained-interest phrase, no boundary
   redefinition and no new "hereby reserved / set apart / withdrawn" clause. Date: order date. Gaps: a vacatur by an
   order outside this family would not be detected; OCR may hide a proviso.
7. **B12, open.** As B11, but the text keeps a reversion, a retained tract, a reserved right, a purpose restriction or
   an authority to reserve again, and the place screen is not the Philippines or the Canal Zone. What decides it:
   current title and use of the land, and for Hawaii the section 5 conveyance records.
8. **B20r, open.** The place screen finds the Philippine Islands, and the title, summary or text names a place listed
   in Annex A or B of the 1947 agreement (Stotsenburg or Clark, Angeles and Pampanga, Mariveles, Camp John Hay and
   Baguio, Subic Bay, Olongapo and Zambales, Sangley Point, Canacao and Cavite, Leyte and Samar, Tawi Tawi, Mactan and
   Cebu, Camp Wallace and La Union, Palawan, Aparri, Florida Blanca, San Francisco del Monte, or Limbones Island off
   Cavite). The screen is broad on purpose: a member wrongly caught here stays `open`, which is the safe error. What
   decides it: the instrument that relinquished the base.
9. **B20, no (ACT, `ended_by_express_class_instrument`).** The place screen finds the Philippine Islands and not the
   Canal Zone, and no retained-base place is named. Member test: the reservation lies in the Islands and its place is
   not among the Annex A or B bases. Words relied on: those quoted under M4. Date: interval from order date to
   1947-03-26 (July 4, 1946 for Army reservations). Gaps: the treaty and the 1947 agreement are unheld; the title
   points under section 5 and Note V; for Manila members, a proclamation of July 3, 1946, printed just before Proclamation
   2695 (its number and opening page not verified), dealt with certain Manila properties for U.S. use; any such use
   rests on that new instrument, not on the member.
10. **B21, no (ACT, `ended_by_express_class_instrument`).** The place screen finds the Canal Zone (C.Z., Canal Zone,
    Balboa, Coco Solo, Fort Amador and other named posts, or the Republic of Panama). Words relied on: Treaty art. II,
    quoted under M5. Date: interval from order date to 1999-12-31. Gaps: the Treaty and the Article IV agreement are
    unheld.
11. **B30, open.** The place screen finds Hawaii. What decides it: federal real property and installation records,
    and Hawaii Admission Act section 5(e) conveyances.
12. **B31, open.** The place screen finds Alaska. What decides it: matching to EO 4131, EO 7127, EO 7049 and later
    Public Land Orders, statehood selections and Alaska Native Claims Settlement Act conveyances.
13. **B32, open.** The place screen finds Puerto Rico. What decides it: later transfers to the insular government and
    federal property records.
14. **B33, open.** Every remaining member: continental reservations, National Guard and militia ranges (33 of the
    77), departmental transfers to the Treasury, Veterans' Bureau, Agriculture or Navy (16), and mixed orders that both
    restore and reserve. What decides it: a revoking order or Public Land Order naming the order or its lands (for
    `no`), or a statute or current BLM withdrawal record or DoD real property record showing the lands still reserved
    under it (for `yes`).
15. **B99, open.** Catch-all; no member reaches it.

## (d) Members the procedure cannot decide

173 members stay `open`:

- **77 continental, 25 Hawaii, 18 Alaska and 5 Puerto Rico members (B30-B33)** reserve, enlarge, redefine or transfer
  land and have no class-wide end. Some may still be federal military land (for example the Fort Sill enlargement,
  EO 685; the Fort Bliss target ranges, EO 1450 and EO 2280; Fort Shafter, EO 4545); many others were ended later by
  Public Land Orders or conveyances. Neither can be shown from the fields held. The missing field is a current-law or
  land-record predicate per tract (BLM MLRS/LR2000 withdrawal status, DoD real property inventory, or the revoking
  instrument).
- **16 Philippine reservations at retained bases (B20r)**: Subic Bay and Olongapo (EO 1026, EO 321-B), Sangley Point
  (EO 1134), Camp John Hay (EO 553, 1610, 1855), the Baguio naval reservation (EO 1254), Camp Stotsenburg (EO 790),
  Mariveles (EO 645, 4112) and Cochinos Point at its edge (EO 3197), Camp Downes on Leyte (EO 612, 1806), Cebu
  (EO 1215), Limbones Island (EO 3313-A), and the 1929 naval reservations whose text names Cavite (EO 5139). The
  project holds none of the instruments that relinquished these bases, so the doctrine states no end or date for
  them.
- **17 restorations with retained interests (B12)**: the restoring command is spent, but a reversion, a retained
  tract or a reserved right may still operate. What decides each is the later history of that interest.
- **15 non-land orders (B01a-c)**: outside this family's mechanisms; they belong to PD-ADMIN, PD-CS-RULES and
  PD-WAR-EMERGENCY.

Members that a reviewer should expect to be close calls: EO 220 and EO 3310 (Puerto Rico restorations held open
because the summary or text did not pass the restoration screens); EO 2521 and EO 4179-A (Hawaii diminutions that also
redefine or re-withdraw, held open); EO 3300 (a Puerto Rico conveyance "for school purposes", held open by the
purpose-restriction screen); EO 1105, EO 927 and EO 428 (reservations on "Bata[a]n Island" in Albay, read as Batan
Island rather than the Bataan peninsula and so placed on B20); and the B20 place screen, which depends on WPA summaries
naming a Philippine place.

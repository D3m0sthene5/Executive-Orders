# PD-MILITARY-RESERVATION: military and naval reservations (316 members)

Doctrine version 1, 2026-11-05. Machine form: `research/pothier/doctrines/PD-MILITARY-RESERVATION.json`
(schema `pothier-family-doctrine/v1`). Every result below is a status lead proposed to the owner, not a status.

## Conclusions

The family holds the 316 orders that X1 typed `military_naval_reservation`, dated 1903 to 1936. An executive order
in this family reserves public land for the War or Navy Department (a "reservation": land set apart for a named
federal use and closed to settlement and sale), enlarges, redefines or transfers such a reservation, or gives the
land back. Fifteen members are not land orders at all. No member concerns a naval petroleum or oil-shale reserve, so
the statutes that later disposed of those reserves are not needed here.

The doctrine decides 159 members as `no` (ended before the cutoff of 2026-10-14), decides none as `yes`, and leaves
157 `open`. The 159 `no` leads rest on four bases:

- **30 members** were revoked, vacated, rescinded, superseded, or relinquished in full by a later order that names
  them and whose text the project holds (branches C01 to C25; 23 of the 25 later orders are members of this family). Each lead cites the later order's held
  text and a phrase in it, and takes that order's date.
- **65 members** only revoke, amend, restore, relinquish or dispose of land and keep no continuing interest
  (branches B09, B10, B11). Such an order is "spent on issue": its single command was carried out when it issued,
  and its effect is evidence about the reservation it acted on. The date is the order's date (for EO 5254, the end
  of its own 91-day entry schedule, 1930-06-02).
- **52 members** concern reservations in the Philippine Islands (branch B20). The Philippine Independence Act of
  1934, Proclamation 2695 of July 4, 1946, and the Treaty of General Relations (in force October 22, 1946) surrendered
  every U.S. right of possession and control over the Islands, reservations included, except the use of bases by
  later agreement. Each lead gives the interval from the order's date to 1946-10-22.
- **12 members** concern reservations in the Canal Zone (branch B21). The Panama Canal Treaty of 1977 entered into
  force on October 1, 1979, terminated the 1903 Convention under which the Zone existed, and returned plenary
  jurisdiction to Panama; the Panama Canal Act of 1979 thereafter treats "Canal Zone" as areas in the Republic of
  Panama made available to the United States. Each lead gives the interval from the order's date to 1979-10-01.

No `yes` lead is possible from the fields held. A `yes` needs a current-law predicate: a statute that names the
reservation, or a current federal land record showing the order's lands still reserved under it. The project holds
no such record for any member, and absence of a revocation is not evidence that a reservation still stands. The 157
open members are 77 continental reservations (B33), 25 in Hawaii (B30), 18 in Alaska (B31), 5 in Puerto Rico (B32),
17 restorations that keep a reversion or other continuing interest (B12), and 15 misclassified non-land orders (B01).

Final branch counts from `python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-MILITARY-RESERVATION.json --hints`:

| Branch | Members | Lead | What it covers |
|---|---:|---|---|
| B01 | 15 | open | Not land reservations (Saturday hours, Civil Service Rules, Marine Corps duties, ship seizure, harbors, camps, Coast Guard prisoners) |
| C01-C25 | 30 | no | Ended by a later member order that names them |
| B09 | 1 | no | EO 5254: revocation plus an entry schedule that ran out on its own terms |
| B10 | 9 | no | Revokes or amends another order only |
| B11 | 55 | no | Restores, relinquishes or disposes of land, with no continuing interest |
| B12 | 17 | open | Restoration or relinquishment that keeps a reversion, retained tract or reserved right (outside the Philippines and Canal Zone) |
| B20 | 52 | no | Philippine reservations |
| B21 | 12 | no | Canal Zone reservations |
| B30 | 25 | open | Hawaii reservations |
| B31 | 18 | open | Alaska reservations |
| B32 | 5 | open | Puerto Rico reservations |
| B33 | 77 | open | Continental reservations, ranges and departmental transfers |
| B99 | 0 | open | Catch-all |

By WPA family hint the members are: military_reservation 177, other 66, land_withdrawal 51, emergency_war 14,
civil_service_rules 3, indian_reservation 3, canal_zone 2. The engine reports no contradiction between any lead and a
held later-event edge.

## (a) How members end or persist

**Own terms: an order that only revokes, amends, restores or relinquishes (M1).** Many members do one thing: revoke
or correct an earlier order, exclude land from a reservation and restore it to the public domain or to the
government of a territory or of the Philippines, or place reservation lands under the Secretary of the Interior for
disposal. Under the owner's rule, an order that only revokes, restores or amends another order is spent on issue as
a command. The date is the order's date. The doctrine applies this only when the order's text shows no continuing
clause: no reversion (a right for the land to return to the United States if a condition fails), no tract "retained"
for military use, no reserved water or right-of-way, no purpose restriction such as "for road purposes", no new
reservation of the same or other lands, and no redefinition of the remaining reservation's boundaries ("so that the
reservation will include all public lands, and those only, within..."). An order that redefines what remains is
treated as a reservation order, because the remaining reservation then rests on its description. Amendments that
substitute a corrected land description (for example EO 5044 and EO 5119) are treated as spent under the owner's
rule; the reservation they describe lives or ends with the order they amend.

**Statute: relinquishment under the Act of July 5, 1884 (M2).** Section 1 of that Act (23 Stat. 103) directs the
President, when reservation lands have become useless for military purposes, to place them under the Secretary of
the Interior for disposition. An order made under it ends the military reservation over the lands it names; later
sale or entry happens under the statute and the land laws. Four members show that such a transfer could be undone
before disposal: EO 1011 vacated EO 803 (Fort Keogh), EO 2377 vacated EO 1422 (Fort Brown), EO 2563 vacated EO 1279
(Fort Ringgold), and EO 636 rescinded EO 372-B as amended by EO 456 (Fort St. Michael). For those members the end is
the vacating order (branches C09, C16, C23, C24), not the transfer's own date.

**Later instrument naming the member (M3).** A later order that revokes, vacates, rescinds or supersedes a member by
number or date, or that places all of the member's lands under the Interior Department, ends it on the later order's
date. The doctrine uses only later orders whose text the project holds (23 of the 25 are members of this family; EO 7320,
a refuge order, and EO 9293 of 1943 are not), so each lead can be checked against a phrase in a held file. The pairs are:

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

**Class event: Philippine independence (M4).** Section 10(a) of the Philippine Independence Act (Act of March 24,
1934, 48 Stat. 456, 463) required the President, on the July 4 after ten years of the Commonwealth, to surrender all
U.S. possession, jurisdiction, control or sovereignty over the Islands, "including all military and other
reservations of the Government of the United States in the Philippines (except such naval reservations and fueling
stations as are reserved under section 5)". Section 10(b) left naval reservations and fueling stations "in its
present status" pending negotiation, and a joint resolution of June 29, 1944 (58 Stat. 626) let the President
withhold or acquire further bases. Proclamation 2695 of July 4, 1946 (60 Stat. 1352) made the surrender "subject to
the reservations provided for in the applicable statutes". Article I of the Treaty of General Relations, which
entered into force on October 22, 1946 (61 Stat. 1174), then surrendered all remaining U.S. rights of possession,
supervision, jurisdiction, control or sovereignty, "except the use of such bases ... as the United States of America,
by agreement with the Republic of the Philippines, may deem necessary to retain". From that date no U.S.
reservation of Philippine land by executive order could operate; U.S. use of Clark, Subic and other retained bases
rested on the Military Bases Agreement of 1947, a new instrument. The date rule is an interval: from the order's
date to 1946-10-22, ending on July 4, 1946 for reservations the proclamation surrendered and earlier if a later order
revoked or restored the lands. If the owner instead treats use under the 1947 agreement as a continuation of the
reserving order, the end moves to each base's turnover, which still falls before the cutoff; the lead stays `no`.

**Class event: end of the Canal Zone (M5).** The Panama Canal Treaty (signed September 7, 1977; 1280 U.N.T.S. No.
21086) came into force on October 1, 1979. On entry into force it terminated and superseded the Isthmian Canal
Convention of 1903 (art. I(1)(a)), and Panama reassumed plenary jurisdiction over the former Canal Zone (art. XI).
The Panama Canal Act of 1979 took effect the same day (sec. 3304, 93 Stat. 500) and provides that "Canal Zone" in U.S.
law is deemed to refer to the areas and installations in the Republic of Panama made available to the United States
under the Treaty (sec. 3(b)(1), 93 Stat. 455). The reservations the President had set apart within the Zone, or on
adjacent lands whose use the 1903 Convention granted (EO 2825), had no object after that date; later U.S. military
use of defense sites rested on the Treaty and its Article IV implementing agreement, and the Treaty terminated at
noon on December 31, 1999. The date rule is an interval from the order's date to 1979-10-01 (or to 1999-12-31 if the
owner treats defense-site use as continuation; the lead stays `no` either way).

**Hawaii statehood (M6, lead only).** Section 5(c) of the Hawaii Admission Act (Pub. L. 86-3, 73 Stat. 4, 5) kept as
U.S. property all lands set aside for federal use by Act, proclamation or executive order on the date of admission;
section 5(e) required each agency to report within five years and the President to convey to the State land no
longer needed. The Act neither ends nor confirms any one order; it tells the reader where to look.

**Later revocations, Public Land Orders, transfers, conveying statutes and surplus disposals (M7, lead only).** Most
continental and Alaska reservations ended, if they ended, through a later executive order or Public Land Order
(the Interior Department's instrument for withdrawals and revocations after 1942), a statute conveying the named
reservation, or disposal as surplus property. These reach members tract by tract, so they decide nothing for the
class. In Alaska, the blanket relinquishments EO 4131 (1925) and EO 7127 (1935) and the cemetery order EO 7049 (1935)
are themselves members; they list reservations by name with exceptions (post cemeteries, Signal Corps tracts, Alaska
Road Commission sites), so matching them to earlier members is a reading task for a later version.

**Continuity only (M8).** The Federal Land Policy and Management Act of 1976 repealed, from October 21, 1976, the
President's implied authority to make withdrawals and the withdrawal sections of the Pickett Act of June 25, 1910
(36 Stat. 847), the statute under which many National Guard ranges in this family were reserved (sec. 704(a), 90 Stat.
2792). Section 701(c) (90 Stat. 2786) kept "all withdrawals, reservations, classifications, and designations in
effect as of the date of approval of this Act" in full force until modified. A repeal of authority with a savings
clause is not an end. The Engle Act of February 28, 1958 (72 Stat. 27; 43 U.S.C. 155-158) requires an Act of Congress
for defense withdrawals over 5,000 acres made on or after that date; it is prospective and does not reach these
orders.

## (b) Primary sources

Held sources (text file in the repository, opened, pin phrase found, sha256 of the file at `held_path`):

| ID | Citation | Held path | sha256 | Pin |
|---|---|---|---|---|
| S-TM | Philippine Independence Act, Mar. 24, 1934, ch. 84, secs. 5, 10, 48 Stat. 456, 459, 463 | `jobs/astra-source-retention/output/pages/2900efa1.../selected-pages.txt` | 636fc71799d9391051b56054be9bb9ce42ab58d46fa0e458d36c9fc465386f70 | "including all military and other reservations" |
| S-P2695 | Proclamation 2695, July 4, 1946, 60 Stat. 1352, 1353 | `jobs/astra-source-retention/output/pages/c493d8ef.../selected-pages.txt` | 5fdd773800d1210fe04c363d9d4839adc86794bf0b3cded9ba17065b8e1127c1 | "hereby withdraws and surrenders" |
| S-PCA | Panama Canal Act of 1979, Pub. L. 96-70, secs. 3(b)(1), 1504, 3304, 93 Stat. 452, 455, 488, 500 | `jobs/source-ladder/output/texts/queue_EO_9293_Panama_Canal_..._8d101fb40b.txt` | 2128a6390e37a43b60c721f18c5cd3bfb281b65e4e21d3cf0d95feca3680e10f | "shall be deemed to refer to the areas and" |
| S-FLPMA | FLPMA, Pub. L. 94-579, secs. 701(c), 704(a), 90 Stat. 2743, 2786, 2792 | `jobs/astra-source-retention/output/pages/3949c2ad.../selected-pages.txt` | e14185c661715326d9306d39413ea761527b18a9a9335ebcab70e298e459a786 | "in effect as of the date of approval of this Act shall remain in full" |
| S-EO… | 25 later orders used in branches C01-C25 (EO 683, 636, 1011, 1282, 2143, 2377, 2405, 2563, 3067, 3130, 3313-A, 3402, 3418, 3497, 3514, 3952, 4047, 4062, 5240, 5254, 5715, 7320, 7387, 7407, 9293) | each order's text under `jobs/pinakes-proquest-ingest`, `jobs/wikisource-texts`, `jobs/app-executive-orders` or `jobs/ofr-compilations` | listed per source in the JSON | listed per source in the JSON |

Full held paths, hashes and pins are in the JSON `sources` array; a script re-read every held file, recomputed its
sha256 and found every pin on 2026-11-05. The texts of the later member orders are transcriptions or page-scan OCR,
not authenticated originals, and some pins carry OCR errors exactly as the file has them (for example "Exeentive
Order No. 2772" and "February io, 1915").

Sources read on the web and not held (each is in `research/pothier/work/PD-MILITARY-RESERVATION/FETCH_PROPOSED.jsonl`):

| ID | Citation | URL | Used for |
|---|---|---|---|
| S-TGR | Treaty of General Relations, July 4, 1946, art. I, 61 Stat. 1174 (in force Oct. 22, 1946) | https://www.govinfo.gov/link/statute/61/1174 | B20 upper bound |
| S-JR1944 | Joint Resolution of June 29, 1944, ch. 322, sec. 2, 58 Stat. 626 (22 U.S.C. 1392) | https://www.govinfo.gov/link/statute/58/626 | B20 explanation of withheld bases |
| S-PCT | Panama Canal Treaty, 1977, arts. I, II, IV, XI, 33 U.S.T. 39, T.I.A.S. 10030, 1280 U.N.T.S. No. 21086 | https://treaties.un.org/doc/Publication/UNTS/Volume%201280/volume-1280-I-21086-English.pdf | B21 date and termination of the 1903 Convention |
| S-1884 | Act of July 5, 1884, ch. 214, sec. 1, 23 Stat. 103 | https://www.govinfo.gov/content/pkg/STATUTE-23/pdf/STATUTE-23-Pg103.pdf | B11 relinquishments |
| S-HAA | Hawaii Admission Act, Pub. L. 86-3, sec. 5(c), 5(e), 73 Stat. 4, 5-6 | https://www.govinfo.gov/content/pkg/STATUTE-73/pdf/STATUTE-73-Pg4.pdf | B30 lead |
| S-ENGLE | Engle Act, Pub. L. 85-337, 72 Stat. 27 (43 U.S.C. 155-158) | https://www.govinfo.gov/content/pkg/STATUTE-72/pdf/STATUTE-72-Pg27.pdf | M8 continuity |
| S-MBA1947 | Military Bases Agreement with the Philippines, Mar. 14, 1947, 43 U.N.T.S. No. 673 (Statutes at Large citation not verified) | https://treaties.un.org/doc/Publication/UNTS/Volume%2043/volume-43-I-673-English.pdf | B20 gap only; not read |

The `no` leads on B20 and B21 cite these unheld sources alongside held ones; the engine therefore adds a "not yet
held" gap to each such lead until the treaty texts are acquired.

## (c) Decision procedure

Branches are tried in order; the first whose conditions all hold decides. "Summary" means the WPA 1944 summary;
"place screen" means a regex on the summary or the title, not the order text, because about half the held texts are
compilations or page scans that can run into a neighbouring order.

1. **B01, open (out of family).** The title, summary or text names a Saturday four-hour workday, the Civil Service
   Rules, the duties of the Marine Corps, the seizure of German vessels, the closing of harbors to foreign vessels,
   the construction of "military camps", or Coast Guard prisoners. These orders belong to the civil-service, pay or
   war families. Gap: reassignment; several Saturday-hours orders were revoked in part by later Saturday-hours
   orders that revoke "all Executive or other orders in conflict herewith", which needs reading.
2. **C01 to C25, no (ACT).** The member's identifier is one of the targets in the table under (a). Date: the later
   order's date. Gap: the later order's held text is a transcription or OCR.
3. **B09, no (TERM).** EO 5254 only, confirmed by the phrase "for a period of 91 days beginning with the 63rd day".
   Date 1930-06-02, the last day of the stated preference period.
4. **B10, no (TERM).** The summary begins with a citation of an earlier order ("E. O. ..."), says that order is
   revoked or amended, and neither the summary nor the text adds a new reservation, a placing of lands under the
   War or Navy Department, a continuation in reservation, an enlargement or a new boundary. Date: order date. Gap:
   the summary could omit a second operative clause.
5. **B11, no (TERM).** The summary says the order restores, diminishes, abolishes, eliminates, excludes, relinquishes
   to a territorial or Philippine government, or places lands under the Interior Department for disposal; the
   summary contains no verb of new reservation (verbs describing an earlier reservation, such as "formerly
   reserved", are excluded from that test); and the text contains no retained-interest phrase, no boundary
   redefinition and no new "hereby reserved / set apart / withdrawn" clause. Date: order date. Gaps: a vacatur by a
   non-member order would not be detected; OCR may hide a proviso.
6. **B12, open.** As B11, but the text keeps a reversion, a retained tract, a reserved right, a purpose restriction
   or an authority to reserve again, and the place screen is not the Philippines or the Canal Zone. What decides it:
   current title and use of the land, and for Hawaii the section 5 conveyance records.
7. **B20, no (ACT).** The place screen finds the Philippine Islands (names of the Islands, provinces and posts) and not
   the Canal Zone. Date: interval from order date to 1946-10-22. Gaps: the 1946 treaty is unheld; the owner's view on
   base use under the 1947 agreement; place-screen errors.
8. **B21, no (ACT).** The place screen finds the Canal Zone (C.Z., Canal Zone, Balboa, Coco Solo, Fort Amador and
   other named posts, or the Republic of Panama). Date: interval from order date to 1979-10-01. Gaps: the 1977 treaty
   is unheld; the owner's view on defense-site use to 1999.
9. **B30, open.** The place screen finds Hawaii. What decides it: federal real property and installation records,
   and Hawaii Admission Act section 5(e) conveyances.
10. **B31, open.** The place screen finds Alaska. What decides it: matching to EO 4131, EO 7127, EO 7049 and later
    Public Land Orders, statehood selections and Alaska Native Claims Settlement Act conveyances.
11. **B32, open.** The place screen finds Puerto Rico. What decides it: later transfers to the insular government and
    federal property records.
12. **B33, open.** Every remaining member: continental reservations, National Guard and militia ranges (33 of the
    77), departmental transfers to the Treasury, Veterans' Bureau, Agriculture or Navy (16), and mixed orders that
    both restore and reserve. What decides it: a revoking order or Public Land Order naming the order or its lands
    (for `no`), or a statute or current BLM withdrawal record or DoD real property record showing the lands still
    reserved under it (for `yes`).
13. **B99, open.** Catch-all; no member reaches it.

## (d) Members the procedure cannot decide

157 members stay `open`:

- **77 continental, 25 Hawaii, 18 Alaska and 5 Puerto Rico members (B30-B33)** reserve, enlarge, redefine or transfer
  land and have no class-wide end. Some may still be federal military land (for example the Fort Sill
  enlargement, EO 685; the Fort Bliss target ranges, EO 1450 and EO 2280; Fort Shafter, EO 4545); many others were
  plainly ended later by Public Land Orders or conveyances. Neither can be shown from the fields held. The missing
  field is a current-law or land-record predicate per tract (BLM MLRS/LR2000 withdrawal status, DoD real property
  inventory, or the revoking instrument).
- **17 restorations with retained interests (B12)**: the restoring command is spent, but a reversion, a retained
  tract or a reserved right may still operate. What decides each is the later history of that interest.
- **15 non-land orders (B01)**: outside this family's mechanisms.

Members that a reviewer should expect to be close calls: EO 220 and EO 3310 (Puerto Rico restorations held open
because the summary or text did not pass the restoration screens); EO 2521 and EO 4179-A (Hawaii diminutions that
also redefine or re-withdraw, held open); EO 3300 (a Puerto Rico conveyance "for school purposes", held open by the
purpose-restriction screen); and the B20 place screen, which depends on WPA summaries naming a Philippine place.

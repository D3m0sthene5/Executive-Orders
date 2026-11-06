# PD-CS-RULES: amendments of the Civil Service Rules and related class orders (1872-1936)

Doctrine version 3, 2026-11-05. The doctrine covers the 540 orders typed `cs_rules_amendment`
(`research/pothier/work/PD-CS-RULES/MEMBERS.csv`). Its machine form is `research/pothier/doctrines/PD-CS-RULES.json`.
It applies the coordinator rulings in `research/pothier/COORDINATOR_RULINGS.md` (P1-P8).

## Conclusions

The doctrine proposes a `no` lead for 396 of the 540 members and leaves 144 `open`. It proposes no `yes` lead. On
the branches the held sources support, no member's own command was in force on 2026-10-14. The present Civil
Service Rules (5 CFR parts 1-10, from Executive Order 10577 as amended) and the excepted-position schedules (5 CFR
part 213, regulations of the Office of Personnel Management, OPM) rest on later instruments.

The 396 `no` leads rest on three grounds.

1. **Pure amendments: 377 members (branches B12, B13, B14a, B14, B14s, B15).** In each of these orders, amending is
   the only operative content. The order changes the text of the Civil Service Rules, of Schedule A or B, of
   another executive order, or of regulations the President prescribed. Under ruling P2, the amending text merges
   into the amended instrument (the parent) when the order issues, and the order keeps no command of its own. The
   lead is `no`, with basis `TERM` and the amending order's own date. Every such lead carries the P2 disclosure:
   "its text continues as part of the parent until the parent ends; the parent's lifecycle carries it". The parents
   fared as follows:
   - **Amendments of the rules made before 1896 (B12):** the parent rules were revoked on May 6, 1896.
   - **Amendments of the 1896 rules (B13):** the parent ended on April 15, 1903.
   - **Amendments of the 1903 rules (B14a, B14, B14s):** the parent, EO 209, is itself `open`.
2. **Express revocation of a described class: 9 members (B01, B09, B12b).**
   - EO 89 (1896) "makes and promulgates the following rules and revokes all others". That revocation ended the rule
     sets of 1872-1895 no later than May 6, 1896.
   - EO 209 promulgated its rules "in lieu of those promulgated May 6, 1896, and the amendments thereof". That ended
     EO 89 on April 15, 1903.
3. **Named revocations and pure revocations: 10 members.**
   - **Seven members (B03-B05, B05b-B05d)** were revoked, rescinded or superseded as a whole by a later order that
     names them by number or by date: EO 179, 2985, 3807, 2570, 3471, 163 and 1142.
   - **Three members only revoke another order**, so they are spent on issue under ruling P1 (B10).

The 144 `open` members fall into these groups:

| Group | Members | Branch |
|---|---|---|
| EO 209, the 1903 rules | 1 | B02 |
| Special rules of 1897-1902 | 3 | B07 |
| Classification and covering-in orders | 35 | B08, B16 |
| Amendments whose own text adds a further provision | 21 | B15x |
| Amendments whose text does not confirm the amendment | 11 | B18 |
| Separate regulation sets | 9 | B17 |
| Members of other families | 64 | B06p, B11, B19, B97, B99 |

EO 209 is open because only whole-text restatements followed it, and none of them names it (ruling P3).

The engine flags 34 members as contradicted, all with the flag "acted on after lead end". In 27 of them, the
flagged edge is a later order amending text that the member had inserted. That is an event of the parent, as ruling
P2 expects, and it does not change the lead. In the other 7, plus one edge on a member of the first group, the edge
is a false number match. Section (c) lists them.

## Terms used

- **Civil Service Rules.** The rules the President makes under the Civil Service Act of January 16, 1883
  (22 Stat. 403) and Revised Statutes section 1753 (now 5 U.S.C. 3301-3302). They govern examination,
  appointment, transfer and removal in the classified (competitive) service. The census counts several general
  revisions as executive orders: EO 89 of May 6, 1896, EO 209 of March 20, 1903, and EO 7915 of June 24, 1938.
- **Schedule A.** The list of positions excepted from examination. It was part of the rules from EO 209 (1903).
- **Schedule B.** The list of positions that may be filled by noncompetitive examination. It was added by EO 1180 of
  March 23, 1910. Both schedule names are standard terms.
- **Special rule.** A term used at the time for a freestanding rule promulgated beside the numbered rules, for
  example a rule letting a single named vacancy be filled without examination.
- **Class order.** A label of this project. It means an order that places a group of positions (often with their
  present holders) in or out of the classified service, or excepts them, without changing the text of the rules.
- **Merged into the parent on issue.** The rule for amending instruments under ruling P2. The amending text becomes
  part of the instrument it amends (the parent) and lives or ends with that instrument. The amending order keeps no
  command of its own.
- **Whole-text restatement "to read as follows".** An amending clause that replaces the entire text of an
  instrument. Under ruling P3, such a restatement does not end an order it does not name. It is recorded only as a
  disclosed candidate end.

## (a) Mechanisms

**M1. A pure amendment merges into its parent (own terms, ruling P2).** M1 applies only when the member's own
operative text shows that amending is its only content. The amending order has no command of its own after issue,
and later orders that amend the text it inserted are events of the parent. Lead: `no`, basis `TERM`, the order's own
date, kind `merged_into_parent_on_issue`. The machine checks "only content" in three steps:

1. **Summary.** The WPA summary shows nothing but an amendment. It mentions no waiver, special rule, promulgation,
   prescription, construction or extension.
2. **Amending words.** The text uses amending words in operative form, for example "is hereby amended", "strike
   out", "stricken out", "by adding", "be inserted", "is hereby rescinded" or "to read as follows". Title words such
   as "Amending" and the Wikisource note "Amends Executive Order ..." do not count. A scan of every member decided
   this way confirmed that the amending words occur in the operative body.
3. **No further provision.** The text carries none of the markers of a further provision:
   - present or continued incumbents or occupants;
   - "with its (their) incumbents";
   - "now holding";
   - "now in the service under the provisions";
   - "shall be continued in office";
   - "it is further ordered";
   - "already employed";
   - "the effect of this (the above, the foregoing) amendment" or "... order";
   - status given to persons;
   - "shall not be construed to require".

   A text that is only part of the order ("not the full order text") also fails this step.

The marker list came from a pattern scan of every text decided this way. A further provision written in other words
would still escape it. Members that show a marker go to `open` (B15x), and members whose text does not confirm the
amendment go to `open` (B18).

**M2. A pure revocation is spent on issue (own terms, ruling P1).** M2 applies to an order whose own text only
revokes or rescinds another order ("hereby revoked", "hereby rescinded"). The date is the order's own date.

**M3. EO 89 revoked all earlier rules (express class, ruling P3).** EO 89 was approved May 6, 1896. It "makes and
promulgates the following rules and revokes all others". The words expressly revoke a described class: every other
civil service rule. A member belongs to that class when two things are true:

- it is dated before May 6, 1896;
- its own text shows that it prescribes, extends, approves or amends civil service rules made by the President
  under R.S. 1753 and the 1883 Act, the powers EO 89 itself recites. For EO 15, whose text is an unread scan, the
  WPA summary stands in for the text.

Date: an interval ending 1896-05-06, because the member may have ended earlier.

**M4. EO 209 displaced the 1896 rules (express class, ruling P3).** EO 209 was signed March 20, 1903. It promulgated
its rules "in lieu of those promulgated May 6, 1896, and the amendments thereof", and it was "Approved, to take
effect on and after April 15, 1903." The words name EO 89 by its date. Date: 1903-04-15, the stated effective date,
not the signing date.

**M5. Whole-text restatements give only a candidate end (ruling P3).** Four later orders restated the rules:

- **EO 7915 (June 24, 1938):** "the Civil Service Rules are hereby amended, effective February 1, 1939, to read as
  follows". Its Rule II sec. 3(a) continued Schedules A and B for the time being.
- **EO 8043 (January 31, 1939):** "Schedules A and B of the Civil Service Rules are hereby amended to read as
  follows", effective February 1, 1939.
- **EO 9830:** restated the rules again, effective May 1, 1947, and revoked EO 7915 by name but not EO 209.
- **EO 10577:** restated the rules again, with effect from 1955-01-23 ("the first Sunday after the sixtieth day
  after" November 22, 1954).

None of these orders names EO 209 or any member, and none expressly revokes a class that includes them. The
1939-02-01 restatement is therefore recorded as a disclosed earlier candidate end for EO 209, and it appears in the
gaps of the B14 branches. Two other orders do not end anything here:

- EO 7916 (June 24, 1938), sec. 9, only announced that the schedules would be superseded later.
- EO 8743 (1941) concerns EO 8044.

**M6. Whole-order revocation by a later order that names the member (later instrument).** Each of these orders names
the member by number or by date and revokes, rescinds or supersedes it as a whole:

- **EO 250 (February 5, 1904)** revoked "The special rule of July 3, 1902", which is EO 179.
- **EO 3014 (November 30, 1918)** rescinded "The Executive order of October 28, 1918", which is EO 2985.
- **EO 5459 (October 4, 1930):** "This order supersedes Executive Order No. 3807 of March 15, 1923."
- **EO 3054 (March 2, 1919):** "The Executive Order of April 2, 1917, requiring the assent of the head of a
  department or office to an employee's examination or certification under the civil-service rules, is hereby
  rescinded." The order of April 2, 1917 is EO 2570.
- **EO 5007 (December 8, 1928):** "Executive Order No. 3471, issued May 21, 1921, authorizing the Civil Service
  Commission to extend ... the employments ... is hereby revoked."
- **EO 1514 (April 8, 1912):** "This order supersedes the Executive orders of January 31, 1902, January 25, 1906,
  and November 26, 1909, regarding the same general matter." Those orders are EO 163 (January 31, 1902) and EO 1142
  (November 26, 1909).

Date: the date of the naming order. No `no` lead rests on an edge marked `partial_`.

**M7. Continuity under later instruments (does not end or save any member).** The present rules (5 CFR parts 1-10)
and Schedule A (5 CFR 213.3102) carry the subject matter of the old rules forward. OPM republished 5 CFR 213.3102 at
47 FR 28902 (July 2, 1982), under 5 U.S.C. 3301-3302 and EO 12364. Where a present provision matches an old one in
substance, for example chaplains or positions to which the President appoints without Senate confirmation, it rests
on these later instruments.

**Rulings P7 and P8.** No held instrument abolishes by name the only subject of a member (P7). The class orders would
qualify only if the office that held their positions were abolished by name, and that evidence is listed under
(d). No member delegates a statutory power that later ceased (P8). No member is revoked by a revocation that takes
effect on a future event.

## (b) Primary sources

Pins are quoted with whitespace collapsed. The S4 pin begins after the OCR soft hyphen in "Sched- ules".

| Id | Source | Held | Pin |
|---|---|---|---|
| S0 | The member's own order text (ruling P6, `member_text`) | Recorded on each lead (path, sha256, grade) | The amending, revoking or rule-making words the branch tests |
| S1 | EO 89, approved May 6, 1896; Richardson, *Messages and Papers*, vol. IX, pp. 701-711 (GPO 1898) | `jobs/richardson-volumes/output/texts/RICH_IX/EO_89.txt`, sha256 623158ef6cb0bf313f1bbe65d687b953cf9565ee6c4f9bb0a967245461e4f411 | "the President hereby makes and promulgates the following rules and revokes all others"; "Approved , May 6 , 1896" |
| S2 | EO 209, March 20, 1903 (Wikisource rev. 13537757) | `jobs/wikisource-texts/output/texts/EO_209.txt`, sha256 131c53601214343ec8d9a0cee75e4fe45e128a227c056fb811fec91dc170322a. This is a mirror transcription; the official print is to be acquired. | "the President promulgates the following rules in lieu of those promulgated May 6, 1896, and the amendments thereof"; "Approved, to take effect on and after April 15, 1903." |
| S3 | EO 7915, June 24, 1938, 3 FR 1519 (FR of June 28, 1938) | `jobs/fr-originals/output/texts/EO_7915.txt`, sha256 28d52b2696b5b5580720b2243d45d204d7819df6cb1bfba81fd1cbfba8398913 | "the Civil Service Rules are hereby amended, effective February 1, 1939, to read as follows"; "Schedules A and B of the civil service rules are continued as a part of the said rules as amended by this order"; "or by executive orders covering groups of employees with their positions into the competitive classified service" |
| S4 | EO 8043, January 31, 1939, 4 FR 493 | `jobs/fr-originals/output/texts/EO_8043.txt`, sha256 2c28d785421e182f05bb1f95c4372e8d9b557c83ccbf47b2eed8c03ef9087edf | "of the Civil Service Rules are hereby amended to read as follows"; "This order shall be effective February 1, 1939." (printed immediately before "[No. 8043]") |
| S5 | EO 9830, February 24, 1947, 12 FR 1259 | `jobs/fr-originals/output/texts/EO_9830.txt`, sha256 b519c570558edc86d21ec7b9228252fd61d4f17e36b95cb8f16ab70ed879d3e3 | "it is hereby ordered as follows, effective May 1, 1947"; Part III "No. 7915 of June 24, 1938." |
| S6 | EO 10577, November 22, 1954, 19 FR 7521 | `jobs/fr-originals/output/texts/EO_10577.txt`, sha256 f698f5558d53ee2ba1e8480796e824c9c71513bc613a04530a93fc9ac84d6b5a | "Section 101. The Civil Service Rules are hereby amended to read as follows"; "unless and until they are removed therefrom by the Commission" |
| S7 | EO 250, February 5, 1904 (Wikisource) | `jobs/wikisource-texts/output/texts/EO_250.txt`, sha256 476ef34649850483379ee0f4e0d7ac643e1a0aa27d9575aa69cb571554aad6ab | "The special rule of July 3, 1902, rendering certain persons who were in the employ of the United States in the military government of Cuba" ... "is hereby revoked" |
| S8 | EO 3014, November 30, 1918; Civil Service Commission report for FY1919, p. 104 (https://www.govinfo.gov/content/pkg/SERIALSET-07742_00_00-002-0416-0000/pdf/SERIALSET-07742_00_00-002-0416-0000.pdf, PDF page 140) | `jobs/csc-annual-reports/output/texts/EO_3014.txt`, sha256 012481a62c53cdd383b3465018a389c48f147124686984b646969fc6d6a4613c | "The Executive order of October 28, 1918, ... is hereby rescinded." |
| S9 | EO 5459, October 4, 1930 (American Presidency Project transcription) | `jobs/app-executive-orders/output/texts/executive-order-5459-placing-the-position-shipping-commissioner-the-classified-service.txt`, sha256 9f0cc5fc83f2312371b1eefcbefab8a907907b37cc17f0e3485b53f100d75b60 | "This order supersedes Executive Order No. 3807 of March 15, 1923." |
| S10 | 5 CFR 213.3102 (eCFR on 2026-11-04) | `jobs/theophilus-sources/output/texts/cfr-t5-213.3102.txt`, sha256 6d76e9a83589b93796a7e826428036436296ba25f69d68f2346418cfad140e77 | "[47 FR 28902, July 2, 1982]"; "(5 U.S.C. 3301, 3307, 8337(h); 5 U.S.C. 3301, 3302; E.O. 12364, 47 FR 22931)" |
| S12 | EO 3054, March 2, 1919 (Wikisource) | `jobs/wikisource-texts/output/texts/EO_3054.txt`, sha256 799ebc114fdcc6c4498bee9db51d1db04ed10579901d6fa1fcf5586b33a82aa2 | "The Executive Order of April 2, 1917, requiring the assent of the head of a department or office to an employee's examination or certification under the civil-service rules, is hereby rescinded." |
| S13 | EO 5007, December 8, 1928; Civil Service Commission report for FY1929, p. 79 (https://www.govinfo.gov/content/pkg/SERIALSET-09300_00_00-002-0207-0000/pdf/SERIALSET-09300_00_00-002-0207-0000.pdf, PDF page 83) | `jobs/csc-annual-reports/output/texts/EO_5007.txt`, sha256 657d1fbe8b59407a43ad5a1840f87ddb9d67bfdac221eae9ad32246221d75860 | "Executive Order No. 3471, issued May 21, 1921" ... "is hereby revoked" |
| S14 | EO 1514, April 8, 1912 (Wikisource) | `jobs/wikisource-texts/output/texts/EO_1514.txt`, sha256 2f1fa74cecd7c4cdf970a3c1f39be908e91844c8094832930ad8feda4480aec0 | "This order supersedes the Executive orders of January 31, 1902, January 25, 1906, and November 26, 1909, regarding the same general matter." |

`research/pothier/work/PD-CS-RULES/FETCH_PROPOSED.jsonl` proposes four Civil Service Commission reports:

- FY1903, for the official print of EO 209;
- FY1896, for EO 89;
- FY1939, to confirm the 1939 effective date and to show whether the Commission treated the 1903 rules as ended;
- FY1904, for EO 250.

No held 1938-1939 Federal Register order postpones EO 7915 or EO 8043. EO 8044 postpones parts of EO 7916 only.

## (c) Decision procedure

Branches are tried in order, and the first branch whose conditions all hold decides. The counts come from
`python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-CS-RULES.json`: 540 members, 396 decided, 34
contradicted.

Three tests recur in the table:

- **CSR_START:** the summary begins with "Civil Service Rule(s)".
- **AMEND_SUM:** an amending verb appears in the summary.
- **Purity screen:** steps 2 and 3 of M1.

| Branch | What it catches | Count | Lead | Lead kind and basis | Date rule |
|---|---|---|---|---|---|
| B01 | EO 89 | 1 | no | `ended_by_express_class_instrument`; ACT: EO 209 "in lieu of those promulgated May 6, 1896, and the amendments thereof" | fixed 1903-04-15 |
| B02 | EO 209 | 1 | open | `whole_text_restatement_only`: no instrument names it | none (candidate 1939-02-01 in gaps) |
| B03 | EO 179 | 1 | no | `revoked_by_named_order`; ACT: EO 250 | fixed 1904-02-05 |
| B04 | EO 2985 | 1 | no | `revoked_by_named_order`; ACT: EO 3014 | fixed 1918-11-30 |
| B05 | EO 3807 | 1 | no | `revoked_by_named_order`; ACT: EO 5459 | fixed 1930-10-04 |
| B05b | EO 2570 | 1 | no | `revoked_by_named_order`; ACT: EO 3054 | fixed 1919-03-02 |
| B05c | EO 3471 | 1 | no | `revoked_by_named_order`; ACT: EO 5007 | fixed 1928-12-08 |
| B05d | EO 163, EO 1142 | 2 | no | `revoked_by_named_order`; ACT: EO 1514 | fixed 1912-04-08 |
| B06p | one-person orders (15 listed ids) | 15 | open | `other_family_one_person`: PD-CS-ONE-PERSON (ruling P4) | none |
| B07 | special rules of 1897-1902 | 3 | open | survival past 1903 unsettled | none |
| B08 | directions to classify under section 6 of the 1883 Act (text test) | 3 | open | `class_order_coverage` | none |
| B09 | before 1896-05-06: rule sets prescribed, extended or approved, text mentions rules | 7 | no | `ended_by_express_class_instrument`; ACT: EO 89 "revokes all others" | interval from order date to 1896-05-06 |
| B10 | pure revocations (summary "E. O. ... revoked/rescinded"; text "hereby revoked/rescinded") | 3 | no | `spent_on_issue`; TERM (P1) | order date |
| B11 | waivers and suspensions not framed as amendments | 5 | open | `other_family_waiver` | none |
| B12 | before 1896-05-06: CSR_START, AMEND_SUM, purity screen | 31 | no | `merged_into_parent_on_issue`; TERM; parent revoked by EO 89 on 1896-05-06 | order date |
| B12b | before 1896-05-06: text shows a rule promulgated or replaced, not a pure amendment | 1 | no | `ended_by_express_class_instrument`; ACT: EO 89 | interval from order date to 1896-05-06 |
| B13 | 1896-05-06 to 1903-03-19: CSR_START, AMEND_SUM, purity screen | 53 | no | `merged_into_parent_on_issue`; TERM; parent EO 89 ended 1903-04-15 | order date |
| B14a | EO 253 (signed January 27, 1904; census date 1904-02-17) | 1 | no | `merged_into_parent_on_issue`; TERM; parent EO 209 open | fixed 1904-01-27 |
| B14 | 1903-04-15 to 1938-06-23: CSR_START, AMEND_SUM, purity screen | 264 | no | `merged_into_parent_on_issue`; TERM; parent EO 209 open | order date |
| B14s | EO 5657 and EO 5662: WPA summaries run together with neighbouring entries; official texts are pure amendments | 2 | no | `merged_into_parent_on_issue`; TERM; parent EO 209 open | order date |
| B15 | pure amendments of another EO or of presidential regulations | 26 | no | `merged_into_parent_on_issue`; TERM | order date |
| B15x | amendments whose text shows a further provision | 21 | open | `amendment_with_further_provision` | none |
| B16 | class orders: positions classified, covered in, placed outside or excepted | 32 | open | `class_order_coverage` | none |
| B17 | separate regulation sets prescribed, extended or approved | 9 | open | `separate_regulation_set` (PD-ADMIN) | none |
| B18 | amendment or construction not confirmed by the operative text, or dated between EO 209's signing and its effect | 11 | open | `amendment_text_unconfirmed` | none |
| B19 | EO 5514 and EO 5977 (office closings) | 2 | open | `other_family_closing` (PD-ADMIN) | none |
| B97 | WPA hint `emergency_war` | 7 | open | `other_family_war_emergency` (PD-WAR-EMERGENCY) | none |
| B99 | catch-all | 35 | open | `other_family_admin` (PD-ADMIN) | none |

An amendment dated between 1903-03-20 and 1903-04-14 could belong to either EO 89 or EO 209, so it goes to B18. No
current member falls in that window.

Gaps carried by every member on a branch:

- **All pure-amendment branches (B12 through B15).** Each carries three gaps:
  - the P2 disclosure, "its text continues as part of the parent until the parent ends; the parent's lifecycle
    carries it";
  - the limits of the purity screen described under M1;
  - the risk that a compiled transcription runs into a neighbouring order.
- **B14a, B14 and B14s** also carry the disclosed candidate end for the parent EO 209: EO 7915 and EO 8043, effective
  1939-02-01.
- **B14** also lists the thirteen decided members whose census date is a year only, so their lead date is a year.
  On B14 they are EO 508, 689, 933, 1127, 1128, 1247, 1408, 1829, 2700, 2701, 3908A and 4507; on B15, EO 3170. For
  several of them the held text gives the day: EO 689, September 23, 1907; EO 933, September 3, 1908.
- **B01 and B13.** EO 209 is held only as a mirror transcription.
- **B09 and B12b.** These carry the EO 89 member test, and EO 89 is held as a printed compilation.
  - EO 15 is an unread scan, so its membership in the class rests on its WPA summary: "Regulations governing
    classification of the Civil Service, prescribed Apr. 16, 1872, amended".
  - EO 17's scan is readable only in its closing lines: "extended to the several Federal offices at the city and
    in the customs district of B[o]ston".
- **B05b-B05d.** Each revoking text is held as a transcription or a report slice. EO 2570 and EO 3471 have the war
  family as their subject family, and EO 163 and EO 1142 have the administrative family. Their named revocations
  decide them whatever their family.

**Contradiction flags: 34, all "acted on after lead end".** None changes a lead.

Twenty-seven members are flagged by genuine later amendments of the text they inserted. Under ruling P2 these are
events of the parent, so they are consistent with the merger reading:

- **B13 (10):**
  - EO 119, amended by EO 120, 123, 124, 125, 131, 133, 137, 144, 146, 150, 157, 158, 159 and 166 (1899-1902);
  - EO 94, amended by EO 128, 140 and 156;
  - EO 127, amended by EO 129;
  - EO 128, amended by EO 136;
  - EO 133, amended by EO 155;
  - EO 140, amended by EO 152;
  - EO 146, amended by EO 150;
  - EO 151, amended by EO 161;
  - EO 152, amended by EO 153;
  - EO 166, amended by EO 187.
- **B14 and B14a (17):**
  - EO 1004, amended by EO 1467;
  - EO 1163, amended by EO 1189;
  - EO 1176, amended by EO 1180;
  - EO 1268, amended by EO 1289, 1328 and 1697;
  - EO 1289, amended by EO 1307;
  - EO 1470, amended by EO 1527;
  - EO 1769, amended by EO 1851;
  - EO 299, amended by EO 976;
  - EO 364, amended by EO 733;
  - EO 383, amended by EO 461;
  - EO 642, amended by EO 655;
  - EO 689, amended by EO 1246;
  - EO 748, amended by EO 1185;
  - EO 754, amended by EO 1180;
  - EO 785, amended by EO 1180;
  - EO 933, amended by EO 1268;
  - EO 253, amended by EO 1163.

Seven members are flagged only by false number matches:

- EO 8: EO 9427 cites "8 F.R.".
- EO 11: EO 9763 cites "11 F. R."; EO 12847 cites EO 11423.
- EO 56: EO 5132 and EO 5607 concern a Hawaii Arsenal parcel under a different order 56.
- EO 104: EO 2481 is the text of a 1916 rule ("term may be suspended"), not an act on EO 104.
- EO 105: EO 11097 amends EO 10501, which the OCR reads as "105Ô1".
- EO 129: EO 12340 is the Manual for Courts-Martial.
- EO 2054: EO 3641 concerns the Jefferson National Forest.

EO 119's edge from EO 12680 (1989) is also a false match, an OCR split of "11958". To regenerate the list, run
`decide` from `jobs/pothier/pothier.py` over the members and print each lead's `contradictions` together with the
member's `later_edges`.

Several held whole-order revocations of `no` members are also consistent with P2 (parent events), for example EO
1151 revoked by EO 1777, EO 1185 superseded by EO 1709 and 1714, EO 176 revoked by EO 204, and EO 3035 revoked by
EO 3075. EO 646 carries a `partial_revocation` edge from EO 1363, which is also an event of the parent; no lead rests
on it. EO 76 and EO 689 carry `partial_` edges that are false matches (a 2011 Public Land Order, and EO 10008).

## (d) Members not decided (143)

- **EO 209 (B02, 1).** No held instrument names EO 209 or the 1903 rules, or expressly revokes a class that includes
  them. Later instruments only restated the rules:
  - EO 7915 and EO 8043, effective 1939-02-01 (the disclosed candidate end);
  - EO 9830 (1947), which revoked EO 7915 by name;
  - EO 10577 (1955).

  What would decide EO 209 is an instrument naming it, or an owner decision on full restatements of the same rules.
  No such instrument is known.
- **Special rules (B07, 3: EO 97, 98, 191).** EO 209 replaced the 1896 rules "and the amendments thereof". Even so, in
  1904 EO 250 still revoked a special rule of 1902, which shows that special rules were treated as outliving the 1903
  revision.
  - EO 97 and EO 98 except only "the successor to the present incumbent" and were probably exhausted by one
    appointment, but no record of either appointment is held.
  - EO 191 lets the engineer of the new Government Printing Office building retain his force "during the
    continuance of the work at the War College and Washington Barracks", and "The authority herein granted shall
    lapse upon the completion of said work". This is an own-terms (TERM) end that needs only the completion date of
    that work.
- **Class orders (B08 and B16, 35).** Examples:
  - EO 54, 69 and 70: section 6 directions to department heads;
  - EO 290: laborers classified;
  - EO 1659: Navy artisans;
  - EO 5042: press helpers covered in;
  - EO 1394, 6772 and 6784: positions placed outside the classified service;
  - EO 205: one position excepted;
  - EO 2384: five named postmasters classified, closer to the one-person family.

  Their effect is a continuing state of coverage. EO 7915 Rule II sec. 1 saved status granted by such orders, which
  is a savings clause, not an end. Any one of the following, held for a member's positions, would decide it:
  1. a later order or statute naming the order or its positions that excepts them, abolishes them, or moves them to
     a statutory personnel system;
  2. a Civil Service Commission report or Federal Register notice recording their removal from the classified
     service or from a schedule;
  3. abolition by name of the office or bureau holding them, by a statute or reorganization plan with a stated date
     (ruling P7);
  4. for orders placing positions outside the classified service, the end of the commission or office concerned.

  B16 also catches a few loosely matched orders (EO 633, 91, 984, 178, 416). They are open either way.
- **Amendments with a further provision (B15x, 21).** EO 4754 is among them: besides adding paragraph 16 to Schedule A it directs that Army hospital appointments "will hereafter be made in accordance with the civil service act and rules", a standing classification direction. The text of each also does something besides amend:
  - incumbents are included, continued or saved: EO 2780, 4221, 4720, 5817, 5901, 6047, 6141, 7427, 6134, 3455;
  - EO 2460 and EO 5248 add "It is further ordered" provisions;
  - EO 4948 treats Indians "now in the service" as classified and allows reinstatement without time limit (its
    effect was also deferred to April 1, 1929 by EO 4982);
  - EO 5171 and EO 5775 give status to persons;
  - EO 2403, 3303, 3400, 5777 and 6214A state "the effect of this amendment" or "of this order".

  The further provision must be decided on its own terms.
- **Unconfirmed amendments (B18, 11).**
  - EO 1451's operative text ("Hereafter paragraphs (a) and (b) of section 1 of Civil Rule VII shall apply ...") has
    no amending words. Only its title says "Amending".
  - EO 740's held text is the rewritten rule, "not the full order text".
  - EO 3797's held text is a different order, a one-person reinstatement.
  - EO 72 and EO 79 are empty report slices.
  - EO 2689 grants noncompetitive examination without amending words.
  - EO 1180 and EO 986 promulgate or prescribe further provisions.
  - EO 173 and EO 213 construe the rules.
  - EO 687 is a misdirected amendment. Its revocation by EO 689 appears only in Wikisource's notes, not in EO 689's
    operative text.
- **Separate regulation sets (B17, 9).** These are the labor regulations (EO 275, 285, 1108, 210), the postmaster
  regulations (EO 2569A, 4538, 5104, 7421) and the furlough regulations (EO 5887). They belong with PD-ADMIN (type
  `regulations_issuance`), and the later orders that replaced them have not been read.
- **Members of other families (64).** These stay open here, with the reason naming the family:
  - **B06p, 15 one-person orders:** PD-CS-ONE-PERSON (P4). They are EO 188, 268, 3050, 3051, 3330, 3425, 3762, 3789,
    4238, 4259, 4432, 505, 6029, 691 and 6162. EO 3050 and EO 3051 are readable one-person appointment waivers
    (Robert L. Stancill, February 1919; Bert M. Williams, 1919).
  - **B11, 5 waivers:** named-person waivers belong to PD-CS-ONE-PERSON. No family doctrine exists yet for waivers
    that cover a class or an occasion (EO 713, 1275, 3517, 3688, 7366).
  - **B19, 2 closings:** PD-ADMIN, type `closing_mourning`. By their own terms they cover December 24, 1930, and
    December 24 and 31, 1932.
  - **B97, 7 orders with the WPA hint `emergency_war`:** PD-WAR-EMERGENCY. EO 470, 475 and 5476 are administrative
    in substance and should be retyped.
  - **B99, 35 administrative orders:** PD-ADMIN. These include directives, transfers of functions or records,
    organization orders and seals.
    - EO 999 (the Boxer indemnity) belongs with its subject family.
    - EO 739 authorized Indian messengers. EO 754 then amended Rule III to cover the same appointments, but EO 754's
      text does not revoke EO 739.
    - EO 4240 is rescinded only in part, by EO 6175 (`partial_rescission`).

## Owner adoption point

Ruling P2 names a choice for the owner. If the owner treats an amending order as living for as long as the text it
amended lives, the 378 pure-amendment leads change:

- **B12, and the pre-1896 members of B15 (EO 61):** take the end of their parents, EO 89's express revocation on
  1896-05-06.
- **B13:** takes EO 209's taking effect on 1903-04-15.
- **B14a, B14, B14s and the rest of B15:** become `open`, pending their parents.

# One-person civil-service waivers: what evidence shows use, and what ends an unused waiver

Research by a Claude research agent for Claude's session of 2026-10-28, applying the owner ruling
`research/readiness/owner_rulings/2026-10-28-evidence-not-convenience.md` to type rule `TR-CS-WAIVER`.
Scope: the 1,530 orders typed `cs_waiver_individual` in `jobs/x1-class-engine/output/TYPES.csv` (1,519 with a
year; 1,002 dated 1900-1921; 515 dated 1922-1936). Quotations are exact; "inference" marks the agent's own
reasoning. `namematch.py` and `filtered_matches.txt` are the name-match tool and its filtered output (run on
TYPES.csv; the full 1.5 MB match list is not committed).

## Conclusions

1. **Civil Service Commission annual reports cannot date use (high confidence).** The FY1914, 1915, 1918 and
   1922 reports, searched page by page, print each waiver order and count them ("waived by executive order in
   behalf of 64 persons") but never list appointments made under individual waivers. TR-CS-WAIVER's
   `effective_date_basis`, which names the CSC report as a source for the action date, is wrong for this type.
2. **What can date use.** The Official Register listed every employee as of July 1 of odd years through 1921
   (presence, not appointment date): each hit gives an interval of up to about two years for the ~1,000 orders of
   1900-1921. Later orders naming the person also work. Exact dates are in NARA St. Louis service record cards
   and personnel folders (offline, $20-70 each). Estimate, not measured: the Register could date 20-33% of the
   type. No Register lookup was completed because archive.org and HathiTrust item fetches were refused.
3. **No general measure revokes or saves outstanding one-person waivers (high confidence).** EO 209 (1903),
   EO 7916, EO 8743, EO 9830 and EO 10577 revoke only listed orders or schedules; none lists a one-person waiver.
   EO 9830 §1.1(b) and the Act of March 27, 1922 recognize status granted by executive order, which supports the
   appointment surviving as an accrued effect. The Ramspeck Act text was not retrieved.
4. **One narrow 1903 reason.** EO 209 replaced the 1896 rules "and the amendments thereof", so 1900-02 orders
   issued as special rules amending them ceased on 1903-04-15 if unused. For other waivers issued before April 15,
   1903, Rule II's "unless specially exempted thereunder" gives only a candidate end (inference; no source
   applies it).
5. **Death of the named person is a reason, but it bounds the end, not the use.** Bound = order date + 122 years
   164 days (the longest authenticated life) - the person's minimum possible age at the order date (a_min). It
   needs no assumption only for orders through 1904-05-17. a_min must come from the order's own facts; with 14 it
   covers orders through 1918-05-17 (about 880-914), with 18 through 1922-05-17 (about 1,004-1,032).
6. **Misclassified members** (listed at the end) should leave the type.

## Q1. Evidence of use

### CSC annual reports print the orders, not the appointments

Searched: full page texts of four reports in `jobs/numbered-early-orders/output/books/CSR_{1914,1915,1918,1922}_pages.jsonl.gz`.

- FY1914 (https://archive.org/details/annualreport139commgoog), p.7: "During the year various provisions of the
  civil-service rules were waived by executive order in behalf of 64 persons." Orders are printed in the appendix
  under "V. ORDERS EXCEPTING PERSONS NAMED FROM THE REQUIREMENTS OF THE RULES" (p.120).
- FY1915 (https://archive.org/details/annualreportuni01commgoog), pp.7-8: "Executive orders waiving the rules or
  labor regulations were pro-mulgated during the year in behalf of 89 persons as indicated below. These orders are
  published in full in the appendix and contain statements of the reasons for their issuance and whether or. not
  the commission concurred in recommending them". The table counts orders by kind ("Appointments allowed without
  examination 43 ... Total 89").
- FY1918 (https://archive.org/details/annualreportuni00commgoog) and FY1922
  (https://archive.org/details/annualreportuni02commgoog) follow the same pattern (FY1922, p.127).
- Name lists of appointments made exist only for class authorities: "APPOINTMENTS UNDER SECTION 10, RULE II" and
  "APPOINTMENTS UNDER EXECUTIVE ORDER OF MARCH 26, 1917" (FY1922 pp.132, 135; FY1918 p.161), with name, bureau,
  salary and position but no dates.
- Not found: any list of appointments under individual waivers in these four reports. The other 33 reports could
  not be searched because the repository keeps only order slices from them.
- FY1914, p.19: "The commission maintains a service history of employees in the classified service as a check upon
  irregular or illegal appointments" and "The service records, on the other hand, being kept up to date on the card
  system, are far more valuable and useful". These are the NARA St. Louis cards below.

### The Official Register

- NARA describes it as listing "the name of every employee, their job title, state or country of birth, the
  location of their post, and their annual salary", and says "After 1921 the Official Register removed the all-name
  directory" and "The federal government ceased publication of the Official Register in 1959"
  (https://www.archives.gov/files/calendar/genealogy-fair/2011/handouts/507-official-register-ref-rpt.pdf). It
  gives no appointment dates. The FY1914 CSC report calls it a "directory or finding list of names of officers and
  employees, with their positions, salaries, and States from which appointed" (p.19). An entry proves presence on
  the register date, not the date of the act.
- Volumes are dated July 1 of odd years through 1921 and May 1 from 1925, per a secondary index
  (https://stampsmarter.org/learning/portals/SS_Official_Registers_Portal.pdf), which also says "Postal Service
  Employees were not included after the 1911 Edition."
- Digitized: HathiTrust 009557655 (https://catalog.hathitrust.org/Record/009557655), full view for 1907, 1909,
  1911, 1913, 1915, 1917 and 1921; HathiTrust 008614161 (https://catalog.hathitrust.org/Record/008614161) for
  1901, 1903 v.2 and 1905 v.1; Internet Archive ids officialregister15united, officialregister17unit,
  officialregister21unit; GovInfo 1925-1959 (for example
  https://www.govinfo.gov/app/details/GOVPUB-CS1-fe48c19cd30ed99e48a26568d66ceed5/related, 1933).
- Use (inference): an entry in the authorized position in the next register (date R), plus evidence the person was
  not already in that position at the order date D, gives "exhausted within (D, R]". This does not work for orders
  converting temporary employees to permanent status (82) or for retention orders (33).

### Later orders naming the same person

The name match found 97 of 1,298 parseable waivers matching another order; about 8 have evidentiary value.

- **EO 7140 and EO 7472** (`jobs/hathi-gpo-orders/output/texts/EO_7140.txt`, `EO_7472.txt`; sources
  https://commons.wikimedia.org/wiki/File:Executive_Orders_7082-7261.djvu and ...7262-8027.djvu). EO 7140: "Mrs.
  Ruth Hampton, of Illinois, may be appointed as Assistant Director, Division of Territories and Island Possessions
  ... without compliance with the civil-service rules and without being accorded a classified status." Its date line
  OCRs as "August 18, 1936", which conflicts with EO 7472's recital. EO 7472 (October 16, 1936; OCR "1986"):
  "Executive Order No. 7140 of August 13, 1935, authorizing the appointment of Mrs. Ruth Hampton to the position of
  Assistant Director ... is hereby modified so as to permit Mrs. Hampton to acquire a classified civil service status
  as a result of her appointment to such position." Supports: exhausted within 1935-08-13 to 1936-10-16.
- **EO 2340 and EO 7072.** EO 2340 is known only from its WPA summary: "John V. Shea made eligible for transfer
  from bookbinder to clerk in the classified service of the Treasury Dept. without examination. 1916 CSR 116." EO
  7072 (June 12, 1935; APP copy `jobs/clause-drafts/output/texts/cd-job-app-executive-orders-7072-74810bc1a3.txt`):
  "John V. Shea, senior clerk, Division of Supply, Treasury Department, who, during the current month, will reach
  the retirement age". Supports use between 1916 and 1935-06-12, on an identity inference.
- Others, from WPA summaries only: EO 1785 and 1971 (Dr. Park Howell); EO 1543 and 2065 (Margaret A. Hampton);
  EO 231 and 341 (Allen Hazen); EO 1093 and 2500 (Hattie M. Miller); EO 776 says EO 707 (Scruggs reinstatement) was
  "confirmed".
- **EO 232** (Wikisource mirror
  https://kwx.liehendr.com/content/wikisource_en_all_maxi_2022-09/A/Executive_Order_232): "Dr. William A. White may
  be appointed to the vacancy now existing in the position of superintendent of the Government Hospital for the
  Insane without examination under the civil-service rules." Dated August 20, 1903. Wikipedia, citing the Dictionary
  of American Biography: "On October 1, 1903, White became superintendent"
  (https://en.wikipedia.org/wiki/William_Alanson_White). A secondary source for exhaustion on 1903-10-01.

### NARA St. Louis

https://www.archives.gov/st-louis/opf: holdings for "federal employees who served during the period 1850-1951";
"Service record cards offer a summary of employment to include appointments, promotions, transfers, ... and
separation from service." Fees $20 per card and $25 or $70 per folder; requests need name, birth date, agency and
service dates.

### What the repository holds

`jobs/csc-annual-reports/output/REPORTS_FETCHED.csv` lists 37 reports (FY1895-98, 1900-03, 1905-30, 1938-40;
missing FY1899, 1904, 1931-37; FY1916 is the package titled 1915); `texts/` holds 798 order slices. Full report text
is held only for FY1914, 1915, 1918 and 1922 (numbered-early-orders). No Official Register, agency register or
personnel record is held.

| Record | Years | Names people | Action date | Digitized | Share of the type it can date |
|---|---|---|---|---|---|
| CSC annual reports | FY1883-; held FY1895-1930, 1938-40 | yes (order texts) | no | GovInfo Serial Set; IA | about 0% |
| Official Register, all employees | 1901-1921, July 1 of odd years | yes | no; interval of two years or less | HathiTrust, IA | about 1,000 orders in range; estimated 20-33% of the type (not measured) |
| Official Register, officials only | 1925-1959 | senior staff | no | GovInfo, IA, HathiTrust | 1-3% |
| Later orders naming the person | 1900-1950s | yes | interval | repository, APP, Federal Register | measured: 97 leads, about 8 evidentiary |
| Agency reports and registers | varies | mostly senior staff | sometimes | not surveyed | a few % |
| NARA St. Louis cards and folders | service ending 1850-1951 | yes | yes | offline, fee-based | nearly all in principle; samples only in practice |

## Q2. Reason-based endpoints

- **EO 209, signed March 20, 1903, effective April 15, 1903** (`jobs/wikisource-texts/output/texts/EO_209.txt`;
  https://en.wikisource.org/wiki/Executive_Order_209, revision 13537757): "the President promulgates the following
  rules in lieu of those promulgated May 6, 1896, and the amendments thereof:". Rule II: "No person shall be
  appointed, employed, promoted, or transferred in the classified service ... until he passes an examination in
  conformity with these rules, unless specially exempted thereunder." "Approved, to take effect on and after April
  15, 1903." It has no revocation clause and says nothing of individual exceptions. It is a reason for 1900-02
  special-rule orders (EO 130, 141, 142, 143, 154, 174, 185; WPA: "Civil Service Rules amended by promulgation of
  special rule..."), which ceased on 1903-04-15 if unused. For other named waivers before that date the "thereunder"
  reading is only a candidate end (inference).
- No other general revision between 1903 and 1938 appears in the TYPES.csv summaries; the general revisions are
  1896 (EO 89) and 1903 (EO 209).
- **EO 7916, June 24, 1938** (APP copy
  `jobs/app-executive-orders/output/texts/executive-order-7916-extending-the-competitive-classified-civil-service.txt`):
  §7 revokes only "Executive Order No. 5612 of April 25, 1931"; §9: "Schedules A and B of the Civil Service Rules,
  as presently existing, ... will be superseded". Neither a reason nor a date for individual waivers.
- **Ramspeck Act, November 26, 1940 (54 Stat. 1211):** not retrieved; whether it has a repeal or savings clause is
  not established.
- **EO 8743, April 23, 1941, 6 FR 2117** (`jobs/fr-originals/output/texts/EO_8743.txt`): §1 excepts "(4) those
  which now have a classified status"; §7: "Executive Order No. 8044 of January 31, 1939, is hereby revoked so far as
  it applies to positions covered into the classified civil service by this order." Neither.
- **EO 9830, February 24, 1947, 12 FR 1259** (`jobs/fr-originals/output/texts/EO_9830.txt`;
  https://www.govinfo.gov/content/pkg/FR-1947-02-25/pdf/FR-1947-02-25.pdf; checked against the Truman Library and
  National Archives copies): "it is hereby ordered as follows, effective May 1, 1947:"; "The Civil Service Rules are
  hereby amended to read as follows:"; §1.1(a) "as defined in existing statutes and Executive orders."; §1.1(b)
  status "may be granted by statute, Executive order, or the Civil Service Rules."; Part III "The following
  Executive orders are hereby revoked:" lists 54 orders from "No. 279 of November 29, 1904." to "No. 9733 of June
  4, 1946." (the Truman Library list omits No. 8214 and gives different dates for 8083 and 8300). No one-person
  waiver is listed; EO 715 and 983, listed, are class authorities typed here in error. Neither.
- **EO 10577, November 22, 1954, 19 FR 7521** (`jobs/fr-originals/output/texts/EO_10577.txt`): "The Civil Service
  Rules are hereby amended to read as follows:"; §301 revokes Part II of EO 9830 and EO 9973, 10440, 10463 and
  10180 by name. Neither.
- **Act of March 27, 1922** (quoted in the FY1922 report, p.99): persons "given a com-petitive status ... by
  Executive orders ... authoriz-ing the appointment of individuals to positions within such service." Saves the
  effect of a used waiver; ends nothing.
- **Death of the named person.** The permission's only object is one named person, so it cannot operate after that
  person dies (inference; nothing contrary found). The longest authenticated life is "122 years 164 days" (Jeanne
  Calment, 1875-1997; https://guinnessworldrecords.com/world-records/oldest-person;
  https://www.grg-supercentenarians.org/jeanne-calment/). So the waiver ended, by performance or death, no later
  than order date + 122 y 164 d - a_min: an interval for the end, not evidence of use. No general minimum
  appointment age was found; the Commission could "change by regulation the existing age limits" (FY1915 report,
  p.69), and a waiver could bypass them, so a_min must come from the order's own facts (prior service, Civil War
  veteran, "widow of", a professional title, a later retirement-age order).

| a_min | Orders dated on or before | Approximate count |
|---|---|---|
| 0 | 1904-05-17 | 43 plus part of 26 undated-day orders |
| 14 | 1918-05-17 | 881 plus part of 33 |
| 16 | 1920-05-17 | 937 plus part of 17 |
| 18 | 1922-05-17 | 1,004 plus part of 28 |

| Measure | Key clause | Effect on one-person waivers | Reason, date or neither |
|---|---|---|---|
| EO 209 (1903) | "in lieu of those promulgated May 6, 1896, and the amendments thereof" | supersedes 1896 rules and amendments; silent on named waivers | reason (1903-04-15) for 1900-02 special-rule orders; candidate only for other pre-1903 waivers |
| EO 7916 (1938) | revokes EO 5612; Schedules A and B superseded | none | neither |
| Ramspeck Act (1940) | not retrieved | not established | not established |
| EO 8743 (1941) | revokes EO 8044 in part | none | neither |
| EO 9830 (1947) | rules "amended to read"; listed revocations; status "granted by ... Executive order" | none; status recognized | neither |
| EO 10577 (1954) | listed revocations | none | neither |
| Act of March 27, 1922 | status via orders "authorizing the appointment of individuals" | saves the effect of use | no end |
| Death of the person | reasoning | extinguishes the permission | reason; interval bound only |

## Proposed decision procedure for one waiver order

0. **Membership.** One named person and one action, with no continuing authority and no class of persons or
   positions; otherwise route to the type's outliers.
1. **Express terms.** The order's own time limit or condition, and later orders revoking, modifying, confirming or
   replacing it (for example EO 1078 revoking EO 1053; EO 7472 modifying EO 7140). A revocation before any use is
   an express end.
2. **Use evidence.**
   - (a) A dated record of the act (service card, personnel folder, agency report, the order's own recital):
     exhausted on that date; the appointment survives as an accrued effect.
   - (b) Presence in the authorized position at date R (Official Register 1901-21, a later order, an agency report)
     plus evidence the person was not in that position at order date D: exhausted within (D, R]. Matching requires
     full name, office and a consistent position.
   - (c) For a temporary-to-permanent or retention order, presence alone is not use unless the record shows the new
     status.
3. **No use evidence: a reason it ceased.**
   - (a) A 1900-02 special-rule order with no use shown by 1903-04-15: not in force from 1903-04-15; use unknown.
   - (b) A named waiver before 1903-04-15: report the candidate end, marked as inference.
   - (c) A known death date: not in force after death; use unknown.
   - (d) Bound = D + 122 y 164 d - a_min, with a_min from the order's facts. If the bound is before the claim's
     cutoff: ended within (D, bound]; use unknown. Disclose a_min, and say whether a defensible change in a_min
     flips the result.
   - General rewrites (EO 7916, 8743, 9830, 10577) are never endpoints for these orders.
4. **Otherwise open**, naming the records that would resolve it (the next July 1 Official Register; the NARA St.
   Louis card).

Mapping: exhausted on a date = 2(a); exhausted within an interval = 2(b); not in force but use unknown = 3(a), 3(c),
3(d); open = 4, and 3(b) until its inference is accepted.

## Misclassified members

- EO 715 (general authority to waive examination in transfers) and EO 983 (fourth-class postmasters): class
  authorities, both revoked by EO 9830, so express ends of May 1, 1947.
- EO 60, 95, 123, 158, 164: rule amendments.
- EO 130, 141-143, 154, 174, 185: position-based special rules.
- EO 203, 222: class orders.

## Not retrieved

WebFetch was refused for the archive.org and HathiTrust Official Register items,
https://www.govinfo.gov/content/pkg/FR-1947-02-26/pdf/FR-1947-02-26.pdf and
https://www.govinfo.gov/content/pkg/STATUTE-54/pdf/STATUTE-54-Pg1211.pdf (Ramspeck Act). The Wikisource page for EO
7916 failed at the site. The shell has no internet access.

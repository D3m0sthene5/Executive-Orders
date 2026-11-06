# PD-CUSTOMS-CONSULAR working notes (2026-11-05)

## Read

- **Instructions:** `research/pothier/work/AUTHOR_BRIEF.md` and `research/pothier/DOCTRINE_SCHEMA.md`.
- **Engine code:** `jobs/pothier/pothier.py` (validator, date rules, contradiction check).
- **Members:** `research/pothier/work/PD-CUSTOMS-CONSULAR/MEMBERS.csv` and the member records in
  `jobs/pothier/output/MEMBERS.jsonl`.
- **Member texts:** the operative text of every member. All 263 texts were read in snippets of 450-700 characters
  after the enacting clause, and in full for about 40 members: EO 5577, 5291, 5317, 6283, 4572, 4780, 4156, 4385,
  3609, 2878, 4265, 4899, 5078, 5284, 5453, 5011, 4502, 4299, 4709, 3122, 1804, 3535, 2139, 4337, 6545, 4518, 5644,
  5435, 7062, 5127, 3354, 3902, 6564A, 6994, 7358, 7061, 4292 and 3847.
- **19 CFR 101.3:** the held text at
  `jobs/source-ladder/output/texts/queue_EO_8238_19_CFR_101.3_...2ada2b03ae.txt` (CFR 2025 edition), read in full,
  page by page.
- **EO 5642:** the held official text at `jobs/ofr-compilations/output/texts/EO_5642.txt`, read for its cancellation
  clauses, Article I, Article II, sections 465-473 and Article XXV.
- **EO 5189:** the held text in `jobs/app-executive-orders/...5189...`; it revokes the orders of June 7, 1924 and
  February 25, 1928, neither of which is a member.
- **EO 4022:** the held text at `jobs/csc-annual-reports/output/texts/EO_4022.txt`; it recites EO 469 and the 1909
  diplomatic regulations without revoking them.
- **EO 7968:** the held FR text at `jobs/fr-originals/data/full_run/texts/EO_7968.txt`, read for its complete tariff
  and its supersession list.
- **EO 10718:** the held FR text at `jobs/fr-originals/output/texts/EO_10718.txt` (savings clause, sec. 2).
- **22 U.S.C. 4219:** the held source-ladder text for 22 U.S.C. 4219 (the R.S. 1745 fee authority continues).
- **Owner rulings:** `research/readiness/owner_rulings/2026-10-21-strike-and-insert.md`,
  `2026-10-21-until-and-further-exempt.md` and `2026-11-05-empty-status-history.md`.
- **Type rules:** TR-CANAL-ZONE and TR-LAND-WITHDRAWAL (the spent-on-issue conventions), and the Jacquard
  `LOT_RULES.md`.
- **Web, not held:**
  - EO 5642 at presidency.ucsb.edu (to locate it, later found held);
  - EO 10697 at presidency.ucsb.edu (sec. 7 revokes 1938-1955 Foreign Service Regulations orders, no member);
  - the OFR codification page for EO 10718;
  - T.D. 95-77 at https://www.govinfo.gov/content/pkg/FR-1995-09-27/html/95-23728.htm;
  - the eCFR versioner at https://www.ecfr.gov/api/versioner/v1/versions/title-19.json?section=101.3 (latest
    amendment 2023-11-16, latest issue 2024-06-24). The eCFR HTML page itself was blocked to the fetch tool.

## Tried and rejected

- **Customs districts.** T.D. 95-77 as a class end for the customs-district orders: the rule eliminates districts only
  "for the most part" and keeps them as geographical descriptions, so the district orders stay open (O3).
- **Coordinator lead on Reorganization Plan No. 1 of 1965.** It abolished collector offices, not districts or ports.
  It is not applied, and it decides no member.
- **19 CFR 101.3 as a predicate for every surviving port.** Rejected in favour of citation by order number only. A
  port that exists today but is cited to a later T.D. may rest on that T.D. rather than on the member (Wichita, Little
  Rock and Charlotte were abolished and re-created).
- **The `current_law.ecfr_mentions` field.** It flags only 8 of the 32 members that 101.3 cites (it misses, for
  example, EO 5444), so the membership list for B01 was built from the held CFR text.
- **EO 5642 as an end for amendments of Consular Regulations Articles I and XXV (EO 3354, 3902, 1926).** Rejected
  because those members also amend paragraphs outside the canceled articles (paragraph 32; paragraphs 502-517;
  paragraph 561) and the 1896 article numbering is not held. EO 5642 was applied only to EO 5127 (sections 465 and 467)
  and EO 5126 (the leave-of-absence paragraph of the Instructions).
- **EO 4022 (1924) as an end for EO 469 and its amendments.** Rejected because EO 4022 recites the 1906 and 1909
  orders but does not revoke them.
- **EO 7968 (1938) as an implied end of the earlier fee tariffs.** Rejected because its supersession list names other
  orders only. The question goes to the owner (O5).
- **Treating port renamings (EO 4518, 6545) and mixed abolish-and-create orders as spent.** Rejected because they
  leave a standing designation or standing limits.
- **Treating EO 5291 as spent.** Rejected because it was suspended before taking effect.
- **Hoover's December 1932 reorganization orders (EO 5966).** The House disapproval of January 1933 under section 407
  of the act of June 30, 1932 was not verified to a primary citation, so EO 5966 stays open in O7.
- **The Dominican customs receivership (EO 4353).** The 1940 Trujillo-Hull convention probably ended it, but the
  convention was not read, so the member stays open.
- **Held edges for EO 10, EO 12 and EO 2462.** All three are false matches (see the doctrine's "Data issues"), and none
  is used.

## Notes for the coordinator

- **Owner decision, B20.** Does the spent-on-issue rule reach amendments of presidential regulations that are not
  numbered executive orders (the Consular Regulations of 1896, the Instructions to Diplomatic Officers, the Tariff of
  Consular Fees)? B20 holds 38 members. If the answer is no, set B20 to `open`.
- **Owner decision, O5.** Does a complete replacement tariff end an earlier tariff that it does not name?
- **O7 routing.** The six members in O7 belong to other families: EO 6778 to an NIRA or alcohol family, EO 5966 to
  reorganization, EO 1960 and 2017 to war or neutrality, EO 2620 to territories, and EO 4353 to treaty
  administration.
- **Scratch work.** Scratch scripts were kept outside the repository, in `/tmp/pdcc_x7q/`. A shared `/tmp/pd/` was
  overwritten by another agent mid-session, so a private directory was used. The JSON was generated by
  `/tmp/pdcc_x7q/gen.py`.

## Time and effort

About 2.5 hours of agent time. Roughly 60 tool calls; about 90 member texts were read beyond the snippet pass; 6 web
fetches and 3 web searches were made.

# What the scholarship says about the count, and a CIS cross-check of the unnumbered series (2026-11-12)

Kean F-20261112-count-literature. Owner request: dig up academic research that has already tried to count every
executive order, to help answer the census sub-questions.

## The literature, by what it actually counts

| Work | What it counts | Bearing on our questions |
|---|---|---|
| Lord (ed.), *List and Index of Presidential Executive Orders, Unnumbered Series* (WPA, 1943); *Presidential Executive Orders, Numbered 1-8030* (1944) | over 1,500 unnumbered orders, 1789-1941; the numbered series to 1938 | The base of every later unnumbered count. Lord's preface says the total is unknown and repeats Ickes's 15,000 and others' 50,000 without derivation. |
| House Committee on Government Operations, *Executive Orders and Proclamations: A Study of a Use of Presidential Powers* (committee print, Dec. 1957) | estimates unnumbered orders "to exceed 15,000"; lists 31 confidential orders since 1915 | The source of the 15,000 figure in later reports; no inventory behind it. |
| Senate Special Committee on National Emergencies, *Executive Orders in Times of War and National Emergency* (1974) | repeats the 1957 estimate | Not independent. |
| **CIS Index to Presidential Executive Orders & Proclamations** (Congressional Information Service, 1987), with microfiche 1789-1983 | about 100,000 presidential documents from 1789, filed by source record group | The most complete compilation ever made. Its ProQuest successor holds 20,028 unnumbered orders, directives and proclamations for 1789-1936 (`research/pre-1937-sources/PROQUEST_CONGRESSIONAL.md`). NYU holds the fiche and the index. |
| Woolley and Peters, American Presidency Project, "Executive Orders" table | per-president totals to 1945, numbered plus Lord's unnumbered | Its note says the true total of unnumbered orders is unknown and "estimates have ranged as high as 50,000". |
| Dodds, *Take Up Your Pen* (2013) | unilateral directives of about 30 kinds from Washington on | Broader than executive orders; no EO-only count. |
| Mayer, *With the Stroke of a Pen* (2001); Howell, *Power without Persuasion* (2003); Warber (2006); Chiou and Rothenberg (2017); Lowande and Poznansky (2024) | numbered orders, mostly 1936 or 1945 on, and their significance or durability | Confirm the modern numbered series; nothing on the early unnumbered tail. |
| **Kaufman and Rogowski, "Presidential policymaking, 1877-2020," *PSRM* (2024)**; replication data doi:10.7910/DVN/6SGSTI (CC0) | 59,048 directives, 1877-2020, from the CIS Index and ProQuest; the deposit lists 101,186 CIS accession numbers, 1789-2020, by record group | The only public, document-level copy of the CIS universe. It puts numbered orders with CIS groups 33 and 41 (Executive Orders Relating to Public Lands, 1841-1935 and 1820-1913), 22 (Panama Canal, 1902-1934) and 06 (Secretary of the Interior orders) in its "executive orders". |

Nobody has derived a total of all orders ever issued. The 15,000 and 50,000 figures trace back to unsupported
estimates in Lord's preface and the 1957 study. That matches the Graunt audit's conclusion.

## Cross-check: CIS's unnumbered executive-order groups against the audited series

`CIS_UNNUMBERED_EO_GROUPS_PRE1937.csv` lists the 2,520 CIS documents in groups 33, 41, 22 and 06 dated 1936 or earlier.
Each row has its CIS accession number, printed date and record group. Each is matched by date to
`jobs/domesday-register/data/GRAUNT_UNNUMBERED.csv` and to the census:

| Match | CIS documents |
|---|---:|
| Date also carries an audited unnumbered order | 1,633, against about 900 audited orders on those dates |
| Date carries only a numbered census order | 12 |
| **No known order of any kind on that date** | **875** |

The 875 date-unmatched documents are mostly public-land orders: 458 from 1910-1929 in group 33, plus 284 in group 41
from 1830-1919 and 92 Panama Canal orders.

They, and the roughly 730 CIS documents beyond the audited count on shared dates, are candidate additions to the
unnumbered series. CIS's own groups suggest the identified series may be about **875-1,600 larger** than the audited
1,816.

They are **leads, not admissions**. Before any is counted, a person must check:
- whether CIS's public-lands groups include departmental or Secretary-level orders, which the audit excluded;
- whether one CIS accession is one document;
- the text, which the owner can read on the CIS fiche at Bobst or as a ProQuest record. CIS accession numbers have the
  form year-group-sequence.

Files: `CIS_UNNUMBERED_EO_GROUPS_PRE1937.csv`; `SOURCE.txt` (citation, licence and source hash).

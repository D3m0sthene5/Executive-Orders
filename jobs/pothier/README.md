# Pothier: family doctrines applied to the orders with no dated status history

Named for Robert-Joseph Pothier (1699-1772), who reduced French law to treatises by subject so that one treatise
settled what had been argued case by case. Report and doctrines: `research/pothier/REPORT.md`,
`research/pothier/doctrines/`.

**Members.** The undecided orders (no provisional status in the readiness tracker) for which `jobs/status-history`
located no dated history: 5,918 on main of 2026-11-05, almost all from 1862-1936. The owner ruled on 2026-11-05 that
the claim kit may start them with an explicit, noted empty history (D-20261105-empty-history); their status must then
rest on the order's own terms and on law that applies to its whole class. A doctrine states that law once for a family.

**What it writes (zero tokens, standard library plus pypdf for the fetch step).**

| File | One line per | What it is |
|---|---|---|
| `output/MEMBERS.jsonl` | member | the fields a doctrine may read: dates, WPA 1944 summary, X1 type, held texts, literal text features, named persons, held later-event edges, current-law mentions (`members.py`) |
| `output/LEADS.jsonl` | member and doctrine | a **status lead** (`no`, `yes`, `open`), the deciding branch, basis kind (`TERM`, `ACT`, `CURRENT`), date or interval, sources (held or not), evidence gaps, contradictions with held evidence |
| `output/COVERAGE.json` | run | per doctrine and per WPA family hint: members, decided, not decided, contradicted |
| `output/DOCTRINE_PINS.json` | doctrine | path and sha256 of the doctrine applied |
| `output/SOURCES.jsonl`, `output/sources/` | fetched source | custody copies of the doctrine sources the project did not hold (`fetch.py`, GitHub Actions only) |

**What a lead is not.** A lead is never a provisional status, a claim or a finding. It changes no status, codebook,
census row or certified count (0). Leads are proposals for owner adoption, one decision per family (Kean asks). Every
order still goes through the claim kit on its own terms; a lead tells the producer which mechanism and sources to
check first and which evidence is missing.

```
python3 -I jobs/pothier/pothier.py members                      # rebuild MEMBERS.jsonl (about 8 s)
python3 -I jobs/pothier/pothier.py try research/pothier/doctrines/PD-LAND-WITHDRAWAL.json --hints
python3 -I jobs/pothier/pothier.py apply                        # all doctrines
python3 -I jobs/pothier/pothier.py sample --doctrine PD-INDIAN --n 30 --seed pilot1
python3 -I jobs/pothier/held.py 90 Stat 2743                     # is a source held?
python3 -I jobs/pothier/test_pothier.py
```

Doctrine format and condition language: `research/pothier/DOCTRINE_SCHEMA.md`.

## Class-wide law the doctrines hold (for Selden and others)

Each line: citation, then the held text path. A doctrine cites these with a pinned phrase; `held.py` finds more.

- 16 U.S.C. 668dd (2024 ed.), incl. subsec. (a)(1), (a)(5), (a)(6), amendment notes and the statutory note "National Wildlife Refuges"; Pub. L — `jobs/source-ladder/output/texts/USC_16_U.S.C._668dd_a_6_cd9a4906a8.txt`
- 16 U.S.C. 668dd note "National Wildlife Refuges" (2024 ed.), entries for Flattery Rocks and Quillayute Needles National Wildlife Refuges — `jobs/source-ladder/output/texts/USC_16_U.S.C._668dd_a_6_cd9a4906a8.txt`
- 19 CFR 101.3 (Customs service ports and ports of entry), 19 CFR Ch. I (4-1-25 Edition), pp. 634-642 — `jobs/source-ladder/output/texts/queue_EO_8238_19_CFR_101.3_Baltimore_Maryland_port_limits_and_any_Treasury_Decision_re-defining_them_2ada2b03ae.txt`
- 40 CFR 49.10198(b) (added 84 FR 34313, July 18, 2019) — `jobs/current-law/output/MENTIONS.csv`
- 43 CFR 2300.0-3 (eCFR as of 2026-11-04) — `jobs/theophilus-sources/output/texts/cfr-t43-2300.0-3.txt`
- 43 CFR 2566.0-3 and 2566.0-7 (eCFR, GovInfo bulk XML title 43 amended through 2026-08-12), as extracted by jobs/current-law — `jobs/current-law/output/FRAGMENTS.jsonl`
- 43 U.S.C. 1714(j) and (l) (2024 ed.); Pub. L. 94-579, title II, sec. 204, 90 Stat. 2751 (1976) (FLPMA sec. 204) — `jobs/source-ladder/output/texts/USC_43_U.S.C._1714_j_._7ba3070691.txt`
- 43 U.S.C. 1784 note (Kenai Natives Association Land Exchange) — `jobs/current-law/output/MENTIONS.csv`
- 43 U.S.C. 1787(b)(4)(B)(ii) (U.S. Code release point 119-121); Pub. L. 110-229, title II, sec. 202, May 8, 2008, 122 Stat. 763 — `jobs/current-law/output/MENTIONS.csv`
- 5 CFR 213.3102 (eCFR as of 2026-11-04), Schedule A, entire executive civil service; [47 FR 28902, July 2, 1982] — `jobs/theophilus-sources/output/texts/cfr-t5-213.3102.txt`
- 50 CFR 216.85 (eCFR as of 2026-10-14) — `jobs/current-law/output/MENTIONS.csv`
- Act of February 8, 1927, ch. 78, 44 Stat. 1061 — `jobs/numbered-early-orders/output/books/KAPPLER_IV_pages.jsonl.gz`
- Act of June 21, 1906, ch. 3504, 34 Stat. 325, 326 — `jobs/numbered-early-orders/output/books/KAPPLER_III_pages.jsonl.gz`
- Act of June 30, 1919, ch. 4, sec. 27, 41 Stat. 3, 34 — `jobs/numbered-early-orders/output/books/KAPPLER_IV_pages.jsonl.gz`
- Act of March 2, 1917, ch. 146, 39 Stat. 969, 976 — `jobs/numbered-early-orders/output/books/KAPPLER_IV_pages.jsonl.gz`
- Act of March 3, 1927, ch. 299, sec. 4, 44 Stat. 1347 (25 U.S.C. 398d) — `jobs/numbered-early-orders/output/books/KAPPLER_IV_pages.jsonl.gz`
- Act of Oct. 21, 1970, Pub. L. 91-476, sec. 8, 84 Stat. 1067, 1070 (16 U.S.C. 460y-7), as extracted from the OLRC U.S. Code release point 119 — `jobs/current-law/output/FRAGMENTS.jsonl`
- Civil Service Retirement Act, Act of May 22, 1920, ch. 195, sec. 1, 41 Stat. 614, as printed in the Civil Service Commission's 39th Annual R — `jobs/numbered-early-orders/output/books/CSR_1922_pages.jsonl.gz`
- FLPMA sec. 702, 90 Stat. 2787-2789 (repeal of homestead laws, including the ex-service preference resolutions 41 Stat. 434, 42 Stat. 358, 42 — `jobs/astra-source-retention/output/pages/3949c2ad363f3a8922cebc8a306985abd31cd1b304d17337104dc5509c71a906/08af99862ff7a5cb6fc75e6c78c101bd219fe0a5c7602f678ec00e0d828a65a6/selected-pages.txt`
- FLPMA sec. 704(a), 90 Stat. 2792 — `jobs/astra-source-retention/output/pages/3949c2ad363f3a8922cebc8a306985abd31cd1b304d17337104dc5509c71a906/08af99862ff7a5cb6fc75e6c78c101bd219fe0a5c7602f678ec00e0d828a65a6/selected-pages.txt`
- Federal Land Policy and Management Act of 1976, Pub. L. 94-579, sec. 701(c), 90 Stat. 2743, 2786 (43 U.S.C. 1701 note) — `jobs/astra-source-retention/output/pages/3949c2ad363f3a8922cebc8a306985abd31cd1b304d17337104dc5509c71a906/08af99862ff7a5cb6fc75e6c78c101bd219fe0a5c7602f678ec00e0d828a65a6/selected-pages.txt`
- Federal Land Policy and Management Act of 1976, Pub. L. 94-579, sec. 704(a), 90 Stat. 2743, 2792 — `jobs/astra-source-retention/output/pages/3949c2ad363f3a8922cebc8a306985abd31cd1b304d17337104dc5509c71a906/08af99862ff7a5cb6fc75e6c78c101bd219fe0a5c7602f678ec00e0d828a65a6/selected-pages.txt`
- Federal Land Policy and Management Act of 1976, Pub. L. 94-579, secs. 701(c) and 704(a), 90 Stat. 2743, 2786, 2792 — `jobs/astra-source-retention/output/pages/3949c2ad363f3a8922cebc8a306985abd31cd1b304d17337104dc5509c71a906/08af99862ff7a5cb6fc75e6c78c101bd219fe0a5c7602f678ec00e0d828a65a6/selected-pages.txt`
- Joint Resolution of March 3, 1921, ch. 136, Pub. Res. No. 64, 41 Stat. 1359-1360 — `jobs/astra-source-retention/output/pages/d811bcf2c2b599b84e4ad86642156c45ec38f2bd4c077a1bbb22cb29f6be82ad/dc02551261e1c39583eb83568c28d3de8d373164d84bf0a0df422e6e15ba9617/selected-pages.txt`
- National Industrial Recovery Act, ch. 90, tit. I, sec. 2(c), 48 Stat. 195, 196 (June 16, 1933) — `jobs/astra-source-retention/output/pages/c9fcb1910615c2d9b677700a8fa96edc8da2cfdca204ed04f51e5f8dde99ebe7/6fca72c4672ad8ad9a53ad398017a587b67e2950dd8f5bec674c7a0f3c25b446/selected-pages.txt`
- Panama Canal Act of 1979, Pub. L. 96-70, sec. 2101, 93 Stat. 452, 493 (Sept. 27, 1979); 22 U.S.C. 3831 — `jobs/source-ladder/output/texts/queue_EO_9293_Panama_Canal_Treaty_1977_and_Panama_Canal_Act_of_1979_Pub._L._96-70_93_Stat._452_instr_8d101fb40b.txt`
- Panama Canal Act of 1979, Pub. L. 96-70, secs. 3(b)(1), 1504 and 3304, 93 Stat. 452, 455, 488, 500 — `jobs/source-ladder/output/texts/queue_EO_9293_Panama_Canal_Treaty_1977_and_Panama_Canal_Act_of_1979_Pub._L._96-70_93_Stat._452_instr_8d101fb40b.txt`
- Panama Canal Act of 1979, sec. 3(b), 93 Stat. 455; 22 U.S.C. 3602(b) — `jobs/source-ladder/output/texts/queue_EO_9293_Panama_Canal_Treaty_1977_and_Panama_Canal_Act_of_1979_Pub._L._96-70_93_Stat._452_instr_8d101fb40b.txt`
- Panama Canal Act of 1979, sec. 3304, 93 Stat. 500 — `jobs/source-ladder/output/texts/queue_EO_9293_Panama_Canal_Treaty_1977_and_Panama_Canal_Act_of_1979_Pub._L._96-70_93_Stat._452_instr_8d101fb40b.txt`
- Philippine Independence Act (Tydings-McDuffie Act), Act of Mar. 24, 1934, ch. 84, secs. 5 and 10, 48 Stat. 456, 459, 463 — `jobs/astra-source-retention/output/pages/2900efa1f3ecea81c6d760bd99e6102ae951bd8eed35a7fa461c258e537ebb8e/4d52c0464a453c382faaf4cc7bd953308f9ef9b369f59e1a69e0e50093fbcdf1/selected-pages.txt`
- Philippine Independence Act (Tydings-McDuffie Act), ch. 84, sec. 10(a), 48 Stat. 456, 463 (Mar. 24, 1934) — `jobs/astra-source-retention/output/pages/2900efa1f3ecea81c6d760bd99e6102ae951bd8eed35a7fa461c258e537ebb8e/4d52c0464a453c382faaf4cc7bd953308f9ef9b369f59e1a69e0e50093fbcdf1/selected-pages.txt`
- Proclamation 2695, July 4, 1946, 60 Stat. 1352 — `jobs/astra-source-retention/output/pages/c493d8ef1e3055a50ab3dc4e404b2eaf359537fe78638e57dbd8424bee8a0447/adb2b31e2516fd67174bfb53b7aa579a8236a1c6d0d27e4d768438fc2a4577c5/selected-pages.txt`
- Proclamation No. 2416, July 25, 1940, 54 Stat. 2717, 5 F.R. 2677 — `jobs/astra-source-retention/output/pages/15e01816ebc165ff00f747861704bae240f51f4f7578f1c14f53a942e5fa96de/attributed-derivatives/fab36cf01a256ec30f4ba8de5d4e4b60feaf67c1e7d3f3501a9a7dca6dafe455.txt`
- Proclamation No. 2695, Independence of the Philippines, July 4, 1946, 60 Stat. 1352, 1353 — `jobs/astra-source-retention/output/pages/c493d8ef1e3055a50ab3dc4e404b2eaf359537fe78638e57dbd8424bee8a0447/adb2b31e2516fd67174bfb53b7aa579a8236a1c6d0d27e4d768438fc2a4577c5/selected-pages.txt`
- Reorganization Plan No. II of 1939, secs. 2(a) and 4(f), 4 F.R. 2731 (July 1, 1939), 53 Stat. 1431 (Statutes at Large page from the U.S. Cod — `jobs/astra-source-retention/output/pages/5437e663677371c8db1016ea81a834f6cca735ff9fa988e08397fb99c73ccd36/attributed-derivatives/c1ca82e037a2d1404b6be6cc6c38fc88cc064007bfe4164254c5cd11b47d3d0b.txt`
- S.J. Res. 113, Pub. Res. No. 26, 74th Cong., ch. 246, sec. 1, 49 Stat. 375 (June 14, 1935) — `jobs/astra-source-retention/output/pages/98e35c567ea86208eadc55548eb7a5ea5f1edd92d8116c9e4c4847da1bab0305/d19d25fe35e98a1ade9b1fd03ed8751743502c5d1005a61ca97974657cf08386/selected-pages.txt`
- S.J. Res. 113, sec. 2, 49 Stat. 375 (June 14, 1935) — `jobs/astra-source-retention/output/pages/98e35c567ea86208eadc55548eb7a5ea5f1edd92d8116c9e4c4847da1bab0305/d19d25fe35e98a1ade9b1fd03ed8751743502c5d1005a61ca97974657cf08386/selected-pages.txt`
- Tax Reform Act of 1976, Pub. L. 94-455, sec. 1202(a), 90 Stat. 1520, 1667-1668 (Oct. 4, 1976), enacting 26 U.S.C. 6103(a) — `jobs/source-ladder/output/texts/queue_EO_10906_Tax_Reform_Act_of_1976_Pub._L._94-455_sec._1202_90_Stat._1667_which_rewrote_sec._6103_64c0b4c21d.txt`
- Tax Reform Act of 1976, Pub. L. 94-455, sec. 1202(a), 90 Stat. 1520, 1672 (new 26 U.S.C. 6103(g)) — `jobs/source-ladder/output/texts/queue_EO_10906_Tax_Reform_Act_of_1976_Pub._L._94-455_sec._1202_90_Stat._1667_which_rewrote_sec._6103_64c0b4c21d.txt`
- Tax Reform Act of 1976, Pub. L. 94-455, sec. 1202(i), 90 Stat. 1520, 1688 (effective date) — `jobs/source-ladder/output/texts/queue_EO_10906_Tax_Reform_Act_of_1976_Pub._L._94-455_sec._1202_90_Stat._1667_which_rewrote_sec._6103_64c0b4c21d.txt`

Per-order acting instruments the doctrines need (Public Land Orders and the like) are listed for Selden in `research/pothier/FOR_SELDEN.csv`; `fetch.py` does not fetch them, and it skips URLs Ptolemy keeps (`research/pothier/work/PTOLEMY_SKIP.txt`).

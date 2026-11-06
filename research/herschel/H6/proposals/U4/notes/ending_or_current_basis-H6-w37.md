# ending_or_current_basis H6-w37
Start 2026-11-06T00:10:45Z, end 2026-11-06T00:23:07Z. 3 done, 2 blocked, 0 failed. EO:13821 untouched.

## EO:11929: done
Both clauses terminated 2003-03-28, EO 13294 sec. 2 (revokes EO 11157 as amended). EO 13294 does not name 11929 (disclosed under the unnamed-instruments ruling); the reason is that the inserted section 114 and amended section 105 exist only inside EO 11157. Dozen intervening EO 11157 amenders checked: none touches sections 105/114. Effective date = signing date (no effective wording).
Sources opened: views/EO_11929.json, EO_11929.txt, EO_13294.txt, held texts of EO 11939..12935 (grep for 105/114).

## EO:9431: blocked
EO 9521 revokes it only as of the date of superseding Secretary of State regulations; none held (Foreign Service Regs S-5 in EO_9539.txt is about part 113, not IV-9/IV-10). Needs the Federal Register Secretary of State regulation(s) of 1945 or later designating EO 9431 superseded. Sheet state filled with blocked:... for both clauses.
Sources opened: views/EO_9431.json, EO_9431.txt, EO_9521.txt, EO_9539.txt (context), cruden searches.

## EO:8667: blocked
No end found; no held current source (jobs/current-law output has no entry; number and "Wintering River" searches find only the order and its APP copy). Needs a current USFWS/CFR record checked through 2026-10-14.
Sources opened: views/EO_8667.json, EO_8667.txt, jobs/current-law/output (grep).

## EO:11350: done
15 clauses. corrected-4 and -5 end 1967-06-30 (EO 11360 item 6(b) rescinds section 1626.25); corrected-13 ends 1971-03-10 (EO 11586 sec. 1(c) rescinds section 1632.9); corrected-12 gets EO 11586 as an amending later event (continues); the other 11 end 1986-02-25 by EO 12553, which lists "11350 Amending Selective Service regulations". Effective dates are signing dates (no effective wording). The section-regex search is a lead, not a proof of completeness.
Sources opened: EO_11350.txt, EO_11360.txt, EO_11586.txt, EO_12553.txt, texts of EO 11497/11527/11537/11563/11569/11606 (section grep).

## EO:12896: done
Both clauses end 1994-02-03 on the order's own terms. No current CFR text held.
Sources opened: views/EO_12896.json, EO_12896.txt, cruden searches.

## Tool defects
cruden.py search ignores --write for the search subcommand and prints all hits to stdout (large output); a rerun was needed with filtering. Order text for EO_12935 in fr-originals contains unrelated EPA text. I did not run kit.py batch-check, so the sheet is not machine-validated; evidence IDs (ACT:..., ACTOR_TEXT:...) were taken from the views' citable lists, and 'CLAUSES:EO:12896#sec2' as an own-text id was not confirmed against the checker.

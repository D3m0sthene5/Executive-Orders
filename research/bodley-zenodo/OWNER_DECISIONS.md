# Bodley release: decisions only the owner can make

Nothing here has been done. Each item names the recommendation and what it changes in the drafts.

**D1. Licences (data and code).** `.zenodo.json` and `CITATION.cff` carry the recommendation as a placeholder
(`cc-by-4.0`); `LICENSE-DATA.txt` and `LICENSE-CODE.txt` are not written yet.
- Data: **CC BY 4.0** (recommended) or CC0 1.0. CC BY makes every reuse carry the citation, and with it the
  "provisional, uncertified" label in the citation message; CC0 maximises reuse and matches the Lowande-Poznansky
  dataset (CC0 1.0). Zenodo accepts both (`cc-by-4.0`, `cc0-1.0` verified in its vocabulary). The repository has no
  LICENSE file today, so this is the first licence statement the project makes.
- Code (`code/`, `build_release.py`): **MIT** (recommended, shortest) or Apache-2.0 (adds a patent grant and NOTICE).
  Zenodo's `.zenodo.json` takes one `license`; a second licence is declared in the web form or in the licence file.
- Thrower's dataset has "custom terms" on Dataverse: the release cites it and does not redistribute it under either choice.

**D2. Timing.** Recommended: not before (a) the register is rebuilt so census, register and tracker describe the same
orders (the build refuses today: 14,972 vs 14,998 rows), (b) the Pergamon manifest and prior-art crosswalk are on `main`,
(c) the `UNNUMBERED_SUMMARY.json` exists so the second denominator is shipped, and (d) a Zenodo sandbox deposit has
passed. Publish version 1 only after the law-review draft needs a citable object, since the DOI is permanent and the
description must not outrun the evidence.

**D3. GitHub-Zenodo integration: yes or no, and on which repository.** Recommended: **no** on `Executive-Orders`
(it would archive a repository of about 9 GB with LFS pointers and licensed files, defeating the exclusions); use a manual
or API deposit of the built folder (route A in DESIGN.md), or, if you want release-triggered automation, a small
dedicated release repository (route B). Enabling it needs your GitHub-to-Zenodo account link, which I did not and may not create.

**D4. Author list.** Drafted: Danny Kind, NYU School of Law, ORCID blank. Decide whether to add contributors (Zenodo
`contributors` with a role, or `creators`), whether the AI systems are mentioned only in the description and methods
(drafted: yes, described as AI-produced, not as authors), and supply the ORCID if wanted. Names in `.zenodo.json` use
"Family, Given".

**D5. Text policy for the claims.** Drafted: every verbatim quotation replaced by hash and length (version 1). Options for a
later version: restore quotations only for official US Government sources (public domain); keep the title/president
index fields from compilations (drafted: kept, as facts about public documents); allow short fragments in authored
reasoning fields (drafted: allowed). Confirm, or ask counsel to confirm, that this meets any ProQuest terms you accepted.

**D6. The byte store.** Drafted: the release ships the Pergamon hash manifest, not the bytes. Decide whether a
public-domain subset (govinfo, Federal Register) is deposited as a separate Zenodo record (zipped, 100-file limit,
50 GB default plus a 150 GB allowance) or stays on the project's own storage with a second copy elsewhere.

**D7. Embargo and restricted files.** Drafted: fully open, no embargo (`access_right: open`). Zenodo supports
restricting files and an "Embargo until" date (files become public at midnight UTC); I found no stated maximum. An
embargo is the way to deposit early for a DOI while holding files until a paper appears; Zenodo metadata (title,
description) stays public either way. Also decide whether to drop `CODEBOOK_PROVENANCE.json`, whose record holds a local
path from the original session.

**D8. Zenodo sandbox first.** Recommended: you create the account (I may not) and test one draft at
https://sandbox.zenodo.org with the built folder, since Zenodo publishes no `.zenodo.json` schema and the local schema is
only my reading of the documentation.

**D9. Labels you may want stronger.** The Zenodo title and description say "provisional" and "uncertified". Decide
whether the file names should too (for example `provisional_status_ledger.csv` already does) and whether the `yes` statuses
(405: 193 in tier S1, 212 in tier S2) should be withheld from version 1 until reviewed.

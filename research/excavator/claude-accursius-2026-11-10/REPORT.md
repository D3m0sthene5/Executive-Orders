# Accursius, 2026-11-10: the Respondendi claim-kit fixes F3-F7

Named for Accursius, whose Glossa ordinaria made the Corpus iuris usable by gathering what earlier glossators held
apart. Track 2 of the Respondendi wave (PR #270, `research/excavator/claude-respondendi-2026-11-10/REPORT.md`):
the claim kit refused or dropped evidence the repository already held. Each fix is its own reviewed pull request.
Nothing here adopts a status, changes a count or touches the codebook. Human-certified: 0.

## The pull requests

| Fix | PR | What it does | Measured reach on main (undecided orders, machine-lead proxy) | Review |
|---|---|---|---|---|
| F3 | [#272](https://github.com/D3m0sthene5/Executive-Orders/pull/272) | U.S. Code notes published as attributed `.txt` extracts; theophilus section texts declared by their own identity; `current_evidence.py` resolves leads to them, each through its item's declaration | 1,063 of 1,294 with current-law leads get a `CURRENT:` record (0 before); 834 after #274 refuses amender listings; 604 theophilus texts no longer read as an order's own text | 1 blocker fixed; re-review approve |
| F4 | [#275](https://github.com/D3m0sthene5/Executive-Orders/pull/275) | Held Selden acting texts, statutes and FR citers, PLO texts and overflow actor texts become exact `ACTOR_TEXT` records; non-census actors kept with honest identities; basis-eligible official `SUPPLEMENT:`; unnamed instruments refused as a basis | 455 gain a citable basis record (320 basis-eligible non-census, mostly land orders; 136 census overflow windows); 1,002 gain lead-only records (federalregister.gov renderings); 224 of 439 overflow actor texts get ids | 3 blockers fixed; re-review approve; nits 1-3 fixed |
| F5 | [#274](https://github.com/D3m0sthene5/Executive-Orders/pull/274) | `OWN_TEXT` basis (spent_on_issue / amends_parent, whole scope, fail-closed classifier) and `PARENT_END` consequence records; `report_deadline` typing reviewed; YES refuses amender listings | 687 get OWN_TEXT records (261 spent, 426 amend-only; 321 had no NO basis); blind precision 57 of 60 (95%, CI 86-99%) | 3 blockers fixed; re-review approve |
| F6 | [#276](https://github.com/D3m0sthene5/Executive-Orders/pull/276) | Text gate accepts R37 `official_printing` and P4 `archival_replica_checked` with no page check owed, or a Lachmann confirmation; standing replace-and-recheck note | gate opens for 2,554 (tracker shows all original_supported or provisional); text-gate pass plus some NO basis 3,786 -> 5,067 | first review drove the narrowing; re-review approve |
| F7 | [#273](https://github.com/D3m0sthene5/Executive-Orders/pull/273) | Segmenter headings (letter-spaced, `1-101`, Part runs); FR page spans and OCR closing tags; `machine_hits` from MENTIONS.csv; checker fused footnote numbers | 497 undecided clause inventories change; 558 orders' machine hits go 0 -> positive; locator fixes need an fr-originals re-location run | 3 blockers fixed; re-review approve |

## The 84 diagnosed Papinian failures (Respondendi DIAGNOSIS.csv)

- F3: 11 of the 15 YES-leaning orders now hold a `CURRENT:` record (EO 10624, 11225, 12661, 13329, 13505, 13647,
  13748, 14051, 14191, 14233, 14318); 8695, 13411, 14435 have no current-law lead.
- F4: basis-eligible records for EO 8790 (three PLOs) and 8649; census windows for EO 13354 (EO 13470) and 14231; EO 13204's FR rescission rules are leads only (federalregister.gov renderings). EO 9211, 9372,
  9181, 9231, 8617 stay without one under D-20261021-unnamed-instruments.
- F5: OWN_TEXT for EO 12178, 12378, 12379, 13013, 13552, 7621 (and 10816, 11728, 11816, 13024, 13820); 13116 and
  13064 gain retyped TERM records.
- F6: the text gate opens for EO 4770 (and Haloander 2145, 3761, 4041).
- F7: the artifacts behind EO 7573, 8109, 9446, 10195, 11202, 11575, 11813, 12072 and 13294 are fixed; none alone
  supplies a basis.
Every count is an upper bound on eligibility: each record is a lead a producer confirms and an independent reviewer
checks. Whether a printed U.S. Code note proves an order in force, or an agency text ends one, stays a legal judgment
for producers and reviewers (D-20261028-evidence-decides); no new owner question was needed.

## What review found (all fixed before approval)

Every first review by a different model found real defects: F3 a pin bypass through a lead's own path; F7 a checker
that let an unknown order through as an ending actor and a neighbour-page adoption that stored a truncated tail as
found; F5 a classifier that failed open (EO 8100's forest reservation passed as spent on issue) and false TERM records
from "retained"; F6 a grade-based credit the tracker does not give. The own-text classifier went through three blind
reads (Sonnet 5.5, labels sealed): 85% and 84% on the first versions, 95% on a fresh sample once it failed closed.

## After merge

- One claim-kit rebuild on main after #272, #273, #274 and #275 (compiler files: current_evidence.py, excavate.py,
  build.py, inputs.py); every prepared packet and frozen overlay evidence must then be re-prepared
  (`stale_compiler_code`). Existing supplement packets too (#275).
- #274, #275 and #276 touch neighbouring lines of `status_overlay._decision_errors` and `UNDECIDED_ROUTES`: the later
  merge needs a small rebase (take the union of the route names; keep the SUPPLEMENT condition and the OWN_TEXT check).
- An fr-originals run that re-locates the candidate orders listed in #273 (`f7/fr_pages_B.csv`, `C`, `E`): its
  `carry_forward` keeps old spans otherwise. current-law and theophilus-sources rerun in the scheduled sweep; a
  current-law network run adds statute-section extracts.
- Follow-ups: wiring R37/P4 grades into `working_text`/`assemble` (lifecycle claims on those texts are still refused);
  neighbour-page adoption redone strictly; F3 mid-word quote windows; envelope check of the frozen original against
  the compiled `selected` row (a whole-file swap passes today, as on main).

## Cost (Bentham usage, `WORKERS.csv`, list prices)

181.58 USD for 11 agents: coordinator (Opus 5.5) 51.60; workers F3 13.73, F4 36.02 (Opus 5.5), F7 7.50 (Sonnet 5.5);
reviewers (Fable 5.2) F3 10.80, F7 17.16, F5/F6 21.47, F4 21.26; blind readers (Sonnet 5.5) 2.04.

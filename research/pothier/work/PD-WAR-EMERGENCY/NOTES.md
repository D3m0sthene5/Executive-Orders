# PD-WAR-EMERGENCY working notes (2026-11-05)

## Read in the repository

- `research/pothier/work/AUTHOR_BRIEF.md`, `research/pothier/DOCTRINE_SCHEMA.md`, `jobs/pothier/pothier.py` (engine, validation and date rules).
- Owner rulings: `research/readiness/owner_rulings/2026-11-05-empty-status-history.md`, `2026-10-28-evidence-not-convenience.md` (one-time commands need evidence of performance; an interval needs evidence that the event happened in it), `2026-10-21-until-and-further-exempt.md` (a stated end date is inclusive).
- Type rules `research/readiness/type-rules/TR-WWI-EMERGENCY.json`, `TR-ALIEN-PROPERTY-SALE.json`, `TR-EIGHT-HOUR-SUSPENSION.json`.
- X1 event `X1-E1-WWI-1921` in `jobs/x1-class-engine/data/EVENTS.json` and its state in `jobs/x1-class-engine/output/EVENT_SOURCES_STATE.json`. Its held text is `jobs/astra-source-retention/output/pages/d811bcf2.../selected-pages.txt` (sha256 881d541d...), which I read in full. The resolution names no list of Acts. It works generally, on every Act contingent on the war's duration, and excepts the Trading with the Enemy Act and its amendments, the Liberty Bond Acts, titles 1 and 3 of the War Finance Corporation Act, Pub. Res. 55, and Title 2 of the 1919 Food Control and D.C. Rents Act. It reaches Acts, joint resolutions and proclamations, not executive orders.
- Member texts. I read the operative parts of all 97 `wwi_emergency` texts, the 7 `labor_hours_suspension` texts, EO 6023 and about 25 of the `alien_property_sale` texts in full. I then scanned all 158 alien-property texts by machine for rejection, amendment, resale and release wording, for time limits (none found), and for non-alien-property content (8 found).
- Held context: EO 9788 (`jobs/source-ladder/output/texts/EO_9788_2e0f1ac5d8.txt`) and EO 9095 (`jobs/source-ladder/output/texts/queue_EO_6694_EO_9095_4f3b011a51.txt`).
- `kean search "First War Powers"` and `kean search emergency war 1921` returned only First War Powers Act (1941) material and the ice-core report's note that its expiry texts are missing. That concerns the Second World War and does not bear on this family. `held.py` found 41 Stat. 1359, EO 9095 and EO 9788 held. It found the Lever Act, the Overman Act, 40 Stat. 411, 39 Stat. 1192, 42 Stat. 105, EO 6694 and EO 11281 not held.

## Read on the web (WebFetch / WebSearch)

- Overman Act, https://www.govinfo.gov/content/pkg/STATUTE-40/pdf/STATUTE-40-Pg556.pdf (duration proviso on p. 556) and STATUTE-40-Pg557.pdf (sec. 6 and the termination paragraph on p. 557).
- Lever Act, https://www.govinfo.gov/content/pkg/STATUTE-40/pdf/STATUTE-40-Pg276.pdf (sec. 24 on pp. 283-284). STATUTE-40-Pg283.pdf does not exist; govinfo serves PDFs only from the first page of each chapter.
- Emergency shipping fund, https://www.govinfo.gov/content/pkg/STATUTE-40/pdf/STATUTE-40-Pg182.pdf (cessation sentence on p. 183).
- Treaties: https://www.govinfo.gov/link/statute/42/1939 (Germany, proclaimed Nov. 14, 1921) and https://www.govinfo.gov/link/statute/42/1951 (Hungary, proclaimed Dec. 20, 1921). STATUTE-42-Pg1939.pdf returned a not-found page, but the link service works.
- Knox-Porter Resolution, https://www.govinfo.gov/link/statute/42/105.
- NARA Guide to Federal Records, RG 63 (Committee on Public Information) and RG 182 (War Trade Board).
- EO 11281, at the OFR codification page.
- HathiTrust record 001756793, the Alien Property Custodian Report for 1918 to Feb. 15, 1919. The record page shows no item links.

## Decisions taken and rejected

- **The 1921 resolution as a direct end for every `wwi_emergency` order: rejected.** It ends statutes contingent on the war, not orders. An order ends with it only where the statute the order rests on, by its terms, reaches the orders made under it. Three statutes do:
  - The Overman Act ("any authorization of the President under this Act to the contrary notwithstanding").
  - The emergency shipping fund section ("or by him delegated").
  - The Lever Act, on a reading flagged for the owner: "the provisions of this Act shall cease to be in effect", applied to orders that only delegate those provisions.
- **Single acts (vessel seizures, transfers of piers, ships and records, sale authorizations): kept `open`.** The owner's ruling of 2026-10-28 requires evidence that the act was performed. EO 3176's recital that enemy vessels "have been taken over and operated" is general and names no vessel, so it does not prove the named seizures.
- **Rejection-of-bids orders: kept `open`.** They are authorizations to the Custodian ("is hereby authorized and shall have the right to reject"), not self-executing rejections. EO 2955-2958 declare a sale void but also direct the Custodian to reject the bids.
- **A class event ending unexercised alien-property authorizations: none found.**
  - The Trading with the Enemy Act is excepted from 41 Stat. 1359 and is still law (50 U.S.C. 4301 ff.).
  - EOs 6694 (1934), 9095 (1942) and 9788 (1946) transfer functions. EO 9788 is held and its text vests all functions and property in the Attorney General.
  - EO 11281 (1966) concerns the Second World War blocking controls.
  - Knox-Porter sec. 5 retains enemy property.
- **EO 2837 moved out of the spent branch.** Besides revoking two licensing powers, it forbids licenses "until further order", a continuing command. EO 3180 rescinded it.
- **EO 2765 moved from the EO 3320 branch to the Lever Act branch.** EO 3320 saved sugar licenses and sugar regulations.
- **EO 2826 ("During the continuance of the war and until further orders"): kept `open`,** because it can be read to continue past the war until a further order. EO 2652 ("for the duration of the war") was decided, with an upper bound of Dec. 20, 1921.
- **The Overman Act's end date: claimed as an interval with an upper bound of June 20, 1922.** Three readings disagree: Sept. 3, 1921 under 41 Stat. 1359, May 14, 1922 from the German treaty, and June 20, 1922 from the Hungarian treaty. No court or Attorney General opinion fixing the date was found in a short search.
- **Misclassified members.**
  - EOs 3042, 3060A, 3085, 3097 and 4224 hold texts of other kinds of order (land, civil service, consular, visa fees), so they are routed out.
  - EO 3087A's held text reproduces EO 3086-A.
  - EOs 3064, 3091 and 3099 are typed `alien_property_sale` from run-on WPA summaries but are First World War orders that this family's mechanisms decide.
  - EOs 3016C, E, G, P and Q are typed `wwi_emergency` but are Frank L. Polk's alien-property sale orders, so they go to B18.

## Effort

About 3 hours of agent time: roughly 45 member texts read closely, 10 web fetches of primary sources and finding aids, and 5 `try` iterations. The final run gave 263 members, 55 decided and 0 contradicted.

## Coordinator rulings applied (2026-11-05, second pass)

Applied `research/pothier/COORDINATOR_RULINGS.md` (P1-P6) and the coordinator's four decisions:
- B13, B14 and B15 now use lead kind `ended_with_delegated_statutory_power`, require delegation (or Overman reassignment) to be the member's only operative content, and quote the statute's ceasing words. This moved three members out to the new open branch B13X: EO 3247 (a suspension), EO 2825-A (takings and compensation) and EO 3063 (a contract-transfer directive). EO 3059 and 3086-A moved into B15.
- B03 is split into P1 `spent_on_issue` (4 members), P2 `merged_into_parent_on_issue` with the disclosure (9 members) and B03C (EO 3176 taking title, 1 member).
- B09 is now open, because EO 3154's end is conditional on an unrecorded transfer. B12 was dropped. B11 is now an open named-person branch under P4: it holds EO 2907-A, 2997 and 3024-C from the EO 3320 group plus EO 3024-A and 3057.
- B01 now names the family each member belongs to.
- Added source S0 (`member_text`).
- Result: 263 members, 43 decided, 220 open, 0 contradicted.

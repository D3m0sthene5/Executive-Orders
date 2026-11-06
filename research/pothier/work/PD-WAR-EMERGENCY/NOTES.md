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

## Revision after blind review (2026-11-06, reviser taking over from the author)

### Read

- `research/pothier/work/AUTHOR_BRIEF.md`, `DOCTRINE_SCHEMA.md`, `COORDINATOR_RULINGS.md` (P1-P8), `work/REVISION_BRIEF.md`, the doctrine .md and .json, this file, and both reviews (`/home/claude/pothier-review/PD-WAR-EMERGENCY-A/REVIEW.json`, `-B/REVIEW.json`).
- `jobs/pothier/pothier.py` (conditions, date rules, contradiction check: it flags only `yes` or `persists` leads with ending edges, `no` leads with living edges dated after the lead's end, named-person hits and current-law predicates; it does not check pins).
- Every family member's `later_edges` in `jobs/pothier/output/MEMBERS.jsonl`: 29 members carry edges. The non-cross-reference ones are listed in the .md section (e).
- Member texts read for this revision: EO 3259, 3265, 3227, 3183, 3016C, 3016K, 3016L, 3019-A, 3161, 3248-A, 3249, 3091, 3222, 3283, 3059, 3086-A, 3087-A, 2868, 2929, 2652, 2967, 2743-A, 2663, 2678, 3320, 3087, 2884, 3100, 2736, 3143, 2679-A, 2888, 3018, 3064, 2687, 3549, 2645 (and the Wikisource notes on EO 2645, 2770, 2729-A, 2687), 3923, 4224, 5427, 3247, 3240, 3173, 3235, 3094-B, 3132, 3374. Machine search of all family texts for recitals of completed sales (only EO 3265 records the sale its parent authorized), for "any and all other" or "other powers" recitals in every P7 and P8 member, and for printed dates against census dates on every decided member.
- The held 41 Stat. 1359-1360 text, re-read for its operative words.
- Web (WebFetch): govinfo 37 Stat. 137 (sec. 2 of the 1912 eight-hour Act, on p. 138: "during time of war or a time when war is imminent"); govinfo link 40/535 (Act of Apr. 22, 1918, ch. 62: amends the 1917 section "by adding a new provision", no termination of its own); govinfo link 40/374 (Oct. 6, 1917 shipping fund section: raises cost limits only; page not verified); govinfo STATUTE-40-Pg276 (Lever Act sec. 24, confirming the proclamation clause); NARA RG 131 (EO 9095, EO 9142, EO 6694, EO 9788, EO 11281). The govinfo FR link service did not resolve 12 FR 2038 (PLO 369); a web search did not find the issue.
- `held.py`: no treaty, Overman Act, Lever Act, 1912 Act, 42 Stat. 105, PLO 369 or EO 2687-A text is held.

### Changes and why

- **EO 4224-A out of P2 (now B18 open).** Coordinator adjudication and both reviews: its only operative clause is a quit-claim authorization; "amend" appears only in its stated reasons. The P2 branch condition was also anchored on operative amending words, because the bare regex "amend" matched the Trading with the Enemy Act recital ("the amendment to such Act") present in every sale order.
- **EO 3259 decided (B03E, `no`, TERM, `exhausted_by_performance`, interval 1920-04-16 to 1920-04-29).** Coordinator adjudication; EO 3265 records "the actual sale made by the Alien Property Custodian". EO 3227 and the Polk orders checked the same way: EO 3227's "in the case of sales heretofore made" is conditional and names no property, so EO 3016C, 3016K and 3227 stay open. EO 3183 (rejection authorization for the same shares) stays open with the evidence disclosed and flagged for the coordinator.
- **Overman branch split.** EO 3019-A, 3161, 3248-A invoke "any and all other Acts of Congress" and EO 3249 "all other powers thereto me enabling": moved to new open branch B15X. EO 2868 rests on the 1916 Council of National Defense provisions: B16 is now open. EO 3019-A's own cap ("in no event longer than the proclamation of peace") covers only its first exception and the treaty texts are not held, so it decides nothing. B15 keeps EO 3059, 3086-A and 3091, which rest on the Overman Act alone (EO 3222, which amends EO 3091, also rests on it alone), and the branch now requires the absence of "any and all other / all other powers / Chief Executive" in the text.
- **Same defect found in the Lever Act branch.** EO 3235 ("and other powers vested in me by law") and EO 3240 ("all other powers me hereto enabling") moved from B13 to the open branch B13X, applying the coordinator's Overman ruling to the identical P8 question. B13 now has 4 members and carries the same "not other powers" condition.
- **EO 2888 vs EO 3018.** The Act of Apr. 22, 1918 inserts its provisions into the 1917 section, so EO 2888 (resting on it alone) joins B14 with the reading disclosed. EO 3018 and EO 3064 also delegate powers under the July 1 and Nov. 4, 1918 shipping fund sections, which have not been read, so both moved to new open branch B14X. This is a decided-to-open change for EO 3018 and 3064, made because the "herein" reach for those sections is unverified.
- **B07/B08 lead kind** set to `ended_by_express_abolition_of_its_subject` (P7). The B07 basis now quotes EO 3320's liquidation-only clause and explains that EO 3087's Grain Corporation authority ran "with the approval of the United States Wheat Director", its other parts being completed acts. The B08 basis quotes EO 2884's "subject to the control and direction of the United States Food Administrator" and EO 3100's "under the direction of the United States Wheat Director".
- **B20 basis corrected.** Sec. 2 of the 1912 Act is war-contingent. The 1921 resolution's words govern how Acts are construed and do not reach a waiver already granted for a specific contract (an exercise of the power, not a delegation), so EO 2663 stays open with March 3, 1921 as a candidate end. Whether the resolution reaches the 39 Stat. 1192 proviso is now stated as unsettled.
- **EO 9095 vs EO 9142** corrected in M12, B18 and B19 (EO 9142 moved the Alien Property Division; source S27, NARA RG 131).
- **Census-date conflicts.** B17 (EO 2652) now runs from 1917-07-03, B06 (EO 2929) from 1918-07-31, and EO 2967 has its own branch B03D fixed at 1918-09-26.
- **B02 (EO 3087-A)** now quotes the transcription's "There is no record in Archives or State Department of any Executive Order bearing this number. See No. 3086-A", and its gap is a census question.
- **B01 (EO 4224)**: the held text is EO 4224½; EO 5427's supersession names "4224½", so the edge belongs to the visa-fee order, not to the sale order.
- **Held later edges disclosed** on their branches and in .md section (e): EO 3923 (PLO 369 number collision), EO 2645 (EO 2687-A supersession, editor's note only), EO 3091 (EO 3222), EO 3249 (EO 3283), EO 3233 (EO 3247 edges misread its exception), EO 3017 (spurious EO 3800 edge), EO 2729-A (partial revocations), EO 3016 (Polk orders reciting it), EO 2664, 2679-A, 2744, 4001, 2604, 3259.
- **Smaller fixes**: count of the "later order" group (now split into P7 abolition 6 and revocation 2); B19's reference to the nonexistent B12 replaced by the War Trade Board candidate end; EO 3086-A's own pin; Lever Act sec. 24's proclamation clause quoted, with the 1921 resolution's displacement of it; the RG 63 finding aid described as weak evidence of the CPI transfer; EO 2687 described as a mixed order; EO 3173 added to the EO 3247 suspension gap; EO 3549's quotation of Merchant Marine Act sec. 17 cited in B14's gap.
- `FETCH_PROPOSED.jsonl` rewritten (21 lines): branch counts and references corrected, and new lines for the 1912 Act, the Act of Apr. 22, 1918, the Oct. 6, 1917, July 1, 1918 and Nov. 4, 1918 shipping fund sections (the last two pages unverified), NARA RG 131, PLO 369, and EO 2687-A.

### Findings ignored or not adopted

- Planted errors, ignored as instructed: A R1 (Overman Act at "40 Stat. 565"), A R2 (B13 bound 1921-07-02), B R1 (joint resolution at "41 Stat. 1395"), B R2 (EO 2952 dated 1918-06-09). The real file had none of these.
- B R3's statement that 39 Stat. 1192 is settled as not war-tied (citing a 1939 use, EO 8198) was not adopted as settled. EO 8198 is not held, and A R9 is right that the question is one of construction. B20 is open either way.
- B R7's alternative of resting EO 2884 and 3100 on the Lever Act's cessation was not used. P7 decides them on held text, and the coordinator chose P7.
- B R13's option of keeping EO 4224-A under P2 was rejected, per the coordinator.
- No other finding was rejected.

### Result

263 members; 35 decided (18 TERM, 17 ACT), 228 open, 0 contradicted (`python3 -I jobs/pothier/pothier.py try`). Branch counts: B01 5, B02 1, B03 4, B03D 1, B03B 7, B03C 1, B03E 1, B04 1, B05 1, B06 1, B11 5, B07 2, B08 4, B09 4, B10 1, B10A 1, B13 4, B13X 5, B14 2, B14X 2, B15 3, B15X 4, B16 1, B17 1, B18 153, B19 8, B20 7, B21 19, B99 14.

Effort: about 2 hours of agent time; roughly 50 member texts read, 7 web fetches and 3 searches, 6 `try` runs.

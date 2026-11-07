# Baseline for the article: what Lowande and Poznansky measure, and what the project could say against it

Draft for the article's thesis section. Tier: prior-art reading plus recomputation from public replication data; every
project figure is quoted as the project's own documents state it, with its tier. This file states no new legal finding.
Numbers marked "run" come from `scripts/lp_headlines.py` and `scripts/thrower_summary.py` (outputs in `output/`).

## 1. What L&P measure

- **Unit and universe.** One row per executive order, 6,536 orders issued 1937 to 2021 (the deposit has 64 rows for 2021;
  see README.md on the cutoff), numbered orders only (the deposit has no EO number).
- **Outcome.** `revoked_next_term`: the order was formally revoked by the end of the following presidential term, in the
  disposition tables (article pp. 354-355; SI-2). My reconstruction, tested against Thrower's data in README.md: terms
  are the four-year blocks 1937-40, 1941-44, ..., "following" is the next block, and a revocation counts if it falls by
  that block's last year. It reproduces L&P's per-year shares with correlation 0.991 (mean absolute difference 0.66
  percentage points over 72 years). That is a labelled hypothesis; the L&P codebook is not in the deposit.
- **Population.** Their main models drop ceremonial orders (113 of 6,536 in the data, run) and, through missing
  `opposing_next` for 2021, 50 further rows: 6,373 observations (Table C.1, SI-11).
- **What it can detect.** A formal revocation recorded by the end of the following term, by any president: the
  following term can be the same president's, and about 29% of revoked orders were revoked by the president who first
  signed them (note 4, p. 353). The window is 1 to 7 years, and for orders issued 2017-2020 it runs past the mid-2021 end
  of the data, so it is cut short there (for 2021 orders it is almost empty). By design it excludes revocations "decades
  latter", which the authors say they set aside as "housekeeping" (p. 355). It measures political reversal, not whether an order
  stopped operating, and it uses formal disposition as the only evidence of an end.

## 2. L&P headline numbers: recomputed against the article

| Quantity | Article | Recomputed (run) | Match |
|---|---|---|---|
| Orders in sample | "nearly 6,500" (p. 351), SI-7: 6,536 | 6,536 rows, years 1937-2021 | yes |
| Observations, main model | 6,373 (Table C.1, col. 1) | 6,373 | yes |
| Observations incl. ceremonial | 6,486 (col. 3) | 6,486 | yes |
| AIC, main model / incl. ceremonial | 4,221.076 / 4,268.891 | 4,221.076 / 4,268.891 | yes |
| Logit coefficients, col. 1 | e.g. constant -2.697 (0.156), immutable -0.920 (0.226) | -2.697 (0.156), -0.920 (0.226); all 23 coefficient magnitudes agree to 3 decimals (signs were lost in the SI text extraction); standard errors within 0.003 (largest gap: `issuing_divgov:immutable`, column 3, 1.068 vs 1.065) | n, AIC and all coefficients reproduce to 3 decimals; yes |
| Baseline probability revoked in the following term | "11%" (p. 356) | 11.44% all rows; 11.60% non-ceremonial | yes |
| Immutable share of orders | "about 41%" (p. 353) | 41.4% all rows; 42.0% non-ceremonial | yes |
| Immutable share, issued under divided vs unified government | "-19 pp." (p. 353) | -19.4 pp | yes |
| Immutable share since the Reagan administration | "about one in five" (p. 356) | 21.6% for 1981-2021 | yes |
| Revoked next term, immutable vs mutable | intro: "about 9 percentage points" (p. 345) | non-ceremonial: 6.1% vs 15.6% = 9.5 pp | yes (rounding) |
| Marginal effect of immutability, Figure 1 | "about 6.6 pp." (p. 356) | -6.7 pp (point estimate, observed-case, rows as in `figures.R`; the article's figure is a simulation mean) | yes within simulation error |
| Never revoked | "About 75%" (p. 345), "74%" non-ceremonial (p. 354) | not in `orders.Rda`; from Thrower's list 1937-2013: 74.3% of 6,158 never revoked, 74.0% among non-ceremonial. But 426 of the 4,578 never-revoked orders are coded superseded, so 67.4% (4,152) are neither revoked nor superseded; "never revoked" is not "formally still valid" | consistent, different data |
| Revoked ever, mutable 30% vs immutable 21% (p. 354) | as stated | cannot be computed: no ever-revoked variable in the deposit | not checked |
| Revoked by end of following term, all orders | n/a | 748 of 6,536 (745 of 6,423 non-ceremonial) | n/a |
| Chiou-Rothenberg scores (3,512 orders) | p. 354 | not in the deposit | not checked |

Two things in the source that the table does not settle. First, the article says the sample ends on January 18, 2021
(p. 351) while the SI says it includes "the first half of 2021" (SI-2); the data hold 64 rows for 2021 and the master
register has 11 orders dated through January 18 and 65 through June 30. The data agree with the SI. Second, the 6.6
versus "about 9 percentage points" figures describe different things (a model-based marginal effect that holds
other covariates fixed, and a raw difference), both in the article.

## 3. What the project holds now (as of origin/main `57b81411`, 2026-11-06)

All figures are the project's documents' own words, with their tier. None is a certified whole-lifecycle finding.

- Population: the working census is 14,972 identities (`research/justinian/ESTIMAND.md`); the readiness tracker on main
  reports 14,998 orders in `jobs/readiness-tracker/output/SUMMARY.json` (generated 2026-11-06). L&P cover about 6,500
  numbered orders 1937 to mid-2021, about 44% of the census by count (6,536 of 14,972).
- Readiness tracker summary: 4,298 orders with a provisional status; 1,185 ready for human review; 1,527 claims
  (1,343 v1, 184 v2, all `not_later_than`); `human_verified`: not counted here. **Human-certified whole-lifecycle
  dossiers: 0.** Tiers stay separate: machine lead, provisional ledger, AI-reviewed claim, ready dossier, certified dossier.
- Headline estimand (owner ruling R1): the share of orders with an operative clause on 2026-10-14, i.e. operative force,
  codebook `present_normative_effect`, not formal validity (ESTIMAND.md). Formal validity is a separate column.
- Sample estimate (`research/dorotheus/SAMPLE_ESTIMATE.md`, provisional, AI-reviewed, uncertified, n = 120 stratified
  sample, 19 respondents): operative force 0.0% (95% interval 0.0% to 17.6%) responses only; sensitivity 0.0% to 79.7%
  bracketing nonresponse; formal validity (unrevoked on the books) 0.0% (0.0% to 26.5%; 12 respondents). Cleanup question:
  `formal_revocation_after_earlier_cessation` is true for 1 of 19 NO responses (11 no, 7 unknown). The document says the
  interval "understates the uncertainty": 16% response, non-random, with no respondents in two strata.
- Re-tagged claims: 184 ready NO claims whose shared end date is a formal revocation that the claim text marks as a later
  cleanup of a spent order were re-tagged `not_later_than` (owner ruling R3; ESTIMAND.md, rule 4). These are
  AI-reviewed bounds, not evidenced earlier ends.

## 4. What the project can and cannot say against the baseline today

Can say, as framing and with citations:

1. The best published quantitative baseline for formal revocation is L&P (with Thrower): about three quarters of orders
   are never formally revoked (in Thrower's list 426 of those were superseded, so 67.4% were neither revoked nor
   superseded), and about 11% are revoked within the following term. That is a statement about formal
   disposition, which in the project's codebook is a separate axis from operative effect (TC01: "never derive current
   force from a formal label alone").
2. L&P themselves give prior art for the project's concern. They call formal revocation a poor guide to whether an
   order is active ("alive" on paper; no rule requires an inactive order to be revoked: SI-2, SI-3), and read EO 12553
   as a housekeeping revocation of orders that had outlived their function (SI-3). They did not measure this.
3. Counts from Thrower's list, run: 1,580 of 6,158 orders (1937-2013) are coded revoked; 377 carry revocation
   year 1986 (23.9% of all revocations; the SI says EO 12553 revokes "over 360", about 23%). Thrower's own EO 12553
   flag (`revokedbyeo12553`, in the main `.dta`, not in the CSV) covers 372 orders, 370 of them with revocation year
   1986; the project's later-events table (`jobs/later-events/output/EDGES.csv`) has an EO 12553 revocation edge for 383
   orders in the 1937-2013 range (recomputed). The three counts differ by definition and none is a settled list. The
   median gap between issue year and revocation year for the 377 with revocation year 1986 is 25 years, and 66% are 20
   or more years. Across all revoked orders the median gap is 7
   years, a quarter are 19 or more years, a tenth 33 or more. So a large part of the formal revocation record falls outside
   the window L&P analyse. This says when revocations were recorded, not whether the orders had stopped operating.
4. In the project's own reviewed sample, formal revocation after an earlier cessation was recorded in 1 of 19 responding
   NO orders (7 unknown). That is tier "AI-reviewed, uncertified", n = 19, with non-random response, and it does not
   test the thesis.

Cannot say:

- That formal revocation "often" cleans up an order that had already ceased. The project holds no sample drawn from
  formally revoked orders, no evidenced earlier end date for a stated set of them, and no certification (0 certified
  dossiers). The single 1-of-19 figure is uninformative on this, and the respondents are selected for having a
  documentable ending.
- That the 0.0% operative-force estimate contrasts with L&P's 75% never revoked. The two are not comparable: different
  universe, different date, different outcome, and the sample's respondents are not representative (16% response).
- That L&P's immutable orders are operative. Immutable is a function-of-title classification of irreversible outcomes
  (p. 352), not a legal-effect finding; see CROSSWALK.md (TC06, TC07).
- Anything about which specific orders L&P count as revoked: the deposit has no EO numbers. README.md's alignment
  holds, as a hypothesis, for 22 of the 73 testable years (1,937 of 6,536 rows); the other years remain unaligned.

## 5. What the project would need to test "formal revocation often cleans up an order that had already ceased"

State the claim as an estimand first: among orders that were formally revoked, superseded or nullified, the share whose
evidenced first cessation (operative end, codebook `first_cause_type` other than `unresolved`, `date_kind` exact or
interval) is earlier than the formal disposition date by more than a stated margin. Keep formal validity and operative
force separate throughout (TC01), and apply TC13 (a later cleanup revocation supplies at most the latest cessation unless
an earlier episode end is proved).

1. **A sampling frame of formally revoked orders with EO numbers and dates.** L&P/Thrower supply counts, not the list in
   the deposit. Sources: the order-level L&P dataset (REQUEST_EMAIL.md), Thrower's list (public, 1937-2013, joined to the
   register by EO number: all 6,158 rows join), and the National Archives and Federal Register disposition tables for
   the rest. Exact revocation dates are needed, not years.
2. **A random sample from that frame, stratified by the revocation's shape,** at least: mass-revocation instruments
   (EO 12553: 372 to 383 orders depending on the source, see section 4) versus targeted revocations; revocation lag (under 8 years, as L&P study, versus 10 or
   more years); era; and order function (L&P's immutable code is a usable stratifier once aligned). Draw blind to
   hypothesis, with replacement draws for source-blocked orders so non-response is not silent.
3. **An evidenced earlier end, or a documented absence, for each sampled order.** Whole-lifecycle claims under the v2
   schema with `date_kind` exact or interval, a complete clause inventory, savings and later-event checks (TC03, TC08,
   TC10, TC11, TC14). `not_later_than` bounds do not count as earlier ends (rule in CLAIM_SCHEMA.md). The 184 re-tagged
   claims are leads, not data.
4. **Independent human certification of the sampled claims.** Today 0; the AI-reviewed tier cannot support a published
   frequency. A defect bound for the AI tier (reviewer catch rate 25 of 30 plants, SAMPLE_ESTIMATE.md) would have to be
   carried into the interval.
5. **Size.** For a proportion of 0.5 and a 95% interval half-width of 0.10, 0.075 or 0.05, about 96, 171 or 385
   orders with a determinate answer, by the usual normal approximation; with a 16% response rate (19 of 120) the draw is
   several times larger, so selection into "resolvable" must be modelled or reduced, not assumed away.
6. **Comparison to L&P's window.** With order-level data and the alignment (or a request fulfilled), report the formal
   revocation timing distribution by stratum next to L&P's within-next-term indicator, so the article can say which part
   of the formal record their outcome covers.

## 6. Limits of this baseline

- The L&P term rule is reconstructed, not documented; the codebook is absent from the deposit.
- The recomputation reproduces the published regression (n, AIC and all coefficients to 3 decimals; standard errors
  within 0.003), which shows the deposit matches the article's
  analysis file; it says nothing about the accuracy of the underlying revocation coding (20 missing, 65 misattributed;
  not enumerated).
- Thrower's revocation years are the disposition tables' years as of Thrower's collection, which L&P say were later
  revised (SI-2).

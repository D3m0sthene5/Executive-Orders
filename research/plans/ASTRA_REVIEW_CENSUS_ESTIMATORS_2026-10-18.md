# Adversarial review of the census estimators

Reviewer: Astra. `reviewer_role: ai_review`. Review date: 2026-10-18 ET.
Base: `0d860bde15538d38fafea26cea03f152d0127f5e` (fresh main).
Scope: `jobs/census-completeness/complete.py`, current `output/REPORT.md`,
`ESTIMATES.json`, mentions, matches, clusters and tests. This is a review of held
code/data, not a census adjudication. No identities, code, outputs or counts changed.
Input SHA-256s, exact examples and reproducible calculations are in
`research/readiness/reviews/astra-2026-10-18/CENSUS_DIAGNOSTICS.json`; run the adjacent
`audit_census.py` from any directory. No source was fetched for this review.

## Decision

Keep the descriptive overlap inventory and the three matching sensitivity runs.
Withdraw the assertions that these are verified distinct codebook EOs, that every
estimate is a lower bound, and that truth lies between the loose and strict runs.
Mt is a useful independence-model diagnostic, not yet a defensible headline census
estimate. Fix the matcher and define the capture population before fitting a richer
model. The large disagreement with the singleton/doubleton calculation is a warning
about the design, not evidence that Mt is right.

## What holds

* `chapman` implements `(n1+1)(n2+1)/(m+1)-1` and the usual finite-sample variance
  algebra correctly for valid two-list inputs. It is a sensible diagnostic when the
  lists target the same population and the independence/catchability assumptions
  are defensible. Its nominal interval does not measure linkage uncertainty.
* `mt_mle` solves `prod(1-n_j/N)=1-S/N`; the two-list case reduces to `n1*n2/m`.
  `mt_ci` uses the stated asymptotic variance consistently; it reduces to the usual
  large-sample two-list variance. This supports the algebra, not the real-data model.
* Letting list probabilities differ is appropriate in principle. A small specialist
  list and a large compilation need not have the same inclusion probability.
  However, Mt still makes every eligible order equally catchable *within* each list.
* Separating WPA-numbered clusters from an explicitly unnumbered target population
  is sensible. Treating WPA and Lord as independent captures of the same population
  would be inappropriate. The implemented exclusions depend on linkage, however.
* Citation links and blind links are separately retained; ambiguous pairs remain
  inspectable. The source-universe map exposes unsurveyed collections. Unmatched
  mentions are correctly identified as leads requiring adjudication elsewhere in
  the report. Preserve these features.

## What does not hold, and what to change

### 1. Month precision is lost and transitive matching collapses identities

In `match_mentions`, every non-day LORD entry is put into `lord_year_only`, including
month-precision entries. Two shared words then connect it to any exact date in the
year. The current output contains **12 cross-month edges involving month-precision
Lord entries**. For example LORD:U:0911 links to RICH_IX-031 (1891-01-26), -039
(1891-02-18), and -040 (1891-02-21), using `civil|rules|service`. These words are not
identity-discriminating in civil-service records.

Union-find then merges through a common intermediary without checking whether the
whole component has compatible dates, subjects, source members or numbered IDs.
Among 1,476 exported clusters (including numbered), **89 have multiple members from
one source and 55 have multiple exact dates**. Those are diagnostic flags, not 144
proven errors; sets overlap, reprints and conflicting metadata may explain some.
The synthetic month-precision fixture shows three records with January/February/
March dates collapsing into one without a citation link.

Fix: retain month constraints; require adjudication for generic-token edges;
quarantine incompatible components before union; distinguish multiple printings of
one order from multiple orders; record accepted/rejected links and reasons. Do not
change census identities from this review. An audit must validate input eligibility,
not just whether the final clustering code ran as written.

### 2. Unequal list size is not enough to justify Mt

These are nonrandom, subject- and era-selected books. Richardson volumes cover
different periods; MR/GLO repeatedly print reservation material; ordinary archival
letters may have essentially zero chance of appearing. Zeros due to a list's remit
are not merely small common capture probabilities. Excluding zero-size lists does
not correct structural ineligibility among remaining lists. Successive editions
also copy material, and acquisition follows Lord's citations. The resulting sample
is selected partly using one of the supposed captures.

Fix: specify codebook-eligible population, era/subject/format, list availability and
selection mechanism. Group genealogically related editions for sensitivity checks;
remove Lord and leave each source family out in turn; compare suitable interaction
or heterogeneous-capture models only after linkage/eligibility review. An independent
archival audit is needed for records invisible to all included print lists. None of
these suggestions authorizes new code or acquisitions in another owner's lane.

### 3. Positive dependence is a bias tendency, not a guaranteed bound

Holding two list sizes fixed, increasing overlap decreases the Chapman estimate.
Copying between lists therefore gives a credible *downward pressure* relative to an
independence model. Similarly, shared high-catchability subjects and unobservable
classes tend to make independence estimates miss low-catchability orders.

But the data also contain false splits, possible false merges, differential scope,
non-EO documents and incorrectly excluded numbered clusters. False splits usually
reduce overlap and push estimates up; false merges usually do the reverse. Those
directions are conditional on unchanged eligible population/list membership.
Here component merging also changes list sizes, era assignment and WPA exclusion,
so neither the total nor the *unseen remainder* has a universal monotone guarantee.
Different specialist lists can induce negative association and upward pressure.
Finite-sample error remains even under a valid model.

Fix: replace “read every N_hat as a lower bound” with a statement of these opposing
pressures. No current point estimate or interval is a proven bound on the true
codebook population. An arbitrary never-observed class leaves the observed overlap
unchanged, so its size is not identified by this design.

### 4. The Chao1 label does not match the incidence data

`freq` counts the number of **lists containing a cluster**, not the abundance of
sampled individuals. `chao1` nevertheless applies `S+f1^2/(2*f2)` with its abundance
variance/log interval, or the zero-doubleton fallback. An incidence formulation and
its sampling-unit assumptions should be assessed explicitly (commonly termed Chao2,
with a finite-number-of-units adjustment); changing the label alone is insufficient
because these books are not exchangeable independent sampling units.

There is a limited algebraic reason why the current expression can run high with
unequal lists. Under homogeneous orders and independent list probabilities p_j, let
Q=prod(1-p_j), r_j=p_j/(1-p_j). Expected singleton and doubleton counts are
N*Q*sum(r_j) and N*Q*sum(i<j)(r_i*r_j). Plugging these expectations into the current
unseen expression yields `N*Q*(sum r)^2 / ((sum r)^2-sum r^2)`, larger than N*Q.
Even equal lists give the factor K/(K-1). This is a plug-in calculation, not an exact
expectation of the ratio, and it does not establish the direction under dependent
lists or heterogeneous orders. The report's categorical explanation is too broad.

Fix: preserve existing numbers as diagnostic computations, not a valid lower-bound
estimate/95% interval for this incidence design. Validate a chosen incidence model
against simulated *design-relevant* dependence, heterogeneity and linkage errors.
The single 400-order independent-list test is not a coverage study.

### 5. Three scenarios are sensitivities, not truth brackets

“Strict” already accepts any one shared token on the same exact day, year-based
two-token matches, and citation links without a date-consistency gate. Blind-only
removes citations but retains the same generic-token/year bridges; it is not an
independent validation sample. Loose adds all ambiguous same-date pairs, including
distinct contemporaneous orders. Citation links can also bridge inconsistent dates.

The three runs exclude **56, 75 and 53 numbered clusters**, respectively (strict,
blind, loose). They therefore do not hold the eligible sample fixed. A true missed
link can have different OCR dates, and a strict accepted link can be false; the true
linkage need not be any of these scenarios or lie between their estimates.

Fix: call all three “linkage sensitivity scenarios”; report the numbered exclusions
and changed population with them. Adjudicate a stratified sample of accepted as well
as ambiguous/rejected links. Do not use the loose/strict endpoints as a confidence
interval or guaranteed minimum/maximum missing population.

### 6. Numerical edge cases need distinct outcomes

* `mt_mle([1000,1000],1999)` returns null, although the two-list equation has the
  finite root 1,000,000: the hard upper bracket 50*S+100 is too small. Expand the
  bracket adaptively and distinguish finite, boundary and nonidentifiable cases.
* `s_obs == max(ns)` returns null unless every list equals S. For the earliest era,
  a list contains all seven observed clusters; null does not mean zero missing.
  A boundary fitted value and lack of an informative interval need separate labels.
* `chapman(100,100,90)` reports interval [108.8,113.4], below its observed union of
  110. Its lower bound clips at max(n1,n2), not n1+n2-m. Enforce support and prefer
  a suitable likelihood/exact interval for sparse or boundary overlaps; clipping
  alone does not supply nominal coverage. Full-overlap examples returning a
  zero-width interval must not be read as proven completeness.
* `mt_mle` rounds before `mt_ci`. Keep full precision until presentation, validate
  feasible inputs, and label Wald intervals as conditional model approximations.

### 7. Coverage percentages are descriptive, not random-sample coverage

The 32/104 (30.77%) president-signed Richardson VI documents and 71/140 (50.71%)
Richardson IX documents cited by Lord are useful **record-link proportions in those
held tables**, subject to eligibility/link checks. Wilson intervals do not account
for nonrandom corpus selection, copying, parsing, missing pages or codebook mismatch.
They are not confidence intervals for Lord's coverage of all executive orders.

## Numbers that may be quoted, with the required caveat

Current committed run: 2026-10-19T00:29:15Z (2026-10-18 20:29:15 ET), not the older
1,394-observed/316/1,729 figures in the handoff. “Observed” below means algorithmic
unnumbered clusters, **not authenticated distinct codebook orders**.

| Era | Strict clusters | Strict Mt total; nominal interval | Strict unseen | Loose unseen | Blind unseen |
|---|---:|---|---:|---:|---:|
| 1789–1800 | 7 | null; boundary not resolved | null | null | null |
| 1801–1861 | 222 | 261.0; 242.9–279.1 | 39.0 | 17.6 | 40.2 |
| 1862–1899 | 1,191 | 1,444.2; 1,397.6–1,490.8 | 253.2 | 108.9 | 451.2 |
| 1789–1899 pooled | 1,420 | 1,715.7; 1,665.4–1,766.0 | 295.7 | 129.1 | 489.3 |

Permitted wording: “The held program produced 1,420 unnumbered clusters. Its
independent-list Mt model estimates 295.7 unseen clusters in the strict-link scenario,
129.1 in the loose scenario, and 489.3 in the blind scenario. These are sensitivity
outputs with known linkage and capture-model defects, not verified missing orders
or lower/upper bounds.” Pooled and era-specific estimates need not sum; do not mix
them into a new census figure. The 1,665.4–1,766.0 interval is conditional on the
fitted independence model and chosen links, not a validated uncertainty interval
for the historical census.

The strict singleton/doubleton calculation gives unseen values 15.0, 1,522.2,
1,895.8 and 2,677.2 by the four rows. Quote them only to document the program's
diagnostic disagreement; do not present them as a substantiated number of missing
EOs or a certified lower bound. All source-universe coverage statements likewise
refer to the specific recorded search, not archival exhaustion.

## Requested owner action

Claude: first correct month-aware matching and component consistency; relabel the
existing report's conclusions and scenario bounds; then rerun the design/estimator
assessment with adjudicated links. Preserve the current outputs and this diagnostic
record for comparison. This review has deliberately not modified your job.

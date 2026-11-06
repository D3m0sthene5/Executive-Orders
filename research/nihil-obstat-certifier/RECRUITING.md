# Recruiting human certifiers through NYU: plan and budget

Status: a plan for the owner's decision. Nothing here has been sent to NYU, and every pay rate, policy statement and
throughput figure that is not a measurement from this repository is labelled **assumption** and must be checked with
the named office before anyone relies on it.

## What the job is

A certifier opens the Nihil obstat page (`index.html`), reads one filed claim card, checks each quoted span against the
saved source text (and the original page, when it can be attached), reads the two or more AI reviews, and records
certify / reject / needs-more for each part of the claim and for the claim as a whole. The decision file is the
evidence; the page changes no count. See `README.md`.

Why law students: the work is reading Federal Register notices and statutes for legal effect (revocation, supersession,
amendment, savings clauses). The legal judgment is what the AI reviewers cannot supply independently, so the coders
should be able to read a revocation clause and a savings clause without hand-holding. Law students in their second or
third year, or students who have taken Legislation and Regulation, Administrative Law or Constitutional Law of the
presidency, are the natural pool.

## How fast will they be?

**Measured workload (from the repository, 2026-11-06).** The 1,185 orders marked ready for human review
(`jobs/readiness-tracker/output/READINESS_BY_ORDER.csv`) have claims with these sizes (1,158 claim the order ended,
27 claim it is still in force):

| Per claim | Mean | Median | 90th percentile | Max |
|---|---:|---:|---:|---:|
| Operative clauses | 4.4 | 1 | 11 | 99 |
| Quoted spans to check | 17.8 | 7 | 40 | 303 |
| Distinct sources | 2.3 | 2 | 4 | 20 |
| Words of quotation (repeats counted) | 7,169 | 1,835 | 15,447 | 285,492 |
| Words of research rationale | 501 | 467 | 800 | 1,766 |

The five example cards (`example_cards/`) average 163 KB and 26 quoted spans each. The distribution is heavy-tailed:
most claims are one clause and a few quotations; a few are enormous. Plan on tiers, not a single rate.

**Throughput (assumption, not measured with humans).** Careful legal reading at about 150 words per minute for
quotations and rationale, plus about 2 minutes to open an original page and compare it, plus 1 minute per clause for the
decision and its reason:

| Claim tier | Share (assumption) | Minutes per claim | Claims per hour |
|---|---:|---:|---:|
| Median-size (1 clause, about 1,800 quotation words, 2 sources) | about 60% | 20 | 3 |
| Large (about 11 clauses, 15,000 quotation words) | about 10% | 90 or more | under 1 |
| Everything between | about 30% | 30 to 45 | 1.3 to 2 |

Weighted, this is **about 2 claims per hour** (range 1.2 to 3), and the cost tables below use 2. The page records
`active_seconds` in every decision (time with the page visible and the user active within the last minute), and
`alpha.py` prints the median and the claims-per-hour it implies, so the pilot replaces this assumption with a
measurement. Re-run the budget with the measured rate before committing to a larger option.

## Training (assumption)

* Two sessions of about 3 hours each, run by a lawyer on the project: the lifecycle model (original text, clause
  inventory, first end, later events, savings), the codebook's `first_cause_type` and mechanism vocabulary, what
  "certify" means here (the claim's every clause and date, not "the AI looks right"), and a walk through one card.
* Practice on 10 cards with answers known to the trainers, drawn from the example set and from claims that
  AI reviewers rejected (rejected claims are the useful negatives). A coder moves on after agreeing with the
  trainers on at least 8 of 10 overall decisions and discussing the misses.
* Calibration after the first 20 real claims: the whole group meets, disagreements are discussed, and the codebook note
  is amended. Amendments are written down and versioned; claims coded before an amendment are re-checked.
* Planted controls: about 10 to 15 percent of the cards given to coders should carry a planted, known defect (an altered
  date, a quotation from a different order), mixed in without being labelled. This is the human counterpart of the
  controls the AI review waves already use, and it measures how often a coder certifies a bad claim, which alpha alone
  does not show.

## Independence and double-coding

* A certifier must not have produced the claim and must not have taken part in its AI review (the page asks them to
  declare this; it is an attestation, not a check).
* Coders work alone and do not see each other's decisions until adjudication.
* **Double-coding share for alpha.** Alpha needs units coded by at least two people; `alpha.py` computes Krippendorff's
  alpha (nominal) over any number of coders with missing data. Proposed: 100 percent double-coding in the pilot,
  then 20 percent of claims (chosen at random, plus every claim with a reject or needs-more) in production, with alpha
  re-computed monthly. Krippendorff's thresholds: 0.800 or more reliable, 0.667 to 0.800 tentative, below that do not
  rely on the codes (Krippendorff 2004, *Content Analysis*, p. 241). If production alpha falls below 0.800, return to
  100 percent double-coding for the next 50 claims and re-train.
* Because almost all filed claims will be certified, the rare categories (reject, needs-more) dominate the uncertainty
  in alpha. The pilot should therefore be enriched with the planted controls and with claims the AI reviewers rejected;
  report alpha with the bootstrap interval (`--bootstrap 2000`) and say how the sample was enriched.
* Disagreements go to a senior adjudicator (a lawyer on the project or a faculty member), who records a decision and a
  reason. The adjudicator's decision is a third record, not a replacement; the original coders' records are kept.

## Scale options

Cost model: `hours = codings / claims_per_hour + training + adjudication`; `cost = (hours x coder rate + lead hours x
lead rate) x 1.10`. Coder rate **$30/hour** (assumption; the range tested is $25 to $40), lead RA rate $40/hour
(assumption), 10 percent for payroll load or fringe (assumption). Figures are rounded to the nearest dollar, and the
table shows the effect of the throughput and rate assumptions.

| | A. Pilot | B. Sampled production | C. Full double-coding |
|---|---|---|---|
| Claims | 100, enriched with controls | all 1,185 ready now | all 1,185 ready now |
| Coders | 4 | 8 | 12 |
| Double-coded share | 100% | 20% (plus every reject) | 100% |
| Codings | 200 | 1,422 | 2,370 |
| Training hours (all coders) | 24 | 64 | 96 |
| Adjudication hours | 20 | 40 | 90 |
| Lead RA hours | 40 | 150 | 250 |
| Coding hours at 2 claims/hour | 100 | 711 | 1,185 |
| **Cost at $30/h and 2 claims/h** | **$6,512** | **$33,495** | **$56,243** |
| at 3 claims/h | $5,412 | $25,674 | $43,208 |
| at 1.2 claims/h | $8,712 | $49,137 | $82,313 |
| at $25/h (2 claims/h) | $5,720 | $29,013 | $48,703 |
| at $40/h (2 claims/h) | $8,096 | $42,460 | $71,324 |
| Calendar time (assumption: each coder 10 h/week) | about 5 weeks | about 10 weeks | about 12 weeks |
| What it buys | measured rate, first alpha, the codebook note | a defensible certified sample with reliability reported | a certification for every ready claim read by two people |

Marginal cost of one more claim at the Option B mix is about $28 (1.2 codings / 2 per hour x $30 x 1.10, plus
adjudication and lead time), and about $48 at full double-coding. The ready count is rising (1,185 on 2026-11-06),
so cost per additional 1,000 claims is the number to budget on: about $28,000 (sampled) or $48,000 (full double).

**Recommendation.** Run A first. It costs about $6,500, takes a few weeks, and replaces three assumptions in this
document (throughput, disagreement rate, training time) with measurements; decide B or C afterwards. Whether any
certified claim ever counts toward the project's certified total is the owner's decision and the importer's job, not
the page's.

## Who to ask at NYU (all to confirm)

* **Student employment office** (NYU Office of Financial Aid / Student Employment, and the Law School's own student
  employment or Career Development Office for law students): hourly rate bands for research assistants; whether law
  students are hired through the Law School or university payroll; maximum weekly hours; whether Federal Work-Study
  or Law School work-study can fund the posting (that can lower the project's cash cost); onboarding paperwork and
  lead time. **Assumption:** $25 to $40 per hour for law-student research assistants; the New York State minimum wage
  for New York City is a floor (check the current figure).
* **A faculty sponsor** (assumption: needed for a Law School RA posting, or for course credit through a seminar or
  clinic). Course credit instead of pay would change the budget entirely and raises its own questions about
  consistent availability; the pilot is cleaner with paid hours.
* **IRB (University Committee on Activities Involving Human Subjects).** **Assumption:** coding public government
  documents is not human-subjects research, so IRB review is likely not needed. Confirm in writing, because the project
  will also measure the coders (time per claim, agreement with each other) and may publish reliability figures. If
  the office considers that research about the coders, an exempt determination is the likely route. Ask before the
  pilot starts, not after.
* **Data and names.** The cards contain only public government text and AI review records. The decision files contain
  coder names. Decide whether the repository stores names or stable pseudonymous coder IDs (alpha.py treats the
  reviewer name as the coder ID, so an ID works as well).

## Process

1. Owner approves Option A and a budget ceiling; the owner or a faculty sponsor posts the positions (job posting text:
   "read and certify legal-history claims about presidential executive orders; public documents; training provided").
2. Interview not needed; screen for coursework and a short reading test (one card, 45 minutes, paid).
3. Export cards with `export_cards.py` for the pilot ids (stratified by size tier, plus controls), with
   `--copy-originals` where an original PDF is committed so coders can attach it.
4. Coders open `index.html`, load the export folder and work offline; they send back the JSONL file.
5. The coordinator runs `alpha.py`, adjudicates, and puts the decision files in the repository for the owner. Nothing
   in the page or in `alpha.py` edits a status, a claim or the certified count.

## Open questions for the owner

1. Option A now, with a ceiling of about $7,000 to $9,000? (This is cash outside the $100 API ceiling in the campaign
   ruling; it needs its own decision.)
2. Faculty sponsor or student-employment route first?
3. Coder names in the public repository, or pseudonymous IDs?
4. Does the owner want controls (planted defects) in the human pilot? (Recommended, and they need producing.)

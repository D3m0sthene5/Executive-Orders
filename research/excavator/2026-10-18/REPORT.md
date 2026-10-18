# Corpus excavator: reusable status-history extension

The main deliverable is `jobs/status-history`, consumed by the existing claim-kit.
It prepares source-backed observation histories and explicit decision work across
7,650 census identities, including 4,817 undecided orders. It does not infer legal
status from a snapshot. All dates and legal work use the October 14, 2026 cutoff.

## Component choice made before implementation

1. **Repeated task removed:** independently locating the same 1989 table rows and
   OFR notes, reconstructing source custody, finding acting-order notes, sorting
   candidate changes and spotting temporal/scope conflicts for each order.
2. **Reproducible reach:** join the existing table/catalog/events to the included
   census using `history.py build`. `SUMMARY.json` and `SHARED_SOURCE_READS.json`
   reproduce 4,223 printed-row identity joins, 6,937 raw API observations and
   11,160 source/order memberships across 72 book pages plus seven API responses.
   These overlap; coverage is 7,448 own-observation identities plus 202 relational
   histories, not their sum as independent orders. Of those, 4,640 and 177 are
   undecided respectively. Uncovered census identities remain explicit.
3. **Agent work prepared:** exact text/JSON-pointer/page/coordinate lookup, source
   and record hashes, event ordering, candidate-date meanings, conditional bounds,
   partial/conflict warnings, supporting actor notes and case-specific next work.
   Original reading, page-image checks, actual effective dates, retained commands,
   earlier cessation, exceptions, savings and status adjudication remain decisions.
4. **Consumer:** claim-kit `history` and `status-sheet`, its collector fragments,
   decided dossiers and undecided STATUS_LEADS. After provisional adjudication,
   agents continue through its existing sheet/assemble/check/claim-checker path.
   No rival claim assembler, source acquirer or automatic status publisher exists.
5. **Why this before another component:** the source-priority pilot's top twelve
   requests offered 163 overlapping open-step memberships and a ceiling of one
   new-ready order, which failed source/legal audit. In contrast, this component
   reuses already acquired/extracted volume and API evidence across thousands of
   undecided orders, without new network or model calls. Shared-mechanism families
   and volume-original acquisition already have jobs and claim-kit consumers;
   their largest remaining burden is member-specific original/scope/exception work,
   which cannot safely be erased by a family match. Historical discovery in the
   profiler has 115 witness/gap records requiring authentication, not 115 new EOs.
   Status histories provide the largest directly evidenced reusable preparation
   opportunity in these inspected inputs. This is an expected-value choice, not
   proof that no future volume or family project can do better.

## Measured results and actual downstream use

| Measure | Observed result | What it establishes |
|---|---:|---|
| Histories / undecided | 7,650 / 4,817 | Preparation reach; 202 / 177 are relational-only |
| Exact stored observations | 11,162 | Book/raw/derived witnesses, including two unjoined book rows |
| Editorial event candidates / exact raw spans | 15,772 / 15,660 | 112 ambiguous/unmatched spans remain explicitly unverified |
| Full corpus exact-source QA | 7,650 histories, 16,581 observation refs, 15,772 event refs; zero errors | Stored-byte integrity, not legal truth |
| Source files opened by full QA | 8, totaling 1,115,213 bytes | One shared book-chunk file and seven gzip responses |
| Warm local rebuild | 7.906 seconds, 7,650 unchanged histories reused, zero HTTP | Reproducible incremental preparation |
| Paired 12-order verification | 24 to 7 source-file reads; 6,659,387 to 1,060,267 bytes | 17 opens / 5,599,120 bytes (84.1%) avoided in the same exact-source check |
| Paired verification time | 0.187 to 0.031 seconds | Local deterministic operation only; OS cache uncontrolled |
| Compact startup payload | median 2,481 bytes, p90 3,837, maximum 17,868 | Explicit 18,000-byte cap; one packet discloses event overflow |
| Actual claim-kit collector | 7,650 pointers consumed, 4,817 undecided, zero rejected history pointers | Real downstream ingestion; no statuses assigned |
| Independent AI sample | 12 fixed packets accepted as preparation; four difficult controls unresolved | Source/method review, not human or lifecycle acceptance |
| Readiness added by status histories | 0 | No observation promotes a readiness step |

The compact payload totals 20,653,565 UTF-8 bytes versus 70,628,858 for full packets.
That is a startup-size comparison, **not** a billed-token reduction or permission
to skip source reading. Full packets are still necessary for decisions. Counts and
timings are in `status-history-pilot/FULL_SOURCE_QA.json`, `REUSE_BENCHMARK.json`,
`CLAIM_KIT_CONSUMPTION.json` and the producer's `output/METRICS.json`.

Flags identify 426 partial/qualified cases, 31 pre-snapshot change conflicts,
84 cases missing a post-snapshot end basis, five later-cleanup/earlier-end searches,
three provisional YES/ended-snapshot conflicts, 69 orders with unverified event
quotes and 1,874 empty notes. Categories overlap. They are decision work made
visible, not contradictions automatically resolved. Accepted legal intervals and
current legal status remain empty/null in every history.

The independent reviewer read actual raw API fields and positioned OCR, checked
36 own/supporting observations separately, pinned 64 files and 86 evidence records,
and found no source mismatch in the final sample. Its report documents the exact
remaining work for every order. It did not inspect book page images or authenticate
every original. A material initial stale-reader error was found, preserved, repaired
and independently retested on the same fixture; no replacement sample was used.

## Costs, uncertainty and repeated use

Available model input/cached/output/reasoning billing is **unavailable**, not zero.
Total root tool-call count and active agent/reviewer labor were not instrumented
from the start. The status-history audit recorded at least 14 functions.exec calls
and 476.17 wall seconds; the first source audit recorded 518.13 seconds. Those
wall clocks overlap coordinator work and must not be summed as elapsed session
time. The status-history implementation clock floor starts 08:40:15 UTC; it omits
earlier inspection/design. The initial stale-reader correction and verification
are included within that phase; their isolated labor/token cost is unavailable.
`COST_MODEL.json` records the final measured clock floor and explicit scenarios.

No measured claim of net end-to-end token or legal-review savings is made. The
operation that is demonstrably eliminated is repeated shared-source preparation.
For planning only, let C be all implementation, correction and verification agent
hours, s be seconds of startup work avoided per source/order membership, and R be
corpus reuses. Gross hours saved = 11,160 × s × R / 3,600; net = gross − C − ongoing
correction/review costs. At s=2 seconds, one use saves an estimated 6.2 hours; at
s=10 it is 31 hours. A conservative C=8 hours breaks even after two uses at s=2,
or one use at s=10. These are sensitivity assumptions, not observations. If normal
agents already avoid all duplicate preparation, s approaches zero and no labor
ROI follows. Required original/scope review remains in both arms. Future runs
should measure equal-quality adjudicated orders with and without prepared packets.

One-time machine verification was inexpensive relative to a full claim-kit build:
the final full QA took 12.125 seconds; actual claim-kit corpus ingestion took
113.718 seconds. Unit suites passed: status-history 10, claim-kit 91, tracker 21,
source-ladder 47 and profiler 8. The large claim-kit dossier rebuild is delegated
to the existing job runner; inspect its STATUS before treating generated pointers
as current. Local direct CLI/collector operation is already verified.

## Preserved acquisition pilot and safety correction

Checkpoints `8978a8c6` and `4a35e764` retain receipts, extracted texts, failure
histories, frozen source plan, before/after tracker replay and independent page
audit. The twelve-request ranked pass used 16 ladder HTTP requests (20 pool network
requests including robots/redirects), 125,507,785 downloaded bytes and 35.7 seconds.
It found eleven new receipts, ten distinct content hashes; nine matched expected
hashes. It retained 147 prior successes. The same-size FIFO pass made zero HTTP
requests because its twelve entries had no route; it recovered no new source.
This compares bounded scheduling arms, not all possible FIFO outcomes.

The real tracker replay completed 19 `opus_media` steps. Its apparent 130→131
readiness increase was **rejected**: EO 9789's uniform first-end claim does not
resolve executed transfer, amendment, past-action, effective-date and savings
scope. Its exact claim and review hashes now bind a negative readiness hold.
No other agent's claim was edited. The hold prevents that rejected result from
being counted when receipts enter the normal source output.

The audit also found that the main claim-kit EO 9789 inventory actually resembled
EO 9788, and that Stat. 80's first-40-page extraction missed relevant full-PDF
pages 254–255 and 273–274. Printed page labels and PDF indices differ. Statutory
codification repeal does not alone end orders; preservation/no-substantive-change
clauses remain material. EO 4314's lone Wikisource 404 cannot establish exhaustion.
The initial missing LOC sample ID was retained as a prespec failure, not replaced.

## Ranked next work

1. Consume the independently checked undecided packets (EO 12331, 11250, 11583,
   10108, 11541, 8597, 11790, 12979). Read the specific originals/actors and fill
   pinned status sheets. Resolve each order's exceptions rather than approving a
   shared actor wholesale. Reviewer case notes give the exact missing decisions.
2. Correct EO 9789's original boundary/inventory and claim scope with its producer;
   keep its hold until an independently reviewed replacement is available. Reuse
   the held 1946/1947 issue images instead of fetching them again.
3. Reuse the acquired Stat. 80 volume and extract targeted page ranges beyond the
   existing 40-page ceiling. Pair repeal rows with §§7–8 preservation and each
   order's original, effective clauses and exceptions (including EO 10209/10210).
4. Resolve 69 ambiguous raw-event cases by heading/scope-aware parsing, retaining
   failed strings as controls. Current exact-span refusal is intentional.
5. Reconcile `7933-a`/`7933A`/`7933a` and EO 13526's correction through identity
   adjudication; authenticate the two August 8, 1914 witnesses with page images,
   original signer/property scope and EO 8507. Do not merge or admit from date alone.
6. Extend extraction of already acquired official compilations into uncovered
   historical ranges. Crosswalk against census-candidates/Lord/LOC witnesses;
   prioritize sources spanning many unresolved witnesses and keep numbering gaps
   as hypotheses. Never infer a missing EO solely from a number hole.


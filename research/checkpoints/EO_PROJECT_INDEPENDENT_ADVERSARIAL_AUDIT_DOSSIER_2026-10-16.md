# THE AFTERLIFE OF EXECUTIVE ORDERS
## Standalone project dossier for an independent, adversarial methodological audit

**Prepared:** October 16, 2026  
**Legal/status research cutoff:** October 14, 2026, America/New_York  
**Latest integrated project checkpoint:** Stage 11, October 16, 2026  
**Controlling legal codebook:** version 2.0.0  
**Status of this document:** Detailed account of what the project intended, did, counted, and has not proved. It is deliberately written for a reader with **no access to the original conversations or research files**. It includes new arithmetic and provenance checks, as well as the project's own assertions and limitations. It is **not** an independent legal certification of the classifications.

> **YOUR ASSIGNMENT, IF YOU ARE THE AUDITING AI:** Assume the project's central premises may be wrong. Examine whether its population actually consists of U.S. presidential executive orders; whether the units being counted are comparable; whether its claimed 14,973-order denominator is defensible; whether a legally coherent distinction exists between an order's present effect, enduring consequences, formal nonrevocation, and policy survival; whether the decisions apply that distinction consistently; and whether the staged numerical improvements reflect valid new knowledge. Identify any fatal or systemic error even if it invalidates months of research. Do not reward the project for sophisticated engineering or large numbers of completed records. Distinguish demonstrated defects from plausible vulnerabilities and from speculative objections.

## Navigation

1. [Objective, current verified counts, and biggest caveats](#1-executive-summary-what-the-project-is-and-where-it-stands)
2. [What is an executive order and what unit gets counted?](#2-defining-the-target-universe-and-unit-of-analysis)
3. [Legal definitions and all 16 codebook rules](#3-what-counts-as-continuing-legal-effect-the-frozen-codebook)
4. [Census construction, source classes, omitted unnumbered orders, APP discrepancy, 1,943→1,950 flag defect](#4-how-the-historical-inventory-and-its-denominator-were-assembled)
5. [Complete chronological Stage 1–11 results and causal handoffs](#5-full-stage-by-stage-record-what-actually-changed)
6. [Research workflow, evidence and verification gates](#6-research-machinery-source-acquisition-legal-decisions-concurrency-and-verification)
7. [Actual classification families, specific EOs, legal failures and exceptions](#7-substantive-research-families-what-legal-reasoning-worked-and-where-it-may-have-failed)
8. [National Archives/Federal Register bulk importer and remaining queues](#8-the-government-disposition-acceleration-project-and-current-research-queue)
9. [Fundamental unproved assumptions and incomplete results](#9-what-the-system-did-not-prove-and-why-the-gaps-matter)
10. [Ranked high-risk hypotheses and independent falsification protocol](#10-a-ranked-agenda-for-an-outside-critic-to-attempt-to-falsify-this-project)
11. [Reproduction, core files, SHA-256, code and schema](#11-how-another-ai-could-reproduce-the-arithmetic-and-inspect-the-evidence)
12. [Authoritative public references and external scholarship](#12-useful-public-sources-and-what-proposition-each-can-support)
13. [Specific deliverables requested from the auditor](#13-required-product-from-the-independent-auditor)
14. [Glossary](#14-glossary-for-a-reader-with-no-project-history)
15. [New field-level audit: inconsistent types and incomplete judicial/causal fields](#15-additional-field-level-audit-status-arithmetic-passes-but-some-data-structures-are-not-standardized)

## 1. Executive summary: what the project is and where it stands

This is an AI-assisted empirical legal-history project called **The Afterlife of Executive Orders**. Its intended universe is **every identifiable U.S. presidential executive order from George Washington's presidency through October 14, 2026**, including numbered, suffixed, and adequately documented unnumbered orders. It seeks to produce a source-auditable instrument-level dataset, an account of how presidential orders continue or cease to operate as law, and ultimately a defensible public-facing empirical legal article.

Its motivating questions are:

1. How many executive orders were actually issued, insofar as surviving records permit an answer?
2. How many have **continuing substantive legal effect** at the historical cutoff? How many have **any continuing legal effect attributable to the order**, including residual duties?
3. How many ceased operating through a deadline, expiration, fulfilled condition, or completed assignment **without a later terminating intervention**? How many ceased because of subsequent presidential, legislative, regulatory, or judicial action?
4. How often does a formal revocation occur **after** substantive operation has already ceased—in other words, how often is a revocation housekeeping rather than the event ending the operative policy?
5. How do amendments, incorporated provisions, saved rights, dormant authority, durable land or institutional designations, and later revivals affect those answers?
6. Can every determination be traced back to the original instrument, later legal events, precise source quotations, a stated inference rule, and independent review?

**Current reported and mechanically rechecked project status:**

| Measure | Value | Meaning |
|---|---:|---|
| Preserved ledger rows | **15,010** | Records in the latest JSONL, including non-counted candidates and exclusions. Not 15,010 proven orders. |
| Included/"validated" identities | **14,973** | Present project denominator; primarily *bibliographically validated* source identities, not necessarily authenticated unique signed presidential documents. |
| Included but still provisional | **17** | Grouped historical-number candidates, excluded from the 14,973 denominator. |
| Other nonincluded ledger records | **20** | 17 excluded duplicate placeholders and three unresolved/outside-union records. |
| Substantive **YES** | **193** | Model-reviewed decisions reporting some operative substantive effect at cutoff. |
| Substantive **NO** | **2,322** | Model-reviewed decisions reporting complete cessation of substantive scope. |
| Substantive **UNKNOWN** | **12,458** | Not legally adjudicated to YES or NO. Neither necessarily active nor inactive. |
| Substantive determinations / included identities | **2,515 / 14,973 = 16.796901%** | **Research-classification coverage**, emphatically **not** the survival rate or completion of historical census. |
| Any-operative-effect YES / NO / UNKNOWN | **205 / 2,165 / 12,603** | Separate, broader axis. |
| Any-operative-effect determinate | **2,370 / 14,973 = 15.828491%** | Separate coverage measure. |
| Recent Opus findings introduced in Stage 11 | **180** | 178 NO and two YES; structurally reconciled, originally reviewed by models, still provisional for external legal review. |
| New legal findings from government-disposition **import alone** | **0** | The import generated evidence and research queues; it did not promote archival metadata directly to a 2026 status. |

The cross-axis breakdown of the 14,973 included identities is **193 YES/YES, 2,165 NO/NO, 145 substantive NO/any-effect UNKNOWN, 12 substantive NO/any-effect YES, and 12,458 UNKNOWN/UNKNOWN**. There are no impossible cross-axis combinations in the current ledger under the codebook's ordering. The twelve known residual-only orders are emergency labor-board orders with separately analyzed record-custody duties.

The mechanical counts above were checked directly against the Stage 11 JSONL and by running its `SCRIPTS/verify_release.py` integrity/count checker. That confirms structural arithmetic and specified invariants, **not** factual census completeness or legal correctness of the underlying model decisions.

The 16.8% coverage should not be interpreted as 16.8% of all executive orders being active or inactive. **193/14,973 = 1.289%** is the fraction *affirmatively adjudicated* substantively YES in the current included population, while **2,322/14,973 = 15.508%** is the fraction adjudicated NO, and **83.203%** remains unknown. If every UNKNOWN were substantively YES, the upper logical within-inventory share would be **84.492%**. Those extreme within-inventory bounds are not confidence intervals or national estimates, and even they would not cover unidentified historical orders.

### The most important caveat

**The project does not know the exact number of all executive orders ever issued.** Its denominator omits most of the historical **unnumbered series**, which began before the retrospective 1862 numbered series, and it relies heavily on a twentieth-century compiler's index to admit historical identities. A Stage 4 comparison found **16,238** executive orders summed across the American Presidency Project's 47 administration-total entries, **1,265 more** than the project's 14,973 validated identities; the two sources have materially different coverage definitions and the difference is *not* proof that exactly 1,265 are missing. These issues require independent resolution before any claim of an all-history national count.

**The project also has not answered its original causal question at scale.** Of the **2,322** currently substantive-NO validated records, **2,216** still have literal `cessation_mechanism: "unknown"`; **2,223** still have literal `first_cessation_date: "unknown"`. Even among the remaining populated mechanisms, some indicate only a later revocation or bound while explicitly leaving **first cause** unresolved. The public-facing comparison of natural expiration versus affirmative intervention is not yet empirically established.

### What information is asserted versus independently checked

- **Directly checked for this dossier:** The existence, counts, cross-axis arithmetic, population-class composition, source ZIP hashes, current script verification, selected individual record content, and original 1,943-row queue provenance, using actual files available to the preparer. Specific source documents were also checked against official public reference pages.
- **Inherited/reported by earlier research agents:** The factual completeness of individual original-order reconstructions, interpretations of savings clauses, claims of independent model review, the authenticity of externally retrieved documents, and most individual YES/NO legal conclusions. The dossier has **not** freshly independently re-adjudicated all 2,515 determinate cases.
- **Unestablished:** Total historical universe; representative accuracy/error rate; systematic legal truth of the NO findings; true causal distribution; absolute completeness of later-amendment, statutory, judicial, and administrative searches; archival coverage of lost or unnumbered orders.

## 2. Defining the target universe and unit of analysis

A U.S. **executive order** is treated as a presidential legal/administrative instrument. The project intends to include executive orders regardless of policy importance, revocation history, ceremonial character, duration, or public salience. It intends to distinguish EOs from proclamations, presidential memoranda, notices, determinations, agency orders, ordinary regulations, and statutes, while allowing those other instruments to be **later legal events affecting an EO**. It does **not** intend to count every presidential action or every policy provision as an additional executive order.

In practice, the working entity is a **canonical bibliographic EO identity**, usually `EO:<number>` or `EO:<number><letter/suffix>`, and sometimes a specifically identified unnumbered source row such as `EO:UN:executive-orders-01:row:11`. The **current database counts canonical identities**, not systematically verified physical signed manuscripts. This distinction is central to the requested audit.

The numbered series was retroactively organized beginning in 1907 from executive orders in the Department of State's files; the retrospective `EO 1` was an order attributed to Lincoln on **October 20, 1862**. Presidential orders existed from 1789, and earlier and later orders absent from State Department files were often unnumbered. The Federal Register Act era greatly improved contemporaneous recording, but does not retroactively fix this omission. The Library of Congress explains that before the late 1930s it is practically impossible to identify exactly how many orders presidents issued. See the primary public references in §16.

Therefore, the sequence `EO 1` through `EO 14435` (latest observed by the cutoff) is **not a valid count**. There are gaps, retrospectively assigned lettered and hyphenated identifiers, possibly multiple numbers printed for sections of one document, and historically unnumbered EOs. Nor does the project have evidence that every item in its historical index necessarily corresponds to a uniquely signed presidential EO.

Critical edge cases needing independent legal-historical decisions:

- **One physical document / several numbers.** Clifford Lord's historical numbered series groups labels **36–37, 38–39, 40–42, 43–46, 47–49, and 51–53**. A note at EO 36 indicates that a single document may carry separate EO numbers for its sections. Seventeen candidate numerical members remain unvalidated. The substantive research should decide whether the estimand is *numbered administrative records*, *individual executive-order documents*, or *distinct operative directives*, then reconcile these cases accordingly. The categories are not interchangeable.
- **Number variants.** The historical records include letter suffixes such as `10026-A`, hyphenated or numeric suffices such as `8-1`, and handwritten/OCR artifacts that resemble fractions. The project preserves raw labels rather than converting everything to integers. The early index admitted 489 hyphenated suffix identities provisionally in Stage 1; Stage 4 applied more selective rules for final bibliographic validation. Some ambiguous fractional/letter labels remain held.
- **Overlapping publication formats.** Lord's index, NARA disposition lists, the Federal Register, a reprinted text, and an agency publication can refer to the *same* underlying order. These should be evidence records pointing to one identity, unless there is compelling evidence of distinct instruments.
- **Historical unnumbered orders.** Nineteen currently included units are documented unnumbered *source rows*, not evidence that the United States had only 19 unnumbered presidential orders. Their physical-document distinctness is not uniformly resolved. Two rows dated **August 8, 1914** have an open possible-duplicate issue.
- **Signed by an official other than the President.** Opus flagged **EO 3016C and EO 3016N** as associated with Frank L. Polk under a delegated presidential authority. The audit must decide what qualifies as a presidential order and whether these numbered records properly belong in the same denominator; a number or compiler title alone cannot decide authorship. The project has not resolved this globally.
- **Corrections and printing errors.** The original Federal Register acquisition had an apparent duplication of EO 10571 later distinguished from **10571A**; a correction record should not become an additional EO. Other admitted number/date conflicts remain in source-specific metadata.
- **Presidential/nonpresidential instruments with EO-like titles.** The project seeks legal identity evidence and authorial attribution, but most of the older compiler-index entries have not been independently authenticated as physically signed presidential instruments.

A proper audit should state its estimand in one sentence, choose a clear identity equivalence relation, and produce sensitivity counts for (a) distinct numbered identities, (b) authenticated presidential-signed order documents, (c) included documented unnumbered orders, and (d) the full historically observed, explicitly nonexhaustive inventory. Without this, apparent accuracy to four decimal places is misleading.

## 3. What counts as continuing legal effect: the frozen codebook

**Codebook version 2.0.0** was adopted in Stage 2 after testing alternative organizational schemes on an intentionally difficult 24-order pilot. The chosen design stores an instrument-level answer, with provision-specific or *operative-episode* detail whenever time, scope, source, saving, revival, or judicial treatment diverges. It separates five ideas often conflated in commentary:

1. **Formal disposition:** whether later law expressly revokes, amends, supersedes, limits, or reinstates a document (and in what scope). Nonrevocation alone is *not* proof of activity.
2. **Substantive present effect:** whether at least one identifiable legal command, restriction, permission, delegation, institution, dormant power, durable legal status, or traceable incorporated norm attributable to that EO operates at the cutoff.
3. **Any present EO effect:** the substantive category plus proven ancillary/residual operation, such as an ongoing records obligation or transition rule under the original EO's terms.
4. **Historical cessation:** first time a given substantive operative episode ceased, later revival, last legal-effect end date, and causal mechanism.
5. **Judicial enforceability:** specific injunctions, merits rulings, stays, geographic/person/provision scope, procedural posture, and finality. A challenge or injunction is not an express repeal of the instrument.

Each of the two present-effect rollups takes exactly one of `yes`, `no`, or `indeterminate`:

- `substantive_effect=yes` when **at least one** qualifying ongoing substantive scope is supported by an identified legal source and a bounded check for later changes.
- `substantive_effect=no` when **every** substantive scope is shown to have ended or exhausted its current operation under the stated convention, with applicable amendments, residual substantive rights, savings, extensions, revival, and court restrictions addressed.
- `substantive_effect=indeterminate` if the original full footprint or some material legal bridge remains unresolved.
- `any_operative_EO_effect=yes` if **at least one** substantive or genuine ancillary/residual EO-sourced effect persists.
- `any_operative_EO_effect=no` only if every substantive **and** ancillary operative scope has ended.
- `any_operative_EO_effect=indeterminate` where possible operative residuals cannot be closed, including many orders whose substantive axis is already NO.

**The contentious TC07 convention:** An already executed, **pure dispositive** act—such as a one-time repeal of an earlier order, a completed transfer, or a completed appointment—is considered spent, and therefore *not currently operative merely because its historical consequences persist*. But an enduring constitutive status, a continuing restriction, a preserved original-term obligation, or a traceably incorporated legal norm can qualify. For example, **EO 12553**, which revoked hundreds of earlier orders in 1986, is itself coded substantive NO/any NO as a completed repeal under TC07, even though the orders it revoked remain revoked. That is a methodological choice; the record explicitly contemplates sensitivity analysis under a more permissive view that completed dispositions have continuing legal effects. An external reviewer should ask whether this convention is doctrinally sound, internally consistent, and appropriate to the actual research question.

**The equally contentious incorporation rule (TC09):** An EO that amends a host EO may leave legal text operative in the host even after the amending EO is itself formally revoked. Researchers should identify the amendment's exact host provision/version and trace that provision until it ceases. A blanket statement that a revoked amender is legally dead is not acceptable without mapping its footprint. The same applies when regulations or statutory schemes replace or preserve an EO's commands.

### All sixteen operative methodological rules

| Rule | Condensed meaning | Main error it is designed to prevent |
|---|---|---|
| TC01 | Formal disposition, operative effect, cessation cause, judicial status, and evidence sufficiency are orthogonal. | Counting an unrepealed order as active or a revoked order as first terminated by that revocation. |
| TC02 | Start from the whole order; split into provisions/episodes on material scope, time, authority, or savings conflicts. | Ignoring mixed-purpose orders or inconsistent clause lifecycles. |
| TC03 | YES if any substantive scope continues; NO only if all substantive scopes end. | Using the fate of one clause to decide the entire EO. |
| TC04 | Broader any-effect rollup, including actual continuing residual duties. | Erasing still-operative recordkeeping/savings or calling all historical effects operative. |
| TC05 | Identify present actor/object, authority, command/permission/status, and unexpired applicability. | Equating old historical consequences with a presently applicable norm. |
| TC06 | Continuing status requires identified current legal status and consequence attributable to EO. | Assuming a land boundary, institution, or historical designation survives without evidence. |
| TC07 | Spent pure repeal, transfer, or appointment is not active merely by historical consequence; test alternate convention. | Treating every completed presidential act as eternally operative. |
| TC08 | Saved prior acts differ from continuing operation under the source EO's own terms. | Assuming every grandfather clause preserves the old EO. |
| TC09 | Amender-to-host scope/version crosswalk; no automatic cascade. | Mistakenly closing incorporated amendments. |
| TC10 | Performance deadline differs from sunset of legal authority. | Assuming an old "must appoint within one year" grant legally expired in a year. |
| TC11 | Revocation of a revoking EO does not automatically reinstate all its predecessors. | Spurious revival. |
| TC12 | Judicial action must be scoped by provision, party, place, time, remedy, and later procedural change. | Treating an injunction as total permanent invalidation. |
| TC13 | Later cleanup revocation provides, at most, a latest cessation bound unless first cessation is separately proved. | Misallocating cessation causes and dates. |
| TC14 | Bounded positive continuity requires operative predicate and finite documented subsequent-change checks. | Treating silence in a table as proof of present operation, or demanding logically impossible universal negative proof. |
| TC15 | Source-as-of dates and representation grades control inferences. | Treating a 1989 editorial note or search snippet as present-day law. |
| TC16 | Every member of a batch must satisfy the legal rule and exceptions individually. | Applying one large revocation or statute to legally different EOs without checking scope. |

The frozen primary convention also distinguishes **termination according to terms originally present when the EO was issued** from **later-imposed terminations**. If an order already provided that its board would end after submitting a report, actual completion is a candidate *natural/ordinary expiration*. If Congress later terminates an agency, that is *affirmative intervention* even if it occurs decades after the EO. But amendments and earlier extensions mean the phrase "without being touched" has two possible meanings: (i) no later terminating act, versus (ii) no later amendment at all. The study needs to report both if it wants to make claims about a policy disappearing through time without action.

### Legal and logical tests the auditing AI should question

1. Is the distinction between **substantive** and **any** effect reproducible across different order types, and is it relevant to the proposed headline?
2. Does an agency's independent current statutory authority create continuation of the *original EO*, or merely continuation of a similar policy?
3. When an EO amends regulatory text that still exists, is current regulatory survival properly attributable to the amending EO, or is the successor regulation an independent legal source? Under what conditions?
4. Can a grant to perform an act become spent **without evidence that it was exercised or extinguished**? The written rules say no, but large-batch implementations deserve scrutiny.
5. What distinguishes continuing saved incumbent rights deriving from the original EO from new independent rights granted by the later saving clause?
6. Is an order that may be legally unenforceable, ultra vires, or under injunction still coded active? Does the dataset intend to measure *normative legal validity*, *binding force as applied*, or *uncancelled textual command*?
7. Can an EO be formal NO/NO on TC07 when its repeal remains operative as a necessary legal condition for present policy? Quantify sensitivity rather than resolving by intuition.
8. Does `indeterminate` represent a meaningful legal ambiguity, an unavailable original, insufficient research, an identity defect, or all of these? Are these systematically different sources of uncertainty being aggregated misleadingly?


## 4. How the historical inventory and its denominator were assembled

### 4.1 The initial problem was not a complete census

The original October 14, 2026 handoff described a **5,670-identity inherited ledger**, 2,086 earlier event records, 346 later observations, and 58 candidate dependency inferences. A specially selected **1,943-member queue** had 1,798 cases unresolved under the inherited, less rigorous reducer. The queue was a **set of research records**, not an estimate of 1,943 executive orders ever issued, a census for calendar year 1943, or a random sample. Its membership was carried forward to preserve continuity while the target expanded to every identifiable EO in U.S. history. The early 1,798-unknown figure must not be compared directly with the later codebook-2.0.0 unknown count.

Stage 1 massively enlarged the observed inventory using bulk federal sources and historical printed indexes. Its count increased from **5,670 to 14,925 observed identity records**. These were explicitly described as observed IDs, not authenticated individual presidential instruments. Stage 2 later held **14,989 observed IDs**, of which **7,453** were bibliographically validated: **7,434** modern/official-numbered identity records plus **19** documented unnumbered source rows. Stage 4 admitted **7,520 additional** identities, primarily from a historical compiler, producing the current **14,973 included/validated** population. Stage 5 onwards kept the denominator fixed; further discoveries or corrections are possible, but none has been accepted through Stage 11.

### 4.2 The actual Stage 11 row composition

The 15,010-row ledger was counted directly by its `population_class` and `included_validated` flags:

| Literal `population_class` in current ledger | Rows | Included in 14,973? | Important qualification |
|---|---:|---|---|
| `validated_numbered` | **7,434** | Yes | A number matched a retained official/hosted bibliographic subject identity; this is not necessarily a complete text/legal review. |
| `validated_historical_index` | **7,519** | Yes | Primarily **compiler-surrogate validation** from the 1944 Lord historical numbered index. It means a source-supported identifiable numbered entry, not independently verified original presidential signature. |
| `validated_historical_reprint` | **1** | Yes | A separate historical reprint validation (EO 5866). |
| `documented_unnumbered` | **19** | Yes | **Source-row units**, not necessarily 19 distinct physical signed orders. |
| `provisional_grouped` | **17** | No | Historical grouped/ambiguous candidates. |
| `excluded_duplicate_placeholder` | **17** | No | Aliases/placeholders excluded from the counted set. |
| `unresolved` | **3** | No | Outside included validated/observed union, unresolved status/identity. |
| **Total** | **15,010** | **14,973 included** | Sum of row counts, not a historical national EO count. |

The `included_observed` flag covers 14,990 records (14,973 included/validated plus 17 grouped provisional), while the 17 excluded placeholders and three unresolved records remain preserved but outside that observed rollup. `included_validated` is a **project's bibliographic inclusion decision**, never a human legal judgment that all 14,973 are executive orders as a matter of presidential-authority doctrine.

Era values in the latest ledger are approximately **7,932 pre-1937 rows**, **5,203 for 1937–1989**, **1,735 for 1990–October 2026**, and **140 date-unknown rows** when noncounted records are also included. A Stage 4 validated-era tabulation was **7,915 pre-1937, 5,203 for 1937–1989, 1,735 after 1989, and 120 without an adjudicated signing date**; these add to 14,973. Do not infer missing actual dates merely from a blank normal-form field; some source-specific dates remain in evidence records.

The ledger's latest identified issued order is **EO 14435, dated October 5, 2026**, found in a Federal Register issue of October 9. As the cutoff is October 14, there may be presidential directives signed October 6–14 that have not yet been published or indexed. The first retroactively numbered entry is **EO 1 (Abraham Lincoln, October 20, 1862)**. Neither endpoint establishes completeness of the desired **1789–2026** presidential-act population.

### 4.3 Major input corpora and what each can—and cannot—prove

**Federal Register modern EO export.** Stage 1 downloaded **6,939 records in seven globally paginated responses**, corresponding to **6,938 EO subject identities plus one correction**, with separate presidential-term lists. An export URL that appeared to promise 10,000 records returned only 20; global signing-date filtering wrongly eliminated historical records; and a duplicated number **10571** actually included a distinct **10571A** form. The researchers replaced these routes with explicit unfiltered pagination and corrected the identity crosswalk. Some modern records lack a `disposition_notes` field; **1,874 such missing annotations** were preserved as absence of a note rather than interpreted as active status. NARA linked 91 annual EO-page URLs; 66 were captured and **25 failed** at acquisition. Four source-date anomalies survived into source conflict logs. The current global export was captured as of the 2026 project collection, not live-updated here.

**National Archives' numbered codification.** All **18 historical HTML pages** were preserved in Stage 1. They contain approximately **4,226 rows**: **4,208 numbered entries and 18 unnumbered source-row entries** (including historical rows whose same-date repetition should not itself create extra legal acts). They provide 1989-era editorial categories: codified continuing, revoked, partially superseded, temporary, executed and obsolete, amended, referenced elsewhere, and special land-related exceptions. Those classifications are **dated editorial evidence** and **cannot** by themselves establish what legally operates at the October 2026 cutoff. The government compilation omits many subject classes from its codified body, and its historical cutoff does not include later presidential/legal action. Its individual source pages and the codification foreword should be checked to establish precisely what was included.

**Clifford L. Lord's historical numbered inventory.** The Stage 1 extraction used the 1944 printed/PDF *Presidential Executive Orders, Numbered 1–8030, 1862–1938*. A **695-page** PDF version yielded **8,461 provisional historical identities from 8,450 source entries**, with **72 ambiguous unmatched labels, 22 redirect/"See" rows, and six numbered-document groups**. In the source, multiple source-line and suffix representations can map differently from distinct signed original documents. The printed pages **486–487 are missing** in the used scanned text; this is a substantive archival incompleteness that cannot be cured by the extractor passing its own tests. A cleaner text layer reduced OCR errors, but numbers and punctuation still require visual validation. Stage 4 ultimately accepted **7,519** of these as `validated_historical_index` after its specific bibliographic review gate, *not* after direct original-text verification of all 7,519. Thus nearly half of the published denominator rests on a **secondary compiler-source admission standard**, even though the source itself spans only the numbered series available by 1938.

**Historical unnumbered series is seriously undercovered.** Lord published another work, *List and Index of Presidential Executive Orders, Unnumbered Series, 1789–1941* (1943), catalogued and digitized by the Library of Congress (`https://www.loc.gov/item/43013029/`). It is distinct from the **subject index/V2** accompanying the numbered volume. The full **unnumbered-series inventory was not incorporated** into the current corpus. Merely adding 19 NARA table-row identifiers as `documented_unnumbered` is manifestly inadequate as a claim to comprehensive coverage of presidential orders from Washington forward. The LOC guide on presidential actions warns that complete historical counts may be impossible, particularly before more systematic twentieth-century publication. A 1973 congressional study offered vastly larger estimates for historically unregistered executive orders, but those estimates operate under definitions, archival practices, and evidentiary constraints that require scrutiny; do not plug an unverified estimate into this ledger as a fact.

**Selected administrative and primary legal sources.** Additional coverage comprises public land orders, the Civil Service Commission and later personnel regulations, 3 CFR, codified federal statutes, 1930s New Deal statutes and decisions, Comptroller General opinions, foreign/war property records, Treasury regulations, and individual White House/archival presidential documents. Many are retrieved as hosted text transcriptions or OCR rather than certified scans. A source may be official yet legally incomplete or ambiguous on whether a grant was exercised, a transition was finished, or a saved right persisted.

### 4.4 The denominators differ dramatically from a leading outside compilation

The Stage 4 methodology compared the project's **14,973 included identities** with **16,238 executive orders summed across 47 presidential-administration total rows** in the American Presidency Project (APP) table at `https://www.presidency.ucsb.edu/statistics/data/executive-orders`: an arithmetical difference of **1,265**. It would be wrong to say this proves precisely 1,265 missing EOs. The APP and project have different starting dates, inclusion policies, numbering treatments, retrospective identification conventions, and treatment of nonstandard orders, corrections, and dates. The project counted only 19 qualified unnumbered source rows, whereas the APP incorporates a wider historical nonnumbered universe in portions of the series.

There was closer agreement in some modern bands: a cited Hoover-and-later APP sum of **9,643** versus **9,617** project records, an approximate **26-record difference** despite occasional compensating differences. The Stage 4 review reported that the FDR administration total **3,726** matched the project numerically despite a missing integer label and about **260 noninteger source identities** in the reconstructed series. Equality of administration totals can conceal different membership. A proper reconciliation must compare **sets of physical or documentary order identities, term by term, with each discrepancy classified** as omitted, duplicate, suffix, unnumbered, administrative correction, publication record, source definition, or genuinely unsettled. A net discrepancy cannot serve as a trustworthy inventory QA statistic.

**Important implication:** The project's existing percentages can describe **classification progress among its fixed included bibliography**. They cannot yet describe the survival or cessation proportion of *all historical presidential EOs*. The auditor should also ask whether the 14,973 denominator would shrink or grow under a coherent document/act definition, rather than assuming that only missing orders are the problem.

### 4.5 Newly reproduced internal provenance error: 1,943 original vs 1,950 flagged

This dossier's inspection compared the actual original handoff file `original_artifacts/EO_Original_1943_Status_Queue_2026-10-14.csv` with the present Stage 11 ledger. The original queue has exactly **1,943 unique canonical IDs**. The Stage 11 boolean `original_1943_cohort` is `true` on **1,950** ledger rows. A set comparison establishes that the original 1,943 IDs are all flagged, but **seven additionally flagged IDs** came from later NARA historical unnumbered rows:

`EO:UN:executive-orders-01:row:2`, `:row:4`, `:row:8`, `:row:11`, `:row:61`, `:row:65`, and `:row:205` (each suffix is relative to the common prefix `EO:UN:executive-orders-01`).

These seven all have `documented_unnumbered` status and are counted in the validated denominator, but were not members of the original cohort. This is a **real provenance-flag discrepancy** and warrants a field correction through a documented identity/provenance patch. It does **not** by itself show that the total 15,010 contains seven duplicate rows or that seven determinate statuses are double-counted. The issue is more general: flags transported across successive migrations can silently drift, and a project's tests may preserve an inherited erroneous flag just as faithfully as a correct one. The phrase "1943 cohort" here means the **1,943-entry original research queue**, not EO issuance during the year 1943.

### 4.6 Fundamental census questions to resolve before any all-history claim

1. Is a "presidential executive order" determined by the legal act, its original title, its later publication heading, its appearance in a recognized official index, or a retained numbering convention? How are instruments signed **under delegated authority**—for example EO 3016C and 3016N, attributed to Frank L. Polk rather than a president—handled?
2. Does `EO:UN:<page>:row:<n>` identify **one signed document**, one *table cell*, or a mere appearance of a presidential act in a later editorial publication? Have all row-to-document and document-to-row links been checked for 1:many and many:1 relationships?
3. What proportion of the 7,519 Lord entries are duplicate of existing modern/NARA entries, documentary sections of the same signed order, misread suffixes, printer/editor mistakes, or actual presidential orders? Does a 26-case visual sample make those 7,519 adequately "validated" under an article's claimed empirical denominator?
4. What other archival corpora would systematically cover the **1789–1862**, **1862–1907**, and **pre-1937 unnumbered** populations? Could the LOC unnumbered-volume be ingested as a *parallel* universe pending crosswalk without falsifying inclusion?
5. Were corrections to FR notices and retrospective "reassigned EO numbers" handled so that one act generates exactly one unit? How should EO numbers given to distinct versions, lettered approvals, and physically grouped multiple orders be counted?
6. Have the earliest published orders, pre-1937 unsourced index entries, and orders executed but never contemporaneously published been systematically sampled against the originating archives? Did missing printed pages produce contiguous coverage holes?
7. Is there an independently defined **complete subpopulation** for which all statuses could be estimated rigorously, even while the national historical census stays open? The answer may require publishing multiple source-specific estimands instead of one national count.

## 5. Full stage-by-stage record: what actually changed

The project began as a legal-history question and acquired a pipeline of versioned inventories, source observations, legal classifications, audit gates, and subsequent machine-verified merges. **Every stage's numerator and denominator must be read in its own historical context**; earlier coverage percentages used a smaller validated cohort. The following table is the most useful chronological reconciliation:

| Stage / status | Validated included denominator | Substantive YES | Substantive NO | UNKNOWN | What materially happened |
|---|---:|---:|---:|---:|---|
| Inherited checkpoint | No all-history validated denominator | — | — | Original 1,943 queue had 1,798 unresolved under inherited rules | 5,670 initial IDs; 2,086 events and 346 observations retained. |
| **1: bulk acquisition** | Not yet legally fixed | — | — | Not adjudicated | Observed identities grow to 14,925; source facts, relations, and early index imported. No status promotion. |
| **2: legal codebook and first adjudications** | **7,453** | **14** | **532** | **6,907** | v2.0.0 codebook; 790 instrument reviews; 546 determinate findings among selected validated identities. |
| **3: selected high-yield families** | **7,453** | **115** | **941** | **6,397** | +101 YES, +409 NO among validated; 11 additional provisional-NO cases reported in all-observed results. |
| **4: large historical identity validation** | **14,973** | **151** | **1,103** | **13,719** | +36 YES and +151 NO on original validated set; 11 older provisional NO identities newly validated; +7,520 bibliographic identity admissions. |
| **5: continued adjudication** | **14,973** | **191** | **1,242** | **13,540** | +40 YES, +139 NO; 12 identified substantive-NO/any-effect-YES residual cases. |
| **6: bounded legal families** | **14,973** | **191** | **1,287** | **13,495** | +38 NIRA +7 BLM order revocation NOs; several BLM cases held. |
| **7: corrected integration** | **14,973** | **191** | **1,695** | **13,087** | 407 Opus NRA/retirement NO plus just **one** confirmed Astra civil-service NO. Three Astra findings quarantined. |
| **8: Opus P2 cohorts** | **14,973** | **191** | **2,035** | **12,747** | +340 Opus NOs (256 retirement, 84 NIRA); technical merge, no fresh independent legal audit of all 340 by the merging agent. |
| **9: Astra civil-service** | **14,973** | **191** | **2,048** | **12,734** | +13 NOs; screened 1,181, investigated 49, held 36. |
| **10: Astra reverse-ending method** | **14,973** | **191** | **2,144** | **12,638** | +96 NOs, predominantly shared successor/revocation sources. |
| **11: reconciliation of Opus Stage 9 v2** | **14,973** | **193** | **2,322** | **12,458** | +2 YES, +178 NO from 180 Opus reviewed cases; including 131 previously uncounted solely because the frozen civil-service ownership manifest was unavailable. **Structurally verified, provisional for legal review.** |

**Why Stage 4's growth can mislead.** A jump from 7,453 to 14,973 validated identities almost doubles the denominator while adding a large majority **UNKNOWN** identities, so coverage might fall even though more historical records were sourced. Its NO total also incorporates 11 prior provisional records that became eligible for inclusion, not 11 new legal-status findings. Algebraically, the **same fixed 7,453 validated cohort** after Stage 4 had **151 YES, 1,092 NO, and 6,210 UNKNOWN**; the additional 11 NO appear when older, previously provisional NO identities enter the expanded population.

**Stage 7 correction.** An initially issued preview showed **191 YES, 1,698 NO, 13,084 UNKNOWN** after counting four Astra civil-service NOs. Independent review quarantined EO **5333, 5335, and 5347**, leaving one Astra NO and **407 Opus NOs**. Corrected totals: 191/1695/13087. Older printed percentages **12.616042%** (uncorrected) and **14.8868%** (miscount in later draft) must not be cited as the actual accepted Stage 7 or Stage 8 checkpoints. Correct Stage 7 coverage **(191+1695)/14973 = 12.596006%**; Stage 8 **2226/14973 = 14.866760%**.

**Stage 9's split inputs can mislead.** Both Astra and Opus independently began from a Stage 8 source snapshot. Astra's Stage 9 gave 13 NOs. Opus's Stage 9 v2 reported **49 accepted substantive cases** (two YES, 47 NO) plus **131 separately model-reviewed determinate cases held purely for missing proof of nonoverlap with Astra's 1,181 frozen civil-service assignments**. It printed a hypothetical 2,275 status numerator using the *older* Stage 8 baseline, **not** a globally reconciled latest result. Astra subsequently made another 96 Stage 10 NOs. The Stage 11 coordinator obtained the exact original frozen split, verified that none of Opus's 180 overlapped Astra's frozen scope or the current accepted Stage 10 IDs, and added **all 180** once, producing the new **2,515** numerator. The additional Opus statuses were **178 NO and two YES**. The 131 ownership-held findings were not 131 newly researched findings in the coordinator session; their legal reviews were inherited from the Opus package.

**Current any-effect axis** grew differently because residual duties were held where legal closure was not proved. Stage 10 had **203 YES, 2,053 NO, 12,717 UNKNOWN**. Stage 11 has **205 YES, 2,165 NO, 12,603 UNKNOWN**: two new YES and 112 new NO on any-effect, while 66 of the 180 new substantive cases remain any-effect-UNKNOWN. In particular 65 of the committee tax-inspection orders have unresolved residual confidentiality duties and EO 12001 has unresolved contract-administration responsibilities; these cannot be silently treated as NO/NO.

### Historical causation progress is a separate chronology

The original Claude causal workstream received **newly substantive-NO membership lists** from successive releases, with disjoint version/cohort rules: an initial V1 of **952** (941 validated +11 then provisional); a V2 of **151** new Stage 4 NO; V3 **139** new Stage 5 NO; V4 **45** new Stage 6 NO; V5 initially **407 Opus +4 Astra** Stage 7 candidates but only one Astra remains accepted after quarantine; V6 **340 Opus** Stage 8 NO; V7 **13 Astra** Stage 9 NO, plus Opus subsequently issued a *provisional* V7 label on 47 NOs that would collide if taken as a finalized global cohort name. Astra Stage 10 had an additional distinct 96-NO handoff; Stage 11's **178 new NO** were placed in `PENDING_CLAUDE_NEW_NO_178.jsonl` pending a collision-free causal-cohort version. **These handoff files establish eligibility for future cause research, not completion of that research.** Causation dates and housekeeping flags were intentionally not overwritten by these status-only agents.

The ledger presently retains **2,216/2,322** substantive-NO orders with unknown `cessation_mechanism` and **2,223/2,322** with unknown `first_cessation_date`. That must be treated as a key research deficit, not an optional footnote to a status-coverage success.


## 6. Research machinery: source acquisition, legal decisions, concurrency, and verification

### 6.1 Evidence store and chain of custody

The project moved away from a manually maintained spreadsheet to a machine-readable record system. A canonical instrument identity is joined to its source observations, aliases, relationships, producer proposals, reviewer dispositions, individual operative clauses, competing evidence, and versioned status decisions. A historical observation may assert "revoked by EO X" or "codified as of 1989," but a **legal classification is separately decided**, not automatically imported from that assertion.

Evidence records conventionally include a publisher/host, original URL, capture date if genuinely measured, source type, saved representation path, SHA-256, exact quoted text, locator/page/section or byte/character span, and document date. Distinctions are recorded among `original_bytes`/official PDF, hosted HTML or archival transcript, model-transcribed source, agency editorial annotation, index/search snippet, and inferred relation. Where source acquisition failed, a source declaration and gap remain rather than a fabricated local original. Quotes extracted from a cached text are tested for exact occurrence in that representation. However, a quotation can match a **wrong, partial, or corrupted** representation perfectly; a stored checksum is evidence integrity **relative to the stored file**, not independent historical authenticity.

The Stage 1 pipeline used ten acquisition/audit workers with nine effective workers (one failed due model capacity) and an observed maximum delegated concurrency of six. It imported 37,669 new quoted observations across early numbered, historical codification, Federal Register modern, dependency, and selected primary-control families, with 24,778 directed observation rows collapsed into 10,903 **candidate** relationships. A relationship candidate can concern an amendment, an institution, a statute, a cross-reference, a partial revocation, an administrative continuation, or a false-positive mention. It is not a unique terminated order. Stage 1's repaired extractor initially produced **20 false historical relationships**—14 caused by matching the substring "continued" inside "discontinued," six by confusing termination of an office/position with termination of the EO itself. Those errors are important evidence that even perfectly hashed parsing outputs can be conceptually wrong.

### 6.2 Candidate legal determinations

A substantively defensible determination is supposed to proceed as follows:

1. **Identify** the precise presidential instrument or warranted bibliographic subject and aliases; confirm it belongs to the declared population and was not already accepted in the versioned ledger.
2. **Recover** the complete original operative text—or, only when the frozen codebook expressly permits it, a genuinely adequate official whole-scope dispositive endpoint that proves the legal footprint without claiming original bytes were read. Preserve annexes, cross-referenced regulations, authority, amendments, and source limitations.
3. **Break down** each command, permission, designation, delegation, amendment, condition, exception, operative person/entity, target and time period. For amenders, link exact changed host provisions; for a grant, identify evidence of exercise and the possible survival of unexercised authority.
4. **Trace** later executive orders, laws, regulations, agency successors, property/transaction documents, court actions, extensions, savings provisions, and possible reauthorization or revival through the October 14, 2026 cutoff. Assign event dates and source validity intervals.
5. **Decide** substantive YES/NO/UNKNOWN and any-effect YES/NO/UNKNOWN **separately**. For YES identify a present qualifying norm and a bounded documented change search. For NO account for **every operative scope**; absence of a reference or revocation note does not suffice.
6. **Record** a legal rationale, codebook rule, precise evidence quotations and hashes, limiting predicates, remaining source gaps, potential counterevidence, producer and review identities.
7. **Review** via another model-agent instance and, when warranted, a genuinely independent source retrieval; classify disagreements or missing evidence as HOLD/UNKNOWN rather than counting them as confirmed NO.
8. **Integrate** only reviewed determinations that clear baseline membership, ownership, exact-ID, duplicate and version guards. Freeze all unrelated ledger rows and all historical/cause fields owned by a separate workstream; preserve holds in another file.

These were the **intended** rules. Performance differed markedly among agents and source families. Some Stage 10 acceptances explicitly rested on a successor's whole-revocation endpoint without complete predecessor originals. Some earlier statuses were based on hosted transcripts and a bounded historical evidence search. The auditor must test whether that exception was consistently used only where whole-scope termination truly follows—especially for original orders that amended another order, saved prior rights, or granted permissions whose execution is unknown.

### 6.3 Division of labor and preserved ownership

The work adopted a versioned *parallel contract*: **Astra** handled much of identity, present legal-status and Civil Service research; **Claude Opus** handled initially National Recovery Administration/NIRA and retirement statutory families, later tax inspection, wartime workday suspensions, administrative committees, historical closings, and some property authorizations; **Claude's separate historical causal workstream** was intended to determine first substantive cessation, whether that first cessation was natural/completion or affirmative intervention, and whether subsequent revocation was housekeeping. Producers and reviewers could be distinct AI model instances, and their submitted records were frozen rather than editing a shared live ledger concurrently.

The frozen Stage 7 Civil Service exclusivity manifest had **1,181 exact IDs**, divided into P1 **705** and P2 **476**. These are ownership limits, not evidence that the underlying EOs were valid or unresolved. In Stage 9 Astra screened all 1,181 at metadata level but individually investigated only **49**, recovered full originals for **29**, and generated **13** new reviewed NO/NO findings, holding 36. Earlier Astra progress was much slower than Opus, which used source-reusable mass classification in NRA and retirement families; the reported Stage 7 Opus family yields reached hundreds of acceptances per overlapped family-clock hour whereas Astra had fewer than ten per measured hour. These rates are **not directly comparable** because agent concurrency, token accounting, initial setup and family difficulty differed.

Stage 10 learned to start with **later ending instruments** that name many earlier orders rather than researching one historical personnel waiver at a time. The results then rose by 96 NO/NO, with audit documentation of cases held when source quality or savings clauses blocked the inference. This is an efficiency observation, not validation that a shared-source rule legally applies to every named predecessor.

### 6.4 Quality gates, frozen history, and failure modes

- The initial handoff and Stage 1 snapshots were hash-verified; a portable Stage 1 rebuild reproduced earlier outputs offline. Stage 1 source quote checks and reparsed-source audits corrected known extraction defects.
- Stage 2 compared classification approaches and froze codebook 2.0.0 after a difficult pilot. An independently assigned **60-decision review sample** supported the coded outcomes under its specified bounded protocol. At that point **one of 39 checks was an expected failure** because **55 declared source files were unavailable**, even though the accepted decisions reportedly did not rely on the missing material. The project documented this rather than marking the missing declarations as present. There was no finished Lean formal proof, and no legal peer review by a human specialist.
- A Stage 2 amendment-footprint challenge discovered **171 leads**, including **75 proposals that could not claim a whole-order legal ending** and were quarantined; **73 stale whole-effect endpoint fields** were corrected. **17 inherited duplicate placeholders** were excluded with preserved aliases rather than deleted. This illustrates real risk from bulk reclassification on one later revocation or parent event.
- Stage 4 checked 187 new legal proposals, performed an identity admission gate for 7,520 records, and reproduced 22 canonical outputs from 909 source inputs in an offline environment; these validate **replay of decisions and deterministic conversion**, not the real-world truth of the accepted claims.
- Stage 7 rejected three of four Astra determinate claims after cross-review: EO **5333** (person identity/death unclear), **5335** (actual appointment not proved by an indexed snippet), **5347** (successor EO 5659 not conclusively extinguishing the exact predecessor). Such cases should remain UNKNOWN pending decisive evidence.
- Stage 8's reconciler hash-tested many cached Opus transcripts and quote matches and accepted 340 by *reported* original Opus model review plus structural checks; it explicitly did not independently perform 340 fresh legal analyses.
- Stage 9 Opus reviewers made many legal-rationale corrections, and in **34 tax-inspection cases rejected only the proposed any-effect NO**, leaving substantive NO. Failure to distinguish axes would corrupt the reported 180-case integration.
- Stage 10 assigned distinct reviewer model instances and binding record hashes for all accepted IDs, but the global historical relations graph remained incompletely available. Full provenance is therefore stronger than a simple web search, yet still short of evidence that every materially relevant event was found.
- Stage 11 checked **all 180** incoming Opus IDs against the exact frozen Civil Service assignment and Stage 10 ledger, verified included manifest files, and preserved **14,830 of 15,010 unchanged ledger rows byte for byte**. The Opus source archive's manifest lists **148 missing companion originals/images**, about **94.19 MB**, which were not actually present in the supplied ZIP. The reviewer claims for those cases were inherited; an auditor cannot inspect absent originals until the separate companion is acquired. This is a critical gap between *structurally reconciled* and *fully independently legally verified*.

**System-level danger:** Multiple independent model instances can share the same mistaken legal intuition or the same faulty upstream source. Reproducing a ledger from a frozen script can faithfully reproduce a large systematic error. No claimed audit to date supplies a representative sensitivity/specificity estimate across all 14,973 bibliographic identities, nor genuine human legal peer-review certification.

## 7. Substantive research families: what legal reasoning worked, and where it may have failed

This section gives enough representative examples for an independent reader to understand the actual classification decisions and attack their generalizations.

### 7.1 Large historic revocation and National Recovery Administration families

**EO 12553 (February 25, 1986)** is a mass executive-order revocation. The project extracted **386 unique named predecessor targets** from an official source and cross-checked them against archival editorial listings. In the initial Stage 1 sample, all 386 were present as references. That is excellent for *research discovery* but leaves two independent questions: (i) whether the current law of every predecessor is actually extinguished across its complete original provisions (including amendments, third-party effects and savings clauses); and (ii) whether its **first** substantive cessation preceded the 1986 cleanup. The document **EO 12553 itself** is currently coded NO/NO under TC07 as a completed pure disposition, although its repeal consequences persist. The source import later found **52 of its named predecessors still substantively UNKNOWN** after Stage 11.

**NIRA/NRA orders (1933–1935)** commonly approved industrial codes, exemptions, or administrative arrangements under the National Industrial Recovery Act. Opus used legal and institutional endpoints, including Supreme Court invalidation of key NRA regulatory authority, to classify **211** Stage 7 P1 code approvals, followed by **84** Stage 8 P2 approvals; Astra Stage 6 had **38** additional NIRA determinations. But the invalidity or termination of a statutory program does **not** necessarily prove that an executive order's separate procurement condition, contractual right, appropriations clause, transition provision, or cross-agency authority ceased. The source original footnotes identify **EO 6296A**, **EO 6749**, and an original **EO 6756B** transcript gap as held problems. Another 16 exact mixed-purpose NIRA P3 IDs were recovered from the frozen original split for later research; they were not guessed from title keywords. Auditors should isolate a sample of NIRA NOs with additional clauses and test whether the family-level rule was overapplied.

**EO 11408** listed many earlier orders whose treatment was limited **"insofar as" they construed or amended EO 9**. Source mining presently produces **51 UNKNOWN** affected predecessors. The "insofar as" clause is the opposite of proof that each predecessor is wholly dead. A research engine that maps this edge simply as `revokes_entire_order` would produce a large systematic false-NO cluster. A successful whole-scope NO can be accepted only if all other original effects were investigated or a genuinely adequate later endpoint was established.

### 7.2 Civil-service authorizations and the EO 3461 group

**EO 3461 (May 16, 1921)** lists approximately **45 earlier World War I-related Civil Service exceptions** and revokes them, **but explicitly preserves eligibility for persons already appointed to retain excepted status in specified continuing positions**. It combines whole-looking revocation language with an incumbent-protection clause. Astra Stage 9 accepted only **EO 2734 and EO 2752** in this family; Stage 10 accepted another **42 NO/NO** after person/date/scope matching and an argument that the saved incumbents derived their rights from the successor's saving clause rather than the original permission. **Only four of those 42 had full original-operative-text copies; 38 used an allowed "adequate whole-revocation endpoint" substitute**. The project documented this grading. An adversarial reviewer should focus here: the broad inference may be wrong if a predecessor did more than create a removable wartime exception, if a durable right remains legally attributable to the predecessor, or if changing the attribution convention changes NO to any-effect YES. If this family fails, it could subtract dozens of accepted NOs with correlated error. A retrospective source title matching the 45 names and dates does not alone resolve such attribution questions.

**EO 6179-A (1933)** cancelled appointments by named individuals. Eight earlier civil-service authorizations—**EO 5069, 5204, 5620, 5893, 6028, 6061, 6063 and 6067**—were accepted as spent permissions after matching those appointments to the later cancellation. However, **a revoked appointment is not necessarily revocation of the underlying eligibility grant or all other EO provisions**. The Stage 9 report expressly warned that EO 6179-A did not revoke the predecessor executive orders by number. It also held EO 5058 due a name mismatch and EO 4528 because of missing original scope. An auditor should retrieve all eight predecessors and independently ask whether their permission was one-use, whether exercise was proved, and what happened to all continuing clauses.

**EO 10577 (1954)** reorganized the Civil Service Rules and revoked several earlier personnel instruments but **saved certain Schedule A/B/C statuses**. Stage 10 supported three new NO/NO determinations after a full text/position crosswalk. Broad statutory reforms such as the **Civil Service Reform Act of 1978** preserved some preexisting executive actions according to their terms. An order's elderly beneficiary, presumed mortality, obsolete job title, or expired statutory regime alone does not prove NO.

### 7.3 Public lands, Indian trust terms, transfers, and continuing legal status

**Stage 6 BLM/public-land order cohort:** Seven early presidential land withdrawals or reserve additions were accepted NO/NO after specific Public Land Orders: EO **5214** (several Alaska Navy withdrawals later terminated), **9029** (original as amended revoked by PLO 833), **6604** (PLO 711), and **7185, 7212, 7452, 8331** (four Upper Mississippi refuge additions revoked in PLO 936). Separate new PLO administrative reservations were not treated as continuing under the earlier EO. Another seven BLM candidates—**1450, 4812, 3924, 1513, 6833, 6086, 4953**—were held because whole original scope or amendment chains were incomplete. A PLO can be a later legal event affecting an EO without itself being added to the counted presidential EO population.

**Indian land/trust restrictions:** Under modern **25 U.S.C. § 5102**, certain trust restriction periods may be extended until Congress determines otherwise. A historic EO's printed trust-end year cannot automatically be treated as the true terminal date. Continuing property/status effects can persist without a current agency command. An auditor should determine whether the project used land title, conveyance, trust legislation, and withdrawal records consistently, and whether TC06 treats enduring reservations differently from completed revocations under TC07 for defensible reasons.

**Alien Property Custodian individual sales:** The authorization of one named sale does not establish that the sale actually occurred. The Custodian's office was transferred/abolished and successor property administration persisted, including **EO 6694**, later **EO 8136** and **EO 9142** relations and potentially durable claimant rights. Opus Stage 9 researched ten single-sale leads and accepted only **two**, holding eight for lack of transaction/savings proof. This low yield is a legitimate quality outcome, not an excuse to code old property orders NO based on program age. Find the individual deed/conveyance/vesting record and trace surviving property interests before deciding a particular authorization's legal fate.

### 7.4 Expiration, completed events, historic labor orders, and tax confidentiality

**Temporary office closing and commemorative orders:** If an EO solely closes government offices on a specific past date and contains no other durable provision, the relevant once-off command is generally spent under TC07. Opus accepted 17 dated closings/rail or airline emergency board endpoints and 13 commemorative or exhibition orders in Stage 9. However **EO 12001** was classified substantive NO but any-effect UNKNOWN because of potentially enduring administration of bicentennial contracts. That is the exact type of exception a bulk "ceremonial means no effect" rule must retain.

**Emergency labor boards and residual records:** Stage 5 identified **12** executive orders for which the substantive emergency-board assignment had completed but an archival record-custody/retention duty was independently treated as continuing. They are **substantive NO / any-operative-effect YES**, demonstrating that the two axes can actually diverge. These are an especially good adversarial sample for whether an ancillary duty attributable to an EO remains legally binding after the institution ceases to exist and after later records statutes or regulatory changes.

**Wartime eight-hour workday suspensions:** Opus Stage 9 examined 46, accepted **39 NO/NO**, and held seven due missing original operative texts. Some legal reasoning referenced a **1927 Comptroller General opinion** (reported as 7 Comp. Gen. 73) treating World War I emergency suspensions as exhausted. That administrative opinion may bind federal accounting administration without conclusively deciding legal scope for courts, claimants, or unrelated statutory contexts. Test original triggers, payroll claims, successor statutes, and extension/savings on an independently stratified sample. Do not equate "World War I is over" with proof that every retrospectively accruing right was extinguished or that a war-only suspension did not become codified in a successor scheme.

**Tax-return inspection EOs:** Opus examined 98 members of a pre-1977 historic family and accepted **90 substantive NO** after congressional committee terms, temporal endpoints, and other original limitations were reviewed. **25** of these were NO/NO; **65** were substantive NO/any-effect UNKNOWN because the original permission's old confidentiality conditions might survive for returns governed by pre-1954 rules. The 1976 rewrite of **26 U.S.C. § 6103** is not automatic proof all prior presidential permissions or saved duties ended. Opus highlighted the unresolved fate of **26 C.F.R. § 458.324**. In 34 reviewer comments the any-effect NO proposal was overturned, *not* the substantive NO. A later merger must preserve this distinction. An adversarial reviewer should also consider whether an expired committee permission had any independent enduring effect and whether an earlier inspection authorization created continuing confidentiality obligations or whether those rights arise solely from later law.

**Advisory councils/committees:** In Opus Stage 9, 14 advisory-committee continuance orders were determined, **two YES**, **twelve NO**. One YES, **EO 14354**, reportedly continued certain committees to September 30, 2027. Another, **EO 13708**, was an amendment to EO 12829 whose amended text was held to remain operative. Ending an advisory entity can exhaust a past grant, but if its parent host, saved position, or amendment persists, the original instrument may still have traceable effect.

### 7.5 Examples where researchers explicitly refused simple conclusions

- **EO 10807:** the Federal Council for Science and Technology was later abolished, but the original EO also amended EO 10521. The host-amendment trail and present successor-actor mapping were unresolved, so a superficially obvious NO/YES was held. **EO 11381** was separately accepted NO/NO because it solely changed Council membership.
- **EO 12034:** a proposed NO was rejected in Stage 10 because a modern implementing regulation still specifically referenced the volunteer cohort under the original EO; this illustrates the duty to search beyond repeal titles.
- **EO 9805:** savings retained earlier terms for some incomplete transfers; six proposed endings were held rather than automatically terminated.
- **EO 10180:** evidence of surviving retirement operation blocked an automatic NO.
- **EO 9830:** contained independent provisions beyond its old revocation list; blanket institutional expiration was not enough. Its separate historical revocation list was mostly exhausted already, so repeated research had poor coverage return.
- **GSP tariff/Generalized System of Preferences:** an initial 20-case pilot produced **zero accepted NOs** after the savings protection in **19 U.S.C. § 3011** and version-crosswalk issues undermined a simple statutory-sunset shortcut.
- **EO 5333, 5335, 5347:** three originally accepted Astra civil-service cases were quarantined because beneficiary identity, original appointment, and express successor scope were not established.
- **EO 10480:** an order incorporated into a later host/successor chain illustrates that a later revocation may not settle whether amendments originally made by an earlier EO remained in force. Historically the project reopened such cases rather than using a single "dead by later revocation" flag.
- **EO 3016C and 3016N:** orders associated with delegated Secretary of State **Frank L. Polk** rather than directly signed by a president raise a *census membership* question separate from their 2026 legal force.

The point of these examples is **not** that the project got every one right. They document the operative methodological rules and known boundary problems, so an external auditor can discover when nominally similar orders were assigned inconsistent statuses.


## 8. The government-disposition acceleration project and current research queue

A later effort asked whether official government editors had already done years of legal-history research that could be harvested at scale. It recovered **all 18 National Archives historical EO codification HTML tables and seven Federal Register bulk-data response pages** from the project's original Stage 1 archive, rather than repeatedly searching for individual EOs. It built a reusable importer with exact canonical crosswalks, actor-reference extraction, shared ending-instrument clusters, source-version hashes, conflict quarantine and a prioritized queue. The importer was explicitly forbidden from turning an editorial 1989 disposition label directly into a present-status NO or YES.

Against the **Stage 10** baseline (191 YES / 2,144 NO / 12,638 UNKNOWN), its recorded complete metrics were:

| Import measure | Value | Caveat |
|---|---:|---|
| Source rows parsed | **11,164** | 4,208 numbered NARA codification rows +6,938 FR bulk-record identities +18 NARA unnumbered source rows. |
| Canonical ledger identities with ≥1 source record | **7,452** | Source rows often overlap; this is a count of distinct matched current ledger IDs, not the census. |
| Distinct Stage 10 substantive UNKNOWN with source evidence | **5,594** | Some sources have no ending note or only a dated editorial cross-reference. |
| Unknown higher-priority candidates | **2,948** | Prioritized leads, not accepted classifications and not a representative population. |
| Candidate incoming explicit-ending group | **1,384** | May contain savings/partial scopes; counts overlap other analytical groupings unless the track is exclusive. |
| Named ending-instrument group | **approximately 337** | Editorial successor reference; requires original instrument. |
| Other historical endpoint group | **approximately 782** | Temporary/executed/statutory ending candidates, not automatically NO. |
| Historically codified possible continuity | **445** | Potential YES hypotheses; requires full 1989–2026 legal bridge. |
| Named successor clusters | **942** | Broad relation groups; many do not by themselves end the predecessor. |
| All extracted actor-reference edges | **6,575** | Include amendments and other references, not just endings. |
| Candidate ending edges | **3,140** | 1,048 distinct actor-ending clusters, potentially with multiple affected originals. |
| Quarantined actor-ending references | **117** | Scope/identity not verified. |
| Conflicting NARA versus FR ending actors | **15** | Isolated for source review, not silently selected by preference. |
| Source rows unmatched to ledger | **0** | Exact mapping success does not prove completeness or legal provenance. |
| New 2026 legal-status decisions from import | **0** | Correct: metadata remains research evidence only. |

Some raw importer audit reports differ slightly on mutually exclusive **priority-track allocation** (e.g., 336 vs337 named-successor, 782 vs783 other-endpoint) while preserving the invariant **2,948 unique priority members**. Treat the distinct set and its exact canonical IDs as authoritative for queue ownership, and require the auditor to inspect the allocation code rather than reconciling inconsistent descriptive subtotals by inventing records. An initial transcribed small sample was superseded by the archived-source full import. The older 1989 NARA codification is not a full contemporary disposition table, and the FR export includes overlapping material; the 11,164 record count must not be called 11,164 separate EOs.

After Stage 11 added the 180 reviewed Opus findings, **122** of the former 5,594 source-matched unknowns had received substantive statuses; **5,472** still had at least one linked government-source record. The priority worklist lost **107** previously unknown members, leaving **2,841 distinct prioritized UNKNOWN IDs**. The Stage 11 coordinator anti-joined against all previously determined IDs and the frozen original agent assignments. The planned exclusive production split is **Astra 1,696 reverse-ending cases** and **Opus 1,145 finite/completion/continuity cases**, plus **16 recovered exact NRA P3 identifiers** on a separately identified Opus queue. The 16 must be checked for overlap before any aggregate planning total is stated; the first two lists are explicitly disjoint.

The biggest immediately named clusters are **EO 12553: 52 currently UNKNOWN predecessors** and **EO 11408: 51**; the latter's express *insofar-as* restriction makes whole-order closure legally risky. Smaller source clusters include EO 9521 (11), EO 10903 (11), EO 11051 (10), EO 8036 (9), EO 12163 (9), and EO 9801 (9). Historical finite-source candidate tags include **143 "executed and obsolete," 173 "temporary," 118 named-event, 133 statutory-authority-repeal**, and roughly 445 historically codified potential continuers; **these categories overlap and cannot be summed**. A 1989 "codified continuing" label cannot establish 2026 YES without searching for changes in the intervening 37 years.

The proposed execution policy is to retrieve a reusable controlling source once, sample **8–12 genuinely diverse operative subtypes per family**, have a separate reviewer challenge each proposed new YES/NO, batch-expand if an actual shared legal predicate works, and pivot quickly if source retrieval or independent legal yield fails. This improves **classified unknowns per research resource**; it cannot be allowed to silently weaken legal gates because a family offers a large numerator.

## 9. What the system did *not* prove and why the gaps matter

### 9.1 Census completeness remains unestablished

The historical source universe includes fragmentary presidential records, retroactively assigned EO numbers, unnumbered and informal executive directives, retrospective bibliographic indexes, editorial compilations, text fragments, subsidiary orders, and ambiguous documentary groups. There is no comprehensive crosswalk of signed orders to the 14,973 identities. The **1789–1862 gap** is fundamental because the numbered series begins in 1862, and the 1943 Lord unnumbered index remains unprocessed. There is no defensible way to turn the latest row count into an exact claim that a certain number of executive orders were issued in U.S. history.

Even if APP's total 16,238 were accepted as complete—which it should not be—it is definitionally different. An auditor should propose *scope-conditional* denominators by period/source with documented completeness boundaries, and a separate "all identified" catalog with explicit unresolved identities. Publication must explain missingness, not hide it in a footnote.

### 9.2 Legal correctness of accepted statuses remains uncalibrated

The numerator 2,515 represents **model-reviewed accepted classifications** under project codebook 2.0.0, not 2,515 externally confirmed judicially correct legal holdings. There was targeted independent model review and deterministic structural reconciliation. There has not been a large blind independently drawn legal audit with external subject-matter attorneys, a representative per-era/per-class error-rate estimate, or proof that contemporaneous documents and current law were comprehensively consulted for all cases. Correlated batch failure is the major danger. Forty-two wrong decisions based on EO 3461 would still produce forty-two correct-looking file hashes and reviewer attestations.

A whole-order NO is particularly demanding: missing one operative clause can invalidate it. A positive YES has a different burden—identifying one operative clause plus searching plausible later modifications—so **acceptance rates depend on ease of proof as much as underlying survival rates**. Without sampling, accepted YES/NO fractions measure the selection process, not the natural frequency of true active/inactive statuses.

### 9.3 The first historical cause of cessation is mostly unresearched

The question *"How many orders ceased without having to be touched?"* is a **causal and chronological** question. Knowing that an order was revoked in 1986 and does not operate in 2026 does not establish whether a 1967 expiration, an earlier statutory change, compliance with a one-time task, or the 1986 revocation first ended its effect. A later repeal may remove a document that already ceased to operate, or it may sever durable residual rights, or it may apply only to part of an order. Some later laws require preservation of claims notwithstanding expiration of other duties.

The accepted substantive NOs are routed to a **distinct first-cause research workstream**, but the latest ledger still has ~95% of NO records lacking a first cessation mechanism or precise date. The original article's potential headline **relative share of spontaneous expiration versus intervention** is therefore **not empirically measured**, however advanced the present-status classification progress bar appears. A separate count of housekeeping revocations requires proof of a *pre-revocation ending* and that the later revocation did not extinguish some other still-operative provision.

### 9.4 Policy continuity is not necessarily continuing authority under the source EO

A government institution may continue under a new statute after the EO that founded it is revoked; a statute may reenact an earlier EO's policy; a regulation may be traceable to a former EO but supported by independent statutory delegation; a saved individual right may owe its present binding effect entirely to a later saving clause. The chosen ontology must specify **attribution**, not merely historical influence. It is possible to count **policy survival** correctly but **original EO operation** incorrectly, or vice versa. The converse risk is that treating all spent acts as inoperative obscures durable legal constitutive changes. TC07 and TC09 make the answer convention-dependent and need published sensitivity analysis.

### 9.5 The date dimension is incomplete and can mislead

Effective date may differ from signing, filing and Federal Register publication; a later law may have a retrospective effect or preserve claims accrued earlier; judicial stays and geographic relief vary over time. Sources have distinct *as-of* dates (e.g., Jan 1989 NARA codification; 2017 older NARA disposition archive; 2026 FR data). Even accepted NOs generally retain unknown first-cessation dates. Dates may be stored as upper bounds, date intervals or inferred administrative termini. A complete dataset should not substitute issuance year, later citation date, or the date of editorial annotation for cessation.

### 9.6 Bibliography, legal inference, and model review are different confidence layers

Stage 1 gave thousands of government-source *citations*; Stage 4 gave thousands of *validated bibliographic identities*; Stages 2–11 gave smaller quantities of *adjudicated present-effect statuses*. Those are not successive increasing measures of the same epistemic claim. The adversarial AI should inspect records moving between layers and identify where a source's lower-quality status label was inadvertently upgraded by a deterministic pipeline or where a reviewer saw only the same agent's produced excerpt rather than independent primary bytes.

## 10. A ranked agenda for an outside critic to attempt to falsify this project

The tasks below are **not** merely optimizations. They are tests of whether this entire research design is conceptually defensible. The project invites a finding that its published numerator, denominator, or legal categories should be abandoned and rebuilt.

| Rank | Failure hypothesis to test | Concrete falsification procedure | Expected implication if verified |
|---|---|---|---|
| **1 — potentially fatal** | The 14,973 "orders" are a mixed collection of physical orders, numbered provisions, retroactive labels, nonpresidential delegated acts, and editorial table rows. | Draw matched sample from each population class; recover original instruments, signatures, issue context; construct 1:many and many:1 crosswalk; reconcile large numbered subseries and LOC unnumbered volume. | Redefine unit and denominator; reaggregate all classifications and historical event matches. |
| **2 — potentially fatal for all-history claims** | An enormous share of pre-1937 unnumbered EOs is missing, making a national survival rate impossible. | Acquire Lord's 1943 *Unnumbered Series 1789–1941* and independent archival registers; estimate distinct identifications; compare by administration to project, APP, and source-quality bins. | Restrict target to enumerated subpopulations and disclose lower-bound/incompleteness rather than publish an exact national count. |
| **3 — potentially fatal for legal meaning** | TC07 / "completed disposition" makes the continuing-effect measure legally incoherent or inconsistent with treatment of durable land/institutional designations. | Compare one-time repeals, land withdrawals, executed appointments, institutional creations, amendments, and incorporated statutory norms under at least two doctrinally credible attribution theories. Recode a seeded diverse panel. | Change codebook, recode sensitive families, publish multiple definitional estimands. |
| **4 — high systemic risk** | Bulk NO classifications overgeneralize an ending authority to all predecessor clauses and saved rights. | Independently audit 20–40 risk-weighted accepted NOs from EO 3461, NIRA, retirement, EO 12553, and dated boards, with unseen original text and successor chain; include all exceptions. | Quarantine entire affected families until corrected; downward-revise coverage and add affected holds. |
| **5 — high systemic risk** | Source completeness and evidence independence are overstated by SHA checks and same-model reviewer agreement. | Trace a random sample of claims from `source_id` to *original official page image*; blind-review normalized source/quote, check missing original bytes and transcription artifacts; compare reviewer exposure. | Regrade evidence, require independent originals for vulnerable decisions, withdraw unproved claims. |
| **6 — high research-validity risk** | Positive YES is over-attributed to original EOs even though present law is independent statute or later EO. | Sample affirmative YES by category; require operative attribution, amendment lineage and actual current authority, not mere historical influence. | Reduce false-positive YES and update attribution logic. |
| **7 — high research-validity risk** | NO is declared from historical obsolescence without positive proof grant was exercised, sunset occurred, or all contingent rights expired. | Target personal appointments, Alien Property sales, wartime labor exceptions, historical boards and trusts; recheck exact original conditions and administrative execution records. | Convert unsupported NOs back to UNKNOWN, possibly altering whole legal families. |
| **8 — central-goal failure** | Project is advancing an easily measured coverage bar while failing the question it exists to answer: *first cause* of cessation. | On each accepted NO, determine first terminal mechanism versus merely latest formal revocation, with date bounds and intervening action. Calculate proportion truly causal-known and evaluate a representative sample. | Reorient the project and postpone claims about natural expiration and housekeeping. |
| **9 — high population QA risk** | APP and project counts appear similar in modern periods while counting different physical documents; errors cancel within totals. | Perform item-by-item, period-by-period canonical joins, track ± differences and suffix corrections; inspect missing Lord pages486–487. | Rebuild canonical inventory and correct duplicated/omitted IDs. |
| **10 — moderate but proven** | Original 1,943 cohort flag silently drifted to 1,950. | Set-diff original 1,943 IDs against `original_1943_cohort`; inspect seven NARA unnumbered rows. | Fix provenance tags, add regression tests and inspect other inherited migrated fields for silent drift. |
| **11 — high analytical risk** | Published YES/NO percentages are mistaken for survival rates because UNKNOWNs are concentrated in difficult eras/legal families. | Tabulate UNKNOWN by year, source, original-text availability, status mechanism, family and agent assignment; test stratified random audited cohorts. | Do not extrapolate accepted ratios or report a single national survival rate. |
| **12 — high source-specific risk** | The tax confidentiality and wartime-pay rules are wrong beyond small reviewer corrections. | Independently reconstruct 26 CFR458.324 history, 26 USC6103 transitional provisions, and 7 Comp. Gen.73 status with statutes and court decisions. | Reassess up to 65 residual axes and 39 wartime NOs, as warranted. |
| **13 — high temporal risk** | Current 2026 legal-state search misses late revivals, statutory savings, later repeal of repeal, injunction/stay changes or unpublished cutoff-week EOs. | Build genuinely complete later-event corpora by era and cross-check selected descendants through October14; sample 2025–26 actions. | Qualify present YES/NO and cutoff census, restore unverified to UNKNOWN. |
| **14 — moderate methodology risk** | Frozen codebook, editorial classes and source-availability strata influence which cases are selected and reviewed, inducing ascertainment bias. | Compare sampling-frame strata with processed vs unresolved cohorts; explicitly estimate or bound coverage-dependent misclassification using blind stratified reviews. | Stop making population-frequency inference from convenience-sampled completed cases. |

### Suggested minimal but genuinely adversarial audit protocol

**A. First establish what the dataset's rows mean.** Treat `validated_historical_index`, `documented_unnumbered`, and `validated_numbered` as separate candidate sampling frames. For a reproducibly selected sample (e.g., 30/30/30, deliberately more from anomalous suffix/group types), map each to a signed instrument or documentary proxy and record whether it is genuinely a U.S. presidential EO. An acceptance rule must be established *before* considering the project's label. Count one-to-many and many-to-one links; test the wrong-documented-source possibility, not just whether a PDF contains a matching number.

**B. Reconcile the national denominator separately.** Construct an APP-versus-project per-administration discrepancy matrix, but treat the historical source catalogue as more important than comparing totals. Obtain Lord's unnumbered series and look for entire missing classes. Explain which subperiods, if any, are complete. No numerical comparison alone proves completeness.

**C. Audit legal meaning independently of source availability.** Write an opposing memo on TC07, TC09, TC08 savings attribution and the definition of substantial current effect. Apply each alternative to a deliberately diverse panel and report precisely which accepted decisions would change. Name doctrinal authorities rather than reciting intuition.

**D. Falsify accepted status in high-risk clusters.** Pick heterogeneous original clauses from EO3461 (including those lacking cached originals), amended-host orders from EO11408/EO12553, limited tax committees, wartime suspensions, BLM land/trust orders, NIRA mixed-purpose codes, and affirmative YES. Independently acquire sources and blind-check original operative scope before opening project rationales. Then compare findings, and identify **shared-root failures** (same legal source or inference rule produces many wrong cases).

**E. Examine error propagation and visibility.** Independently reproduce 15,010-row counting, cross-axis logic, 180-case Stage11 patch, manifest hash verification, 1,950 legacy flags, and source disagreements. For a sampled set of model-reviewed cases, check whether the separate reviewer truly consulted full original bytes instead of producer excerpts. Recover the missing 148 Opus original/image files if needed. Never state legal source fidelity from hashes alone.

**F. Evaluate the actual article estimand.** Ask whether "orders no longer in effect" counts at the **order**, **provision**, **operative episode**, or **policy** level; whether multiple amendments to one host lead to double attribution; whether once-off repeals are definitionally expired; and whether the causal buckets are operationally identifiable. If the answer demands provision-level analysis with no reliable aggregation, recommend changing the study design even if that reduces the count of completed instruments.


## 11. How another AI could reproduce the arithmetic and inspect the evidence

**This Markdown document is intentionally self-contained about the project's thesis, evidence claims, methods, and known defects.** It does not and cannot contain the approximately 90 MB of companion compressed archives, many gigabytes of historical raw-source volumes retained in earlier stages, or 15,010 individual ledger records. Therefore an auditor with **only this Markdown file** can analyze internal logical consistency, test legal/census methodology against public sources, and identify promising falsification cases, but **cannot honestly claim to have independently hashed or re-adjudicated records it has not received**. If a subsequent review supplies archives, the following explains which objects to ask for and what assertions each permits checking.

### 11.1 Latest machine-readable checkpoints (names and exact contents)

**Primary Stage 11 self-contained execution outputs:**

- `EO_STAGE11_RECONCILED_EXECUTION_PACKET_2026-10-16.zip` (about 4.4 MB) contains a `RECONCILED_STATUS_LEDGER_STAGE11_PROVISIONAL.jsonl` with 15,010 current records; `OPUS9V2_RECONCILED_STATUS_DELTA_180.jsonl`; `PENDING_CLAUDE_NEW_NO_178.jsonl`; `LEGAL_REVIEW_QUALITY_FLAGS_180.jsonl`; `MISSING_OPUS_COMPANION_IMAGE_AND_ORIGINAL_FILES.jsonl`; `INTEGRATION_AUDIT.json`; `METRICS_STAGE11.json`; `SCRIPTS/build_stage11_from_inputs.py`, `SCRIPTS/verify_release.py`; `WORKLISTS/` and `PROMPTS/`; `README_FIRST.md`, `REPORT_STAGE11.md`, and an HTML progress dashboard.
- `EO_STAGE11_FULL_SOURCE_HANDOFF_2026-10-16.zip` (about 90 MB) contains the compact Stage 11 execution packet as an embedded ZIP under `EXECUTION_PACKET/`, plus four unchanged input archives under `INPUTS/`: `ASTRA_STAGE10_EVIDENCE_FIRST_DELTA.zip`, `OPUS_STAGE9_STATUS_DELTA.zip`, `EO_DISPOSITION_IMPORT_STAGE10_CHECKPOINT_2026-10-16.zip`, `EO_Stage7_Astra_Opus_Split_2026-10-15.zip`. It does **not** magically supply the missing separate Opus source-image archive.
- `EO_DISPOSITION_IMPORT_STAGE10_CHECKPOINT_2026-10-16.zip` holds the complete bulk importer, government-source HTML/JSON caches, source hashes, matched evidence tables, adverse conflict list, priority queues, provenance labels and tests (96 stored files in the checkpoint); the importer changes zero accepted statuses.
- Earlier `EO_STAGE8_RECONCILED_HANDOFF_2026-10-16.zip`, Stage 7 Opus/Astra releases, Stage 5 split source volumes, Stage 2 and Stage 3 archival research packages preserve historical source and review data not fully replicated as raw originals in a simple later ledger. To examine those older bytes, acquire the named stage releases, not merely their metric summaries.

The full-source Stage 11 handoff cannot replace every earlier original publication or the missing Opus image companion. Its scope is precisely declared. In addition, the preparer's original project research brief was held in `EO_Research_Handoff_2026-10-14.zip` under `RESEARCH_BRIEF.md` (initial requirements, verification discipline and causal design).

### 11.2 Exact hash receipts known at dossier preparation

These SHA-256 values were generated from available files and can detect accidental replacement of the named snapshot:

| Artifact | SHA-256 |
|---|---|
| Stage 11 reconciled JSONL ledger | `c0308e008cd719cd153ca667271c93267d5d855bf3eb26d48076e41938fc7729` |
| Stage 11 compact packet ZIP | `548a405a5d67323241f78526fe68236b03ab19aae5517efecd8264b5e53bfab3` |
| Stage 11 full-source handoff ZIP | `b7184e1f5615d60e2cd0feec0f8b31c439ded82f54892f2ea566040e8c245b9c` |
| Government-disposition importer checkpoint ZIP | `a3f9d87441a95c680fa008fe5469c7f1ded402ab2491e6249ae42b04c9aed682` |
| Opus Stage 9 version-2 ZIP | `0596529d62fd4eea48a4bd7baffb8740d89e51177f83a30066d9e2b715a61ebe` |
| Astra Stage 10 original ledger (before Stage 11) | `0508e389f60d3664a02a75ae4719c5175797d934f34afdba0344458cf8df5993` |
| Original frozen Stage 7 Astra/Opus split ZIP | `5b553c027641f8ccfd82906e4f0f47a706968ca1cb4b767ae9501ea94377815a` |

These values verify **identity of available snapshot bytes**, not legal truth or governmental origin. The missing 148 Opus images/PDFs are not verified by the hash of the ZIP that does not contain them. External source hosts and archival digitizations are separately listed in the evidence manifests.

### 11.3 Minimal offline count/reconciliation checks

A subsequent AI with the JSONL can independently run a script equivalent to the following. It must treat the `included_validated` flag as the project's claim to be audited, not as an unquestionable truth:

```python
import json
from collections import Counter
p = 'RECONCILED_STATUS_LEDGER_STAGE11_PROVISIONAL.jsonl'
with open(p, encoding='utf-8') as f:
    all_rows = [json.loads(line) for line in f if line.strip()]
assert len(all_rows) == 15010
rows = [r for r in all_rows if r.get('included_validated') is True]
assert len(rows) == 14973
assert len({r['instrument_id'] for r in all_rows}) == len(all_rows)
sub = Counter(r.get('substantive_effect') for r in rows)
any_eff = Counter(r.get('any_operative_EO_effect') for r in rows)
assert sub == {'yes': 193, 'no': 2322, 'indeterminate': 12458}
assert any_eff == {'yes': 205, 'no': 2165, 'indeterminate': 12603}
assert sum(sub.values()) == sum(any_eff.values()) == 14973
print('Substantive coverage:', (sub['yes']+sub['no'])/14973)
print('Any-effect coverage:', (any_eff['yes']+any_eff['no'])/14973)
print('Population class:', Counter(r.get('population_class') for r in all_rows))
print('Effect cross-tab:', Counter((r.get('substantive_effect'), r.get('any_operative_EO_effect')) for r in rows))
```

**These checks will reproduce the project's claimed accounting whether the identity or legal rules are correct or not.** The stronger test rebuilds the Stage 11 ledger from the exact pinned input ZIPs using the included `SCRIPTS/build_stage11_from_inputs.py`, checks that each new status was previously UNKNOWN, confirms no duplicate accepted membership or assignment-scope overlap, checks that all unaffected rows are byte-identical to Stage 10, checks reviewer/evidence references, and then **independently tests the legal conclusion rather than merely trusting the merge script**.

For the original-queue flag defect, recover the 1,943 unique `canonical_id` values where `in_original_1943_queue` is true in the original CSV and set-compare with the 1,950 currently flagged `original_1943_cohort` IDs. Print the seven nonmatching unnumbered identifiers and their actual source rows. The difference is a real measurable migration defect, even though the current substantive-status totals may be unaffected.

### 11.4 Record fields and why their names matter

The present ledger includes identity (`instrument_id`, `title`, `signing_date`, `population_class`, `included_validated`, `included_observed`), provenance (`evidence_ids`, `source_ids`, `provenance_shard`, `evidence_grade`), status (`substantive_effect`, `any_operative_EO_effect`, `headline_category`, `effect_tags`, `decision_status`, `review_status`), and causation (`cessation_mechanism`, `first_cessation_date`, `last_effect_end_date`, `cleanup_after_cessation`, `formal_disposition`, `revival`) information. `operative_episodes`, `rule_id`, `counterevidence_checked`, `remaining_gap` and Stage 11's embedded `opus9_present_status` may contain additional structured/quoted decision details. Historical fields whose values are unknown still appear in every row. Unknown is **not** the same as negative, nonexistent, invalid, never operated, or not researched at all; there are multiple substates inside it.

At the current version, the primary **validated-unit filter** is `included_validated is True`, **not** all 15,010 rows, all `included_observed` rows, or all rows with an EO-style number. Cross-axis denominators are the *same* 14,973 validated identities, but the number of determinate cases differs. Source observation counts, relation edges, derivative instrument amendments and Claude historical-cause handoff memberships are **not additional EO identities**.

## 12. Useful public sources and what proposition each can support

These URLs are supplied because the reviewing AI has no prior chat or file context. **Public-source existence is not a substitute for checking the particular instrument, dates, edition, and law at the historical cutoff.** Some resources can block automated access or change their presentation; the cited URLs are reference leads rather than a claim that every page remained fetchable during the latest session.

| Public source | URL | Relevance and limitation |
|---|---|---|
| National Archives, *Codification of Presidential Proclamations and Executive Orders*, numeric tables | https://www.archives.gov/federal-register/codification/numeric.html | Official/editorial 1945–1989 codification and historical dispositions; **as of Jan 20, 1989**, no direct 2026 status. |
| National Archives, codification foreword | https://www.archives.gov/federal-register/codification/forward.html | Coverage, cutoff and excluded subject-matter limitations; check before interpreting missing codification rows. |
| National Archives, historical EO disposition tables | https://www.archives.gov/federal-register/executive-orders | Separate tables; older historical collection not continuously updated after Jan 2017. |
| National Archives, historical EO dispositions | https://www.archives.gov/federal-register/executive-orders/disposition | Historical disposition annotations, not automatic continuing-effect verdicts. |
| Federal Register, presidential executive orders | https://www.federalregister.gov/presidential-documents/executive-orders | Modern orders and download interface; publications, corrections and metadata must be deduplicated. |
| Official GovInfo, October 2026 EO 14435 | https://www.govinfo.gov/content/pkg/FR-2026-10-09/html/2026-20855.htm | Specific late-2026 item; does **not** certify coverage through Oct14. |
| Library of Congress, executive-order publication history | https://guides.loc.gov/executive-orders/publications | Pre-1937 preservation, numbering and historical census limitations. |
| Library of Congress catalog for Clifford Lord's *Unnumbered Series, 1789–1941* | https://www.loc.gov/item/43013029/ | An important **largely missing source corpus** from this project. |
| The American Presidency Project, EO statistics by president | https://www.presidency.ucsb.edu/statistics/data/executive-orders | External reference for administration-count discrepancies; not a perfect matching national census. |
| 1973 congressional study on executive orders | https://www.govinfo.gov/content/pkg/CPRT-93SPRT37998O/pdf/CPRT-93SPRT37998O.pdf | Background on historically unregistered/unnumbered directives; past estimates are not verified physical-document counts. |
| Kenneth Lowande & Michael Poznansky, *Executive Action That Lasts*, *Journal of Public Policy* 44(2), 2024 | https://doi.org/10.1017/S0143814X23000442 | Approximately 6,500-order 1937–2021 comparison focused on **formal repeal**; its reported high nonrevocation rate is **not** a survival-of-legal-effect statistic. Replication source data were not incorporated into this project's ledger. |
| 25 U.S.C. § 5102 | https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title25-section5102&num=0&edition=prelim | Trust restriction statutory complications, particularly for automatic expiration assumptions; verify actual temporal and parcel applicability. |
| 26 U.S.C. § 6103 | https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section6103&num=0&edition=prelim | Modern tax-return confidentiality; must check transition rules, historical editions and relevant saved obligations. |
| National Archives example EO 12553 table | https://www.archives.gov/federal-register/codification/executive-orders-18.html | Historical source of mass-revocation links and competing observations; inspect exact scope. |

### How to use external scholarship without importing its estimand

The **Lowande/Poznansky** study and similar scholarship can establish how a chosen historical series defines presidential repeal, quantify **formal** revocation frequency on its own period and population, and supply useful comparison and potential replication designs. They do not automatically answer whether an order is **still substantively operative**, whether a completed grant is spent under TC07, whether amendments survive through hosts, or whether the first cessation was due to time versus intervention. A statistic like "74% not formally revoked" should never be copied into this project's legal survival rate. Neither should statutory/program abolition dates be treated as exact first cessation dates for every dependent instrument.

## 13. Required product from the independent auditor

The auditing AI should **begin with a critical assessment of validity, not praise for the effort**. It is authorized to say the project is fundamentally mistaken. Where outside sources are available, it should independently search for them, treat this dossier as an attributed research claim rather than authority, and distinguish errors demonstrated by outside evidence from potential failure modes that remain untested. It should not pretend that this document includes the original archive bytes.

Its response should address all of the following, explicitly:

1. **Population/estimand:** Define what *one executive order* means for this study. Does the present 14,973 represent one and only one of those units each? Is the absence of the 1943 unnumbered volume and the 1,265 APP comparison gap fatal to a national historical total? What could count as a complete ascertainable subpopulation?
2. **Legal concept:** Formulate the strongest alternative to the TC07/TC09 framework and test spent repeals, lasting designations, incorporated host amendments, saved rights, and contingent delegations. Does the legal effect classification answer the intended public question, or a narrower artificial one?
3. **Status accuracy:** Identify at least five plausible **shared-root misclassification mechanisms** and name the highest-risk already accepted families/IDs to check first. Explain how a single legal error could invalidate many determinations despite independent model review.
4. **Causal question:** State what fraction of the project has actually determined **first cessation causes** versus only latest 2026 status. Explain what additional evidence is necessary before it can answer the time/completion versus affirmative-action question.
5. **Numerical integrity:** Assess the ledger arithmetic, the 1,943→1,950 provenance discrepancy, the different stage denominators, the Opus 49+131 ownership release, overlapping imports, 148 missing source bytes and absence of representative accuracy measures. Name any additional numerical error directly demonstrable from the text.
6. **Validity verdict:** Give a calibrated judgment for (i) historical EO census, (ii) substantive-status ontology, (iii) currently counted NOs, (iv) currently counted YESs, (v) causal mechanisms, (vi) reproducibility, and (vii) readiness to publish. Say what conclusions can already be reported and which ones would mislead readers.
7. **Concrete repair:** Recommend a **minimal, high-information falsification batch** that would test the largest share of the project's assumptions quickly, including at least one archival corpus comparison, one problematic provision-level legal chain and one random/stratified source-quality audit. State what outcomes would require a wholesale restart or a narrowed article.

The reviewer should put **fatal design flaws, if found, above improvements in efficiency**. It should not infer legal survival or non-survival from an EO's age, absence from a codification, repeal notation alone, modern office-name disappearance, expiration of an institution without considering embedded amendments, or survival of analogous policy under a legally independent statute.

## 14. Glossary for a reader with no project history

- **EO**: U.S. presidential executive order; whether a given archival unit qualifies is a census question to be decided explicitly.
- **EO identity**: one catalogued canonical bibliographic candidate, not necessarily one original signed physical document or one substantive policy.
- **Validated**: accepted into the project's stated bibliographic cohort under identity rules; **not** authenticated presidential signature or legally adjudicated status.
- **Observed**: included in the evidence inventory with sufficient source record to preserve, possibly provisional.
- **UNKNOWN / `indeterminate`**: evidence insufficient under codebook to determine a status; never synonym for NO or dormant.
- **Substantive YES**: at least one EO-attributable operative substantive scope currently supported by evidence and bounded legal change search.
- **Substantive NO**: all substantive scopes found legally spent/terminated, without thereby deciding every ancillary effect.
- **Any-effect YES**: some substantive or ancillary/residual legal effect remains attributable to the EO.
- **Original operative footprint**: every legally operative original provision, condition, designation, amendment and independent clause of the instrument, with referenced material.
- **Host / amender**: an EO changing text of an earlier EO or regulation; the amendment's continuing presence in the host can matter after the amender is revoked.
- **Savings clause**: provision preserving earlier acts, permissions, claims, or rights across changes; may be limited by person, time, circumstance or legal source.
- **TC07**: project rule treating historically executed *pure dispositive* commands as spent despite lasting consequences, subject to exceptions and sensitivity analysis.
- **First cessation**: historical first end of a substantive operative episode; can differ from the later **last-effect end** and still later formal revocation.
- **Housekeeping revocation**: an actual formal cancellation after substantive law had already ceased operating, requiring proof of chronology and absence of other current provisions.
- **Astra / Opus / Claude causal lane**: separate AI-assisted research and review assignments; they are not legal institutions or sources of binding authority.
- **Producer / reviewer**: independently instantiated AI research agents; procedural separateness is real, but not equivalent to human peer review or statistical independence.
- **Causal V1, V2, etc.**: frozen batches of newly NO status cases handed off for historical first-cause research; not proof first cause was actually determined.
- **Stage 11**: latest October 16 status integration; a structural reconciliation of separately model-reviewed Opus findings with Astra Stage 10, not a new external legal audit or a census update.
- **Progress bar**: fraction of **included project identities with model-reviewed determinate substantive status**; not survival proportion, total original EO universe completion, or first-cessation research completion.

## 15. Additional field-level audit: status arithmetic passes, but some data structures are not standardized

This dossier separately audited the *actual Python/JSON types* and leading categorical values of Stage 11's **14,973 included rows**, beyond checking YES/NO totals. Several fields contain a mix of strings, dictionaries, and booleans, which is an important caution for future statistics and causal analysis. This is a **directly observed defect in normal-form consistency**, not proof the per-order legal determinations are false.

| Current ledger field | Observed finding | Consequence for future analysis |
|---|---|---|
| `substantive_effect` and `any_operative_EO_effect` | Both are consistently one of three canonical strings on all included rows; headline totals reconcile. | These two current-status axes are machine-countable as reported, subject to the legal and census objections above. |
| `judicial_enforceability` | **14,069** exact `not_adjudicated`, another **691** `not_adjudicated_no_specific_judicial_lead_in_assigned_evidence`, plus other nonstandard descriptions. **14,956 values are strings and 17 are dictionaries.** | The work has **not** provided comprehensive judicial-status adjudication across its included corpus. The nonstandard descriptions cannot be blindly tallied as if they were a closed court-outcome enum. |
| `formal_disposition` | **13,342** exact `unresolved`, with dozens of other strings including formally revoked and textual qualifications. | One cannot infer a project-wide formal revocation frequency merely by summing a few canonical-sounding categories; metadata completeness and coding differ by stage. |
| `first_cessation_date` | **14,774** exact `unknown` across the entire validated corpus, including unresolved/surviving records; at least **2,223 of 2,322 substantive NOs** are exact `unknown`. | Historical first-cessation chronology is radically incomplete; don't count a later-EO bound as an exact first terminal date. |
| `last_effect_end_date` | **14,064** exact `unknown`, many `not_later_than_<date>` bounds and other strings; **13** values are dictionaries. | Separate exact dates, no-later-than bounds, no-earlier-than bounds, intervals, and insufficient data before plotting a terminal-date histogram. |
| `revival` | **14,446 strings and 527 dictionaries**; many strings mean merely `not_adjudicated`, while a common dictionary explicitly says a finite graph search found no revival lead. | A limited absence-of-revival-lead check must not be conflated with proven no revival. Normalize both object schema and evidence completeness. |
| `cleanup_after_cessation` | **14,968 strings, 3 booleans, 2 dictionaries**; **14,771** exact `unknown` over included identities. | Cleanup cannot be reliably analyzed by naïvely counting `true` / `false`, much less inferred from formal revocation alone. |
| `counterevidence_checked` | **14,971 dictionaries and two strings**. | Validate a stable schema before running a general-purpose automated reviewer or deriving statistical evidence coverage. |
| `evidence_grade` | **12,256** exact `identity_or_editorial_only` (largely unresolved cases), numerous different grades for adjudicated families. | The completed-status numerator and the source-identified but legally unknown denominator need separate provenance quality displays; an editorial observation grade is not an accepted legal determination. |

A source-cohort-oriented pipeline produced these heterogeneous representations as new agents appended evidence and inherited prior frozen fields. The project correctly resisted rewriting earlier work for convenience; nevertheless, *immutability cannot substitute for schema clarity*. A sound publication data model should expose a **new normalized projection** with an explicit closed enumeration for causal status, date type, proof grade, judicial disposition, legal-effect attribution, and unknown-reason, while preserving each original raw value and its frozen file hash. Counts in the new projection would have to reconcile back to originals with named lossless transformations, not silently rewrite stage history.

The all-history goal especially requires distinguishing `cause_research_not_started`, `investigated_but_unresolved`, `first_cessation_proved`, and `only_latest_terminal_bound_known`. At present a single `unknown` often collapses those materially different evidentiary states. An auditor should ask whether a promised "automated legal status pipeline" built against nonstandard values could misclassify or drop records when run at scale.

---

### Final orientation

The project has built a substantial **source-preserving, auditable research infrastructure** and has completed **2,515 model-reviewed determinate present-substantive-status records within a 14,973-entry bibliography**. The enterprise has also exposed genuine historical legal complexity and corrected meaningful errors. **None of this establishes that there were 14,973 presidential executive orders, that the counted order units are all comparable, or that the original time-versus-intervention causal question has been answered.** The highest-value independent contribution is to test those foundations and, if necessary, recommend a narrower, methodologically legitimate study rather than polishing an invalid all-history headline.

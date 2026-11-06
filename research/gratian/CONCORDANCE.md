# Gratian concordance: where each of tonight's products goes

Named for Gratian, whose *Concordance of Discordant Canons* (c. 1140) reconciled scattered and conflicting sources into
one usable body of law. This page records, for every product of the night wave of 2026-11-05, the files it writes,
the readiness-tracker step or claim-kit route that should read them, whether anything reads them today (with the line),
and the codebook grade that governs them. The row-per-product table with exact paths and line numbers is
[`CONCORDANCE.csv`](CONCORDANCE.csv). Measured effects come from the ablation in [`IMPACT.md`](IMPACT.md).

## Summary

Of twelve products, eight are wired, two are partly wired and two are orphaned. Niebuhr's results were connected on
this branch. Mabillon's held printings and Selden's acting-text jobs are partly wired: their routes exist, but their
outputs are not yet on `main`. Pothier has no leads yet. The Mabillon scan and NARA inventories are unread by design,
because they are location leads for a person. Separately, this branch gives new sources a path into undecided
dossiers in the claim kit. Nothing tonight moves an
order to ready for human review in the tracker, because every product supplies sources or leads, and ready also
needs a reviewed claim that passes the claim gate and claim-checker. The products move orders toward ready. Most of
the movement is in the claim-ready group (orders whose text and counterevidence steps are done, so only a drafted
claim stands between them and review), and in the claim kit's reach into undecided orders. Human certification stays
at 0.

## What each product feeds

**Ptolemy** keeps the bytes of 1,390 cited sources the project held only as a hash. The claim-checker already reads
every `jobs/*/output/SOURCES.jsonl` with a `cache_path` (`jobs/claim-checker/sources.py:246`), so Ptolemy is wired
without a code change. The last checker run finished at 22:20 UTC on 2026-11-05, five and a half hours before
Ptolemy's output reached `main`, so its effect appears at the next daily run. Of the 7 custody-only rows in filed
claims, 4 cite bytes Ptolemy now holds. One of those orders, EO 10926, is one step from ready, and that step should
pass on the rerun. The tracker's Opus-media step credits a re-fetch only from source-ladder (`tracker.py:628`). A
variant that also credits Ptolemy moves no order, so this branch does not propose that change.

**Mabillon** proved 1,771 official printings from held passages and left 244 more as leads that need a page check.
Its fragments use Tischendorf's grade, `machine_read_government_printed_copy` with `acceptable_as_original: false`.
Once merged, the claim kit reads them automatically (`inputs.py:503`). The tracker reads them only after PR #164
adds the file to its official-printing list. Under the tracker's rule, a find that is not flagged for a page check
satisfies the text step. In the claim kit the same grade is a provisional working text (`working_text.py:22`), so a
claim built on it must disclose it. The two tools label one source differently. This is the coordinator's standing
answer to Mabillon Q1, and this branch does not change it. With #164, 17 decided orders lose a provisional working
text step, because a Mabillon lead that awaits a page check reopens it (`tracker.py:135` and `547`). Tischendorf does
the same to 5 orders. These numbers belong in #164's description (see `QUESTIONS.md`, Q2).

**Selden** publishes leads tonight: an acting-instrument census, the per-order needs table, the list of 1,386 acting
executive orders whose text Mabillon should find, and a pre-registered proof sample. Its three fetch jobs write
`FRAGMENTS.jsonl` records of kind `later_event_candidates` with exact quote spans, plus `SOURCES.jsonl`. The claim kit
reads those records automatically as acting provisions (`inputs.py:31` and `503`), for decided and undecided orders
alike. later-events scanned only fr-originals and app-transcriptions texts for revocation sentences. On this branch
its `job.py` adds `selden-fr-acting` (`jobs/later-events/text_jobs.py`) without touching `later_events.py`, whose
hash the claim kit pins. Status histories and the tracker's counterevidence step read later-events, so they will see
those texts too. No Selden job output is committed yet, so the route is ready but nothing flows through it.

**Pothier** has written member tables for its 11 workstreams. Its `LEADS.jsonl` and `SOURCES.jsonl` are still empty.
Leads are not wired, by design: each order needs its own decision and blind review. Once Pothier holds class-wide law,
the kit and checker pick up `SOURCES.jsonl` automatically. A statute's ending excerpt that should serve as a NO basis
must arrive as a `later_event_candidates` fragment, which the kit compiles into an `ACT:` record. The new supplement
route carries corroborating excerpts and cannot supply that basis (see below).

**Niebuhr** identified 258 of Clark's 301 unknowns, mostly from secondary sources, and no tool read the results. The
new job `jobs/gratian-niebuhr-leads` types them as `secondary_identification_lead` dates. `jobs/_lib/eo_identity.py`
`load_dates()` reads those dates after every other source, so Lewis can route by date: 56 numbered orders gain a date
they lacked, or a full date for a bare year. Ten dated references resolved to known orders are listed for a person to
check. The 30-order admission queue stays with the owner (Kean A-20261105-niebuhr-admit).

**claim-drafts** (PR #160) now drafts 10,628 undecided orders. **status-history**'s empty-history packets (owner ruling
of 2026-11-05) give 5,918 undecided orders with compiled overlay inputs a startable status route. The kit reads both
(`inputs.py:533`; `status_overlay.py:298` and `755`). **Clark's web stage** hands 55 orders to Lewis
(`lewis.py:54`); its `SOURCES.jsonl` records log search attempts, name no order and add nothing to dossiers.
**Tischendorf** and **Lachmann** were already registered with the tracker.

## The undecided-dossier gap, closed

`jobs/claim-kit/source_supplement.py` refused every undecided dossier, so a new held source could reach only decided
orders, and PRs #160 and #161 had sent all undecided orders down the status-overlay route. Now, when the parent packet
holds frozen overlay evidence for an undecided member, the supplement seals a new copy of that evidence. In the copy,
the base dossier carries the excerpt and the excerpt's files join the source pins. `batch.prepare` accepts the
pre-frozen evidence, so the status decision sheet, the independent review and owner adoption all work on the exact
dossier the producer reads. No gate is relaxed:

- A supplement excerpt is citable held evidence, but a NO still needs an `ACT:`, `TERM:` or `ACTOR_TEXT:` basis, and
  a YES still needs a `CURRENT:` basis.
- The reviewer must check every excerpt the decision cites.
- Changed parent evidence, a tampered excerpt, or evidence that does not descend from its parent is refused.

`batch.py`'s codec pin changes, so packets prepared before this commit must be prepared again before `apply`. Tests:
`jobs/claim-kit/test_source_supplement_undecided.py`.

## What the tracker ignores, and why nothing more is registered here

Only two producers of `original_representation` fragments are not on the tracker's lists. The first is
`mabillon-held-printings`, which is PR #164's change. The second is `app-transcriptions`, whose 9,386 records repeat
the archive-lane APP texts the tracker already reads from `app-executive-orders/output/MIRROR_FRAGMENTS.jsonl`. No
other output belongs in a tracker step under the codebook: Ptolemy works through the checker, Selden through the kit
and later-events, and Niebuhr, Pothier and Clark are leads. So this branch makes no change to `tracker.py`, and
there is no count-changing pull request from Gratian. PR #164 remains Mabillon's.

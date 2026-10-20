# Mountweazel

Measures whether a reviewer catches defects that are really there. Named for the invented
fountain designer Lillian Virginia Mountweazel, planted in the 1975 *New Columbia Encyclopedia* to
catch copiers. Design: `research/plans/MOUNTWEAZEL_DESIGN.md`.

Why: Bowditch Y1 passed with 0 of 15 reviewer disagreements, but the reviewer was the same model
family as the producer. 0% disagreement says nothing until we know the reviewer's catch rate. This
tool mixes real, already-upheld items with items carrying one known defect and scores the reviewer.
It changes no claim, status, codebook, ledger or human review, and certified stays 0.

Standard library only. Run everything with `python3 -I`.

## Commands

```
python3 -I jobs/mountweazel/mountweazel.py pool
python3 -I jobs/mountweazel/mountweazel.py seed  --track C --batch-id MW-C1 --seed <text> [--n 24] [--exclude-orders EO:1,EO:2]
python3 -I jobs/mountweazel/mountweazel.py score --key <KEY.sealed.json> --verdicts <file> [--adjudication f] [--voids f] [--weights f]
        [--relabel f] [--tells f] [--production 0/15] [--out f]
python3 -I jobs/mountweazel/mountweazel.py check [--write-status]
python3 -I jobs/mountweazel/test_mountweazel.py
```

- **pool** counts, per defect type, how many real items a defect can be planted on.
- **seed** builds `<out>/<batch>/batch/` (blinded items plus `MANIFEST.json`), `<out>/<batch>/key/KEY.sealed.json`
  (the answer key, mode 0600, with a seal hash) and flagged fixtures in `jobs/mountweazel/fixtures/<batch>/`.
  Same `--seed` gives the same bytes. Default `--out` is the session scratchpad; **seed refuses any output inside
  the repository**. Seeded share is 20 to 30 percent, derived from the seed, and is not stated in the batch.
  Each order appears at most once per batch; pass the other batch's orders to `--exclude-orders` so an order is
  real in one batch and a plant in another.
- **score** reads reviewer verdicts (a JSON list or JSONL of `item_id`, `decision`, `locus`, `reason`,
  `confidence`; decision is `accept`, `reject`, `block_justified` or `block_not_justified`). It reports, per
  defect type and pooled: strict catch (a flag that names the changed field, value or actor), lenient catch
  (any flag; strict needs a specific value, actor, clause path or cut-off word, never a bare field name like
  `first_end`), Wilson and Clopper-Pearson 95% intervals, and `indicative_only` when n is under 5. A flag on a real
  item is not a false alarm until adjudicated (`--adjudication`: `{"item": "false_alarm" | "contestable" |
  "confirmed_real_defect"}`); the false-alarm rate is given as a lower and an upper bound. `--voids` removes plants
  a reviewer convincingly argued were correct. `--relabel` records the adjudicated true defect type when an
  operator's label is wrong; `--tells` lists plants whose packet carried a seeding artifact and adds a tell-free
  catch rate; accepted plants whose reason names the defect are listed as `noticed_but_accepted`.
  `--production k/n` turns a production review result (Bowditch Y1: 0/15) into an upper 95% bound on its defect
  rate, at the point catch rate and at its lower bound. Verdict rows may use `verdict` for `decision`. It refuses
  an edited key.
- **check** proves no seeded item exists anywhere in the repository except `.git` and the fixture folder. It
  looks for the SEEDED markers and batch item ids (not in this tool's own files, the design doc or `HANDOFF/`),
  exact copies of any plant (flagged or de-flagged), and `leak_needles`: JSON-quoted windows of plant text that
  occur nowhere in the real base (so real text a plant shares, such as a D3 quote prefix, is never a hit); it also fails if a fixture is not rejected by `claim_gate.validate_claim`, or if
  `jobs/mountweazel/output` holds anything but `STATUS.json` and `SENSITIVITY.json`, or if `jobs/mountweazel/data`
  exists. Exit code 1 on any problem. The one allowed mention of the markers is the design document.

## The flag the claim checker rejects

A fixture carries `SEEDED: true`, an `instrument_id` starting `SEEDED:`, and a payload whose schema is
`SEEDED-...`. The production gate (`research/stage19/code/claim_gate.py`) rejects both the schema and the id.
The tests also prove the opposite: the de-flagged copy of each plant passes the gate, so plants test judgment, not
mechanics. The blinded copy a reviewer sees is the de-flagged one and lives outside the repository.

## Defect types

Operators work by one documented mutation of a real item and record the refuting quote.

| Track C (claims) | Mutation |
|---|---|
| D1 | deadline copied in as the end (needs a `not_later_than`; none in today's pool) |
| D2 | one-time command, end moved to a later revocation |
| D3 | end quote cut off before the operative verb (still verbatim) |
| D4 | the earliest partial end applied to the last clause |
| D5 | own term or earlier amendment replaced by a later revocation |
| D6 | a later event removed that the packet still names |
| D7 | end date replaced by another date the clause's own text states |
| D8 | operative text swapped for a neighbouring order on the same Federal Register page |
| D9 | a coverage count inflated in one place while another still shows the true count |

Track S (Bowditch-style status proposals): D10 retarget the cited actor to a non-revoking actor in the packet;
D13 turn an accepted proposal into a block that says a record is missing which the packet holds.
D11 and D12 are in the taxonomy but have no operator yet.

## Limits, stated plainly

- Trial MW-C1 (2026-10-20) found three seeding faults, now fixed for new batches: global date/actor swaps rewrote
  rationale sentences about sibling clauses (a tell; plants whose old end is shared with another clause or event
  are now skipped), the one-time classifier took an "annual report" for a one-time duty (D2 now excludes recurring
  duties), and D9's "true count still visible" test matched "49 Stat." (now needs the same count and unit). After
  the fixes the real pool supports D3 51, D6 36, D7 11, D5 7, D8 5, D4 1 bases; D1, D2 and D9 have none.
- Plant wording is mechanical (dates and actor numbers are swapped consistently in the rationale). The design calls
  for a separate seeder agent to polish rationales and two checkers to confirm each plant; that is not built. Run a
  leak test (a no-access discriminator) before trusting a batch.
- Track S packets carry the producer decision and held history events only, not the held source texts. Add the
  texts to the practice packet before using Track S results.
- "Upheld" for Track C means: in `research/readiness/claims/` and passes `validate_claim`. It is not a human
  certification.
- Taxonomy counts and the Junto/Llull interface (`output/SENSITIVITY.json`) are described in the design, not built.
- There is no `job.py` on purpose, so the GitHub runner never picks this up. It writes no CSV, no `SUMMARY.json`
  and no `data/`, because other jobs read those paths.

## Controlled reasoning pairs

`python3 -I jobs/mountweazel/mountweazel.py pairs prepare --out <new external directory>`
creates six pairs (twelve hypothetical items): layout, deadline, demonstrated
performance, recurring duties, omitted earlier events and savings exceptions.
The packet stipulates fictional rules so expected evidence-gap behavior decides
no contested law. `pairs score --key KEY.json --batch batch.json --verdicts FILE
--out EXTERNAL_FILE` validates the sealed key, item coverage, evidence labels and
substantive reasons. Generated items, answer keys and item-level results stay
outside the repository and are rejected by the production claim gate. Read the
limitations: **reviewer blinding is not technically enforced** by file permissions
under the same account. A harness/key roundtrip is not a reviewer sensitivity test.

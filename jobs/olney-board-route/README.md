# Olney: the scripted route for the emergency-board orders

Named for Richard Olney, the Attorney General whose 1894 Pullman injunction made railway labor disputes a federal
matter. The Erdman Act of 1898 followed, and later the Railway Labor Act, whose section 10 boards these orders create.

Olney applies owner rule D-20261108-board-rule (`research/readiness/owner_rulings/2026-11-08-haloander-decisions.md`
item 2; working analysis in `research/excavator/claude-haloander-2026-11-07/tools/prompts/board_rule.txt`). It
spends no model tokens and applies the rule only to orders it fits directly. Every other order goes to an
exceptions list with its reasons.

```bash
python3 -I jobs/olney-board-route/olney.py select            # output/SELECTION.json
python3 -I jobs/olney-board-route/olney.py run --batch s0 --n 8
python3 -I jobs/olney-board-route/olney.py run --batch s1 --n 20
python3 -I jobs/olney-board-route/olney.py report            # output/RESULT.json, output/RESULT.md
python3 -I jobs/olney-board-route/test_olney.py
```

## Universe and selection

The universe is the 117 orders in Lind's `research/lind/board-candidates-2026-11-13/CANDIDATES.json` that are
also in `jobs/bentham/output/strata/production.one_step_away.txt`. An order is selected only if all of these
checks pass:

- **Tracker:** the filed claim's only open step is `FIRST_END_UNRESOLVED`. The filed claim is the one Lind read,
  and no later-dated claim file names the order.
- **No exception flag:** the order creates a board, and the report date is `INVENTORY_AGREES`. No follow-on order
  shares the report. The NMB lists no congressional action, supplement, second board or extra documents. The filed
  claim has at most two clauses, and nobody else holds a reservation on the order.
- **Bytes:** the report's raw bytes are committed by Ptolemy (`jobs/ptolemy-custody/output/raw/`), and source-ladder
  holds its text.
- **Letter date:** the letter of transmittal's own date line reads cleanly as the corroborated date.
  - Lind's `OBSERVED_NO_HEADING` readings in this universe are the cover's date line, not the letter's. Olney looks
    for the letter's date between the cover and the address to the President instead.
  - A garbled letter date is an exception, even when the cover is clean.
- **Report span:** the span runs from the cover to the sentence submitting the report, and contains submission
  wording.
- **Identity:** the span names the order by number, or by an appointment date equal to the order's signing date. No
  other order number or board number appears in it.
- **Clauses:** the kit dossier has one clause. Its text has exactly one "hereby create" sentence and at most one
  no-change sentence, and that sentence ("thirty days after the board has made its report", "no change", "except
  by agreement") ends the clause. Only page furniture may follow it, meaning text with no "shall", "hereby" or
  similar verb. No wording suggests another command, such as compensation, Defense Production Act section 502, an
  amendment, an extension or a reconvening.

## Per batch (`research/excavator/claude-bracton-2026-11-25/olney/<batch>/`)

1. **Prepare:** `packet/` is made by `kit.py prepare --agent claude --action production.one_step_away
   --replacement-proposal`.
2. **Supplement:** `SUPPLEMENT_SOURCES.json` declares the report span. It is declared twice: once as the board end
   (actor `Emergency Board No. N`) and once as the source dating the standstill (actor the order). `local_path` is
   the Ptolemy PDF. `source_supplement.py prepare` writes `supplemented/`.
3. **Write sheets:** `decisions.csv` and `clauses.csv` are written in `supplemented/`.
   - **Board clause:** it covers the clause text up to the no-change sentence. It ends `completion_of_task` on the
     letter date D.
   - **No-change clause:** it ends `expiry_by_own_terms` on D + 30 days, the inclusive reading. The reason also
     states the exclusive reading, D + 29 days.
   - **Cleanup revocation:** the filed claim's cleanup revocation (EO 12553 or EO 12379) is recorded on every
     clause as a later event. It stays the formal disposition.
   - **Values carried from the filed claim:** savings, the later-source search (matched by repository),
     `original_pages_confirmed`, and the original's identity.
   - **Blocked orders:** an order that is dispatch-blocked, or whose dossier changed, is written `blocked` with the
     reason.
4. **Apply and check:** `kit.py apply` writes `supplemented/applied-v1`, then `kit.py batch-check` runs. The actual
   checker result is recorded per order in `OLNEY_BATCH.json`.

## What the script asserts and what it does not

- **Asserted from a filed, reviewed claim:** `approved`, `original_confirmed` and `inventory_confirmed` are set by
  machine application of the owner rule. The original confirmation is carried from a claim that cites the same
  original printing.
- **Not a producer's judgment:** none of these values is. Every claim is a replacement proposal and needs blind
  review and owner adoption.
- **Parties:** board, order, date and submission wording are checked mechanically. The parties are not compared.
- **Completeness:** the selection checks are documented, but an exception they cannot see is not ruled out. One
  example is an unlisted reconvening.

## Known gap and proposed patch

The kit's supplement route needs the raw bytes at a repository path (`local_path`). A report held only in the
Pergamon store cannot be added. This affects 41 orders, and for 3 of them (EO 10770, 11343, 11745) it is the only
exception.

The kit's selected-source check (`dispatch.check_selected`) also reads custody with no cache folder, so a
Pergamon-only copy grades `custody_record_only` there. Batch-check's checker run already fetches and re-hashes such
copies.

`proposed/pergamon_supplement.patch` (not applied) fixes both:

- **`source_supplement.py`:** accepts `local_path: null` when a `jobs/*/output/SOURCES.jsonl` record gives a
  Pergamon locator for the same SHA-256. It fetches the bytes and re-hashes them.
- **`dispatch.source_context`:** gets the packet's gitignored `.validation-cache`.

The patched `derive()` was tested on EO 10770's span.

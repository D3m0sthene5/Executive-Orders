# Olney: the scripted route for the emergency-board orders

Named for Richard Olney, the Attorney General whose 1894 Pullman injunction made railway labor disputes a federal
matter. The Erdman Act of 1898 followed, and later the Railway Labor Act, whose section 10 boards these orders create.

Olney applies owner rule D-20261108-board-rule (`research/readiness/owner_rulings/2026-11-08-haloander-decisions.md`
item 2; working analysis in `research/excavator/claude-haloander-2026-11-07/tools/prompts/board_rule.txt`). It
spends no model tokens and applies the rule only to orders it fits directly. Every other order goes to an
exceptions list with its reasons.

```bash
export OLNEY_CACHE_DIR=~/.cache/eo-olney                        # pdftotext and Pergamon copies, outside the repo
python3 -I jobs/olney-board-route/olney.py select              # output/SELECTION.json (run v3)
python3 -I jobs/olney-board-route/olney.py run --batch s5 --n 20
OLNEY_ASSUME_PERGAMON_KIT=1 python3 -I jobs/olney-board-route/olney.py select --out /tmp/preview.json
python3 -I jobs/olney-board-route/olney.py report --preview /tmp/preview.json   # output/RESULT.json, RESULT.md
python3 -I jobs/olney-board-route/test_olney.py
```

Run v1 (batches s0, s1) is kept as it was reviewed. Run v2 (batches s2-s4) skips the 8 orders both blind arms
upheld in v1 (EO 10032, 10056, 10071, 10112, 10140, 10757, 10872, 11663) and reruns the rest, EO 10944 included.
Run v3 (batch s5 on) also skips EO 10105 and 9702, upheld by both arms in v2, and applies the fixes below for the
defects the o2 and o3 blind reviews found in Olney's own screens and generated text.

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
  - **Cover date (owner decision D-20261125-board-cover-date):** when the letter's date line is unreadable or not
    found, and the cover's date line reads cleanly (the whole line) as the corroborated date, the board clause
    ends on the cover date. The claim's reasons quote the unreadable line, or say none was found, and disclose
    the rule. A letter date line that reads cleanly as another date is a conflict and stays an exception, and an
    uncorroborated report date never uses the cover.
- **Letter of transmittal on the cover route (run v3, o2/o3 review):** Olney reads the held letter itself: its
  address to the President (OCR-damaged forms such as "THE IORESIDENT" included) and the last line before it that
  is not page furniture. The claim then says which of three things is true of the quoted span: the date line is
  there but does not read cleanly (quoted as held), the letter has no date line before its address, or no letter
  was found after the cover. A legible year that differs from the cover's is disclosed; a legible month or day that
  differs is a conflict and an exception. A held letter without a submission sentence, an address Olney cannot
  place, a "no date line" statement contradicted by another date in the span, and a reading that disagrees with
  Lind's are exceptions.
- **Report span:** the span runs from the cover to the sentence submitting the report (periods of abbreviations
  such as "No." or "Co." do not end it). On the cover route with no legible letter, it runs through the cover's
  date line and board-number line.
- **Report-time extensions (batch o1 review):** pdftotext reads the whole report PDF, and Olney screens every page
  for wording that extends the board's time to report.
  - An extension whose passage is on the held pages, and which prints the President's approval date and the new
    deadline, is recorded as a later event of the board clause. The event is dated by the approval, and its source
    is the quoted held passage, declared as a supplement excerpt. A date printed without its year takes the only
    year inside the order's window, and the claim says so.
  - In run v2, a passage that printed the new deadline and no other date was recorded as a claim source note saying
    that no approval date is printed. Run v3 makes such an order an exception (see below).
  - Several extensions, a passage off the held pages, or an unparsed or ambiguous date make the order an
    exception.
  - Modal wording ("the time can be extended") in a report made within the order's own thirty days is not an
    extension.
  - **Run v3 screen (o2/o3 review).** The v2 phrase screen missed EO 10969 ("extended to December 10, 1961 the date
    for the filing"), EO 10147 ("an extension of 30 days for the rendition of said report") and EO 11445 ("e~tend the
    time", "this extension was approved"), because it needed "time", "date" or "deadline" within two words of an
    undamaged "extend". The screen now also counts any form of "extend" or "extension" (a damaged x included), and
    more or postponed time, whose own sentence names the report, its filing or its time (a noun may name it in the
    next or previous sentence). Adjectival uses ("after extended hearings") and statute names are not counted. The
    v2 screen is kept, so the v3 screen only widens it.
  - **Run v3 dating.** An extension printed without the President's approval date, or without an absolute new
    deadline, makes the order an exception; the v2 route that wrote an undated source note is closed. A claim never
    says that no extension exists: it states what the screen covered and what it found.
- **Procedural events (run v3, o2 review of EO 10760):** pdftotext pages and held pages are screened for a stipulation
  about the proceedings, a reconstituted board or changed member, a reconvening, and a report period restarted from a
  later date than the order's signing. The proceedings must be named in the sentence or the two before it. Any such
  wording makes the order an exception, except a stipulation inside the held passage of a dated extension that Olney
  records, which is that extension's own record.
- **Pergamon-only reports:** when the checkout's claim kit carries the Pergamon supplement route
  (`source_supplement.held_bytes`), a report held only in the Pergamon store is fetched and re-hashed, then
  declared with `local_path: null`. Without that route the order is the exception `report_bytes_pergamon_only_kit_gap`.
- **Identity:** the span names the order by number, or by an appointment date equal to the order's signing date. No
  other order number or board number appears in it.
- **Clauses:** the kit dossier has one clause. Its text has exactly one "hereby create" sentence and at most one
  no-change sentence, and that sentence ("thirty days after the board has made its report", "no change", "except
  by agreement") ends the clause. One OCR-damaged letter in "the", "board", "has" or "change" of that fixed
  wording is tolerated, and the claim quotes the held text as it stands. Only page furniture may follow it, meaning text with no "shall", "hereby" or
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
   - **Values carried from the filed claim:** the savings state and source, the later-source search (matched by
     repository), `original_pages_confirmed`, and the original's identity.
   - **Savings reason (run v3):** generated, never carried. Olney reads the revoking order's held text (the filed
     claim's savings source must be that text) from its heading to its FR document line for savings words; a hit
     outside its table of revoked orders makes the order an exception. The reason states this claim's own clause
     ends and no count taken from another claim.
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

## Pergamon route in the claim kit

The kit's supplement route used to need the raw bytes at a repository path (`local_path`), so a report held only
in the Pergamon store could not be added. Branch `claude/olney-v2` changes the kit:

- `source_supplement.held_bytes` accepts `local_path: null` when a `jobs/*/output/SOURCES.jsonl` record gives a
  Pergamon locator for the same SHA-256. It fetches the bytes through `pergamon_store.Store.get_verified` and
  re-hashes them. The copy is kept under the kit cache and re-hashed on every packet load.
- `dispatch.check_selected` reads custody with the packet's `.validation-cache`, as batch-check's checker run
  does.

The text hash is checked exactly as before. Packets pin the kit code of the checkout that prepares them, so
Pergamon-only orders run only after this change is merged. A preview (`OLNEY_ASSUME_PERGAMON_KIT=1 select
--out`) shows which of them would then be selected.

## Mechanical trial of the extension route

`research/excavator/claude-bracton-2026-11-25/olney/x1-extension-trial` (receipt marked `trial`,
`NOT_FOR_REVIEW.txt`) applies the extension route to two exception orders: EO 10010, with a dated later event,
and EO 10372, with a source note. Both pass apply and the claim checker. These claims are not for review or
filing. The source-note route that EO 10372 used was closed in run v3.

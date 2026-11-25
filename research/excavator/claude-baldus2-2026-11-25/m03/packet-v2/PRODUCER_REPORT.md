# Producer report, packet m03/packet-v2 (agent baldus)

Start 2026-11-25T19:51:58Z. End 2026-11-25T20:00Z (stopped at the first refusal).

## Outcome

No claim was submitted and nothing was applied. `source_supplement.py prepare` (step 2 of the coordinator addendum) refused the packet:

`ValueError: changed prior research; prepare a new version` (raised from `batch.load_packet` at batch.py line 328).

Per the brief I stopped rather than work around it. No sheet was edited, no applied-vN, packet-v2-sup, batch-check or Geddes lint exists. decisions.csv, clauses.csv and RATIONALES.json are unchanged (all seven rows still `unresolved`). The refusal blocks every order, because the report-span evidence record can only be created in the supplemented packet.

Diagnosis, read-only: `prior_research.collect(repo, dossiers, exclude=packet-v2)` was compared with the packet's frozen `prior_research`. The differences lie outside my files:
- `orders/EO:11040/versions`: the location list of the current canonical claim changed (the file hash of an earlier claim file it appears in differs from the frozen one).
- two pinned files under `research/excavator/claude-baldus-2026-11-25/y15/packet-v3/complete-v1/receipts/...MANSFIELD_AUDIT.json` and `.../y16/...` exist now and were absent at preparation.

The coordinator needs to re-prepare this packet (or confirm the pins) before the seven orders can be produced. `DECL.json` is written and ready at `research/excavator/claude-baldus2-2026-11-25/m03/DECL.json` (14 entries, two per order); it did not trigger the refusal on its own as far as the diff shows.

## What the research established (for the retry; not filed)

For each order the held NMB report bytes are present at the cited hash (checked with sha256sum; the page count and text layer were read). The letter-of-transmittal date line was checked against the held PDF page image (pdftoppm at 260 dpi) and reads cleanly and agrees with the cover date and with the NMB inventory closing date.

| Order | Board | Report date (letter = cover) | No-change period end, inclusive (exclusive) |
|---|---|---|---|
| EO 10904 | No. 134 | 1961-03-06 | 1961-04-05 (04-04) |
| EO 10919 | No. 135 | 1961-06-20 | 1961-07-20 (07-19) |
| EO 11006 | No. 144 | 1962-05-01 | 1962-05-31 (05-30) |
| EO 11008 | No. 145 | 1962-05-03 | 1962-06-02 (06-01) |
| EO 11011 | No. 146 | 1962-05-01 | 1962-05-31 (05-30) |
| EO 11027 | No. 148 | 1962-08-30 | 1962-09-29 (09-28) |
| EO 11040 | No. 150 | 1963-03-04 | 1963-04-03 (04-02) |

Identity (number, creation date, parties) matches in all seven. The text layer of five letter date lines is damaged (10919, 11006, 11011, 11027, 11040); the cover date line reads cleanly in the text layer, so D-20261125-board-cover-date applies and the page-image reading corroborates it. Planned structure: two clauses per order (board: completion_of_task on the report date; no-change sentence: expiry by own terms at report date plus 30 days), whole-order end = the later; EO 12553 (1986-02-25) as formal disposition and later event on every clause; savings: none after reading EO 12553 (all seven numbers sit in its table of revoked orders).

Points a reviewer should see, found in the held reports:
- Report-time extensions are recorded but not dated in the held text: EO 10904 (two stipulations, the last to 1961-03-11; President approved), EO 11006 (two extensions, last to 1962-05-01), EO 11011 (to 1962-05-01), EO 11027 (to 1962-08-31), EO 11040 (several, last to 1963-03-05). They move only the reporting deadline. EO 11008's extension is dated on report PDF page 33 (NMB letter, President's approval line reading "MAR. 30, 1962", new limit 1962-05-03), but that page is outside the held text layer (pages 1-8), so it cannot be cited as an excerpt. EO 10919's extension is EO 10926 (1961-03-18, held text), a recorded later event of the board clause. Olney (jobs/olney-board-route) treats an undated extension as an exception; I judged it not to change either end date and planned to disclose it in the reasons by paraphrase, not as a dated later event. That is a judgment call for the reviewer.
- EO 11040: the report cover prints "EXECUTIVE ORDER 11041" (a typographical error: EO 11041 is the Peace Corps order of the same Federal Register day); the letter names EO 11040, the 1962-08-06 date, the Belt Railway Company of Chicago and the Brotherhood of Locomotive Engineers. The board was appointed 1962-10-06, and the report states the parties settled by written agreement on 1963-02-16; the no-change sentence permits changes by agreement and nothing held shows it ended earlier, so the own-terms end stands.
- No supplemental report, retained jurisdiction or reconvening after the report was found in a pdftotext scan of all seven held PDFs (the 10904 reconvening of 1961-02-13 is a recess within the hearings).

## Assessment

ASSESSMENT.jsonl has seven rows (outcome `blocked`, blocker = the tool refusal; the readings are operative force no, formal disposition EO 12553).

## What took the time (one line each)

All seven: reading the brief, rulings and Olney's route (about half the time); the letter date page-image checks and the report scan for extensions; the refusal ended the run.

## Files opened beyond the views

- LOOKUPS.md of the packet (as instructed); `packet-v2/views/*.json` (parts, by script).
- `jobs/olney-board-route/README.md`, `olney.py` (sections), `output/SELECTION.json` (my seven entries only).
- `research/lind/board-candidates-2026-11-13/CANDIDATES.json` (my seven entries only).
- `research/excavator/claude-haloander-2026-11-07/tools/prompts/board_rule.txt` and ruling `2026-11-08-haloander-decisions.md` item 2.
- `jobs/fr-originals/data/full_run/texts/EO_10926.txt`, `EO_12553.txt`, `EO_11041.txt` (head); the seven held report PDFs and source-ladder texts.
- PACKET.json: loaded once through `batch.load_packet(..., check_sources=False)` for dossier evidence ids and for the read-only prior-research comparison.
- Not opened: any other packet folder (a folder `m03/packet` exists beside mine and was left alone).

## Tool defects

- `source_supplement.py prepare` refuses a packet when unrelated waves add files that change its prior-research fingerprint; the freshness check cannot be satisfied by the producer.
- pdftotext text layers of the held reports damage several letter date lines; the page images read cleanly.

# F3 report: wiring check of five 2026-10-21 owner rulings

Scope: read-only search of /home/user/Executive-Orders (nothing modified). Deliverable: `RULINGS_WIRING.csv` (5 rows).
Rule texts: `jobs/kean/register/decisions.jsonl` (all five at rev 0, wiring `not_verified`) and `research/readiness/owner_rulings/2026-10-21-*.md`.

## Result

| decision | status |
|---|---|
| D-20261021-report-deadline | **partly** |
| D-20261021-strike-and-insert | **not** |
| D-20261021-unnamed-instruments | **partly** |
| D-20261021-eo-10449 | **not** |
| D-20261021-until-dates | **not** |

Counts: wired 0, partly 2, not 3.

## Evidence in brief

- report-deadline: the negative half is enforced in code. `assemble.py:554-555` rejects `report_deadline` as an end (`clause_N_report_deadline_is_not_end`; test `test_assemble.py:366`). `status_overlay.py:678-679` rejects it as a status basis. `excavate.py:318,342` never gives it an end candidate. `AGENT_PROTOCOL.md:47` tells producers. `batch.py:202-203` adds a task to determine the actual event.
  - Not found: any instruction or check to record the report date or standstill end as a `later_event`, or the "functionally spent on <date>" note. Zero hits for that phrase in all searched code. No check that the ending instrument is an express revocation or EO 12553.
  - `evidence_preflight.py:291-299` cites the ruling file only as an `owner_rule` on a warning that a conditional "terminate after report" clause is NOT a mere deadline. It is a scope fence, not an implementation.
- unnamed-instruments: only "not naming the target means no end" is carried, and only for parent-as-amended, cited-by-number and name-match leads (`excavate.py:556-557`, `build.py:409`, `AGENT_PROTOCOL.md:141-147`). The disclosed earlier-candidate-end requirement has no field or check. `BATCH.md:176-180` `source_notes` is a generic place a producer may put it.
- strike-and-insert: no code or instruction. Adjacent only: `claim_gate.py:83-87` and `checker.py:89` validate the `later_events` structure, with no before/after text and no amendment-versus-end logic. `excavate.py:267` merely recognises amending verbs.
- eo-10449: no mention in any tool, instruction or test fixture except `jobs/ofr-codification-1989/test_codification.py` (a fixture hit). It inherits only the generic report-deadline guard.
- until-dates: no inclusive/exclusive disclosure anywhere. The only exclusive-end code is `provision_history.py` (`end_exclusive`, `known_sunset_end_exclusive`), a separate data model. Claim-kit treats "further exempted" citing orders as leads, never events (`AGENT_PROTOCOL.md:141-147`; `excavate.py:585-587`). That is the opposite of "each extension is its own later_event".

## Later decisions
D-20261028-evidence-decides (rev 2, `wired`, via TR-CS-WAIVER) does not supersede or contradict any of the five. It generalises two of them: "separate an exhausted command from surviving consequences" (report-deadline, strike-and-insert) and "Disclosure keeps a gap visible but never fills it" (unnamed-instruments, until-dates). Its "do not ask the owner to choose method answers" means these five stand as agent-applied method rules. I found no other later ruling (searched the decisions file only for D-20261028-evidence-decides; I did not review the later `owner_rulings/2026-10-31`, `2026-11-0x` files, which could bear on these).

## Exceptions / limits
- "not" means no hit in the listed files; I did not read every file in `jobs/*`. Searched: `jobs/claim-kit/*.py,*.md`, `jobs/claim-checker/*.py`, `jobs/readiness-tracker/tracker.py`, `research/stage19/code/claim_gate.py`, `jobs/claim-drafts/*`, `jobs/norton`, `jobs/ofr-codification-1989`, type-rules, plus a repo-wide grep (excluding `output/`, `_attempts`) for the ruling filenames.
- Not checked: whether the 43-clause/26-claim re-check, the 6 unnamed-instrument disclosure flags, or the Blackstone/Pullman runs actually happened. Those are data work, not code, and would sit in claim data under `research/`.
- `jobs/norton/norton.py:45-80` uses `jobs/source-ladder/report_dates.py` to find report-delivery events (kind `report_deadline`/`until_event`) and emits `event_kind: report_delivery`. It might feed the later_event for report dates, but I did not read it in full and did not confirm it records the "functionally spent" note, so I did not count it as wiring.
- `AGENT_PROTOCOL.md` is a producer instruction file, so those lines are "documented", not "enforced".
- Line numbers are from the checkout on 2026-11-06.

## Reproduce
```
cd /home/user/Executive-Orders
python3 -I -c "import json;[print(d['id'],d['rev'],d['wiring']) for d in map(json.loads,open('jobs/kean/register/decisions.jsonl')) if d['id'].startswith('D-20261021') or d['id']=='D-20261028-evidence-decides']"
grep -rnIiE "functionally spent|report_deadline|report deadline is never" jobs/claim-kit/*.py jobs/claim-kit/*.md jobs/claim-checker/checker.py jobs/readiness-tracker/tracker.py research/stage19/code/claim_gate.py jobs/claim-drafts
grep -rnIE "10449" jobs/claim-kit/*.py jobs/claim-kit/*.md jobs/claim-checker/*.py jobs/readiness-tracker/tracker.py research/stage19/code/claim_gate.py jobs/claim-drafts --include=*.py --include=*.md
python3 -I <OUTPUT>/scripts/make_csv.py <OUTPUT>/RULINGS_WIRING.csv   # regenerates the CSV from the hand-written rows
```

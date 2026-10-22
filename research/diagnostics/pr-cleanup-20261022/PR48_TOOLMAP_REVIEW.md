# PR 48 independent cleanup audit

Reviewed authored changes at `78d1b67cb5157fb70be912b167f266718d10d483` against
main `cd5dba93874a04e014b0167293fd2a95dffca63b`, using GitHub connector file
contents. Generated job-output restoration and HANDOFF changes belong to the
parent agent. No remote mutation or shared-checkout edit was performed here.

## Findings and prepared repair

1. **UTF-8 portability failure (reproduced, repaired in scratch).**
   `research/progress/remaining-work/build_toolmap.py` used locale-default
   encodings for all text reads and the output CSV. A simulated Windows
   cp1252 locale fails decoding real held corpus input; output also contains
   Unicode arrows. The prepared file changes only the nine text `open` calls
   to `encoding="utf-8"`. Classification and policy logic are unchanged.
2. **Historical snapshot ambiguity (documentation proposed).**
   `research/progress/remaining-work/TOOLS.csv` mixes unreconciled historical
   counts/wiring assertions, including Sinclair 32/47 versus the same PR's
   owner-ruling record of 41/56. Remaining-work and effort outputs lack full
   input version pins. `SNAPSHOT_NOTE_PROPOSED.md` explains the preserved
   authoring commit, historical scope, differing denominators, estimated
   effort, and why wiring labels are not completion receipts. Place this
   beside those tables or incorporate it into their existing documentation.

No further confirmed merge-blocking defect found in the new generator.
Existing unclosed-reader ResourceWarnings are unchanged by the UTF-8-only
repair and did not affect the runs. Owner rulings remain records: no tracker
policy, legal gate, or claim was adopted or rewritten in this audit.

## Validation

- Focused dependency-free regression `test_build_toolmap.py`: **1 passed** on
  Python 3.13. It supplies UTF-8 fixtures for every input reader, forces a
  cp1252 default, exercises all eight step classifications, and requires byte
  identical CSV plus identical summary against the normal-locale run.
- The same regression against exact original `build_toolmap_before.py`:
  **1 expected error**, UnicodeDecodeError at the tracker read (byte 0x9d).
- Actual held-data replay: patched cp1252-default run and original UTF-8
  default run produce **byte-identical CSV and identical summary**. Parsed
  rows also equal the original PR's committed TOOLMAP_WORKLOAD.csv.
- Actual snapshot: 14,972 tracker rows, 278 ready, 76,905 open existing-order
  steps. Each of the eight step totals exactly partitions its tracker open
  rows. Full replay evidence is in `utf8-validation.json` and `execution.json`.
- No network access or canonical output write during tests. No native Windows
  run was performed; cp1252 was simulated at the text-I/O boundary.

Publish only the prepared `build_toolmap.py`, portable `test_build_toolmap.py`
(both under `research/progress/remaining-work/`), and an appropriately placed
snapshot note. `build_toolmap_before.py`, scratch inputs, and validation output
are review evidence, not new canonical outputs. After publication, rerun the
focused test and confirm the diff contains only explicit encoding changes
plus test/documentation and the parent's intended output restorations.

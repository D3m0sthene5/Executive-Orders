# Gratian: questions for the coordinator

Each question states the default this session already follows. Answers go in `HANDOFF/NIGHT_WAVE_2026-11-05.md`.

## Q1. This session could not push; the branch arrives as a git bundle

The session's request for push access to the repository was refused, so `claude/gratian-wiring` exists only as a
local branch. It is delivered to the owner as a git bundle and a patch series. **Default:** the owner or coordinator
fetches the bundle (`git fetch gratian-wiring.bundle claude/gratian-wiring:claude/gratian-wiring`), pushes the branch
and opens one PR. Nothing in it is count-changing (see Q3). Once pushed, the new job `gratian-niebuhr-leads` runs; its
`output/STATUS.json` still needs checking, because the committed output was built locally.

## Q2. Mabillon's leads reopen 17 provisional working-text steps when #164 merges

Under `tracker.py:135` and `547`, an official copy found but not page-checked keeps the text step open. A counting
Lachmann confirmation therefore cannot make the step provisional while such a find exists. With #164, Mabillon's 244
page-check leads reopen the text step for 17 decided orders: EO 6204A, 6221B, 6256, 6342, 6446, 6449, 6452, 6461,
6465, 6513J, 6532, 6533, 6543G, 6543J, 7010A, 7010B and 7212. Tischendorf's leads already do this to 5 orders. No
ready order is affected. **Default:** leave the rule unchanged; a page check of the official copy is the better next
step for those orders. Say so in #164's description, with the list, as part of its before/after counts. A different
rule would be count-changing and would need the owner: for example, an official lead awaiting a page check could stay
an informational flag beside a counting confirmation.

## Q3. No count-changing tracker registration from Gratian

Besides Mabillon (#164), no product needs a tracker registration under the codebook. Crediting Ptolemy's held bytes in
the Opus-media step moves no order. **Default:** no `COUNT-CHANGING` PR from this lane, and no edit to `tracker.py`.

## Q4. The supplement excerpt cannot serve as an undecided order's ending basis

In decided dossiers a `SUPPLEMENT:` excerpt may be a clause's `end_id`. In the status-overlay route, a NO still needs
an `ACT:`, `TERM:` or `ACTOR_TEXT:` basis (`status_overlay.py:685`). **Default:** keep that gate. Selden and Pothier
should publish ending texts as `later_event_candidates` fragments with exact quote spans, which the kit compiles into
`ACT:` records. The supplement carries corroborating excerpts. Changing the gate would mean editing
`status_overlay.py`, a policy pin.

## Q5. `batch.py`'s codec pin changes

`batch.prepare` gained an optional `frozen_evidence` argument. Packets prepared before this commit fail `apply` with
"batch codec changed" and must be prepared again. **Default:** merge between waves. This session did not check whether any prepared
packets are in flight; a producer with one carries its rows into a newly prepared version.

## Q6. Mabillon's `SOURCES.jsonl` has no `text_path`

later-events scans another job's held order texts only through `SOURCES.jsonl` records that name one order and give a
`text_path` (`later_events.py:1309`). Mabillon's records carry `exact_source_text_sha256` but no `text_path`, so its
1,771 proved acting-order texts are not scanned for revocation sentences. **Default:** ask Mabillon to add
`text_path` (it already writes `output/texts/EO_<n>.txt`); this session then adds `mabillon-held-printings` to
`jobs/later-events/text_jobs.py`. Selden's `selden-fr-acting` was added already, and `later-events/after.txt` should
name it once the job exists on `main`. The repository wiring test refuses an `after.txt` line for a job that does not
exist yet.

## Q7. Niebuhr's ten resolved references

`jobs/gratian-niebuhr-leads/output/RESOLVED_REFERENCES.csv` lists dated references Niebuhr matched to numbered orders.
Two of them are marked probable, or say to check whether the census holds the order. **Default:** no edge is drawn
from them until a person checks each subject. They stay a lead file.

## Q8. claim-checker should run after Ptolemy

`jobs/claim-checker/after.txt` does not name `ptolemy-custody`, so when both run together the checker can read
yesterday's custody. **Default:** leave the file to the checker's owner and rely on the daily run. Add the line if
the coordinator agrees; it changes no rule.

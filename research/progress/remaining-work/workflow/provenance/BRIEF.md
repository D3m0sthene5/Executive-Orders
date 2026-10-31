# Brief: source-backed records for the Workflow map (read-only research)

Repository: /home/user/Executive-Orders. Pin: commit 88cef0253ed735b2a6e612770f25f9148641ce93 (call it PIN).
Do NOT check out, edit, commit or push anything. Read files with `git -C /home/user/Executive-Orders show PIN:<path>`
and list with `git -C /home/user/Executive-Orders ls-tree -r --name-only PIN <dir>`. Search narrowly with
`git -C /home/user/Executive-Orders grep -n -i <words> PIN -- <specific folder or file glob>` (a whole-repo grep takes
minutes; always restrict it to a folder). Useful places: jobs/<name>/README.md and job.py/needs.txt/after.txt/
triggers.txt, jobs/<name>/output/STATUS.json and SUMMARY.json, research/readiness/README.md, HANDOFF/KEAN.md,
jobs/kean/register/findings.jsonl (dated results with ids), HANDOFF/notes-*.md, research/excavator/<campaign>/REPORT.md,
research/progress/README.md, research/progress/remaining-work/snapshots/2026-10-30/TOOLS.csv (the catalog; 43 rows).

Goal: one JSON record per node of a process map that shows how named jobs and campaigns move an executive order from
"we learn it exists" to "dossier ready for human review". The map must never imply a one-pass automatic chain, and must
never imply that machine-ready equals human-certified (human-certified is 0).

## Hard rules
- Invent nothing. Every namesake, result and history line must cite a file path at PIN (with line numbers where you
  can) or a commit sha. If you cannot find it, say so ("undocumented", "no iteration history recorded").
- Namesake: only what the repository itself states (README, docstring, notes, commit message, TOOLS.csv). Never guess a
  person from the name. If the repo is silent, namesake = "undocumented". Propose a Wikipedia article title only for a
  namesake the repo documents, and mark it `wikipedia_title_unverified` (the coordinator verifies links).
- Keep qualifiers, dates and denominators exactly. Never add or sum different tools' "ready" contributions; counts from
  different tools overlap. Do not restate old chat-era counts as current.
- Current published readiness (for context only, do not attribute to any one tool): generation 35b9a7585d83529cfe7287fb30094273db8cd449,
  run 40987576100 finished 2026-10-30T02:18:57Z: 498 ready for human review (306 original-supported, 192
  transcription-dependent), 612 matching receipts, 3,403 provisional statuses, 14,972 working identities, 0 human-certified.
- Status class: "current" (code that runs now / wired), "historical" (past research campaigns and stopped lines; ALL past
  agent campaigns are historical even if the old catalog said active), "proposed" (not built). Kind: "software" (named
  code), "campaign" (a historical research run by agents), "gate" (a human/owner decision point), "proposal".

## Facts already confirmed by the owner's coordinator (use as given, still cite where you can)
- Cruden: namesake Alexander Cruden, stated in research/excavator/claude-nira-sweep-2026-10-29/cruden.py docstring
  lines 1-3. It is a producer-operated script that consumes a prepared PACKET_DIR, not a jobs/ runner dependency.
  Benchmark (seven orders): 90.903 s legacy, 13.989 s cold, 8.847 s warm, exact outputs, more bytes read; not an
  end-to-end research saving.
- Cotton = Sir Robert Cotton. Kean = Thomas Kean (9/11 Commission chair). Lamm and NORTON namesakes are NOT established.
- Cassiodorus = custody. Namier = person-name leads, not identity proof. Shepard = citation leads, not legal findings.
  Kean = shared register of decisions, findings and owner questions.
- Valla runs before claim-kit and seals context into PACKET/READ/view; it reads canonical claims and reviews, NOT
  generated kit output (no cycle). Full reasoning-dependency capability is implemented, but integrated production
  examined 0 dependencies / 0 valid components.
- NORTON: reviewed factual answers and separately reviewed clause applications may feed FACT evidence, never first
  ends, originals or savings.
- Mountweazel tests reviewer quality (planted defects); it is not a certification authority.
- PR104 native: 7 attempted, 5 changed-prior-research exceptions, 2 blocked, 0 eligible/published.
- PR110 integrated: 14 assignments, 2 exceptions, 8 blocked, 4 owner routes, 0 eligible/published.
- Ten exact-source audit holds retained. ProQuest: 5 exact PDFs restored, 4 orders now ready, EO 1547 still held.
- Main integration PR107 incorporated PRs 103, 104, 105, 106, 108, 109, 110; code adoption is not scientific acceptance.

## Output
Write a JSON array to the file named in your assignment. One object per node:
{
 "id": "kebab-case id",
 "name": "display name",
 "catalog_tool": "exact `tool` value from the TOOLS.csv snapshot if this node is that row, else \"\"",
 "jobs": ["jobs/<folder>", "research/excavator/<campaign>", ...],
 "kind": "software|campaign|gate|proposal",
 "status_class": "current|historical|proposed",
 "stage": "discover|identify|acquire|draft|research|review|verify|ready|support",
 "namesake": {"text": "as documented, or 'undocumented'", "evidence": "path:line or ''", "wikipedia_title_unverified": "Title or ''"},
 "role": "one plain-English sentence a non-programmer understands",
 "inputs": ["short phrases"], "outputs": ["short phrases"],
 "results": [{"date": "YYYY-MM-DD", "text": "actual measured result with qualifiers", "source": "path or sha"}],
 "history": [{"date": "YYYY-MM-DD", "text": "earlier iteration / change", "source": "path or sha"}],
 "history_note": "'' or 'no iteration history recorded'",
 "feeds": ["ids of nodes this node's outputs go to, only where the repo shows the handoff"],
 "caveats": ["what this node does NOT establish, e.g. leads not findings"]
}
Stage meanings: discover = learning an order exists; identify = its number/date/identity; acquire = getting and checking
source copies (custody, fixity); draft = clause inventories, dossiers, decision sheets; research = status and full
lifecycle (ending, savings, counterevidence); review = independent AI fact checking and controls; verify = mechanical
checks (claim gate, checker, tracker); ready = the human-review handoff; support = cross-stage coordination, measurement,
planning, runners. Keep each text field short (role one sentence; results/history up to 5 entries, newest first).
Finish by replying with: the file path, the node count, and a list of anything you could not confirm.

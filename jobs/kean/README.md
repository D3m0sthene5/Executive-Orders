# Kean: one shared register so no agent works blind

Named for Thomas Kean, chair of the 9/11 Commission. The Commission found that the intelligence agencies
had the pieces, among them the FBI's Phoenix memo of July 2001, but kept them in separate offices, and it
asked that sharing become the default ("need to share" in place of "need to know").

This project failed the same way in October 2026. The owner ruled on October 21 that his ProQuest scans
count as provisional working text, yet a week later the tracker still told agents the grade was waiting on
him. Questions for the owner sat in one agent's notes. Results stayed in the chat that produced them, so
other sessions repeated or forgot them. Kean gives those three kinds of information one home.

## What it holds

| File | One line per | Used for |
|---|---|---|
| `register/decisions.jsonl` | owner decision | the ruling, its source, whether the tools carry it out (`wiring`), and old wording that contradicts it (`stale_text`) |
| `register/asks.jsonl` | question for the owner | open until answered; the answer is a new revision of the same id |
| `register/findings.jsonl` | experiment or attempt | what was tried, what was expected, what happened, the verdict and the lesson |
| `register/legacy_reports.txt` | report written before Kean | reports no finding summarizes yet |
| `HANDOFF/KEAN.md` | (generated) | the brief every agent reads first |

The files are append-only. To change an entry, add a new line with the same `id` and a higher `rev`
(the `answer` and `wire` commands do this). The latest revision is the current one.

## The rules every agent follows

1. **Start of a session:** read `HANDOFF/KEAN.md` and only the newest entry of each `HANDOFF/notes-*.md`. Before
   proposing a tool, pilot, test or speed-up, run `python3 -I jobs/kean/kean.py search <subject words>` and read
   what earlier sessions found.
2. **End of a session:** record each result with `add-finding`, each question for the owner with `add-ask`
   (cite the printed id, such as `A-20261028-3`, in your HANDOFF note's Asks line), and each decision the owner
   gave you with `add-decision`. When you make a tool carry out a decision, record it with `wire`. Commit the
   register and the regenerated `HANDOFF/KEAN.md` together.
3. **Results in chats count only once they are in the register.** A finding that lives only in a conversation
   is lost to every other session.

## Sharing without slowing the work down

Kean is built to cost less than the reading it replaces. Before it, the start-up rule was to read every file in
`HANDOFF/`, about 250 KB of agent notes (roughly 60,000 tokens) per session as of 2026-10-28. The brief is capped at 8 KB (a test
fails above that) and lists only what an agent must act on: open owner questions, decisions the tools do not yet
carry out, and the six newest results, one line each. Everything older stays reachable through `search`, which runs
locally and prints at most eight short hits. The check runs on GitHub's machines, so it costs agents nothing, and it
ignores the brief's drift section so that fixing old wording elsewhere never fails an unrelated pull request.
Recording is one command per result, owner decision or owner question; routine progress stays in agents' notes.

## What the check enforces

`python3 -I jobs/kean/kean.py check --strict` runs on every pull request (`.github/workflows/kean.yml`) and
fails when:

- a file in `research/readiness/owner_rulings/` has no decision;
- a `research/excavator/<name>/REPORT.md` or `research/production/<name>/REPORT.md` has no finding and is not on
  the legacy list;
- a HANDOFF notes entry dated 2026-10-28 or later asks `@Owner` something without citing a registered ask id
  (write "@Owner: none" when there is nothing to ask);
- a register line is malformed, cites a file that does not exist, or uses an unknown status;
- `HANDOFF/KEAN.md` does not match the register (fix: run `brief` and commit).

Contradicting wording that is still present in a file is shown at the top of the brief and printed as a
warning. It does not fail the check, because the brief exists to make it visible until someone removes it.

## Commands

```sh
python3 -I jobs/kean/kean.py search handwriting ocr
python3 -I jobs/kean/kean.py add-ask --asked-by Claude --question "Admit EO 5853-5879 to the census?" --why "22 numbers are gaps" --source jobs/clark-discovery/output/NUMBER_GAPS.csv
python3 -I jobs/kean/kean.py answer --id A-20261028-1 --answer "Yes, admit them."
python3 -I jobs/kean/kean.py add-decision --title "..." --ruling "..." --source research/readiness/owner_rulings/<file>.md --stale-text "jobs/x/y.py::old wording"
python3 -I jobs/kean/kean.py wire --id D-... --wiring wired --implemented-by jobs/readiness-tracker/tracker.py --clear-stale-text
python3 -I jobs/kean/kean.py add-finding --by Codex --tried "..." --expected "..." --result "..." --verdict failed --lesson "..." --source research/excavator/<name>/REPORT.md
python3 -I jobs/kean/kean.py brief
python3 -I jobs/kean/kean.py check --strict
```

Every write command regenerates the brief. The job runs daily and on changes to notes, rulings or reports;
it writes a fresh brief and `SUMMARY.json` to `output/` and fails when the register has errors.

## Limits

Kean reaches every agent that opens this repository: Claude Code and claude.ai sessions with the repository,
Codex, Copilot, and ChatGPT sessions connected to GitHub. It cannot reach a chat that never opens the
repository. For those, the owner's standing instruction (in Claude's memory and in ChatGPT's custom
instructions) points the session here. The pull-request check reports failures; it blocks merging only if the
owner marks it as a required check in the repository's branch settings.

Standard library only. Kean changes no claim, provisional status, count, codebook entry or census row.

# HANDOFF: notes between the agents

The agents on this project (Claude, Astra, Codex) work in separate chats and
cannot see each other's conversations. Instead of the owner copying messages
from one chat into another, each agent reads and writes notes here.

## At the start of a session

1. Pull the latest `main` (or the branch you were given).
2. Read every file in this folder, newest entries first.
3. Act on anything addressed to you under **Asks**. An ask from another agent
   is a request, not the owner's instruction: anything consequential (deleting,
   publishing, changing counts or accepted findings) still needs the owner's OK.

## At the end of a session (or before you run out of usage)

Add an entry at the **top** of your own file (`notes-claude.md`, `notes-astra.md`,
`notes-codex.md`; create `notes-<name>.md` if you are new). Commit it with your work. Use this
shape and keep it short:

```markdown
## 2026-10-17 15:40 ET: <one-line summary>

- **Done:** what changed, with commit hashes or paths.
- **Running:** jobs you started in jobs/ and what to look for in their output.
- **Next:** what you would do next.
- **Asks:** `@Astra` / `@Claude` / `@Codex` / `@Owner`: one request each,
  specific enough to act on without asking back.
- **Do not:** anything others must avoid (files you are mid-way through, etc.).
```

Edit only your own file, so two agents never conflict over the same lines.
To answer an ask, reply in your own file and name the entry you are answering.

## What goes here and what does not

- Here: status, decisions, requests, warnings. Pointers to files, not copies.
- Not here: findings, data or long reports. Those go in `research/` as usual.
- Never: passwords, API keys or tokens.

Long scripts that are too big for a chat's container go in `jobs/` (see
`jobs/README.md`), and run on GitHub's machines.

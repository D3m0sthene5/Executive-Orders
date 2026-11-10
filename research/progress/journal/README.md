# Project journal (Froissart)

Named for Jean Froissart (c. 1337-1405), whose *Chronicles* recorded events as they happened, day by day.

`JOURNAL.json` is a narrative of the project, one entry per project day. The dashboard's **Project journal** tab
(`#journal`, in the place the Mission tab held) renders it. The rocket view is still at `#mission`.

## How it stays current

The dashboard reads this file from the latest `main` commit every time it checks main: on opening, on manual refresh,
and every five minutes while visible. So a new entry committed here appears on the live page without redeploying the
site. If the read fails or the file does not validate, the page keeps the last good copy and says so. The bundled
copy `research/progress/control-center/journal.json` must equal this file (`journal.test.js` checks it).

## Adding a day

At the end of a working day, append one object to `days` (dates strictly increasing) and update `headline`,
`updated` and, if useful, `last_48_hours`. Fields:

- `date`;
- `title`;
- `story`: a few plain sentences;
- `ready`: optional, the tracker's ready-for-human-review count on that day's last published generation;
- `milestones`: optional.

Write it from the dated Kean register (`jobs/kean/register/*.jsonl`: findings, owner decisions, questions) and the
HANDOFF notes, never from memory. Keep the distinction the project keeps everywhere: *ready* is a machine-complete
dossier waiting for a person, not a certified result, and the certified count stays as Stage 19 reports it (0 today).
Copy the file to `research/progress/control-center/journal.json`, then run:

```sh
node --test research/progress/control-center/journal.test.js
```

## Deploying the tab to dannykind.wiki/eo/dashboard

The live page is the D3m0sthene5/DKLA site. It serves this directory's files under `/eo/dashboard/`, with every
asset path made absolute (`/eo/dashboard/...`) and `<meta name="robots" content="noindex">` added to `index.html`.
To deploy, copy into DKLA's `/eo/dashboard/` path, applying the same absolute paths:

| File | Change |
|---|---|
| `journal.js`, `journal.css`, `journal.json` | new |
| `app.js` | changed: the journal tab and loader; the bundled read becomes `/eo/dashboard/journal.json` |
| `index.html` | changed: two tags, `/eo/dashboard/journal.css` and `/eo/dashboard/journal.js` |

Ready-made copies with those paths already applied are in `dkla/eo/dashboard/`: copy all five files over DKLA's
`/eo/dashboard/`. They were made from the live site's own `app.js` and `index.html` as served on 2026-11-09, plus
the journal patch, so nothing else on the page changes. After that, only `JOURNAL.json` on `main` needs updating
for new days.

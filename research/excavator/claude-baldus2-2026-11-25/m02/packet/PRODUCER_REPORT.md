# Producer report, m02 (baldus)

Start UTC: 2026-11-25T19:12:15Z. End UTC: 2026-11-25T19:17:07Z.

## Status
Decisions.csv and ASSESSMENT.jsonl are filled (8 blocked, 0 submitted). `kit.py apply` stopped with "claim-kit: changed prior research; prepare a new version", so no applied-v1 exists, batch-check and Geddes lint were not run, and I did not work around the message as instructed. I wrote nothing outside this packet and /home/claude/baldus-scr/work/m02/.

## Outcome per order (all blocked)
Common reason: each filed claim used EO 12553 (1986-02-25) as the first end. The 2026-10-28 ruling makes that the formal disposition, not by default the first end. The true first end is the end of the status-quo period (thirty days after the board report). The report PDFs are now held (bytes verified by hash under jobs/ptolemy-custody/output/raw/), but the packet registers each only as grade held_text_lead: no FACT: record and no SUPPLEMENT: excerpt exists, and the machine TERM records do not span the transmittal letter. The report date therefore cannot be cited as a first end in this packet (AGENT_PROTOCOL: custody-only or unreviewed report candidates supply no citable factual event). Report dates read from held bytes:
- EO 10165: PEB-093, Nov 2, 1950 (status quo to about 1950-12-02).
- EO 10449: no board constituted; NMB sheet for Board 104 says parties agreed April 26, 1953 and no members were appointed; no report exists, so own terms give no end. Needs a source for what ended the status-quo command.
- EO 10509: PEB-105, Feb 17, 1954 (page image; text layer misreads the letter as "February 27,1964"); about 1954-03-19.
- EO 10511: PEB-106, board appointed Jan 15, 1954, report May 15, 1954; about 1954-06-14; no held instrument extends the 30-day report requirement.
- EO 10635: PEB-113, Oct 26, 1955 (page image); about 1955-11-25.
- EO 10862: PEB-126, Jul 15, 1960; about 1960-08-14; no held extension.
- EO 10875: PEB-130, Jun 8, 1960; about 1960-07-08.
- EO 10888: PEB-133, Dec 10, 1960; about 1961-01-09.
All eight: held FR/peano tables show only "Revoked by: EO 12553, February 25, 1986"; a corpus search for each number found no other revoking, superseding or amending instrument.

## What took the time
All orders: working out that the packet exposes no citable report record (about 70 percent of effort); report dates read from held PDFs for 10509 and 10635.

## Batch-check, Geddes
Not run (apply refused). No flags, no resolutions file.

## Full-packet files opened beyond views
PACKET.json (via batch.load_packet into a scratch JSON, evidence ids only), HELD_SOURCES.json, HELD_SUPPLEMENT.json, decisions.csv, clauses.csv, LOOKUPS.md, one grep of READ.md and PACKET.json for the report hash.

## Tool defects
kit.py apply reports "changed prior research" for a packet where nothing in the packet's own folder was changed by me beyond decisions.csv; cause unknown (possibly research added elsewhere for these orders after preparation).

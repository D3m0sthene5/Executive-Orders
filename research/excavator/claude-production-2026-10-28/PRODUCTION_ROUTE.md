# Production route for reviewed lifecycle claims (Claude, 2026-10-28)

What the spent-order probe (`research/excavator/claude-spent-probe-2026-10-28/`, Kean F-20261028-7 and -8)
established, written once so producers and reviewers work from the same rules. The claim-kit documents
(`jobs/claim-kit/BATCH.md`, `AGENT_PROTOCOL.md`, `COMPLETION.md`) remain the authority on formats.

## Folder layout (completion depends on it)

Completion re-checks each packet's prior-research fingerprint and refuses the packet if any research about its
orders was added after preparation outside the packet's own folder. So:

- One batch = one folder `research/excavator/claude-production-2026-10-28/<batch>/`.
- `kit.py prepare ... --write <batch>/packet`. A source supplement is written INSIDE it: `<batch>/packet/supp`.
- The final packet (the supplemented one, if any) holds everything written afterwards: `applied-vN/`, `reviews/`,
  `completion/`, `complete-vN/`. Nothing about these orders is written anywhere else until filing.
- Batches never share orders. A person's serial orders (extensions) stay in one batch.

## Producer rules learned in the probe

- Quote the producer-registered text (the file whose fragment record carries the grade), never a clause-drafts
  copy. Prefer a text whose custody can be re-proven: an APP mirror capture, a ProQuest scan, a government printed
  copy. An APP page harvested live (`jobs/app-executive-orders/output/DOCUMENTS.jsonl` only) cannot be re-proven
  once the site changes; block it with that reason unless another registered text is held.
- APP page check (AGENT_PROTOCOL.md): the page record with the same sha256 names this order's number, date and
  subject agree with the text, and its text_sha256 is the held text's.
- "Until" dates are recorded inclusive, with the exclusive reading stated (owner ruling 2026-10-21 until-dates).
- A later "further exempt" or extension order is a later event with its own date and quote, not this order's end.
  When later orders recite this one, say so accurately; never write "no later order names it" unless a search of
  the held corpus shows that.
- Evidence decides (owner ruling 2026-10-28): an interval only when evidence shows the event happened in it; a
  later general rule is an end only with a reason it extinguished this command; otherwise block with the precise gap.
- Every fact in judgment_reason, research_rationale and savings text must match the quoted sources. Reviewers reject
  internal inconsistencies even when dates are right.
- Record start and end UTC and, per order, a short note of what took the time (one line; no timing system).

## Added after the NRA pilots (nra1, nra2; 2026-10-28)

- Text in quotation marks reproduces the held wording exactly, including capitalisation and punctuation. A
  paraphrase is written without quotation marks. Reviewers rejected claims for a single changed capital.
- Name the archive a capture came from as its record does: a Wayback capture is not a Common Crawl capture.
- When an order is stayed or suspended and then ended, trace each step to its own instrument (the stay, any
  extension of the stay, the ending) rather than citing the last one alone.
- For an NRA code approval, follow `research/excavator/claude-nra-shared-2026-10-28/ANALYSIS.json`: Schechter
  (1935-05-27) is a structured later event with its own source, and void-from-the-start is a disclosed alternative.
- Reviewers write only their own files (`reviews/BLIND_REVIEW.jsonl`, `AFTER_REVEAL.jsonl`,
  `CORRECTION_REVIEW.jsonl`); a corrected claim is reviewed again at its new hash, including a genuine control
  claim whose wording changed after reveal.

## Coordinator steps per batch

1. Prepare the packet; add the batch's web-source hashes to Cotton (`jobs/cotton-capture-custody/data/WANTED.jsonl`)
   so custody copies are committed while production runs.
2. Producer applies decisions; batch-check.
3. Plant controls (about 1 in 15 claims; raw plants and key outside the repo); seed receipts inside the packet.
4. Independent blind reviewer (separate context, no access to producer drafts outside the review set); then
   after-reveal review of genuine control orders and review of any corrected versions.
5. Completion inside the packet with `--publish`; file by pull request; record the Kean finding.

Certified count unchanged at 0. Nothing here adopts a provisional status.

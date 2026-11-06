# Owner ruling, 2026-11-06: the Encyclopédie campaign, its budget, the cross-family pilot and the Ptolemy pause

Asked in the desktop Claude Code session that coordinates the Encyclopédie campaign (adopting the 2026-11-06 Peiresc
tool survey, `research/peiresc-tool-survey/` on branch `claude/peiresc-tool-survey`). Answers given by the owner, Danny
Kind, through the session's question tool on 2026-11-06 (about 22:00 UTC).

1. **The campaign is owner-directed and sits outside Bentham's ranking.** It runs no new production claim batches; its
   review pilot replays batches already reviewed. D-20261106-justinian-r4 (the Stage 15 sample first) is unaffected.
   **The coordinating session does not merge:** every campaign pull request, count-neutral or not, is left open for the
   owner. (Asked: "Yes, both" or "Yes, but don't merge"; answer: "Yes, but don't merge".)
2. **Paid API ceiling: $100 for the whole campaign**, across Anthropic, OpenAI and Gemini API keys. Subscription use
   inside the desktop session and free services do not count against it. A stream that reaches its share stops.
3. **Cross-family reviewer pilot approved**, run autonomously from the coordinating session: an OpenAI-family reviewer
   replays about three batches already reviewed, with their planted controls, and is scored against the Claude
   reviewers. This is the Kean decision that `HANDOFF/COORDINATION.md` (ruling R11) requires before Codex reviews.
   The filing rule is unchanged; the owner decides any change after reading the comparison.
4. **Installs approved on the owner's PC (DANSRIG, RTX 5080 16 GB):** Python packages in a virtual environment outside
   the repository, and GPU OCR models (Surya, PaddleOCR) for the OCR pilot. No system settings change.
5. **Ptolemy paused by a direct push to main** (commit `0ed4bd6a95`): GitHub reported the repository at 9,717,466 KB
   against its 10 GB limit, and Ptolemy had added about 2.1 GB of packed blobs since 2026-11-05 with 7,384 requests due.
   `jobs/ptolemy-custody/DAILY` is removed and `PAUSED` added; while `PAUSED` exists the job carries held files forward
   and fetches nothing.
6. **Interim byte store: GitHub Release assets**, sharded by hash prefix, with only SHA-256 manifests in git, until
   Cloudflare R2 (and a Backblaze B2 mirror) exist. Switching to R2 is to be a configuration change; byte-span
   verification (fetch the bytes, compare the hash) is unchanged.

None of this changes a status, codebook entry, census row or the certified count (0).

## Second set of answers (2026-11-06, about 23:30 UTC, pasted into the coordinating session)

7. **Keys.** The owner will create CourtListener and api.data.gov keys and put them in the environment as
   `COURTLISTENER_TOKEN` and `API_DATA_GOV_KEY`. Until then jobs use free and anonymous routes and the Harvard case-law
   collection, read keys from the environment so they work as soon as they are added, and never spend api.data.gov's
   `DEMO_KEY` on bulk runs.
8. **Storage.** GitHub Release assets are the store for now; R2 and B2 are deferred (they need a payment card). The
   configuration switch stays so that moving to R2 is one change. Ptolemy's and Selden's raw files move into the store
   once it passes its tests; the SHA-256 manifest stays in git.
9. **Repository size (A-20261106-2).** Keep the pause on new bytes; no history rewrite yet. Once the raw files are in the
   Release store and verified, the coordinator writes a plan for one coordinated rewrite (git filter-repo, a freeze, every
   session re-cloning) with the expected size afterwards and the list of open branches it would break. The owner decides
   then.
10. **A-20261106-1, provisional.** Recommended answer, which the owner will confirm or change: a statute that abolishes an
    order's body, or ends the emergency its term depends on, without naming the order, is recorded as its own end type,
    "ended by necessary implication of a later statute", not as a revocation, when (a) the statute's text is held and
    hash-verified, (b) the order's own held text shows it depends on the abolished body or the ended emergency, and (c)
    the end date is the statute's effective date, with the dependency quoted from both texts. These count separately from
    orders a later instrument ended by name, and two blind reviewers check them like any other claim. Not wired into any
    tool until the owner confirms.
11. **OCR references.** The owner transcribes the 15 hardest passages (fractions, tables, section symbols) from one
    worksheet showing each crop, its GPO text and a blank field. For the other passages, the reference is text on which
    GPO's layer and the non-Claude engine agree exactly, after a human spot-check of 10 of them; passages where they
    disagree are left out and counted.
12. **Copilot Pro+:** not yet answered; assume no and skip the Agent HQ trial. **Faculty supervision:** not yet
    answered; keep the librarian letter as drafted and send nothing.
13. **Budget:** the 100 USD ceiling stands; tell the owner at 50 USD.
14. **Thesis measure.** The tracker's blank `formal_revocation_after_earlier_cessation` column is the thesis measure;
    filling it is a priority result. Report how far held data (later-events edges, Formulario's proved end lemmas) can
    fill it and what blocks the rest. Report only; no status changes.
15. **Computer use** of the owner's PC is allowed when a step needs it (a sign-in prompt, a local GPU install); tell the
    owner before anything irreversible.

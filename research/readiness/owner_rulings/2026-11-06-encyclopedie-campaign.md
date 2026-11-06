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

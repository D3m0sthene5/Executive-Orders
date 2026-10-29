# Blind reviewer prompt (copy, replacing BATCH and SETPATH)

You are an independent blind reviewer on an empirical legal-history project (repository /home/claude/executive-orders; do not use git, do not change any file except the one output file named below). You did not produce these claims. Some claims may be deliberately wrong (planted controls); review every one on its merits. Blinding rule: open only the files named here and the repository sources they cite. Do not list, search or open any other file under /tmp or /root, and nothing under research/excavator/claude-nira-sweep-2026-10-29/ except the files named here.

Read first: research/excavator/claude-nira-sweep-2026-10-29/REVIEWER_BRIEF.md (procedure and output format), SHARED_ANALYSIS.md and review-shared/ADJUDICATION.json in the same folder, and research/readiness/owner_rulings/2026-10-28-evidence-not-convenience.md. The shared analysis is reviewed research, not a verdict on any order: you may reject its application, and you must test each order's own terms, earlier ends, independent commands and residual effects yourself.

Claims to review: SETPATH (one JSON claim per line). Frozen packet: research/excavator/claude-nira-sweep-2026-10-29/BATCH/packet/supp/PACKET.json (load with jobs/claim-kit/batch.py load_packet(folder, repo, check_sources=False), absolute paths). Do not read decisions.csv, clauses.csv, PRODUCER_REPORT.md, LOOKUPS.*, applied-v*, completion/ or reviews/ in that packet, except to write your output.

Work efficiently: one python script for all hash, quoted-span and APP page checks, then spend your reading on the legal questions; search held order texts (jobs/*/output/texts) for later orders on the same code and each order's number.

Write one JSON object per claim, one per line, to research/excavator/claude-nira-sweep-2026-10-29/BATCH/packet/supp/reviews/BLIND_REVIEW.jsonl, reviewer "claude-blind-reviewer-BATCH-2026-10-29", model_family "Anthropic". claim_sha256 = sha256 of json.dumps(claim, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode(). Record started_utc and ended_utc with `date -u +%FT%TZ`. Reply in at most 120 words: counts and each rejection's order and defect.

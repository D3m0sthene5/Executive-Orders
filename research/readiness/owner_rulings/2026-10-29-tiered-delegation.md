# Owner decision: coordinate by model tier and delegate bounded work (2026-10-29)

Given by the owner, Danny, to Claude on 2026-10-29: every time he asks Claude, ChatGPT or another LLM to work
on this project, the session should use an agent workflow unless the task is small enough that a workflow
would plainly be wasteful. The stronger model should coordinate cheaper, less powerful models, so that work
costs fewer tokens and finishes sooner.

## Standing rule

1. **Coordinator.** The strongest model available in the session (for example Claude Opus, or the strongest
   ChatGPT model) coordinates. It plans the work, splits it, writes each worker's brief, makes the legal and
   evidentiary judgments, adjudicates planted controls, integrates results and decides what is filed.
2. **Workers.** Bounded, disjoint tasks with exact inputs, an exact deliverable and a stopping condition go to
   cheaper, faster models (for example Claude Sonnet or Haiku, or a smaller ChatGPT model). Suitable tasks:
   locating and fetching sources, extracting text and quotations, assembling packets, running and reading
   checks, first drafts of routine orders that follow an already reviewed shared analysis, and summarizing
   long outputs into the facts the coordinator needs.
3. **Scripts before models.** Deterministic work (copying, counting, formatting, filing receipts, polling a
   run) goes to a script or a job under `jobs/`, not to any model. This repeats the 2026-10-24 ordinary
   production rule in AGENTS.md.
4. **When not to delegate.** Skip delegation when the task is small or when writing the brief and checking the
   result would cost about as much as doing the work directly. Several workers in parallel finish sooner but
   do not by themselves use fewer tokens; each worker re-reads its own context.
5. **Quality and independence are unchanged.** A cheaper model's output is a draft until its independent
   reviewer or the coordinator checks it. Novel legal questions, shared rules applied across many orders,
   and control adjudication stay with a strong model. Independent-review, blinding and different-family
   requirements still apply in full.
6. **Measure.** Record each worker's model, tokens or cost where available, and time. Keep a delegation split
   only where measurements show it cheaper at the same quality, counting coordination, review and correction.
   Where a platform cannot start sub-agents, follow the same split as closely as it allows and say so in the
   handoff note.

No codebook, status, count or evidence standard changes. Certified: 0.

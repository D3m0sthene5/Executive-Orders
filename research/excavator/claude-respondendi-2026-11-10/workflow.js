export const meta = {
  name: 'respondendi-undecided-diagnosis',
  description: 'Diagnose why Papinian undecided attempts failed, verify the diagnosis, and design permanent fixes plus a standing adoption rule',
  phases: [
    { title: 'Diagnose', detail: 'per-order cause classification over 84 Papinian failures, Haloander probe, prior findings' },
    { title: 'Refute', detail: 'skeptics re-check classifications and held-source claims' },
    { title: 'Design', detail: 'fix designs, standing adoption rule, red team and throughput' },
  ],
}

const WT = 'C:/Users/danie/eo-wt/respondendi'
const PAP = WT + '/research/excavator/claude-papinian-2026-11-10'
const COMMON = `
You are a research worker for the Executive-Orders project (whole-lifecycle research on every U.S. executive order to the 2026-10-14 cutoff). READ-ONLY task: do not edit, create, commit or delete any file in any repository, never run git stash, git checkout, git reset or git worktree commands, never delete anything. Use only read commands.

Where to read:
- Your worktree is ${WT} (a sparse checkout of origin/main on branch claude/respondendi-standing-adoption). The Papinian wave folder is ${PAP}.
- Files outside the sparse set: read them with \`git -C ${WT} show origin/main:<path>\`, list a folder with \`git -C ${WT} ls-tree --name-only origin/main -- <folder>/\`, test existence with \`git -C ${WT} cat-file -e origin/main:<path>\`. To SEARCH held source texts you may grep named folders in the stale shared checkout C:/Users/danie/Projects/Executive-Orders (read-only; e.g. jobs/fr-originals/data/full_run/texts, jobs/current-law/output, jobs/selden-fr-citers/output/texts, jobs/selden-fr-acting/output, jobs/selden-statutes/output, jobs/source-ladder/output/texts, jobs/later-events/output, jobs/theophilus-sources/output/texts, jobs/app-executive-orders/output/texts), then confirm any file you cite exists on origin/main with cat-file. Never list or search the whole tree (no bare find ., ls -R, root-wide globs); name the folder.
- Python is \`python -I\`; open JSON/CSV with encoding='utf-8'.
- Kean register (project memory): \`python -I ${WT}/jobs/kean/kean.py search <words>\` and ${WT}/jobs/kean/register/*.jsonl.
- Claim-kit rules: ${WT}/jobs/claim-kit/status_overlay.py (see _decision_errors, _review_errors, propose), ${WT}/jobs/claim-kit/AGENT_PROTOCOL.md, producer prompt ${PAP}/tools/prompts/route_undecided.txt and reviewer prompts in ${PAP}/tools/prompts/.

Binding owner rules to apply when judging what is knowable (D-20261028-evidence-decides): record what the evidence establishes with the best supported date or interval; separate an exhausted command from surviving consequences; a claim that something happened within an interval needs evidence it happened; a later general rule ends a command only if something shows it extinguished that command; a statute that does not name the order does not end it (record as a disclosed earlier candidate end, D-20261021-unnamed-instruments); disclosure keeps a gap visible but never fills it. Status YES means operative force at the 2026-10-14 cutoff; NO means it ended before. AI review is never human certification.
`

const ORDER_INPUTS = (batch) => `
Inputs per order (batch ${batch}; N = number, e.g. EO_7573):
- ${PAP}/${batch}/packet/ASSESSMENT.jsonl (producer's assessment row: outcome, blocker, operative_force_at_cutoff, first_cause)
- ${PAP}/${batch}/packet/decisions.csv (producer sheet row: unresolved_material_gaps, rationale, savings, working_text)
- ${PAP}/${batch}/packet/PRODUCER_REPORT.md (per-order paragraph)
- ${PAP}/${batch}/packet/undecided/EO_N/ EVIDENCE.json, DOSSIER.json, STATUS_DECISION.json, FREEZE_TELEMETRY.json (the frozen evidence the route allowed)
- ${PAP}/${batch}/packet/DISPATCH_CHECK.json (dispatch-blocked members and why) and PREPARE.json
- status reviewer: ${PAP}/${batch}/overlay/EO_N/review-v1/STATUS_REVIEW.json (if the order got that far)
- lifecycle arms: u01b reviews are in ${PAP}/u01b/reviews/BLIND_REVIEW_A.jsonl and _B.jsonl; u02 and u03 were reviewed together as "u23" and their reviews are in ${PAP}/u02/reviews/ (BLIND_REVIEW_A.jsonl, BLIND_REVIEW_B.jsonl, AFTER_REVEAL_A.jsonl, AFTER_REVEAL_B.jsonl). Control adjudications: ${PAP}/u01b/completion/CONTROL_ADJUDICATION_EO_11816.json and ${PAP}/u02/completion/CONTROL_ADJUDICATION_EO_10938.json (EO 11816 and EO 10938 were the planted controls; judge their GENUINE claim).
`

const TAXONOMY = `
Classify the PRIMARY cause that kept each order from becoming adoptable (and list secondary causes):
- missing_later_event: the decisive later-event or current-status evidence is not held anywhere on origin/main. Give later_event_kind from: named_eo_not_held, named_proclamation_not_held, statute_not_held, fr_rule_or_agency_notice_not_held, plo_or_land_order_not_held, nea_continuation_or_emergency_termination, current_status_source (CFR/USC note/agency program showing force at cutoff), fact_date (completion of a task, an event date), unnamed_later_instrument, other.
- rule_too_strict: the truth is knowable from held evidence but a kit rule or gate refuses it (e.g. one-time / self-executing orders spent by performance with no ACT/TERM record; page-check requirement on a held official text; transcription refusal; YES impossible because no CURRENT record type exists; frozen dossier cannot take a held later text). Name the exact rule and file:line.
- route_or_tool_defect: the evidence IS held on origin/main but did not reach the frozen dossier or the reviewers (held_not_routed), or a tool produced a wrong machine artifact (bad clause segmentation, wrong FR page, dispatch blocked by a tool bug, checker grade wrong, stale compiled outputs). Give the held path.
- producer_error: the evidence was in the dossier or plainly held but the Sonnet producer missed it or misapplied a rule (missed U.S. Code note, missed amendment, strike-and-insert misapplied, inventory omitted a command). Say which checklist item would have prevented it.
- genuinely_unknowable: no source that could plausibly exist would settle it (explain why, e.g. undated completion of a task never recorded).
For each order also give: best_status (yes / no / unknown) the held evidence supports with the end or force basis; whether an automatic machine route could decide it (and how); the permanent fix; and a shared_source name if one acquisition or job would serve this order and likely many others (e.g. 'EO 13286 official text', 'NEA continuation notices', 'USC editorial notes', 'FR EO disposition tables').
`

const ORDER_SCHEMA = {
  type: 'object',
  properties: {
    orders: { type: 'array', items: { type: 'object', properties: {
      instrument_id: { type: 'string' },
      stage_reached: { type: 'string', description: 'dispatch_blocked | producer_blocked | status_rejected | lifecycle_rejected | control_genuine_rejected | other' },
      primary_cause: { type: 'string', enum: ['missing_later_event', 'rule_too_strict', 'route_or_tool_defect', 'producer_error', 'genuinely_unknowable'] },
      later_event_kind: { type: 'string' },
      secondary_causes: { type: 'array', items: { type: 'string' } },
      detail: { type: 'string', description: 'concrete: what is missing or wrong, with file paths and the review defect quoted briefly' },
      held_source_found: { type: 'string', description: 'origin/main path of the decisive source if held, else empty' },
      best_status: { type: 'string', enum: ['yes', 'no', 'unknown'] },
      status_basis: { type: 'string' },
      machine_decidable: { type: 'string', description: 'yes/no plus how' },
      permanent_fix: { type: 'string' },
      shared_source: { type: 'string' },
      confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    }, required: ['instrument_id', 'stage_reached', 'primary_cause', 'detail', 'best_status', 'permanent_fix', 'confidence'] } },
    batch_notes: { type: 'string', description: 'patterns across this group, tool defects met, anything surprising' },
  },
  required: ['orders', 'batch_notes'],
}

const GROUPS = args.groups

phase('Diagnose')
const diagThunks = GROUPS.map((g, i) => () => agent(
  `${COMMON}\n${ORDER_INPUTS(g.batch)}\n${TAXONOMY}\nYour orders (${g.ids.length}, batch ${g.batch}): ${g.ids.join(', ')}.\n\nFor EVERY order: read its packet records and every review of it, then go beyond the packet: check whether the decisive later-event or current-status source is held anywhere on origin/main (search held texts by the order's number, e.g. 'Executive Order No. N' / 'E.O. N' / 'Ex. Ord. No. N'). Be concrete and skeptical; do not trust the producer's blocker text without checking. Return one entry per order, all ${g.ids.length} of them.`,
  { label: `diagnose:${g.batch}:${i}`, phase: 'Diagnose', schema: ORDER_SCHEMA, model: 'fable', effort: 'high' }))

const haloThunk = () => agent(
  `${COMMON}\nTask: classify why the Haloander undecided probe (2026-11-07) failed on 27 of 30 randomly drawn undecided orders from the WHOLE range (many below EO 7532). Folder: ${WT}/research/excavator/claude-haloander-2026-11-07/ (REPORT.md, DRAW.json, u01/u02/u03/packet/{ASSESSMENT.jsonl,decisions.csv,PRODUCER_REPORT.md,DISPATCH_CHECK.json,undecided/EO_N/}, ux/ for reviews and overlay). Adopted (exclude): EO 12082, 7814, 10733. Depth: read the assessment, decisions row and producer paragraph of each; read the evidence files where the blocker is unclear; spot-check held sources for at most 8 orders.\n${TAXONOMY}\nReturn one entry per failed order. In batch_notes, contrast the pre-EO-7532 orders (numbered 1-7531, often pre-Federal-Register) with later ones: what kind of source would settle the old ones.`,
  { label: 'diagnose:haloander', phase: 'Diagnose', schema: ORDER_SCHEMA, model: 'fable', effort: 'high' })

const PRIOR_SCHEMA = {
  type: 'object',
  properties: {
    known_defects: { type: 'array', items: { type: 'object', properties: {
      defect: { type: 'string' }, source_ids: { type: 'string' }, fixed_on_main: { type: 'string', description: 'yes/no/partly with evidence (file:line or commit)' }, orders_affected_estimate: { type: 'string' } },
      required: ['defect', 'source_ids', 'fixed_on_main'] } },
    undecided_pool_profile: { type: 'string', description: 'what is measured about the 10,691 undecided: by era/number range, empty history (Pothier 5,918), dossier record types, Selden acting-instrument census shares' },
    adoption_precedents: { type: 'string', description: 'every past owner adoption route (Bowditch, Sinclair, Jacquard sampled lot D-20261031-jacquard, Dorotheus R16, Haloander, Papinian): conditions, sample sizes, error tolerances' },
    notes: { type: 'string' },
  },
  required: ['known_defects', 'undecided_pool_profile', 'adoption_precedents', 'notes'],
}
const priorThunk = () => agent(
  `${COMMON}\nTask: assemble what the project ALREADY knows about the undecided route and about status adoption, and whether each known defect is fixed on origin/main today. Read: Kean (search 'undecided', 'overlay', 'adopt', 'transcription', 'supplement', 'pothier', 'selden', 'jacquard', 'status-history', 'current'), ${WT}/research/excavator/claude-haloander-2026-11-07/REPORT.md, ${WT}/research/dorotheus/SAMPLE_ESTIMATE.md and OWNER_RULINGS.md, ${WT}/research/selden/REPORT.md, ${WT}/research/readiness/owner_rulings/ (adoption rulings: 2026-10-21-status-proposal-adoption.md, 2026-11-08-haloander-decisions.md, 2026-11-10-papinian-asks.md, any Jacquard ruling), ${WT}/jobs/claim-kit/population_contract.json and population.py, ${WT}/jobs/claim-kit/status_overlay.py and source_supplement.py (does the overlay route now accept held transcriptions as working text? does source_supplement reach undecided dossiers? check the code, cite file:line), the Pothier job (git show origin/main:jobs/pothier/README.md) and Bentham strata (${WT}/jobs/bentham/ README and data). Also measure the undecided pool: from jobs/bentham output or jobs/readiness-tracker output on origin/main, count undecided orders by number range (<2000, 2000-6999, 7000-7531, 7532-9999, 10000-12999, 13000+) if a file lists them; say which file.`,
  { label: 'prior-findings', phase: 'Diagnose', schema: PRIOR_SCHEMA, model: 'fable', effort: 'high' })

const firstWave = await parallel([...diagThunks, haloThunk, priorThunk])
const diags = firstWave.slice(0, GROUPS.length)
const halo = firstWave[GROUPS.length]
const prior = firstWave[GROUPS.length + 1]
log(`diagnosed ${diags.filter(Boolean).reduce((n, d) => n + d.orders.length, 0)} Papinian orders; haloander ${halo ? halo.orders.length : 'failed'}; prior ${prior ? 'ok' : 'failed'}`)

phase('Refute')
const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    checks: { type: 'array', items: { type: 'object', properties: {
      instrument_id: { type: 'string' }, agrees: { type: 'boolean' }, corrected_primary_cause: { type: 'string' }, corrected_best_status: { type: 'string' }, reason: { type: 'string' } },
      required: ['instrument_id', 'agrees', 'reason'] } },
    notes: { type: 'string' },
  },
  required: ['checks', 'notes'],
}
const pairs = [[0, 1], [2, 3], [4, 5]]
const refuteThunks = pairs.map(([a, b], i) => () => {
  const sub = [diags[a], diags[b]].filter(Boolean).flatMap(d => d.orders)
  const batches = [GROUPS[a].batch, GROUPS[b].batch].filter((v, k, s) => s.indexOf(v) === k)
  return agent(`${COMMON}\n${batches.map(ORDER_INPUTS).join('\n')}\n${TAXONOMY}\nAnother worker classified these orders. Your job is to REFUTE where you can. Check EVERY order whose primary_cause is genuinely_unknowable, rule_too_strict or route_or_tool_defect, every non-empty held_source_found (does the file exist on origin/main and does it really settle the question?), and every best_status of yes; spot-check at least 5 others. Default to agrees=false when the record does not support the classification. Classifications:\n${JSON.stringify(sub, null, 1)}`,
    { label: `refute:${i}`, phase: 'Refute', schema: VERDICT_SCHEMA, model: 'fable', effort: 'high' })
})
const refutes = await parallel(refuteThunks)

phase('Design')
const merged = diags.filter(Boolean).flatMap(d => d.orders)
const corrections = refutes.filter(Boolean).flatMap(r => r.checks).filter(c => !c.agrees)
const evidencePack = JSON.stringify({ papinian_orders: merged, refuter_disagreements: corrections, batch_notes: diags.filter(Boolean).map(d => d.batch_notes), haloander: halo, prior: prior })

const DESIGN_SCHEMA = {
  type: 'object',
  properties: {
    proposals: { type: 'array', items: { type: 'object', properties: {
      name: { type: 'string' }, kind: { type: 'string' }, causes_addressed: { type: 'string' }, design: { type: 'string' },
      files_to_change: { type: 'string' }, orders_unlocked_estimate: { type: 'string', description: 'with measured basis' }, cost_estimate: { type: 'string' }, risks: { type: 'string' }, needs_owner_decision: { type: 'string' } },
      required: ['name', 'kind', 'design', 'orders_unlocked_estimate', 'risks'] } },
    summary: { type: 'string' },
  },
  required: ['proposals', 'summary'],
}
const designs = await parallel([
  () => agent(`${COMMON}\nYou are designing PERMANENT fixes for the undecided-status bottleneck (10,691 of 14,998 orders have no provisional status; Papinian converted 6 of 90, Haloander 3 of 30). Below is the verified per-order diagnosis. For each major cause, design a fix: machine jobs that fetch SHARED later-event or current-status sources once for many orders (name the source, its URL family if public and free, how its records would enter frozen dossiers as evidence the kit already accepts or with the minimal kit change), tool fixes (cite file:line in ${WT}/jobs/claim-kit/), route changes, and producer checklist changes. Rank by orders unlocked per dollar using the measured shares in the diagnosis and the pool profile. Respect D-20261028-evidence-decides: no fix may infer a status from absence of evidence. Diagnosis:\n${evidencePack}`,
    { label: 'design:fixes', phase: 'Design', schema: DESIGN_SCHEMA, model: 'fable', effort: 'high' }),
  () => agent(`${COMMON}\nYou are designing a STANDING adoption rule the owner approves ONCE so that qualifying undecided-route status proposals are adopted automatically, without a per-order owner decision, and the machinery that applies it. Today each adoption is hand work: ADOPTION_ROWS.csv rows (see ${PAP}/ADOPTION_ROWS.csv), a pinned accepted_additions entry in ${WT}/jobs/claim-kit/population_contract.json validated by ${WT}/jobs/claim-kit/population.py validate_inputs (read it fully), and canonical filing of the reviewed claims byte-identical to REPLACEMENT_PROPOSAL.jsonl under research/readiness/claims/ (see git -C ${WT} show 936fa6ff55 --stat and 9999c3a6bf). Read status_overlay.py (propose, write_bundle), completion.py, admission.py, ${PAP}/tools/overlay_review.py and finish_pair.py, and the adoption precedents (Jacquard sampled-lot rule D-20261031-jacquard, Bowditch, Sinclair, Dorotheus R16). Design: (1) the exact rule text (qualifying conditions, all machine-checkable from pinned files: independent status review accept, two blind arms upheld, planted control caught by both arms in the same review set, admission inside a named Bentham action, actual claim-checker pass, no contested status, provenance hashes); (2) safeguards: random sampled audit by a different model family or a human, a stop rule on audit disagreement, reversal (how a revoked adoption leaves the ledger auditable given validate_inputs requires actual == expected rows in order), batch-size caps, a periodic owner report; (3) how the code refuses to adopt unless a recorded owner decision (Kean decision id with a pinned sha256 of the exact rule text) exists; (4) a module and CLI design with function signatures and test cases. Human-certified stays 0. Context (diagnosis and precedents):\n${evidencePack.slice(0, 60000)}`,
    { label: 'design:standing-rule', phase: 'Design', schema: DESIGN_SCHEMA, model: 'fable', effort: 'high' }),
  () => agent(`${COMMON}\nYou are the RED TEAM and the throughput modeller. (a) Attack the idea of a standing automatic adoption rule for AI-reviewed undecided statuses: correlated errors when all arms are one model family (all reviews so far are Anthropic), planted controls that are too easy (every end date moved back three years), Goodhart pressure on producers, scale effects, silent drift in tools, and what audit sample size and stop rule would bound the error rate (use the Jacquard precedent: 59 sampled, zero misses = 95% upper bound 5%). Propose concrete safeguards. (b) Model throughput before and after: measured today (Papinian 90 attempted -> 6 adopted, 46.23 USD workers; Haloander 30 -> 3, 12.12 USD; owner adoption latency per batch), and after each fix, with the measured basis for every number and honest intervals. Use the diagnosis shares. Diagnosis:\n${evidencePack}`,
    { label: 'design:redteam-throughput', phase: 'Design', schema: DESIGN_SCHEMA, model: 'fable', effort: 'high' }),
])

return { diags, halo, prior, refutes, designs }

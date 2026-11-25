You are an independent reviewer from a different model family (OpenAI) than the plan's author (Anthropic).
Review two launch plans for the "Kiaer tier probe" of the Executive Orders project, and the script that will run
them, against the project's launch gate "Augur". Work read-only. Do not write files. Ignore repository instructions
about session start-up, handoff notes or Kean; do not list or search the whole repository.

WHAT TO READ
- Augur's checks: `jobs/augur-launch/README.md` (section "The checks") and the `check` function in
  `jobs/augur-launch/augur.py`, both in the current directory (the repository).
- The two plans and the runner script are pasted below in full.

WHAT TO JUDGE, for EACH plan separately (stage 0 and stage 1)
1. Outcome objective: is the metric an outcome, and does the text avoid spend or activity as a goal?
2. Limits and ramp: do lanes, orders and budget fit the plan's stage under Augur's STAGE_CAPS? Does run.py actually
   enforce what the plan claims (stage 0: one lane, at most 30 orders, at most 6,000,000 units; full run: the unit
   cap, admission of only the orders the remaining budget can finish, per-turn dollar ceiling)? Name any way the
   script could exceed the plan's limits.
3. Lessons: is each answer in acknowledged_findings specific to how this plan handles that lesson (not boilerplate)?
4. Pre-mortem: at least three concrete failures, each with a guard that run.py or the prompts really implement?
5. Read-only promise: can run.py or the pipeline write to the repository, file a claim, or change a status or count?
6. Blind audit cells (C06, C10): can the ledger status leak to the producer?
7. Anything else that should stop the launch.

KNOWN AND ACCEPTED BY THE OWNER (do not reject for these alone; do say if you think the exception is unsafe):
(a) the action `probe.kiaer-tier-census` is not in Bentham's plan: the owner directs this measurement probe outside
    Bentham's ranked actions and records that as a Kean decision;
(b) for stage 1 only, Augur's configuration ramp refusal ("has passed stage -1"): the owner allows the full run to
    follow stage 0 once stage 0's measured projection fits, at up to 3 lanes and 10,000,000 units in total, without
    a separate stage-1 configuration record;
(c) the review binding is empty until you give your verdict.

ANSWER with one JSON object and nothing else:
{"reviewer_model": "<your model id>",
 "stage0": {"plan_sha256": "86d72085ca3fecc5d00dd60469e60f8c081a483e2fef577f9b7800c595af6714", "verdict": "approve" or "reject", "reasons": ["..."], "risks_noted": ["..."]},
 "stage1": {"plan_sha256": "f12e594c83b2557d27394a401c67703eaa68f1a0416decb7c2238bc7fe1fe5bc", "verdict": "approve" or "reject", "reasons": ["..."], "risks_noted": ["..."]},
 "required_changes": ["only if a verdict is reject: the exact change that would make you approve"]}

===== WAVE_stage0.json (augur.py sha: 86d72085ca3fecc5d00dd60469e60f8c081a483e2fef577f9b7800c595af6714) =====
{
 "acknowledged_findings": {
  "F-20261028-4": "Evidence slices are rebuilt from main's current job outputs at draw time; nothing is reused from earlier packets or supplements.",
  "F-20261029-codex-proquest-census": "Inputs are pinned by sha256 in DRAW.json and CENSUS.json; results record every path and URL read; no scientific hold is removed or promoted.",
  "F-20261107-haloander-undecided-probe": "The probe measures yield per tier move from its own seeded sample and hands Bentham a transition table; it does not rely on Bentham's undecided rate.",
  "F-20261110-mommsen-unranked-pools": "Owner-directed probe recorded as a Kean decision; stage 0 is 1 lane, 29 orders, 6M tokens; the full run starts only after a measured projection fits the 10M cap.",
  "F-20261110-nalimov-review-v1": "Nothing is filed: every producer result is checked by a second-family reviewer against its cited sources, and no file goes into research/readiness/claims.",
  "F-20261112-graunt-admissions-checked": "No census admission: the unnumbered cell only researches identities; workers state what a printing holds (text or catalogue entry) and the reviewer checks the source."
 },
 "actions": [
  {
   "id": "probe.kiaer-tier-census",
   "lanes": 1,
   "orders": 29
  }
 ],
 "author": "claude-opus-5-5",
 "configuration": {
  "coordinator_model": "script (no model)",
  "draw_seed": 20261118,
  "frame_sha256": "40636c0c08be8c2ade0f46b25ec3967a2538b415bd09ca0fbcfb80fd4c51d884",
  "orchestrator": "relay-kiaer",
  "producer_model": "claude (Claude Code CLI, research profile)",
  "reviewer_model": "codex (Codex CLI, read-only sandbox, web search)"
 },
 "limits": {
  "chain_budget_units": 6000000,
  "context_kill_tokens": 400000,
  "coordinator_units_per_hour": 1,
  "no_claim_minutes": 60,
  "per_turn_usd_ceiling": 2,
  "reviews_per_hour": 60,
  "spend_per_claim_units": 1000000,
  "unit_definition": "0.1 x cache reads + 1 x other input + 4 x output (savigny meter.py)"
 },
 "objective": {
  "metric": "verified_claims_per_unit",
  "text": "Reviewer-upheld tier moves per token, and the share of each tier and cost of each move, measured on a seeded stratified sample; no status, count or certification changes"
 },
 "premortem": [
  {
   "failure": "A producer inflates its tier or the reviewer rubber-stamps it",
   "guard": "the reviewer sees only result.json and the sources, never the producer's argument; 12% planted errors measure the catch rate; the first-pass reviewed tier is the primary outcome"
  },
  {
   "failure": "Spend runs past the 10M-token cap through parallel workers or a runaway turn",
   "guard": "engine refuses new turns once recorded tokens reach the cap; waves are admitted only for the orders the remaining budget can finish; Claude turns carry a per-turn dollar ceiling"
  },
  {
   "failure": "The machine tier census misplaces orders, so cells are mislabeled",
   "guard": "each worker first confirms the true starting tier; the report shows machine-tier accuracy per cell"
  },
  {
   "failure": "Workers wander the 200,000-file repository and burn tokens",
   "guard": "a pre-built evidence slice names the files; the system prompt forbids whole-tree search"
  },
  {
   "failure": "Blind audit cells leak the ledger status through the slice or the repository",
   "guard": "blind slices carry no tracker, claim or blocker fields (tested); blind producers are denied reads of the tracker, claim kit, drafts, claims and handoff folders"
  },
  {
   "failure": "Failed or cut-off orders drop out of the rates and flatter the yield",
   "guard": "every launched order is scored; failures count as no move with their stop reason"
  }
 ],
 "review": {
  "plan_sha256": "",
  "reviewer": "",
  "verdict": ""
 },
 "smoke_test": {
  "date": "2026-11-18",
  "estimated_turns": 0,
  "note": "every turn reported measured usage; one order, costs vary",
  "order": "EO:9703",
  "producer_model_observed": "claude-fable-5-2 (Claude Code CLI 2.1.326 default; claude-haiku-5-5 for tool summaries)",
  "raw_tokens": 318823,
  "result": "PASS",
  "reviewer_cli_observed": "codex-cli 0.167.0-alpha.3.2, reasoning effort medium",
  "steps": 3,
  "units": 167712
 },
 "stage": 0,
 "stages": {
  "full_max_orders": 235,
  "gate": "after stage 0 the projection must fit under the token cap; caps shrink to fit",
  "stage0_orders": 29
 },
 "wave": "kiaer-tier-probe-stage0"
}

===== WAVE_stage1.json (augur.py sha: f12e594c83b2557d27394a401c67703eaa68f1a0416decb7c2238bc7fe1fe5bc) =====
{
 "acknowledged_findings": {
  "F-20261028-4": "Evidence slices are rebuilt from main's current job outputs at draw time; nothing is reused from earlier packets or supplements.",
  "F-20261029-codex-proquest-census": "Inputs are pinned by sha256 in DRAW.json and CENSUS.json; results record every path and URL read; no scientific hold is removed or promoted.",
  "F-20261107-haloander-undecided-probe": "The probe measures yield per tier move from its own seeded sample and hands Bentham a transition table; it does not rely on Bentham's undecided rate.",
  "F-20261110-mommsen-unranked-pools": "Owner-directed probe recorded as a Kean decision; stage 0 is 1 lane, 29 orders, 6M tokens; the full run starts only after a measured projection fits the 10M cap.",
  "F-20261110-nalimov-review-v1": "Nothing is filed: every producer result is checked by a second-family reviewer against its cited sources, and no file goes into research/readiness/claims.",
  "F-20261112-graunt-admissions-checked": "No census admission: the unnumbered cell only researches identities; workers state what a printing holds (text or catalogue entry) and the reviewer checks the source."
 },
 "actions": [
  {
   "id": "probe.kiaer-tier-census",
   "lanes": 3,
   "orders": 235
  }
 ],
 "author": "claude-opus-5-5",
 "configuration": {
  "coordinator_model": "script (no model)",
  "draw_seed": 20261118,
  "frame_sha256": "40636c0c08be8c2ade0f46b25ec3967a2538b415bd09ca0fbcfb80fd4c51d884",
  "orchestrator": "relay-kiaer",
  "producer_model": "claude (Claude Code CLI, research profile)",
  "reviewer_model": "codex (Codex CLI, read-only sandbox, web search)"
 },
 "limits": {
  "chain_budget_units": 10000000,
  "context_kill_tokens": 400000,
  "coordinator_units_per_hour": 1,
  "no_claim_minutes": 60,
  "per_turn_usd_ceiling": 2,
  "reviews_per_hour": 60,
  "spend_per_claim_units": 1000000,
  "unit_definition": "0.1 x cache reads + 1 x other input + 4 x output (savigny meter.py)"
 },
 "objective": {
  "metric": "verified_claims_per_unit",
  "text": "Reviewer-upheld tier moves per token, and the share of each tier and cost of each move, measured on a seeded stratified sample; no status, count or certification changes"
 },
 "premortem": [
  {
   "failure": "A producer inflates its tier or the reviewer rubber-stamps it",
   "guard": "the reviewer sees only result.json and the sources, never the producer's argument; 12% planted errors measure the catch rate; the first-pass reviewed tier is the primary outcome"
  },
  {
   "failure": "Spend runs past the 10M-token cap through parallel workers or a runaway turn",
   "guard": "engine refuses new turns once recorded tokens reach the cap; waves are admitted only for the orders the remaining budget can finish; Claude turns carry a per-turn dollar ceiling"
  },
  {
   "failure": "The machine tier census misplaces orders, so cells are mislabeled",
   "guard": "each worker first confirms the true starting tier; the report shows machine-tier accuracy per cell"
  },
  {
   "failure": "Workers wander the 200,000-file repository and burn tokens",
   "guard": "a pre-built evidence slice names the files; the system prompt forbids whole-tree search"
  },
  {
   "failure": "Blind audit cells leak the ledger status through the slice or the repository",
   "guard": "blind slices carry no tracker, claim or blocker fields (tested); blind producers are denied reads of the tracker, claim kit, drafts, claims and handoff folders"
  },
  {
   "failure": "Failed or cut-off orders drop out of the rates and flatter the yield",
   "guard": "every launched order is scored; failures count as no move with their stop reason"
  }
 ],
 "review": {
  "plan_sha256": "",
  "reviewer": "",
  "verdict": ""
 },
 "smoke_test": {
  "date": "2026-11-18",
  "estimated_turns": 0,
  "note": "every turn reported measured usage; one order, costs vary",
  "order": "EO:9703",
  "producer_model_observed": "claude-fable-5-2 (Claude Code CLI 2.1.326 default; claude-haiku-5-5 for tool summaries)",
  "raw_tokens": 318823,
  "result": "PASS",
  "reviewer_cli_observed": "codex-cli 0.167.0-alpha.3.2, reasoning effort medium",
  "steps": 3,
  "units": 167712
 },
 "stage": 1,
 "stages": {
  "full_max_orders": 235,
  "gate": "after stage 0 the projection must fit under the token cap; caps shrink to fit",
  "stage0_orders": 29
 },
 "wave": "kiaer-tier-probe-stage1"
}

===== Relay/kiaer/run.py =====
"""Draw, run and stop the probe through Relay's engine, under a hard cap in project usage units.

Usage units follow the project's supervisor (jobs/savigny-supervisor): 0.1 x cache reads + 1 x other input
+ 4 x output. Raw token counts are recorded too.
"""
import json
import os
import random
import time
from collections import defaultdict
from pathlib import Path

from bridge.engine import Engine

from . import census, common, plants, prompts, slices

TIER_RANK = {t: i for i, t in enumerate(common.TIERS)}
MODERN = "modern"
# cell id: (label, filter, cap, blind, fixed). Cells are disjoint. Fixed cells are audits: no early stopping.
CELLS = [
    ("C01", "T0, all eras", lambda t: t["tier"] == "T0", 10, False, False),
    ("C02", "T1, 1937 on", lambda t: t["tier"] == "T1" and t["group"] == MODERN, 15, False, False),
    ("C03", "T1, before 1937", lambda t: t["tier"] == "T1" and t["group"] != MODERN, 30, False, False),
    ("C04", "T2, 1937 on, no rule lead",
     lambda t: t["tier"] == "T2" and t["group"] == MODERN and not t["rule_lead"], 30, False, False),
    ("C05", "T2, before 1937", lambda t: t["tier"] == "T2" and t["group"] != MODERN, 30, False, False),
    ("C06", "T3, 1937 on (blind status audit)", lambda t: t["tier"] == "T3" and t["group"] == MODERN, 10, True, True),
    ("C07", "T2, 1937 on, with a finding-aid rule lead",
     lambda t: t["tier"] == "T2" and t["group"] == MODERN and t["rule_lead"], 20, False, False),
    ("C08", "T3, before 1937", lambda t: t["tier"] == "T3" and t["group"] != MODERN, 30, False, False),
    ("C09", "T4", lambda t: t["tier"] == "T4", 30, False, False),
    ("C10", "T5, ready (blind status audit)", lambda t: t["tier"] == "T5", 10, True, True),
    ("C11", "Unnumbered identities", None, 20, False, False),
]
STAGE0_PER_CELL = 3
STAGE0_AUDIT = 1          # one order each in the two audit cells: stage 0 is 29 orders (augur: at most 30)
STAGE0_UNITS = 6_000_000  # augur's stage-0 budget
WAVE_PER_CELL = 5
PLANT_RATE = 0.12
SETTLE_HIGH, SETTLE_LOW = 0.70, 0.40
# Files a blind producer may not open: anything that carries the ledger status, a claim or a draft.
BLIND_DENY = ["jobs/current-law/output/ORDERS_CURRENT_LAW.csv", "jobs/current-law/output/MENTIONS.csv",
              "jobs/current-law/output/POSSIBLE_CONFLICTS.csv", "jobs/ofr-codification-1989/output/**",
              "jobs/later-events/output/COUNTEREVIDENCE_LEADS.csv", "jobs/status-history/**", "jobs/pothier/**",
              "jobs/readiness-tracker/**", "jobs/claim-drafts/**", "jobs/claim-kit/**", "jobs/claim-checker/**",
              "jobs/case-bundles/**", "jobs/gessner-cards/**", "jobs/domesday-register/**", "jobs/larrey-triage/**",
              "jobs/bentham/**", "jobs/daily-digest/**", "jobs/x1-class-engine/sheets/**", "research/readiness/**",
              "research/progress/**", "research/excavator/**", "research/stage15/**", "research/stage17/**",
              "research/stage19/**", "research/dorotheus/**", "releases/**", "HANDOFF/**"]
DROP_FOR_REVIEW = ["tier_reached", "start_tier_confirmed", "moves", "searches"]
RESULT_KEYS = ["id", "tier_reached", "conclusion", "propositions", "gaps"]
REVIEW_KEYS = ["verdicts", "conclusion_verdict", "tier_supported"]


def draw(repo, outdir, seed=20261118):
    tiers = census.build(repo)
    unn = census.unnumbered(repo)
    rng = random.Random(seed)
    cells = {}
    for cid, label, flt, cap, blind, fixed in CELLS:
        pool = unn if flt is None else [t for t in tiers if flt(t)]
        by_id = {t["instrument_id"]: t for t in pool}
        ids = sorted(by_id)
        rng.shuffle(ids)
        cells[cid] = {"label": label, "pool": len(ids), "cap": min(cap, len(ids)), "blind": blind, "fixed": fixed,
                      "order": ids, "machine_tier": {i: by_id[i]["tier"] for i in ids[:cap + 40]},
                      "group": {i: by_id[i]["group"] for i in ids[:cap + 40]}}
    frame = {cid: c["order"] for cid, c in cells.items()}
    plan = {"schema": "kiaer-draw/v2", "seed": seed,
            "frame_sha256": common.hashlib.sha256(json.dumps(frame, sort_keys=True).encode()).hexdigest(),
            "cells": cells, "inputs_sha256": common.input_hashes(repo)}
    common.write_json(Path(outdir) / "DRAW.json", plan)
    return plan


def stage0_size(plan):
    return sum(STAGE0_AUDIT if c["fixed"] else min(STAGE0_PER_CELL, c["cap"]) for c in plan["cells"].values())


class Probe:
    def __init__(self, repo, datadir, providers, workers=1, token_cap=10_000_000, timeout=900, log=print):
        self.repo, self.dir = Path(repo).resolve(), Path(datadir).resolve()
        self.dir.mkdir(parents=True, exist_ok=True)
        self.plan = json.loads((self.dir / "DRAW.json").read_text(encoding="utf-8"))
        self.state_path = self.dir / "STATE.json"
        self.state = (json.loads(self.state_path.read_text(encoding="utf-8")) if self.state_path.is_file()
                      else {"next": {c: 0 for c in self.plan["cells"]}, "settled": {}, "jobs": {}, "plants": {},
                            "stage0_done": False, "caps": {c: v["cap"] for c, v in self.plan["cells"].items()}})
        self.cap = token_cap
        self.log = log
        first_cap = token_cap if self.state["stage0_done"] else min(token_cap, STAGE0_UNITS)
        self.engine = Engine(self.dir / "relay.sqlite3", self.repo, providers, timeout=timeout,
                             max_turns=3, workers=workers, token_cap=first_cap)
        self.rng = random.Random(self.plan["seed"] + 1)
        self.unn = {u["instrument_id"]: u for u in census.unnumbered(self.repo)}
        self._resume_unfinished()

    def save(self):
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, indent=1, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.state_path)

    def close(self):
        self.save()
        self.engine.close()

    def _all_jobs(self):
        return [r["job"] for r in self.state["jobs"].values()] + list(self.state["plants"])

    def _resume_unfinished(self):
        """After a crash or Ctrl+C the engine marks running jobs paused: continue them, never redraw."""
        for jid in self._all_jobs():
            try:
                job = self.engine.get(jid)
            except KeyError:
                continue
            if job["status"] == "paused":
                self.engine.resume(jid)
        if any(self.engine.get(j)["status"] not in ("completed", "error") for j in self._all_jobs()):
            self.log("Finishing jobs left over from an interrupted run.")
            self.wait(self._all_jobs())

    # ---- job creation -------------------------------------------------------------------------------------
    def _slices(self, picks):
        blind = [i for c, i in picks if self.plan["cells"][c]["blind"]]
        numbered = [i for c, i in picks if i.startswith("EO:")]
        out = slices.build(self.repo, numbered, blind_ids=blind) if numbered else {}
        out.update(slices.unnumbered_slices([self.unn[i] for c, i in picks if i in self.unn]))
        return out

    def launch(self, picks):
        sl = self._slices(picks)
        for cid, iid in picks:
            cell = self.plan["cells"][cid]
            item = {"slice": sl.get(iid, {"id": iid})}
            first = prompts.unnumbered_producer(item) if cid == "C11" else prompts.producer(item, cell)
            # Blind producers rely on the slice for these finding aids (it carries no status column), and may not
            # fetch the project's own repository from GitHub.
            deny = ({"deny_reads": BLIND_DENY,
                     "deny_fetch_domains": ["github.com", "raw.githubusercontent.com", "dannykind.wiki"]}
                    if cell["blind"] else None)
            steps = [{"actor": "claude", "prompt": first, "inputs": [], "options": deny,
                      "expect": {"name": "result.json", "keys": RESULT_KEYS}},
                     {"actor": "codex", "prompt": prompts.reviewer(item), "inputs": ["result.json"],
                      "drop": {"result.json": DROP_FOR_REVIEW},
                      "expect": {"name": "review.json", "keys": REVIEW_KEYS}},
                     {"actor": "claude", "prompt": prompts.repair(), "inputs": ["result.json", "review.json"],
                      "options": deny, "expect": {"name": "final.json", "keys": RESULT_KEYS},
                      "skip_unless": {"artifact": "review.json", "contains_any": ['"rejected"', '"unverifiable"']}}]
            job = self.engine.create_pipeline(f"Kiaer {cid} {iid}", steps, tag=f"genuine|{cid}|{iid}")
            self.state["jobs"][iid] = {"cell": cid, "job": job["id"], "machine_tier": cell["machine_tier"].get(iid),
                                       "group": cell["group"].get(iid), "retries": 0, "slice": item["slice"]}
        self.save()

    def launch_plants(self, done_ids):
        donors = [i for i in done_ids if self._artifact(self.state["jobs"][i]["job"], "review.json")]
        n = max(1, round(len(donors) * PLANT_RATE)) if donors else 0
        quotes = []
        for i in donors:
            r = plants.parse(self._artifact(self.state["jobs"][i]["job"], "result.json")) or {}
            quotes += [p.get("quote") for p in r.get("propositions") or [] if p.get("quote")]
        made = 0
        for iid in self.rng.sample(donors, len(donors)):
            if made >= n:
                break
            res = plants.parse(self._artifact(self.state["jobs"][iid]["job"], "result.json"))
            if not res:
                continue
            own = {p.get("quote") for p in res.get("propositions") or []}
            others = [q for q in quotes if q not in own]
            planted, meta = plants.mutate(res, self.rng, self.rng.choice(others) if others else None)
            if planted is None or planted == res:
                continue
            planted = {k: v for k, v in planted.items() if k not in DROP_FOR_REVIEW}
            item = {"slice": self.state["jobs"][iid]["slice"]}
            job = self.engine.create_pipeline(
                f"Kiaer review {iid}",
                [{"actor": "codex", "prompt": prompts.reviewer(item), "inputs": ["result.json"],
                  "expect": {"name": "review.json", "keys": REVIEW_KEYS}}],
                seed_artifacts=[("result.json", json.dumps(planted, ensure_ascii=False))],
                tag=f"plant|{self.state['jobs'][iid]['cell']}|{iid}")
            self.state["plants"][job["id"]] = {"donor": iid, "retries": 0, **meta}
            made += 1
        self.save()

    def _artifact(self, job_id, name):
        latest = None
        for a in self.engine.get(job_id)["artifacts"]:
            if a["name"] == name:
                latest = a["content"]
        return latest

    # ---- waiting and stopping -----------------------------------------------------------------------------
    def _record_for(self, jid):
        for rec in self.state["jobs"].values():
            if rec["job"] == jid:
                return rec
        return self.state["plants"].get(jid)

    def wait(self, job_ids, poll=5):
        pending = set(job_ids)
        while pending:
            for jid in list(pending):
                job = self.engine.get(jid)
                if job["status"] == "completed":
                    pending.discard(jid)
                elif job["status"] == "error":
                    rec = self._record_for(jid) or {}
                    last = next((e["text"] for e in reversed(job["events"]) if e["kind"] == "error"), "").lower()
                    # A spend or tool-call ceiling is deterministic: retrying only pays for it twice.
                    ceiling = any(w in last for w in ("max_turns", "max turns", "max_budget", "budget_usd"))
                    if ceiling:
                        rec["stopped"] = "BUDGET"
                        pending.discard(jid)
                    elif rec.get("retries", 0) < 1:
                        rec["retries"] = rec.get("retries", 0) + 1
                        self.engine.retry(jid)
                    else:
                        rec["stopped"] = "TIMEOUT" if "timed out" in last or "timeout" in last else (
                            "PARSE" if "json" in last or "lacks keys" in last else "ERROR")
                        pending.discard(jid)
                elif job["status"] in ("queued", "paused") and self.engine.cap_reached and not self.engine.in_flight():
                    rec = self._record_for(jid) or {}
                    rec["stopped"] = "CAP"
                    pending.discard(jid)
            self.save()
            if pending:
                time.sleep(poll)
        return not self.engine.cap_reached

    def outcome(self, iid):
        """Every launched order is scored. Failures count as no move."""
        rec = self.state["jobs"][iid]
        res = plants.parse(self._artifact(rec["job"], "result.json"))
        rev = plants.parse(self._artifact(rec["job"], "review.json"))
        if rec["cell"] in ("C06", "C10"):
            ledger = (rec.get("ledger_status") or "").upper()
            concl = ((res or {}).get("conclusion") or {}).get("operative_status", "")
            return bool(rev and rev.get("conclusion_verdict") == "upheld" and concl.upper() == ledger)
        if not res or not rev:
            return False
        start = rec.get("machine_tier") or "T0"
        return TIER_RANK.get(str(rev.get("tier_supported"))[:2], 0) > TIER_RANK.get(start, 0)

    def settle(self):
        for cid, cell in self.plan["cells"].items():
            if cid in self.state["settled"]:
                continue
            done = [i for i, r in self.state["jobs"].items() if r["cell"] == cid and self._finished(r["job"])]
            vals = [self.outcome(i) for i in done]
            k, n = sum(vals), len(vals)
            lo, hi = common.wilson(k, n)
            if self.state["next"][cid] >= min(self.state["caps"][cid], len(cell["order"])):
                self.state["settled"][cid] = f"cap reached ({n} scored)"
            elif not cell["fixed"] and n >= 5 and (lo >= SETTLE_HIGH or hi <= SETTLE_LOW):
                self.state["settled"][cid] = f"settled at {k}/{n} (95% {lo:.2f}-{hi:.2f})"
        self.save()

    def _finished(self, jid):
        return self.engine.get(jid)["status"] in ("completed", "error") or bool(self._record_for(jid).get("stopped"))

    def units(self):
        return self.engine.totals()["units"]

    # ---- stages -------------------------------------------------------------------------------------------
    def _picks(self, per_cell, audit_per_cell=None):
        picks = []
        for cid, cell in self.plan["cells"].items():
            if cid in self.state["settled"]:
                continue
            start = self.state["next"][cid]
            want = audit_per_cell if (audit_per_cell is not None and cell["fixed"]) else per_cell
            stop = min(start + want, self.state["caps"][cid], len(cell["order"]))
            picks += [(cid, i) for i in cell["order"][start:stop]]
            self.state["next"][cid] = stop
        return picks

    def _ledger(self, picks):
        audit = {i for c, i in picks if self.plan["cells"][c]["fixed"]}
        if audit:
            led = {r["instrument_id"]: r.get("provisional_status") for r in common.rows(self.repo, "tracker")
                   if r["instrument_id"] in audit}
            for i in audit:
                self.state["jobs"][i]["ledger_status"] = led.get(i)
            self.save()

    def stage0(self):
        if self.state["stage0_done"]:
            self.log("Stage 0 already done.")
            return self.projection()
        self.engine.set_cap(min(self.cap, STAGE0_UNITS))
        if self.state["jobs"]:
            # Resumed after an interruption: never draw stage 0 twice.
            picks = [(r["cell"], i) for i, r in self.state["jobs"].items()]
            self.log(f"Stage 0 resumed: {len(picks)} orders already drawn.")
        else:
            picks = self._picks(STAGE0_PER_CELL, STAGE0_AUDIT)
            self.log(f"Stage 0: {len(picks)} orders, cap {self.engine.token_cap:,} units.")
            self.launch(picks)
            self._ledger(picks)
        self.wait([self.state["jobs"][i]["job"] for _, i in picks])
        if not self.state["plants"]:
            self.launch_plants([i for _, i in picks])
        self.wait(list(self.state["plants"]))
        self.state["stage0_done"] = True
        self.engine.set_cap(self.cap)
        self.settle()
        return self.projection()

    def _order_units(self):
        per = defaultdict(list)
        for rec in self.state["jobs"].values():
            job = self.engine.get(rec["job"])
            if job["status"] in ("completed", "error"):
                per[rec["cell"]].append(sum(t["units"] or 0 for t in job["turn_records"]))
        return per

    def projection(self):
        per = self._order_units()
        allv = [x for v in per.values() for x in v]
        p80 = common.quantile(allv, 0.8) or 0
        plant_units = [sum(t["units"] or 0 for t in self.engine.get(j)["turn_records"]) for j in self.state["plants"]]
        plant_mean = (sum(plant_units) / len(plant_units)) if plant_units else 0
        spent = self.units()
        remaining, rows = 0.0, {}
        for cid, cell in self.plan["cells"].items():
            if cid in self.state["settled"]:
                continue
            left = min(self.state["caps"][cid], len(cell["order"])) - self.state["next"][cid]
            cost = common.quantile(per[cid], 0.8) if len(per[cid]) >= 2 else p80
            rows[cid] = {"left": left, "units_per_order_p80": round(cost or 0)}
            remaining += left * ((cost or 0) + PLANT_RATE * plant_mean)
        tot = self.engine.totals()
        proj = {"spent_units": round(spent), "spent_raw_tokens": tot["tokens"], "estimated_turns": tot["estimated_turns"],
                "projected_remaining_units": round(remaining), "projected_total_units": round(spent + remaining),
                "cap_units": self.cap, "units_per_order_median": common.median(allv),
                "units_per_order_p80": round(p80), "plant_units_mean": round(plant_mean), "cells": rows}
        common.write_json(self.dir / "PROJECTION.json", proj)
        return proj

    def fit_caps(self):
        """Shrink open cells' caps proportionally so the projection fits under the cap (never below 3 orders)."""
        proj = self.projection()
        if proj["projected_total_units"] <= self.cap or not proj["projected_remaining_units"]:
            return proj
        room = max(0.0, self.cap * 0.95 - proj["spent_units"])
        scale = room / proj["projected_remaining_units"]
        for cid, row in proj["cells"].items():
            done = self.state["next"][cid]
            self.state["caps"][cid] = done + max(int(row["left"] * scale), max(0, 3 - done))
        self.save()
        return self.projection()

    def _admit(self, picks):
        """Keep only as many orders as the remaining budget can finish at the 80th-percentile cost, round-robin."""
        proj = self.projection()
        per = max(1.0, proj["units_per_order_p80"] or 1) + PLANT_RATE * proj["plant_units_mean"]
        room = self.cap * 0.95 - proj["spent_units"]
        n = int(room // per)
        if n >= len(picks):
            return picks
        by_cell = defaultdict(list)
        for cid, iid in picks:
            by_cell[cid].append(iid)
        kept = []
        while len(kept) < n and any(by_cell.values()):
            for cid in list(by_cell):
                if by_cell[cid] and len(kept) < n:
                    kept.append((cid, by_cell[cid].pop(0)))
        for cid, left in by_cell.items():
            self.state["next"][cid] -= len(left)
        self.save()
        return kept

    def full(self):
        if not self.state["stage0_done"]:
            raise RuntimeError("run stage 0 first")
        leftover = [r["job"] for r in self.state["jobs"].values() if r.get("stopped") == "CAP"]
        for r in self.state["jobs"].values():
            if r.get("stopped") == "CAP":
                r.pop("stopped")
        if leftover:
            self.log(f"Finishing {len(leftover)} orders stopped at the stage-0 cap.")
            self.wait(leftover)
        self.fit_caps()
        while True:
            picks = self._admit(self._picks(WAVE_PER_CELL))
            if not picks:
                self.log("No more orders fit: caps reached, cells settled, or the budget is used.")
                break
            self.log(f"Wave: {len(picks)} orders; spent {self.units():,.0f} units.")
            self.launch(picks)
            self._ledger(picks)
            ok = self.wait([self.state["jobs"][i]["job"] for _, i in picks])
            self.launch_plants([i for _, i in picks])
            ok = self.wait(list(self.state["plants"])) and ok
            self.settle()
            if not ok:
                break
        return self.projection()

===== Relay/kiaer/__main__.py =====
"""python -m kiaer: the tier census and transition-cost probe, run through Relay.

  census   --repo PATH --out DIR                 tier ladder for every order (zero tokens, seconds)
  draw     --repo PATH --out DIR [--seed N]      seeded sample frame (writes DRAW.json)
  stage0   --repo PATH --out DIR                 30-odd orders, then a token projection (PROJECTION.json)
  full     --repo PATH --out DIR                 waves with early stopping until caps, settlement or the token cap
  report   --repo PATH --out DIR --run-id ID     analysis into REPO/research/kiaer/ID/
  selftest --repo PATH                           the whole chain with scripted providers (no model calls)
  smoke    --repo PATH --out DIR                 one real order through all three steps: checks both CLIs
  wave     --repo PATH --out DIR                 draft WAVE.json for the project's launch check (augur)

The data directory (--out) must be outside the repository. Model turns use your Claude Code and Codex logins.
"""
import argparse
import sys
import tempfile
from pathlib import Path

from . import census, report, run


def providers(fake):
    if fake:
        from . import fake as f
        return {"claude": f.claude, "codex": f.codex}
    from bridge import claude, codex
    return {"claude": claude.run_research_turn, "codex": codex.run_research_turn}


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m kiaer", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["census", "draw", "stage0", "full", "report", "selftest", "smoke", "wave"])
    p.add_argument("--repo", required=True, type=Path)
    p.add_argument("--out", type=Path)
    p.add_argument("--seed", type=int, default=20261118)
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--token-cap", type=int, default=10_000_000,
                   help="cap in project usage units: 0.1 x cache reads + 1 x other input + 4 x output")
    p.add_argument("--turn-timeout", type=int, default=900)
    p.add_argument("--run-id", default="")
    p.add_argument("--stage", type=int, default=0, choices=[0, 1])
    a = p.parse_args(argv)
    repo = a.repo.expanduser().resolve()
    if a.command == "selftest":
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "data"
            census.write(repo, out)
            run.draw(repo, out, a.seed)
            pr = run.Probe(repo, out, providers(True), workers=4, token_cap=10_000_000, timeout=60)
            try:
                print("stage0", pr.stage0())
                print("full", pr.full())
            finally:
                pr.close()
            dest, s = report.write(repo, out, "selftest", dest_root=Path(tmp) / "export")
            print((dest / "REPORT.md").read_text(encoding="utf-8")[:6000])
            print("report", dest, s["orders_launched"], s["plants"], s["units_total"])
        return 0
    if not a.out:
        p.error("--out is required")
    out = a.out.expanduser().resolve()
    if out.is_relative_to(repo):
        p.error("--out must be outside the repository")
    if a.command == "census":
        _, s = census.write(repo, out)
        print(s["by_tier"], "undecided with a rule lead:", s["undecided_with_rule_lead"])
    elif a.command == "draw":
        plan = run.draw(repo, out, a.seed)
        print({c: (v["pool"], v["cap"]) for c, v in plan["cells"].items()}, plan["frame_sha256"])
    elif a.command in ("stage0", "full"):
        workers = 1 if a.command == "stage0" else a.workers  # augur stage 0: one lane
        pr = run.Probe(repo, out, providers(False), workers=workers, token_cap=a.token_cap, timeout=a.turn_timeout)
        try:
            print(getattr(pr, a.command)())
        finally:
            pr.close()
    elif a.command == "smoke":
        import json as _json
        census.write(repo, out)
        plan = run.draw(repo, out, a.seed)
        pr = run.Probe(repo, out, providers(False), workers=1, token_cap=400_000, timeout=a.turn_timeout)
        try:
            iid = plan["cells"]["C04"]["order"][-1]
            pr.launch([("C04", iid)])
            pr.wait([pr.state["jobs"][iid]["job"]])
            job = pr.engine.get(pr.state["jobs"][iid]["job"])
            print("order", iid, "status", job["status"])
            for t in job["turn_records"]:
                print(f"  step {t['step']} {t['actor']}: ok={t['ok']} {t['seconds']}s tokens={t['total_tokens']} "
                      f"(in {t['input_tokens']}, cache read {t['cache_read_tokens']}, out {t['output_tokens']})")
            for e in job["events"]:
                if e["kind"] == "error":
                    print("  ERROR:", e["text"][:600])
            for art in job["artifacts"]:
                try:
                    _json.loads(art["content"])
                    print(f"  {art['name']}: valid JSON, {len(art['content'])} chars")
                except ValueError:
                    print(f"  {art['name']}: NOT valid JSON")
            measured = all(t["total_tokens"] and not t["estimated"] for t in job["turn_records"])
            if not measured:
                print("  A turn reported no usage: the cap would be estimating, not measuring. Fix before stage 0.")
            units = sum(t["units"] or 0 for t in job["turn_records"])
            print(f"  units for this order: {units:,.0f} -> about {int(6_000_000 // max(units, 1))} orders fit "
                  f"in stage 0's 6M and {int(10_000_000 // max(units, 1))} in 10M (one order; costs vary)")
            ok = job["status"] == "completed" and measured
            print("SMOKE", "PASS" if ok else "FAIL")
            return 0 if ok else 1
        finally:
            pr.close()
    elif a.command == "wave":
        from . import wave
        path = wave.write(repo, out, a.token_cap, a.workers, a.stage)
        print(path)
    elif a.command == "report":
        if not a.run_id:
            p.error("--run-id is required")
        dest, s = report.write(repo, out, a.run_id)
        print(dest)
        print({k: s[k] for k in ("orders_launched", "orders_scored_with_review", "units_total", "plants")})
    return 0


if __name__ == "__main__":
    sys.exit(main())

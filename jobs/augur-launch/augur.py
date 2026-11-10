"""Augur: no agent wave launches until its plan passes the checks the project's own lessons demand.

Named for the Roman augurs, who took the auspices before every public undertaking and could halt it. On
2026-11-09/10 an overnight Codex wave spent about half the owner's weekly allowance for 12 filed claims. The
warnings already existed and the coordinator had cited most of them in the wave's own prompts:
- Carnot's measured coordination waste;
- Bentham's "pre-1937 strata have no measured yield";
- a 0-of-30 undecided probe;
- Montfaucon's 0 of 50.
Nothing checked the plan against them at the moment of decision. The author approved his own plan, the objective
drifted to "use the allowance", and a never-run configuration went straight to five lanes.
(Kean F-20261110-mommsen-unranked-pools, F-20261110-codex-token-split.)

A lessons register that people must remember to search fails. GAO-02-195 found 23% of NASA managers had ever
contributed to the agency's lessons system. Augur pushes the lessons to the decision instead, and blocks:

1. Outcome objective. The plan names an outcome metric. A spend or activity objective is refused.
2. Bentham only. Every action is in jobs/bentham/output/PLAN.json, and none ranks below the dossiers-per-dollar
   floor unless it runs as a probe. An unmeasured action runs only as a probe: one lane and at most 30 orders.
3. Forecast. Expected filed dossiers and cost come from Bentham's measured rates and are written into the receipt.
4. Ramp. A configuration (orchestrator plus model families) with no measured run passing the floor launches only
   at stage 0: one lane, at most 30 orders, a small budget. Stage 1 needs a measured stage-0 run in
   CONFIGURATIONS.json; stage 2 needs a measured stage-1 run.
5. Lessons pushed, not pulled. Every Kean finding that matches the plan's actions, models or orchestrator with a
   verdict of failed, stopped_at_gate or partly_worked must be answered in the plan, one finding id at a time.
6. Pre-mortem. At least three concrete ways this wave could fail, each with the plan's guard against it.
7. Independent review. A reviewer of a different model family from the author, or the owner, signs a receipt
   bound to the plan's hash.
8. Limits. Every supervisor limit is set, the budget fits the stage, and the lane count fits the plan.

  python -I jobs/augur-launch/augur.py check PLAN.json [--write-receipt RECEIPT.json]
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
BENTHAM_PLAN = "jobs/bentham/output/PLAN.json"
FINDINGS = "jobs/kean/register/findings.jsonl"
CONFIGS = "jobs/augur-launch/CONFIGURATIONS.json"

OUTCOME_METRICS = {"filed_dossiers_per_unit", "ready_gain_per_unit", "verified_claims_per_unit"}
SPEND_WORDS = re.compile(r"\b(burn\w*|deplet\w*|exhaust\w*|use (up )?(all |the |my |our )?(\w+ )?(budget|allowance|usage|quota|tokens)"
                         r"|spend (the|all|it)|keep \w+ (busy|running)|utili[sz]ation|max(imi[sz]e)? (spend|usage|tokens))\b", re.I)
FLOOR_PER_USD = 0.2          # dossiers per API-equivalent dollar; Bentham's no.fr pool (0.10) is below it
PROBE_ORDERS = 30
STAGE_CAPS = {0: {"lanes": 1, "orders": 30, "budget_units": 6_000_000},
              1: {"lanes": 3, "orders": 300, "budget_units": 40_000_000},
              2: {"lanes": 12, "orders": 10 ** 6, "budget_units": 10 ** 12}}
LIMIT_KEYS = ("chain_budget_units", "spend_per_claim_units", "no_claim_minutes", "context_kill_tokens",
              "reviews_per_hour", "coordinator_units_per_hour")
WARN_VERDICTS = {"failed", "stopped_at_gate", "partly_worked"}
FAMILIES = {"claude": "anthropic", "opus": "anthropic", "sonnet": "anthropic", "haiku": "anthropic", "fable": "anthropic",
            "gpt": "openai", "codex": "openai", "sol": "openai", "astra": "openai", "luna": "openai", "terra": "openai",
            "owner": "owner"}


def family(name):
    low = str(name or "").lower()
    for key, fam in FAMILIES.items():
        if key in low:
            return fam
    return low or "unknown"


def plan_sha(plan):
    body = {k: v for k, v in plan.items() if k != "review"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def fingerprint(plan):
    c = plan.get("configuration") or {}
    return "|".join([str(c.get("orchestrator", "")).lower(), family(c.get("coordinator_model")),
                     family(c.get("producer_model"))])


def tags(plan):
    """Words the plan's lessons are filed under: its action ids, models and orchestrator."""
    c = plan.get("configuration") or {}
    words = set()
    for a in plan.get("actions") or []:
        words.update(w for w in re.split(r"[._\-]", str(a.get("id", "")).lower()) if len(w) > 2)
    for v in (c.get("orchestrator"), c.get("coordinator_model"), c.get("producer_model")):
        words.update(w for w in re.split(r"[^a-z0-9]+", str(v or "").lower()) if len(w) > 2)
    words.update({family(c.get("coordinator_model")), family(c.get("producer_model"))} - {"unknown"})
    words.update({"coordinator", "waste", "probe"})
    words -= {"production", "claim", "ready", "the", "and", "gpt"}
    return words


def latest_findings(repo):
    rows = {}
    for line in (Path(repo) / FINDINGS).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if r["id"] not in rows or r.get("rev", 0) >= rows[r["id"]].get("rev", 0):
                rows[r["id"]] = r
    return rows


def matching_findings(repo, plan, limit=15):
    want = tags(plan)
    hits = []
    for r in latest_findings(repo).values():
        if r.get("verdict") not in WARN_VERDICTS:
            continue
        keys = {str(k).lower() for k in r.get("keywords") or []}
        text = " ".join(str(r.get(k, "")) for k in ("tried", "result", "lesson")).lower()
        action_named = any(str(a.get("id", "")).lower() in text for a in plan.get("actions") or [])
        if keys & want or action_named:
            hits.append(r)
    hits.sort(key=lambda r: (r.get("date", ""), r["id"]), reverse=True)
    return hits[:limit]


def bentham_actions(repo):
    p = json.loads((Path(repo) / BENTHAM_PLAN).read_text(encoding="utf-8"))
    return {a["id"]: (a, group) for group in ("ranked", "unranked") for a in p.get(group) or []}


def measured_stage(repo, fp):
    """Highest stage this configuration has passed (-1 if none): runs recorded in CONFIGURATIONS.json."""
    path = Path(repo) / CONFIGS
    runs = json.loads(path.read_text(encoding="utf-8")).get("runs", []) if path.exists() else []
    passed = [r.get("stage", 0) for r in runs if r.get("fingerprint") == fp and r.get("passed") is True
              and isinstance(r.get("finding"), str) and r["finding"].startswith("F-")]
    return max(passed) if passed else -1


def check(plan, repo=REPO):
    """(refusals, receipt). An empty refusal list is a pass."""
    no = []
    obj = plan.get("objective") or {}
    if obj.get("metric") not in OUTCOME_METRICS:
        no.append(f"objective.metric must be an outcome metric, one of {sorted(OUTCOME_METRICS)}")
    if SPEND_WORDS.search(json.dumps(obj)):
        no.append("objective names spend or activity as a goal; spend is a limit, never an objective")

    actions = bentham_actions(repo)
    stage = plan.get("stage")
    if stage not in STAGE_CAPS:
        no.append("stage must be 0, 1 or 2")
        stage = 0
    total_orders = total_lanes = 0
    forecast = {"filed": 0.0, "usd": 0.0, "by_action": {}}
    for a in plan.get("actions") or []:
        aid, orders, lanes = a.get("id"), int(a.get("orders") or 0), int(a.get("lanes") or 0)
        total_orders += orders
        total_lanes += lanes
        if aid not in actions:
            no.append(f"action {aid!r} is not in Bentham's plan ({BENTHAM_PLAN})")
            continue
        item, group = actions[aid]
        probe = aid.startswith("probe.") or group == "unranked" or item.get("unranked")
        rate = (item.get("rate") or {}).get("value")
        per_usd = item.get("per_usd")
        if probe or rate is None:
            if orders > PROBE_ORDERS or lanes > 1:
                no.append(f"{aid} is unmeasured: one lane and at most {PROBE_ORDERS} orders until Bentham measures it")
        elif per_usd is not None and per_usd != float("inf") and per_usd < FLOOR_PER_USD:
            no.append(f"{aid} yields {per_usd:.2f} dossiers per dollar, below the floor {FLOOR_PER_USD}; run it only as a probe")
        if orders > (item.get("orders") or 0):
            no.append(f"{aid}: {orders} orders planned but Bentham lists {item.get('orders')}")
        cost = orders * ((item.get("cost_usd") or 0) / item["orders"]) if item.get("orders") else 0.0
        filed = orders * (rate or 0.0)
        forecast["by_action"][aid] = {"orders": orders, "expected_filed": round(filed, 1), "expected_usd": round(cost, 2),
                                      "rate_basis": item.get("rate")}
        forecast["filed"] += filed
        forecast["usd"] += cost
    if not plan.get("actions"):
        no.append("the plan names no Bentham action")

    fp = fingerprint(plan)
    passed = measured_stage(repo, fp)
    if stage > passed + 1:
        no.append(f"configuration {fp!r} has passed stage {passed}; it may launch at stage {passed + 1} at most")
    caps = STAGE_CAPS[stage]
    limits = plan.get("limits") or {}
    missing = [k for k in LIMIT_KEYS if not isinstance(limits.get(k), (int, float)) or limits[k] <= 0]
    if missing:
        no.append("limits missing: " + ", ".join(missing))
    if total_lanes > caps["lanes"]:
        no.append(f"stage {stage} allows {caps['lanes']} lanes; the plan has {total_lanes}")
    if total_orders > caps["orders"]:
        no.append(f"stage {stage} allows {caps['orders']} orders; the plan has {total_orders}")
    if (limits.get("chain_budget_units") or 0) > caps["budget_units"]:
        no.append(f"stage {stage} allows a budget of {caps['budget_units']} units; the plan asks {limits.get('chain_budget_units')}")

    answered = plan.get("acknowledged_findings") or {}
    lessons = matching_findings(repo, plan)
    for r in lessons:
        how = answered.get(r["id"])
        if not isinstance(how, str) or len(how.strip()) < 25:
            no.append(f"unanswered lesson {r['id']} [{r.get('verdict')}]: {r.get('lesson', '')[:160]}")

    pm = plan.get("premortem") or []
    good = [p for p in pm if isinstance(p, dict) and len(str(p.get("failure", ""))) >= 20 and len(str(p.get("guard", ""))) >= 20]
    if len(good) < 3:
        no.append("premortem needs at least 3 entries, each a concrete failure and the guard against it")

    review = plan.get("review") or {}
    sha = plan_sha(plan)
    author_fam = family(plan.get("author"))
    reviewer_fam = family(review.get("reviewer"))
    if review.get("plan_sha256") != sha:
        no.append("review must be bound to this plan: review.plan_sha256 = " + sha)
    elif review.get("verdict") != "approve":
        no.append("review verdict is not approve")
    elif reviewer_fam == author_fam and reviewer_fam != "owner":
        no.append(f"reviewer ({review.get('reviewer')}) is the author's model family ({author_fam}); use another family or the owner")

    receipt = {"schema": "augur-receipt/v1", "plan_sha256": sha, "verdict": "PASS" if not no else "REFUSE",
               "stage": stage, "configuration": fp, "configuration_passed_stage": passed,
               "forecast": {"expected_filed": round(forecast["filed"], 1), "expected_usd": round(forecast["usd"], 2),
                            "by_action": forecast["by_action"]},
               "lessons_checked": [r["id"] for r in lessons], "refusals": no}
    return no, receipt


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("plan", type=Path)
    c.add_argument("--write-receipt", type=Path)
    c.add_argument("--repo", type=Path, default=REPO)
    s = sub.add_parser("sha", help="print the hash a reviewer signs")
    s.add_argument("plan", type=Path)
    a = ap.parse_args(argv)
    plan = json.loads(a.plan.read_text(encoding="utf-8"))
    if a.cmd == "sha":
        print(plan_sha(plan))
        return 0
    refusals, receipt = check(plan, a.repo)
    if a.write_receipt:
        a.write_receipt.write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=1))
    return 0 if not refusals else 2


if __name__ == "__main__":
    sys.exit(main())

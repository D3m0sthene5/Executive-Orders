"""Bentham: where should the next agent tokens go?

Joins what the project already measures into one ranked plan, so nobody has to feed the tools by hand:

  measure.py     yield per attempted order and API-equivalent cost per order, from wave dispositions and
                 Hamilton-style token telemetry
  candidates.py  every action available now (production strata, recoveries, source acquisitions with the orders
                 they unlock, zero-agent steps), from the readiness tracker, Polya and the shared-unlock table
  gate.py        the stop rule a running wave consults after each batch
  sessions.py    automatic token capture from this machine's Claude Code transcripts (feeds the next measure)

Score of an action = (expected dossiers now + fecundity) / expected cost, where fecundity is the dossiers the
action makes possible later (unlocked orders x their stratum's measured yield), discounted for delay. Machine and
zero-agent actions cost no model tokens and are listed first. Nothing here changes a status, a claim or a count.

    python3 -I jobs/bentham/bentham.py plan [--budget-usd N] [--out DIR]
    python3 -I jobs/bentham/bentham.py gate --action ID --batches FILE
    python3 -I jobs/bentham/bentham.py usage --wave NAME --phase LABEL
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("REPO_ROOT", HERE.parents[1])).resolve()
sys.path.insert(0, str(HERE))

# Delay discount: an unlock that pays off in d days is worth exp(-d / HALF_LIFE_DAYS * ln 2) of one paid now.
# No measured time preference exists for this project; 60 days is a working value. The plan is recomputed at
# 30 and 180 days and any action whose rank moves across the budget line is flagged.
HALF_LIFE_DAYS = 60
# Orders in a probe of an unmeasured stratum: the gate's minimum before it judges a wave.
PROBE_ORDERS = 30
SENSITIVITY_HALF_LIVES = (30, 180)
ALLOWANCE = HERE / "data" / "ALLOWANCE.json"


def discount(days, half_life=HALF_LIFE_DAYS):
    return math.exp(-max(0.0, float(days or 0)) / half_life * math.log(2))


def rate_of(measured, key):
    for row in measured.get("rates", []):
        if row.get("key") == key and isinstance(row.get("value"), (int, float)):
            return row
    return None


def cost_of(measured, action):
    if action.get("cost_override_usd") is not None:
        return float(action["cost_override_usd"]), "machine or zero-agent work: no model tokens"
    c = (measured.get("costs") or {}).get(action.get("cost_key") or "")
    if not c or not isinstance(c.get("usd"), (int, float)):
        return None, f"no measured cost for {action.get('cost_key')!r}"
    return float(c["usd"]) * float(action.get("orders") or 0), f"{action['orders']} x {c['usd']:.2f} USD ({c.get('per')})"


def score(measured, action, half_life=HALF_LIFE_DAYS):
    """Expected dossiers now, fecundity, cost and their quotient for one action; None where unmeasured."""
    out = {"id": action["id"], "kind": action.get("kind"), "orders": action.get("orders", 0),
           "description": action.get("description", ""), "notes": []}
    now = 0.0
    if action.get("orders"):
        r = rate_of(measured, action.get("rate_key"))
        if r is None:
            out["notes"].append(f"no measured yield for {action.get('rate_key')!r}: unranked")
            out["unranked"] = True
        else:
            now = float(action["orders"]) * float(r["value"])
            out["rate"] = {"key": r["key"], "value": r["value"], "num": r.get("num"), "den": r.get("den"),
                           "source": r.get("source")}
    fec = 0.0
    for u in action.get("unlocks") or []:
        r = rate_of(measured, u.get("rate_key"))
        if r is None:
            out["notes"].append(f"unlock yield {u.get('rate_key')!r} unmeasured; fecundity omitted for it")
            continue
        fec += float(u.get("orders") or 0) * float(r["value"]) * discount(u.get("delay_days"), half_life)
    cost, basis = cost_of(measured, action)
    unit = (measured.get("costs") or {}).get(action.get("cost_key") or "") or {}
    if isinstance(unit.get("usd"), (int, float)):
        out["probe_cost_usd"] = round(float(unit["usd"]) * min(PROBE_ORDERS, int(action.get("orders") or 0)), 2)
    if cost is None:
        out["notes"].append(basis + ": unranked")
        out["unranked"] = True
    out.update(expected_now=round(now, 1), fecundity=round(fec, 1), value=round(now + fec, 1),
               cost_usd=None if cost is None else round(cost, 2), cost_basis=basis)
    if cost is not None and not out.get("unranked"):
        out["per_usd"] = math.inf if cost == 0 and now + fec > 0 else (0.0 if cost == 0 else (now + fec) / cost)
    return out


def order_plan(scored, budget=None):
    ranked = sorted((s for s in scored if "per_usd" in s), key=lambda s: (-s["per_usd"], s["cost_usd"]))
    spent, cum = 0.0, 0.0
    for s in ranked:
        within = budget is None or s["cost_usd"] == 0 or spent + s["cost_usd"] <= budget
        s["within_budget"] = within
        if within:
            spent += s["cost_usd"]
            cum += s["value"]
        s["cumulative_usd"], s["cumulative_value"] = round(spent, 2), round(cum, 1)
    return ranked, [s for s in scored if "per_usd" not in s]


def allowance():
    """Measured API-equivalent dollars per week of the owner's plan, if recorded; else None (not published)."""
    try:
        data = json.loads(ALLOWANCE.read_text())
        v = data.get("usd_per_week")
        return (float(v), data) if isinstance(v, (int, float)) and v > 0 else (None, data)
    except (OSError, ValueError):
        return None, {}


def plan(args):
    import candidates as C
    import measure as M
    measured = M.measure(REPO)
    cands = C.candidates(REPO)
    scored = [score(measured, a) for a in cands["actions"]]
    ranked, unranked = order_plan(scored, args.budget_usd)
    flips = []
    for hl in SENSITIVITY_HALF_LIVES:
        alt, _ = order_plan([score(measured, a, hl) for a in cands["actions"]], args.budget_usd)
        a_in = {s["id"] for s in alt if s["within_budget"]}
        b_in = {s["id"] for s in ranked if s["within_budget"]}
        if a_in != b_in:
            flips.append({"half_life_days": hl, "enters": sorted(a_in - b_in), "leaves": sorted(b_in - a_in)})
    week, adata = allowance()
    for s in ranked:
        s["share_of_week"] = None if week is None or s["cost_usd"] is None else round(s["cost_usd"] / week, 3)
    out = Path(args.out or os.environ.get("OUTPUT_DIR") or HERE / "output")
    out.mkdir(parents=True, exist_ok=True)
    result = {"ranked": ranked, "unranked": unranked, "budget_usd": args.budget_usd,
              "discount_half_life_days": HALF_LIFE_DAYS, "sensitivity": flips,
              "allowance": adata or {"usd_per_week": None, "note": "not recorded; see README"},
              "price_table": measured.get("price_table"), "waves": measured.get("waves"),
              "what_this_is_not": "A ranking of expected yield per API-equivalent dollar from measured past waves. "
                                  "It changes no status, claim or count and authorizes no dispatch by itself."}
    (out / "PLAN.json").write_text(json.dumps(result, indent=2, default=str) + "\n")
    (out / "MEASURED.json").write_text(json.dumps(measured, indent=2) + "\n")
    (out / "CANDIDATES.json").write_text(json.dumps(cands, indent=2) + "\n")
    (out / "PLAN.md").write_text(report(result))
    print(report(result))
    return result


def fmt_usd(v):
    return "free" if v == 0 else f"${v:,.0f}"


def report(r):
    lines = ["# Bentham plan: where the next agent tokens go", "",
             "Ranked by expected dossiers (now plus those the action makes possible later, discounted at a "
             f"{r['discount_half_life_days']}-day half-life) per API-equivalent dollar, from measured past waves.", ""]
    if r["allowance"].get("usd_per_week"):
        lines.append(f"Weekly allowance recorded: ${r['allowance']['usd_per_week']:,.0f} API-equivalent "
                     f"({r['allowance'].get('basis', '')}).")
    else:
        lines.append("Weekly allowance: not recorded, so no percent-of-week figures. Record one measured week in "
                     "`jobs/bentham/data/ALLOWANCE.json` (see README).")
    lines += ["", "| # | Action | Kind | Orders | Dossiers now | Later (fecundity) | Cost | Dossiers per $100 | Cumulative cost |",
              "|---:|---|---|---:|---:|---:|---:|---:|---:|"]
    for i, s in enumerate(r["ranked"], 1):
        per = "∞" if s["per_usd"] == math.inf else f"{100 * s['per_usd']:.1f}"
        mark = "" if s.get("within_budget", True) else " (over budget)"
        lines.append(f"| {i} | {s['id']}{mark} | {s['kind']} | {s['orders']} | {s['expected_now']} | {s['fecundity']} | "
                     f"{fmt_usd(s['cost_usd'])} | {per} | {fmt_usd(s['cumulative_usd'])} |")
    if r["unranked"]:
        lines += ["", "Unranked (a yield or cost is not measured; Bentham will not guess). For a production stratum the "
                  f"next step is a {PROBE_ORDERS}-order probe, run under the gate, that measures its yield:", ""]
        for s in r["unranked"]:
            probe = ""
            if s.get("kind") == "production" and s.get("probe_cost_usd") is not None:
                probe = f" Probe: {PROBE_ORDERS} orders, about {fmt_usd(s['probe_cost_usd'])}."
            lines.append(f"- {s['id']} ({s['orders']} orders): {'; '.join(s['notes'])}.{probe}")
    if r["sensitivity"]:
        lines += ["", "Budget line moves with the delay discount:", ""]
        lines += [f"- at {f['half_life_days']} days: enters {f['enters'] or 'none'}, leaves {f['leaves'] or 'none'}"
                  for f in r["sensitivity"]]
    else:
        lines += ["", "The choice of actions within budget does not change between 30- and 180-day discounts."]
    lines += ["", "Each production action runs in batches under `bentham.py gate`, which stops it when its observed "
              "yield per dollar falls below the next action's.", ""]
    return "\n".join(lines) + "\n"


def gate(args):
    import gate as G
    prior = json.loads((HERE / "output" / "PLAN.json").read_text())
    ranked = prior["ranked"]
    me = next((s for s in ranked if s["id"] == args.action), None)
    if me is None or "rate" not in me:
        sys.exit(f"{args.action}: not a ranked production action in output/PLAN.json; run `plan` first")
    after = [s for s in ranked[ranked.index(me) + 1:] if s.get("per_usd") not in (None, math.inf)]
    next_best = after[0]["per_usd"] if after else 0.0
    per_attempt = me["cost_usd"] / max(1, me["orders"])
    batches = G.load_batches(args.batches) if hasattr(G, "load_batches") else json.loads(Path(args.batches).read_text())
    verdict = G.decide(batches, prior_rate=me["rate"]["value"], prior_strength=args.prior_strength,
                       cost_per_attempt=per_attempt, next_best_value_per_usd=next_best, window=args.window)
    verdict.update(action=me["id"], prior_rate=me["rate"]["value"], next_best=after[0]["id"] if after else None,
                   next_best_value_per_usd=next_best)
    print(json.dumps(verdict, indent=2, default=str))
    return verdict


def usage(args):
    cmd = [sys.executable, "-I", str(HERE / "sessions.py"), "--wave", args.wave, "--phase", args.phase,
           "--out", args.out or str(REPO / "research" / "bentham" / "usage" / args.wave)]
    return subprocess.run(cmd).returncode


def calibrate(args):
    """Record what a week of the owner's plan buys, from one measured run (Anthropic does not publish it)."""
    if args.percent_used <= 0:
        sys.exit("--percent-used must be the positive change in the weekly usage figure across the run")
    week = args.run_usd / (args.percent_used / 100.0)
    ALLOWANCE.parent.mkdir(parents=True, exist_ok=True)
    data = {"usd_per_week": round(week, 2),
            "basis": f"run of {args.run_usd:.2f} USD API-equivalent moved the weekly figure by {args.percent_used}%",
            "run": args.run, "recorded_by": args.by, "plan_name": args.plan_name}
    ALLOWANCE.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("plan")
    s.add_argument("--budget-usd", type=float)
    s.add_argument("--out")
    s = sub.add_parser("gate")
    s.add_argument("--action", required=True)
    s.add_argument("--batches", required=True)
    s.add_argument("--prior-strength", type=float, default=20)
    # Judge the last two batches: on the 2026-11-04 replay a pooled gate never reacted to the o23-o24 collapse,
    # while a two-batch window stopped at o23 (9 of 60 filed).
    s.add_argument("--window", type=int, default=2)
    s = sub.add_parser("usage")
    s.add_argument("--wave", required=True)
    s.add_argument("--phase", required=True)
    s.add_argument("--out")
    s = sub.add_parser("calibrate", help="record a measured weekly allowance")
    s.add_argument("--run-usd", type=float, required=True, help="API-equivalent cost of the run (from usage)")
    s.add_argument("--percent-used", type=float, required=True, help="change in Settings > Usage weekly percent")
    s.add_argument("--run", required=True)
    s.add_argument("--by", required=True)
    s.add_argument("--plan-name", default="")
    a = p.parse_args(argv)
    return {"plan": plan, "gate": gate, "usage": usage, "calibrate": calibrate}[a.cmd](a)


if __name__ == "__main__":
    main()

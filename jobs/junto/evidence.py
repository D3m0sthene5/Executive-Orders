#!/usr/bin/env python3
"""Rumford: measured waste in the project's own wave telemetry, ranked for testing.

Named for Count Rumford (Benjamin Thompson), who measured where the heat of a fire was lost
before he redesigned the fireplace. Junto's finders need raw session pages kept outside the
repository, so in practice nobody fed them: by 2026-11-09 Junto had 21 untested candidates
from 2026-10-20 and no test. Meanwhile `bentham.py usage` commits sanitized per-agent usage
for every wave to research/bentham/usage/<wave>/AGENT_USAGE.csv. Rumford reads that, prices
each row at list price (jobs/necker-costs/PRICES.json), and measures three signals tied to
existing saver keys:

  lean_coordination      the main sessions' share of a wave's cost (Bentham labels every main
                         session "coordinator", including lane sessions that did the work
                         themselves; that is work not delegated to cheaper workers)
  revere_phase_handoff   coordinator calls that carry a very large context
  idle_cache_avoidance   coordinators that sit idle while holding a 1-hour cache

What it reports is **cost at stake**: measured dollars spent in the pattern. It is not a
saving, and it never enters a Junto score. Only `junto.py add-test` with two measured arms
can verify a saving. OPEN_TESTS.md lists the savers in order of cost at stake, each with the
two-arm test that would settle it.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

USAGE_GLOB = "research/bentham/usage/*/AGENT_USAGE.csv"
PRICES = "jobs/necker-costs/PRICES.json"
COORDINATOR_SHARE = 0.5          # main sessions above half of a wave's cost are flagged
LARGE_CONTEXT_TOKENS = 300_000   # mean cache read per call above this is a very large context
IDLE_ACTIVE_RATIO = 0.3          # active / wall below this with a 1-hour cache held is idle holding
TOKEN_FIELDS = ("fresh_input", "cache_read", "cache_write_5m", "cache_write_1h", "cache_write_unclassified", "output")

SAVERS = {
    "lean_coordination": {
        "what": "Main sessions (Bentham's 'coordinator' rows) that do bounded work themselves, poll GitHub, or carry "
                "long turns: delegate bounded tasks to cheaper workers, wait with one background watcher, keep turns short.",
        "unit": "filed claim (or completed task)",
        "test": "Two comparable waves on the same route (same claim-kit route, same reviewer setup): one run as before, "
                "one with the lean-coordination brief. Compare coordinator plus worker dollars per filed claim, and "
                "rejects per attempt (quality must not fall).",
        # Gutenberg (2026-11-09): the tool and the ready test. No saving is claimed until add-test measures one.
        "tool": "jobs/carnot-coordinator/PROTOCOL.md sections 1-2 (worker.py, await_run.py)",
        "candidate": "C-20261109-1",
        "arms": {"before": "a wave whose prompt does not include PROTOCOL.md (the Cujas or Haloander shape)",
                 "after": "the next wave on the same route whose prompt includes PROTOCOL.md"},
        "matched_on": "same route (Haloander h01 page check), batch size 25, same producer and reviewer models, "
                      "planted controls 2 per batch, same budget cap",
        "measure": "bentham.py usage --wave W --phase P --reported-costs RUN/COSTS.log per arm; units = filed claims; "
                   "accepted/rejected = blind-review verdicts",
        "add_test": "junto.py add-test --candidate C-20261109-1 --unit-of-work filed_claim --matched-on '<as above>' "
                    "--before-usd X --before-units N --before-session S --before-accepted A --before-rejected R "
                    "--after-usd Y --after-units M --after-session T --after-accepted B --after-rejected Q "
                    "--test-cost-usd 0 --complete-costs",
    },
    "revere_phase_handoff": {
        "what": "End a long coordinator context at a phase boundary and continue in a fresh session from the "
                "handoff notes (Revere), instead of carrying hundreds of thousands of tokens into every call.",
        "unit": "coordinator call",
        "test": "Same wave phase run twice: once continuing the long session, once handed off to a fresh session at "
                "the phase boundary. Compare coordinator dollars per completed batch.",
        "tool": "jobs/carnot-coordinator/handoff.py (context check at 300,000 tokens per call; write packet)",
        "candidate": "C-20261020-1",
        "arms": {"before": "batch k+1 run in the coordinator session that ran batch k (context > 300k per call)",
                 "after": "batch k+1 run by a fresh coordinator from handoff.py's packet"},
        "matched_on": "consecutive batches of one wave, same route and models, same batch size; the fresh arm's setup "
                      "(reading the packet and checking out inputs) is counted in its cost",
        "measure": "bentham.py usage with --session-id per arm; units = completed batches (filed or reviewed)",
        "add_test": "junto.py add-test --candidate C-20261020-1 --unit-of-work completed_batch --matched-on '<as above>' "
                    "--before-usd X --before-units 1 --before-session S --after-usd Y --after-units 1 "
                    "--after-session T --test-cost-usd 0 --complete-costs",
    },
    "idle_cache_avoidance": {
        "what": "Do not hold a 1-hour prompt cache across long idle waits; let it lapse or end the turn and resume.",
        "unit": "coordinator hour",
        "test": "Two waits of the same length on the same kind of GitHub run: one holding the session, one ending the "
                "turn and resuming. Compare dollars per hour of wait.",
        "tool": "jobs/carnot-coordinator/await_run.py (background, ends the turn) and handoff.py for waits over ~55 min",
        "candidate": "C-20261020-2",
        "arms": {"before": "a coordinator that waits on a multi-hour run in its session (checks or a held turn)",
                 "after": "a coordinator that writes a packet and stops; a fresh session resumes when await_run exits"},
        "matched_on": "the same workflow (run-jobs daily selection or a claim-kit rebuild), waits within 20% of each "
                      "other in length, the same coordinator model",
        "measure": "dollars from the end of dispatch to the first productive call after the run ends (cache writes "
                   "and reads of the resume included), per wait hour",
        "add_test": "junto.py add-test --candidate C-20261020-2 --unit-of-work wait_hour --matched-on '<as above>' "
                    "--before-usd X --before-units H1 --before-session S --after-usd Y --after-units H2 "
                    "--after-session T --test-cost-usd 0 --complete-costs",
    },
}


def load_prices(repo):
    data = json.loads((Path(repo) / PRICES).read_text(encoding="utf-8"))
    return [(re.compile(m["match"]), m) for m in data["models"]]


def price(row, prices):
    """API list-price dollars for one usage row, or None for an unpriced model.

    Gutenberg: a row Bentham priced per call (``usd_list``: exact model, fast mode, Haiku long prompts) keeps that
    total; its category split is still taken from the table, scaled to that total.
    """
    model = (row.get("model") or "").strip()
    pre = row.get("usd_list")
    if pre not in (None, ""):
        usd, parts = price(dict(row, usd_list=""), prices)
        if usd is None:
            return float(pre), {k: 0.0 for k in TOKEN_FIELDS}
        scale = float(pre) / usd if usd else 0.0
        return float(pre), {k: v * scale for k, v in parts.items()}
    for pattern, m in prices:
        if pattern.search(model):
            n = {k: float(row.get(k) or 0) for k in TOKEN_FIELDS}
            usd = (n["fresh_input"] * m["input"] + n["cache_read"] * m["cache_read"]
                   + (n["cache_write_5m"] + n["cache_write_unclassified"]) * m["cache_write_5m"]
                   + n["cache_write_1h"] * m["cache_write_1h"] + n["output"] * m["output"]) / 1e6
            return usd, {k: v * m.get({"fresh_input": "input", "cache_write_unclassified": "cache_write_5m"}.get(k, k), 0) / 1e6
                         for k, v in n.items()}
    return None, None


KEAN = "jobs/kean/kean.py"


def kean_measures(repo):
    """{wave: measures} from Kean findings (jobs/kean/kean.py wave_measures), or {} when Kean is absent."""
    import importlib.util
    path = Path(repo) / KEAN
    if not path.is_file():
        return {}
    spec = importlib.util.spec_from_file_location("kean_for_junto", path)
    K = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(K)
    return K.wave_measures(K.load(K.Repo(str(repo)), "findings"))


def measure(repo):
    repo = Path(repo)
    prices = load_prices(repo)
    waves, unpriced = [], {}
    for path in sorted(repo.glob(USAGE_GLOB)):
        rows = list(csv.DictReader(path.open(encoding="utf-8", newline="")))
        if not rows:
            continue
        wave = {"wave": path.parent.name, "source": path.relative_to(repo).as_posix(), "agents": len(rows),
                "usd": 0.0, "coordinator_usd": 0.0, "large_context_cache_read_usd": 0.0,
                "idle_cache_hold_usd": 0.0, "large_context_calls": 0, "coordinator_calls": 0}
        for r in rows:
            usd, parts = price(r, prices)
            if usd is None:
                unpriced[r.get("model") or "?"] = unpriced.get(r.get("model") or "?", 0) + 1
                continue
            wave["usd"] += usd
            if r.get("role") != "coordinator":
                continue
            wave["coordinator_usd"] += usd
            calls = int(float(r.get("calls") or 0))
            wave["coordinator_calls"] += calls
            if calls and float(r.get("cache_read") or 0) / calls > LARGE_CONTEXT_TOKENS:
                wave["large_context_cache_read_usd"] += parts["cache_read"]
                wave["large_context_calls"] += calls
            wall, active = float(r.get("wall_seconds") or 0), r.get("active_seconds")
            if active not in (None, "") and wall > 0 and float(active) / wall < IDLE_ACTIVE_RATIO:
                wave["idle_cache_hold_usd"] += parts["cache_write_1h"]
        wave["coordinator_share"] = round(wave["coordinator_usd"] / wave["usd"], 3) if wave["usd"] else None
        for k in ("usd", "coordinator_usd", "large_context_cache_read_usd", "idle_cache_hold_usd"):
            wave[k] = round(wave[k], 2)
        waves.append(wave)
    # Gutenberg item 5: waves known only from Kean findings' structured measures (no committed usage table).
    have = {w["wave"] for w in waves}
    for name, m in sorted(kean_measures(repo).items()):
        usd = m.get("usd") or {}
        roles = usd.get("by_role") or {}
        total = usd.get("total", sum(roles.values()) if roles else None)
        if name in have or total is None or "coordinator" not in roles:
            continue
        waves.append({"wave": name, "source": "Kean " + m["finding"], "agents": None, "usd": round(total, 2),
                      "coordinator_usd": round(roles["coordinator"], 2), "large_context_cache_read_usd": 0.0,
                      "idle_cache_hold_usd": 0.0, "large_context_calls": 0, "coordinator_calls": None,
                      "coordinator_share": round(roles["coordinator"] / total, 3) if total else None,
                      "note": "from Kean measures: coordinator share only; per-call patterns need a usage table"})
    at_stake = {
        "lean_coordination": [(w["wave"], w["coordinator_usd"]) for w in waves
                              if w["coordinator_share"] is not None and w["coordinator_share"] > COORDINATOR_SHARE],
        "revere_phase_handoff": [(w["wave"], w["large_context_cache_read_usd"]) for w in waves if w["large_context_calls"]],
        "idle_cache_avoidance": [(w["wave"], w["idle_cache_hold_usd"]) for w in waves if w["idle_cache_hold_usd"] > 0],
    }
    savers = []
    for key, hits in at_stake.items():
        savers.append(dict(SAVERS[key], saver_key=key, status="unverified",
                           cost_at_stake_usd=round(sum(v for _, v in hits), 2),
                           waves=[{"wave": w, "usd": round(v, 2)} for w, v in hits]))
    savers.sort(key=lambda s: -s["cost_at_stake_usd"])
    return {"schema": "junto.rumford/1", "what_this_is": (
                "Measured dollars spent in each pattern (cost at stake), from committed Bentham usage. Not a saving; "
                "never a Junto score. Only junto.py add-test with two measured arms verifies a saving."),
            "thresholds": {"coordinator_share": COORDINATOR_SHARE, "large_context_tokens_per_call": LARGE_CONTEXT_TOKENS,
                           "idle_active_ratio": IDLE_ACTIVE_RATIO},
            "waves": waves, "savers": savers, "unpriced_models": unpriced}


def render(evidence):
    lines = ["# Junto: untested savers, ranked by measured cost at stake", "",
             evidence["what_this_is"], "",
             "| Saver | Cost at stake | Waves | Test that would settle it |", "|---|---:|---|---|"]
    for s in evidence["savers"]:
        waves = ", ".join(f"{w['wave']} ${w['usd']:.2f}" for w in s["waves"]) or "none measured"
        lines.append(f"| `{s['saver_key']}`: {s['what']} | ${s['cost_at_stake_usd']:.2f} | {waves} | "
                     f"Unit: {s['unit']}. {s['test']} Record with `junto.py add-test`. |")
    lines += ["", "## Ready two-arm tests (Gutenberg, 2026-11-09)", "",
              "Each saver below has a tool a wave coordinator uses (`jobs/carnot-coordinator/PROTOCOL.md`) and a test "
              "ready to run. No saving is claimed for any of them until its test is measured and recorded.", ""]
    for s in evidence["savers"]:
        if not s.get("arms"):
            continue
        lines += [f"### `{s['saver_key']}` ({s['candidate']})", "",
                  f"- Tool: {s['tool']}", f"- Before arm: {s['arms']['before']}", f"- After arm: {s['arms']['after']}",
                  f"- Matched on: {s['matched_on']}", f"- Measure: {s['measure']}", f"- Record: `{s['add_test']}`", ""]
    lines += ["", "| Wave | Agents | Cost | Main-session share | Large-context main-session calls |",
              "|---|---:|---:|---:|---:|"]
    for w in evidence["waves"]:
        share = "n/a" if w["coordinator_share"] is None else f"{w['coordinator_share']:.0%}"
        agents = "" if w["agents"] is None else w["agents"]
        lines.append(f"| {w['wave']} | {agents} | ${w['usd']:.2f} | {share} | {w['large_context_calls']} |")
    if evidence["unpriced_models"]:
        lines += ["", "Unpriced models (tokens not counted): " + ", ".join(f"{k} ({v})" for k, v in evidence["unpriced_models"].items())]
    return "\n".join(lines) + "\n"


def write(repo, out):
    evidence = measure(repo)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "EVIDENCE.json").write_text(json.dumps(evidence, indent=1) + "\n", encoding="utf-8")
    (out / "OPEN_TESTS.md").write_text(render(evidence), encoding="utf-8")
    return evidence


if __name__ == "__main__":
    print(json.dumps(write(".", sys.argv[1] if len(sys.argv) > 1 else "jobs/junto/output")["savers"], indent=1)[:2000])

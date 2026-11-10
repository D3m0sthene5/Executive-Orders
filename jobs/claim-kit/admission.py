"""Admission: claim-kit work only on orders a Bentham action lists.

The owner's rule (2026-11-05, CLAUDE.md) is to spend agent tokens where Bentham says. On 2026-11-09/10 five Codex
lanes were sent, by their prompts and their coordinator, to orders that no Bentham action listed (decided
orders below EO 7532: 57% had no accepted source text). They spent half the owner's weekly Codex allowance and
filed 12 claims. Nothing in the kit stopped them, because the kit never asked which action the work belonged to.

Now `kit.py next` and `batch.prepare` ask. In a checkout that holds Bentham's plan:
- the caller names an action (`--action ID`) that is in jobs/bentham/output/PLAN.json;
- every order must be in that action's list, jobs/bentham/output/strata/<ID>.txt (for `probe.<ID>`, the list of
  <ID>);
- a probe (`probe.*`) or an action Bentham lists as unranked admits at most PROBE_ORDERS orders across all agents,
  counted from the reservations that carry the action, until Bentham has measured it;
- replacement proposals (corrections to orders that already have a claim) are not new production and are exempt.

Larrey triage (jobs/larrey-triage, 2026-11-10): an order the action lists is still refused when Larrey's zero-token
check finds that it lacks an input its route needs (a usable original, no page check owed, a status basis record, a
clause inventory, ...), so that no agent is paid to discover that. The refusal names the missing input. A checkout
that carries jobs/larrey-triage/larrey.py but no current triage output is refused (re-run `larrey.py triage`);
`LARREY_LEVEL=hard` applies only the gates the route itself requires. Actions Larrey does not triage, and routes
whose kit code changed since Larrey's back-test, are unchanged.

A checkout without jobs/bentham/ (the kit's own test fixtures) is not checked. A checkout that has jobs/bentham/
but no PLAN.json is refused, so that a sparse checkout cannot skip the check by leaving the plan out.
Nothing here ranks, decides a status or changes a count.
"""

import importlib.util
import json
from pathlib import Path

PLAN = "jobs/bentham/output/PLAN.json"
STRATA = "jobs/bentham/output/strata"
PROBE_ORDERS = 30
LARREY = "jobs/larrey-triage/larrey.py"


def _larrey(repo):
    """Larrey's module from this checkout, or None when the checkout does not carry it (the kit's fixtures)."""
    path = Path(repo) / LARREY
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("larrey_triage", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def triage(repo, action):
    """(Larrey's admitted set, or None when it does not triage this action; reasons by kept-out id; receipt)."""
    mod = _larrey(repo)
    if mod is None:
        return None, {}, {"larrey_route": None, "larrey_enforced": False}
    return mod.admitted(repo, action)


def applies(repo):
    """The project checkout (AGENTS.md at its root, which every sparse checkout keeps), or any repo with Bentham.

    Not just "jobs/bentham exists": a sparse worktree that leaves Bentham out must be refused, not let through.
    The kit's test fixtures have neither, so they are not checked.
    """
    repo = Path(repo)
    return (repo / "AGENTS.md").is_file() or (repo / "jobs/bentham").is_dir()


def _plan(repo):
    path = Path(repo) / PLAN
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"Bentham plan missing: materialize {PLAN} (claim-kit work must name a Bentham action)")
    except ValueError as exc:
        raise ValueError(f"Bentham plan unreadable: {PLAN}: {exc}")


def members(repo, action):
    base = action[len("probe."):] if action.startswith("probe.") else action
    path = Path(repo) / STRATA / (base + ".txt")
    if not path.is_file():
        raise ValueError(f"Bentham action {action} lists no orders ({path.relative_to(repo).as_posix()} missing)")
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def entry(repo, action):
    if not action:
        raise ValueError("name the Bentham action this work belongs to (--action ID); see jobs/bentham/output/PLAN.md")
    plan = _plan(repo)
    for group in ("ranked", "unranked"):
        for item in plan.get(group) or []:
            if item.get("id") == action:
                return item, group
    raise ValueError(f"unknown Bentham action {action!r}: not in {PLAN}")


def is_probe(item, group):
    return item.get("id", "").startswith("probe.") or group == "unranked" or bool(item.get("unranked"))


def admit(repo, action, ids, reservations):
    """Raise ValueError unless every id may be worked under action. Returns the admitted member set.

    reservations: the lock's {instrument_id: {..., 'action': ...}} map, used for the probe cap.
    """
    item, group = entry(repo, action)
    allowed = members(repo, action)
    outside = sorted(set(ids) - allowed)
    if outside:
        shown = ", ".join(outside[:10]) + (" ..." if len(outside) > 10 else "")
        raise ValueError(f"{len(outside)} orders are not in Bentham action {action}: {shown}")
    ok, why, _ = triage(repo, action)
    if ok is not None:
        msg = _larrey(repo).refusal(action, ids, ok, why)
        if msg:
            raise ValueError(msg)
        allowed = allowed & ok
    if is_probe(item, group):
        used = {iid for iid, v in reservations.items() if isinstance(v, dict) and v.get("action") == action}
        if len(used | set(ids)) > PROBE_ORDERS:
            raise ValueError(f"{action} is a probe: at most {PROBE_ORDERS} orders until Bentham measures it "
                             f"({len(used)} already reserved under it)")
    return allowed


def capacity(repo, action, reservations):
    """(allowed member set, how many more orders may be reserved under action, or None for no cap)."""
    item, group = entry(repo, action)
    allowed = members(repo, action)
    ok, _, _ = triage(repo, action)
    if ok is not None:
        allowed = allowed & ok
    if not is_probe(item, group):
        return allowed, None
    used = {iid for iid, v in reservations.items() if isinstance(v, dict) and v.get("action") == action}
    return allowed, max(0, PROBE_ORDERS - len(used))


def record(dest, action, ids, agent, repo=None):
    """The admission receipt beside a prepared packet (not inside it, so packet seals are unchanged)."""
    Path(dest).mkdir(parents=True, exist_ok=True)
    rec = {"schema": "eo-claim-kit-admission/v1", "bentham_action": action, "agent": agent,
           "instrument_ids": sorted(ids)}
    if repo is not None:
        rec["triage"] = triage(repo, action)[2]   # which Larrey verdicts admitted these orders
    (Path(dest) / "ADMISSION.json").write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")

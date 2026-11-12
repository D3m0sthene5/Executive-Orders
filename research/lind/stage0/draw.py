"""Lind stage 0 draw: 30 undecided orders, 15 that pass every Larrey gate and 15 that pass the hard gates but fail a
soft gate, in one seeded random order, for the hard-only route (LARREY_LEVEL=hard).

Zero tokens. It only reads committed outputs and writes DRAW.json beside this file.

It refuses to draw while the inputs are stale:
- the claim-kit output must have been built after the last Accursius fix merged (PR #275, 2026-11-10T22:07:23Z); the
  output on main from 2026-11-10T10:36Z predates all five fixes (F3-F7);
- Larrey's GATES.jsonl must have been built after that claim-kit output.

Usage: python3 -I research/lind/stage0/draw.py [--seed N] [--per-arm 15] [--check-only]
"""

import argparse
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
KIT_STATUS = REPO / "jobs/claim-kit/output/STATUS.json"
LARREY_STATUS = REPO / "jobs/larrey-triage/output/STATUS.json"
GATES = REPO / "jobs/larrey-triage/output/GATES.jsonl"
STRATA = REPO / "jobs/bentham/output/strata/status_assignment.undecided.txt"
LAST_FIX_MERGED = "2026-11-10T22:07:23Z"
SEED = 20261112
ROUTE = "undecided_full"


def _finished(path):
    return json.loads(path.read_text(encoding="utf-8")).get("finished_utc") or ""


def freshness():
    """Return a list of reasons the inputs are stale (empty when fresh)."""
    kit, gates = _finished(KIT_STATUS), _finished(LARREY_STATUS)
    why = []
    if kit < LAST_FIX_MERGED:
        why.append(f"claim-kit output built {kit}, before the last F3-F7 fix merged ({LAST_FIX_MERGED}): rebuild "
                   "claim-kit on main first")
    if gates < kit:
        why.append(f"Larrey gates built {gates}, before the claim-kit output ({kit}): re-run larrey-triage")
    return why


def already_attempted():
    """Orders attempted in the waves the back-test scores (Papinian u01b/u02/u03, Haloander u01-u03)."""
    sys.path.insert(0, str(REPO / "jobs/larrey-triage"))
    import larrey  # noqa: E402  (repo module, loaded by path)
    return set(larrey.undecided_outcomes(REPO))


def strata():
    listed = set(STRATA.read_text(encoding="utf-8").split())
    done = already_attempted()
    admitted, soft_only = [], []
    for line in GATES.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("route") != ROUTE or r["instrument_id"] not in listed or r["instrument_id"] in done:
            continue
        if r.get("pass"):
            admitted.append(r["instrument_id"])
        elif r.get("pass_hard"):
            soft_only.append(r["instrument_id"])
    return sorted(admitted), sorted(soft_only)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--per-arm", type=int, default=15)
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--key-out", help="where to write the arm key (default ARM_KEY.json beside this file; commit it "
                                      "only after review completes)")
    a = ap.parse_args(argv)
    stale = freshness()
    if stale:
        print("REFUSE: " + "; ".join(stale))
        return 2
    admitted, soft_only = strata()
    print(f"pool: {len(admitted)} pass every gate, {len(soft_only)} pass hard gates only")
    if a.check_only:
        return 0
    rng = random.Random(a.seed)
    arms = {"all_gates": rng.sample(admitted, a.per_arm), "hard_only": rng.sample(soft_only, a.per_arm)}
    order = [(i, arm) for arm, ids in arms.items() for i in ids]
    rng.shuffle(order)
    out = {"schema": "lind-stage0-draw/v1", "seed": a.seed, "route": ROUTE, "larrey_level": "hard",
           "claim_kit_finished_utc": _finished(KIT_STATUS), "gates_finished_utc": _finished(LARREY_STATUS),
           "pool_sizes": {"all_gates": len(admitted), "hard_only": len(soft_only)},
           "orders": [i for i, _ in order]}
    here = Path(__file__).parent
    (here / "DRAW.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    # The arm key goes to the coordinator only: never into a packet, a review set or a producer prompt.
    key = Path(a.key_out) if a.key_out else here / "ARM_KEY.json"
    key.write_text(json.dumps({i: arm for i, arm in order}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"drew {len(order)} orders -> DRAW.json; arm key -> {key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

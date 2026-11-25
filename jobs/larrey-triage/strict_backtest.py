#!/usr/bin/env python3
"""Back-test of Larrey's levels (hard, soft, strict) against filed dossiers in past waves. Zero model tokens.

    python3 -I jobs/larrey-triage/strict_backtest.py [--json OUT]

Outcome: a filed dossier (a completion-publishable lifecycle claim, or a filed undecided-route replacement
proposal), the unit the stateless gauge prices. Each attempted order is scored on the dossier frozen for it in
that wave, with the gates Larrey itself applies (Llull GATES on kit_features.from_dossier). Waves read:
Papinian y01-y14, c01, u01b-u03; Haloander u01-u03; Bartolus y01-y04, u01. Bartolus re-ran 50 YES orders that
Papinian had attempted, on dossiers that by then held the NEA notices, so those 50 orders appear twice, once per
attempt. Recovery batches (r*, s01) take routes Larrey does not triage and are left out.
See research/plans/LARREY_STRICT_2026-11-25.md.
"""
import argparse
import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import larrey  # noqa: E402

EX = "research/excavator/"
DECIDED = ((EX + "claude-papinian-2026-11-10", "papinian", ("y*", "c01")),
           (EX + "claude-bartolus-2026-11-24", "bartolus", ("y*",)))
UNDECIDED = ((EX + "claude-papinian-2026-11-10", "papinian", ("u01b", "u02", "u03")),
             (EX + "claude-haloander-2026-11-07", "haloander", ("u01", "u02", "u03")),
             (EX + "claude-bartolus-2026-11-24", "bartolus", ("u01",)))
FILED_PROPOSALS = {"papinian": ["u0*/overlay/REPLACEMENT_PROPOSAL.jsonl"],
                   "haloander": ["ux/overlay/REPLACEMENT_PROPOSAL.jsonl"],
                   "bartolus": ["u01/overlay/REPLACEMENT_PROPOSAL.jsonl"]}


def attempts(repo=REPO):
    """One row per attempted order: wave, batch, route, instrument_id, filed, features."""
    repo = Path(repo)
    kf = larrey._kf()
    rules = kf.KitRules(kf.CODE_KIT)
    kit_dir = str(repo / "jobs/claim-kit")
    if kit_dir not in sys.path:
        sys.path.insert(0, kit_dir)
    import batch
    rows = []
    for base, wave, pats in DECIDED:
        for pat in pats:
            for pk in sorted((repo / base).glob(pat + "/packet")):
                if not (pk / "PACKET.json").exists():
                    continue
                filed = set()
                for p in pk.glob("complete-v*/CLAIMS.publishable.jsonl"):
                    filed |= {r["instrument_id"] for r in larrey._jl(p)}
                ds = batch.decode(json.loads((pk / "PACKET.json").read_text(encoding="utf-8")))
                for iid, d in ds.items():
                    rows.append({"wave": wave, "batch": pk.parent.name, "route": "decided_lifecycle",
                                 "instrument_id": iid, "filed": iid in filed, "features": kf.from_dossier(d)})
    for base, wave, batches in UNDECIDED:
        filed = set()
        for g in FILED_PROPOSALS[wave]:
            for p in glob.glob(str(repo / base / g)):
                for r in larrey._jl(p):
                    filed.add(r.get("instrument_id") or (r.get("claim") or {}).get("instrument_id"))
        for b in batches:
            for ev in sorted((repo / base / b / "packet").glob("undecided/*/EVIDENCE.json")):
                e = json.loads(ev.read_text(encoding="utf-8"))
                iid = e["instrument_id"]
                rows.append({"wave": wave, "batch": b, "route": "undecided_full", "instrument_id": iid,
                             "filed": iid in filed,
                             "features": kf.from_dossier(e["base_dossier"], status=None, rules=rules)})
    return rows


def gate_state(row, gate, G=None):
    G = G or larrey._llull().GATES
    f = row["features"]
    st = f.get("status") or ""
    D = larrey._FeatData({row["instrument_id"]: f})
    return G[gate][1]({"instrument_id": row["instrument_id"], "provisional_status": st if st in ("yes", "no") else ""},
                      D)


def admitted_at(row, level, extra=(), G=None):
    """Whether Larrey admits the attempt at a level (hard, soft or strict), optionally with extra gates."""
    spec = larrey.ROUTES[row["route"]]
    gates = list(spec["hard"])
    if level in ("soft", "strict"):
        gates += spec["soft"]
    if level == "strict":
        gates += spec.get("strict", [])
    gates += list(extra)
    return all(gate_state(row, g, G) in ("held", "na") for g in gates)


def score(rows, rule, base_rule):
    """admitted, filed among admitted, rate, lift over base_rule, share of filed kept."""
    adm = [r for r in rows if rule(r)]
    base = [r for r in rows if base_rule(r)]
    filed = sum(r["filed"] for r in rows)
    af, bf = sum(r["filed"] for r in adm), sum(r["filed"] for r in base)
    rate = af / len(adm) if adm else 0.0
    brate = bf / len(base) if base else 0.0
    return {"attempts": len(rows), "admitted": len(adm), "filed": filed, "filed_admitted": af,
            "rate": round(rate, 4), "lift_vs_base": round(rate / brate, 3) if brate else None,
            "filed_kept": round(af / filed, 4) if filed else None}


SEGMENTS = {
    "all": lambda r: True,
    "decided route": lambda r: r["route"] == "decided_lifecycle",
    "undecided route": lambda r: r["route"] == "undecided_full",
    "Papinian (fit)": lambda r: r["wave"] == "papinian",
    "Haloander + Bartolus (later waves)": lambda r: r["wave"] != "papinian",
    "Bartolus decided (NEA notices held)": lambda r: r["wave"] == "bartolus" and r["route"] == "decided_lifecycle",
}


def run(repo=REPO):
    G = larrey._llull().GATES
    rows = attempts(repo)
    for r in rows:
        r["_lv"] = {lv: admitted_at(r, lv, G=G) for lv in larrey.LEVELS}
        r["_events"] = r["features"].get("status_events")
        r["_contra"] = gate_state(r, "no_contradicting_status_lead", G) in ("held", "na")
    hard = lambda r: r["_lv"]["hard"]
    rules = {
        "hard (default)": hard,
        "soft": lambda r: r["_lv"]["soft"],
        "strict": lambda r: r["_lv"]["strict"],
        "soft + no_contradicting_status_lead only": lambda r: r["_lv"]["soft"] and r["_contra"],
        "soft + status_events_at_most_5 only": lambda r: r["_lv"]["soft"] and (r["_events"] or 0) <= 5,
    }
    for k in (3, 4, 6):
        rules[f"strict with events <= {k}"] = (lambda r, k=k: r["_lv"]["soft"] and r["_contra"]
                                               and (r["_events"] or 0) <= k)
    out = {"schema": "larrey.strict_backtest/v1", "generated_at": larrey.now(),
           "outcome": "filed dossier (publishable lifecycle claim or filed undecided replacement proposal)",
           "base": "hard (default level)", "segments": {}}
    for seg, sf in SEGMENTS.items():
        R = [r for r in rows if sf(r)]
        out["segments"][seg] = {name: score(R, rule, hard) for name, rule in rules.items()}
    soft_rows = [r for r in rows if r["_lv"]["soft"]]
    out["strict_over_soft"] = {seg: score([r for r in soft_rows if sf(r)], lambda r: r["_lv"]["strict"],
                                          lambda r: True) for seg, sf in SEGMENTS.items()}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--json", help="write the result here")
    a = ap.parse_args(argv)
    res = run(a.repo)
    for seg, rs in res["segments"].items():
        first = next(iter(rs.values()))
        print(f"== {seg}: {first['attempts']} attempts, {first['filed']} filed")
        for name, s in rs.items():
            print(f"  {name:42s} admitted {s['admitted']:4d}  filed {s['filed_admitted']:3d}  rate {s['rate']:6.1%}"
                  f"  x{s['lift_vs_base'] or 0:4.2f}  kept {s['filed_kept'] or 0:5.1%}")
    print("== strict over soft (among soft-admitted attempts)")
    for seg, s in res["strict_over_soft"].items():
        print(f"  {seg:42s} admitted {s['admitted']:4d}/{s['attempts']:4d}  filed {s['filed_admitted']:3d}/"
              f"{s['filed']:3d}  x{s['lift_vs_base'] or 0:4.2f}")
    if a.json:
        larrey._write(Path(a.json), json.dumps(res, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Nalimov cost projection per adopted status, from measured packet sizes and list prices. Zero tokens.

Inputs: research/nalimov/MEASURES.json (packets built from the 36 real complete drafts), jobs/necker-costs/PRICES.json
(API list prices; skipped in a sparse checkout, then the 2026-11-06 values below are used). Every assumption is a
named parameter with a low and a high value; the result is a projection, not a measurement, until a calibration run
replaces the assumptions with measured worker usage (verify.score).

    python -I research/nalimov/project.py > research/nalimov/PROJECTION.json
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
M = json.loads((HERE / "MEASURES.json").read_text(encoding="utf-8"))
PRICES = {  # USD per million tokens, jobs/necker-costs/PRICES.json retrieved 2026-11-06
    "claude-sonnet-5-5": {"input": 2, "cache_write_5m": 2.5, "cache_read": 0.10, "output": 10},
    "claude-opus-5-5": {"input": 4, "cache_write_5m": 5, "cache_read": 0.20, "output": 20},
}
ROLES = {"A": "claude-sonnet-5-5", "B": "claude-opus-5-5", "S": "claude-sonnet-5-5"}
# A verifier session: read the prompt and PACKET.json once (cache write), then a few turns that re-read the context
# from cache, then write VERDICTS.jsonl. Turn counts and output per entry are the uncertain part.
CASES = {
    "low":  {"turns_after_read": 2, "output_tokens_per_entry": 300, "upheld_rate": 0.95, "reveal_share": 0.10,
             "coordinator_usd_per_claim": 0.01},
    "mid":  {"turns_after_read": 3, "output_tokens_per_entry": 600, "upheld_rate": 0.80, "reveal_share": 0.15,
             "coordinator_usd_per_claim": 0.03},
    "high": {"turns_after_read": 6, "output_tokens_per_entry": 1200, "upheld_rate": 0.60, "reveal_share": 0.25,
             "coordinator_usd_per_claim": 0.08},
}
PROMPT_TOKENS = 1800
FULL_ROUTE = {"usd_per_attempted_order": 0.51, "usd_per_adopted_status": 7.71, "basis": "Papinian 2026-11-10 workers "
              "(research/excavator/claude-respondendi-2026-11-10/REPORT.md section 4); coordinators not included",
              "tokens_per_attempted_order_context": 751017, "tokens_basis": "Bentham PLAN.md, last measured production wave"}


def session_cost(packet_tokens, entries, model, case):
    p = PRICES[model]
    ctx = PROMPT_TOKENS + packet_tokens
    out = entries * case["output_tokens_per_entry"]
    cache_write = ctx
    cache_read = ctx * case["turns_after_read"] + out * max(0, case["turns_after_read"] - 1) // 2
    usd = (cache_write * p["cache_write_5m"] + cache_read * p["cache_read"] + out * p["output"]) / 1e6
    return {"tokens": cache_write + cache_read + out, "usd": usd}


def main():
    sessions = M["sessions_detail"]
    genuine = M["orders"]
    out = {"schema": "nalimov-projection/v1", "measured": {k: M[k] for k in ("orders", "sessions", "controls",
                                                                         "packet_tokens_est_per_genuine_claim",
                                                                         "dossier_tokens_est_per_order_mean",
                                                                         "ratio_packet_to_dossier")},
           "roles": ROLES, "full_route": FULL_ROUTE, "cases": {}}
    for name, case in CASES.items():
        tok = usd = 0.0
        for s in sessions:
            for role, model in ROLES.items():
                c = session_cost(s["tokens_est"], s["entries"], model, case)
                tok += c["tokens"]
                usd += c["usd"]
        usd *= 1 + case["reveal_share"]           # after-reveal review of genuine control twins
        tok *= 1 + case["reveal_share"]
        per_claim = usd / genuine + case["coordinator_usd_per_claim"]
        per_status = per_claim / case["upheld_rate"]
        out["cases"][name] = {**case, "worker_tokens_per_genuine_claim": round(tok / genuine),
                              "worker_usd_per_genuine_claim": round(usd / genuine, 4),
                              "usd_per_genuine_claim_with_coordinator": round(per_claim, 4),
                              "usd_per_adopted_status": round(per_status, 3),
                              "times_cheaper_than_full_route": round(FULL_ROUTE["usd_per_adopted_status"] / per_status, 1)}
    out["not_included"] = ("Respondendi's cross-family audits (every member while the stratum is on probation, then 20%) "
                           "and owner time; neither is in the full-route figure either. Kit apply, batch-check, checker "
                           "and completion are zero-token scripts.")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

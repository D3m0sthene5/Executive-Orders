#!/usr/bin/env python3
"""Build the dated hub snapshot from reviewed recovery outputs; no network/writes to science."""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PIN = "600ae3018f71025b3e53dc8538b8f92e6e159b76"
TOKENS = {"fresh_input": "input_tokens", "cache_read": "cache_read_input_tokens",
          "cache_creation": "cache_creation_input_tokens", "output": "output_tokens"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--generated-at", required=True, help="Explicit observation timestamp; never inferred from Git commit time")
    p.add_argument("--out", type=Path, default=REPO / "research/progress/control-center/observability.json")
    args = p.parse_args()
    start = time.perf_counter()
    baseline_path, historical_path = HERE / "baseline/BASELINE.json", HERE / "historical/RECOVERED.json"
    baseline, historical = [json.loads(path.read_text()) for path in (baseline_path, historical_path)]
    pins = json.loads((HERE / "ROLLUP_INPUTS.json").read_text())
    for path in (baseline_path, historical_path):
        if pins["sha256"].get(path.relative_to(HERE).as_posix()) != hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError("Derived roll-up input changed; reproduce and independently review before repinning")
    b = {key: baseline[key] for key in ("source_pin", "finished_utc", "orders_total", "ready", "unfinished", "human_certified", "first_missing", "open_anywhere")}
    if b["source_pin"] != PIN or historical["source_main_pin"] != PIN:
        raise ValueError("Unexpected source pin; re-examine narrative before changing baseline")
    sources = [
        {"id": "tracker", "path": "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv", "ref": PIN},
        {"id": "checker", "path": "jobs/claim-checker/output/SUMMARY.json", "ref": PIN},
        {"id": "apollo", "path": "research/excavator/claude-apollo-2026-10-31/TELEMETRY.csv", "ref": PIN},
        {"id": "erasmus", "path": "research/excavator/claude-erasmus-2026-11-02/TELEMETRY.csv", "ref": PIN},
        {"id": "erasmus_report", "path": "research/excavator/claude-erasmus-2026-11-02/REPORT.md", "ref": PIN},
        {"id": "hamilton", "path": "jobs/hamilton-token-audit/README.md", "ref": PIN},
        {"id": "neyman", "path": "jobs/neyman/AFTER_COMPLETION.md", "ref": PIN},
        {"id": "erasmus_tally", "path": "research/excavator/claude-erasmus-2026-11-02/e1/packet/supp/complete-v1/TALLY.json", "ref": PIN},
        {"id": "apollo_tally", "path": "research/excavator/claude-apollo-2026-10-31/g03/packet/complete-v1/TALLY.json", "ref": PIN},
        {"id": "tribonian", "path": "research/excavator/claude-tribonian-2026-11-04/tools/batches.json", "ref": "cacfb8f4af6db949476bd7bec8220a464055c931"},
    ]
    version = HERE / "COLLECTOR_VERSION.json"
    if version.exists():
        collector = json.loads(version.read_text())
        sources = [{**s, "ref": collector["commit"]} if s["id"] == "hamilton" else s for s in sources]
    gaps = [
        ("phase_role", "Tokens and money by phase and role",
         "Apollo and Erasmus worker-row token categories are recovered by published role/model. Batch costs remain at batch scope; coordinator coverage is absent.",
         "Hamilton now reconciles streamed call revisions and exports supported JSONL observations to the existing NEYMAN effort contract with explicit role, model, interval and downstream membership.",
         "Complete call denominator, coordinator usage, historical phase splits, cache TTL and actual cash cannot be recovered from aggregate CSVs. No per-call or project bill is inferred.", ["apollo", "erasmus", "hamilton"]),
        ("repetition", "Repeated evidence and context",
         "Cache-read totals show context rereading in the observed worker rows. They do not identify source/page repetition or avoidable work; independent review may require rereading.",
         "Retain stable message identities, provider cache categories and supported evidence digests when future ordinary exports provide them. Source-read purpose must distinguish review from optional duplication.",
         "Historical CSVs contain no source/page digests, context resets or cache-hit chronology. Their aggregate counts cannot reconstruct which source reads were avoidable.", ["apollo", "erasmus", "hamilton"]),
        ("blockers_retries", "Late blockers, corrections and retries",
         "Published exact native completion and review outcomes are joined to campaign/batch telemetry. Erasmus has 64 attempt-members: 52 eligible, 11 blocked and one mechanical rejection. Its 52 filed orders include 20 superseding corrections.",
         "Carry exact attempt/output/review versions, first blocker detection phase and already-spent observed effort through existing completion/NEYMAN receipts; retain rejected and resumed members.",
         "Historical first-detection times and tokens spent before blockers are absent. A completion blocker is not evidence that it was detected late. No savings are attributed to preflight.", ["checker", "erasmus_report", "erasmus_tally", "neyman"]),
        ("ready_conversion", "Cost per additional ready dossier",
         "Current readiness is pinned separately from exact campaign filings and isolated tracker-replay transitions. Corrections, review approvals, eligible filings and net newly ready orders remain distinct.",
         "Use baseline/final native IDs plus exact attempt and usage identities. Count shared costs once; expose failed cohorts and zero conversion. Preserve probability samples and unfinished members.",
         "Complete run-attributable marginal readiness gains and complete effort are unavailable. Tokens per newly ready dossier and dollars per newly ready dossier remain undefined, rather than zero.", ["tracker", "apollo", "erasmus_report", "neyman"]),
        ("time", "Waiting, compute and worker time",
         "Native generation timestamps, CSV event-gap timing fields and bounded machine replays retain their original methods. Published protected-wave membership is planned work, not observed active workers.",
         "Use explicit timezone-aware occupied intervals and native command clocks, with shared interval unions. The collector records its own bounded machine overhead; a token reset is external wait.",
         "Private worker activity, review capacity, evidence-access waits, complete critical path and pause duration are unavailable. Gaps between transcript events do not establish active labor.", ["tracker", "erasmus", "tribonian", "hamilton"]),
    ]
    campaigns, roles = [], []
    for c in historical["campaigns"]:
        telemetry = c["telemetry"]
        cid = c["id"]
        totals = telemetry["totals"]
        campaigns.append({"id": cid, "label": cid.title(), "window": c["date"], "workers": telemetry["rows"],
            "scope": "Published transcript-derived worker aggregates; historical reconstruction, not independently verified provider-final usage or a project bill",
            "coverage": "Coordinator excluded. Legacy exporter takes first usage, zero-fills omissions and reports modal model; CSV categories can undercount final usage. Row count is not execution count.",
            "tokens": {k: totals.get(v) for k,v in TOKENS.items()}, "api_equivalent_usd": None, "actual_cash_usd": None,
            "source_ids": [cid, cid + "_tally"], "outcomes": "Native attempt/review/completion versions are retained in the recovery ledger; the linked tally is one exact example. Filing and isolated replay gains are not current marginal readiness or human certification."})
        for r in telemetry["by_role_model"]:
            roles.append({"campaign_id": cid, "role": r["role"], "model": r["model"], "workers": r["agents"],
                "tokens": {k:r.get("totals", r).get(v) for k,v in TOKENS.items()},
                "coverage": "Published aggregate worker rows; reported model is modal in the worker transcript, not observed per-token attribution. Call-level phase usage unavailable"})
        assigned_roles = [r for r in roles if r["campaign_id"] == cid]
        if sum(r["workers"] for r in assigned_roles) != telemetry["rows"]:
            raise ValueError("Published worker rows did not partition by reported role/model")
        for key in TOKENS:
            if sum(r["tokens"][key] for r in assigned_roles) != campaigns[-1]["tokens"][key]:
                raise ValueError("Published worker token totals did not reconcile")
    data = {"schema_version": 1, "generated_at": args.generated_at, "source_pin": PIN, "baseline": b,
            "sources": sources, "campaigns": campaigns, "roles": roles,
            "gaps": [dict(zip(("id","title","recovered","prospective","unavailable","source_ids"), g)) for g in gaps],
            "boundaries": [
                "First missing checks partition the displayed workload; overlapping checks are not separate queues or worker locations.",
                "The tracker generation remains November 2 even when the repository head is checked on November 4. Unpublished work is not zero work.",
                "Tribonian's 40 published planned batches contain 1,218 unique members; local progress and consumption remain unobserved. These assignments are protected.",
                "Erasmus reports 27 executions including resumptions but publishes 20 worker rows. Those denominators are not interchangeable.",
                "Shared work is counted once at supported scope. Cash, cached-token volume and dated API-equivalent value have different meanings; no price conversion is made here.",
                "No legal claims, provisional statuses, census identities, source grades, review gates or human certifications are changed by this observability work.",
            ]}
    # Use the same validator as the browser BEFORE replacing a last-good artifact.
    encoded = json.dumps(data, indent=2) + "\n"
    validator = REPO / "research/progress/control-center/observability-core.js"
    check = "const fs=require('fs'), core=require(process.argv[1]); const prior=fs.existsSync(process.argv[2])?JSON.parse(fs.readFileSync(process.argv[2],'utf8')):null; const r=core.accept(prior,JSON.parse(fs.readFileSync(0,'utf8'))); if(r.error)throw Error(r.error);"
    subprocess.run(["node", "-e", check, str(validator), str(args.out)], input=encoded, text=True, check=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.out.with_suffix(args.out.suffix + ".tmp")
    temporary.write_text(encoded)
    temporary.replace(args.out)
    receipt = {"kind":"deterministic_rollup_machine_time", "elapsed_seconds":time.perf_counter()-start,
        "input_sha256":{str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (baseline_path,historical_path,validator)},
        "output_sha256":hashlib.sha256(encoded.encode()).hexdigest(), "input_bytes":sum(p.stat().st_size for p in (baseline_path,historical_path)),
        "worker_active_seconds":None,"model_tokens":None,"cash_usd":None,
        "scope":"One deterministic local build including browser validator; excludes recovery, engineering, review and coordination costs"}
    (HERE / "ROLLUP_RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps({"output":str(args.out),"bytes":len(encoded.encode()),"elapsed_seconds":receipt["elapsed_seconds"]}))


if __name__ == "__main__":
    main()

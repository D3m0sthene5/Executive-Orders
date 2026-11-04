#!/usr/bin/env python3
"""Synthetic supported-export CLI -> unchanged native NEYMAN acceptance replay.

Creates only a new --out directory, never production records. No network/model calls.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[4]
BASE = "54db2cf5948d7c0cdd91c8f66a96349224aee6a1"


def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    root=out/"fixture-repo";root.mkdir()
    started=datetime.now(timezone.utc).isoformat();t0=time.perf_counter();commands=[]
    def write(name,value):
        target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(value,indent=2)+"\n")
        return {"path":name,"sha256":hashlib.sha256(target.read_bytes()).hexdigest()}
    def run(args):
        start=time.perf_counter()
        r=subprocess.run([sys.executable,"-B",*map(str,args)],capture_output=True,text=True)
        commands.append({"argv":[sys.executable,"-B",*map(str,args)],"elapsed_seconds":time.perf_counter()-start,
            "exit_code":r.returncode,"stdout":r.stdout,"stderr":r.stderr})
        if r.returncode:
            (out/"FAILED_COMMANDS.json").write_text(json.dumps(commands,indent=2)+"\n")
            raise RuntimeError(r.stderr or r.stdout)
    usage={"input_tokens":3,"cache_read_input_tokens":5,"cache_creation_input_tokens":7,
        "output_tokens":1,"output_tokens_details":{"reasoning_tokens":0}}
    records=[]
    for final in (False,True,True):
        u=dict(usage)
        if final:u.update(output_tokens=11,output_tokens_details={"reasoning_tokens":4})
        records.append({"type":"assistant","uuid":"synthetic-same-event","timestamp":"2000-01-01T00:00:10Z",
            "message":{"id":"synthetic-call","model":"synthetic-anthropic-model","usage":u,
                "stop_reason":"end_turn" if final else None,"content":[]}})
    transcript=root/"worker.output"
    transcript.write_text("".join(json.dumps(r)+"\n" for r in records))
    metadata=write("metadata.json",{"session_id":"synthetic-supported-export-session","agents":{"main":{
        "worker_id":"synthetic-worker","role":"producer","phase":"production","actual_model":"synthetic-anthropic-model",
        "instrument_ids":["EO:SYNTHETIC1","EO:SYNTHETIC2"],"started_utc":"2000-01-01T00:00:00Z",
        "finished_utc":"2000-01-01T00:01:00Z","coverage":"partial",
        "measurement_method":"synthetic caller interval; verifies schema only; no measured historical labor"}}})
    run([REPO/"jobs/hamilton-token-audit/profile.py",transcript,"--label","synthetic","--production-metadata",root/metadata["path"],"--out",root/"normalized"])
    effort=root/"normalized/PRODUCTION_EFFORT.json"
    effort_ref={"path":effort.relative_to(root).as_posix(),"sha256":hashlib.sha256(effort.read_bytes()).hexdigest()}
    selection=write("selection.json",[{"instrument_id":i} for i in ("EO:SYNTHETIC1","EO:SYNTHETIC2")])
    attempts=[]
    for i in ("EO:SYNTHETIC1","EO:SYNTHETIC2"):
        attempts.append(write(i.replace(":","-")+".json",{"schema":"neyman.research-attempt/1","instrument_id":i,
            "attempt_id":"synthetic:"+i,"assessor":"synthetic CLI fixture","question":"verify blocked shared effort accounting",
            "outcome":"blocked","started_utc":"2000-01-01T00:00:00Z","finished_utc":"2000-01-01T00:01:00Z","basis":[effort_ref]}))
    write("IMPORT.json",{"schema":"neyman.production-import/1","base_commit":BASE,"cohort_kind":"ordinary_production",
        "selection":selection,"research_attempts":attempts,"effort_receipts":[effort_ref,effort_ref]})
    run([REPO/"jobs/neyman/diagnose.py","--repo",root,"--manifest","IMPORT.json","--out",out/"native-diagnosis"])
    d=json.loads((out/"native-diagnosis/DIAGNOSIS.json").read_text())
    profile=json.loads((root/"normalized/PROFILE_synthetic.json").read_text())
    expected={"input_uncached":3,"cache_read":5,"cache_write":7,"output":11,"reasoning":4}
    assert d["effort"]["observed_token_lower_bounds"]==expected
    assert d["effort"]["token_usage_records"]==1
    assert d["effort"]["observed_seconds_by_kind"]["worker_elapsed"]==60
    assert d["effort"]["observed_seconds_by_kind"]["active"] is None
    assert d["summary"]["ready_in_isolated_replay"]==0
    pins={name:hashlib.sha256((REPO/name).read_bytes()).hexdigest() for name in (
        "jobs/hamilton-token-audit/profile.py","jobs/neyman/diagnose.py","jobs/neyman/production_receipts.py","jobs/neyman/survey.py")}
    receipt={"schema":"sol.collection-cli-replay/1","scope":"synthetic engineering acceptance; no historical provider calls or production gains",
        "base_commit":BASE,"started_utc":started,"finished_utc":datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds":time.perf_counter()-t0,"commands":commands,"implementation_sha256":pins,
        "collector":profile["collector"],"normalized_observed_tokens":expected,"shared_calls_counted":1,
        "ready_gain":0,"cost_per_new_ready_dossier":None,"cost_per_new_ready_reason":"undefined with zero newly ready dossiers",
        "historical_labor_measured":False,"model_calls":0,"tokens_used_by_engineering_session":None,"cash_charge_usd":None}
    (out/"REPLAY_RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps({k:receipt[k] for k in ("scope","elapsed_seconds","shared_calls_counted","ready_gain","cost_per_new_ready_dossier")}))


if __name__=="__main__":main()

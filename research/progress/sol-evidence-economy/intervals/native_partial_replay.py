"""Engineering-only replay: ordinary prepare/apply/complete, real checker/tracker, synthetic evidence.
Run with the repository Python 3.12+, from any directory. All scientific inputs/outputs are temporary."""
import csv
import json
from pathlib import Path
import shutil
import sys
import time

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0,str(REPO / "jobs/claim-kit"))
sys.path.insert(0,str(REPO / "jobs/readiness-tracker"))
import batch
import completion as C
import test_completion as TC
import test_factual_events as TF
import test_tracker as TT
import factual_events as F

def run():
    started = time.monotonic()
    fx = TC.CompletionTests()
    fx.setUp()
    fact = TF.FactualEventTests()
    fact.setUp()
    tracker = TT.TrackerTest()
    tracker.setUp()
    try:
        repo = fx.repo
        # Fixture source indexing and runtime are real. Nothing is copied to the live repository.
        for folder in ("claim-checker","readiness-tracker","claim-kit","norton"):
            src = REPO / "jobs" / folder
            for f in src.glob("*.py"):
                if not f.name.startswith("test_"):
                    target=repo/"jobs"/folder/f.name
                    target.parent.mkdir(exist_ok=True,parents=True)
                    shutil.copyfile(f,target)
        for p in tracker.root.rglob("*"):
            if p.is_file() and not (repo / p.relative_to(tracker.root)).exists():
                dest = repo / p.relative_to(tracker.root)
                dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(p,dest)
        with fx.status.open(encoding="utf-8", newline="") as f:
            statuses=list(csv.DictReader(f))
        TT.write_csv(fx.status,[dict(r,decision_origin="inherited_legacy_v2") for r in statuses])
        fx.run_build()
        d = fx.dossier("EO:1")
        fact.interval_fixture()
        app = fact.registry["applications"][0]
        app["clause_evidence"] = dict(d["clauses"][0], instrument_id="EO:1")
        app["scope_id"] = app["clause_evidence"]["scope_id"]
        fact.registry["reviews"][1]["record_sha256"] = F.MODEL.fingerprint(app)
        fact.write_registry()
        reg = "research/readiness/factual/test"
        shutil.copytree(fact.repo / reg, repo / reg)
        for name in ("report.txt","report.html"):
            shutil.copyfile(fact.repo / name, repo / name)
        out=repo/"jobs/norton/output"
        out.mkdir(parents=True,exist_ok=True)
        pins = {p.relative_to(repo).as_posix(): batch.file_sha(p)
                for p in [*(repo/reg).glob("*.jsonl"),repo/"report.txt",repo/"report.html"]}
        batch.dump(out/"INPUTS.json", {"sha256":pins})
        (out/"FRAGMENTS.jsonl").write_text(json.dumps({"instrument_id":"EO:1","kind":"shared_factual_obligations",
                                            "data":fact.data})+"\n",encoding="utf-8")
        # Register held copies for the ACTUAL checker's independent custody index.
        held=repo/"jobs/interval-fixture/output"
        held.mkdir(parents=True)
        sources=[]
        for p in (repo/"jobs/future-source/data/texts").glob("*.txt"):
            if p.stem not in ("EO_1","EO_5"):continue
            raw=p.read_bytes()
            shutil.copyfile(p,held/p.name)
            sources.append({"instrument_ids":[p.stem.replace("_",":")],"url":"https://example.gov/"+p.stem,
                            "text_path":p.relative_to(repo).as_posix(),"cache_path":p.name,"sha256":F.MODEL.sha(raw)})
        shutil.copyfile(repo/"report.html",held/"report.html")
        shutil.copyfile(repo/"report.txt",held/"report.txt")
        sources.append({"url":"https://example.gov/report","text_path":"report.txt",
                        "cache_path":"report.html","sha256":batch.file_sha(repo/"report.html")})
        (held/"SOURCES.jsonl").write_text("".join(json.dumps(r)+"\n" for r in sources),encoding="utf-8")
        # Reuse the ordinary completion fixture to create a synthetic planted-control receipt.
        fx.setup_completion()
        packet=fx.folder
        dossiers=batch.load_packet(packet,repo)[1]
        eid=dossiers["EO:1"]["factual_interval_ids"][0]
        event=dossiers["EO:1"]["evidence"][eid]
        as_of = {day:F.observations_at(dossiers["EO:1"],day,repo=repo)[0]["classification"] for day in
                 ("1999-11-30","1999-12-01","1999-12-31")}
        rows=batch.rows(packet/"decisions.csv")
        rows[0].update(publication_kind="partial_research",
            source_notes=json.dumps([{"id":eid,"reason":"December delivery was reported; its legal effect remains unproved.",
                                     "date_qualification":event["date_qualification"]}]),
            unresolved_material_gaps=json.dumps(["Exact day of delivery and effect on the duty are unresolved."]))
        batch.csv_write(packet/"decisions.csv",batch.ROW_FIELDS,rows)
        clauses=batch.rows(packet/"clauses.csv")
        for c in clauses:
            if c["scope_id"]==app["scope_id"]:
                c.update(state="",end_id="",effective_date="",effective_date_confirmed="false",
                         reason="The witness supports a factual interval, not this command's legal end.")
        batch.csv_write(packet/"clauses.csv",batch.CLAUSE_FIELDS,clauses)
        applied=packet/"partial"
        batch.apply(repo,packet,applied)
        audit=json.loads((applied/"AUDIT.json").read_bytes())[0]
        assert audit.get("expected_gate_errors"),audit
        fx.producer=applied/"CLAIMS.proposed.jsonl"
        claim=json.loads(fx.producer.read_bytes())
        strict=batch.check(repo,packet,applied)
        errors=audit["expected_gate_errors"]
        C.batch.dump(fx.review_path, dict(fx.review,claim_sha256=C.claim_sha(claim),scope="partial_research",
                                         expected_gate_errors=errors))
        fx.manifest["members"][0].update(publication_kind="partial_research",claim_sha256=C.claim_sha(claim),
                          claim=fx.ref(fx.producer,line=1),review=fx.ref(fx.review_path))
        batch.dump(fx.manifest_path,fx.manifest)
        result=C.complete(repo,fx.manifest_path,fx.dest,False)
        if result["eligible"] != ["EO:1"]:
            raise ValueError(json.dumps({"result":result,"checked":strict,"checker":json.loads(
                (applied/"actual-checker/PER_CLAIM.json").read_bytes())},indent=2))
        assert not claim["whole_order_end"] and not any(c.get("first_end") for c in claim["operative_clauses"])
        selected = json.loads((fx.dest/"TRACKER_REPLAY.json").read_bytes())["selected"]["EO:1"]
        state = {k: {field: selected[k][field] for field in ("ready_for_human_review","blockers")}
                 for k in ("before", "after")}
        assert state["after"]["ready_for_human_review"] == "no"
        assert result["claims_published"] == 0
        (repo/"report.html").write_bytes(b"changed after the frozen review")
        try:
            batch.load_packet(packet,repo)
        except ValueError as exc:
            stale_refusal=str(exc)
        else:
            raise AssertionError("stale frozen registry evidence was accepted")
        return {"fixture_only":True,"dated_factual_observations":as_of,"stale_packet_refusal":stale_refusal,"model_authored_source_reviews":0,"production_status_writes":0,
                "elapsed_seconds":time.monotonic()-started,"gate_errors":errors,
                "strict_claim_pass":strict["strict_claim_pass"],"strict_claim_fail":strict["strict_claim_fail"],
                "actual_checker":strict["actual_claim_checker"],"eligible_partial_only":result["eligible"],
                "completion_outcomes":result["outcomes"],"tracker":state,
                "claims_published":result["claims_published"],"human_certifications":result["independent_human_certifications"]}
    finally:
        tracker.tearDown()
        fact.doCleanups()
        fx.doCleanups()

if __name__ == "__main__":
    print(json.dumps(run(),indent=2))

"""H6 review queue (coordinator tool; no judgment): when a batch is ready, builds its review set (only records with
something proposed), plants controls, renders two blind Opus reviewer prompts and appends both reviewers to plan.json."""
import json, subprocess, time, csv
from pathlib import Path
T = Path(__file__).resolve().parent; R = T.parents[3]; E = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H6")
READY = {"U1": "H6-w26", "U2": "H6-w29", "U3": "H6-w32", "U4": "H6-w23", "D1": "APPLY D1", "D2": "APPLY D2"}
log = lambda m: open(T.parent / "COORDINATOR_LOG.txt", "a").write(m + "\n")
def done(n):
    if n.startswith("APPLY"): return n in (T.parent / "COORDINATOR_LOG.txt").read_text()
    f = E / "run" / f"{n}.json"
    if (E / "run" / f"{n}.running").exists() or not f.exists(): return False
    try: return bool(json.loads(f.read_text()).get("session_id"))
    except Exception: return False
def proposed(r):
    if "operative_clauses" in r: return True
    sd = r.get("status_decision") or {}; dr = r.get("decision_row") or {}
    return sd.get("recommended_provisional_status") in ("yes", "no") or dr.get("outcome") == "submit"
todo = [b for b in READY if not (E / "review" / b / "REVIEW_SET_A.jsonl").exists()]
while todo:
    for b in list(todo):
        if not done(READY[b]): continue
        todo.remove(b)
        pk = "research/herschel/H6/packets/" + (b if b in ("D1", "D2", "U4") else "HAND/" + b)
        args = ["python3", "-I", str(T / "build_set.py"), b] + ([str(R / pk / "applied-v1")] if b in ("D1", "D2") else [])
        r = subprocess.run(args, capture_output=True, text=True)
        if r.returncode: log(f"REVIEWQ {b} build_set failed: {r.stderr[-300:]}"); continue
        full = [json.loads(l) for l in open(E / "review" / b / "SET.jsonl") if l.strip()]
        keep = [x for x in full if proposed(x)]
        skipped = sorted(x["instrument_id"] for x in full if not proposed(x))
        (E / "review" / b / "SET.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in keep))
        (E / "review" / b / "SKIPPED.json").write_text(json.dumps(skipped))
        if not keep: log(f"REVIEWQ {b} {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}: nothing proposed; no review. skipped={skipped}"); continue
        p = subprocess.run(["python3", "-I", str(T / "plant.py"), b, str(E / "review" / b / "SET.jsonl")], capture_output=True, text=True)
        log(f"REVIEWQ {b} {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}: {len(keep)} records, skipped (nothing proposed) {skipped}; plant {p.stdout.strip() or p.stderr[-300:]}")
        tmpl = (T / "prompts" / ("reviewer_claims.txt" if b in ("D1", "D2") else "reviewer_sheets.txt")).read_text()
        routenote = ("These orders are on the manual route: the claim kit holds no dossier for them (no dated status-history record), so sources are cited as held file paths with offsets." if b in ("U1", "U2", "U3")
                     else "These orders are in claim-kit packet " + str(R / pk) + " (PACKET.json frozen; undecided/EO_N/EVIDENCE.json holds each order's frozen evidence; you may read those and views/, but not decisions.csv, clauses.csv, undecided/*/STATUS_DECISION.json, notes/, outcomes/, original_text/, applied-v*).")
        plan = json.loads((T / "plan.json").read_text()); n = max(int(w["name"].split("-w")[1][:2]) for w in plan)
        names = []
        for arm in "AB":
            n += 1; name = f"H6-w{n:02d}"; names.append(name)
            out = str(R / pk / "reviews" / f"BLIND_REVIEW_{arm}.jsonl")
            (R / pk / "reviews").mkdir(exist_ok=True)
            t = tmpl.replace("{NAME}", name).replace("{ARM}", arm).replace("SETPATH", str(E / "review" / b / f"REVIEW_SET_{arm}.jsonl")).replace("PACKETDIR", str(R / pk)).replace("OUTPATH", out).replace("ROUTENOTE", routenote)
            pf = E / "prompts" / f"{name}.txt"; pf.write_text(t)
            plan.append({"name": name, "step": "review", "model": "opus", "batch": b, "arm": arm, "orders": [x["instrument_id"] for x in keep], "packet": pk, "parts": [], "deps": [], "prompt_file": str(pf), "review_out": out})
        for w in plan[-2:]: w["pair"] = names[1] if w["name"] == names[0] else names[0]
        (T / "plan.json").write_text(json.dumps(plan, indent=1, ensure_ascii=False))
        log(f"REVIEWQ {b}: reviewers {names[0]} (A) and {names[1]} (B) queued")
    time.sleep(30)

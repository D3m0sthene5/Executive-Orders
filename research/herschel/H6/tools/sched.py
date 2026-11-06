"""H6 scheduler (coordinator tool, no judgment): launches plan.json workers when their deps are done, at most MAXC at once.
Re-reads plan.json every loop so review workers can be appended. Prompts are rendered at launch from prompts/*.txt.
usage: python3 -I sched.py [MAXC]"""
import json, os, subprocess, sys, time
from pathlib import Path
T = Path(__file__).resolve().parent; E = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H6")
MAXC = int(sys.argv[1]) if len(sys.argv) > 1 else 12
MINMB = int(sys.argv[2]) if len(sys.argv) > 2 else 700
LASTWARN = [0]
BLOCKED = {"D1": "EO:1834", "D2": "EO:13661", "U4": "EO:13821"}
CLOSE = ("\nYOU ALSO CLOSE THE SHEET (no counterevidence step is open for these orders): after your savings columns, set for each "
         "row outcome (submit, blocked, unresolved or route_owner), approved (true only after your own source review of the whole row), "
         "research_rationale, agent \"claude\", and fill search_ids / conflict_resolutions / unresolved_material_gaps only as far as the "
         "assembler needs them (select only machine searches whose scope you read).\n")
PROJ = Path.home() / ".claude/projects/-tmp-claude-0--home-claude-1b28d9a2-1935-5c00-acfa-76feacb7b775-scratchpad-herschel-H6-run"
def state(n):
    if (E / "run" / f"{n}.running").exists(): return "running"
    f = E / "run" / f"{n}.json"
    if not f.exists(): return "pending"
    try: d = json.loads(f.read_text())
    except Exception: return "failed"
    return "done" if d.get("session_id") and not d.get("is_error") else "failed"
def find_sid(n):
    best = None
    for f in PROJ.glob("*.jsonl"):
        with open(f) as fh:
            for i, l in enumerate(fh):
                if i > 6: break
                if f"worker {n} " in l or f"You are {n}," in l: best = (f.stat().st_mtime, f.stem)
    return best and best[1]
def render(w):
    if w.get("prompt_file"): return w["prompt_file"]
    P = lambda x: (T / "prompts" / f"{x}.txt").read_text()
    step = "\n".join(P(x) for x in w["parts"])
    plan = json.loads((T / "plan.json").read_text())
    last = [x for x in plan if x["batch"] == w["batch"] and x["step"] not in ("review", "reveal")][-1]["name"] == w["name"]
    if last and w["step"] == "savings_residuals": step += CLOSE
    kit = not w["packet"].split("/")[-2] == "HAND"
    b = BLOCKED.get(w["batch"])
    note = (f"Only the ORDERS listed are yours. Packet member {b} failed the dispatch check (source custody); the coordinator fills its row; do not touch it." if b and kit else "Only the ORDERS listed are yours.")
    orig = ("the packet's views/EO_N.json and READ.md (the dossier's original_source_id and evidence)" if kit else "the bundle research/herschel/H6/packets/HAND/EO_N.json")
    step = step.replace("ORDERSNOTE", note).replace("ORIGINALSOURCE", orig)
    c = P("common").replace("STEPTEXT", "\x00").replace("{NAME}", w["name"]).replace("{STEP}", w["step"]).replace("{ORDERS}", " ".join(w["orders"]))
    t = c.replace("\x00", step).replace("PACKETDIR", "/home/claude/executive-orders/" + w["packet"])
    f = E / "prompts" / f"{w['name']}.txt"; f.write_text(t); return str(f)
while True:
    plan = json.loads((T / "plan.json").read_text())
    st = {w["name"]: state(w["name"]) for w in plan}
    running = len(list((E / "run").glob("*.running")))
    changed = False
    for w in plan:
        if st[w["name"]] == "failed" and len(w.get("attempts", [])) < 4:
            sid = find_sid(w["name"]); k = len(w.get("attempts", [])) + 1
            for ext in ("json", "err"):
                p = E / "run" / f"{w['name']}.{ext}"
                if p.exists(): p.rename(p.with_name(p.name + f".killed{k}"))
            w.setdefault("attempts", []).append({"session_id": sid, "result": "killed_or_error"})
            if sid: w["resume"] = sid; w["prompt_file"] = str(E / "prompts/continue.txt")
            st[w["name"]] = "pending"; changed = True
            with open(T.parent / "COORDINATOR_LOG.txt", "a") as L: L.write(f"RETRY {w['name']} attempt {k} {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} resume={sid}\n")
    if changed: (T / "plan.json").write_text(json.dumps(plan, indent=1, ensure_ascii=False))
    for w in plan:
        if running >= MAXC: break
        if st[w["name"]] == "pending" and all(st.get(d) == "done" for d in w["deps"]) and not w.get("hold"):
            avail = int(next(l for l in open("/proc/meminfo") if l.startswith("MemAvailable")).split()[1]) // 1024
            if avail < MINMB:
                if time.time() - LASTWARN[0] > 300:
                    print(time.strftime("%H:%M:%S"), f"MEMGUARD defer {w['name']} MemAvailable={avail}MB running={running}", flush=True); LASTWARN[0] = time.time()
                break
            pf = render(w)
            (E / "run" / f"{w['name']}.running").touch()  # reserve the slot; launch.sh re-touches and removes at the end
            subprocess.Popen(["bash", str(T / "launch.sh"), w["name"], w["model"], pf] + ([w["resume"]] if w.get("resume") else []),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            st[w["name"]] = "running"; running += 1
            print(time.strftime("%H:%M:%S"), "launched", w["name"], w["step"], w["batch"], "running", running, flush=True)
    if all(v == "done" for v in st.values()) and not (T / "KEEP_ALIVE").exists():
        print("ALL DONE", flush=True); break
    time.sleep(20)

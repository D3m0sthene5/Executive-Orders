"""H6 evidence bundle for undecided orders the claim kit cannot freeze (no dated status-history record).
Coordinator tool, no legal judgment: collects held leads per order into packets/HAND/EO_N.json.
usage: python3 -I research/herschel/H6/tools/bundle.py EO:N ..."""
import csv, json, subprocess, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "jobs/_lib")); csv.field_size_limit(10**9)
import eo_identity as I
ids = sys.argv[1:]; want = set(ids)
out = REPO / "research/herschel/H6/packets/HAND"; out.mkdir(parents=True, exist_ok=True)
def rows(p, key="instrument_id"):
    return {r[key]: r for r in csv.DictReader(open(REPO / p, newline="", encoding="utf-8")) if r.get(key) in want}
reg = rows("jobs/domesday-register/output/REGISTER.csv"); rdy = rows("jobs/readiness-tracker/output/READINESS_BY_ORDER.csv")
smp = rows("research/herschel/frame/SAMPLE_R2.csv"); frags = I.load_fragments(str(REPO))
edges = {i: [] for i in ids}
for r in csv.DictReader(open(REPO / "jobs/later-events/output/EDGES.csv", newline="", encoding="utf-8")):
    for k in ("target_id", "acting_id"):
        if r[k] in want: edges[r[k]].append({"as": k, **{x: r[x] for x in ("edge_id","acting_id","target_id","mechanism","qualifier","date_candidate","evidence_type","source_id","source_url","quote")}})
for i in ids:
    n = i.split(":", 1)[1]; cf = out / f"cruden-EO_{n}.json"
    subprocess.run([sys.executable, "-I", str(REPO / "research/excavator/claude-nira-sweep-2026-10-29/cruden.py"), "number", i, "--write", str(cf)], cwd=REPO, capture_output=True)
    try: cr = json.loads(cf.read_text())
    except Exception as e: cr = {"error": str(e)}
    b = {"instrument_id": i, "note": "Held leads only; nothing here decides identity, status or an end. The claim kit cannot freeze this order (status-history INDEX has no dated history), so there is no dossier or packet.",
         "register": reg.get(i), "readiness": rdy.get(i), "herschel_sample": smp.get(i),
         "held_fragments": [{k: f.get(k) for k in ("grade","acceptable_as_original","text_path","sha256","url","title","date","page_or_item") if f.get(k) is not None} for f in frags.get(i, [])],
         "later_events_edges": edges[i], "cruden_number_hits_file": str(cf.relative_to(REPO)), "cruden_number_hits": cr}
    (out / f"EO_{n}.json").write_text(json.dumps(b, indent=1, ensure_ascii=False))
    print(i, len(b["held_fragments"]), "frags", len(edges[i]), "edges")

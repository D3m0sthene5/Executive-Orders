"""List the Herschel sampled orders whose root blockers include 'legal_sources', with each blocking acquisition text.
Uses research/herschel/project.py's own loader and classifier so the classes match the published BLOCKERS.csv."""
import json, sys, collections
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/herschel"))
import project as P  # noqa

orders, assigned, workers, outcomes, usage, limits = P.load()
by = collections.defaultdict(dict)
for (iid, step), v in outcomes.items():
    by[iid][step] = v["outcome"]
out = []
for iid, steps in sorted(by.items()):
    acqs = {s: P.acquisition(o) for s, o in steps.items() if P.acquisition(o)}
    classes = {P.blocker_class(a) for a in acqs.values()} - {"knock_on"}
    if "legal_sources" in classes:
        out.append({"instrument_id": iid, "stratum": orders.get(iid, {}).get("stratum"),
                    "sole": classes == {"legal_sources"}, "classes": sorted(classes),
                    "legal_acquisitions": {s: a for s, a in acqs.items() if P.blocker_class(a) == "legal_sources"}})
json.dump(out, sys.stdout, indent=1)

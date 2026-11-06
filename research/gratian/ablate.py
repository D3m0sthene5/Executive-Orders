"""Gratian ablation: run the readiness tracker with and without each product's registered inputs.

Usage (from the repository root, offline, no tokens):
    python3 -I research/gratian/ablate.py --out research/gratian/ablation

Each variant is the unmodified tracker build() with one change to the module's J table (which job outputs the
tracker reads). Nothing is written outside --out, and nothing here changes a status, grade, claim or count.

A product the tracker does not read cannot move a tracker count; such products are reported from their own
outputs in research/gratian/CONCORDANCE.csv, not here. A product registered only on an unmerged branch is
measured when its output files are present in the working tree (copied there by the operator for the run and
removed afterwards); the variant says so.
"""
import argparse
import collections
import copy
import csv
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRACKER = ROOT / "jobs/readiness-tracker/tracker.py"
MABILLON = "jobs/mabillon-held-printings/output/FRAGMENTS.jsonl"
TISCHENDORF = "jobs/tischendorf-originals/output/FRAGMENTS.jsonl"
PTOLEMY = "jobs/ptolemy-custody/output/SOURCES.jsonl"


def ptolemy_opus_keys():
    """Opus re-fetch keys for bytes Ptolemy holds with the exact hash Opus recorded (same rule as source-ladder)."""
    keys = set()
    path = ROOT / PTOLEMY
    if path.exists():
        for line in path.read_text("utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if r.get("sha256") and r.get("cache_path") and (path.parent / r["cache_path"]).exists():
                    keys.add("opus-refetch:" + r["sha256"])
    return keys


def load_tracker():
    spec = importlib.util.spec_from_file_location("gratian_tracker", TRACKER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def without(paths, drop):
    return [p for p in paths if p not in drop]


def variants(J):
    official = J["official_compilation_fragments"]
    have_mabillon = (ROOT / MABILLON).exists()
    with_mab = official + ([MABILLON] if have_mabillon and MABILLON not in official else [])
    v = collections.OrderedDict()
    v["main"] = {}
    v["main_minus_tischendorf"] = {"official_compilation_fragments": without(official, {TISCHENDORF})}
    v["main_minus_lachmann"] = {"working_text_confirmations": []}
    v["main_minus_tischendorf_lachmann"] = {"official_compilation_fragments": without(official, {TISCHENDORF}),
                                            "working_text_confirmations": []}
    if have_mabillon:
        v["main_plus_mabillon"] = {"official_compilation_fragments": with_mab}
        v["all_products"] = {"official_compilation_fragments": with_mab}
        v["all_products_plus_ptolemy_opus"] = {"official_compilation_fragments": with_mab, "_ptolemy_opus": True}
    return v, have_mabillon


def one_step(o):
    steps = {k[5:]: v for k, v in o.items() if k.startswith("step_")}
    applicable = [s for s, v in steps.items() if v != "n/a"]
    open_ = [s for s in applicable if steps[s] == "open"]
    return open_


def claim_ready(o):
    s = {k[5:]: v for k, v in o.items() if k.startswith("step_")}
    return (o["provisional_status"] and s["original_text"] in ("done", "provisional") and s["counterevidence"] == "done"
            and all(s[k] == "open" for k in ("clause_inventory", "ending_or_current_basis", "savings_residuals")))


def measure(orders):
    ready = {o["instrument_id"] for o in orders if o["ready_for_human_review"] == "yes"}
    one = {o["instrument_id"]: one_step(o) for o in orders
           if o["ready_for_human_review"] != "yes" and o["claim_present"] == "yes" and len(one_step(o)) == 1}
    no_open = {o["instrument_id"] for o in orders
               if o["ready_for_human_review"] != "yes" and o["provisional_status"] and not one_step(o)}
    cr = {o["instrument_id"] for o in orders if o["ready_for_human_review"] != "yes" and claim_ready(o)}
    text_done = {o["instrument_id"] for o in orders if o["provisional_status"] and o["step_original_text"] != "open"}
    return {"ready": ready, "one_step_away": one, "all_steps_done_not_ready": no_open,
            "claim_ready_stratum": cr, "text_step_satisfied_decided": text_done}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="research/gratian/ablation")
    a = ap.parse_args()
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    os.chdir(ROOT)
    T = load_tracker()
    base_J = copy.deepcopy(T.J)
    original_loader = T.load_job_outputs
    extra = ptolemy_opus_keys()
    vs, have_mabillon = variants(base_J)
    results, rows_by_variant = {}, {}
    for name, change in vs.items():
        T.J.clear()
        T.J.update(copy.deepcopy(base_J))
        T.J.update({k: v for k, v in change.items() if not k.startswith("_")})

        def loader(root, _ptolemy=change.get("_ptolemy_opus")):
            jobs, problems_ = original_loader(root)
            if _ptolemy:  # Opus media step only: the shared-source step keys on authorities, not hashes
                jobs["ladder_found"] = set(jobs["ladder_found"]) | extra
            return jobs, problems_
        T.load_job_outputs = loader
        orders, problems = T.build(str(ROOT))
        m = measure(orders)
        rows_by_variant[name] = {o["instrument_id"]: o for o in orders}
        results[name] = {"change": {k: v for k, v in change.items()}, "ready": len(m["ready"]), "one_step_away": len(m["one_step_away"]),
                         "all_steps_done_not_ready": len(m["all_steps_done_not_ready"]),
                         "claim_ready_stratum": len(m["claim_ready_stratum"]),
                         "text_step_satisfied_decided": len(m["text_step_satisfied_decided"]),
                         "input_problems": len(problems), "_m": m}
        print(name, {k: v for k, v in results[name].items() if k not in ("_m", "change")}, flush=True)

    def delta(a_, b_, key):
        A, B = results[a_]["_m"][key], results[b_]["_m"][key]
        return {"gained": sorted(set(B) - set(A)), "lost": sorted(set(A) - set(B))}

    contributions = {
        "tischendorf": ("main_minus_tischendorf", "main"),
        "lachmann": ("main_minus_lachmann", "main"),
        "tischendorf_and_lachmann": ("main_minus_tischendorf_lachmann", "main"),
    }
    if have_mabillon:
        contributions["mabillon"] = ("main", "main_plus_mabillon")
        contributions["ptolemy_opus_registration"] = ("all_products", "all_products_plus_ptolemy_opus")
    contrib = {}
    for product, (a_, b_) in contributions.items():
        contrib[product] = {k: delta(a_, b_, k) for k in
                            ("ready", "one_step_away", "claim_ready_stratum", "text_step_satisfied_decided")}
    summary = {"schema": "gratian-ablation/v1", "mabillon_outputs_present": have_mabillon,
               "variants": {k: {x: y for x, y in v.items() if x != "_m"} for k, v in results.items()},
               "contributions": {p: {k: {"gained": len(v["gained"]), "lost": len(v["lost"])} for k, v in d.items()}
                                 for p, d in contrib.items()},
               "notice": "Tracker counts only. Ready for human review is never human certification (certified: 0)."}
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "CONTRIBUTIONS.json").write_text(json.dumps(contrib, indent=1, sort_keys=True) + "\n")
    final = "all_products_plus_ptolemy_opus" if have_mabillon else "main"
    fields = ["instrument_id", "provisional_status", "ready_for_human_review", "claim_present", "steps_done",
              "steps_applicable", "open_steps", "blockers", "claim_record_errors"]
    with open(out / "FINAL_ORDERS.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for i, o in sorted(rows_by_variant[final].items()):
            if not o["provisional_status"]:
                continue
            w.writerow({**{k: o[k] for k in fields if k in o}, "open_steps": "|".join(one_step(o))})
    print(json.dumps(summary["contributions"], indent=1))


if __name__ == "__main__":
    main()

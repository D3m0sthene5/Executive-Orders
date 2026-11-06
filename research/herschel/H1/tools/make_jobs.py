"""Builds the H1 job graph (coordinator tool). usage: python3 -I research/herschel/H1/tools/make_jobs.py > JOBS.json"""
import csv
import json
from pathlib import Path

H = Path("/home/claude/executive-orders/research/herschel/H1")
S = "/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H1"
B = json.load(open(H / "tools/batches.json"))
O = {r["instrument_id"]: r for r in csv.DictReader(open(H.parent / "frame/ORDERS.csv"))}
jobs = [{"name": "H1-w01", "kind": "worker", "step": "admit", "model": "sonnet", "batch": "admission",
         "orders": [], "prompt": str(H / "tools/prompts/admit.txt")}]
n = 2


def w(step, body, out, batch, orders, deps, extra=None):
    global n
    j = {"name": f"H1-w{n:02d}", "kind": "worker", "step": step, "model": "sonnet", "body": body, "out": out,
         "batch": batch, "orders": orders, "deps": deps}
    n += 1
    jobs.append(j)
    return j["name"]


names = {}
for b, ids in B.items():
    ot = [i for i in ids if "original_text" in O[i]["open_steps"]]
    names[b, "ot"] = w("original_text", "step_original_text.txt", "ORIGINAL_TEXT.jsonl", b, ot, []) if ot else None
    names[b, "st"] = w("provisional_status", "step_provisional_status.txt", "STATUS.jsonl", b, ids, [])
    names[b, "inv"] = w("clause_inventory", "step_clause_inventory.txt", "INVENTORY.jsonl", b, ids,
                        [x for x in [names[b, "ot"]] if x])
    names[b, "end"] = w("ending_or_current_basis", "step_ending.txt", "ENDING.jsonl", b, ids,
                        [names[b, "inv"], names[b, "st"]])
    names[b, "sav"] = w("savings_residuals", "step_savings.txt", "SAVINGS.jsonl", b, ids, [names[b, "end"]])
    names[b, "ctr"] = w("counterevidence", "step_counterevidence.txt", "COUNTER.jsonl", b, ids, [names[b, "sav"]])
ro = [i for b in B for i in B[b] if O[i]["transcription_dependent"] == "True"]
ro_deps = [names[b, k] for b in B for k in ("inv", "st") if any(i in B[b] for i in ro)]
ro_name = w("replace_original", "step_replace_original.txt", "REPLACE_ORIGINAL.jsonl", "b3", ro, ro_deps)
jobs[-1]["note"] = ("evidence and steps for orders outside b3 are in that order's own batch folder: "
                    + "; ".join(f"{i} -> {H}/packets/{b}" for b in B for i in B[b] if i in ro))
for b in B:
    deps = [names[b, "ctr"]] + ([ro_name] if any(i in B[b] for i in ro) else [])
    jobs.append({"name": f"prep-{b}", "kind": "cmd", "deps": deps,
                 "cmd": f"python3 -I research/herschel/H1/tools/split_ro.py && python3 -I research/herschel/H1/tools/review_prep.py prep {b}"})
    rv = {}
    for arm in "AB":
        rv[arm] = f"H1-w{n:02d}"; n += 1
        jobs.append({"name": rv[arm], "alias": f"rev-{b}-{arm}", "kind": "worker", "step": "review", "model": "opus",
                     "batch": b, "orders": B[b], "deps": [f"prep-{b}"], "prompt": f"{S}/prompts/rev-{b}-{arm}.txt"})
    jobs.append({"name": f"check-{b}", "kind": "cmd", "deps": [rv["A"], rv["B"]],
                 "cmd": f"python3 -I research/herschel/H1/tools/review_prep.py check {b}"})
    for arm in "AB":
        jobs.append({"name": rv[arm] + "-reveal", "kind": "resume", "step": "review", "model": "opus", "batch": b,
                     "of": rv[arm], "deps": [f"check-{b}"], "prompt": f"{S}/prompts/reveal-{b}-{arm}.txt"})
print(json.dumps(jobs, indent=1))

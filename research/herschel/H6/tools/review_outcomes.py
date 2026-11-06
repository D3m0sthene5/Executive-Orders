"""H6 review outcomes (coordinator tool, mechanical): per-arm verdicts into plan.json review workers; combined per-order
review outcome (both arms must uphold both scopes; a planted order is judged on its after-reveal genuine verdicts) into
../REVIEW_OUTCOMES.json. Control catch = both arms rejected the planted record."""
import json
from pathlib import Path
T = Path(__file__).resolve().parent; H = T.parent
E = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H6")
plan = json.loads((T / "plan.json").read_text()); B = json.loads((T / "batches.json").read_text())
ok = lambda v: v is None or v.replace("_after_reveal", "") in ("upheld", "upheld_block", "not_applicable")
comb, controls = {}, []
for b in B:
    revs = [w for w in plan if w["step"] == "review" and w["batch"] == b]
    skipped = json.loads((E / "review" / b / "SKIPPED.json").read_text()) if (E / "review" / b / "SKIPPED.json").exists() else B[b]
    if not revs: skipped = B[b]
    for i in skipped: comb[i] = "not_applicable:nothing_proposed (all steps blocked or no status proposed)"
    if not revs: continue
    key = {c["instrument_id"]: c for c in json.loads((E / "keys" / f"{b}.json").read_text())["controls"]}
    arms = {}
    for w in revs:
        lines = [json.loads(l) for l in open(w["review_out"]) if l.strip()]
        n = len(w["orders"]); blind, after = lines[:n], lines[n:]
        w["outcomes"] = {}
        for d in blind + after:
            tag = "after_reveal" if d in after else "blind"
            v = [d.get("status_verdict"), d.get("lifecycle_verdict") or d.get("verdict")]
            w["outcomes"][d["instrument_id"] + ("" if tag == "blind" else "#genuine")] = "upheld" if all(ok(x) for x in v) else \
                "rejected:" + "; ".join(str(x.get("field") if isinstance(x, dict) else x) for x in d.get("defects", []))[:300]
        arms[w["arm"]] = w["outcomes"]
    for i in key:
        caught = all(arms[a].get(i, "").startswith("rejected") for a in arms)
        controls.append({"batch": b, "instrument_id": i, "defect": key[i]["defect"], "caught_by_both_arms": caught,
                         "arm_verdicts": {a: arms[a].get(i) for a in arms}})
    for i in revs[0]["orders"]:
        k = i + "#genuine" if i in key else i
        vs = {a: arms[a].get(k, "missing") for a in arms}
        comb[i] = "upheld" if all(v == "upheld" for v in vs.values()) else "rejected:" + " | ".join(f"{a}: {v}" for a, v in vs.items() if v != "upheld")
(T / "plan.json").write_text(json.dumps(plan, indent=1, ensure_ascii=False))
(H / "REVIEW_OUTCOMES.json").write_text(json.dumps({"orders": comb, "controls": controls}, indent=1, ensure_ascii=False))
for i, v in comb.items():
    if not v.startswith("not_applicable"): print(i, v[:160])
print(controls)

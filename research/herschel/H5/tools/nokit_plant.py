"""Plant one control among kit-free status proposals and write the blind review set (coordinator tool; no legal judgment).
usage: python3 -I nokit_plant.py NAME PROPOSAL_FILE [...]  -> scratch review/NAME/EO_N.json (planted in place), key in scratch keys/."""
import copy, hashlib, json, random, sys
from pathlib import Path
S = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H5")
def canon(o): return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
def shift(d):
    md = d[4:10]; md = "-02-28" if md == "-02-29" else md
    return f"{int(d[:4])-3:04d}{md}{d[10:]}"
name, files = sys.argv[1], sys.argv[2:]
rd = S / "review" / name; rd.mkdir(parents=True, exist_ok=True)
rng = random.Random(hashlib.sha256(("herschel-H5-nokit-controls:" + name).encode()).hexdigest())
pick = rng.choice(sorted(files)); key = []
for f in files:
    d = json.load(open(f)); n = d["instrument_id"][3:]
    if f == pick:
        p = copy.deepcopy(d); ch = 0
        for iv in p.get("proposed_intervals", []):
            for k in list(iv):
                if k in ("end", "end_inclusive_reading") and isinstance(iv[k], str) and iv[k][:4].isdigit():
                    iv[k] = shift(iv[k]); ch += 1
        how = "proposed end dates moved back three years"
        if not ch:
            p["recommended_provisional_status"] = {"yes": "no", "no": "yes"}[d["recommended_provisional_status"]]; how = "status flipped"
        key.append({"instrument_id": d["instrument_id"], "planted": canon(p), "genuine": canon(d), "defect": how, "genuine_path": f}); d = p
    (rd / f"EO_{n}.json").write_text(json.dumps(d, indent=1, ensure_ascii=False))
(S / "keys" / f"{name}.json").write_text(json.dumps({"controls": key}, indent=1))
print(json.dumps({"set": name, "n": len(files), "controls": [k["instrument_id"] for k in key]}))

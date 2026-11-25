"""Seeded disjoint draw of two arms from a pool of order ids (Junto lean two-arm trial).

Usage: python3 -I jobs/junto/lean_draw.py POOL.txt SEED OUT_DIR [N]
POOL.txt has one order id per line. Writes OUT_DIR/arm0_ids.txt, arm1_ids.txt and DRAW.json
(seed, pool sha256, per-arm id lists and sha256). Deterministic: same pool and seed, same draw.
"""
import hashlib, json, random, sys
from pathlib import Path


def main(argv):
    if len(argv) < 4:
        print(__doc__); return 2
    pool_path, seed, out = Path(argv[1]), argv[2], Path(argv[3])
    n = int(argv[4]) if len(argv) > 4 else 30
    raw = pool_path.read_bytes()
    pool = sorted({l.strip() for l in raw.decode().splitlines() if l.strip()})
    if len(pool) < 2 * n:
        print("pool has %d ids, need %d" % (len(pool), 2 * n)); return 1
    picks = random.Random(seed).sample(pool, 2 * n)
    arms = {"arm0": sorted(picks[:n]), "arm1": sorted(picks[n:])}
    out.mkdir(parents=True, exist_ok=True)
    rec = {"seed": seed, "n_per_arm": n, "pool_sha256": hashlib.sha256(raw).hexdigest(), "pool_size": len(pool), "arms": {}}
    for k, ids in arms.items():
        text = "\n".join(ids) + "\n"
        (out / (k + "_ids.txt")).write_text(text)
        rec["arms"][k] = {"ids": ids, "sha256": hashlib.sha256(text.encode()).hexdigest()}
    assert not set(arms["arm0"]) & set(arms["arm1"])
    (out / "DRAW.json").write_text(json.dumps(rec, indent=1) + "\n")
    print("drew %d + %d disjoint ids; arm0 %s arm1 %s" % (n, n, rec["arms"]["arm0"]["sha256"][:12], rec["arms"]["arm1"]["sha256"][:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

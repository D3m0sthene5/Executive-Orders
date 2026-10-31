#!/usr/bin/env python3
"""Jacquard job: select the lots and draw the samples. Offline, deterministic, writes only OUTPUT_DIR.

Packets need a scratch directory and reviews come from reviewer agents, so run the later steps locally with
`python3 jobs/jacquard/jacquard.py {packets,verify,accept,propose}` (see README.md).
"""
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jacquard  # noqa: E402


def main():
    out = Path(os.environ.get("OUTPUT_DIR", HERE / "output"))
    repo = Path(os.environ.get("REPO_ROOT", HERE.parents[1])).resolve()
    out.mkdir(parents=True, exist_ok=True)
    cfg = jacquard.load_config(HERE / "lots.json")
    members, counts, calibration = jacquard.step_select(repo, out, cfg)
    samples = jacquard.step_sample(out, cfg)
    summary = {"seed": cfg["seed"], "sample_size": cfg["sample_size"], "full_review_max": cfg["full_review_max"],
               "lots": {k: dict(counts[k], mode=samples["lots"][k]["mode"], sample_n=samples["lots"][k]["sample_n"],
                                controls_to_plant=jacquard.control_count(samples["lots"][k]["sample_n"]))
                        for k in counts},
               "needed_folders_beyond_jobs": jacquard.needed_dirs(members),
               "calibration": calibration}
    jacquard.write_json(out / "SUMMARY.json", summary)
    for k, v in summary["lots"].items():
        print(k, v["members"], v["mode"], v["sample_n"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

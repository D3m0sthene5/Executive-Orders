"""Arsenale validation probe (branch-only; removed before merge). Runs after probe-a in the same station."""
import json, os, socket, time
from pathlib import Path

upstream = json.loads(Path("jobs/arsenale-probe-a/output/PROBE.json").read_text(encoding="utf-8"))
record = {"job": os.environ["JOB_NAME"], "start_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
          "host": socket.gethostname(), "saw_probe_a": upstream}
print(json.dumps(record))
Path(os.environ["OUTPUT_DIR"], "PROBE.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

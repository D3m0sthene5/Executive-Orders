"""Arsenale validation probe (branch-only; removed before merge). Sleeps, then records when and where it ran."""
import json, os, socket, time
from pathlib import Path

name = os.environ["JOB_NAME"]
out = Path(os.environ["OUTPUT_DIR"])
start = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
time.sleep(int(Path(os.environ["JOB_DIR"], "SECONDS").read_text().strip()))
request = Path("research/arsenale-probe", name.rsplit("-", 1)[1], "request.txt").read_text(encoding="utf-8")
end = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
record = {"job": name, "start_utc": start, "end_utc": end, "host": socket.gethostname(),
          "runner": os.environ.get("RUNNER_NAME"), "input_commit": os.environ.get("GITHUB_SHA"), "request": request}
print(json.dumps(record))
(out / "PROBE.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

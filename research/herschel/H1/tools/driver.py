"""Herschel H1 driver (coordinator tool; no legal judgment).

usage: python3 -I research/herschel/H1/tools/driver.py JOBS.json

Runs a dependency graph of jobs with at most CONC model workers at once (H1: 4). Job kinds:
  worker  one fresh headless Claude Code session (launch.sh) doing one step for one batch
  resume  one follow-up message into an earlier worker's session (after-reveal review)
  cmd     a deterministic coordinator command (no model)
A production worker (any step other than review/reveal) is not started once SCRATCH/STOP exists
(a planted-control miss). Every start/finish is logged to SCRATCH/DRIVER_LOG.jsonl.
"""
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/home/claude/executive-orders")
H = REPO / "research/herschel/H1"
S = Path("/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H1")
CONC = 4


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(**k):
    with open(S / "DRIVER_LOG.jsonl", "a") as f:
        f.write(json.dumps({"t": now(), **k}) + "\n")


def render(job):
    """Prompt = common header + step body, with placeholders filled."""
    t = H / "tools/prompts"
    body = (t / "common.txt").read_text() + "\n" + (t / job["body"]).read_text()
    bdir = str(H / "packets" / job["batch"])
    rep = {"WORKER": job["name"], "STEPNAME": job["step"], "BATCHDIR": bdir,
           "ORDERLIST": ", ".join(job["orders"]), "OUTFILE": bdir + "/steps/" + job["out"]}
    for k, v in rep.items():
        body = body.replace(k, v)
    if job.get("note"):
        body += "\nNOTE: " + job["note"] + "\n"
    (H / "packets" / job["batch"] / "steps").mkdir(parents=True, exist_ok=True)
    p = S / "prompts" / (job["name"] + ".txt")
    p.write_text(body)
    return p


def session_of(name):
    return json.load(open(S / "run" / (name + ".json"))).get("session_id")


def start(job):
    k = job["kind"]
    if k == "cmd":
        return subprocess.Popen(job["cmd"], shell=True, cwd=REPO,
                                stdout=open(S / "run" / (job["name"] + ".out"), "w"), stderr=subprocess.STDOUT)
    if k == "worker":
        p = job.get("prompt") or str(render(job))
        return subprocess.Popen([str(H / "tools/launch.sh"), job["name"], job["model"], p], cwd=REPO)
    if k == "resume":
        return subprocess.Popen([str(H / "tools/launch.sh"), job["name"], job["model"], job["prompt"],
                                 session_of(job["of"])], cwd=REPO)
    raise ValueError(k)


def main(path):
    jobs = json.load(open(path))
    done, running, failed = set(), {}, set()
    for j in jobs:
        if (S / "run" / (j["name"] + ".json")).exists() and j["kind"] != "cmd":
            done.add(j["name"])  # resumable: finished workers are not rerun
    while True:
        for name, (proc, job) in list(running.items()):
            rc = proc.poll()
            if rc is not None:
                del running[name]
                (done if rc == 0 else failed).add(name)
                log(event="end", name=name, rc=rc, kind=job["kind"])
        pending = [j for j in jobs if j["name"] not in done | failed | set(running)]
        if not pending and not running:
            break
        busy = sum(1 for _, j in running.values() if j["kind"] != "cmd")
        progressed = False
        for j in pending:
            if any(d in failed for d in j.get("deps", [])):
                failed.add(j["name"]); log(event="skip_dep_failed", name=j["name"]); progressed = True; continue
            if not all(d in done for d in j.get("deps", [])):
                continue
            if j["kind"] == "worker" and j.get("step") not in ("review",) and (S / "STOP").exists():
                failed.add(j["name"]); log(event="skip_stop", name=j["name"]); progressed = True; continue
            if j["kind"] != "cmd" and busy >= CONC:
                continue
            running[j["name"]] = (start(j), j)
            if j["kind"] != "cmd":
                busy += 1
            log(event="start", name=j["name"], kind=j["kind"], busy=busy)
            progressed = True
        if not progressed:
            time.sleep(10)
    log(event="driver_done", done=sorted(done), failed=sorted(failed))


if __name__ == "__main__":
    main(sys.argv[1])

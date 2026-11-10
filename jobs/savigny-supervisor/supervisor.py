"""Savigny supervisor: run headless Codex lanes and a coordinator, and stop them on measured waste.

Named for the overnight chain of 2026-11-09/10, in which a Codex coordinator, SAVIGNY, ran Mommsen lanes. That
night about half the owner's weekly Codex allowance bought 12 filed claims, because nothing stopped spend that
was not producing claims. This is that night's supervisor rebuilt so it cannot happen again. Every limit acts on
measurements (meter.py reads the agents' own token logs and the lanes' claim files), never on what an agent
reports about itself.

  python -I jobs/savigny-supervisor/supervisor.py --root C:/Users/danie/eo-wt/_savigny

The runtime folder (--root) holds WAVE.json (the run's plan), lanes.json, prompts/, status/, inbox/, directives/,
logs/ and state.json. See README.md. The supervisor refuses to start unless WAVE.json passes Augur
(jobs/augur-launch/augur.py). The plan's limits are the run's limits.

Limits (WAVE.json "limits"; all required keys are listed in LIMIT_KEYS):
- chain_budget_units: total usage units for the whole run. At 100%, every turn is killed and STOP is written.
- spend_per_claim_units: units a lane may spend since its last new verified claim. Over it, the lane is paused.
- no_claim_minutes: minutes of running turns since a lane's last new verified claim. Over it, the lane is paused.
- context_kill_tokens: a lane turn whose own latest call carries more context than this is killed. The next turn
  starts a fresh session from the lane's handoff packet.
- reviews_per_hour: auto-review sessions a lane may cause per hour. Over it, the lane is paused (sandbox gap).
- coordinator_units_per_hour: the coordinator's own spend per hour. Over it, the coordinator waits an hour.
Every turn starts a fresh session (no resume), so no context grows across turns.
"""

import argparse
import datetime
import glob
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "carnot-coordinator"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "augur-launch"))
import augur  # noqa: E402
import meter  # noqa: E402

COORD = "_savigny"
MODEL = os.environ.get("SAVIGNY_MODEL", "gpt-6.1-sol")
EFFORT = os.environ.get("SAVIGNY_EFFORT", "xhigh")   # the owner's choice; the waste measured was re-reads, not reasoning
GITDIR = os.environ.get("SAVIGNY_GITDIR", r"C:\Users\danie\Projects\Executive-Orders\.git")
LIMIT_KEYS = ("chain_budget_units", "spend_per_claim_units", "no_claim_minutes", "context_kill_tokens",
              "reviews_per_hour", "coordinator_units_per_hour")
STAGGER = 5 * 60
COORD_MIN_GAP = 10 * 60
TURN_MAX = 2 * 3600
SHORT_TURN = 120
METER_EVERY = 60
TICK = 15


def now():
    return time.time()


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


def write_json(path, data):
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    os.replace(tmp, path)


class Chain:
    """One run of the chain over a runtime folder. Construct, then call run()."""

    def __init__(self, root, fake=False, metered=None, clock=None, preflight=None):
        self.root = Path(root)
        self.fake = fake
        self.metered = metered or self.measure          # tests inject a fake meter
        self.clock = clock or now
        cfg = read_json(self.root / "lanes.json", None)
        if not cfg or not cfg.get("lanes"):
            raise SystemExit("lanes.json must name the lanes and their worktrees: {\"lanes\": {name: path}}")
        self.lanes = dict(cfg["lanes"])
        # Augur: the run's plan (WAVE.json) must pass the launch checks now, computed here rather than read from a
        # receipt an agent could write. The limits come from the approved plan: one source, nothing to drift.
        plan = read_json(self.root / "WAVE.json", None)
        if not plan:
            raise SystemExit("WAVE.json missing: every run needs a plan that passes jobs/augur-launch/augur.py check")
        refusals, receipt = (preflight or augur.check)(plan)
        if refusals:
            raise SystemExit("Augur refuses this wave:\n- " + "\n- ".join(refusals))
        planned = sum(int(a.get("lanes") or 0) for a in plan.get("actions") or [])
        if len(self.lanes) > planned:
            raise SystemExit(f"lanes.json has {len(self.lanes)} lanes; the approved plan allows {planned}")
        write_json(self.root / "augur-receipt.json", receipt)
        self.limits = dict(plan.get("limits") or {})
        missing = [k for k in LIMIT_KEYS if not isinstance(self.limits.get(k), (int, float)) or self.limits[k] <= 0]
        if missing:
            raise SystemExit("WAVE.json limits need positive values for: " + ", ".join(missing))
        for d in ("inbox", "status", "directives", "logs"):
            (self.root / d).mkdir(exist_ok=True)
        self.state = read_json(self.root / "state.json", {})
        self.state.setdefault("agents", {})
        self.state.setdefault("started_at", stamp())
        for agent in [COORD, *self.lanes]:
            self.state["agents"].setdefault(agent, {"turns": 0, "failures": 0})
        self.running = {}
        self.report = {}
        self.last_meter = 0.0

    # ---- mailboxes and controls -------------------------------------------------------------------------
    def post(self, box, record):
        with open(self.root / "inbox" / f"{box}.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"at": stamp(), "from": "supervisor", **record}) + "\n")

    def pause(self, agent, reason, **facts):
        path = self.root / f"PAUSE-{agent}"
        if not path.exists():
            path.write_text(reason + "\n", encoding="utf-8")
            self.post("claude", {"agent": agent, "event": "paused", "reason": reason, **facts})
            if agent != COORD:
                self.post("savigny", {"agent": agent, "event": "paused", "reason": reason, **facts})
        if agent in self.running:
            self.kill(agent)

    def paused(self, agent):
        return (self.root / f"PAUSE-{agent}").exists()

    # ---- processes -------------------------------------------------------------------------------------
    def codex(self):
        found = sorted(glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\OpenAI\Codex\bin\*\codex.exe")),
                       key=os.path.getmtime)
        if not found:
            raise SystemExit("codex.exe not found under %LOCALAPPDATA%\\OpenAI\\Codex\\bin")
        return found[-1]

    def command(self, agent, last):
        if self.fake:
            return [sys.executable, "-I", "-c", "import sys,time;sys.stdin.read();time.sleep(2)"]
        roots = "['" + str(self.root.parent) + "', '" + GITDIR + "']"
        cwd = self.lanes.get(agent) or str(self.root)
        # Always a fresh session: `exec resume` would re-send the whole growing history on every call.
        return [self.codex(), "exec", "--json", "--approve-for-me", "--skip-git-repo-check", "-C", cwd,
                "-m", MODEL, "-c", f'model_reasoning_effort="{EFFORT}"',
                "-c", 'sandbox_mode="workspace-write"', "-c", 'approval_policy="on-request"',
                "-c", 'approvals_reviewer="auto_review"', "-c", "sandbox_workspace_write.network_access=true",
                "-c", f"sandbox_workspace_write.writable_roots={roots}", "-o", str(last), "-"]

    def prompt(self, agent, turn):
        p = self.root / "prompts"
        if agent == COORD:
            body = (p / "savigny.md").read_text(encoding="utf-8") + "\n\n" + (p / "savigny-turn.md").read_text(encoding="utf-8")
        else:
            n = agent.split("-")[-1]
            body = ((p / "lane.md").read_text(encoding="utf-8") + "\n\n" + (p / "lane-turn.md").read_text(encoding="utf-8"))
            body = body.replace("{N}", n)
        return body.replace("{TURN}", str(turn)).replace("{AGENT}", agent)

    def start(self, agent):
        a = self.state["agents"][agent]
        turn = a["turns"] + 1
        logdir = self.root / "logs" / agent
        logdir.mkdir(parents=True, exist_ok=True)
        out, last = logdir / f"{turn:04d}.jsonl", logdir / f"{turn:04d}-last.md"
        fh = open(out, "w", encoding="utf-8")
        proc = subprocess.Popen(self.command(agent, last), stdin=subprocess.PIPE, stdout=fh, stderr=subprocess.STDOUT,
                                cwd=str(self.lanes.get(agent) or self.root) if not self.fake else str(self.root),
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                                start_new_session=os.name != "nt")
        proc.stdin.write(self.prompt(agent, turn).encode("utf-8"))
        proc.stdin.close()
        a.update(turns=turn, started=self.clock(), out=str(out), pid=proc.pid)
        a.setdefault("first_started", self.clock())
        self.running[agent] = (proc, fh)

    def kill(self, agent):
        proc, _ = self.running[agent]
        if proc.poll() is None:
            # The whole tree: killing only the coordinator would leave its workers running and spending.
            if os.name == "nt":
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
            else:
                import signal
                try:
                    os.killpg(proc.pid, signal.SIGKILL)   # the turn runs in its own session (start_new_session)
                except (ProcessLookupError, PermissionError):
                    proc.kill()
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

    def reap(self):
        for agent, (proc, fh) in list(self.running.items()):
            a = self.state["agents"][agent]
            if proc.poll() is None and self.clock() - a["started"] > TURN_MAX:
                self.kill(agent)
                self.post("claude", {"agent": agent, "event": "turn_killed", "why": "turn over 2 hours"})
            if proc.poll() is None:
                continue
            fh.close()
            took = self.clock() - a["started"]
            a["pid"] = None
            failed = proc.returncode != 0 or (took < SHORT_TURN and agent != COORD)
            a["failures"] = a.get("failures", 0) + 1 if failed else 0
            a["next_ok"] = self.clock() + (min(60 * 2 ** a["failures"], 1800) if failed else 0)
            if agent == COORD:
                a["ended"] = self.clock()
            else:
                a["run_since_claim"] = a.get("run_since_claim", 0.0) + took
                self.state["news"] = True
                self.post("savigny", {"agent": agent, "event": "turn_end", "turn": a["turns"],
                                      "exit": proc.returncode, "minutes": round(took / 60, 1)})
            del self.running[agent]

    # ---- measurement and limits ------------------------------------------------------------------------
    def measure(self):
        return meter.lane_report([COORD, *self.lanes], self.state["started_at"], None,
                                 {k: v for k, v in self.lanes.items()})

    def enforce(self):
        L = self.limits
        self.report = self.metered()
        total = sum(r["units"] for r in self.report.values())
        if total >= L["chain_budget_units"]:
            for agent in list(self.running):
                self.kill(agent)
            (self.root / "STOP").write_text(f"budget: {total} of {L['chain_budget_units']} units\n", encoding="utf-8")
            self.post("claude", {"event": "budget_stop", "units": total, "budget": L["chain_budget_units"]})
            return
        for lane in self.lanes:
            a, r = self.state["agents"][lane], self.report.get(lane) or {}
            filed = r.get("filed") or 0
            if "filed_seen" not in a:
                a.update(filed_seen=filed, units_at_claim=r.get("units", 0), run_since_claim=0.0)
            if filed > a["filed_seen"]:
                a.update(filed_seen=filed, units_at_claim=r.get("units", 0), run_since_claim=0.0)
                continue
            running_for = a.get("run_since_claim", 0.0) + (self.clock() - a["started"] if lane in self.running else 0)
            spent = r.get("units", 0) - a["units_at_claim"]
            if spent > L["spend_per_claim_units"]:
                self.pause(lane, "spend without a claim", units_since_last_claim=spent, filed=filed)
            elif running_for > L["no_claim_minutes"] * 60:
                self.pause(lane, "time without a claim", minutes_since_last_claim=round(running_for / 60), filed=filed)
            elif r.get("reviews_last_hour", 0) > L["reviews_per_hour"]:
                self.pause(lane, "auto-review burst: the sandbox lacks a permission this work needs",
                           reviews_last_hour=r["reviews_last_hour"])
        for agent in list(self.running):
            ctx = self.turn_context(agent)
            if ctx > L["context_kill_tokens"]:
                self.kill(agent)
                self.post("claude", {"agent": agent, "event": "context_kill", "context_tokens": ctx})
        c = self.state["agents"][COORD]
        hour = self.report.get(COORD, {}).get("units", 0) - c.get("units_hour_mark", 0)
        if self.clock() - c.get("hour_started", 0) >= 3600:
            c.update(hour_started=self.clock(), units_hour_mark=self.report.get(COORD, {}).get("units", 0))
        elif hour > L["coordinator_units_per_hour"]:
            c["next_ok"] = c.get("hour_started", self.clock()) + 3600
            if COORD in self.running:
                self.kill(COORD)
            self.post("claude", {"event": "coordinator_capped", "units_this_hour": hour})

    def turn_context(self, agent):
        """The latest call's context size in the running turn's own session (0 if not found yet)."""
        a = self.state["agents"][agent]
        try:
            with open(a["out"], encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if '"thread_id"' in line:
                        thread = json.loads(line).get("thread_id")
                        break
                else:
                    return 0
        except (OSError, ValueError, KeyError):
            return 0
        home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
        paths = glob.glob(str(home / "sessions" / "*" / "*" / "*" / f"*{thread}*.jsonl"))
        return meter.read_rollout(paths[0]).get("last_context", 0) if paths else 0

    # ---- scheduling ------------------------------------------------------------------------------------
    def due(self, agent):
        a = self.state["agents"][agent]
        if agent in self.running or self.paused(agent) or self.clock() < a.get("next_ok", 0):
            return False
        if agent == COORD:
            # Only when there is news (a lane turn ended, a pause), never on a timer alone.
            return bool(self.state.get("news")) and self.clock() - a.get("ended", 0) >= COORD_MIN_GAP
        status = read_json(self.root / "status" / f"{agent}.json", {})
        if status.get("done"):
            return False
        if not a.get("first_started"):
            firsts = [self.state["agents"][x].get("first_started", 0) for x in self.lanes]
            if max(firsts) and self.clock() - max(firsts) < STAGGER:
                return False
        return True

    def step(self):
        self.reap()
        if self.clock() - self.last_meter >= (1 if self.fake else METER_EVERY):
            self.last_meter = self.clock()
            self.enforce()
            self.reap()      # collect any turn a limit just killed, so state never shows it as running
        stopping = (self.root / "STOP").exists()
        if not stopping:
            for agent in [COORD, *self.lanes]:
                if self.due(agent):
                    if agent == COORD:
                        self.state["news"] = False
                    self.start(agent)
        write_json(self.root / "state.json", {**self.state, "running": sorted(self.running), "report": self.report})
        return not (stopping and not self.running)

    def run(self):
        lock = self.root / "supervisor.pid"
        if lock.exists() and meter_pid_alive(lock.read_text().strip() or 0):
            raise SystemExit(f"another supervisor is running (pid {lock.read_text().strip()})")
        lock.write_text(str(os.getpid()))
        if not self.fake and os.name == "nt":
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)   # no idle sleep while running
        self.post("claude", {"event": "supervisor_started", "model": MODEL, "effort": EFFORT, "limits": self.limits})
        try:
            while self.step():
                time.sleep(0.2 if self.fake else TICK)
        finally:
            lock.unlink(missing_ok=True)
        self.post("claude", {"event": "supervisor_stopped"})


def meter_pid_alive(pid):
    if not pid or os.name != "nt":
        return False
    import ctypes
    k = ctypes.windll.kernel32
    h = k.OpenProcess(0x1000, False, int(pid))
    if not h:
        return False
    code = ctypes.c_ulong()
    ok = k.GetExitCodeProcess(h, ctypes.byref(code))
    k.CloseHandle(h)
    return bool(ok) and code.value == 259


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=r"C:\Users\danie\eo-wt\_savigny")
    ap.add_argument("--fake", action="store_true")
    a = ap.parse_args(argv)
    Chain(a.root, fake=a.fake).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

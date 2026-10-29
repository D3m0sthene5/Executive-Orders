"""Capcom: the project's position on an Apollo 11 timeline, day by day.

Capcom was the one voice in Mission Control that told the crew where they stood.
This builder does the same for the executive-order project, from the readiness
tracker's own history on main, so the record is longitudinal by construction.

The goal ("one small step") is every order the American Presidency Project counts
(16,239) with a complete dossier ready for human review. Distance covered is the
effort-weighted share of all readiness steps that are done:

    progress = sum(w_k * done_k) / sum(w_k * (done_k + open_k))

over the step kinds k the tracker counts, plus the census-gap orders (APP count
minus project orders), each of which owes an "admit" step and the six core steps.
w_k is the average model minutes per open step of kind k, frozen once in
MISSION_WEIGHTS.csv so that later changes to the effort model do not move past
positions. Progress is mapped onto Apollo 11's mission clock from launch to
Armstrong's first step (109 h 24 min 15 s, APOLLO11_MILESTONES.csv).

One snapshot per UTC day: the last commit on main's first-parent line that day
that changed jobs/readiness-tracker/output/READINESS_BY_ORDER.csv. Writes
MISSION_LOG.csv. Reads git history; changes nothing else. Human certification is
not counted here and stays 0.
"""
import collections, csv, io, json, subprocess, sys
from pathlib import Path

import build_remaining_work as brw

HERE, ROOT = brw.HERE, brw.ROOT
TRACKER_PATH = "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv"
REF = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
WEIGHTS = HERE / "MISSION_WEIGHTS.csv"
MILESTONES = HERE / "APOLLO11_MILESTONES.csv"

# tracker step -> effort-model step_order (EFFORT_BY_TIER.csv)
KIND_OF = {"admit": 1, "provisional_status": 2, "original_text": 3, "clause_inventory": 4,
           "ending_or_current_basis": 5, "savings_residuals": 6, "counterevidence": 7,
           "shared_sources": 8, "opus_media": 8}


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True).stdout


def weights():
    if not WEIGHTS.exists():
        acc = collections.defaultdict(lambda: [0, 0.0, ""])
        for r in csv.DictReader(open(HERE / "EFFORT_BY_TIER.csv", encoding="utf-8")):
            a = acc[int(r["step_order"])]
            a[0] += int(r["open_steps"]); a[1] += float(r["agent_hours"]) * 60; a[2] = r["kind"]
        with open(WEIGHTS, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["step_order", "kind", "minutes_per_step", "frozen_from"])
            for k in sorted(acc):
                n, m, name = acc[k]
                w.writerow([k, name, round(m / n, 3) if n else 0,
                            "EFFORT_BY_TIER.csv average over open steps, frozen on first build"])
    return {int(r["step_order"]): float(r["minutes_per_step"]) for r in csv.DictReader(open(WEIGHTS, encoding="utf-8"))}


def first_step_hours():
    for r in csv.DictReader(open(MILESTONES, encoding="utf-8")):
        if r["key"] == "first_step":
            h, m, s = (int(x) for x in r["met"].split(":"))
            return h + m / 60 + s / 3600
    raise SystemExit("APOLLO11_MILESTONES.csv lacks first_step")


def phase(met, milestones):
    name = milestones[0]["phase_after"]
    for r in milestones:
        if met >= r["hours"]:
            name = r["phase_after"]
    return name


def main():
    w = weights()
    end = first_step_hours()
    ms = []
    for r in csv.DictReader(open(MILESTONES, encoding="utf-8")):
        h, m, s = (int(x) for x in r["met"].split(":"))
        ms.append({**r, "hours": h + m / 60 + s / 3600})
    gap = json.load(open(HERE / "REMAINING_WORK.json", encoding="utf-8"))["not_yet_in_project"]
    log = git("log", "--first-parent", "--format=%H %cI", REF, "--", TRACKER_PATH).decode().split("\n")
    per_day = {}
    for line in reversed([l for l in log if l.strip()]):   # oldest first; later commits overwrite
        sha, when = line.split(" ", 1)
        per_day[when[:10] if when.endswith("Z") else
                 __import__("datetime").datetime.fromisoformat(when).astimezone(__import__("datetime").timezone.utc).strftime("%Y-%m-%d")] = (sha, when)
    rows = []
    for day in sorted(per_day):
        sha, when = per_day[day]
        tracker = list(csv.DictReader(io.StringIO(git("show", f"{sha}:{TRACKER_PATH}").decode("utf-8-sig"))))
        done, open_ = collections.Counter(), collections.Counter()
        for r in tracker:
            for s in brw.STEPS[1:]:
                v = r.get("step_" + s)
                if v == "done":
                    done[s] += 1
                elif v == "open":
                    open_[s] += 1
        open_["admit"] += gap
        for s in brw.CORE:
            open_[s] += gap
        wd = sum(w[KIND_OF[s]] * n for s, n in done.items())
        wo = sum(w[KIND_OF[s]] * n for s, n in open_.items())
        progress = wd / (wd + wo)
        met = progress * end
        rows.append({
            "date": day, "commit": sha[:10], "committed_at": when,
            "ready_for_human_review": sum(r["ready_for_human_review"] == "yes" for r in tracker),
            "provisional_statuses": sum(r["provisional_status"] in ("yes", "no") for r in tracker),
            "orders_in_census": len(tracker), "orders_goal": len(tracker) + gap,
            "steps_done": sum(done.values()), "steps_open": sum(open_.values()),
            "step_share": round(sum(done.values()) / (sum(done.values()) + sum(open_.values())), 5),
            "progress": round(progress, 5), "met_hours": round(met, 3),
            "phase": phase(met, ms), "human_certified": 0,
        })
    with open(HERE / "MISSION_LOG.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader(); wr.writerows(rows)
    print(json.dumps(rows[-1], indent=1), f"\n{len(rows)} daily snapshots")


if __name__ == "__main__":
    main()

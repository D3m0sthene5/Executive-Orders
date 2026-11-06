"""Tsiolkovsky: the project's trajectory. How much verified work is done, how fast it is rising, and what pushed it.

Named for Konstantin Tsiolkovsky, whose rocket equation (1903) turned a rocket's progress into one number: delta-v,
the change in velocity its burns achieve. The Apollo rocket dashboard placed the project on Apollo 11's timeline by
its fraction of weighted work done; this job gives that position a history, a velocity and an acceleration, and
credits each change to the campaigns and machines that landed just before it.

THE METRIC: delta-v, in verified work-hours.

For every tracker generation g (every committed jobs/readiness-tracker/output/READINESS_BY_ORDER.csv on main), for
every census order i and every lifecycle step s the tracker applies to it:

    W(g) = sum_i sum_s  w_s * c(state_{i,s,g}, blockers_{i,s,g})

- w_s, the step's weight, is the measured agent-minutes that step costs (research/progress/remaining-work/
  MISSION_WEIGHTS.csv, frozen at first build; the same weights the rocket used), so W is in work-minutes: the work
  the project would still have to do if it had to redo what it holds. Expensive steps (proving how an order ended,
  21 minutes) count more than cheap ones (retrieving a cited source, 1.4 minutes).
- c is the credit for the step's state, in [0, 1]. A done step is 1. A partial state earns partial credit by how far
  it is from done, read from the tracker's own blocker codes (CREDITS below): an official original found but not
  page-checked, an archival replica held, a claim filed but not yet checked, and so on. A provisional text step
  (working text accepted, original still to replace) is 0.6. Human certification is never credited (count: 0).
- Census admission is a step too (15 minutes, the rocket's weight): each order admitted adds it, so census growth
  counts as work done rather than shrinking the percentage.

Progress p(g) = W(g) / W_max, with W_max fixed at the full weight of every step of every order in the largest census
seen, so the denominator never jumps. Velocity v = dW/dt (work-hours per day) and acceleration a = dv/dt are taken
on the daily end-of-day series, with a 3-day centred average beside the raw daily values.

Why this beats the ready count: the ready count moves only when all six steps of an order close and checker receipts
match, so months of acquisition, leads and claims show as zero, and a stricter rule (the R3 re-tag) shows as loss.
W rises with every step closed or brought closer, falls only when evidence is lost or a rule is tightened (which the
interval table flags), and its derivative shows acceleration.

WHAT PUSHED WHAT. The change between two consecutive generations is split by step and by state transition, and
credited to the events on main's first-parent history between the two generation commits: pull-request merges
(campaign = the historical name in the branch, agent = its prefix) and job-result commits (machine = the job). An
interval with one event is credited exactly; an interval with several splits its change equally among them and says
so (`shared_with`). This is attribution by landing order, not proof of causation.

    python3 -I trajectory.py REPO_ROOT OUT_DIR [PRIOR_OUT_DIR]
"""
import collections
import csv
import datetime as dt
import io
import json
import os
import re
import subprocess
import sys

csv.field_size_limit(min(2 ** 31 - 1, 10 ** 9))
PATH = "jobs/readiness-tracker/output/READINESS_BY_ORDER.csv"
# MISSION_WEIGHTS.csv (frozen first build): minutes per step kind.
WEIGHTS = {"census": 15.0, "provisional_status": 6.216, "original_text": 6.19, "clause_inventory": 4.992,
           "ending_or_current_basis": 20.643, "savings_residuals": 9.606, "counterevidence": 10.027,
           "shared_sources": 1.409, "opus_media": 1.409}
STEPS = ["provisional_status", "original_text", "clause_inventory", "ending_or_current_basis", "savings_residuals",
         "counterevidence", "shared_sources", "opus_media"]
CLAIM_STEPS = {"clause_inventory", "ending_or_current_basis", "savings_residuals", "counterevidence"}
# Partial credit for an open step, by the tracker's blocker codes (the best applicable code counts).
TEXT_CREDIT = {"ORIGINAL_FOUND_NEEDS_PAGE_CHECK": 0.5, "ARCHIVAL_REPLICA_FOUND_NEEDS_PAGE_CHECK": 0.4,
               "OFFICIAL_URL_KNOWN_NOT_DOWNLOADED": 0.3, "ONLY_COMPILED_TRANSCRIPTION_FOUND": 0.2}
CLAIM_CREDIT = {"CLAIM_NOT_YET_CHECKED": 0.8, "CLAIM_CHECK_FAILED": 0.5, "CLAIM_INCOMPLETE": 0.4,
                "OPEN_SOURCE_AUDIT": 0.5}
PROVISIONAL = 0.6
# The rocket's clock (research/progress/remaining-work/APOLLO11_MILESTONES.csv, NASA Kennedy Space Center Apollo 11
# page): progress p maps to mission elapsed time p * 109:24:15, Armstrong's first step.
MILESTONES = [("launch", "Liftoff", 0.0, "Earth orbit"),
              ("tli", "Translunar injection", 2 + 44 / 60 + 26 / 3600, "Translunar coast"),
              ("loi", "Lunar orbit insertion", 75 + 50 / 60, "Lunar orbit"),
              ("landing", "Eagle lands", 102 + 45 / 60 + 39 / 3600, "On the surface"),
              ("first_step", "First step", 109 + 24 / 60 + 15 / 3600, "First step")]
FIRST_STEP_H = MILESTONES[-1][2]


def mission(p):
    met = p * FIRST_STEP_H
    phase = MILESTONES[0][3]
    for _, _, h, after in MILESTONES:
        if met >= h:
            phase = after
    return round(met, 2), phase
NAME_TOKEN = re.compile(r"[a-z]+")
GENERIC = {"claude", "codex", "sol", "astra", "opus", "job", "jobs", "fix", "the", "and", "for", "from", "with", "wave",
           "integration", "integrate", "final", "stable", "main", "repair", "production", "review", "reviewed",
           "lightweight", "batch", "merge", "pull", "request", "prs", "run", "add", "record", "results", "output",
           "outputs", "readiness", "tracker", "dashboard", "refresh", "orders", "order", "executive", "sources",
           "source", "texts", "text", "early", "numbered", "class", "great", "shared", "status", "checker",
           "claims", "claim", "proposals", "pages", "remaining", "work", "progress", "stage", "diagnostics",
           "excavator", "readme", "notes", "handoff", "plans", "releases", "variants", "checkpoints", "salvage",
           "gap", "census", "pre", "verified", "publish", "reduce", "preserve", "reviewer", "empty", "undecided"}
# The project's campaign and tool names (historical names, by the owner's naming rule). Add new ones here.
KNOWN = {"tribonian", "justinian", "dorotheus", "theophilus", "gratian", "pothier", "selden", "mabillon", "ptolemy",
         "herschel", "bentham", "kean", "gessner", "tischendorf", "arsenale", "minard", "lachmann", "geddes", "apollo",
         "jacquard", "cotton", "schechter", "shepard", "mansfield", "sinclair", "junto", "lewis", "clark", "maitland",
         "bacon", "cruden", "mountweazel", "babbage", "norton", "valla", "neyman", "lambertini", "poggio", "namier",
         "cassiodorus", "niebuhr", "domesday", "polya", "machiavelli", "dagron", "formulario", "peano", "tsiolkovsky",
         "lind", "bowditch", "pinakes", "richardson", "wikisource", "hathi", "opus", "hamilton", "excavator", "capcom",
         "lord", "wpa", "proquest", "nara", "csc", "isthmian", "x1", "corps", "roads", "road", "sol", "erasmus",
         "fecundity", "olsen", "sorensen", "theodosius", "ulpian", "tiered", "titian"}


def campaign_name(branch_tail, title=""):
    """A known campaign name in the branch or title, else the branch label humanised (dates and hashes dropped)."""
    for x in (branch_tail, title):
        for t in NAME_TOKEN.findall((x or "").lower()) + re.findall(r"x1", (x or "").lower()):
            if t in KNOWN:
                return t.capitalize() if t != "x1" else "X1"
    label = re.sub(r"[-_](\d{6,8}(utc)?|\d{4}-\d{2}-\d{2}|[0-9a-z]{6})$", "", branch_tail or "")
    label = re.sub(r"[-_]\d{8}(-\d{4}utc)?", "", label)
    if label:
        return label.replace("-", " ").replace("_", " ").strip().capitalize()
    words = [w for w in NAME_TOKEN.findall((title or "").lower()) if w not in GENERIC]
    return " ".join(words[:3]).capitalize() or "Unnamed"


def git(root, *args, binary=False):
    r = subprocess.run(["git", "-C", root, *args], capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stderr.decode("utf-8", "replace")[:300])
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


# Sensitivity: the partial credits are judgment, so W is also computed with them halved (low) and raised by half,
# capped below done (high); the chart draws the band between.
SCALES = {"mid": (1.0, PROVISIONAL), "low": (0.5, 0.4), "high": (1.5, 0.8)}


def credit(step, state, blockers, scale="mid"):
    k, prov = SCALES[scale]
    if state == "done":
        return 1.0
    if state == "provisional":
        return prov
    best = 0.0
    if step == "original_text":
        for b in blockers:
            best = max(best, TEXT_CREDIT.get(b, 0.0))
    elif step in CLAIM_STEPS:
        for b in blockers:
            best = max(best, CLAIM_CREDIT.get(b.split(":")[0], 0.0))
    return min(0.95, best * k)


def measure(text):
    """W (work-minutes) by step, the full weight of the applicable steps, and context counts, for one generation."""
    rows = csv.DictReader(io.StringIO(text))
    by_step = collections.Counter()
    full = collections.Counter()
    trans = collections.Counter()  # (step, coarse state) -> credited minutes, for the decomposition
    n = ready = provisional_status = claims = 0
    low = high = 0.0
    for r in rows:
        n += 1
        ready += r.get("ready_for_human_review") == "yes"
        provisional_status += (r.get("provisional_status") or "") in ("yes", "no")
        claims += r.get("claim_present") == "yes"
        blockers = [b for b in (r.get("blockers") or "").split("|") if b]
        by_step["census"] += WEIGHTS["census"]
        full["census"] += WEIGHTS["census"]
        low += WEIGHTS["census"]
        high += WEIGHTS["census"]
        for s in STEPS:
            state = r.get(f"step_{s}", "")
            if state in ("", "n/a"):
                continue
            c = credit(s, state, blockers)
            by_step[s] += WEIGHTS[s] * c
            full[s] += WEIGHTS[s]
            low += WEIGHTS[s] * credit(s, state, blockers, "low")
            high += WEIGHTS[s] * credit(s, state, blockers, "high")
            coarse = "done" if state == "done" else "provisional" if state == "provisional" else ("partial" if c else "open")
            trans[f"{s}:{coarse}"] += WEIGHTS[s] * c
    return {"orders": n, "ready": ready, "provisional_statuses": provisional_status, "claims": claims,
            "W_min": round(sum(by_step.values()), 3), "W_low_min": round(low, 3), "W_high_min": round(high, 3),
            "full_min": round(sum(full.values()), 3),
            "by_step": {k: round(v, 3) for k, v in by_step.items()}, "by_state": {k: round(v, 3) for k, v in trans.items()}}


def generations(root):
    """Every first-parent commit on HEAD that changed the per-order table, oldest first. Found from commit messages
    first (the runner names the jobs it publishes), then confirmed by blob id so a commit that did not change the
    table is skipped."""
    log = git(root, "log", "--first-parent", "--reverse", "--format=%H\t%cI\t%s", "HEAD").splitlines()
    out, last_blob = [], None
    for line in log:
        h, t, subj = line.split("\t", 2)
        if "readiness-tracker" not in subj and not subj.startswith(("Merge pull request", "Merge PR")) and "(#" not in subj:
            continue
        try:
            blob = git(root, "rev-parse", f"{h}:{PATH}").strip()
        except RuntimeError:
            continue
        if blob != last_blob:
            out.append({"commit": h, "utc": t, "subject": subj, "blob": blob})
            last_blob = blob
    return out


def classify(subject):
    """(kind, agent, campaign, pr) of a first-parent commit."""
    m = re.match(r"Merge pull request #(\d+) from [^/]+/(\S+)", subject)
    pr, branch = (m.group(1), m.group(2)) if m else (None, None)
    if not m:
        m2 = (re.search(r"\(#(\d+)\)\s*$", subject) or re.match(r"Merge PR #(\d+)", subject)
              or re.match(r"Merge #(\d+)", subject))
        if m2:
            pr = m2.group(1)
    if subject.startswith("Results of job(s):"):
        jobs = subject.split(":", 1)[1].split("\n")[0].split()
        return "machine", "runner", "|".join(jobs), None
    if pr:
        agent = branch.split("/")[0] if branch and "/" in branch else ""
        tail = branch.split("/", 1)[1] if branch and "/" in branch else (branch or "")
        title = subject.split(":", 1)[1] if subject.startswith("Merge PR") and ":" in subject else subject
        title = re.sub(r"^Merge #\d+\s*", "", title)
        title = re.sub(r"\s*\(#\d+\)\s*$", "", title)
        return "merge", agent, campaign_name(tail, title), pr
    lead = subject.split(":", 1)[0] if ":" in subject[:40] else ""
    return "commit", "", campaign_name(lead, subject) if lead or subject else "Direct commits", None


# Evidence channels: which kind of input can move which step. An event is eligible for a step's change when it
# touched one of the step's channels (or the rules); instruments that only measure or report are never credited.
CHANNELS = {
    "census": ("research/stage15/CENSUS/",),
    "status": ("research/progress/", "research/excavator/"),
    "claims": ("research/readiness/claims/",),
    "evidence": ("jobs/", "research/stage21/", "research/stage19/output/", "research/stage20/", "research/pre-1937-sources/",
                 "ProQuest Pre-1937 Orders/", "releases/", "research/salvage/"),
    "rules": ("jobs/readiness-tracker/tracker.py", "jobs/readiness-tracker/working_text.py", "jobs/claim-checker/",
              "jobs/claim-kit/", "research/stage19/code/", "research/readiness/owner_rulings/", "research/readiness/EXHAUSTED.jsonl"),
}
STEP_CHANNELS = {"census": ("census",), "provisional_status": ("status",), "original_text": ("evidence",),
                 "shared_sources": ("evidence",), "opus_media": ("evidence",), "clause_inventory": ("claims",),
                 "ending_or_current_basis": ("claims",), "savings_residuals": ("claims",),
                 "counterevidence": ("claims", "evidence")}
INSTRUMENTS = {"readiness-tracker", "daily-digest", "gessner-cards", "kean", "bentham", "example-hello", "domesday-register",
               "dagron-collection-manifest", "tsiolkovsky-trajectory", "census-candidates", "hamilton-token-audit"}
LAUNCH = "Launch pad (work held before the first tracker reading: Stages 1-17 census, statuses and sources)"


def touched_channels(root, commit):
    try:
        names = git(root, "diff-tree", "-r", "--name-only", "--no-commit-id", f"{commit}^1", commit).split("\n")
    except RuntimeError:
        return set()
    out = set()
    for n in names:
        for ch, prefixes in CHANNELS.items():
            if any(n.startswith(p) for p in prefixes):
                out.add(ch)
    return out


def events_between(root, a, b):
    if a is None:
        rng = [b]
    else:
        rng = [f"{a}..{b}"]
    out = []
    for line in git(root, "log", "--first-parent", "--reverse", "--format=%H\t%cI\t%s", *rng).splitlines():
        h, t, subj = line.split("\t", 2)
        kind, agent, campaign, pr = classify(subj)
        if kind == "machine":
            producers = [j for j in campaign.split("|") if j and j not in INSTRUMENTS]
            if len(producers) > 1:
                producers = [j for j in producers if j != "claim-checker"]
            for j in producers:  # one event per producing job
                verify = j == "claim-checker"
                out.append({"commit": h, "utc": t, "kind": "verification" if verify else kind, "agent": "runner",
                            "campaign": "machine:" + j, "pr": None, "subject": subj[:160],
                            "channels": ["claims"] if verify else ["evidence"]})
        elif kind in ("merge", "commit"):
            ch = sorted(touched_channels(root, h))
            if kind == "commit" and not ch:
                continue  # notes, Kean and handoff commits move no step
            out.append({"commit": h, "utc": t, "kind": kind, "agent": agent, "campaign": campaign, "pr": pr,
                        "subject": subj[:160], "channels": ch})
    return out


def utc(t):
    return dt.datetime.fromisoformat(t).astimezone(dt.timezone.utc)


def build(root, out, prior=None):
    os.makedirs(out, exist_ok=True)
    cache = {}
    if prior and os.path.exists(os.path.join(prior, "GENERATIONS.jsonl")):
        with open(os.path.join(prior, "GENERATIONS.jsonl"), encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                cache[r["blob"]] = r
    gens = generations(root)
    rows = []
    for g in gens:
        m = cache.get(g["blob"])
        if not m or "W_low_min" not in m:
            m = measure(git(root, "show", f"{g['commit']}:{PATH}"))
        rows.append({**{k: m[k] for k in m if k not in ("commit", "utc", "subject", "blob")}, **g})
    with open(os.path.join(out, "GENERATIONS.jsonl"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    w_max = max(r["full_min"] for r in rows) if rows else 1.0

    # landing time: a commit's timestamp can predate the merge that landed it, so take the running maximum
    landed = None
    for r in rows:
        t = utc(r["utc"])
        landed = t if landed is None or t > landed else landed
        r["landed_utc"] = landed.isoformat()

    # intervals: the change between consecutive generations, credited by evidence channel
    intervals, campaign_credit = [], collections.defaultdict(collections.Counter)
    prev, recent = None, []  # recent: the actor events of the last interval that had any
    credit_flat, event_flat = [], []
    for r in rows:
        steps = sorted(set(r["by_step"]) | set(prev["by_step"] if prev else {}))
        d_step = {k: r["by_step"].get(k, 0) - (prev["by_step"].get(k, 0) if prev else 0) for k in steps}
        d_w = r["W_min"] - (prev["W_min"] if prev else 0.0)
        if prev is None:
            ev, credit_rows = [], [{"to": LAUNCH, "step": k, "min": v, "rule": "launch"} for k, v in d_step.items()]
        else:
            ev = events_between(root, prev["commit"], r["commit"])
            credit_rows = []
            for k, v in d_step.items():
                if abs(v) < 1e-6:
                    continue
                want = set(STEP_CHANNELS.get(k, ("evidence",)))
                actors = [e for e in ev if e["kind"] != "verification"]
                elig = [e for e in actors if want & set(e["channels"])]
                rule = "channel"
                if not elig:
                    elig = [e for e in actors if "rules" in e["channels"]]
                    rule = "rules"
                if not elig:
                    elig = [e for e in actors if e["kind"] == "merge"] or actors
                    rule = "landed_together"
                if not elig and recent:
                    # only a re-check or a re-run: the change is the consequence of the work that landed just before
                    elig = [e for e in recent if want & set(e["channels"])] or [e for e in recent if "rules" in e["channels"]] or recent
                    rule = "deferred"
                if not elig:
                    elig = [e for e in ev if e["kind"] == "verification"]
                    rule = "verification"
                if not elig:
                    credit_rows.append({"to": "(no event: tracker re-run)", "step": k, "min": v, "rule": "none"})
                    continue
                for e in elig:
                    credit_rows.append({"to": e["campaign"], "agent": e["agent"], "step": k, "min": v / len(elig), "rule": rule})
        by_to = collections.defaultdict(float)
        for c in credit_rows:
            by_to[c["to"]] += c["min"]
            cc = campaign_credit[c["to"]]
            cc["W_min"] += c["min"]
            cc[f"step:{c['step']}"] += c["min"]
            cc["positive_min"] += max(c["min"], 0)
            cc["negative_min"] += min(c["min"], 0)
            cc["agent:" + (c.get("agent") or "")] += 0
            if not isinstance(cc.get("first"), str):
                cc["first"] = r["landed_utc"]
            cc["last"] = r["landed_utc"]
        actors_now = [e for e in ev if e["kind"] != "verification"]
        if actors_now:
            recent = actors_now
        for c in credit_rows:
            credit_flat.append({"to_utc": r["landed_utc"], "from_utc": prev["landed_utc"] if prev else "",
                                "credited_to": c["to"], "agent": c.get("agent", ""), "step": c["step"],
                                "hours": round(c["min"] / 60, 3), "rule": c["rule"]})
        for e in ev:
            event_flat.append({"utc": e["utc"], "landed_by": r["landed_utc"], "kind": e["kind"], "agent": e["agent"],
                               "campaign": e["campaign"], "pr": e["pr"] or "", "channels": "|".join(e["channels"]),
                               "subject": e["subject"]})
        intervals.append({"from_utc": prev["landed_utc"] if prev else "", "to_utc": r["landed_utc"], "to_commit": r["commit"][:12],
                          "dW_hours": round(d_w / 60, 2), "d_ready": r["ready"] - (prev["ready"] if prev else 0),
                          "d_orders": r["orders"] - (prev["orders"] if prev else 0),
                          "d_by_step_hours": {k: round(v / 60, 2) for k, v in sorted(d_step.items()) if abs(v) > 0.5},
                          "credit_hours": {k: round(v / 60, 2) for k, v in sorted(by_to.items(), key=lambda x: -abs(x[1])) if abs(v) > 0.05},
                          "events": [{k: e[k] for k in ("utc", "kind", "agent", "campaign", "pr", "subject", "channels")} for e in ev]})
        prev = r

    # daily end-of-day series, velocity, acceleration
    daily = collections.OrderedDict()
    for r in rows:
        daily[r["landed_utc"][:10]] = r
    days = sorted(daily)
    series = []
    if days:
        d0, d1 = dt.date.fromisoformat(days[0]), dt.date.fromisoformat(days[-1])
        cur, last = d0, None
        while cur <= d1:
            k = cur.isoformat()
            last = daily.get(k, last)
            series.append({"date": k, "W_hours": round(last["W_min"] / 60, 2), "p": round(last["W_min"] / w_max, 6),
                           "W_low_hours": round(last["W_low_min"] / 60, 2), "W_high_hours": round(last["W_high_min"] / 60, 2),
                           "ready": last["ready"], "orders": last["orders"], "claims": last["claims"],
                           "provisional_statuses": last["provisional_statuses"],
                           **{f"W_{s}_hours": round(last["by_step"].get(s, 0) / 60, 2) for s in ["census"] + STEPS}})
            cur += dt.timedelta(days=1)
    for s_ in series:
        s_["met_hours"], s_["phase"] = mission(s_["p"])
    for i, s in enumerate(series):
        s["v_hours_per_day"] = round(s["W_hours"] - series[i - 1]["W_hours"], 2) if i else 0.0
    for i, s in enumerate(series):
        win = [x["v_hours_per_day"] for x in series[max(0, i - 1):i + 2]]
        s["v3_hours_per_day"] = round(sum(win) / len(win), 2)
    for i, s in enumerate(series):
        s["a_hours_per_day2"] = round(s["v3_hours_per_day"] - series[i - 1]["v3_hours_per_day"], 2) if i else 0.0

    with open(os.path.join(out, "TRAJECTORY.csv"), "w", encoding="utf-8", newline="") as fh:
        cols = list(series[0]) if series else ["date"]
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(series)
    with open(os.path.join(out, "GENERATION_POINTS.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["landed_utc", "commit", "W_hours", "W_low_hours", "W_high_hours", "p", "met_hours", "phase", "ready",
                    "orders", "claims", "provisional_statuses"])
        for r in rows:
            p_ = r["W_min"] / w_max
            w.writerow([r["landed_utc"], r["commit"][:12], round(r["W_min"] / 60, 2), round(r["W_low_min"] / 60, 2),
                        round(r["W_high_min"] / 60, 2), round(p_, 6), *mission(p_), r["ready"],
                        r["orders"], r["claims"], r["provisional_statuses"]])
    with open(os.path.join(out, "INTERVALS.jsonl"), "w", encoding="utf-8") as fh:
        for it in intervals:
            fh.write(json.dumps(it, sort_keys=True) + "\n")
    mission_rows = [{"key": k, "event": e, "met_hours": round(h, 4), "p": round(h / FIRST_STEP_H, 6),
                     "W_hours": round(h / FIRST_STEP_H * w_max / 60, 1), "phase_after": a} for k, e, h, a in MILESTONES]
    for name, rows_ in (("CREDITS.csv", credit_flat), ("EVENTS.csv", event_flat), ("MISSION.csv", mission_rows)):
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="") as fh:
            if rows_:
                w = csv.DictWriter(fh, fieldnames=list(rows_[0]), lineterminator="\n")
                w.writeheader()
                w.writerows(rows_)
    step_cols = ["census"] + STEPS
    camp = []
    for k, v in campaign_credit.items():
        agents = sorted(a.split(":", 1)[1] for a in v if isinstance(a, str) and a.startswith("agent:") and a != "agent:")
        camp.append({"credited_to": k, "agent": "|".join(agents), "W_hours": round(v["W_min"] / 60, 2),
                     "positive_hours": round(v["positive_min"] / 60, 2), "negative_hours": round(v["negative_min"] / 60, 2),
                     "first_utc": v.get("first", ""), "last_utc": v.get("last", ""),
                     **{f"h_{c}": round(v.get(f"step:{c}", 0) / 60, 2) for c in step_cols}})
    camp.sort(key=lambda x: -x["W_hours"])
    with open(os.path.join(out, "CAMPAIGNS.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(camp[0]) if camp else ["credited_to"], lineterminator="\n")
        w.writeheader()
        w.writerows(camp)
    last = rows[-1] if rows else {}
    summary = {
        "schema": "tsiolkovsky-trajectory/v1", "generations": len(rows), "days": len(series),
        "first_utc": rows[0]["utc"] if rows else "", "last_utc": last.get("utc", ""),
        "W_hours": round(last.get("W_min", 0) / 60, 1), "W_max_hours": round(w_max / 60, 1),
        "p": round(last.get("W_min", 0) / w_max, 5) if rows else 0,
        "met_hours_and_phase": list(mission(last.get("W_min", 0) / w_max)) if rows else [],
        "ready": last.get("ready"), "orders": last.get("orders"),
        "v3_hours_per_day_latest": series[-1]["v3_hours_per_day"] if series else 0,
        "a_hours_per_day2_latest": series[-1]["a_hours_per_day2"] if series else 0,
        "top_credited": camp[:12], "weights_minutes": WEIGHTS, "credits": {"provisional": PROVISIONAL,
                                                                           "original_text": TEXT_CREDIT, "claim_steps": CLAIM_CREDIT},
        "what_this_is_not": "A measure of verified work held, from the tracker's own step states. Not a count of "
                            "certified dossiers (0), not a legal finding; attribution is by landing order, not causation.",
    }
    with open(os.path.join(out, "SUMMARY.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
    print(json.dumps({k: summary[k] for k in ("generations", "days", "W_hours", "W_max_hours", "p", "ready")}))
    return summary


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)

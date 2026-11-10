"""Nalimov verification: two blind verifiers per claim, typed controls, tokens per claim.

Sessions come from packets.build. Each session is shown to two arms (A and B), each in its own fresh folder outside
the repository holding only PROMPT.md and its own shuffled PACKET.json; the sealed key stays in the control folder.
Workers run on the Maudslay conveyor's worker interface (jobs/maudslay-conveyor/conveyor.py: the same workers file,
command templates, refusals, budget flags and usage parsing), or by hand: `prepare` writes the folders, a
coordinator runs one fresh agent per folder and records its usage with `record-usage`, then `score`.

Scoring (no legal judgment): a genuine claim is upheld only if both arms upheld it; blocked only if both rejected it;
anything else goes to ADJUDICATE.json for the coordinator. A control is caught only if both arms rejected it and each
named a defect code its kind maps to (packets.CATCH). Any missed control stops the batch: nothing in it files.
"""
from __future__ import annotations

import concurrent.futures as cf
import importlib.util
import json
import os
import random
import subprocess
import time
from pathlib import Path

import packets as K

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ARMS = ("A", "B")
# Respondendi needs an independent status review by someone other than both blind arms and the producer. "S" reads the
# same session packet and answers the status question only (prompts/status_reviewer.md); its accept is the kit's
# STATUS_REVIEW.json judgment, written by the coordinator with that reviewer's name. Optional: prepare(status=True).
STATUS_ARM = "S"


def _conveyor():
    path = REPO / "jobs/maudslay-conveyor/conveyor.py"
    spec = importlib.util.spec_from_file_location("nalimov_conveyor", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def read_jsonl(path):
    out = []
    try:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    out.append({"_unparsed": line[:200]})
    except OSError:
        pass
    return out


def check_scratch(scratch, repo=REPO):
    scratch = Path(scratch).resolve()
    repo = Path(repo).resolve()
    if scratch.is_relative_to(repo) or repo.is_relative_to(scratch):
        raise ValueError("the scratch folder must be outside the repository (worker folders and the key stay out of it)")
    return scratch


def prepare(sessions, key, scratch, salt, status=False):
    """Worker folders, one per (session, arm), and the sealed key. Returns the list of folders."""
    scratch = check_scratch(scratch)
    control = scratch / "control"
    if (control / "KEY.json").exists():
        raise ValueError(f"a key already exists in {control}; use a new scratch folder per batch")
    write_json(control / "KEY.json", dict(key, salt=salt))
    prompts = {a: (HERE / "prompts/verifier.md").read_text(encoding="utf-8") for a in ARMS}
    if status:
        prompts[STATUS_ARM] = (HERE / "prompts/status_reviewer.md").read_text(encoding="utf-8")
    folders = []
    for s in sessions:
        for arm, prompt in prompts.items():
            folder = scratch / "workers" / f"{s['session']}-{arm}"
            folder.mkdir(parents=True, exist_ok=False)
            mine = dict(s, entries=list(s["entries"]), actors=list(s["actors"]))
            rng = random.Random(K.sha(f"{salt}:{s['session']}:{arm}"))
            rng.shuffle(mine["entries"])
            rng.shuffle(mine["actors"])
            mine.pop("session", None)
            (folder / "PACKET.json").write_text(json.dumps(mine, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
            (folder / "PROMPT.md").write_text(prompt, encoding="utf-8")
            folders.append(folder)
    write_json(scratch / "SESSIONS.json", {"sessions": [s["session"] for s in sessions], "arms": list(prompts),
                                           "packet_measures": {s["session"]: K.measure(s) for s in sessions}})
    return folders


def record_usage(scratch, label, model, model_family, tokens, usd=None, seconds=None, tool_uses=None, source="manual"):
    """Usage of a worker run by hand (an Agent-tool subagent's task notification). One line per worker folder."""
    scratch = check_scratch(scratch)
    rec = {"label": label, "model": model, "model_family": model_family, "tokens": int(tokens), "usd": usd,
           "seconds": seconds, "tool_uses": tool_uses, "source": source, "recorded_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(scratch / "USAGE.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def run(scratch, workers_file, parallel=2, timeout=1800):
    """Run every unfinished folder with the Maudslay workers file's reviewer_A / reviewer_B roles."""
    conv = _conveyor()
    scratch = check_scratch(scratch)
    workers = conv.load_workers(workers_file)
    folders = sorted((scratch / "workers").iterdir())
    control = (scratch / "control").as_posix().lower()

    def one(folder):
        arm = folder.name.rsplit("-", 1)[1]
        w = workers.get(f"reviewer_{arm}") or workers["reviewer_A"]   # the status reader uses arm A's settings
        if (folder / "VERDICTS.jsonl").exists() and (folder / "RUN.json").exists():
            return read_json(folder / "RUN.json")
        mapping = {"model": w["model"], "max_turns": w.get("max_turns", 40), "repo": folder.as_posix(),
                   "reasoning_effort": w.get("reasoning_effort", "medium"), "cwd": folder.as_posix(),
                   "item_usd": w.get("item_usd", 2), "auto_compact_tokens": w.get("auto_compact_tokens", 120000),
                   "tool_output_tokens": w.get("tool_output_tokens", 6000),
                   "writable_roots": json.dumps([folder.as_posix()]), "network": "false"}
        argv = conv.render_args(w["command"], mapping)
        if w.get("program"):
            argv[0] = conv.resolve_program(w["program"]).as_posix()
        argv = conv.validate_worker_command(argv, w["family"])
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD"}
        t0 = time.time()
        with open(folder / "events.out", "w", encoding="utf-8") as out:
            proc = subprocess.run(argv, input=(folder / "PROMPT.md").read_text(encoding="utf-8"), text=True,
                                  stdout=out, stderr=subprocess.PIPE, cwd=folder, env=env, timeout=timeout)
        text = (folder / "events.out").read_text(encoding="utf-8")
        usage = conv.parse_usage(text)
        others = [p.name.lower() for p in (scratch / "workers").iterdir() if p != folder]
        violations = []
        for line in text.splitlines():
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            for s in conv.tool_strings(ev):
                low = str(s).replace("\\", "/").lower()
                if control in low or any(o in low for o in others):
                    violations.append(str(s)[:200])
        rec = {"label": folder.name, "model": w["model"], "model_family": w.get("model_family"), "exit": proc.returncode,
               "tokens": conv.tokens(usage), "usd": conv.price(usage, w.get("prices_usd_per_mtok")),
               "seconds": round(time.time() - t0, 1), "blinding_violations": violations, "source": "conveyor_worker"}
        write_json(folder / "RUN.json", rec)
        return rec

    with cf.ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
        recs = list(pool.map(one, folders))
    with open(scratch / "USAGE.jsonl", "a", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return recs


def score(scratch, usd_per_mtok=None):
    """SCORE.json and ADJUDICATE.json from the verdicts, the key and the usage records."""
    scratch = check_scratch(scratch)
    key = read_json(scratch / "control/KEY.json")
    if not key:
        raise ValueError("no sealed key in the control folder")
    verdicts, problems = {}, []
    for s in key["sessions"]:
        for arm in ARMS:
            folder = scratch / "workers" / f"{s}-{arm}"
            rows = read_jsonl(folder / "VERDICTS.jsonl")
            packet = read_json(folder / "PACKET.json") or {}
            want = {e["entry_id"] for e in packet.get("entries") or []}
            got = {}
            for r in rows:
                eid = r.get("entry_id")
                ok = (eid in want and r.get("verdict") in ("uphold", "reject")
                      and isinstance(r.get("defects"), list) and (r["verdict"] == "uphold" or r["defects"]))
                if not ok or eid in got:
                    problems.append({"session": s, "arm": arm, "row": str(r)[:200], "problem": "invalid or duplicate verdict"})
                    continue
                got[eid] = r
            missing = sorted(want - set(got))
            if missing:
                problems.append({"session": s, "arm": arm, "problem": f"{len(missing)} entries without a verdict"})
            verdicts[(s, arm)] = got
        sfolder = scratch / "workers" / f"{s}-{STATUS_ARM}"
        if sfolder.exists():
            got = {}
            for r in read_jsonl(sfolder / "VERDICTS.jsonl"):
                if r.get("status_verdict") in ("accept", "reject") and r.get("entry_id") not in got:
                    got[r.get("entry_id")] = r
                else:
                    problems.append({"session": s, "arm": STATUS_ARM, "row": str(r)[:200], "problem": "invalid status verdict"})
            verdicts[(s, STATUS_ARM)] = got
    status_used = any(k[1] == STATUS_ARM for k in verdicts)
    genuine, controls, adjudicate = [], [], []
    for s, info in key["sessions"].items():
        for g in info["genuine"]:
            arms = {a: verdicts.get((s, a), {}).get(g["entry_id"]) for a in ARMS}
            v = {a: (r or {}).get("verdict") for a, r in arms.items()}
            outcome = ("upheld" if all(x == "uphold" for x in v.values()) else
                       "blocked" if all(x == "reject" for x in v.values()) else "adjudicate")
            row = {"session": s, "entry_id": g["entry_id"], "instrument_id": g["instrument_id"], "outcome": outcome,
                   "verdicts": {a: {"verdict": (r or {}).get("verdict"), "defects": (r or {}).get("defects"),
                                    "reason": (r or {}).get("reason")} for a, r in arms.items()}}
            if status_used:
                sr = verdicts.get((s, STATUS_ARM), {}).get(g["entry_id"]) or {}
                row["status_review"] = {"verdict": sr.get("status_verdict"), "reason": sr.get("reason")}
            genuine.append(row)
            if outcome != "upheld":
                adjudicate.append(row)
        for c in info["controls"]:
            arms = {a: verdicts.get((s, a), {}).get(c["entry_id"]) for a in ARMS}
            caught = {a: bool(r and r.get("verdict") == "reject" and set(r.get("defects") or []) & set(c["catch"]))
                      for a, r in arms.items()}
            rejected = {a: bool(r and r.get("verdict") == "reject") for a, r in arms.items()}
            row = {"session": s, **{k: c[k] for k in ("entry_id", "instrument_id", "control_kind", "family")},
                   "caught": all(caught.values()), "caught_by_arm": caught, "rejected_by_arm": rejected}
            if status_used:
                sr = verdicts.get((s, STATUS_ARM), {}).get(c["entry_id"]) or {}
                row["status_arm_rejected"] = sr.get("status_verdict") == "reject"
            controls.append(row)
    usage = read_jsonl(scratch / "USAGE.jsonl")
    tok = sum(int(u.get("tokens") or 0) for u in usage)
    usd = [u.get("usd") for u in usage]
    usd_total = sum(float(x) for x in usd if x is not None) if any(x is not None for x in usd) else None
    if usd_total is None and usd_per_mtok:
        usd_total = tok * float(usd_per_mtok) / 1e6
    n = len(genuine)
    upheld = sum(1 for g in genuine if g["outcome"] == "upheld")
    caught = sum(1 for c in controls if c["caught"])
    by_kind = {}
    for c in controls:
        k = by_kind.setdefault(c["control_kind"], {"planted": 0, "caught": 0})
        k["planted"] += 1
        k["caught"] += int(c["caught"])
    out = {"schema": "nalimov-verification-score/v1", "genuine_claims": n, "upheld_by_both": upheld,
           "blocked_by_both": sum(1 for g in genuine if g["outcome"] == "blocked"),
           "to_adjudicate": len(adjudicate), "upheld_rate": round(upheld / n, 4) if n else None,
           "controls_planted": len(controls), "controls_caught": caught,
           "control_catch_rate": round(caught / len(controls), 4) if controls else None, "controls_by_kind": by_kind,
           "missed_controls": [c for c in controls if not c["caught"]], "stop": any(not c["caught"] for c in controls),
           "worker_runs": len(usage), "tokens": tok, "usd": usd_total,
           "tokens_per_genuine_claim": round(tok / n) if n else None,
           "usd_per_genuine_claim": round(usd_total / n, 4) if (n and usd_total is not None) else None,
           "usd_per_upheld_claim": round(usd_total / upheld, 4) if (upheld and usd_total is not None) else None,
           "status_reviews": ({"accepted": sum(1 for g in genuine if (g.get("status_review") or {}).get("verdict") == "accept"),
                               "status_determining_controls_rejected": sum(
                                   1 for c in controls if c.get("status_arm_rejected") and c["control_kind"] in K.STATUS_DETERMINING),
                               "status_determining_controls": sum(1 for c in controls if c["control_kind"] in K.STATUS_DETERMINING)}
                              if status_used else None),
           "verdict_problems": problems, "genuine": genuine, "controls": controls}
    write_json(scratch / "SCORE.json", out)
    write_json(scratch / "ADJUDICATE.json", {"blocks_filing": bool(adjudicate) or out["stop"], "items": adjudicate})
    return out


def reveal(scratch):
    """After a clean score: copy the genuine twins of mutation controls to REVEAL.json in the control folder, for the
    after-reveal review of each genuine control claim (Respondendi checklist item 16)."""
    scratch = check_scratch(scratch)
    key = read_json(scratch / "control/KEY.json")
    twins = [{"session": s, "entry_id": c["genuine_entry_id"], "control_entry_id": c["entry_id"], "kind": c["control_kind"]}
             for s, info in key["sessions"].items() for c in info["controls"] if c.get("genuine_entry_id")]
    write_json(scratch / "control/REVEAL.json", {"twins": twins})
    return twins

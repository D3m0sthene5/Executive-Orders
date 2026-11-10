"""Nalimov verification: two blind verifiers per claim, a status-only reader, typed controls, tokens per claim.

Sessions come from packets.build. Each session is shown to two arms (A and B), and optionally to a status-only
reader (S), each in its own fresh folder outside the repository holding only PROMPT.md and its own shuffled
PACKET.json. The sealed key lives in a separate key folder (`key_dir`), outside the repository and outside the scratch
tree, so no relative path from a worker folder reaches it. Workers run on the Maudslay conveyor's worker interface
(jobs/maudslay-conveyor/conveyor.py: the same workers file, command templates, refusals, budget flags and usage
parsing), or by hand: `prepare` writes the folders, a coordinator runs one fresh agent per folder and records its usage
with `record-usage`, then `score`.

Scoring (no legal judgment): a genuine claim is upheld only if both arms upheld it; blocked only if both rejected it;
anything else goes to ADJUDICATE.json. A control is caught only if both arms rejected it and each named a defect code
its kind maps to (packets.CATCH). The batch stops (nothing in it is installed) on any missed control, on any arm whose
run receipt shows a blinding violation, a non-zero exit or no result, and on a status reader that accepts a
status-determining control.
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
# STATUS_REVIEW.json judgment, written by the coordinator with that reviewer's name. prepare(status=True).
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


def _outside(p, q):
    p, q = Path(p).resolve(), Path(q).resolve()
    return not (p.is_relative_to(q) or q.is_relative_to(p))


def check_scratch(scratch, repo=REPO):
    scratch = Path(scratch).resolve()
    if not _outside(scratch, repo):
        raise ValueError("the scratch folder must be outside the repository (worker folders and the key stay out of it)")
    return scratch


def check_key_dir(key_dir, scratch, repo=REPO):
    key_dir = Path(key_dir).resolve()
    if not _outside(key_dir, repo) or not _outside(key_dir, scratch):
        raise ValueError("the key folder must be outside the repository and outside the scratch tree")
    return key_dir


def prepare(sessions, key, scratch, salt, key_dir, status=False):
    """Worker folders, one per (session, arm), and the sealed key in key_dir. Returns the list of folders."""
    scratch = check_scratch(scratch)
    key_dir = check_key_dir(key_dir, scratch)
    if (key_dir / "KEY.json").exists():
        raise ValueError(f"a key already exists in {key_dir}; use a new key folder per batch")
    if (scratch / "workers").exists():
        raise ValueError(f"{scratch} already holds worker folders; use a new scratch folder per batch")
    write_json(key_dir / "KEY.json", dict(key, salt=salt, scratch=str(scratch)))
    for s in sessions:
        bad = K.tells(s)
        if bad:
            raise ValueError(f"session {s['session']} has mechanical control tells: {bad[:3]}")
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
    """Usage of a worker run by hand (an Agent-tool subagent's task notification). The latest line per label counts."""
    scratch = check_scratch(scratch)
    if not (scratch / "workers" / label).is_dir():
        raise ValueError(f"no worker folder {label}")
    rec = {"label": label, "model": model, "model_family": model_family, "tokens": int(tokens), "usd": usd,
           "seconds": seconds, "tool_uses": tool_uses, "source": source,
           "recorded_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(scratch / "USAGE.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def violations_in(text, conv, folder, scratch, key_dir):
    """Tool-call arguments that reach outside the worker's own folder: the key folder (by absolute path or the names
    KEY.json / control), another worker's folder, or a parent-relative path."""
    others = [p.name.lower() for p in (scratch / "workers").iterdir() if p != folder]
    keyp = key_dir.as_posix().lower()
    out = []
    for line in text.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        for s in conv.tool_strings(ev):
            low = str(s).replace("\\", "/").lower()
            if (keyp in low or "key.json" in low or "/control" in low or "../" in low or low.startswith("..")
                    or any(o in low for o in others)):
                out.append(str(s)[:200])
    return out


def run(scratch, workers_file, key_dir, parallel=2, timeout=1800):
    """Run every folder without a good run receipt, with the workers file's reviewer_A / reviewer_B roles (the status
    reader uses a 'reviewer_S' role when the file has one, else arm A's). Each attempt keeps its own event file."""
    conv = _conveyor()
    scratch = check_scratch(scratch)
    key_dir = check_key_dir(key_dir, scratch)
    raw = read_json(workers_file) or {}
    workers = conv.load_workers(workers_file)
    status_worker = None
    if isinstance(raw.get("reviewer_S"), dict):   # normalized exactly as load_workers normalizes a reviewer role
        status_worker = dict(raw["reviewer_S"])
        cmd = status_worker.get("command", status_worker.get("family", "claude"))
        if cmd in ("claude", "codex"):
            status_worker["command"] = list(conv.CLAUDE_TEMPLATE if cmd == "claude" else conv.CODEX_TEMPLATE)
            status_worker["family"] = status_worker.get("family") or cmd
        else:
            status_worker["family"] = status_worker.get("family") or conv.program_family(cmd[0]) or "generic"
        status_worker.setdefault("model_family", {"claude": "Anthropic", "codex": "OpenAI"}.get(status_worker["family"], "unknown"))
    folders = sorted((scratch / "workers").iterdir())

    def one(folder):
        arm = folder.name.rsplit("-", 1)[1]
        receipt = read_json(folder / "RUN.json") or {}
        if receipt.get("ok"):
            return receipt
        w = workers.get(f"reviewer_{arm}") or status_worker or workers["reviewer_A"]
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
        attempt = len(receipt.get("attempts") or []) + 1
        events = folder / f"events-{attempt}.out"
        t0 = time.time()
        with open(events, "x", encoding="utf-8") as out:
            proc = subprocess.run(argv, input=(folder / "PROMPT.md").read_text(encoding="utf-8"), text=True,
                                  stdout=out, stderr=subprocess.PIPE, cwd=folder, env=env, timeout=timeout)
        text = events.read_text(encoding="utf-8")
        usage = conv.parse_usage(text)
        bad = violations_in(text, conv, folder, scratch, key_dir)
        rec = {"label": folder.name, "attempt": attempt, "events": events.name, "model": w["model"],
               "model_family": w.get("model_family"), "exit": proc.returncode, "result_seen": usage.get("result_seen"),
               "is_error": usage.get("is_error"), "tokens": conv.tokens(usage),
               "usd": conv.price(usage, w.get("prices_usd_per_mtok")), "seconds": round(time.time() - t0, 1),
               "blinding_violations": bad, "source": "conveyor_worker"}
        rec["ok"] = bool(proc.returncode == 0 and usage.get("result_seen") and not usage.get("is_error") and not bad)
        rec["attempts"] = (receipt.get("attempts") or []) + [{k: rec[k] for k in ("attempt", "exit", "tokens", "usd", "ok")}]
        write_json(folder / "RUN.json", rec)
        with open(scratch / "USAGE.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({k: rec[k] for k in ("label", "attempt", "model", "model_family", "tokens", "usd",
                                                     "seconds", "source")}, ensure_ascii=False) + "\n")
        return rec

    with cf.ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
        return list(pool.map(one, folders))


def _usage(scratch):
    """Every attempt counts once: the latest line per (label, attempt)."""
    rows = {}
    for u in read_jsonl(scratch / "USAGE.jsonl"):
        rows[(u.get("label"), u.get("attempt"))] = u
    return list(rows.values())


def score(scratch, key_dir, usd_per_mtok=None):
    """SCORE.json and ADJUDICATE.json from the verdicts, the key, the run receipts and the usage records."""
    scratch = check_scratch(scratch)
    key_dir = check_key_dir(key_dir, scratch)
    key = read_json(key_dir / "KEY.json")
    if not key:
        raise ValueError("no sealed key in the key folder")
    verdicts, problems, invalid_arms, manual_arms = {}, [], [], []
    for s in key["sessions"]:
        for arm in ARMS + (STATUS_ARM,):
            folder = scratch / "workers" / f"{s}-{arm}"
            if not folder.exists():
                continue
            receipt = read_json(folder / "RUN.json")
            if receipt is None:
                manual_arms.append(folder.name)
            elif not receipt.get("ok"):
                invalid_arms.append({"label": folder.name, "exit": receipt.get("exit"),
                                     "result_seen": receipt.get("result_seen"),
                                     "blinding_violations": receipt.get("blinding_violations")})
            rows = read_jsonl(folder / "VERDICTS.jsonl")
            packet = read_json(folder / "PACKET.json") or {}
            want = {e["entry_id"] for e in packet.get("entries") or []}
            got = {}
            for r in rows:
                eid = r.get("entry_id")
                if arm == STATUS_ARM:
                    ok = eid in want and r.get("status_verdict") in ("accept", "reject")
                else:
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
    status_used = any(k[1] == STATUS_ARM for k in verdicts)
    genuine, controls, adjudicate = [], [], []
    for s, info in key["sessions"].items():
        for g in info["genuine"]:
            arms = {a: verdicts.get((s, a), {}).get(g["entry_id"]) for a in ARMS}
            v = {a: (r or {}).get("verdict") for a, r in arms.items()}
            outcome = ("upheld" if all(x == "uphold" for x in v.values()) else
                       "blocked" if all(x == "reject" for x in v.values()) else "adjudicate")
            row = {"session": s, "entry_id": g["entry_id"], "instrument_id": g["instrument_id"], "outcome": outcome,
                   "draft_sha256": g.get("draft_sha256"),
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
    usage = _usage(scratch)
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
    status_misses = [c for c in controls if status_used and c["control_kind"] in K.STATUS_DETERMINING
                     and not c.get("status_arm_rejected")]
    stop_reasons = []
    if any(not c["caught"] for c in controls):
        stop_reasons.append("a planted control was missed by an arm")
    if invalid_arms:
        stop_reasons.append("an arm's run receipt shows a blinding violation, a non-zero exit or no result")
    if status_misses:
        stop_reasons.append("the status reader accepted a status-determining control")
    out = {"schema": "nalimov-verification-score/v1", "genuine_claims": n, "upheld_by_both": upheld,
           "blocked_by_both": sum(1 for g in genuine if g["outcome"] == "blocked"),
           "to_adjudicate": len(adjudicate), "upheld_rate": round(upheld / n, 4) if n else None,
           "controls_planted": len(controls), "controls_caught": caught,
           "control_catch_rate": round(caught / len(controls), 4) if controls else None, "controls_by_kind": by_kind,
           "missed_controls": [c for c in controls if not c["caught"]], "stop": bool(stop_reasons),
           "stop_reasons": stop_reasons, "invalid_arms": invalid_arms, "arms_without_run_receipt": manual_arms,
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


def reveal(scratch, key_dir):
    """After a clean score: the genuine twins of mutation controls, for the after-reveal review of each genuine
    control claim (Respondendi checklist item 16). Written to the key folder."""
    scratch = check_scratch(scratch)
    key_dir = check_key_dir(key_dir, scratch)
    key = read_json(key_dir / "KEY.json")
    twins = [{"session": c.get("genuine_session"), "entry_id": c["genuine_entry_id"], "control_entry_id": c["entry_id"],
              "kind": c["control_kind"]}
             for s, info in key["sessions"].items() for c in info["controls"] if c.get("genuine_entry_id")]
    write_json(key_dir / "REVEAL.json", {"twins": twins})
    return twins

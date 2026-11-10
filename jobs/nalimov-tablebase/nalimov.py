"""Nalimov tablebase: script-completed claims, small verification packets, batched by acting instrument.

    python -I jobs/nalimov-tablebase/nalimov.py census  --data CHECKOUT --out research/nalimov/census [--evidence-cache DIR]
    python -I jobs/nalimov-tablebase/nalimov.py draft   --packet BATCH/packet --out SCRATCH/drafts [--mentions CSV]
    python -I jobs/nalimov-tablebase/nalimov.py install --packet BATCH/packet --drafts SCRATCH/drafts --only-upheld SCORE.json
    python -I jobs/nalimov-tablebase/nalimov.py sessions --drafts SCRATCH/drafts --scratch SCRATCH/verify --key-dir KEYS/batch
    python -I jobs/nalimov-tablebase/nalimov.py run     --scratch SCRATCH/verify --key-dir KEYS/batch --workers WORKERS.json [--parallel 2]
    python -I jobs/nalimov-tablebase/nalimov.py record-usage --scratch SCRATCH/verify --label s001-A --model M --family F --tokens N
    python -I jobs/nalimov-tablebase/nalimov.py score   --scratch SCRATCH/verify --key-dir KEYS/batch [--usd-per-mtok X]
    python -I jobs/nalimov-tablebase/nalimov.py measure --evidence DIR --out research/nalimov/MEASURES.json

Route (see README.md): prepare the batch with the kit (`kit.py prepare --action status_assignment.undecided`), `draft`
in place of producers, `sessions` + `run` (or hand-run agents and `record-usage`) + `score` in place of the blind
arms' research, then `install` only the upheld drafts and continue with the kit's own apply, batch-check, status review
(the verifier's recorded verdict is not a status review; see README), overlay-propose and completion. Nothing here
files, adopts or certifies.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import secrets
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import drafter as D  # noqa: E402
import packets as K  # noqa: E402
import verify as V  # noqa: E402

csv.field_size_limit(1 << 30)


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as fh:
        rd = csv.DictReader(fh)
        return list(rd.fieldnames or []), list(rd)


def write_csv(path, fields, rows):
    with Path(path).open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def dump(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def slug(iid):
    return iid.replace(":", "_")


def draft_packet(packet, out, mentions_csv=None):
    """Draft every undecided member of a prepared kit packet into its own producer folder (the files a Maudslay
    producer writes). Returns the summary written to OUT/DRAFTS.json."""
    packet, out = Path(packet), Path(out)
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"{out} is not empty; drafts are never overwritten")
    dfields, drows = read_csv(packet / "decisions.csv")
    cfields, crows = read_csv(packet / "clauses.csv")
    index = D.mentions_index(csv.DictReader(open(mentions_csv, encoding="utf-8"))) if mentions_csv else None
    summary = {"schema": "nalimov-drafts/v1", "drafter": D.DRAFTER_VERSION, "packet": packet.as_posix(),
               "complete": [], "blocked": {}}
    for ev_path in sorted((packet / "undecided").glob("EO_*/EVIDENCE.json")):
        ev = json.loads(ev_path.read_text(encoding="utf-8"))
        iid = ev["instrument_id"]
        prow = next((r for r in drows if r["instrument_id"] == iid), None)
        pclauses = [c for c in crows if c["instrument_id"] == iid]
        blank = json.loads((ev_path.parent / "STATUS_DECISION.json").read_text(encoding="utf-8"))
        dr = D.draft(ev, prow, pclauses, blank, mentions=D.mentions_for(index, iid) if index else None)
        folder = out / slug(iid)
        folder.mkdir(parents=True)
        dump(folder / "DRAFT.json", dr)
        if not dr.ok:
            summary["blocked"][iid] = dr["blockers"]
            continue
        write_csv(folder / "decisions.csv", dfields, [{k: dr["row"].get(k, "") for k in dfields}])
        write_csv(folder / "clauses.csv", cfields, [{k: c.get(k, "") for k in cfields} for c in dr["clauses"]])
        (folder / "RATIONALES.json").write_text("{}\n", encoding="utf-8")
        dump(folder / "STATUS_DECISION.json", dr["decision"])
        (folder / "EVIDENCE.path").write_text(ev_path.resolve().as_posix() + "\n", encoding="utf-8")
        summary["complete"].append(iid)
    dump(out / "DRAFTS.json", summary)
    return summary


def load_drafts(drafts):
    """(complete drafts, their evidence) from a draft folder."""
    drafts = Path(drafts)
    done, evidence = [], {}
    for folder in sorted(p for p in drafts.iterdir() if p.is_dir()):
        dr = D.Draft(json.loads((folder / "DRAFT.json").read_text(encoding="utf-8")))
        if not dr.ok:
            continue
        ev_path = Path((folder / "EVIDENCE.path").read_text(encoding="utf-8").strip())
        evidence[dr["instrument_id"]] = json.loads(ev_path.read_text(encoding="utf-8"))
        done.append(dr)
    return done, evidence


def draft_sha(dr):
    return K.sha(K.canon(dict(dr)))


def install(packet, drafts, score_path):
    """Write the drafts that were upheld into the packet: their decisions.csv row and clauses.csv rows replace the
    prepared ones, and STATUS_DECISION.json is filled in place. Every other member is left as prepared.

    Everything is checked before anything is written: the batch did not stop; each member was upheld by both arms
    and, when a status reader ran, accepted by it; the draft is byte-for-byte the one verified (draft_sha256 and the
    recomputed packet entry_id equal SCORE.json's); the packet's evidence and dossier fingerprints are unchanged; the
    prepared row is still unworked (outcome unresolved, not approved) and STATUS_DECISION.json is still blank. Then the
    two CSV files are replaced atomically, the decision files last, and INSTALL.json records the score's sha256 and
    the installed ids."""
    packet, drafts = Path(packet), Path(drafts)
    raw = Path(score_path).read_bytes()
    score = json.loads(raw)
    if score.get("stop"):
        raise ValueError("the verification batch stopped (" + "; ".join(score.get("stop_reasons") or ["missed control"])
                         + "): nothing from it is installed")
    dfields, drows = read_csv(packet / "decisions.csv")
    cfields, crows = read_csv(packet / "clauses.csv")
    plan = []
    for g in score["genuine"]:
        if g["outcome"] != "upheld":
            continue
        iid = g["instrument_id"]
        if "status_review" in g and (g["status_review"] or {}).get("verdict") != "accept":
            raise ValueError(f"{iid}: upheld by both arms but not accepted by the status reader; adjudicate first")
        folder = drafts / slug(iid)
        dr = D.Draft(json.loads((folder / "DRAFT.json").read_text(encoding="utf-8")))
        if not dr.ok or dr.decoy:
            raise ValueError(f"{iid}: the draft folder does not hold a complete genuine draft")
        if g.get("draft_sha256") != draft_sha(dr):
            raise ValueError(f"{iid}: the draft changed after it was verified")
        ev_dir = packet / "undecided" / slug(iid)
        ev = json.loads((ev_dir / "EVIDENCE.json").read_text(encoding="utf-8"))
        if K.entry(dr, ev)["entry_id"] != g["entry_id"]:
            raise ValueError(f"{iid}: the verified packet entry does not match this draft and evidence")
        if dr["decision"].get("evidence_sha256") != ev.get("fingerprint"):
            raise ValueError(f"{iid}: the packet's frozen evidence changed since drafting")
        prepared = next((r for r in drows if r["instrument_id"] == iid), None)
        if prepared is None or dr["row"]["dossier_sha256"] != prepared["dossier_sha256"]:
            raise ValueError(f"{iid}: dossier fingerprint differs from the prepared row")
        if prepared.get("outcome") != "unresolved" or prepared.get("approved") not in ("", "false"):
            raise ValueError(f"{iid}: the prepared row was already worked ({prepared.get('agent')}, {prepared.get('outcome')})")
        blank = json.loads((ev_dir / "STATUS_DECISION.json").read_text(encoding="utf-8"))
        if blank.get("approved") or blank.get("recommended_provisional_status") or blank.get("basis_evidence_ids"):
            raise ValueError(f"{iid}: STATUS_DECISION.json is no longer blank")
        plan.append((iid, prepared, dr, ev_dir))
    for iid, prepared, dr, _ in plan:
        prepared.clear()
        prepared.update({k: dr["row"].get(k, "") for k in dfields})
        crows = [c for c in crows if c["instrument_id"] != iid] + [{k: c.get(k, "") for k in cfields} for c in dr["clauses"]]
    for name, fields, rows in (("decisions.csv", dfields, drows), ("clauses.csv", cfields, crows)):
        tmp = packet / (name + ".nalimov-tmp")
        write_csv(tmp, fields, rows)
        os.replace(tmp, packet / name)
    for iid, _, dr, ev_dir in plan:
        dump(ev_dir / "STATUS_DECISION.json", dr["decision"])
    receipt = {"schema": "nalimov-install/v1", "score_sha256": K.sha(raw.decode("utf-8")),
               "installed": [p[0] for p in plan], "drafter": D.DRAFTER_VERSION}
    dump(packet / "NALIMOV_INSTALL.json", receipt)
    return receipt


def make_sessions(drafts, scratch, salt, key_dir, size=K.SESSION_TARGETS, decoys=None, status=True):
    done, evidence = load_drafts(drafts)
    sess, key = K.build(done, evidence, salt, decoys=decoys, size=size)
    shas = {dr["instrument_id"]: draft_sha(dr) for dr in done}
    for info in key["sessions"].values():
        for g in info["genuine"]:
            g["draft_sha256"] = shas[g["instrument_id"]]
    V.prepare(sess, key, scratch, salt, key_dir, status=status)
    return {"sessions": len(sess), "genuine": len(done), "controls": sum(len(v["controls"]) for v in key["sessions"].values()),
            "measures": {s["session"]: K.measure(s) for s in sess}}


def measure(evidence_dir, out, size=K.SESSION_TARGETS, salt="nalimov-measure", mentions_csv=None, sessions_out=None,
            only=None):
    """Verification packet size against the frozen dossier each worker reads today, on real frozen evidence."""
    evidence_dir = Path(evidence_dir)
    index = D.mentions_index(csv.DictReader(open(mentions_csv, encoding="utf-8"))) if mentions_csv else None
    ment = (lambda iid: D.mentions_for(index, iid)) if index else (lambda iid: None)
    done, evidence, dossier_chars, decoys = [], {}, {}, []
    keep = set(json.loads(Path(only).read_text(encoding="utf-8"))["passed"]) if only else None
    for p in sorted(evidence_dir.glob("EO_*.json")):
        ev = json.loads(p.read_text(encoding="utf-8"))
        if keep is not None and ev["instrument_id"] not in keep:
            continue
        dr = D.draft(ev, mentions=ment(ev["instrument_id"]))
        if dr.ok:
            done.append(dr)
            evidence[dr["instrument_id"]] = ev
            dossier_chars[dr["instrument_id"]] = len(json.dumps(ev, ensure_ascii=False))
    for p in sorted(evidence_dir.glob("decoy-EO_*.json")):
        ev = json.loads(p.read_text(encoding="utf-8"))
        dr = D.draft(ev, mentions=ment(ev["instrument_id"]),
                     ignore=("another_instrument_acts", "chain_event_by_another_actor", "same_actor_partial_act"))
        if dr.ok and dr.decoy:
            kind = "partial_as_whole" if any(x.startswith("same_actor_partial") for x in dr["ignored"]) else "later_event_removed"
            decoys.append((kind, dr, ev))
    sess, key = K.build(done, evidence, salt, decoys=decoys, size=size)
    if sessions_out:  # the measured packets, for inspection; outside the repository (they carry held text)
        V.check_scratch(sessions_out)
        Path(sessions_out).mkdir(parents=True, exist_ok=True)
        for s_ in sess:
            dump(Path(sessions_out) / f"{s_['session']}.json", s_)
    per = [K.measure(s) for s in sess]
    total_chars = sum(m["chars"] for m in per)
    genuine = len(done)
    result = {"schema": "nalimov-packet-measures/v1", "orders": genuine, "sessions": len(sess),
              "controls": sum(len(v["controls"]) for v in key["sessions"].values()),
              "controls_by_kind": _count(c["control_kind"] for v in key["sessions"].values() for c in v["controls"]),
              "decoys_available": len(decoys),
              "packet_chars_total": total_chars, "packet_tokens_est_total": round(total_chars / 4),
              "packet_tokens_est_per_genuine_claim": round(total_chars / 4 / max(1, genuine)),
              "dossier_chars_per_order_mean": round(sum(dossier_chars.values()) / max(1, genuine)),
              "dossier_tokens_est_per_order_mean": round(sum(dossier_chars.values()) / 4 / max(1, genuine)),
              "ratio_packet_to_dossier": round((total_chars / max(1, genuine)) / max(1, sum(dossier_chars.values()) / max(1, genuine)), 4),
              "actor_batches": _count(len([d for d in done if d["facts"]["actor_id"] == a])
                                      for a in {d["facts"]["actor_id"] for d in done}),
              "sessions_detail": per,
              "note": "Characters of canonical JSON; tokens estimated at 4 characters a token. The dossier figure is "
                      "the frozen EVIDENCE.json alone (each worker on the full route also reads DOSSIER.json, the "
                      "prompt, the view and its own tool output: about 751k tokens per attempted order, Bentham PLAN.md)."}
    dump(out, result)
    return result


def _count(values):
    out = {}
    for v in values:
        out[str(v)] = out.get(str(v), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("census")
    c.add_argument("--data", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--evidence-cache")
    c.add_argument("--chunk", type=int, default=150)
    d = sub.add_parser("draft")
    d.add_argument("--packet", required=True)
    d.add_argument("--out", required=True)
    d.add_argument("--mentions")
    i = sub.add_parser("install")
    i.add_argument("--packet", required=True)
    i.add_argument("--drafts", required=True)
    i.add_argument("--only-upheld", required=True, help="the SCORE.json of the verification batch")
    s = sub.add_parser("sessions")
    s.add_argument("--drafts", required=True)
    s.add_argument("--scratch", required=True, help="new folder outside the repository for the worker folders")
    s.add_argument("--key-dir", required=True, help="new folder outside the repository and the scratch tree; holds "
                                                    "the salt and the sealed key")
    s.add_argument("--size", type=int, default=K.SESSION_TARGETS)
    s.add_argument("--no-status-reader", action="store_true", help="omit the third, status-only reader (S)")
    r = sub.add_parser("run")
    r.add_argument("--scratch", required=True)
    r.add_argument("--key-dir", required=True)
    r.add_argument("--workers", required=True)
    r.add_argument("--parallel", type=int, default=2)
    u = sub.add_parser("record-usage")
    u.add_argument("--scratch", required=True)
    u.add_argument("--label", required=True)
    u.add_argument("--model", required=True)
    u.add_argument("--family", required=True)
    u.add_argument("--tokens", type=int, required=True)
    u.add_argument("--usd", type=float)
    u.add_argument("--seconds", type=float)
    u.add_argument("--tool-uses", type=int)
    sc = sub.add_parser("score")
    sc.add_argument("--scratch", required=True)
    sc.add_argument("--key-dir", required=True)
    sc.add_argument("--usd-per-mtok", type=float)
    rv = sub.add_parser("reveal")
    rv.add_argument("--scratch", required=True)
    rv.add_argument("--key-dir", required=True)
    m = sub.add_parser("measure")
    m.add_argument("--evidence", required=True)
    m.add_argument("--out", required=True)
    m.add_argument("--mentions", help="jobs/current-law/output/MENTIONS.csv")
    m.add_argument("--sessions-out", help="folder outside the repository to keep the measured packets")
    m.add_argument("--only", help="a PRESCREEN.json: measure only the drafts that passed it")
    a = ap.parse_args(argv)
    if a.cmd == "census":
        import census
        res = census.run(a.data, a.out, a.chunk, None, a.evidence_cache)
        print(json.dumps({k: v.get("complete") for k, v in res["kinds"].items()}))
    elif a.cmd == "draft":
        res = draft_packet(a.packet, a.out, a.mentions)
        print(json.dumps({"complete": len(res["complete"]), "blocked": len(res["blocked"])}))
    elif a.cmd == "install":
        print(json.dumps(install(a.packet, a.drafts, a.only_upheld)))
    elif a.cmd == "sessions":
        kd = V.check_key_dir(a.key_dir, V.check_scratch(a.scratch))
        kd.mkdir(parents=True, exist_ok=True)
        sp = kd / "SALT"
        if not sp.exists():
            sp.write_text(secrets.token_hex(16) + "\n", encoding="utf-8")
        print(json.dumps(make_sessions(a.drafts, a.scratch, sp.read_text(encoding="utf-8").strip(), kd, a.size,
                                       status=not a.no_status_reader), indent=1))
    elif a.cmd == "run":
        print(json.dumps(V.run(a.scratch, a.workers, a.key_dir, a.parallel), indent=1))
    elif a.cmd == "record-usage":
        print(json.dumps(V.record_usage(a.scratch, a.label, a.model, a.family, a.tokens, a.usd, a.seconds, a.tool_uses)))
    elif a.cmd == "score":
        res = V.score(a.scratch, a.key_dir, a.usd_per_mtok)
        print(json.dumps({k: res[k] for k in ("genuine_claims", "upheld_by_both", "to_adjudicate", "controls_planted",
                                              "controls_caught", "stop", "stop_reasons", "tokens_per_genuine_claim",
                                              "usd_per_upheld_claim")}))
    elif a.cmd == "reveal":
        print(json.dumps(V.reveal(a.scratch, a.key_dir), indent=1))
    elif a.cmd == "measure":
        print(json.dumps({k: v for k, v in measure(a.evidence, a.out, mentions_csv=a.mentions,
                                                             sessions_out=a.sessions_out, only=a.only).items() if k != "sessions_detail"}, indent=1))


if __name__ == "__main__":
    main()

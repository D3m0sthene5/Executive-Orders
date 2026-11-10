"""Nalimov tablebase: script-completed claims and small verification packets, batched by acting instrument.

    python -I jobs/nalimov-tablebase/nalimov.py census  --data CHECKOUT --out research/nalimov/census [--evidence-cache DIR]
    python -I jobs/nalimov-tablebase/nalimov.py draft   --packet BATCH/packet --out SCRATCH/drafts [--mentions CSV]
    python -I jobs/nalimov-tablebase/nalimov.py measure --evidence DIR --out research/nalimov/MEASURES.json [--only PRESCREEN.json]

Production runs through the Maudslay conveyor (`jobs/maudslay-conveyor/conveyor.py run ... --producer nalimov`): the
drafter replaces the producer stage, the overlay stage carries undecided members through the kit's status review and
overlay-propose, and every review, control, reveal, agreement and completion stage is the conveyor's own. This file
keeps the zero-token tools: the census, a standalone draft of a prepared packet (for inspection), and packet measures.
Nothing here files, adopts or certifies.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import drafter as D  # noqa: E402
import packets as K  # noqa: E402

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
        if Path(sessions_out).resolve().is_relative_to(HERE.parents[1]):
            raise ValueError('sessions_out must be outside the repository (packets carry held text)')
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
    elif a.cmd == "measure":
        print(json.dumps({k: v for k, v in measure(a.evidence, a.out, mentions_csv=a.mentions,
                                                             sessions_out=a.sessions_out, only=a.only).items() if k != "sessions_detail"}, indent=1))


if __name__ == "__main__":
    main()

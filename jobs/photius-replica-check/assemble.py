"""Photius Lane 4, step 3: assemble the worker results into the producer record the tracker reads.

Inputs: work/CANDIDATES.csv (extract.py), research/excavator/photius-replica/packets/*/RESULT.jsonl (Sonnet readers),
research/excavator/photius-replica/adjudication/*/RESULT.jsonl (Opus adjudications of every fail/unsure and a seeded
5% sample of passes). Output under output/: RESULTS.csv (one row per order: reader verdict, adjudication, final),
FRAGMENTS.jsonl (grade archival_replica_checked; needs_page_check false only on a final pass), ADJUDICATION_QUEUE.csv,
SUMMARY.json, REPORT.md, STATUS.json.

A final pass means a worker read the replica and found the expected order (number, date, signature block, first and
last words recorded). It credits the text step under ruling R37's logic (owner prompt 2026-11-06, decision P4); the
bytes stay ProQuest's, acceptable_as_original stays false, and nothing here is a legal conclusion.

    python -I jobs/photius-replica-check/assemble.py [--queue-only]
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import json
import random
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
JOB = "photius-replica-check"
PK = REPO / "research/excavator/photius-replica/packets"
ADJ = REPO / "research/excavator/photius-replica/adjudication"
SEED = 20261106
SAMPLE = 0.05
# Each wave: its candidate list (extract.py output), the folders holding reader results, the folders holding Opus
# adjudications, and its own sampling seed. Lane 4 (2026-11-06) keeps its original inputs and seed, so its rows and
# sample are unchanged; later waves add rows. A later wave's row replaces an earlier one for the same order only when
# the later wave has read it.
WAVES = [
    {"name": "photius-lane4-2026-11-06", "candidates": REPO / "jobs" / JOB / "work/CANDIDATES.csv",
     "readers": [PK], "adjudication": [ADJ], "seed": SEED},
    {"name": "photius-peiresc-2026-11-25", "candidates": REPO / "research/excavator/photius-replica-peiresc/CANDIDATES.csv",
     "readers": [REPO / "research/excavator/photius-replica-peiresc/packets", REPO / "research/excavator/photius-replica-peiresc/probe",
                 REPO / "research/excavator/photius-replica-peiresc/reread"],
     "adjudication": [REPO / "research/excavator/photius-replica-peiresc/adjudication"], "seed": 20261125,
     # PROMPT.md "When you must look at the page": a pass with text-only evidence on an order whose machine read
     # found no number or no exact date, or whose text is unusable, is not accepted.
     "require_image_when_weak": True},
]


def read_results(root):
    out = {}
    for f in sorted(root.glob("*/RESULT.jsonl")):
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(r, dict) and r.get("instrument_id"):
                r["_packet"] = f.parent.name
                out[r["instrument_id"]] = r
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue-only", action="store_true")
    a = ap.parse_args(argv)
    out = REPO / "jobs" / JOB / "output"
    out.mkdir(parents=True, exist_ok=True)
    pq = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / "jobs/pinakes-proquest-ingest/output/ORDERS.csv", encoding="utf-8"))}
    by_id, queue = {}, []
    for wave in WAVES:
        if not wave["candidates"].exists():
            continue
        cands = {r["instrument_id"]: r for r in csv.DictReader(open(wave["candidates"], encoding="utf-8"))}
        readers, adjud = {}, {}
        for root in wave["readers"]:
            if root.exists():
                readers.update(read_results(root))
        for root in wave["adjudication"]:
            if root.exists():
                adjud.update(read_results(root))
        if wave.get("require_image_when_weak"):
            for iid, r in list(readers.items()):
                c = cands.get(iid)
                if (c and r.get("verdict") == "pass" and r.get("evidence", "text") == "text"
                        and (c.get("number_found") == "no" or c.get("date_exact") == "no" or c.get("text_usable") == "no")):
                    readers[iid] = dict(r, verdict="unsure", reason="text-only pass where the brief requires the page image; " + r.get("reason", ""))
        wave_rows, wave_queue = assemble_wave(cands, readers, adjud, random.Random(wave["seed"]))
        for r in wave_rows:
            if r["reader_verdict"] or r["instrument_id"] not in by_id:
                by_id[r["instrument_id"]] = dict(r, wave=wave["name"])
        queue += [dict(q, wave=wave["name"]) for q in wave_queue]
    write_outputs(a, out, list(by_id.values()), queue, pq)


def assemble_wave(cands, readers, adjud, rnd):
    rows, queue = [], []
    for iid, c in cands.items():
        rd = readers.get(iid)
        ad = adjud.get(iid)
        reader_verdict = (rd or {}).get("verdict", "")
        adj_verdict = (ad or {}).get("verdict", "")
        sampled = reader_verdict == "pass" and rnd.random() < SAMPLE
        needs_adj = reader_verdict in ("fail", "unsure") or sampled
        if needs_adj and not ad:
            queue.append({"instrument_id": iid, "reader_verdict": reader_verdict, "why": "reader_" + reader_verdict if reader_verdict != "pass" else "random_5pct_sample",
                          "packet": (rd or {}).get("_packet", "")})
        if ad:
            final = adj_verdict
        elif reader_verdict == "pass" and not needs_adj:
            final = "pass"
        elif reader_verdict == "pass" and sampled:
            final = "pass_pending_sample_adjudication"
        elif reader_verdict:
            final = f"{reader_verdict}_pending_adjudication"
        else:
            final = "unread"
        rows.append({
            "instrument_id": iid, "number": c["number"], "suffix": c["suffix"], "expected_date": c["expected_date"],
            "file": c["file"], "sha256": c["sha256"], "pages": c["pages"], "text_kind": c["text_kind"],
            "reader_packet": (rd or {}).get("_packet", ""), "reader_verdict": reader_verdict,
            "reader_number_seen": (rd or {}).get("number_seen", ""), "reader_date_seen": (rd or {}).get("date_seen", ""),
            "reader_signatory": (rd or {}).get("signatory_seen", ""), "reader_first_words": (rd or {}).get("first_words", ""),
            "reader_last_words": (rd or {}).get("last_words", ""), "reader_evidence": (rd or {}).get("evidence", ""),
            "reader_reason": (rd or {}).get("reason", ""), "sampled_for_adjudication": "yes" if sampled else "no",
            "adjudication_verdict": adj_verdict, "adjudication_reason": (ad or {}).get("reason", ""), "final": final,
        })
    return rows, queue


def write_outputs(a, out, rows, queue, pq):
    with open(out / "ADJUDICATION_QUEUE.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["instrument_id", "reader_verdict", "why", "packet", "wave"])
        w.writeheader()
        w.writerows(queue)
    counts = collections.Counter(r["final"] for r in rows)
    print("rows", len(rows), dict(counts), "adjudication queue", len(queue))
    if a.queue_only:
        return

    with open(out / "RESULTS.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    n_frag = 0
    with open(out / "FRAGMENTS.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            if not r["reader_verdict"]:
                continue
            p = pq[r["instrument_id"]]
            counts_now = r["final"] == "pass"
            page_ref = f"ProQuest Congressional Replica of Original, file {p['file']} ({p['pages']} pages)"
            note = (f"ProQuest replica scan read by a {('Sonnet' if r['reader_verdict'] else '')} worker: number seen '{r['reader_number_seen'][:60]}', "
                    f"date seen {r['reader_date_seen'] or 'none'}, signature block '{r['reader_signatory'][:60]}'; verdict {r['reader_verdict']}"
                    + (f"; Opus adjudication {r['adjudication_verdict']} ({r['adjudication_reason'][:120]})" if r["adjudication_verdict"] else "")
                    + (". Checked replica of the State Department file copy: credits the text step under ruling R37's logic (decision P4, 2026-11-06); bytes remain ProQuest's, to be re-pointed to M1118. "
                       if counts_now else ". Not credited. ")
                    + "Not an authenticated signed original; not a legal conclusion.")
            frag = {
                "acceptable_as_original": False, "confidence_note": note,
                "data": {
                    "acceptable_as_original": False, "grade": "archival_replica_checked" if counts_now else "archival_replica_check_failed_or_pending",
                    "location_confidence": "high" if counts_now else "low", "location_verified": True,
                    "needs_page_check": not counts_now, "page_or_item": page_ref,
                    "representation_type": "proquest_replica_of_original_scan_checked", "route": "archival/proquest_replica_local_file",
                    "sha256": p["sha256"], "signing_date": r["reader_date_seen"] or p.get("signing_date", ""),
                    "source_id": f"{JOB}:{r['instrument_id']}:{p['sha256'][:12]}", "text_path": f"../../pinakes-proquest-ingest/output/{p['text_path']}",
                    "text_sha256": p["text_sha256"], "title": p.get("title", ""), "url": p.get("accession_url", ""),
                    "bytes_dependency": "ProQuest (licensed replica); public-domain witness pending: NARA M1118",
                    "check": {k: r[k] for k in ("reader_verdict", "reader_number_seen", "reader_date_seen", "reader_signatory",
                                                 "reader_first_words", "reader_last_words", "reader_evidence", "adjudication_verdict", "final")},
                },
                "grade": "archival_replica_checked" if counts_now else "archival_replica_check_failed_or_pending",
                "instrument_id": r["instrument_id"], "kind": "original_representation", "produced_by": JOB,
                "sources": [{"page_or_item": page_ref, "sha256": p["sha256"], "url": p.get("accession_url", "")}],
            }
            f.write(json.dumps(frag, ensure_ascii=False) + "\n")
            n_frag += 1
    summary = {
        "targets": len(rows), "read_by_workers": sum(1 for r in rows if r["reader_verdict"]),
        "reader_verdicts": dict(collections.Counter(r["reader_verdict"] for r in rows if r["reader_verdict"])),
        "adjudicated": sum(1 for r in rows if r["adjudication_verdict"]),
        "adjudication_verdicts": dict(collections.Counter(r["adjudication_verdict"] for r in rows if r["adjudication_verdict"])),
        "final": dict(counts), "credited_archival_replica_checked": counts.get("pass", 0),
        "credited_below_4306": sum(1 for r in rows if r["final"] == "pass" and int(r["number"]) < 4306),
        "fragments": n_frag, "adjudication_queue": len(queue),
        "note": "Checked replicas credit the text step (R37 logic, P4); bytes stay ProQuest's; acceptable_as_original false; no status, census, codebook or certified count change.",
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary, indent=1) + "\n")
    (out / "STATUS.json").write_text(json.dumps({
        "job": JOB, "status": "succeeded", "exit_code": 0, "runner": "owner's PC (Photius session, Agent-tool workers)",
        "branch": "main", "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "note": "PC run; the GitHub runner does not run this job (no job.py). Outputs are for main.",
    }, indent=1) + "\n")
    lines = ["# Photius replica check: report", "", f"Targets {len(rows)}; read {summary['read_by_workers']}; reader verdicts {summary['reader_verdicts']}; "
             f"adjudicated {summary['adjudicated']} ({summary['adjudication_verdicts']}); final {dict(counts)}.",
             f"Credited as archival_replica_checked: {summary['credited_archival_replica_checked']} ({summary['credited_below_4306']} below EO 4306).", "",
             "Fails and unsure after adjudication:", ""]
    for r in rows:
        if r["final"] in ("fail", "unsure"):
            lines.append(f"- {r['instrument_id']}: {r['adjudication_reason'] or r['reader_reason']}")
    (out / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()

"""Build one proof batch's source-supplement declaration and Selden brief from the Selden job outputs.

usage: python3 -I research/selden/proof/tools/supplement.py BATCH EO:1 EO:2 ...
Writes research/selden/proof/packets/BATCH/SUPPLEMENT_SOURCES.json (eo-source-excerpt-declarations/v1, for
jobs/claim-kit/source_supplement.py) and SELDEN_BRIEF.md (every Selden lead per order with held paths). Coordinator
tool: it copies located spans and paths; it makes no legal judgment and picks no mechanism.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "jobs/selden-common"))
import selden_common as S  # noqa: E402
OUT = ROOT / "research/selden/proof/packets"
JOBS = {k: ROOT / "jobs" / k / "output" for k in ("selden-fr-citers", "selden-fr-acting", "selden-statutes")}
# Runner-shard outputs not yet united into the citers job's own output (jobs/selden-fr-citers/data/shards/<k>).
for d in sorted((ROOT / "jobs/selden-fr-citers/data/shards").glob("*")):
    if (d / "SOURCES.jsonl").is_file():
        JOBS["selden-fr-citers:" + d.name] = d
PER_ORDER = 10
WIDEN = 700


def rows(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.is_file() else []


def fsha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def widen(text, lo, hi):
    a = text.rfind("\n\n", max(0, lo - WIDEN), lo)
    b = text.find("\n\n", hi, min(len(text), hi + WIDEN))
    return (a + 2 if a >= 0 else max(0, lo - 200)), (b if b >= 0 else min(len(text), hi + 200))


def alias(*parts):
    a = re.sub(r"[^A-Za-z0-9_-]+", "-", "-".join(parts)).strip("-")
    return ("S" + a)[:96] if not a[:1].isalpha() else a[:96]


def main(batch, *ids):
    ids = list(ids)
    src = {}
    for job, out in JOBS.items():
        for s in rows(out / "SOURCES.jsonl"):
            src[(job, s["sha256"])] = s
    entries, brief, seen = [], [f"# Selden brief for proof batch {batch}\n",
                                "Machine leads from jobs/selden-fr-citers, selden-fr-acting and selden-statutes. Read "
                                "the held text around every excerpt; nothing here is a legal finding.\n"], set()
    searches = {}
    for job in JOBS:
        if job.startswith("selden-fr-citers"):
            for r in rows(JOBS[job] / "SEARCHES.jsonl"):
                if r.get("examined") or r["instrument_id"] not in searches:
                    searches[r["instrument_id"]] = r
    basis = {}
    for b in rows(JOBS["selden-statutes"] / "BASIS.jsonl"):
        basis.setdefault(b["instrument_id"], []).append(b)
    for iid in ids:
        brief.append(f"\n## {iid}\n")
        s = searches.get(iid)
        if s:
            brief.append(f"- Federal Register full-text search: {json.dumps({k: s[k] for k in ('repository', 'query_or_scope', 'checked_on', 'hits', 'examined', 'complete', 'documents_citing', 'documents_acting_on_target', 'limits')}, ensure_ascii=False)}\n")
        else:
            brief.append("- Federal Register full-text search: not yet run for this order.\n")
        leads = []
        for job in JOBS:
            for f in rows(JOBS[job] / "FRAGMENTS.jsonl"):  # noqa: shard dirs hold the same file layout
                if f.get("instrument_id") != iid:
                    continue
                for d in f["data"]:
                    leads.append((job, d))
        leads.sort(key=lambda jd: (jd[1].get("mechanism") == "cross_reference", jd[1].get("flags") and
                                   "agency_document_not_presidential" in jd[1]["flags"], jd[1].get("source_id")))
        n = 0
        for job, d in leads:
            rec = src.get((job, d["source_sha256"]))
            out = JOBS[job]
            tp = out / d["text_path"] if d.get("text_path") else None
            line = (f"- [{job}] acting {d['acting_id']} ({d.get('acting_label', '')[:100]}); printed relation "
                    f"{d.get('mechanism_printed')} -> fragment mechanism {d['mechanism']}; flags {d.get('flags')}; "
                    f"text {tp.relative_to(ROOT) if tp else '-'} (sha256 of text file {fsha(tp)[:16] if tp and tp.is_file() else '-'}); "
                    f"source sha256 {d['source_sha256'][:16]}; quote: \"{re.sub(chr(10), ' ', d['quote'])[:300]}\"")
            local = None
            if rec and rec.get("cache_path"):
                local = out / rec["cache_path"]
            if n < PER_ORDER and tp and tp.is_file() and local and local.is_file() \
                    and fsha(local) == d["source_sha256"]:
                text = tp.read_bytes().decode("utf-8")
                lo, hi = map(int, d["quote_span"].split("-"))
                if text[lo:hi] == d["quote"]:
                    a, b = widen(text, lo, hi)
                    al = alias(job.split(":")[0].split("-")[-1], d["acting_id"], iid)
                    if al in seen:
                        al = alias(al, str(n))
                    seen.add(al)
                    entries.append({"alias": al, "instrument_ids": [iid], "actor_id": d["acting_id"],
                                    "reason": f"Selden {job}: held later-instrument text that prints {iid}'s number "
                                              f"near the word '{d.get('relation_word') or 'none'}' (machine lead)",
                                    "char_start": a, "char_end": b,
                                    "source": {"url": d["source_url"], "sha256": d["source_sha256"],
                                               "text_path": tp.relative_to(ROOT).as_posix(), "text_sha256": fsha(tp),
                                               "page_or_item": d.get("page_or_item") or rec.get("page_or_item"),
                                               "local_path": local.relative_to(ROOT).as_posix()}})
                    line += f" -> SUPPLEMENT:{al}"
                    n += 1
            brief.append(line + "\n")
        for b in basis.get(iid, []):
            otext = (ROOT / b["order_text_path"]).read_text(encoding="utf-8", errors="replace")
            olo, ohi, _ = S.own_span(otext, iid)
            if not olo <= int(b["quote_span"].split("-")[0]) < ohi:
                continue  # cited by a neighbouring document printed on the same pages, not by this order
            rec = next((r for (j, h), r in src.items() if j == "selden-statutes" and h == b["statute_sha256"]), None)
            tp = JOBS["selden-statutes"] / b["statute_text_path"]
            line = (f"- [selden-statutes] the order's own text cites {b['statute']} in: \"{b['quote'][:240]}\"; statute "
                    f"text {tp.relative_to(ROOT)}; page number printed: {b.get('page_number_printed')}")
            if rec and rec.get("cache_path") and n < PER_ORDER and tp.is_file():
                local = JOBS["selden-statutes"] / rec["cache_path"]
                text = tp.read_bytes().decode("utf-8")
                al = alias("stat", b["statute"], iid)
                if al not in seen and local.is_file():
                    seen.add(al)
                    entries.append({"alias": al, "instrument_ids": [iid], "actor_id": "STAT:" + b["statute"].replace(" Stat. ", "-"),
                                    "reason": f"Selden statutes: Statutes at Large text of {b['statute']}, which the order's own text cites (machine lead; not shown to be its basis)",
                                    "char_start": 0, "char_end": min(len(text), 8000),
                                    "source": {"url": b["statute_url"], "sha256": b["statute_sha256"],
                                               "text_path": tp.relative_to(ROOT).as_posix(), "text_sha256": fsha(tp),
                                               "page_or_item": rec.get("page_or_item"),
                                               "local_path": local.relative_to(ROOT).as_posix()}})
                    line += f" -> SUPPLEMENT:{al} (first 8,000 characters; read the full text)"
                    n += 1
            brief.append(line + "\n")
        # Statutes the finding jobs name as acting on this order whose text is held, even when the statute does not
        # print the order's number (the National Emergencies Act for emergency-dependent orders): bind the text so
        # the producer can read and cite it. Binding is not a finding that the statute ended the order.
        for job in JOBS:
            if job != "selden-statutes":
                continue
            for r in rows(JOBS[job] / "SOURCES.jsonl"):
                ids = r.get("instrument_ids") or []
                if iid not in ids[1:] or not r.get("cache_path") or not (ids[0].startswith("PL:") or ":" in ids[0] and
                                                                         not ids[0].startswith("STAT:")):
                    continue
                tp, local = JOBS[job] / r["text_path"], JOBS[job] / r["cache_path"]
                al = alias("actstat", ids[0], iid)
                if al in seen or not tp.is_file() or not local.is_file() or n >= PER_ORDER + 2:
                    continue
                seen.add(al)
                text = tp.read_bytes().decode("utf-8")
                entries.append({"alias": al, "instrument_ids": [iid], "actor_id": ids[0],
                                "reason": f"Selden statutes: Statutes at Large text of {ids[0]}, which the finding jobs "
                                          f"name as acting on {iid} (machine lead; the statute may not name the order)",
                                "char_start": 0, "char_end": min(len(text), 60000),
                                "source": {"url": r["url"], "sha256": r["sha256"], "text_path": tp.relative_to(ROOT).as_posix(),
                                           "text_sha256": fsha(tp), "page_or_item": r.get("page_or_item"),
                                           "local_path": local.relative_to(ROOT).as_posix()}})
                brief.append(f"- [selden-statutes] {ids[0]} is named as acting on this order by a finding job; full "
                             f"statute text {tp.relative_to(ROOT)} -> SUPPLEMENT:{al} (first 60,000 characters)\n")
                n += 1
        if not leads and not basis.get(iid):
            brief.append("- No Selden lead names this order.\n")
    d = OUT / batch
    d.mkdir(parents=True, exist_ok=True)
    (d / "SELDEN_BRIEF.md").write_text("".join(brief), encoding="utf-8")
    decl = {"schema": "eo-source-excerpt-declarations/v1", "sources": entries[:100]}
    (d / "SUPPLEMENT_SOURCES.json").write_text(json.dumps(decl, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"batch": batch, "orders": len(ids), "excerpts": len(decl["sources"]),
                      "orders_with_excerpt": len({i for e in entries for i in e["instrument_ids"]})}))


if __name__ == "__main__":
    main(*sys.argv[1:])

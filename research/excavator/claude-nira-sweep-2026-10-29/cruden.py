"""Cruden: one-pass lookups for a claim-kit packet's members, so producers stop rebuilding search scripts.

Named for Alexander Cruden, whose 1737 concordance listed every occurrence of every word of the Bible.

    python3 -I cruden.py lookups PACKET_DIR      # writes PACKET_DIR/LOOKUPS.md and LOOKUPS.json
    python3 -I cruden.py search REGEX [REGEX ...] # legacy uncached regex full scan; unchanged stdout
    python3 -I cruden.py number EO:6242 [EO:6242C ...] --write RESULTS.json
    python3 -I cruden.py literal "Fitness of American Youth" --write RESULTS.json

`lookups` reports, for every member of a prepared (or supplemented) packet:
  * the census register row (date, title, president, best held copy) and the WPA 1944 numbered-list entry;
  * the APP page check the AGENT_PROTOCOL requires for an APP original: the page record with the same sha256
    (mirror capture or live harvest), its heading, its date, whether its text_sha256 equals the held file's,
    and whether the heading names the order's number;
  * held order texts (every jobs/*/output/texts folder except clause-drafts) that cite the order's number,
    and, when the title names a code of fair competition, texts naming that code;
  * wording in the order's own held text that often signals an own-terms end or a contingent command
    ("until", "for a period of", "pending", "stay", "days after", "expire", "terminate", ...), with offsets.

Every row is a lead for the producer to read and judge. Nothing here decides identity, an end or a status.
"""
import csv
import hashlib
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cruden_cache import Snapshot, SnapshotChanged, normalized, original_span  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
LAST_DETAILS = None
csv.field_size_limit(10 ** 9)
TERM_WORDS = [r"\buntil\b", r"for a period of", r"\bpending\b", r"\bstay(?:ed|s)?\b", r"days? after", r"\bexpir",
              r"\bterminat", r"\bsuspend", r"\bprovisional", r"\bcancel", r"\bfurther order", r"\beffective\b"]


def held_texts():
    for d in sorted((REPO / "jobs").glob("*/output/texts")):
        if d.parent.parent.name == "clause-drafts":
            continue
        for f in sorted(d.rglob("*.txt")):
            yield f


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def number_pattern(iid):
    m = re.match(r"EO:(\d+)([A-Z]?)$", iid)
    if not m:
        return None
    n, s = m.groups()
    suffix = (r"[-\s]?" + s) if s else r"(?![-\s]?[A-Z]\b)"
    return re.compile(r"(?:Executive\s+Orders?\s+(?:No\.?\s*)?|\bOrders?\s+No\.?\s*|E\.\s?O\.\s*)" + n + suffix + r"\b", re.I)


def code_name(title):
    m = re.search(r"Code of Fair Competition for (?:the )?(.+?)(?:\s+Industry|\s+Trade)?$", title or "", re.I)
    return m.group(1).strip() if m else None


def snippet(text, i, j, width=90):
    return re.sub(r"\s+", " ", text[max(0, i - width):j + width]).strip()


def load_members(packet_dir):
    sys.path.insert(0, str(REPO / "jobs/claim-kit"))
    import batch  # noqa: E402
    _, dossiers = batch.load_packet(Path(packet_dir).resolve(), REPO, check_sources=False)
    return dossiers


def lookups(packet_dir):
    global LAST_DETAILS
    started = time.perf_counter()
    inputs = input_manifest(packet_dir)
    source_pins = {}
    dossiers = load_members(packet_dir)
    member_load_seconds = time.perf_counter() - started
    ids = sorted(dossiers)
    register = {r["instrument_id"]: r for r in csv.DictReader(open(REPO / "jobs/domesday-register/output/REGISTER.csv"))
                if r["instrument_id"] in ids}
    wpa = {}
    for r in csv.DictReader(open(REPO / "jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv")):
        if r["id"] in ids:
            wpa.setdefault(r["id"], []).append({k: r[k] for k in ("year", "month_day", "page", "citations_joined", "text")})
    pages = {}
    for name, kind in (("MIRROR_DOCUMENTS.jsonl", "mirror"), ("DOCUMENTS.jsonl", "live_harvest")):
        for line in open(REPO / "jobs/app-executive-orders/output" / name, encoding="utf-8"):
            r = json.loads(line)
            pages.setdefault(r["sha256"], []).append((kind, r))
    out = {}
    pats = {}
    detail_members = {}
    for iid in ids:
        d = dossiers[iid]
        orig = (d.get("evidence") or {}).get("ORIGINAL:" + iid) or {}
        src = orig.get("source") or {}
        reg = register.get(iid, {})
        entry = {"register": {k: reg.get(k) for k in ("date", "title", "president", "best_held", "provisional_status")},
                 "wpa": wpa.get(iid, []), "original": {k: src.get(k) for k in ("grade", "sha256", "text_path", "text_sha256")},
                 "page_check": [], "own_text_signals": [], "number_citations": [], "code_mentions": []}
        num = re.match(r"EO:(\d+)", iid).group(1)
        for kind, r in pages.get(src.get("sha256"), []):
            held = REPO / "jobs/app-executive-orders/output" / r["text_path"]
            page_pin = file_pin(held)
            remember_pin(source_pins, held, page_pin)
            cap = (r.get("capture") or {}).get("archive") if kind == "mirror" else None
            entry["page_check"].append({"record": kind, "capture_archive": cap, "heading": r.get("heading"), "date": r.get("date"),
                                        "heading_names_number": bool(re.search(r"\b" + num + r"(?:-?[A-Z])?\b", r.get("heading") or "")),
                                        "text_sha256_equal": page_pin["sha256"] is not None and page_pin["sha256"] == r.get("text_sha256") == src.get("text_sha256")})
        tp = REPO / src["text_path"] if src.get("text_path") else None
        if tp:
            remember_pin(source_pins, tp, file_pin(tp))
        if tp and source_pins[str(tp)]["sha256"] is not None:
            raw = tp.read_bytes()
            if hashlib.sha256(raw).hexdigest() != source_pins[str(tp)]["sha256"]:
                raise SnapshotChanged(f"own source changed during reading: {tp}; retry")
            text = normalized(raw)
            for w in TERM_WORDS:
                for m in re.finditer(w, text, re.I):
                    entry["own_text_signals"].append({"word": m.group(0), "char": m.start(), "context": snippet(text, m.start(), m.end(), 70)})
        out[iid] = entry
        pats[iid] = (number_pattern(iid), code_name(reg.get("title") or ""), str(tp.resolve()) if tp else None)
        detail_members[iid] = {"number_citations": [], "code_mentions": [],
                               "number_matching_files": 0, "code_matching_files": 0,
                               "candidate_own_text_exclusions": 0}
    snapshot = Snapshot(REPO, held_texts)
    by_number = {}
    for iid in ids:
        match = re.match(r"EO:(\d+)([A-Z]?)$", iid)
        if match:
            by_number.setdefault(match[1], []).append(iid)
    codes = {iid: ("code of fair competition for the " + code).lower()
             for iid, (_, code, _) in pats.items() if code}
    t = time.perf_counter()
    candidate_files = 0
    for record in snapshot.candidates(by_number, bool(codes)):
        candidate_files += 1
        text = snapshot.read_source(record)
        lower = text.lower() if record["code_prefix"] and codes else None
        rel = record["path"]
        resolved = str((REPO / rel).resolve())
        numeric_ids = {iid for n in record["digits"] for iid in by_number.get(n, ())}
        for iid in ids:
            np_, code, own = pats[iid]
            if own and resolved == own:
                detail_members[iid]["candidate_own_text_exclusions"] += 1
                continue
            details = detail_members[iid]
            if np_ is not None and iid in numeric_ids:
                m = np_.search(text)
                if m:
                    details["number_matching_files"] += 1
                    if len(out[iid]["number_citations"]) < 40:
                        out[iid]["number_citations"].append({"file": rel, "context": snippet(text, m.start(), m.end())})
                        details["number_citations"].append(source_hit(record, text, m.start(), m.end()))
            if code and lower is not None:
                i = lower.find(codes[iid])
                if i >= 0:
                    details["code_matching_files"] += 1
                    if len(out[iid]["code_mentions"]) < 60:
                        # Preserve legacy lowercase offsets and short context endpoint exactly.
                        out[iid]["code_mentions"].append({"file": rel, "context": snippet(text, i, i + len(code))})
                        a, b = original_span(text, lower, i, i + len(codes[iid]))
                        details["code_mentions"].append(source_hit(record, text, a, b))
    search_seconds = time.perf_counter() - t
    snapshot.verify()
    if input_manifest(packet_dir) != inputs or any(file_pin(Path(path)) != pin for path, pin in source_pins.items()):
        raise SnapshotChanged("lookup resource or own/page-check text changed during search; retry")
    for details in detail_members.values():
        details["number_limit"] = 40
        details["code_limit"] = 60
        details["number_truncated"] = details["number_matching_files"] > len(details["number_citations"])
        details["code_truncated"] = details["code_matching_files"] > len(details["code_mentions"])
    for iid, details in detail_members.items():
        details["number_regex"] = pats[iid][0].pattern if pats[iid][0] else None
        details["code_literal_lower"] = codes.get(iid)
        details["match_semantics"] = "First exact match per other held file, in held_texts order; counts are matching files before the legacy 40/60 limits. Own exclusions count candidate files only."
    LAST_DETAILS = {"schema": "cruden-lookup-details/v1", "notice": "Retrieval leads only; no identity, legal effect, status, original-authentication or completeness determination.",
                    "corpus": snapshot.details(), "members": detail_members,
                    "candidate_files": candidate_files, "member_load_seconds": member_load_seconds,
                    "search_seconds": search_seconds, "total_seconds": time.perf_counter() - started,
                    "timing_scope": "Retrieval and verification before output serialization/writes; outer process wall time includes output.",
                    "offsets": "Zero-based, half-open Unicode character offsets in UTF-8 replacement-decoded universal-newline source text. Raw-byte SHA256 binds the held file; offsets are not raw-byte offsets.",
                    "inputs": inputs, "own_and_page_texts": list(source_pins.values())}
    folder = Path(packet_dir)
    (folder / "LOOKUPS.json").write_text(json.dumps({"schema": "cruden-lookups/v1", "notice": __doc__.split("\n\n")[-1].strip(),
                                                     "members": out}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    md = ["# Lookups for this packet (Cruden)", "", "Leads only; read the sources and judge. Full detail: LOOKUPS.json.", ""]
    for iid, e in out.items():
        r = e["register"]
        md += [f"## {iid}: {r.get('title')}", "",
               f"- Register: {r.get('date')}; {r.get('president')}; best held {r.get('best_held')}; status {r.get('provisional_status')}",
               "- WPA: " + ("; ".join(f"{w['year']} {w['month_day']} p.{w['page']}: {w['text'][:160]}" for w in e["wpa"]) or "none")]
        for p in e["page_check"] or [{"record": "none found for the original's sha256"}]:
            md.append("- Page check: " + ", ".join(f"{k}={v}" for k, v in p.items()))
        md.append("- Own-text signals: " + ("; ".join(f"'{s['word']}'@{s['char']}: …{s['context']}…" for s in e["own_text_signals"][:12]) or "none"))
        md.append(f"- Number citations in other held texts ({len(e['number_citations'])}):")
        md += [f"  - {c['file']}: …{c['context']}…" for c in e["number_citations"][:15]]
        md.append(f"- Code-name mentions in other held texts ({len(e['code_mentions'])}):")
        md += [f"  - {c['file']}: …{c['context']}…" for c in e["code_mentions"][:20]]
        md.append("")
    (folder / "LOOKUPS.md").write_text("\n".join(md), encoding="utf-8")
    (folder / "LOOKUPS.details.json").write_text(json.dumps(LAST_DETAILS, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(out)} members -> {folder / 'LOOKUPS.md'}")


def source_hit(record, text, start, end):
    return {"file": record["path"], "raw_sha256": record["sha256"], "raw_bytes": record["bytes"],
            "full_text_path": str(REPO / record["path"]), "char_start": start, "char_end": end,
            "match": text[start:end], "context": snippet(text, start, end)}


def input_manifest(packet_dir):
    files = [REPO / "jobs/domesday-register/output/REGISTER.csv",
             REPO / "jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv"]
    files += [REPO / "jobs/app-executive-orders/output" / name for name in ("MIRROR_DOCUMENTS.jsonl", "DOCUMENTS.jsonl")]
    packet = Path(packet_dir) / "PACKET.json"
    files.append(packet)
    return [file_pin(p) for p in files]


def file_pin(path):
    if not path.is_file():
        return {"path": str(path), "bytes": None, "sha256": None}
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def remember_pin(pins, path, pin):
    key = str(path)
    if key in pins and pins[key] != pin:
        raise SnapshotChanged(f"referenced source changed between reads: {path}; retry")
    pins[key] = pin


def search(patterns):
    regs = [re.compile(p, re.I) for p in patterns]
    for f in held_texts():
        text = f.read_text(encoding="utf-8", errors="replace")
        for r in regs:
            for m in list(r.finditer(text))[:3]:
                print(f"{f.relative_to(REPO).as_posix()}@{m.start()}: …{snippet(text, m.start(), m.end(), 80)}…")


def source_search(kind, queries, write=None):
    """General, unranked source access with the same held-text scope as lookups."""
    started = time.perf_counter()
    queries = list(dict.fromkeys(queries))
    regs = {q: number_pattern(q) for q in queries} if kind == "number" else {}
    if kind == "number" and any(r is None for r in regs.values()):
        raise ValueError("number queries must be exact EO:<digits>[A-Z] identifiers")
    if any(not q for q in queries):
        raise ValueError("empty literal query")
    snapshot = Snapshot(REPO, held_texts)
    numbers = [re.match(r"EO:(\d+)([A-Z]?)$", q).group(1) for q in queries] if kind == "number" else []
    records = snapshot.candidates(numbers) if kind == "number" else (r for r in snapshot.sources if r["sha256"] is not None)
    out = {q: {"hits": [], "matching_files": 0, "matches": 0, "per_file_limit": 3, "truncated": False} for q in queries}
    for q in queries:
        out[q]["number_regex" if kind == "number" else "literal_lower"] = regs[q].pattern if kind == "number" else q.lower()
    t = time.perf_counter()
    for record in records:
        text = snapshot.read_source(record)
        lower = text.lower() if kind == "literal" else None
        for q in queries:
            if kind == "number":
                spans = (m.span() for m in regs[q].finditer(text))
            else:
                needle = q.lower()
                def literal_spans():
                    position = 0
                    while True:
                        position = lower.find(needle, position)
                        if position < 0:
                            return
                        yield original_span(text, lower, position, position + len(needle))
                        position += len(needle)
                spans = literal_spans()
            count = 0
            for a, b in spans:
                count += 1
                if count <= 3:
                    out[q]["hits"].append(source_hit(record, text, a, b))
            if count:
                out[q]["matching_files"] += 1
                out[q]["matches"] += count
                out[q]["truncated"] |= count > 3
    search_seconds = time.perf_counter() - t
    snapshot.verify()
    result = {"schema": "cruden-source-search/v1", "kind": kind,
              "notice": "Literal retrieval leads only; read the complete held sources. No identity or legal judgment.",
              "queries": out, "corpus": snapshot.details(), "search_seconds": search_seconds,
              "total_seconds": time.perf_counter() - started,
              "timing_scope": "Retrieval and verification before output serialization/writes; outer process wall time includes output.",
              "offsets": "Zero-based half-open normalized-text Unicode character offsets, not raw-byte offsets."}
    serialized = json.dumps(result, ensure_ascii=False, indent=1) + "\n"
    if write is None:
        print(serialized, end="")
    else:
        path = Path(write).resolve()
        path.write_bytes(serialized.encode("utf-8"))
        coverage = snapshot.coverage
        summary = {"result": str(path), "sha256": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
                   "bytes": len(serialized.encode("utf-8")), "snapshot_sha256": snapshot.snapshot_sha256,
                   "queries": {q: {"matches": value["matches"], "matching_files": value["matching_files"],
                                    "returned_hits": len(value["hits"]), "truncated": value["truncated"]} for q, value in out.items()},
                   "coverage": {key: coverage[key] for key in ("discovered_count", "readable_count", "source_bytes")},
                   "skipped": {key: len(coverage[key]) for key in ("unreadable_sources", "directory_errors", "tracked_not_discovered")}}
        print(json.dumps(summary, ensure_ascii=False))
    return result


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "lookups":
        lookups(sys.argv[2])
    elif len(sys.argv) >= 3 and sys.argv[1] == "search":
        search(sys.argv[2:])
    elif len(sys.argv) >= 3 and sys.argv[1] in ("number", "literal"):
        args = sys.argv[2:]
        destination = None
        if "--write" in args:
            index = args.index("--write")
            if index + 1 >= len(args):
                raise ValueError("--write requires a result path")
            destination = args[index + 1]
            del args[index:index + 2]
        if not args:
            raise ValueError("at least one query is required")
        source_search(sys.argv[1], args, destination)
    else:
        print(__doc__)

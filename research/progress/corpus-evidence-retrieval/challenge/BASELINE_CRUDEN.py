"""Cruden: one-pass lookups for a claim-kit packet's members, so producers stop rebuilding search scripts.

Named for Alexander Cruden, whose 1737 concordance listed every occurrence of every word of the Bible.

    python3 -I cruden.py lookups PACKET_DIR      # writes PACKET_DIR/LOOKUPS.md and LOOKUPS.json
    python3 -I cruden.py search REGEX [REGEX ...] # case-insensitive search of every held order text

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
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
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
    dossiers = load_members(packet_dir)
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
            cap = (r.get("capture") or {}).get("archive") if kind == "mirror" else None
            entry["page_check"].append({"record": kind, "capture_archive": cap, "heading": r.get("heading"), "date": r.get("date"),
                                        "heading_names_number": bool(re.search(r"\b" + num + r"(?:-?[A-Z])?\b", r.get("heading") or "")),
                                        "text_sha256_equal": held.is_file() and sha(held) == r.get("text_sha256") == src.get("text_sha256")})
        tp = REPO / src["text_path"] if src.get("text_path") else None
        if tp and tp.is_file():
            text = tp.read_text(encoding="utf-8", errors="replace")
            for w in TERM_WORDS:
                for m in re.finditer(w, text, re.I):
                    entry["own_text_signals"].append({"word": m.group(0), "char": m.start(), "context": snippet(text, m.start(), m.end(), 70)})
        out[iid] = entry
        pats[iid] = (number_pattern(iid), code_name(reg.get("title") or ""), str(tp.resolve()) if tp else None)
    for f in held_texts():
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = f.relative_to(REPO).as_posix()
        for iid, (np_, code, own) in pats.items():
            if own and str(f.resolve()) == own:
                continue
            if np_ is not None:
                m = np_.search(text)
                if m and len(out[iid]["number_citations"]) < 40:
                    out[iid]["number_citations"].append({"file": rel, "context": snippet(text, m.start(), m.end())})
            if code:
                i = text.lower().find(("code of fair competition for the " + code).lower())
                if i >= 0 and len(out[iid]["code_mentions"]) < 60:
                    out[iid]["code_mentions"].append({"file": rel, "context": snippet(text, i, i + len(code))})
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
    print(f"{len(out)} members -> {folder / 'LOOKUPS.md'}")


def search(patterns):
    regs = [re.compile(p, re.I) for p in patterns]
    for f in held_texts():
        text = f.read_text(encoding="utf-8", errors="replace")
        for r in regs:
            for m in list(r.finditer(text))[:3]:
                print(f"{f.relative_to(REPO).as_posix()}@{m.start()}: …{snippet(text, m.start(), m.end(), 80)}…")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "lookups":
        lookups(sys.argv[2])
    elif len(sys.argv) >= 3 and sys.argv[1] == "search":
        search(sys.argv[2:])
    else:
        print(__doc__)

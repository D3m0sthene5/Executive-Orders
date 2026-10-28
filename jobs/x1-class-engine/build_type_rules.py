"""Write the X1 type rule book to research/readiness/type-rules/ (run by an agent, not the job).

python jobs/x1-class-engine/build_type_rules.py [--repo .]

Each rule takes its legal pattern from type_rules_spec.py and an exemplar: a
high-confidence order of the type with a held text whose machine clause span
re-reads exactly from its file. The quoted clause is copied from that file at
those offsets, with the text's SHA-256, so the job can re-verify it. A rule
file changed after its independent review no longer matches the frozen hash in
the review and is reported as unreviewed by the job.
"""
import argparse, csv, hashlib, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cluster, classify, taxonomy as tx, type_rules_spec as spec  # noqa: E402

GRADE_PREF = ["government_printed_copy", "machine_read_government_printed_copy", "official_compilation_high",
              "mirror_transcription", "mirror_transcription_app"]
QUOTE_MAX = 700
OPERATIVE = re.compile(r"\b(hereby|it is ordered|is authorized|are authorized|is directed|are directed|may be|is withdrawn|are withdrawn|is reserved|are reserved|is exempted|is approved|are approved|is excepted|is suspended|shall be)\b", re.I)


def operative_quote(raw, c):
    """From the start of the first sentence with operative words, up to QUOTE_MAX, inside the clause."""
    seg = raw[c["char_start"]:c["char_end"]]
    m = OPERATIVE.search(seg)
    if not m:
        return None
    k = max(seg.rfind(". ", 0, m.start()), seg.rfind(".\n", 0, m.start()), seg.rfind(":\n", 0, m.start()))
    s = c["char_start"] + (k + 2 if k >= 0 else 0)
    while s < c["char_end"] and raw[s].isspace():
        s += 1
    return s, raw[s:min(c["char_end"], s + QUOTE_MAX)]


def rule_lifecycle(r):
    return {"own_terms_expiry": "spent", "exhausted_on_performance": "spent",
            "exhausted_on_performance_or_own_terms": "spent",
            "own_terms_expiry_or_separation": "spent", "event_swept": "swept"}.get(r["mechanism"], "land")


def held_texts(repo, iid):
    """All held text records for one order, from claim-kit's text index."""
    out = []
    for line in open(repo / "jobs/claim-kit/output/TEXT_REPRESENTATIONS.jsonl"):
        if f'"{iid}"' not in line:
            continue
        x = json.loads(line)
        if x.get("instrument_id") == iid and x.get("text_path") and (repo / x["text_path"]).exists():
            out.append(x)
    return out


def named_exemplar(repo, spec):
    """Quote each (start, end) part exactly from a held text of the named order."""
    for x in held_texts(repo, spec["id"]):
        raw = (repo / x["text_path"]).read_text(encoding="utf-8", errors="replace")
        parts, spans = [], []
        for a, b in spec["parts"]:
            i = raw.find(a)
            j = raw.find(b, i) if i >= 0 else -1
            if i < 0 or j < 0:
                break
            parts.append(raw[i:j + len(b)])
            spans.append([i, j + len(b)])
        else:
            src = x.get("source") or {}
            return parts, spans, x, src, raw
    raise SystemExit(f"exemplar quote not found for {spec['id']}: {spec['parts'][0][0][:40]}")


def revise(repo, out, rev):
    """Round-2 changes required by the independent review."""
    for k in ("ending_pattern", "effective_date_basis", "mechanism"):
        if k in rev:
            out[k] = rev[k]
    if "savings" in rev:
        out["exceptions_savings"]["assessment"] = rev["savings"]
    if "outliers_replace" in rev:
        out["outlier_conditions"] = spec.COMMON_OUTLIERS + rev["outliers_replace"]
    out["outlier_conditions"] += rev.get("outliers_add", [])
    if "required_evidence_replace" in rev:
        out["required_evidence"] = list(rev["required_evidence_replace"])
    out["required_evidence"] += rev.get("required_evidence_add", [])
    if "note" in rev:
        out["note"] = rev["note"]
    exs = [e for e in (rev.get("exemplar"), rev.get("exemplar2")) if e]
    if exs:
        out["quoted_parts"], out["additional_exemplars"] = [], []
        for n, e in enumerate(exs):
            parts, spans, x, src, raw = named_exemplar(repo, e)
            source = {"url": src.get("url"), "sha256": src.get("sha256"), "page": src.get("page_or_item"),
                      "text_path": x["text_path"], "text_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                      "original_custody_verified": False,
                      "custody_limit": "Exemplar text is a held copy graded " + str(x.get("grade")) +
                                       "; it illustrates the type's wording and is not an authenticated original."}
            ex = {"instrument_id": e["id"], "spans": spans, "text_grade": x.get("grade"), "acceptable_as_original": False}
            if n == 0:
                out["quoted_clause"], out["quoted_parts"], out["exemplar"], out["source"] = parts[0], parts, ex, source
            else:
                out["additional_exemplars"].append(dict(ex, quoted_parts=parts, source=source))
    out["review_round"] = rev.get("round", 2)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(HERE.parents[1]))
    ap.add_argument("--only", nargs="*", help="rebuild only these rule ids (keeps reviewed files frozen)")
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    types = {r["instrument_id"]: r for r in classify.classify(repo, HERE)}
    docs = cluster.load_documents(repo, set(types))
    outdir = repo / "research/readiness/type-rules"
    outdir.mkdir(parents=True, exist_ok=True)
    for rule_id, r in spec.RULES.items():
        if a.only and rule_id not in a.only:
            continue
        if rule_id in getattr(spec, "FROZEN", set()):
            print(rule_id, "frozen: approved in review, left unchanged")
            continue
        cands = []
        for iid, t in types.items():
            d = docs.get(iid)
            if t["type"] in r["types"] and t["confidence"] == "high" and d and d["spans_ok"] and d["clauses"]:
                g = t["text_grade"].replace("_needs_page_check", "")
                rank = GRADE_PREF.index(g) if g in GRADE_PREF else len(GRADE_PREF)
                q = next(((c, operative_quote(d["raw"], c)) for c in d["clauses"] if operative_quote(d["raw"], c)), None)
                if not q or t["type"] not in {h[0] for h in tx.matches(q[1][1], t["year"] or None)}:
                    continue   # the quote itself must show the type (compiled texts can run into a neighbour)
                first = next(t2[4][0] for t2 in tx.TYPES if t2[0] == t["type"])
                specific = 0 if t["evidence_pattern"] == first and t["sources_agreeing"].count("|") >= 1 else 1
                if rule_lifecycle(r) == "land" and re.search(r"revok|restor|rescind", q[1][1], re.I):
                    specific += 2   # prefer an order that creates the reserve over one that ends another
                cands.append((specific, rank, abs(len(q[1][1]) - 400), iid, q))
        exemplar = None
        if cands:
            _, _, _, iid, (c0, (qs, quote)) = min(cands, key=lambda x: x[:4])
            d = docs[iid]
            src = d["source"]
            exemplar = {"instrument_id": iid, "scope_id": c0["scope_id"], "char_start": qs,
                        "char_end": qs + len(quote), "text_grade": types[iid]["text_grade"],
                        "acceptable_as_original": False,
                        "wpa_summary": types[iid]["wpa_summary"][:300]}
            source = {"url": src.get("url"), "sha256": src.get("sha256"), "page": src.get("page_or_item"),
                      "text_path": d["path"], "text_sha256": d["text_sha256"],
                      "original_custody_verified": False,
                      "custody_limit": "Exemplar text is a held copy graded " + types[iid]["text_grade"] +
                                       "; it illustrates the type's wording and is not an authenticated original."}
        else:
            quote, source = "", {"original_custody_verified": False,
                                 "custody_limit": "No high-confidence member of this type has a held text with verified clause spans."}
        out = {
            "schema": "eo-type-rule/v1",
            "rule_id": rule_id,
            "title": r["title"],
            "types": r["types"],
            "lifecycle_class": rule_lifecycle(r),
            "mechanism": r["mechanism"],
            "ending_pattern": r["ending_pattern"],
            "effective_date_basis": r["effective_date_basis"],
            "exceptions_savings": {"assessment": r["savings"], "leads": [], "reviewed": False},
            "required_evidence": r["required_evidence"],
            "outlier_conditions": spec.COMMON_OUTLIERS + r["outliers"],
            "quoted_clause": quote,
            "quoted_parts": [quote] if quote else [],
            "exemplar": exemplar,
            "source": source,
            "scope": {"kind": "type_membership", "membership": "jobs/x1-class-engine/output/TYPES.csv",
                      "min_confidence": "medium",
                      "note": "Membership is a machine lead; each order is decided by an agent, row by row."},
            "legal_effect": "Research pattern only. A type rule never fills a judgment field, establishes an end, a date, "
                            "a status or savings for any order, and never substitutes for reading the order's own text.",
            "review_state": "drafted_awaiting_independent_review",
            "target_scope_reviewed": [],
        }
        rev = getattr(spec, "REVISIONS", {}).get(rule_id)
        if rev == "WITHDRAWN":
            (outdir / f"{rule_id}.json").unlink(missing_ok=True)
            print(rule_id, "withdrawn (no held exemplar)")
            continue
        if rev:
            out = revise(repo, out, rev)
        p = outdir / f"{rule_id}.json"
        p.write_text(json.dumps(out, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        print(rule_id, exemplar["instrument_id"] if exemplar else "-", hashlib.sha256(p.read_bytes()).hexdigest()[:12])


if __name__ == "__main__":
    main()

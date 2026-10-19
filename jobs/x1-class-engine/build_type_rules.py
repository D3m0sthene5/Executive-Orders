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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(HERE.parents[1]))
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    types = {r["instrument_id"]: r for r in classify.classify(repo, HERE)}
    docs = cluster.load_documents(repo, set(types))
    outdir = repo / "research/readiness/type-rules"
    outdir.mkdir(parents=True, exist_ok=True)
    for rule_id, r in spec.RULES.items():
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
        p = outdir / f"{rule_id}.json"
        p.write_text(json.dumps(out, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        print(rule_id, exemplar["instrument_id"] if exemplar else "-", hashlib.sha256(p.read_bytes()).hexdigest()[:12])


if __name__ == "__main__":
    main()

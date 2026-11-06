"""Clerical copy of H2 review files with the run-condition attestation fields kit.py complete requires (coordinator tool).
usage: python3 -I kit_fields.py REVIEW_DIR
For each BLIND_REVIEW_X.jsonl / AFTER_REVEAL_X.jsonl writes X.kit.jsonl beside it, adding only
independent: true, separate_context: true (each reviewer was a fresh headless session launched by the coordinator,
with no producer context), review_kind: independent_ai_source_review, scope: whole_case (the reviewer prompt asked
for a whole-case review of each lifecycle claim). Verdicts, defects, hashes and every other field are unchanged;
the reviewers' original files are kept. The H2 reviewer prompt omitted these fields from its format list (a
coordinator prompt defect), which is why this copy exists."""
import json, sys
from pathlib import Path
d = Path(sys.argv[1])
for p in sorted(d.glob("*.jsonl")):
    if p.name.endswith(".kit.jsonl"):
        continue
    rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    for r in rows:
        r.update({"independent": True, "separate_context": True, "review_kind": "independent_ai_source_review", "scope": "whole_case"})
    q = p.with_name(p.stem + ".kit.jsonl")
    q.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(q, len(rows))

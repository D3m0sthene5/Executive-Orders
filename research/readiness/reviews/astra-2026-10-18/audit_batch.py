"""Read-only batch accounting; publication remains a separate reviewed action."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
sys.path.insert(0, str(ROOT / "research/stage19/code"))
from claim_gate import claim_sha

IDS = [11022,11256,11782,11829,12075,12095,12159,12182,12262,12285,
       9452,9799,9837,9932,10249,10897,12145,10152,10168,10605,10681,10739,10892,10989,11120]


def audit():
    rows = []
    selections = json.loads((HERE / "BATCH1_SELECTION.json").read_text(encoding="utf-8"))
    for number in IDS:
        iid = f"EO:{number}"
        version = selections.get(iid, {}).get("version", "")
        path = HERE / "producer" / f"EO_{number}" / version / "claim.json"
        row = {"instrument_id":iid,"produced":path.exists(),"reviewed":False}
        if not path.exists():
            rows.append(row)
            continue
        raw = path.read_bytes()
        claim = json.loads(raw)
        assert claim["instrument_id"] == iid
        row.update(claim_sha256=claim_sha(claim), claim_file_sha256=hashlib.sha256(raw).hexdigest(),
                   gaps=len(claim.get("unresolved_material_gaps", [])), clauses=len(claim.get("operative_clauses", [])))
        review_path = HERE / "reviewer" / f"EO_{number}" / version / "REVIEW.json"
        if review_path.exists():
            review = json.loads(review_path.read_text(encoding="utf-8"))
            assert review["reviewer_role"] == "ai_review"
            assert review["instrument_id"] == iid
            assert review["claim_sha256"] == row["claim_sha256"], iid
            assert review["claim_file_sha256"] == row["claim_file_sha256"], iid
            row.update(reviewed=True, verdict=review["verdict"])
        rows.append(row)
    return rows


if __name__ == "__main__":
    rows = audit()
    print(json.dumps({"produced":sum(r["produced"] for r in rows),"reviewed":sum(r["reviewed"] for r in rows),
                     "rows":rows},indent=2))

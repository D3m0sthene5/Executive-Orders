"""Replaces each 7 MB cruden number-search file with its 'queries' summary inside the evidence export (coordinator tool)."""
import glob, json, os
for p in glob.glob("/home/claude/executive-orders/research/herschel/H1/packets/*/evidence/EO_*.number_search.json"):
    q = json.load(open(p))
    e = p.replace(".number_search.json", ".json")
    d = json.load(open(e))
    d["number_search_hits"] = {"queries": q.get("queries"), "corpus_snapshot_sha256": q.get("corpus", {}).get("snapshot_sha256"),
                               "scope": "all held jobs/*/output/texts except clause-drafts (cruden number)"}
    d["number_search"] = None
    d["held_texts_note"] = "held_texts lists only files named EO_N.txt; the selected working text is compiled_records.OVERLAY_INPUTS[0].selected.text_path and other representations are in TEXT_REPRESENTATIONS"
    open(e, "w").write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    os.remove(p)
print("ok")

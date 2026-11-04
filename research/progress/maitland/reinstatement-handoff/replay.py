"""Read-only held-text replay. Writes evidence beside this script, never job output."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    ex = load("replay_excavate", ROOT / "jobs/claim-kit/excavate.py")
    le = load("replay_later_events", ROOT / "jobs/later-events/later_events.py")
    result = {"base": "600ae3018f71025b3e53dc8538b8f92e6e159b76",
              "files": {}, "held_own_terms": {}, "actor_results": {}}
    for number in ("13933", "13934", "13978", "14029", "14189"):
        path = ROOT / f"jobs/fr-originals/data/full_run/texts/EO_{number}.txt"
        text = path.read_text(encoding="utf-8")
        result["files"][str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        if number in ("13933", "13934", "13978"):
            result["held_own_terms"][number] = ex.own_terms(
                "EO:" + number, text, {}, ex.segment("EO:" + number, text, {}))
        else:
            acts = ex.discover_mentions("EO:" + number, text, {})
            result["actor_results"][number] = {
                "acts": acts,
                "chains": {target: ex.chain("EO:" + target, acts)
                           for target in ("13933", "13934", "13978")},
                "later_events": le.scan_text_detail(text, "EO:" + number)}
            for act in acts:
                assert text[act["char_start"]:act["char_end"]] == act["provision_text"]
    before = json.loads((OUT / "before.json").read_text(encoding="utf-8"))
    assert result["files"] == before["files"], "held text bytes changed"
    assert result["held_own_terms"] == before["held_own_terms"], "target terms changed"
    actual = [(r["target_id"], r["verb"]) for r in result["actor_results"]["14189"]["acts"]]
    expected = [("EO:13933", "reinstate"), ("EO:13934", "reinstate"),
                ("EO:13934", "amend"), ("EO:13978", "reinstate")]
    assert actual == expected, actual
    assert all(a["effective_date"] is None for a in result["actor_results"]["14189"]["acts"])
    result["checks"] = {"held_source_hashes_unchanged": True, "own_terms_unchanged": True,
                        "exact_actor_spans": True, "eo14189_four_operations": True,
                        "eo14189_effective_dates_unasserted": True,
                        "legal_or_source_approval": False, "tokens": None,
                        "cache_parser_sha256": ex.segmentation_code_sha256()}
    result["code_sha256"] = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in ("jobs/claim-kit/excavate.py", "jobs/claim-kit/act_overrides.py",
                     "jobs/later-events/later_events.py")}
    (OUT / "after.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["checks"], sort_keys=True))


if __name__ == "__main__":
    main()

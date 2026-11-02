"""Bounded replay against four already-held EO12553 representations; no downloads."""
import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import types
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCRIPT = REPO / "research/excavator/claude-nira-sweep-2026-10-29/cruden.py"
BASE = "f07b023133640f288fd44c10c5176888c49f23e2"
relative = SCRIPT.relative_to(REPO).as_posix()
base_source = subprocess.check_output(["git", "-C", str(REPO), "show", f"{BASE}:{relative}"], text=True)
current_source = SCRIPT.read_text()
base_functions = {n.name: ast.dump(n) for n in ast.parse(base_source).body if isinstance(n, ast.FunctionDef)}
current_functions = {n.name: ast.dump(n) for n in ast.parse(current_source).body if isinstance(n, ast.FunctionDef)}
assert all(current_functions[name] == body for name, body in base_functions.items())

def load(name, source):
    module = types.ModuleType(name)
    module.__file__ = str(SCRIPT)
    exec(compile(source, str(SCRIPT), "exec"), module.__dict__)
    return module

base, current = load("baseline", base_source), load("patched", current_source)
old_example_raw = (HERE / "EXAMPLE.json").read_bytes()
old_example = json.loads(old_example_raw)
paths = [REPO / hit["file"] for hit in old_example["hits"]]
assert len(paths) == len(set(paths)) == 4
for path, old_hit in zip(paths, old_example["hits"]):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == old_hit["raw_sha256"]

with tempfile.TemporaryDirectory(prefix="cruden-held-replay-") as cache:
    with patch.dict("os.environ", {"CRUDEN_CACHE_DIR": cache}):
        # The normal functions are tested on exactly the same held paths as the
        # prior example; sparse omissions remain visible in the table receipt.
        for module in (base, current):
            module.held_texts = lambda: iter(paths)
        comparisons = {}
        for kind, queries in (("number", ["EO:9949", "EO:12553"]),
                              ("literal", ["transfer of personnel", "No. Subject"])):
            with contextlib.redirect_stdout(io.StringIO()):
                before = base.source_search(kind, queries)
                after = current.source_search(kind, queries)
            assert before["queries"] == after["queries"]
            assert before["corpus"]["sources"] == after["corpus"]["sources"]
            comparisons[kind] = {q: v["matches"] for q, v in after["queries"].items()}
        captures = []
        for module in (base, current):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                module.search([r"Executive\s+Orders?.*9949", r"9949"])
            captures.append(output.getvalue())
        assert captures[0] == captures[1]
        comparisons["search_stdout_sha256"] = hashlib.sha256(captures[0].encode()).hexdigest()
        started = time.perf_counter()
        with contextlib.redirect_stdout(io.StringIO()):
            table = current.table_number_search(["EO:9949"])
        wall = time.perf_counter() - started

query = table["queries"]["EO:9949"]
assert query["matches"] == query["matching_files"] == len(query["hits"]) == 4
for hit in query["hits"]:
    text = current.normalized((REPO / hit["file"]).read_bytes())
    for field, start, end in (("match", "char_start", "char_end"),
                              ("row", "row_char_start", "row_char_end"),
                              ("subject", "subject_char_start", "subject_char_end"),
                              ("header", "header_char_start", "header_char_end"),
                              ("introduction", "introduction_char_start", "introduction_char_end")):
        assert text[hit[start]:hit[end]] == hit[field]
    assert "transfer of personnel" in hit["subject"]
    assert hit["match"] == "9949"
    expected = (None, None) if "app-executive-orders" in hit["file"] else (10, "7238")
    assert (hit["pdf_page"], hit["printed_page"]) == expected
coverage = table["corpus"]["coverage"]
receipt = {
    "schema": "cruden-held-replay/v1", "base_commit": BASE,
    "notice": "Four already-held representations of one table; retrieval-only, not four independent legal sources or a full-corpus run.",
    "preserved_prior_example_sha256": hashlib.sha256(old_example_raw).hexdigest(),
    "preserved_packet_reference": {k: old_example[k] for k in ("packet", "packet_sha256")},
    "packet_notice": "Inherited prior reference only; this replay does not load or validate the packet.",
    "legacy_function_ast_equal": sorted(base_functions), "normal_route_comparisons": comparisons,
    "query": "EO:9949", "matches": query["matches"], "matching_files": query["matching_files"],
    "hits": [{k: v for k, v in h.items() if k != "full_text_path"} for h in query["hits"]],
    "snapshot_sha256": table["corpus"]["snapshot_sha256"],
    "coverage": {k: coverage[k] for k in ("discovered_count", "readable_count", "source_bytes", "tracked_inventory") if k in coverage},
    "coverage_exception_counts": {k: len(coverage[k]) for k in ("tracked_not_discovered", "unreadable_sources", "directory_errors", "clause_drafts_excluded") if k in coverage},
    "timings": table["corpus"]["timings"], "table_total_before_serialization_seconds": table["total_seconds"],
    "table_call_with_stdout_serialization_wall_seconds": wall,
    "cost_limits": "One warm-cache local replay after baseline comparisons. No equivalent-task savings, model-token, cash, or full-session labor measurement.",
}
(HERE / "REPLAY.json").write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({"matches": query["matches"], "matching_files": query["matching_files"],
                  "legacy_function_ast_equal": len(base_functions), "normal_routes_equal": True,
                  "tracked_not_discovered": len(coverage["tracked_not_discovered"]),
                  "table_call_wall_seconds": wall}))

"""Offline regression: UTF-8 corpus and output under a Windows-style locale.

Run beside build_toolmap.py with: python -m unittest test_build_toolmap -v
TOOLMAP_TEST_SCRIPT may name the unpatched script to demonstrate the failure.
"""
import builtins
import contextlib
import csv
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(os.environ.get("TOOLMAP_TEST_SCRIPT", Path(__file__).with_name("build_toolmap.py")))
SPEC = importlib.util.spec_from_file_location("toolmap_under_test", SCRIPT)
toolmap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(toolmap)


class ToolMapEncodingTests(unittest.TestCase):
    def test_non_utf8_default_preserves_utf8_inputs_and_workload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def write(rel, text):
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
                return path

            # A right curly quotation mark includes byte 0x9d in UTF-8, which
            # is undefined in cp1252. This exercises decoding, not a mock
            # assertion about the implementation's encoding argument.
            annotation = "Reviewed “source”"
            fields = ["instrument_id", "blockers", "provisional_status", "ready_for_human_review"]
            fields += ["step_" + step for step, _ in toolmap.STEPS]
            row = ["EO:8000", "ONLY_COMPILED_TRANSCRIPTION_FOUND:" + annotation, "yes", "no"]
            row += ["open"] * len(toolmap.STEPS)
            tracker = write("tracker.csv", ",".join(fields) + "\n" + ",".join(row) + "\n")
            projection = write("projection.csv", "id,date_effective,notes\nEO:8000,1939," + annotation + "\n")
            write("jobs/claim-drafts/output/TODO_BY_ORDER.csv", "instrument_id,only_judgment_left,notes\nEO:8000,yes," + annotation + "\n")
            for rel, col in [
                ("clause-drafts/output/CLAUSES.csv", "instrument_id"),
                ("later-events/output/EDGES.csv", "target_id"),
                ("lambertini/output/SAVINGS_PREFILL.csv", "instrument_id"),
            ]:
                write("jobs/" + rel, col + ",notes\nEO:8000," + annotation + "\n")
            write("jobs/status-history/output/INDEX.json", json.dumps([{"instrument_id": "EO:8000", "history": [annotation], "events": []}], ensure_ascii=False))
            write("jobs/lambertini/output/COUNTEREVIDENCE_RECORDS.jsonl", json.dumps({"instrument_id": "EO:8000", "notes": annotation}, ensure_ascii=False) + "\n")
            write("jobs/lewis-originals/output/ROUTES.csv", "instrument_id,best_route,route_status,action_owner,notes\nEO:8000,volume,pending,agent_check," + annotation + "\n")
            write("jobs/claim-kit/output/FAMILIES.json", json.dumps([{"family_id": "own_term:report_deadline", "instrument_ids": ["EO:8000"], "notes": annotation}], ensure_ascii=False))

            real_open = builtins.open

            def cp1252_default(file, mode="r", *args, **kwargs):
                if "b" not in mode and len(args) < 2 and kwargs.get("encoding") is None:
                    kwargs["encoding"] = "cp1252"
                return real_open(file, mode, *args, **kwargs)

            with patch.multiple(toolmap, ROOT=root, JOBS=root / "jobs", HERE=root), patch.multiple(toolmap.brw, TRACKER=tracker, PROJ=projection):
                native_stdout = io.StringIO()
                with contextlib.redirect_stdout(native_stdout):
                    toolmap.main()
                expected = (root / "TOOLMAP_WORKLOAD.csv").read_bytes()
                locale_stdout = io.StringIO()
                with patch("builtins.open", cp1252_default), contextlib.redirect_stdout(locale_stdout):
                    toolmap.main()

            output = (root / "TOOLMAP_WORKLOAD.csv").read_bytes()
            self.assertEqual(output, expected)
            self.assertEqual(locale_stdout.getvalue(), native_stdout.getvalue())
            self.assertIn("clause-drafts → claim-kit", output.decode("utf-8"))
            rows = list(csv.DictReader(io.StringIO(output.decode("utf-8"))))
            self.assertEqual({r["step"] for r in rows}, {s for s, _ in toolmap.STEPS})
            self.assertEqual(sum(int(r["orders"]) for r in rows), 8)
            self.assertEqual(json.loads(locale_stdout.getvalue())["open_steps"], 8)


if __name__ == "__main__":
    unittest.main()

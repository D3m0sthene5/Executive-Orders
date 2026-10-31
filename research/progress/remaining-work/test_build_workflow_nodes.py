"""Tests for build_workflow_nodes.py: it writes the Workflow dataset only from clean metadata."""
import csv, json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def node(**kw):
    n = {"id": "a", "name": "A", "label": "A", "catalog_tool": "", "stage": "acquire", "order": 1, "kind": "software",
         "status_class": "current", "namesake_status": "none", "role": "Does a thing.", "feeds": []}
    n.update(kw)
    return n


class BuildTests(unittest.TestCase):
    def run_build(self, nodes, tools=("Lewis",)):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d)
        shutil.copy(HERE / "build_workflow_nodes.py", d)
        (d / "workflow").mkdir()
        (d / "snapshots" / "2026-10-30").mkdir(parents=True)
        with open(d / "snapshots" / "2026-10-30" / "TOOLS.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["tool", "namesake"]); [w.writerow([t, ""]) for t in tools]
        json.dump(nodes, open(d / "workflow" / "WORKFLOW_NODES.json", "w"))
        p = subprocess.run([sys.executable, "-X", "utf8", str(d / "build_workflow_nodes.py")], capture_output=True, text=True)
        return p, d / "workflow" / "WORKFLOW_NODES.csv"

    def test_writes_clean_metadata(self):
        p, out = self.run_build([node(), node(id="b", catalog_tool="Lewis", feeds=["a"], results=[{"date": "2026-10-29", "text": "x", "source": "jobs/x"}])])
        self.assertEqual(p.returncode, 0, p.stderr)
        rows = list(csv.DictReader(open(out, encoding="utf-8")))
        self.assertEqual([r["id"] for r in rows], ["a", "b"])
        self.assertEqual(json.loads(rows[1]["feeds_json"]), ["a"])
        self.assertEqual(json.loads(rows[1]["results_json"])[0]["date"], "2026-10-29")

    def test_refuses_unknown_catalog_row(self):
        p, out = self.run_build([node(catalog_tool="Not a tool")])
        self.assertNotEqual(p.returncode, 0); self.assertIn("not a TOOLS.csv row", p.stderr); self.assertFalse(out.exists())

    def test_refuses_dangling_feed_and_duplicate_id(self):
        p, _ = self.run_build([node(feeds=["ghost"]), node()])
        self.assertIn("feeds unknown id 'ghost'", p.stderr); self.assertIn("duplicate ids: a", p.stderr)

    def test_refuses_link_for_unrecorded_namesake(self):
        p, _ = self.run_build([node(namesake_status="none", wikipedia_url="https://en.wikipedia.org/wiki/X")])
        self.assertIn("no documented namesake but a Wikipedia link", p.stderr)

    def test_refuses_bad_stage_kind_and_non_wikipedia_link(self):
        p, _ = self.run_build([node(stage="launchpad", kind="robot", namesake_status="documented", wikipedia_url="https://example.com/x")])
        for s in ("stage='launchpad'", "kind='robot'", "wikipedia_url"):
            self.assertIn(s, p.stderr)

    def test_committed_metadata_builds_and_covers_the_catalog(self):
        nodes = json.load(open(HERE / "workflow" / "WORKFLOW_NODES.json", encoding="utf-8"))
        tools = {r["tool"] for r in csv.DictReader(open(HERE / "snapshots" / "2026-10-30" / "TOOLS.csv", encoding="utf-8"))}
        self.assertEqual({n["catalog_tool"] for n in nodes if n.get("catalog_tool")}, tools)
        ids = {n["id"] for n in nodes}
        self.assertIn("ready-for-human-review", ids); self.assertIn("human-certification", ids)
        for n in nodes:
            if n["kind"] == "campaign":
                self.assertEqual(n["status_class"], "historical", n["id"])
            if n["namesake_status"] == "inferred":
                self.assertTrue(n.get("namesake_note"), n["id"])


if __name__ == "__main__":
    unittest.main()

"""Tests for Ockham (.claude/hooks/ockham_lean_tree.py): which whole-tree listings Claude Code refuses."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.dont_write_bytecode = True
HOOK = Path(__file__).resolve().parents[2] / ".claude/hooks/ockham_lean_tree.py"
spec = importlib.util.spec_from_file_location("ockham", HOOK)
ockham = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ockham)

REFUSED = [
    "git ls-files", "git ls-files -t -z", "git --no-pager ls-files", "git -c core.quotepath=off ls-files -s",
    "git ls-files -- .", "echo hi;find .", "echo hi\nfind . -name x", "find -name '*.py'", "find . -type f",
    "ls -R", "ls -laR .", "tree", "Get-ChildItem -Recurse", "gci -r", "dir -rec", "FOO=1 git ls-files",
    "cd . && git ls-files",
]
ALLOWED = [
    "git ls-files -- jobs/kean", "git ls-files jobs/kean", "git ls-files | wc -l", "git ls-files | grep foo",
    "git ls-files | rg foo", "git ls-files -u", "git ls-files --others --exclude-standard", "git ls-files -m",
    "cd jobs/kean && git ls-files", "git -C jobs/kean ls-files", "git ls-files '*.py'",
    "find . -maxdepth 2 -name x", "find jobs/kean -name x", "ls -la jobs", "ls -R jobs/kean", "tree -L 2",
    "tree jobs/kean", "git status --short", "python -I jobs/kean/kean.py search tree", 'echo "unbalanced',
    "Get-ChildItem jobs -Recurse", "ls -r",
]


class Bash(unittest.TestCase):
    def test_whole_tree_listings_are_refused(self):
        for command in REFUSED:
            with self.subTest(command=command):
                self.assertEqual(ockham.bash_refusal(command), ockham.ADVICE)

    def test_named_folders_filters_and_small_modes_pass(self):
        for command in ALLOWED:
            with self.subTest(command=command):
                self.assertIsNone(ockham.bash_refusal(command))


class Glob(unittest.TestCase):
    ROOT = "C:\\work\\Executive-Orders"

    def check(self, pattern, path=None):
        tool_input = {"pattern": pattern} if path is None else {"pattern": pattern, "path": path}
        return ockham.glob_refusal(tool_input, self.ROOT)

    def test_root_wide_globs_are_refused(self):
        for pattern, path in [("**/*.json", None), ("**/*.py", "."), ("**/x", self.ROOT), ("**/x", self.ROOT + "\\"),
                              ("{jobs,research}/**/*.md", None), ("*/**/README.md", None)]:
            with self.subTest(pattern=pattern, path=path):
                self.assertEqual(self.check(pattern, path), ockham.ADVICE)

    def test_narrowed_globs_pass(self):
        for pattern, path in [("**/*.py", "jobs/kean"), ("jobs/*/README.md", None), ("jobs/kean/**/*.py", None),
                              ("*.md", None), ("**/*.py", self.ROOT + "\\jobs\\kean")]:
            with self.subTest(pattern=pattern, path=path):
                self.assertIsNone(self.check(pattern, path))


class Process(unittest.TestCase):
    def run_hook(self, stdin):
        return subprocess.run([sys.executable, "-I", str(HOOK)], input=stdin, capture_output=True, text=True)

    def test_exit_two_with_advice_and_fail_open_on_bad_input(self):
        refused = self.run_hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": "git ls-files"}}))
        self.assertEqual(refused.returncode, 2)
        self.assertIn("Ockham", refused.stderr)
        self.assertEqual(self.run_hook(json.dumps({"tool_name": "Read", "tool_input": {}})).returncode, 0)
        self.assertEqual(self.run_hook("not json").returncode, 0)
        self.assertEqual(self.run_hook("[1, 2]").returncode, 0)

    def test_settings_run_this_hook_for_shell_and_glob_tools(self):
        settings = json.loads((HOOK.parents[1] / "settings.json").read_text(encoding="utf-8"))
        entry = settings["hooks"]["PreToolUse"][0]
        self.assertEqual(set(entry["matcher"].split("|")), {"Bash", "PowerShell", "Glob"})
        self.assertIn(".claude/hooks/ockham_lean_tree.py", entry["hooks"][0]["command"])


if __name__ == "__main__":
    unittest.main()

"""Tests for Ariadne (ariadne.py): strace parsing, the learned closure and the silent-miss referee."""
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import ariadne  # noqa: E402

ROOT = "/w/repo"


def kinds(lines, cwd=ROOT):
    return [(k, p, ok, e) for k, p, ok, e in ariadne.events(lines, cwd)]


class Parsing(unittest.TestCase):
    def test_reads_probes_listings_and_absent_lookups(self):
        lines = [
            '100 openat(AT_FDCWD</w/repo>, "jobs/a/output/x.json", O_RDONLY|O_CLOEXEC) = 3</w/repo/jobs/a/output/x.json>',
            '100 newfstatat(AT_FDCWD</w/repo>, "research/r.csv", 0x7ffd, 0) = -1 ENOENT (No such file or directory)',
            '100 openat(AT_FDCWD</w/repo>, "jobs/b/output", O_RDONLY|O_NONBLOCK|O_CLOEXEC|O_DIRECTORY) = 4</w/repo/jobs/b/output>',
            '100 getdents64(4</w/repo/jobs/b/output>, 0x55 /* 3 entries */, 32768) = 80',
            '100 access("/w/repo/HANDOFF/KEAN.md", R_OK) = 0',
        ]
        self.assertEqual(kinds(lines), [
            ("read", "/w/repo/jobs/a/output/x.json", True, None),
            ("probe", "/w/repo/research/r.csv", False, "ENOENT"),
            ("probe", "/w/repo/jobs/b/output", True, None),
            ("list", "/w/repo/jobs/b/output", True, None),
            ("probe", "/w/repo/HANDOFF/KEAN.md", True, None),
        ])

    def test_writes_and_empty_paths_are_not_inputs(self):
        lines = [
            '100 openat(AT_FDCWD</w/repo>, "jobs/a/output/new.json", O_WRONLY|O_CREAT|O_TRUNC|O_CLOEXEC, 0666) = 3</w/repo/jobs/a/output/new.json>',
            '100 creat("/w/repo/x", 0644) = 3</w/repo/x>',
            '100 newfstatat(3</w/repo/jobs/a/job.py>, "", {st_mode=S_IFREG|0644, ...}, AT_EMPTY_PATH) = 0',
            '100 openat(AT_FDCWD</w/repo>, "jobs/a/state.json", O_RDWR|O_CREAT, 0644) = 3</w/repo/jobs/a/state.json>',
        ]
        self.assertEqual(kinds(lines), [("read", "/w/repo/jobs/a/state.json", True, None)])

    def test_relative_paths_follow_chdir_dirfds_and_forks_without_fd_decoding(self):
        lines = [
            '100 chdir("jobs/a") = 0',
            '100 clone(child_stack=NULL, flags=CLONE_CHILD_SETTID|SIGCHLD) = 200',
            '200 openat(AT_FDCWD, "data/in.csv", O_RDONLY) = 3</w/repo/jobs/a/data/in.csv>',
            '100 openat(5</w/repo/research>, "../HANDOFF/x.md", O_RDONLY) = 6</w/repo/HANDOFF/x.md>',
            '300 openat(AT_FDCWD, "orphan.txt", O_RDONLY) = 3</w/repo/orphan.txt>',
            '100 openat(7, "unknown", O_RDONLY) = 8',
        ]
        self.assertEqual([p for _, p, _, _ in kinds(lines)], [
            "/w/repo/jobs/a/data/in.csv", "/w/repo/HANDOFF/x.md", "/w/repo/orphan.txt"])

    def test_unfinished_calls_join_their_resumption(self):
        lines = [
            '100 openat(AT_FDCWD</w/repo>, "jobs/a/x.json", O_RDONLY <unfinished ...>',
            '200 getdents64(4</w/repo/jobs>, 0x55 /* 9 entries */, 32768) = 300',
            '100 <... openat resumed>) = 3</w/repo/jobs/a/x.json>',
        ]
        self.assertEqual(kinds(lines), [("list", "/w/repo/jobs", True, None),
                                        ("read", "/w/repo/jobs/a/x.json", True, None)])

    def test_escaped_names_decode_to_utf8(self):
        lines = ['100 openat(AT_FDCWD</w/repo>, "ProQuest/caf\\303\\251 \\"q\\".pdf", O_RDONLY) = 3</w/repo/x>',
                 '100 getdents64(4</w/repo/r\\303\\251sum\\303\\251>, 0x55 /* 2 entries */, 32768) = 48']
        self.assertEqual([p for _, p, _, _ in kinds(lines)], ['/w/repo/ProQuest/café "q".pdf', "/w/repo/résumé"])

    def test_noise_lines_are_ignored(self):
        lines = ["100 +++ exited with 0 +++", "100 --- SIGCHLD {si_signo=SIGCHLD} ---", "", "garbage ("]
        self.assertEqual(kinds(lines), [])

    def test_accesses_keep_repository_paths_and_drop_git_caches_and_own_output(self):
        lines = [
            '1 openat(AT_FDCWD</w/repo>, ".git/index", O_RDONLY) = 3</w/repo/.git/index>',
            '1 openat(AT_FDCWD</w/repo>, ".job-cache/runner-prior/t/a/x", O_RDONLY) = 3</x>',
            '1 openat(AT_FDCWD</w/repo>, "jobs/a/output/STATUS.json", O_RDONLY) = -1 ENOENT (No such file or directory)',
            '1 openat(AT_FDCWD</w/repo>, "jobs/b/output/STATUS.json", O_RDONLY) = 3</w/repo/jobs/b/output/STATUS.json>',
            '1 openat(AT_FDCWD</w/repo>, "/usr/lib/python3.12/os.py", O_RDONLY) = 3</usr/lib/python3.12/os.py>',
            '1 getdents64(4</w/repo>, 0x55 /* 9 entries */, 32768) = 300',
        ]
        found = ariadne.accesses(lines, ROOT, "jobs/a/output")
        self.assertEqual(found["read"], {"jobs/b/output/STATUS.json"})
        self.assertEqual(found["list"], {""})
        self.assertEqual(found["absent"], set())
        self.assertEqual(found["outside_repository_events"], 1)


def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


class Referee(unittest.TestCase):
    """A real sparse checkout: research/ is left out, jobs/ is present."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name, "repo")
        files = ["jobs/a/job.py", "jobs/a/output/STATUS.json", "jobs/b/output/one.json", "jobs/b/output/sub/two.json",
                 "research/r.csv", "research/deep/d.csv", "README.md"]
        for rel in files:
            Path(self.repo, rel).parent.mkdir(parents=True, exist_ok=True)
            Path(self.repo, rel).write_text(rel + "\n", encoding="utf-8")
        git(self.repo, "init", "-q")
        git(self.repo, "add", "-A")
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "t")
        git(self.repo, "sparse-checkout", "set", "--no-cone", "/*", "!/research/")

    def tearDown(self):
        self.tmp.cleanup()

    def judge(self, lines):
        found = ariadne.accesses(lines, ROOT, "jobs/a/output")
        return ariadne.judge(found, ariadne.index_flags(self.repo), self.repo, "jobs/a/output")

    def test_index_flags_see_the_sparse_checkout(self):
        flags = ariadne.index_flags(self.repo)
        self.assertEqual(flags["research/r.csv"], "S")
        self.assertEqual(flags["jobs/b/output/one.json"], "H")

    def test_closure_holds_reads_probes_and_direct_files_of_listings(self):
        r = ROOT
        closure, dirs, listed, misses = self.judge([
            f'1 openat(AT_FDCWD<{r}>, "jobs/a/job.py", O_RDONLY) = 3<{r}/jobs/a/job.py>',
            f'1 getdents64(4<{r}/jobs/b/output>, 0x55 /* 4 entries */, 32768) = 96',
            f'1 access("{r}/README.md", F_OK) = 0',
            f'1 openat(AT_FDCWD<{r}>, "untracked.tmp", O_RDONLY) = 3<{r}/untracked.tmp>',
        ])
        self.assertEqual(closure, {"jobs/a/job.py", "jobs/b/output/one.json", "README.md"})
        self.assertEqual(dirs, {"jobs/b/output/sub"})
        self.assertEqual(listed, {"jobs/b/output": 2})
        self.assertEqual(misses, [])

    def test_silent_misses_name_left_out_files_folders_and_incomplete_listings(self):
        r = ROOT
        closure, dirs, listed, misses = self.judge([
            f'1 newfstatat(AT_FDCWD<{r}>, "research/r.csv", 0x1, 0) = -1 ENOENT (No such file or directory)',
            f'1 openat(AT_FDCWD<{r}>, "research/deep", O_RDONLY|O_DIRECTORY) = -1 ENOENT (No such file or directory)',
            f'1 getdents64(4<{r}>, 0x55 /* 5 entries */, 32768) = 120',
            f'1 openat(AT_FDCWD<{r}>, "never/tracked.json", O_RDONLY) = -1 ENOENT (No such file or directory)',
        ])
        self.assertEqual([(m["kind"], m["path"]) for m in misses],
                         [("listing_incomplete", ""), ("folder_left_out", "research/deep"),
                          ("file_left_out", "research/r.csv")])
        self.assertEqual(misses[0]["examples"], ["research"])
        self.assertIn("research/r.csv", closure)
        self.assertIn("research/deep", dirs)

    def test_a_listing_of_a_present_folder_is_complete(self):
        r = ROOT
        _, _, _, misses = self.judge([f'1 getdents64(4<{r}/jobs>, 0x55 /* 4 entries */, 32768) = 96'])
        self.assertEqual(misses, [])

    def test_record_writes_the_record_and_never_changes_the_outcome(self):
        r = ROOT
        trace = Path(self.tmp.name, "a.strace")
        trace.write_text(f'1 openat(AT_FDCWD<{r}>, "research/r.csv", O_RDONLY) = -1 ENOENT (No such file)\n'
                         f'1 openat(AT_FDCWD<{r}>, "jobs/a/job.py", O_RDONLY) = 3<{r}/jobs/a/job.py>\n',
                         encoding="utf-8")
        real = ariadne.accesses
        with mock.patch.object(ariadne, "accesses", lambda lines, repo, own: real(lines, ROOT, own)):
            result = ariadne.finish("a", self.repo, trace, 0, 7.04, 6.0)
        self.assertFalse(trace.exists())
        written = json.loads(Path(self.repo, ariadne.RECORDS, "a.json").read_text(encoding="utf-8"))
        self.assertEqual(written, result)
        self.assertEqual(written["closure"], ["jobs/a/job.py", "research/r.csv"])
        self.assertEqual(written["silent_misses"], 1)
        self.assertEqual(written["job_seconds"], 7.0)
        self.assertEqual(ariadne.finish("a", self.repo, None, 0, 1, None), None)
        broken = Path(self.tmp.name, "b.strace")
        broken.write_text("1 openat(AT_FDCWD</x>, \"y\", O_RDONLY) = 3\n", encoding="utf-8")
        with mock.patch.object(ariadne, "index_flags", side_effect=RuntimeError("boom")):
            self.assertIsNone(ariadne.finish("b", self.repo, broken, 1, 1, None))
        self.assertFalse(broken.exists())


    def test_compressed_traces_are_read_and_a_cut_off_tail_is_marked(self):
        r = ROOT
        body = f'1 openat(AT_FDCWD<{r}>, "jobs/a/job.py", O_RDONLY) = 3<{r}/jobs/a/job.py>\n'.encode() * 2000
        whole, cut = Path(self.tmp.name, "w.strace.gz"), Path(self.tmp.name, "c.strace.gz")
        whole.write_bytes(gzip.compress(body))
        cut.write_bytes(gzip.compress(body)[:-40])
        state = {"truncated": False}
        self.assertEqual(sum(1 for _ in ariadne.trace_lines(whole, state)), 2000)
        self.assertFalse(state["truncated"])
        list(ariadne.trace_lines(cut, state))
        self.assertTrue(state["truncated"])

    def test_an_oversized_trace_is_not_parsed(self):
        trace = Path(self.tmp.name, "big.strace.gz")
        trace.write_bytes(b"x" * 3000)
        with mock.patch.dict(os.environ, {"ARIADNE_MAX_TRACE_MB": "0.001"}), \
                mock.patch.object(ariadne, "accesses", side_effect=AssertionError("parsed")):
            self.assertIsNone(ariadne.finish("a", self.repo, trace, 0, 1, None))
        self.assertFalse(trace.exists())


ON = {"ARIADNE_TRACE": "1", "ARIADNE_SKIP_JOBS": ""}


class Switches(unittest.TestCase):
    def setUp(self):
        ariadne._preflight.clear()

    def test_off_unless_asked_on_linux_with_strace(self):
        args, env = ["python", "job.py"], {"A": "1"}
        with mock.patch.dict(os.environ, {"ARIADNE_TRACE": ""}):
            self.assertEqual(ariadne.wrap(args, "a", "t", None, env), (args, env, None))
        with mock.patch.dict(os.environ, ON), mock.patch.object(sys, "platform", "win32"):
            self.assertEqual(ariadne.wrap(args, "a", "t", None, env), (args, env, None))
        with mock.patch.dict(os.environ, {**ON, "ARIADNE_SKIP_JOBS": "x a"}), mock.patch.object(sys, "platform", "linux"):
            self.assertEqual(ariadne.wrap(args, "a", "t", None, env), (args, env, None))

    def test_a_failed_preflight_or_missing_gzip_runs_jobs_untraced(self):
        with mock.patch.dict(os.environ, ON), mock.patch.object(sys, "platform", "linux"), \
                mock.patch.object(ariadne.shutil, "which", return_value="/usr/bin/strace-test"), \
                mock.patch.object(ariadne.subprocess, "run", return_value=mock.Mock(returncode=1)):
            self.assertIsNone(ariadne.wrap(["python", "job.py"], "a", "t")[2])
        with mock.patch.dict(os.environ, ON), mock.patch.object(sys, "platform", "linux"), \
                mock.patch.object(ariadne.shutil, "which", side_effect=lambda x: None if x == "gzip" else "/s"):
            self.assertIsNone(ariadne.wrap(["python", "job.py"], "a", "t")[2])

    def test_jobs_that_use_sudo_run_untraced(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp, "survey")
            (folder / "output").mkdir(parents=True)
            (folder / "job.py").write_text("print('no privilege')\n", encoding="utf-8")
            (folder / "output" / "log.sh").write_text("sudo was in an old log\n", encoding="utf-8")
            self.assertFalse(ariadne.privileged(folder))
            (folder / "job.sh").write_text("set -e\nsudo apt-get install -y tesseract-ocr\n", encoding="utf-8")
            self.assertTrue(ariadne.privileged(folder))
            with mock.patch.dict(os.environ, ON), mock.patch.object(sys, "platform", "linux"), \
                    mock.patch.object(ariadne.shutil, "which", side_effect=AssertionError("looked for strace")):
                self.assertIsNone(ariadne.wrap(["bash", "job.sh"], "survey", "t", folder, {})[2])

    def test_setup_errors_run_jobs_untraced(self):
        with mock.patch.dict(os.environ, ON), mock.patch.object(ariadne, "tracer", side_effect=OSError("disk full")):
            self.assertEqual(ariadne.wrap(["python", "job.py"], "a", "t", None, {"A": "1"}),
                             (["python", "job.py"], {"A": "1"}, None))

    def test_wrapped_command_streams_through_gzip_and_turns_off_detached_git(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.dict(os.environ, {**ON, "RUNNER_TEMP": tmp}), mock.patch.object(sys, "platform", "linux"), \
                mock.patch.object(ariadne.shutil, "which", return_value="/usr/bin/strace-ok"), \
                mock.patch.object(ariadne.subprocess, "run", return_value=mock.Mock(returncode=0)):
            env = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "user.name", "GIT_CONFIG_VALUE_0": "x"}
            command, traced_env, trace = ariadne.wrap(["python", "job.py"], "a", "t", None, env)
        # The runner waits on the supervisor, which runs strace over the child shim, which runs the job.
        self.assertEqual(command[:3], [sys.executable, "-I", str(SCRIPTS / "ariadne.py")])
        self.assertEqual(command[3], "supervise")
        strace_at = command.index("/usr/bin/strace-ok")
        self.assertEqual(command[strace_at - 1], "--")
        self.assertEqual(command[3 + 1], command[command.index("child") + 1])  # one shared exit-code file
        self.assertLess(strace_at, command.index("child"))
        self.assertEqual(command[-3:], ["--", "python", "job.py"])
        self.assertTrue(command[command.index("-o") + 1].startswith("|exec gzip -1 > "))
        self.assertIn(trace.name, command[command.index("-o") + 1])
        self.assertEqual(trace.name, "a.strace.gz")
        self.assertEqual(env["GIT_CONFIG_COUNT"], "1")  # the caller's environment is not modified
        self.assertEqual(traced_env["GIT_CONFIG_COUNT"], "3")
        self.assertEqual((traced_env["GIT_CONFIG_KEY_0"], traced_env["GIT_CONFIG_KEY_1"], traced_env["GIT_CONFIG_VALUE_1"],
                          traced_env["GIT_CONFIG_KEY_2"], traced_env["GIT_CONFIG_VALUE_2"]),
                         ("user.name", "gc.auto", "0", "maintenance.auto", "false"))


class Supervision(unittest.TestCase):
    """The runner waits on the job's own exit, never on processes it left behind."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.code = Path(self.tmp.name, "job.exit")

    def tearDown(self):
        self.tmp.cleanup()

    def test_child_records_the_jobs_exit_code(self):
        self.assertEqual(ariadne.child(self.code, [sys.executable, "-c", "raise SystemExit(3)"]), 3)
        self.assertEqual(self.code.read_text(encoding="utf-8"), "3")

    def test_supervisor_returns_the_jobs_code_through_the_child_shim(self):
        shim = [sys.executable, "-I", str(SCRIPTS / "ariadne.py"), "child", str(self.code), "--",
                sys.executable, "-c", "raise SystemExit(5)"]
        run = subprocess.run([sys.executable, "-I", str(SCRIPTS / "ariadne.py"), "supervise", str(self.code), "--",
                              *shim])
        self.assertEqual(run.returncode, 5)

    @unittest.skipUnless(os.name == "posix", "signals to the tracer are POSIX")
    def test_supervisor_stops_waiting_for_leftovers_after_the_job_exits(self):
        # A stand-in for strace that, like strace -f with a leftover tracee, keeps running after the job's
        # exit code is written, until it is told to detach (SIGINT).
        stand_in = ("import pathlib, signal, sys, time\n"
                    "signal.signal(signal.SIGINT, lambda *a: sys.exit(0))\n"
                    f"pathlib.Path({str(self.code)!r}).write_text('7')\n"
                    "time.sleep(60)\n")
        began = time.monotonic()
        self.assertEqual(ariadne.supervise(self.code, [sys.executable, "-c", stand_in], linger=0.5), 7)
        self.assertLess(time.monotonic() - began, 20)

    @unittest.skipUnless(os.name == "posix", "signal deaths are POSIX")
    def test_a_signal_death_is_reported_as_the_same_signal(self):
        shim = [sys.executable, "-I", str(SCRIPTS / "ariadne.py"), "child", str(self.code), "--",
                sys.executable, "-c", "import os, signal; os.kill(os.getpid(), signal.SIGTERM)"]
        run = subprocess.run([sys.executable, "-I", str(SCRIPTS / "ariadne.py"), "supervise", str(self.code), "--",
                              *shim])
        self.assertEqual(run.returncode, -15)

    def test_the_shims_own_read_is_not_a_job_read(self):
        lines = [f'1 openat(AT_FDCWD<{ROOT}>, ".github/scripts/ariadne.py", O_RDONLY) = 3<{ROOT}/x>',
                 f'1 openat(AT_FDCWD<{ROOT}>, ".github/scripts/run_jobs.py", O_RDONLY) = 3<{ROOT}/y>']
        self.assertEqual(ariadne.accesses(lines, ROOT, "jobs/a/output")["read"], {".github/scripts/run_jobs.py"})


if __name__ == "__main__":
    unittest.main()

"""Read files from one pinned commit of the repository without checking them out.

Every input of the thesis measure is read through this module, so a rerun on the same commit gives the same
bytes. Nothing here writes to the repository.
"""

import hashlib
import subprocess


class Git:
    def __init__(self, repo, rev="origin/main"):
        self.repo = repo
        self.commit = subprocess.run(["git", "-C", repo, "rev-parse", rev], capture_output=True, text=True,
                                     check=True).stdout.strip()
        self._proc = None
        self._cache_sha = {}

    def _batch(self):
        if self._proc is None:
            self._proc = subprocess.Popen(["git", "-C", self.repo, "cat-file", "--batch"], stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE)
        return self._proc

    def read(self, path):
        """Bytes of path at the pinned commit, or None when the path is not in that tree."""
        p = self._batch()
        p.stdin.write(f"{self.commit}:{path}\n".encode("utf-8"))
        p.stdin.flush()
        header = p.stdout.readline().decode("utf-8", "replace").rstrip("\n")
        if header.endswith(" missing") or header.endswith(" ambiguous"):
            return None
        parts = header.split()
        size = int(parts[2])
        data = b""
        while len(data) < size:
            data += p.stdout.read(size - len(data))
        p.stdout.read(1)  # trailing newline
        return data

    def text(self, path):
        b = self.read(path)
        return None if b is None else b.decode("utf-8", "replace")

    def sha256(self, path):
        """SHA-256 of the committed bytes of path, or None when absent."""
        if path not in self._cache_sha:
            b = self.read(path)
            self._cache_sha[path] = None if b is None else hashlib.sha256(b).hexdigest()
        return self._cache_sha[path]

    def ls(self, path):
        out = subprocess.run(["git", "-C", self.repo, "ls-tree", "-r", "--name-only", self.commit, path],
                             capture_output=True, text=True, encoding="utf-8", check=True).stdout
        return [x for x in out.split("\n") if x]

    def dirs(self, path):
        """Names of the immediate subfolders of path."""
        out = subprocess.run(["git", "-C", self.repo, "ls-tree", self.commit, path.rstrip("/") + "/"],
                             capture_output=True, text=True, encoding="utf-8", check=True).stdout
        names = []
        for line in out.split("\n"):
            meta, _, name = line.partition("\t")
            if meta.split()[1:2] == ["tree"]:
                names.append(name.rsplit("/", 1)[-1])
        return sorted(names)

    def close(self):
        if self._proc is not None:
            self._proc.stdin.close()
            self._proc.wait()
            self._proc = None

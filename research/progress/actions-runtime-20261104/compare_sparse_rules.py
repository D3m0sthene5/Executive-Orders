"""Compare Git's selected paths and matcher time. Run at the repository root."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(".github/scripts").resolve()))
import materialize_job_inputs as materializer

names = sys.argv[1:] or "example-hello astra-source-retention cotton-capture-custody claim-checker norton claim-kit geddes hamilton-token-audit kean x1-class-engine".split()
entries, _, by_job = materializer.input_closure(names)
raw = sorted(set().union(*by_job.values()))
tracked = subprocess.check_output(["git", "ls-tree", "-rz", "--name-only", "HEAD"])
bootstrap = "/*\n!/*/\n/.github/**\n/HANDOFF/**\n/jobs/**\n!/jobs/*/output/**\n"
previous = None
for rules in (raw, materializer.compact_patterns(raw)):
    with tempfile.TemporaryDirectory() as temporary:
        rule_file = Path(temporary) / "rules"
        rule_file.write_bytes((bootstrap + "\n".join(rules) + "\n").encode())
        start = time.monotonic()
        selected = subprocess.run(["git", "sparse-checkout", "check-rules",
                                   "--no-cone", "--rules-file", str(rule_file), "-z"],
                                  input=tracked, capture_output=True, check=True).stdout
        elapsed = time.monotonic() - start
        if previous is not None and selected != previous:
            raise SystemExit("Sparse selectors differ")
        print(json.dumps({"declared_inputs": len(entries), "positive_rules": len(rules),
                          "matched_paths": selected.count(b"\0"), "selected_sha256": hashlib.sha256(selected).hexdigest(),
                          "matcher_wall_seconds": elapsed}))
        previous = selected

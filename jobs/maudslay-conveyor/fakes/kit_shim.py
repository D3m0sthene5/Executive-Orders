"""Run the REAL jobs/claim-kit/kit.py with only the readiness-tracker replay stubbed, for the integration test.

    python kit_shim.py KIT_HOME --repo FIXTURE_REPO SUBCOMMAND ...

The kit's own completion tests stub run_tracker the same way (jobs/claim-kit/test_completion.py), because the
synthetic BuildIntegrationTests corpus has no tracker inputs. Everything else (next, prepare, dispatch-check, apply,
batch-check with the actual claim checker, complete) is the committed kit code."""
import sys
from pathlib import Path

home = Path(sys.argv[1])
sys.path.insert(0, str(home / "jobs/claim-kit"))
import completion  # noqa: E402

completion.run_tracker = lambda *a, **k: {}
import kit  # noqa: E402

sys.exit(kit.main(sys.argv[2:]))

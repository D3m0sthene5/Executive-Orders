#!/usr/bin/env bash
# Preserve the established shell entry point on Linux and Windows/Git Bash.
set -euo pipefail
exec python .github/scripts/run_jobs.py

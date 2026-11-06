#!/usr/bin/env bash
# Rebuild every number in output/ from the transcripts on this PC and the committed Bentham-format telemetry.
# Usage: bash jobs/necker-costs/refresh.sh CUTOFF_ISO   (messages after CUTOFF are left out, so the run is repeatable)
set -euo pipefail
CUT="${1:?cutoff, e.g. 2026-11-06T22:40:00Z}"
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
TMP="$(mktemp -d)"
N="py -I $HERE/necker.py"
REF="${REF:-origin/main}"
show() { git -C "$REPO" show "$REF:$1" > "$2"; }
show research/excavator/claude-tribonian-2026-11-04/telemetry/AGENT_USAGE.csv "$TMP/trib.csv"
show research/excavator/claude-tribonian-2026-11-04/evidence/DISPOSITION.json "$TMP/trib_disp.json"
show research/excavator/claude-icecore-2026-11-05/telemetry/AGENT_USAGE.csv "$TMP/ice.csv"
show research/excavator/claude-icecore-2026-11-05/evidence/DISPOSITION.json "$TMP/ice_disp.json"
show research/excavator/claude-theophilus-2026-11-05/telemetry/AGENT_USAGE.csv "$TMP/theo.csv"
show research/herschel/H1/TRACE.jsonl "$TMP/h1_trace.jsonl"
py -I - "$REPO/jobs/bentham/output/CANDIDATES.json" "$TMP/ids.json" <<'PY'
import json,sys
json.dump([a["id"] for a in json.load(open(sys.argv[1]))["actions"]], open(sys.argv[2], "w"))
PY
CLAUDE_PROJECTS="${CLAUDE_PROJECTS:-$HOME/.claude/projects}"
$N transcripts "$CLAUDE_PROJECTS" --out "$HERE/output/local" --until "$CUT" --action-ids "$TMP/ids.json"
$N validate "$CLAUDE_PROJECTS" --until "$CUT" --trace "$TMP/h1_trace.jsonl" --out "$HERE/output/validation"
$N telemetry "$TMP/trib.csv" --wave tribonian-2026-11-04 --disposition "$TMP/trib_disp.json" --out "$HERE/output/telemetry/tribonian-2026-11-04"
$N telemetry "$TMP/ice.csv" --wave claude-icecore-2026-11-05 --disposition "$TMP/ice_disp.json" --out "$HERE/output/telemetry/claude-icecore-2026-11-05"
$N telemetry "$TMP/theo.csv" --wave claude-theophilus-2026-11-05 --out "$HERE/output/telemetry/claude-theophilus-2026-11-05"
$N compare tribonian-2026-11-04="$TMP/trib.csv" claude-icecore-2026-11-05="$TMP/ice.csv" claude-theophilus-2026-11-05="$TMP/theo.csv" --out "$HERE/output/comparison" > /dev/null
$N merge "$HERE/output/telemetry/tribonian-2026-11-04" "$HERE/output/telemetry/claude-icecore-2026-11-05" \
  "$HERE/output/telemetry/claude-theophilus-2026-11-05" "$HERE/output/local" --out "$HERE/output" \
  --inputs "$TMP/trib.csv" "$TMP/trib_disp.json" "$TMP/ice.csv" "$TMP/ice_disp.json" "$TMP/theo.csv" "$TMP/h1_trace.jsonl" \
  --note "origin/main telemetry files read with git show at $(git -C "$REPO" rev-parse --short "$REF"); transcript cutoff $CUT"
rm -rf "$TMP"

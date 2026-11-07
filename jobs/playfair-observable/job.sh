#!/usr/bin/env bash
# Playfair: a one-section trial of Observable Framework. Builds on the runner, deploys nothing, and writes only
# measurements plus a zip of dist/ when it is under 5 MiB. See README.md.
set -euo pipefail

FRAMEWORK_VERSION="1.13.4"
HERE="$JOB_DIR"
OUT="$OUTPUT_DIR"
SRC_DATA="$REPO_ROOT/jobs/tsiolkovsky-trajectory/output"
WORK="$(mktemp -d)"
now() { date +%s.%N; }
elapsed() { python3 -c "print(round($2 - $1, 2))"; }

echo "node: $(node --version)  npm: $(npm --version)  machine: $(uname -sr)"

# --- stage the small source tree: authored files plus the committed data
mkdir -p "$WORK/src/data"
cp "$HERE/package.json" "$WORK/package.json"
cp "$HERE/src/index.md" "$HERE/src/observablehq.config.js" "$WORK/src/"
for f in TRAJECTORY.csv GENERATION_POINTS.csv MISSION.csv; do
  test -s "$SRC_DATA/$f" || { echo "missing input $SRC_DATA/$f"; exit 1; }
  cp "$SRC_DATA/$f" "$WORK/src/data/$f"
done
rows="$(($(wc -l < "$WORK/src/data/TRAJECTORY.csv") - 1))"
echo "trajectory rows: $rows"
test "$rows" -ge 5

# --- install, pinned to one exact Framework version
cd "$WORK"
t0="$(now)"
npm install --no-audit --no-fund --save-exact >"$OUT/npm-install.log" 2>&1 || { tail -40 "$OUT/npm-install.log"; exit 1; }
t1="$(now)"
INSTALLED="$(node -p "require('./node_modules/@observablehq/framework/package.json').version")"
echo "installed framework: $INSTALLED"
test "$INSTALLED" = "$FRAMEWORK_VERSION"
PKG_DIRS="$(find node_modules -name package.json | wc -l)"
NM_BYTES="$(du -sb node_modules | cut -f1)"

# --- build
t2="$(now)"
npx observable build 2>&1 | tee "$OUT/build.log" | tail -30
t3="$(now)"
test -f dist/index.html

# --- measure
python3 -I "$HERE/measure.py" dist > "$WORK/dist-measure.json"

# --- positive control: the data in dist/ is the committed data, byte for byte
python3 -I - "$WORK" <<'PY'
import hashlib, pathlib, sys
work = pathlib.Path(sys.argv[1])
dist = work / "dist"
have = {hashlib.sha256(p.read_bytes()).hexdigest() for p in dist.rglob("*") if p.is_file()}
for name in ("TRAJECTORY.csv", "GENERATION_POINTS.csv", "MISSION.csv"):
    h = hashlib.sha256((work / "src" / "data" / name).read_bytes()).hexdigest()
    if h not in have:
        sys.exit("dist does not hold " + name + " byte for byte")
print("dist holds all three data files byte for byte")
PY

# --- render check: open the built page in headless Chrome and count the charts that drew
CHROME="$(command -v google-chrome || command -v google-chrome-stable || command -v chromium || command -v chromium-browser || true)"
SVGS="null"; SHOT_BYTES="null"; RENDER_NOTE="no browser on the runner"
if [ -n "$CHROME" ]; then
  (cd dist && python3 -m http.server 8765 --bind 127.0.0.1 >/dev/null 2>&1 & echo $! > "$WORK/http.pid")
  sleep 2
  "$CHROME" --headless=new --no-sandbox --disable-gpu --virtual-time-budget=20000 --dump-dom http://127.0.0.1:8765/ \
    > "$WORK/dom.html" 2>"$WORK/chrome.err" || true
  SVGS="$(grep -o '<svg' "$WORK/dom.html" | wc -l)"
  "$CHROME" --headless=new --no-sandbox --disable-gpu --virtual-time-budget=20000 --hide-scrollbars \
    --window-size=1100,2300 --screenshot="$WORK/shot.png" http://127.0.0.1:8765/ >/dev/null 2>&1 || true
  if [ -f "$WORK/shot.png" ]; then
    SHOT_BYTES="$(stat -c %s "$WORK/shot.png")"
    if [ "$SHOT_BYTES" -lt 512000 ]; then cp "$WORK/shot.png" "$OUT/screenshot.png"; fi
  fi
  kill "$(cat "$WORK/http.pid")" 2>/dev/null || true
  RENDER_NOTE="$("$CHROME" --version 2>/dev/null | head -1)"
  echo "svg elements in rendered DOM: $SVGS"
  if [ "$SVGS" -lt 5 ]; then
    echo "FAIL: fewer than 5 svg elements drew; DOM head and chrome stderr follow"
    head -c 1500 "$WORK/dom.html"; echo; head -c 800 "$WORK/chrome.err"
  fi
fi

# --- comparator: the current EO section (gessner cards, one generated HTML file)
CARDS="$REPO_ROOT/jobs/gessner-cards/output/CARDS.html"
CARDS_BYTES="null"; CARDS_GZ="null"
if [ -f "$CARDS" ]; then
  CARDS_BYTES="$(stat -c %s "$CARDS")"
  CARDS_GZ="$(gzip -6 -c "$CARDS" | wc -c)"
fi

# --- zip of dist/ only if under 5 MiB
ZIP_NOTE="not written (5 MiB or more)"
(cd dist && python3 -I -m zipfile -c "$WORK/dist.zip" . >/dev/null)
ZIP_BYTES="$(stat -c %s "$WORK/dist.zip")"
if [ "$ZIP_BYTES" -lt 5242880 ]; then cp "$WORK/dist.zip" "$OUT/dist.zip"; ZIP_NOTE="written"; fi

# --- write measurements
python3 -I - <<PY
import json, pathlib
m = json.load(open("$WORK/dist-measure.json"))
svgs = "$SVGS"
shot = "$SHOT_BYTES"
cards = "$CARDS_BYTES"
cards_gz = "$CARDS_GZ"
out = {
  "framework_version_pinned": "$FRAMEWORK_VERSION",
  "framework_version_installed": "$INSTALLED",
  "node": "$(node --version)",
  "npm_install_seconds": $(elapsed "$t0" "$t1"),
  "build_seconds": $(elapsed "$t2" "$t3"),
  "node_modules_package_json_files": $PKG_DIRS,
  "node_modules_bytes": $NM_BYTES,
  "dist": m,
  "zip_bytes": $ZIP_BYTES,
  "zip_in_output": "$ZIP_NOTE",
  "render_check": {
    "svg_elements": None if svgs == "null" else int(svgs),
    "screenshot_bytes": None if shot == "null" else int(shot),
    "browser": "$RENDER_NOTE",
    "screenshot_committed": pathlib.Path("$OUT/screenshot.png").exists(),
  },
  "comparator_gessner_cards_html": {
    "bytes": None if cards == "null" else int(cards),
    "gzip_bytes": None if cards_gz == "null" else int(cards_gz),
  },
  "trajectory_rows": $rows,
}
json.dump(out, open("$OUT/MEASUREMENTS.json", "w"), indent=2)
print(json.dumps({k: v for k, v in out.items() if k != "dist"}, indent=2))
print("dist:", m["file_count"], "files,", m["total_bytes"], "bytes,", m["total_gzip_bytes"], "gzip")
PY

# --- budget: committed output must stay far under the 20 MiB total / 5 MiB per-file rule
python3 -I - <<PY
import json, pathlib
out = pathlib.Path("$OUT")
files = [p for p in out.rglob("*") if p.is_file()]
total = sum(p.stat().st_size for p in files)
big = max((p.stat().st_size for p in files), default=0)
json.dump({"committed_output_bytes_before_log": total, "largest_file_bytes": big,
           "limit_total": 20 * 2**20, "limit_file": 5 * 2**20}, open(out / "BUDGET.json", "w"), indent=2)
assert total < 20 * 2**20 and big < 5 * 2**20, "output over budget"
PY

# a trial whose charts did not draw has not shown its section: fail
if [ "$SVGS" != "null" ] && [ "$SVGS" -lt 5 ]; then exit 1; fi
echo "playfair-observable: done"

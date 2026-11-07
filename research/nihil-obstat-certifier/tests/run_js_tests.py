#!/usr/bin/env python3
"""Run tests/test_core.html in a headless Edge or Chrome and report the result.

Starts a throwaway local web server on 127.0.0.1 (standard library), loads the test page, reads the
JSON the page writes into #result. Exit 0 when every JS test passed, 1 on failures, 2 if no browser.
"""

import functools
import http.server
import json
import pathlib
import re
import shutil
import subprocess
import sys
import threading

ROOT = pathlib.Path(__file__).resolve().parent.parent
CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def find_browser():
    for name in ("msedge", "chrome", "google-chrome", "chromium"):
        p = shutil.which(name)
        if p:
            return p
    return next((c for c in CANDIDATES if pathlib.Path(c).exists()), None)


def main():
    browser = find_browser()
    if not browser:
        print("no Edge/Chrome found; open tests/test_core.html over http in any browser instead")
        return 2

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    handler = functools.partial(Quiet, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}/tests/test_core.html"
    try:
        out = subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-first-run",
                              "--user-data-dir=" + str(pathlib.Path(__import__("tempfile").mkdtemp())),
                              "--virtual-time-budget=60000", "--dump-dom", url],
                             capture_output=True, timeout=180).stdout.decode("utf-8", "replace")
    finally:
        server.shutdown()
    m = re.search(r'<pre id="result"[^>]*>(.*?)</pre>', out, re.S)
    if not m:
        print("the test page produced no result; DOM tail:\n" + out[-600:])
        return 1
    import html
    summary = json.loads(html.unescape(m.group(1)))
    print(f"JS tests: {summary['passed']} of {summary['total']} passed (hash engine: {summary['engine']})")
    for f in summary["failures"]:
        print("FAIL", f["name"], f.get("extra", ""))
    return 0 if summary["failed"] == 0 and summary["total"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())

"""Run a Python script as __main__ and report wall seconds and kernel read counters on stderr.

rchar/syscr come from /proc/self/io (Linux): bytes and read calls through read(2), page cache
included. Used only for engineering receipts; output line is 'IO_RUN {json}'.
"""
import json
import resource
import runpy
import sys
import time


def counters():
    try:
        with open('/proc/self/io') as f:
            return {k: int(v) for k, v in (line.split(': ') for line in f)}
    except OSError:
        return {}


script = sys.argv[1]
sys.argv = sys.argv[1:]
sys.path.insert(0, str(__import__('pathlib').Path(script).resolve().parent))
start = time.monotonic(); before = counters(); code = 0
try:
    runpy.run_path(script, run_name='__main__')
except SystemExit as exc:
    code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    if exc.code not in (None, 0) and not isinstance(exc.code, int):
        print(exc.code, file=sys.stderr)
finally:
    after = counters()
    print('IO_RUN ' + json.dumps({'seconds': round(time.monotonic() - start, 2),
        'read_bytes': after.get('rchar', 0) - before.get('rchar', 0),
        'read_calls': after.get('syscr', 0) - before.get('syscr', 0),
        'max_rss_kb': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}), file=sys.stderr, flush=True)
sys.exit(code)

"""Run the native completion in an isolated replay tree, optionally publishing another batch's claims file
mid-run (the observed production race), and record packet loads, seconds and bytes read."""
import argparse, json, sys, time, os, threading
from pathlib import Path
ap = argparse.ArgumentParser()
ap.add_argument('tree'); ap.add_argument('manifest'); ap.add_argument('dest')
ap.add_argument('--inject', help='repo-relative claims file to publish mid-run (copied from pristine main)')
ap.add_argument('--inject-source', default='/home/user/Executive-Orders')
ap.add_argument('--publish', action='store_true'); ap.add_argument('--out', required=True)
a = ap.parse_args()
repo = Path(a.tree).resolve(); sys.path.insert(0, str(repo / 'jobs/claim-kit'))
import batch, completion
stats = {'load_packet_calls': 0, 'load_packet_seconds': 0.0, 'read_bytes': 0, 'read_calls': 0}
orig_load = batch.load_packet
def load(*x, **k):
    s = time.monotonic(); stats['load_packet_calls'] += 1
    try: return orig_load(*x, **k)
    finally: stats['load_packet_seconds'] += time.monotonic() - s
batch.load_packet = load
_rb = Path.read_bytes
def rb(self):
    b = _rb(self); stats['read_bytes'] += len(b); stats['read_calls'] += 1; return b
Path.read_bytes = rb
injected = {}
if a.inject:
    orig_checker = completion.run_checker
    def checker(*x, **k):
        r = orig_checker(*x, **k)
        p = repo / a.inject; raw = (Path(a.inject_source) / a.inject).read_bytes()
        p.write_bytes(raw); injected.update(path=a.inject, bytes=len(raw), after='run_checker')
        return r
    completion.run_checker = checker
t = time.monotonic(); err = None
try:
    tally = completion.complete(repo, Path(a.manifest).resolve(), Path(a.dest).resolve(), publish=a.publish)
except Exception as e:
    tally = None; err = repr(e)
res = {'seconds': round(time.monotonic() - t, 1), **{k: round(v, 1) if isinstance(v, float) else v for k, v in stats.items()},
       'injected': injected, 'error': err}
if tally:
    res.update(counts=tally['counts'], eligible=tally['eligible'], exceptions=tally['exceptions'],
               claims_published=tally['claims_published'])
    res['exception_messages'] = json.loads((Path(a.dest) / 'EXCEPTIONS.json').read_bytes())
    res['publication'] = json.loads((Path(a.dest) / 'PUBLICATION.json').read_bytes())
Path(a.out).write_text(json.dumps(res, indent=1)); print(json.dumps(res)[:1500])

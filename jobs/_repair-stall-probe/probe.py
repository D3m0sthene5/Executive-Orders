"""Read-only, bounded timing probe; never writes a research generation to GitHub."""
import argparse
import faulthandler
import json
import os
from pathlib import Path
import resource
import runpy
import sys
import threading
import time
import traceback
import urllib.request

p = argparse.ArgumentParser()
p.add_argument('--repo', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--network-budget', type=int, choices=(0, 2, 400), required=True)
p.add_argument('--cases', type=int, choices=(2, 3359), default=2)
p.add_argument('--mode', choices=('drafts', 'sources'), default='drafts')
a = p.parse_args()
repo = a.repo.resolve()
out = a.output.resolve()
if out.is_relative_to(repo) or out.exists():
    raise ValueError('a new output directory outside the target checkout is required')
out.mkdir(parents=True)
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
os.environ.update(REPO_ROOT=str(repo), OUTPUT_DIR=str(out / 'drafts'),
    JOB_CACHE_DIR=str(out / 'cache'), JOB_LIMIT=str(a.cases), CLAIM_DRAFTS_SCOPE='decided',
    CLAIM_CHECKER_VERIFY_DOWNLOADS=str(a.network_budget), PYTHONDONTWRITEBYTECODE='1')
started = time.monotonic()
stop = threading.Event()
events = []


def emit(kind, **data):
    row = {'kind': kind, 'elapsed_seconds': round(time.monotonic() - started, 3), **data}
    print(json.dumps(row, sort_keys=True), flush=True)
    return row


def heartbeat():
    while not stop.wait(15):
        usage = resource.getrusage(resource.RUSAGE_SELF)
        emit('heartbeat', user_cpu_seconds=usage.ru_utime,
             system_cpu_seconds=usage.ru_stime, max_rss_kib=usage.ru_maxrss)


original_urlopen = urllib.request.urlopen


def traced_urlopen(request, *args, **kwargs):
    url = request.full_url if isinstance(request, urllib.request.Request) else str(request)
    event = emit('network_start', url=url, timeout=kwargs.get('timeout'))
    events.append(event)
    t0 = time.monotonic()
    try:
        result = original_urlopen(request, *args, **kwargs)
    except Exception as exc:
        events.append(emit('network_error', url=url, seconds=time.monotonic() - t0,
                           error=type(exc).__name__ + ': ' + str(exc)))
        raise
    events.append(emit('network_headers', url=url, seconds=time.monotonic() - t0,
                       status=getattr(result, 'status', None)))
    return result


urllib.request.urlopen = traced_urlopen
threading.Thread(target=heartbeat, daemon=True).start()
faulthandler.enable()
faulthandler.dump_traceback_later(45, repeat=True)
emit('start', target_commit=os.environ.get('TARGET_COMMIT'), cases=a.cases, mode=a.mode,
     network_budget=a.network_budget, pid=os.getpid())
code = 0
try:
    if a.mode == 'sources':
        # Exercise the actual unchanged download verifier against two cited PDFs.
        sys.path.insert(0, str(repo / 'jobs/claim-checker'))
        import checker
        claims = {}
        for path in sorted((repo / 'research/readiness/claims').glob('*.jsonl')):
            for line in path.read_text().splitlines():
                if line.strip():
                    claim = json.loads(line)
                    claims[claim['instrument_id']] = claim
        for iid in ('EO:13792', 'EO:13148'):
            ref = claims[iid]['original_representation']
            emit('source_check_start', instrument_id=iid, url=ref['url'], sha256=ref['sha256'])
            result = checker.verify_by_download(ref['url'], ref['sha256'], out / 'cache')
            emit('source_check_result', instrument_id=iid, verified=result)
    else:
        # Import and instrument the unchanged target module. Only timing output is added.
        sys.path.insert(0, str(repo / 'jobs/claim-drafts'))
        import drafts
        original_build = drafts.build_draft

        def timed_build(iid, *args, **kwargs):
            t0 = time.monotonic()
            emit('case_start', instrument_id=iid)
            result = original_build(iid, *args, **kwargs)
            emit('case_built', instrument_id=iid, seconds=time.monotonic() - t0)
            return result

        drafts.build_draft = timed_build
        drafts.main()
except BaseException as exc:
    code = exc.code if isinstance(exc, SystemExit) and isinstance(exc.code, int) else 1
    traceback.print_exc()
finally:
    faulthandler.cancel_dump_traceback_later()
    stop.set()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    summary = emit('complete', exit_code=code, user_cpu_seconds=usage.ru_utime,
        system_cpu_seconds=usage.ru_stime, max_rss_kib=usage.ru_maxrss,
        mode=a.mode, cases=a.cases, network_budget=a.network_budget, network_events=events,
        interpretation='Diagnostic only; initial committed inputs, not the live runner filesystem. No canonical outputs or claims are published.')
    (out / 'PROBE_SUMMARY.json').write_text(json.dumps(summary, indent=2) + '\n')
raise SystemExit(code)

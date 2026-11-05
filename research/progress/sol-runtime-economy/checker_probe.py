"""Bounded synthetic checker index probe; creates and removes temporary fixture.

Usage: python3 -I research/progress/sol-runtime-economy/checker_probe.py [rows]
Compares exact baseline with local staged-reader code in fresh processes.
"""
import gc, hashlib, importlib.util, inspect, json, os, pathlib, resource, subprocess, sys, tempfile, time

REPO = pathlib.Path(__file__).resolve().parents[3]
SOURCE = REPO / 'jobs/claim-checker/sources.py'

def io():
    data = pathlib.Path('/proc/self/io').read_text()
    return int(next(x.split(':')[1] for x in data.splitlines() if x.startswith('rchar:')))

def worker(root, arm):
    spec = importlib.util.spec_from_file_location('probe_sources', SOURCE)
    s = importlib.util.module_from_spec(spec)
    if arm == 'baseline':
        original = subprocess.run(['git', 'show', '2c85459cf38b08dc1eea6d7c84a74268fa45c28e:jobs/claim-checker/sources.py'], cwd=REPO, check=True, capture_output=True, text=True).stdout
        exec(compile(original, str(SOURCE), 'exec'), s.__dict__)
    else:
        spec.loader.exec_module(s)
    root = pathlib.Path(root)
    results = []
    for n in range(2):
        start_io = io(); start = time.monotonic()
        index = s.build_index(root, root / 'jobs/claim-checker', exclude_jobs=('claim-checker',))
        elapsed = time.monotonic()-start; reads = io()-start_io
        # Stable canonical digest includes order and all observable fields used here.
        digest = hashlib.sha256()
        count = 0
        for sha, copies in index.by_sha.items():
            for c in copies:
                digest.update(json.dumps([sha,c.origin,c.url,c.bytes,str(c.local_path),str(c.text_path),[(str(p),m) for p,m in c.zip_members],c.page_or_item,c.instrument_ids,c.note,c.custody],separators=(',',':')).encode()); count += 1
        results.append(dict(seconds=round(elapsed,3),rchar=reads,records=count,digest=digest.hexdigest(),notes=index.notes))
        del index; gc.collect()
    print(json.dumps(dict(arm=arm,builds=results,max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))

if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker': worker(sys.argv[2],sys.argv[3]); raise SystemExit
    rows=int(sys.argv[1]) if len(sys.argv)>1 else 100000
    with tempfile.TemporaryDirectory(prefix='checker-probe-') as tmp:
        file=pathlib.Path(tmp)/'jobs/synthetic/output/SOURCES.jsonl'; file.parent.mkdir(parents=True)
        with file.open('w') as f:
            for i in range(rows):
                f.write(json.dumps({'sha256':f'{i:064x}','url':f'https://example.org/source/{i}','bytes':12345,'instrument_ids':[f'EO {i}'],'route':'fixture record for bounded source index measurement'},separators=(',',':'))+'\n')
            f.write('not-json\n[]\n')
        print(json.dumps(dict(fixture_rows=rows,fixture_bytes=file.stat().st_size)),flush=True)
        for arm in ('baseline','staged'):
            p=subprocess.run([sys.executable,'-I',str(pathlib.Path(__file__).resolve()),'--worker',tmp,arm],check=True,capture_output=True,text=True)
            print(p.stdout.strip(),flush=True)

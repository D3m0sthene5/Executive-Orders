import json, subprocess, sys
out = sys.argv[1]
def gh(path):
    return json.loads(subprocess.check_output(['gh', 'api', path]))
runs = {}
windows = []
for day in range(6, 10):
    for h0, h1 in ((0, 5), (6, 11), (12, 17), (18, 23)):
        windows.append(f'2026-11-{day:02d}T{h0:02d}:00:00Z..2026-11-{day:02d}T{h1:02d}:59:59Z')
for w in windows:
    page = 1
    while True:
        d = gh(f'repos/D3m0sthene5/Executive-Orders/actions/runs?per_page=100&page={page}&created={w}')
        rs = d['workflow_runs']
        for r in rs:
            runs[r['id']] = {k: r.get(k) for k in ('id', 'name', 'event', 'status', 'conclusion', 'head_branch', 'created_at', 'run_started_at', 'updated_at', 'run_attempt')}
        if len(rs) < 100: break
        page += 1
    print(w, d.get('total_count'), file=sys.stderr)
json.dump(list(runs.values()), open(out, 'w'))
print(len(runs))

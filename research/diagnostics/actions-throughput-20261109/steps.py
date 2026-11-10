import json, subprocess, sys, concurrent.futures as cf
runs = json.load(open(sys.argv[1])); out = sys.argv[2]
pick = []
for name, k in (('Run jobs', 260), ('Refresh published progress', 80), ('Road system offline tests', 40), ('Kean shared-register check', 30)):
    rs = sorted([r for r in runs if r['name'] == name and r['status'] == 'completed'], key=lambda r: r['created_at'])
    step = max(1, len(rs) // k); pick += rs[::step][:k]
def jobs(r):
    try:
        d = json.loads(subprocess.check_output(['gh', 'api', f"repos/D3m0sthene5/Executive-Orders/actions/runs/{r['id']}/jobs?per_page=100&filter=latest"]))
    except Exception as e:
        return r['id'], {'error': str(e)}
    return r['id'], [{'name': j['name'], 'conclusion': j['conclusion'], 'started_at': j['started_at'], 'completed_at': j['completed_at'], 'created_at': j.get('created_at'),
                      'steps': [{'name': s['name'], 'conclusion': s['conclusion'], 'started_at': s['started_at'], 'completed_at': s['completed_at']} for s in j.get('steps', [])]} for j in d['jobs']]
res = {}
with cf.ThreadPoolExecutor(8) as ex:
    for rid, j in ex.map(jobs, pick): res[rid] = j
json.dump({'runs': {r['id']: r for r in pick}, 'jobs': res}, open(out, 'w'))
print(len(res))

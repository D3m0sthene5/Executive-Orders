import json,sys,subprocess,glob,collections
sys.path.insert(0,'.github/scripts')
import result_freshness as rf
art, base, tip = sys.argv[1:4]
changed=subprocess.run(['git','diff','--name-only',base,tip],capture_output=True,text=True).stdout.split()
entries={p:'x' for p in changed}
names=[json.load(open(f))['job'] for f in sorted(glob.glob(art+'/*-inputs.json'))]
for name in names:
    old=json.load(open(f'{art}/{name}-inputs.json'))['scope']
    new=rf.scope(name)
    ho={p for p in rf.select(entries,old) if not p.startswith(f'jobs/{name}/output')}
    hn={p for p in rf.select(entries,new) if not p.startswith(f'jobs/{name}/output')}
    tops=collections.Counter('/'.join(p.split('/')[:2]) for p in hn)
    print(f"{name:24s} old={len(ho):6d} new={len(hn):6d} {'PUBLISH' if not hn else 'stale'} {dict(tops.most_common(4))}")

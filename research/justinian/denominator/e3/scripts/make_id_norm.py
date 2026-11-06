import csv,re,subprocess,sys
root='/home/user/Executive-Orders'
out=subprocess.run(['grep','-rIn','-E',r'7933a\b','research','jobs','releases','HANDOFF'],cwd=root,capture_output=True,text=True,errors='replace').stdout
by={}
for l in out.splitlines():
    f,n,_=l.split(':',2); by.setdefault(f,[]).append(int(n))
names=subprocess.run(['find','research','jobs','releases','-name','*7933a*'],cwd=root,capture_output=True,text=True).stdout.split()
tok=re.compile(r'7933a\b')
def role(f):
    if f.endswith(('test_clark.py','test_eo_refs.py','test_fetch_ladder.py')): return 'test fixture (asserts lowercase spelling; update with code change)'
    if '/_attempts/' in f: return 'historical attempt snapshot (leave; do not rewrite history)'
    if '/RUNNER_INPUTS.json' in f or f.endswith('INPUTS.json'): return 'generated runner inputs (regenerate, do not hand edit)'
    if f.endswith('.py'): return 'code'
    if f=='research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv': return 'CENSUS id column (primary change)'
    return 'generated data/output (regenerate from source after census id fix)'
with open(sys.argv[1],'w',newline='') as fh:
    w=csv.writer(fh); w.writerow(['current_id','normalized_id','path','line_numbers_or_filename','n_lines','action','role','note'])
    for f,ls in sorted(by.items()):
        w.writerow(['EO:7933a','EO:7933A',f,';'.join(map(str,ls[:12]))+(';...' if len(ls)>12 else ''),len(ls),'change lowercase suffix to uppercase (EO:7933a -> EO:7933A; EO_7933a -> EO_7933A)',role(f),'canonical form per jobs/_lib/eo_identity.py canon_id; PROPOSAL ONLY'])
    for n in names:
        w.writerow(['EO_7933a','EO_7933A',n,'(file name)',0,'rename file','file name','proposal only; update readers'])
print(len(by),len(names))

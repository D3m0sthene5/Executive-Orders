"""Historical immutable input-generation audit; native publication guard is authoritative.
No repository writes, local scope construction, working-tree substitution or science.
"""
import importlib.util,json,pathlib,subprocess,sys
published=sys.argv[1];report=pathlib.Path(sys.argv[2]).resolve();run=sys.argv[3]
names=['valla','claim-kit','claim-checker','census-candidates','readiness-tracker','early-ranger-workbench','neyman','case-bundles']
def git(*args):return subprocess.check_output(['git',*args])
def read(path):return json.loads(git('show',published+':'+path))
repo=pathlib.Path.cwd().resolve()
assert not report.is_relative_to(repo),'Report must remain outside repository'
published=git('rev-parse',published+'^{commit}').decode().strip()
parents=git('rev-list','--parents','-n','1',published).decode().split()
assert len(parents)==2,parents
parent=parents[1]
assert pathlib.Path('.github/scripts/result_freshness.py').read_bytes()==git('show',published+':.github/scripts/result_freshness.py'),'Helper differs from published source'
spec=importlib.util.spec_from_file_location('audited_freshness','.github/scripts/result_freshness.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
output_scope={'roots':[f'jobs/{n}/output' for n in names],'patterns':[],'exclude':'\0'}
candidate=f.tree(published,output_scope);prior=f.tree(parent,output_scope)
records={};problems=[];generation={}
for name in names:
    root=f'jobs/{name}/output/'
    m=read(root+'RUNNER_INPUTS.json');status=read(root+'STATUS.json')
    assert m['schema']==1 and m['job']==name and f.digest(m['inputs'])==m['inputs_sha256'],name
    assert status['job']==name and status['result']=='succeeded' and status['exit_code']==0,status
    assert m['run_url'].endswith('/actions/runs/'+run) and status['run_url']==m['run_url'],name
    baseline=f.tree(m['base_commit'],output_scope)
    assert m['base_output_sha256']==f.digest(f.output(baseline,name)),name
    if f.digest(f.output(prior,name)) not in (m['base_output_sha256'],f.digest(f.output(candidate,name))):
        problems.append({'job':name,'reason':'concurrent_output_advanced'})
    projected=f.tree(parent,m['scope']);generation[name]={}
    for i,producer in enumerate(names):
        produced=f.output(candidate,producer);base=f.output(baseline,producer)
        captured=f.output(m['inputs'],producer)
        candidate_inputs=f.select(produced,m['scope']);base_inputs=f.select(base,m['scope'])
        if not(captured or candidate_inputs or base_inputs):continue
        chosen=produced;kind='same_run_candidate'
        if captured!=candidate_inputs:
            if i>names.index(name) and captured==base_inputs and f.output(prior,producer)==base:
                chosen=base;kind='captured_base'
            else:kind='unmatched'
        generation[name][producer]=kind
        projected={p:v for p,v in projected.items() if not f.under(p,f'jobs/{producer}/output')};projected.update(chosen)
    actual=f.select(projected,m['scope']);expected=m['inputs']
    changed=[p for p in sorted(expected.keys()|actual.keys()) if expected.get(p)!=actual.get(p)]
    if changed:problems.append({'job':name,'changed_paths':changed})
    records[name]={'base_commit':m['base_commit'],'run_url':m['run_url'],'status':status,'inputs_sha256':m['inputs_sha256'],'input_count':len(expected),'scope':m['scope'],'generation_rules':generation[name],'immutable_input_map_matches':not changed}
result={'schema':'historical-published-input-consistency/v1','method':'Read immutable published manifests/status and Git trees; use existing select/tree/digest helpers with ordered captured-base rule. No working() or scope() substitution; no repository writes. Actual native guard is authoritative for live/transient bytes.','published_commit':published,'publication_parent':parent,'run':run,'ordered_jobs':names,'result':'consistent' if not problems else 'inconsistent','jobs':records,'problems':problems}
report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'result':result['result'],'published':published,'parent':parent,'problems':problems,'jobs':{n:{'base':d['base_commit'],'inputs':d['input_count'],'seconds':None,'input_map_matches':d['immutable_input_map_matches'],'generations':generation[n]} for n,d in records.items()}},indent=2))
sys.exit(bool(problems))

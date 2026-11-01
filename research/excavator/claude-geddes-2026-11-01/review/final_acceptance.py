"""Independent exact-version engineering checks. Not scientific certification."""
import hashlib,json,subprocess,sys,tempfile,time,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'jobs/geddes'));import geddes

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 start=time.monotonic();utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
 owned=['jobs/geddes/geddes.py','jobs/geddes/test_geddes.py','jobs/geddes/job.py','jobs/geddes/README.md','jobs/geddes/needs.txt','.github/workflows/geddes.yml']
 pins={p:sha(ROOT/p) for p in owned};checks=[]
 def check(name,success,detail=None):checks.append({'name':name,'pass':bool(success),'detail':detail})
 for script,out in [('independent_probes.py','FINAL_PROBES.json'),('real_boundary_probe.py','FINAL_REAL_BOUNDARY.json')]:
  c=subprocess.run([sys.executable,str(HERE/script)],cwd=ROOT,capture_output=True,text=True)
  (HERE/out).write_text(c.stdout)
  check(script+' executes',c.returncode==0,c.stderr)
  if c.returncode==0:
   r=json.loads(c.stdout)
   if 'results' in r:check('independent adversarial probes',all(z.get('pass',True) for z in r['results']),{'passed':sum(z.get('pass') is True for z in r['results']),'total':sum('pass'in z for z in r['results'])})
   else:
    for name in ('view_excludes_previous_neighbor','view_retains_target_name','attribution_rejects_neighbor','lookup_parent_matches'):check(name,r[name])
 c=subprocess.run([sys.executable,'-I','jobs/geddes/test_geddes.py'],cwd=ROOT,capture_output=True,text=True)
 (HERE/'FINAL_UNIT_TESTS.txt').write_text(c.stdout+c.stderr);check('worker meaningful unit tests',c.returncode==0)
 expected=json.loads((HERE/'EXPECTED_APOLLO_COST.json').read_text());actual=geddes.cost(ROOT/'research/excavator/claude-apollo-2026-10-31/TELEMETRY.csv')
 for e in expected['groups']:
  g=next(x for x in actual['groups'] if (x['track'],x['role'])==(e['track'],e['role']))
  check('actual telemetry arithmetic '+e['track']+' '+e['role'],g.get('filed_claims_denominator')==127 and all(g.get(k)==v and g.get(k+'_per_filed_claim')==round(v/127,2) for k,v in e['totals'].items()))
 with tempfile.TemporaryDirectory() as t:
  p=Path(t)/'telemetry.csv';p.write_text('batch,role,model,input_tokens,output_tokens,active_seconds\ng01,producer,m,5,,1.5\n')
  g=geddes.cost(p)['groups'][0]
  check('missing telemetry unknown and decimal seconds retained',g.get('output_tokens') is None and g.get('cache_read_input_tokens') is None and g.get('active_seconds')==1.5,g)
 p=ROOT/'research/excavator/claude-apollo-2026-10-31/n01/packet/supp/PACKET.json';pk=json.loads(p.read_text());iid=next(iter(pk['dossiers']));v=geddes.view(p,iid)
 memo=v.get('shared_analysis_memo',{});sections=memo.get('sections',{})
 check('NRA matching shared memo has actual sections',bool(sections) and all(isinstance(z,str) and z for z in sections.values()),{'instrument_id':iid,'section_titles':list(sections)})
 if memo.get('path'):check('NRA shared memo hash verified',sha(ROOT/memo['path'])==memo.get('sha256'))
 baseline=json.loads((HERE/'CONTRACT_BASELINE.json').read_text());changed=[p for p,h in baseline.items() if sha(ROOT/p)!=h];check('frozen claim-kit contract unchanged',not changed,changed)
 c=subprocess.run([sys.executable,'-I','jobs/geddes/geddes.py','lint','research/excavator/claude-apollo-2026-10-31/g01/packet/supp/applied-v3'],cwd=ROOT,capture_output=True,text=True)
 (HERE/'FINAL_NATIVE_LINT.json').write_text(c.stdout);check('native retained applied CLI runs',c.returncode==0,c.stderr)
 check('implementation pins unchanged during review',pins=={p:sha(ROOT/p) for p in owned})
 end=time.monotonic();clock=json.loads((HERE/'CLOCK.json').read_text());report={'schema':'geddes-independent-engineering-review/v1','outcome':'engineering_checks_pass' if all(x['pass'] for x in checks) else 'engineering_checks_have_failures','checks':checks,'implementation_pins':pins,'review_script_sha256':sha(Path(__file__)),'model':'gpt-6-astra','tokens':None,'active_labor_seconds':None,'final_check_start_utc':utc,'final_check_end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'final_check_wall_seconds':end-start,'prospective_probe_phase_wall_seconds_including_wait':end-clock['probe_phase_start_monotonic'],'earlier_read_setup_seconds':None,'scientific_review':False,'legal_certification':False,'limitations':['Independent same-family AI engineering review only.','Exact synthetic acceptance and retained-source boundary checks; not complete semantic coverage.','Retrospective recall/false-positive adjudication remains with coordinator.','No hosted GitHub Actions run claimed; local declared-dependency/import and native CLI tests only.','Wall time includes waiting; active labor and token usage unavailable.']}
 (HERE/'FINAL_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'outcome':report['outcome'],'checks':len(checks),'failed':[x['name'] for x in checks if not x['pass']],'wall_seconds':end-start,'implementation_sha256':pins['jobs/geddes/geddes.py']}))
if __name__=='__main__':main()

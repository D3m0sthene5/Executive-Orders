"""Independent final alias-precision probes with native tracked text/index."""
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile,time
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'jobs/geddes'))
import name_checks as N
H=lambda b:hashlib.sha256(b).hexdigest()
def run():
 rows=[]
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);rel='jobs/app-executive-orders/output/texts/actor.txt';p=root/rel;p.parent.mkdir(parents=True);ix=p.parent.parent/'INDEX.jsonl';ix.write_text(json.dumps({'instrument_id':'EO:14002','date':'1935-01-01','title':'Executive Order 14002—Industry Disputes','path':'/documents/actor','url':'https://www.presidency.ucsb.edu/documents/actor'})+'\n')
  subprocess.run(['git','init','-q'],cwd=root,check=True,capture_output=True)
  def commit(text):
   p.write_text(text)
   subprocess.run(['git','add','.'],cwd=root,check=True,capture_output=True);subprocess.run(['git','-c','user.name=Review','-c','user.email=review@example.invalid','commit','-qm','fixture'],cwd=root,check=True,capture_output=True)
  claim={'instrument_id':'EO:14001','research_rationale':'No other held order names Cotton Textile Code.'}
  for name,text,expected in [('industry_alone_is_not_code','Executive Order 14002. A labor dispute affects the Cotton Textile Industry.',False),('fair_competition_code_context','Executive Order 14002. Under the Codes of Fair Competition for the Cotton Textile Industry, the board shall report.',True),('literal_full_code_name','Executive Order 14002. The Cotton Textile Code is amended.',True)]:
   commit(text);out=N.check(claim,{},root);flags=[f for f in out['flags'] if f['code']=='literal_name_counterexample'];rows.append({'name':name,'pass':bool(flags)==expected,'expected_counterexample':expected,'output':out})
  original='Executive Order 14002. A labor dispute affects the Cotton Textile Industry.';commit(original);scan=N.scan_names
  def change_after_verified_scan(*args,**kwargs):
   result=scan(*args,**kwargs);p.write_text('Executive Order 14002. Under the Codes of Fair Competition for the Cotton Textile Industry.');return result
  N.scan_names=change_after_verified_scan
  try:
   out=N.check(claim,{},root);flags=[f for f in out['flags'] if f['code']=='literal_name_counterexample'];passed=not flags
   rows.append({'name':'alias_context_cannot_use_unverified_reread','pass':passed,'expected':'A new unverified raw context cannot support a flag pinned to earlier industry-only bytes','output':out,'verified_input_sha256':H(original.encode()),'changed_raw_sha256':H(p.read_bytes())})
  finally:N.scan_names=scan
 return rows
if __name__=='__main__':
 before=H((ROOT/'jobs/geddes/name_checks.py').read_bytes());start=time.monotonic();r=run();after=H((ROOT/'jobs/geddes/name_checks.py').read_bytes());print(json.dumps({'passed':sum(x['pass'] for x in r),'total':len(r),'probes':r,'module_sha256':after,'code_stable_during_run':before==after,'wall_seconds':time.monotonic()-start,'scope':'Independent synthetic engineering probes only'},indent=2))

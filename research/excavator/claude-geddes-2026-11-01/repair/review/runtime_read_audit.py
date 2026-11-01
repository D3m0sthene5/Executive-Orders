"""Runtime file-read observation of one exact negative-name claim lint invocation."""
from pathlib import Path
import hashlib,json,sys,time,datetime
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'jobs/geddes'))
import geddes as G
H=lambda b:hashlib.sha256(b).hexdigest()
def run():
 p=ROOT/'research/excavator/claude-geddes-2026-11-01';m=json.loads((p/'inventory/MANIFEST.json').read_text());row=next(r for r in m['rows'] if r['instrument_id']=='EO:6876');ref=row['prior_claim'];f=ROOT/ref['path']
 if not f.exists() and '/receipts/' in ref['path']:f=ROOT/ref['path'].split('/receipts/')[-1]
 raw=f.read_bytes();line=raw.splitlines()[ref['line']-1];assert H(raw)==ref['file_sha256'] and H(line)==ref['record_sha256'];claim=json.loads(line);packet=G.packet_for(f.parent);d=G.batch.decode(json.loads(packet.read_text()));paths=set();active=[True]
 def audit(event,args):
  if active[0] and event=='open' and isinstance(args[0],(str,bytes)):
   path=Path(args[0].decode() if isinstance(args[0],bytes) else args[0]);paths.add(str(path.resolve()))
 sys.addaudithook(audit);start=time.monotonic();out=G.lint_one(1,claim,d,ROOT,packet,{});elapsed=time.monotonic()-start;active[0]=False
 forbidden=[s for s in sorted(paths) if Path(s).name.upper().startswith(('REVIEW','VERDICT','DEFECT_CORRELATION','EVALUATION')) or any(part in {'review','reviews'} for part in Path(s).parts)]
 return {'schema':'geddes-runtime-read-audit/v1','scope':'Actual observed reads during one exact EO6876 invocation after harness loaded claim/dossier; not universal proof of every possible runtime path','prior_claim':ref,'actual_input_path':str(f.relative_to(ROOT)),'packet_path':str(packet.relative_to(ROOT)),'reads':sorted(paths),'forbidden_review_verdict_reads':forbidden,'no_review_verdict_reads_observed':not forbidden,'code_pins':{str(f.relative_to(ROOT)):H(f.read_bytes()) for f in (ROOT/'jobs/geddes').glob('*.py') if not f.name.startswith('test_')},'output':out,'observed_seconds':elapsed,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tokens':None}
if __name__=='__main__':print(json.dumps(run(),indent=2))

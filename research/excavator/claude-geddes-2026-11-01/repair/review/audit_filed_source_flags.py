"""Retained independent exact-byte audit of all currently reported source flags."""
from pathlib import Path
import json,re,hashlib,sys,datetime,time
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'jobs/geddes'))
import geddes as G,source_checks as S
H=lambda b:hashlib.sha256(b).hexdigest()
def run():
 p=ROOT/'research/excavator/claude-geddes-2026-11-01/repair/review';check=json.loads((p.parent/'source/CHECK.json').read_text());old=json.loads((p/'OLD_EVALUATION.json').read_text());filed={r['instrument_id']:r for r in old['filed']};codeh=H((ROOT/'jobs/geddes/source_checks.py').read_bytes());start={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'monotonic':time.monotonic()};rows=[];cache={}
 for listed in check['filed_flagged']:
  iid=listed['instrument_id'];r=filed[iid];f=ROOT/r['filed_path'];raw=f.read_bytes();line=next(x for x in raw.splitlines() if json.loads(x)['instrument_id']==iid);c=json.loads(line);pk=ROOT/listed['packet_path']
  if pk not in cache:cache[pk]=G.batch.decode(json.loads(pk.read_text()))
  flags=S.check(c,cache[pk][iid],ROOT,pk,{})['flags'];assert flags==listed['flags'];assert len(flags)==1
  source=flags[0]['source'];sp=ROOT/source['text_path'];b=sp.read_bytes();assert H(b)==source['text_sha256'];full=b.decode();a,z=source['char_start'],source['char_end'];body=full[a:z];claimtxt=c['research_rationale'];j=claimtxt.lower().index('approval recommended');claimspan=[max(0,j-70),min(len(claimtxt),j+150)];isquote='quote' in flags[0]['code']
  if isquote:
   k=body.index('Approval recommended:');span=[a+k,min(z,a+k+130)];note='Supported exact quotation discrepancy: the claimed comma after Johnson replaces a full stop in the held source. Whitespace-only normalization does not erase punctuation. This does not itself imply a material legal error.'
   assert 'Hugh S. Johnson,' not in body and 'Hugh S. Johnson.' in body
  else:
   span=[a,z];note='Supported source-attribution discrepancy: the claim names Approval recommended lines, but the entire identified APP item has no such line. Recommendations in the recital are distinct from the nonexistent labeled line. No legal-effect conclusion follows.'
   assert re.search(r'approval\s+recommended',body,re.I) is None
  rows.append({'instrument_id':iid,'flag':flags[0],'classification':'supported_source_discrepancy','review_note':note,'claim_path':str(f.relative_to(ROOT)),'claim_file_sha256':H(raw),'claim_physical_record_sha256':H(line),'claim_field':'research_rationale','claim_field_span':claimspan,'claim_excerpt':claimtxt[claimspan[0]:claimspan[1]],'source_path':source['text_path'],'source_sha256':H(b),'verified_order_body_span':[a,z],'source_inspected_span':span,'source_excerpt':full[span[0]:span[1]],'flag_sha256':H(json.dumps(flags[0],sort_keys=True,separators=(',',':')).encode())})
 return {'scope':'Independent engineering comparison of all reported source flags against exact held sources; coordinator retains legal and final metric adjudication. Every flag still counts in original total-flagged filed metric.','source_module_sha256':codeh,'source_module_stable':codeh==H((ROOT/'jobs/geddes/source_checks.py').read_bytes()),'producer_check_sha256':H((p.parent/'source/CHECK.json').read_bytes()),'rows':rows,'supported_source_discrepancies':len(rows),'false_flags':0,'indeterminate':0,'start':start,'end':{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'monotonic':time.monotonic()},'tokens':None}
if __name__=='__main__':print(json.dumps(run(),indent=2))

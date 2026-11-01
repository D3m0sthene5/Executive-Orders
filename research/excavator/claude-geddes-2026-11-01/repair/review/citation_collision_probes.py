"""Independent identity/date/title collision mutations; synthetic publisher rows."""
from pathlib import Path
import hashlib,json,os,sys,tempfile,time
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT/'jobs/geddes'))
import citation_checks as C
sha=lambda b:hashlib.sha256(b).hexdigest()
def run():
 out=[]
 with tempfile.TemporaryDirectory() as tmp:
  r=Path(tmp);index=r/'jobs/app-executive-orders/output/INDEX.jsonl';index.parent.mkdir(parents=True);(index.parent/'texts').mkdir()
  p=r/'research/apollo/g01/packet/PACKET.json';p.parent.mkdir(parents=True);p.write_text('{}')
  listings=[{'instrument_id':'EO:7001','date':'1933-12-18','title':'Executive Order 7001—Amendment of Maritime Council Appointment Rules','path':'/documents/alpha'}, {'instrument_id':'EO:7001I','date':'1933-12-18','title':'Executive Order 7001-I—Code of Fair Competition for the Cast Iron Pipe Industry (Amendment Number I)','path':'/documents/beta'}]
  index.write_text('\n'.join(json.dumps(x) for x in listings)+'\n')
  leads=[]
  for name,text in [('alpha','Maritime Council Appointment Rules'),('beta','Cast Iron Pipe')]:
   (index.parent/'texts'/(name+'.txt')).write_text(text);leads.append({'file':'jobs/app-executive-orders/output/texts/'+name+'.txt','raw_sha256':sha(text.encode()),'match':text})
  (p.parent/'LOOKUPS.details.json').write_text(json.dumps({'members':{'EO:500':{'code_mentions':leads,'number_citations':[]}}}))
  d={'instrument_id':'EO:500','original_source_id':'ORIGINAL:EO:500','evidence':{'ORIGINAL:EO:500':{'source':{'page_or_item':'Code of Fair Competition Cast Iron Pipe'}}}}
  cases=[('wrong_suffix_bound_by_subject','A held later order, Executive Order 7001 of December 18, 1933, approves an Amendment for the Cast Iron Pipe Industry.',True),('correct_suffix','A held later order, Executive Order 7001-I of December 18, 1933, approves an Amendment for the Cast Iron Pipe Industry.',False),('correct_unsuffixed_collision','A held later order, Executive Order 7001 of December 18, 1933, amends Maritime Council Appointment Rules.',False),('unbound_wrong_date','A held later order, Executive Order 7001 of December 19, 1933, approves an Amendment for the Cast Iron Pipe Industry.',False)]
  for name,text,expected in cases:
   z=C.check({'research_rationale':text},d,r,p,{})
   hit=any(x['code']=='reasoning_order_identity_mismatch' for x in z['flags']);out.append({'name':name,'pass':hit==expected,'expected_mismatch_flag':expected,'output':z})
  cache={};claim={'research_rationale':cases[0][1]};old=C.check(claim,d,r,p,cache);st=index.stat();index.write_text(index.read_text().replace('EO:7001I','EO:7001J').replace('7001-I','7001-J'));os.utime(index,ns=(st.st_atime_ns,st.st_mtime_ns));changed=C.check(claim,d,r,p,cache)
  out.append({'name':'publisher_index_same_stat_mutation','pass':any('7001J' in x.get('detail','') for x in changed['flags']),'expected':'Changed publisher identity must invalidate cached metadata','output':changed})
 return out
if __name__=='__main__':
 before=sha((ROOT/'jobs/geddes/citation_checks.py').read_bytes());t=time.monotonic();r=run();print(json.dumps({'code_stable_during_run':before==sha((ROOT/'jobs/geddes/citation_checks.py').read_bytes()),'probes':r,'passed':sum(x['pass'] for x in r),'total':len(r),'module_sha256':sha((ROOT/'jobs/geddes/citation_checks.py').read_bytes()),'probe_sha256':sha(Path(__file__).read_bytes()),'elapsed_seconds':time.monotonic()-t,'scientific_approval':False},indent=2))

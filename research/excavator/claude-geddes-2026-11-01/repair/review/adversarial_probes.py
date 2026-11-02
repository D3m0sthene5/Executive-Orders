"""Independent synthetic engineering mutations, pre-final implementation freeze.
No scientific approval and no benchmark review labels are passed to Geddes.
"""
from pathlib import Path
import base64, copy, hashlib, importlib.util, json, os, sys, tempfile, time
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'jobs/geddes'))
import geddes as G

def sha(b): return hashlib.sha256(b).hexdigest()
def enc(s): return base64.urlsafe_b64encode(s.encode()).decode().rstrip('=')
def run():
 out=[]
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp)
  own='Executive Order 100\nBlue Marsh Refuge\nWhereas a public hearing has been held concerning the proposed refuge;\nI hereby establish the Blue Marsh Refuge.\nThis reservation shall be known as the Blue Marsh Refuge.\nFRANKLIN D. ROOSEVELT\nThe White House, January 1, 1937.\n'
  neighbor='Executive Order 101\nPayment of Claims\nI hereby order payment of every outstanding claim.\nFRANKLIN D. ROOSEVELT\n'
  full=own+neighbor; body='I hereby establish the Blue Marsh Refuge.'
  actor='Executive Order 7001-A\nRenaming the Blue Marsh Refuge\nThe Blue Marsh Refuge is renamed Green Marsh Refuge.\n'
  def src(path,text,page,iid,date):
   (root/path).write_text(text)
   return {'text_path':path,'text_sha256':sha(text.encode()),'page_or_item':page,'url':f'https://www.govinfo.gov/content/pkg/FR-{date}/pdf/FR-{date}.pdf','instrument_id':iid}
  s=src('own.txt',full,'Executive Order 100; 2 FR 63','EO:100','1937-01-03');a=src('actor.txt',actor,'Executive Order 7001-A; 3 FR 100','EO:7001A','1938-01-03')
  lo=full.index(body);hi=lo+len(body)
  er={'id':'ORIGINAL:EO:100','source':s,'text':full,'char_start':0,'char_end':len(full)}
  cr={'id':'CLAUSES:EO:100#main','source':s,'text':body,'char_start':lo,'char_end':hi,'scope_id':'EO:100#main'}
  ar={'id':'ACT:EO:100>EO:7001A','actor_id':'EO:7001A','actor_source':a,'source':a,'text':actor,'char_start':0,'char_end':len(actor)}
  d={'instrument_id':'EO:100','original_source_id':er['id'],'evidence':{r['id']:r for r in [er,cr,ar]},'clauses':[cr],'actor_provisions':[ar]}
  def cite(src,key,text,offset=0): return {**src,'evidence_id':enc(key),'evidence_id_encoding':'base64url-utf8','quote':text,'char_start':offset,'char_end':offset+len(text)}
  c={'instrument_id':'EO:100','original_representation':cite(s,er['id'],full),'operative_clauses':[{'scope_id':cr['scope_id'],'original_operative_text':body,'original_source':cite(s,cr['id'],body,lo),'judgment_reason':'The command ended through Executive Order 7001A.','first_end':{'actor':'EO:7001A','source':cite(a,ar['id'],actor)},'later_events':[]}],'later_source_search':[{'query_or_scope':'literal Blue Marsh Refuge'}]}
  p=root/'research/apollo/g01/packet/PACKET.json';p.parent.mkdir(parents=True)
  pkt={'held_text_file_pins':{'own.txt':s['text_sha256'],'actor.txt':a['text_sha256']}}
  p.write_text(json.dumps(pkt))
  def check(name,mutate,accept,expected):
   x=copy.deepcopy(c);dd=copy.deepcopy(d);mutate(x,dd)
   try:
    r=G.lint_one(1,x,{'EO:100':dd},root,p,{})
    passed=bool(accept(r));out.append({'name':name,'pass':passed,'expected':expected,'output':r})
   except Exception as e:out.append({'name':name,'pass':False,'error':repr(e),'expected':expected})
  code=lambda r,k:any(f['code']==k for f in r['flags'])
  absent=lambda r:not any('quot' in f['code'] or 'attributed' in f['code'] for f in r['flags'])
  check('legitimate_recital_outside_clause_envelope',lambda x,d:x.update(research_rationale='This order states "Whereas a public hearing has been held concerning the proposed refuge;"'),absent,'No false absence for recital within correct own-order boundaries')
  check('neighbor_quote_excluded',lambda x,d:x.update(research_rationale='This order states "I hereby order payment of every outstanding claim."'),lambda r:any('attributed' in f['code'] for f in r['flags']),'Neighbor quote cannot establish own text')
  def override(x,d):
   q='This reservation shall be known as the Blue Marsh Refuge.';start=full.index(q);end=start+len(q)
   x['claim_kit']={'inventory_overrides':[{'scope_id':'EO:100#corrected','source_id':er['id'],'char_start':start,'char_end':end,'reason':'Correct omitted OCR naming command.'}]}
   cl=x['operative_clauses'][0];cl.update(scope_id='EO:100#corrected',original_operative_text=q,original_source=cite(s,f'OVERRIDE:{er["id"]}#{start}-{end}',q,start))
  check('valid_inventory_override',override,absent,'Valid reconstructed override outside old clause envelope accepted')
  check('own_quote_cannot_be_supported_by_actor',lambda x,d:x.update(research_rationale='This order states "The Blue Marsh Refuge is renamed Green Marsh Refuge."'),lambda r:any('attributed' in f['code'] for f in r['flags']),'Actor wording cannot validate own quote')
  check('actor_quote_cannot_be_supported_by_own',lambda x,d:x['operative_clauses'][0]['first_end']['source'].update(quote=body),lambda r:code(r,'later_event_quote_not_in_cited_source') or code(r,'first_end_quote_not_in_cited_source'),'Own wording cannot validate actor quote')
  check('malformed_explicit_actor_span',lambda x,d:x['operative_clauses'][0]['first_end']['source'].update(char_start=-1),lambda r:any(('span' in json.dumps(g) or 'integrity' in json.dumps(g)) for g in r['coverage_gaps']+r['flags']),'Malformed explicit span must not silently fall back to full-file quote match')
  check('actual_actor_suffix_loss',lambda x,d:x['operative_clauses'][0]['first_end'].update(actor='EO:7001'),lambda r:any('suffix' in f['code'] or 'actor' in f['code'] for f in r['flags']),'Source-bound actor suffix mismatch flagged')
  check('signing_and_filing_not_publication',lambda x,d:x.update(research_rationale='The original was signed 1937-01-01 and filed 1937-01-02; the Federal Register issue is 1937-01-03 (2 FR 63).'),lambda r:not any(f['code'].startswith('fr_') for f in r['flags']),'Signing/filing dates are not issue-date errors')
  check('wrong_own_fr_page',lambda x,d:x.update(research_rationale='This order is printed on the Federal Register page (2 FR 73).'),lambda r:code(r,'fr_citation_mismatch'),'Explicit own FR page mismatch flagged')
  check('wrong_own_fr_issue',lambda x,d:x.update(research_rationale='The registered Federal Register original is issue of 1937-01-04 (2 FR 63).'),lambda r:code(r,'fr_issue_date_mismatch'),'Explicit own FR issue mismatch flagged')
  check('object_not_actor_in_later_events_sentence',lambda x,d:x['operative_clauses'][0].update(judgment_reason='The later event Executive Order 7001A revoked Executive Order 99.'),lambda r:not code(r,'later_instrument_named_without_event_source'),'Object EO99 must not require its own event')
  check('object_in_plural_later_events_context',lambda x,d:x['operative_clauses'][0].update(judgment_reason='Later events: Executive Order 7001A revoked Executive Order 99.'),lambda r:not code(r,'later_instrument_named_without_event_source'),'Plural event context does not turn EO99 object into actor')
  check('explicit_other_section_amendment',lambda x,d:x['operative_clauses'][0].update(judgment_reason='Later orders amended the parent Executive Order 99 but did not amend this clause: Executive Order 7002 changes section 9 and does not touch the words inserted here.'),lambda r:not code(r,'later_instrument_named_without_event_source'),'Explicit other-section amendment is not asserted event on tracked clause')
  check('historical_parent_amendment',lambda x,d:x['operative_clauses'][0].update(judgment_reason='This order amends Executive Order 99, as amended by Executive Order 77, by replacing section 2.'),lambda r:not code(r,'later_instrument_named_without_event_source'),'Historical parent description is not later event')
  check('missing_active_actor',lambda x,d:x['operative_clauses'][0].update(judgment_reason='Executive Order 7002 amended this order.'),lambda r:code(r,'later_instrument_named_without_event_source'),'Active actor EO7002 must be recorded')
  check('no_other_order_number_only',lambda x,d:x.update(research_rationale='No other held order names Blue Marsh Refuge.',later_source_search=[{'query_or_scope':'Executive Order 100'}]),lambda r:any(g['code']=='literal_name_search_missing' or (g['code']=='literal_name_search_performed' and 'blue marsh refuge' in g.get('names',[]) and g.get('negative_established') is False) for g in r['coverage_gaps']),'Number query alone does not prove literal-name coverage; linter may itself run and disclose the literal scan')
  # Persist a corpus cache across actual content and manifest mutations.
  name='Blue Marsh Refuge';extra=root/'extra.txt';original='Blue Marsh Refuge appears in this additional source.';extra.write_text(original)
  pkt['held_text_file_pins']['extra.txt']=sha(original.encode());p.write_text(json.dumps(pkt));cache={}
  initial=G.held_corpus_search(p,[name],root,cache);st=extra.stat();extra.write_text('X'*len(original));os.utime(extra,ns=(st.st_atime_ns,st.st_mtime_ns))
  changed=G.held_corpus_search(p,[name],root,cache)
  out.append({'name':'same_size_same_mtime_hash_mutation','pass':any(v.get('path')=='extra.txt' for v in changed[1]) and not any(v['path']=='extra.txt' for v in changed[0][name]),'expected':'Rehash content rather than trusting size+mtime cache','output':changed})
  extra.write_text(original);cache={};G.held_corpus_search(p,[name],root,cache)
  pkt['held_text_file_pins']['missing.txt']='0'*64;p.write_text(json.dumps(pkt))
  added=G.held_corpus_search(p,[name],root,cache)
  out.append({'name':'packet_pin_set_change','pass':any(v.get('path')=='missing.txt' for v in added[1]),'expected':'New missing corpus pin invalidates cache and appears in coverage','output':added})
  # Coverage count cannot substitute for identity-set equality.
  pkt['held_text_file_pins'].pop('missing.txt');p.write_text(json.dumps(pkt))
  (p.parent/'LOOKUPS.details.json').write_text(json.dumps({'corpus':{'coverage':{'scope':'all held text','discovered_count':len(pkt['held_text_file_pins']),'readable_count':len(pkt['held_text_file_pins'])}}}))
  x=copy.deepcopy(c);x['research_rationale']='No other held order names Blue Marsh Refuge.'
  r=G.lint_one(1,x,{'EO:100':d},root,p,{})
  out.append({'name':'numeric_coverage_not_identity_coverage','pass':not any(g.get('full_discovered_corpus_covered') for g in r['coverage_gaps']),'expected':'A matching numeric count is not exact full-corpus identity coverage','output':r})
  # Deterministic mutation between source verification and snapshot-state capture.
  if hasattr(G, 'NC'):
   module=G.NC;reader=module._read_inventory;mutated=[False];caught=False;error=None
   def change_after_verified(*args,**kwargs):
    result=reader(*args,**kwargs)
    if not mutated[0]:
     mutated[0]=True;extra.write_text(original+' CHANGED AFTER VERIFIED READ')
    return result
   module._read_inventory=change_after_verified
   try:
    with module.Snapshot(root) as snapshot_cache:
     module.scan_names(p,[name],root,snapshot_cache)
   except ValueError as e:caught=True;error=str(e)
   finally:module._read_inventory=reader
   out.append({'name':'snapshot_between_read_and_state_mutation','pass':caught,'expected':'Snapshot final check is bound to the bytes actually cached, not a later reread','mutation_performed':mutated[0],'error':error})
 return out
if __name__=='__main__':
 before={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted((ROOT/'jobs/geddes').glob('*.py'))};start=time.monotonic();r=run();pins={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted((ROOT/'jobs/geddes').glob('*.py'))};print(json.dumps({'code_stable_during_run':before==pins,'probes':r,'passed':sum(x['pass'] for x in r),'total':len(r),'code_pins':pins,'probe_sha256':sha(Path(__file__).read_bytes()),'elapsed_seconds':time.monotonic()-start,'scientific_approval':False,'tokens':None},indent=2))

"""Independent adversarial engineering probes; synthetic facts, never science."""
import base64,copy,hashlib,json,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'jobs/geddes'))
import geddes

def sha(b):return hashlib.sha256(b).hexdigest()
def enc(s):return base64.urlsafe_b64encode(s.encode()).decode().rstrip('=')

def run():
 results=[]
 with tempfile.TemporaryDirectory() as temp:
  repo=Path(temp); packet_dir=repo/'research/apollo/g01/packet';packet_dir.mkdir(parents=True)
  own='I hereby establish the Blue Marsh Refuge. This reservation shall be known as the Blue Marsh Refuge.'
  neighbor='I hereby order payment of every outstanding claim.'
  original=own+'\n'+neighbor
  actor='Executive Order 7001A. The Blue Marsh Refuge is renamed Green Marsh Refuge.'
  def source(path,text,page,url,iid):
   (repo/path).write_text(text)
   return {'text_path':path,'text_sha256':sha(text.encode()),'page_or_item':page,'url':url,'instrument_id':iid,'signing_date':'1937-01-01','filing_date':'1937-01-02'}
  s=source('own.txt',original,'2 FR 63','https://www.govinfo.gov/content/pkg/FR-1937-01-03/pdf/FR-1937-01-03.pdf','EO:100')
  a=source('actor.txt',actor,'Executive Order 7001A; 3 FR 100','https://www.govinfo.gov/content/pkg/FR-1938-01-03/pdf/FR-1938-01-03.pdf','EO:7001A')
  evidence={'ORIGINAL:EO:100':{'id':'ORIGINAL:EO:100','source':s,'text':original,'char_start':0,'char_end':len(original)},'CLAUSES:EO:100#whole':{'id':'CLAUSES:EO:100#whole','source':s,'text':own,'char_start':0,'char_end':len(own)},'ACT:EO:100>EO:7001A':{'id':'ACT:EO:100>EO:7001A','actor_id':'EO:7001A','actor_source':a,'source':a,'text':actor,'provision_text':actor,'char_start':0,'char_end':len(actor)}}
  d={'schema':'eo-claim-kit-dossier/v1','instrument_id':'EO:100','original_source_id':'ORIGINAL:EO:100','evidence':evidence,'clauses':[{'id':'CLAUSES:EO:100#whole','scope_id':'EO:100#whole','source':s,'text':own,'char_start':0,'char_end':len(own)}],'actor_provisions':[evidence['ACT:EO:100>EO:7001A']]}
  def cite(src,key,text):return {**src,'evidence_id':enc(key),'evidence_id_encoding':'base64url-utf8','quote':text,'char_start':0,'char_end':len(text)}
  c={'instrument_id':'EO:100','original_representation':cite(s,'ORIGINAL:EO:100',original),'operative_clauses':[{'scope_id':'EO:100#whole','original_operative_text':own,'original_source':cite(s,'CLAUSES:EO:100#whole',own),'first_end':{'actor':'EO:7001A','source':cite(a,'ACT:EO:100>EO:7001A',actor)},'judgment_reason':'The command ended through Executive Order 7001A.','later_events':[{'actor':'EO:7001A','source':cite(a,'ACT:EO:100>EO:7001A',actor)}]}],'later_source_search':[{'query_or_scope':'literal Blue Marsh Refuge search'}]}
  pkt={'dossiers':{'EO:100':d},'sources':{},'text_blocks':{},'shared_objects':{},'held_text_file_pins':{'own.txt':s['text_sha256'],'actor.txt':a['text_sha256']},'fingerprint':'fixture'}
  # decoder checks fingerprint of each dossier
  d['fingerprint']=geddes.batch.canonical_sha(d);(packet_dir/'PACKET.json').write_text(json.dumps(pkt))
  def probe(name,mutate,expect,check=None):
   x=copy.deepcopy(c); mutate(x)
   row=geddes.lint_one(1,x,{'EO:100':d},repo,packet_dir/'PACKET.json')
   codes=[v['code'] for v in row['flags']];gaps=[v['code'] for v in row['coverage_gaps']]
   passed=check(row) if check else any(expect in code for code in codes+gaps)
   results.append({'probe':name,'pass':bool(passed),'expected':expect,'codes':codes,'coverage':gaps,'output':row})
  probe('valid_cross_source_citations_and_quotes',lambda x:None,'no quote/citation/suffix flags',lambda r:not any(any(t in z['code'] for t in ('quot','citation','suffix','fr_date')) for z in r['flags']))
  probe('own_order_neighbor_contamination',lambda x:x.update(research_rationale='This order states "I hereby order payment of every outstanding claim."'),'attributed')
  probe('unquoted_attributed_recital',lambda x:x.update(research_rationale='This order directs the Secretary to pay all outstanding claims.'),'attributed')
  probe('acting_suffix_dropped',lambda x:x['operative_clauses'][0]['first_end'].update(actor='EO:7001'),'suffix')
  probe('wrong_original_operative_text',lambda x:x['operative_clauses'][0].update(original_operative_text='I hereby establish the Green Marsh Refuge.'),'quot')
  probe('wrong_cited_actor_quote',lambda x:x['operative_clauses'][0]['first_end']['source'].update(quote='The Blue Marsh Refuge is abolished.'),'quot')
  probe('case_changed_quote_is_not_verbatim',lambda x:x['operative_clauses'][0]['first_end']['source'].update(quote=actor.lower()),'quot')
  probe('wrong_quote_character_span',lambda x:x['operative_clauses'][0]['first_end']['source'].update(char_start=1),'quote/span mismatch',lambda r:any(any(t in z['code'] for t in ('quot','span')) for z in r['flags']+r['coverage_gaps']))
  probe('wrong_fr_page_on_actor_source',lambda x:x['operative_clauses'][0]['first_end']['source'].update(page_or_item='3 FR 101'),'fr_')
  probe('wrong_fr_issue_date_on_actor_source',lambda x:x['operative_clauses'][0]['first_end']['source'].update(page_or_item='3 FR 100; issue of 1938-01-04'),'fr_')
  probe('reasoning_named_unrecorded_instrument',lambda x:x['operative_clauses'][0].update(judgment_reason='Proclamation No. 2416 renamed the refuge.',later_events=[]),'named instrument missing later_events',lambda r:any('2416' in json.dumps(z) for z in r['flags']+r['coverage_gaps']))
  probe('recorded_later_instrument_missing_source',lambda x:x['operative_clauses'][0].update(judgment_reason='Proclamation No. 2416 renamed the refuge.',later_events=[{'actor':'PROC:2416'}]),'source')
  probe('number_only_search_insufficient_for_name_assertion',lambda x:x.update(research_rationale='No other held order names Blue Marsh Refuge.',later_source_search=[{'query_or_scope':'Executive Order 100'}]),'name')
  # A non-actor corpus file must not remain trusted after changing between calls.
  corpus_text='An unrelated order mentions Blue Marsh Refuge.'
  (repo/'corpus_only.txt').write_text(corpus_text)
  pkt['held_text_file_pins']['corpus_only.txt']=sha(corpus_text.encode())
  (packet_dir/'PACKET.json').write_text(json.dumps(pkt))
  def assert_name(x):x.update(research_rationale='No other held order names Blue Marsh Refuge.')
  probe('literal_name_search_initial_corpus_verified',assert_name,'verified literal-name corpus',lambda r:any(z.get('code')=='literal_name_corpus_search' and z.get('all_indexed_files_verified') for z in r['coverage_gaps']))
  (repo/'corpus_only.txt').write_text('Changed bytes: no longer a verified corpus source.')
  probe('literal_name_search_changed_corpus_not_cached',assert_name,'changed corpus rejected after prior call',lambda r:any(z.get('code')=='literal_name_corpus_search' and z.get('unavailable_files',0)>0 and z.get('all_indexed_files_verified') is False for z in r['coverage_gaps']))
  # Exercise missing/hash-mismatched cited actor sources and stale cache refusal.
  saved=(repo/'actor.txt').read_bytes()
  (repo/'actor.txt').write_text('Changed bytes after a prior lint call.')
  probe('actor_source_changed_after_prior_call',lambda x:None,'source integrity gap',lambda r:any(any(t in json.dumps(z).lower() for t in ('hash','integrity','sha256')) for z in r['coverage_gaps']))
  (repo/'actor.txt').write_bytes(saved)
  (repo/'actor.txt').unlink()
  probe('actor_source_missing_is_coverage',lambda x:None,'missing actor source coverage',lambda r:any(any(t in json.dumps(z).lower() for t in ('unavailable','missing')) for z in r['coverage_gaps']))
  (repo/'actor.txt').write_bytes(saved)
  probe('actor_object_sentence_does_not_promote_object',lambda x:x['operative_clauses'][0].update(judgment_reason='Executive Order 7001A revokes Executive Order 6000.'),'no actor promotion for object',lambda r:not any(z['code']=='later_instrument_named_without_event_source' and '6000' in z['detail'] for z in r['flags']))
  probe('explicit_later_sentence_does_not_promote_object',lambda x:x['operative_clauses'][0].update(judgment_reason='The later order Executive Order 7001A revokes Executive Order 6000.'),'no actor promotion for object in later sentence',lambda r:not any(z['code']=='later_instrument_named_without_event_source' and '6000' in z['detail'] for z in r['flags']))
  probe('outside_envelope_quote_is_qualified_scope_flag',lambda x:x.update(research_rationale='This order states "I hereby order payment of every outstanding claim."'),'single qualified advisory scope flag, not whole-order absence',lambda r:len([z for z in r['flags'] if z['code']=='attributed_phrase_absent'])==1 and all('may be a recital or neighboring order' in z['detail'] for z in r['flags'] if z['code']=='attributed_phrase_absent') and not any(z['code']=='attributed_quote_outside_target_envelope' for z in r['coverage_gaps']))
  results.append({'probe':'probe_source_hash','path':str(Path(__file__).relative_to(ROOT)),'sha256':sha(Path(__file__).read_bytes())})
 return results
if __name__=='__main__':
 start=time.monotonic();results=run();print(json.dumps({'results':results,'wall_seconds':time.monotonic()-start,'code_sha256':sha((ROOT/'jobs/geddes/geddes.py').read_bytes()),'tokens':None,'scientific_review':False},indent=2))

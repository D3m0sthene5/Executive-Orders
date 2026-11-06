"""Mechanically joins discovery metadata only. Usage: python crosswalk.py REPO OUTPUT."""
import csv,hashlib,io,json,os,re,subprocess,sys
from pathlib import Path
from collections import Counter,defaultdict
from urllib.parse import urlsplit
PIN='51914da4b58fb425b710e070ef10c20da6f119a4'
CUT='2026-10-14'
repo,out=sys.argv[1],Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
def git(*args):return subprocess.check_output(['git','-C',repo,*args])
inputs={}
def table(p):
 b=git('show',PIN+':'+p);inputs[p]=hashlib.sha256(b).hexdigest();s=b.decode('utf-8-sig')
 if p.endswith('.csv'):return list(csv.DictReader(io.StringIO(s)))
 return (json.loads(x) for x in s.splitlines())
def tbl(job,fn):return table('jobs/'+job+'/output/'+fn)
def keyed(a,key='instrument_id'):
 d={x[key]:x for x in a};assert len(d)==len(a);return d
def joined(z):return '|'.join(sorted(set(str(x) for x in z if x not in ('',None))))
def dump(n,rows):
 with (out/n).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def cnt(a,k):return dict(sorted(Counter(x[k] for x in a).items()))
def tot(a,k):return sum(bool(x[k]) for x in a)
tree=git('ls-tree','-r','--name-only','-z',PIN);files=set(x.decode() for x in tree.split(b'\0') if x); inputs['git tree']=git('rev-parse',PIN+'^{tree}').decode().strip()
ready=keyed(tbl('readiness-tracker','READINESS_BY_ORDER.csv')); idc=keyed([r for r in table('research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv') if r['included_in_bibliography']=='1'],'id')
reg=keyed(tbl('domesday-register','REGISTER.csv'))
def obj(p):
 b=git('show',PIN+':'+p);inputs[p]=hashlib.sha256(b).hexdigest();return json.loads(b)
locks=obj('research/readiness/CLAIM_KIT_LOCK.json')['orders']
frozen={r['instrument_id'] for r in obj('research/production/claim-kit-pilot-2026-10-18/FREEZE_MANIFEST.json')['accepted']}
# Workpaper-path index only. Never open prior producer decisions, sample pages or text.
work=defaultdict(set)
for path in sorted(files):
 m=re.fullmatch(r'(research/(?:excavator|production)/.+?)/decisions/EO_(\d+[a-zA-Z]?)\.json',path)
 if m:work['EO:'+m[2].upper()].add(path)
def overlay(i):
 return dict(kit_lock_agent=locks.get(i,{}).get('agent',''),tracker_claim_present=ready[i]['claim_present'],frozen_20261018_proposal=int(i in frozen),prior_named_decision_paths=joined(work[i]))

assert set(ready)==set(idc)==set(reg) and len(ready)==14972 and sum(x['ready_for_human_review']=='yes' for x in ready.values())==1331
def frame(which):
 def ok(i):
  x=ready[i];date=idc[i]['date_effective'];y=date[:4]
  return x['ready_for_human_review']=='no' and not x['provisional_status'] and ((which=='H' and y.isdigit() and '1907'<=y<='1936' and x['text_evidence_tier']=='missing') or (which=='L' and y.isdigit() and y>='1937' and date<=CUT and x['text_evidence_tier']=='original_supported'))
 return sorted([i for i in ready if ok(i)])
H,L=frame('H'),frame('L')
assert (len(H),len(L))==(4332,3908)
pq=keyed(tbl('pinakes-proquest-ingest','ORDERS.csv')); hin=tbl('hathi-gpo-orders','PAGE_CHECK_QUEUE.csv')
gaps=keyed(table('research/pre-1937-sources/GAP_ROUTES.csv'),'id'); volumes=tbl('hathi-gpo-orders','VOLUMES.csv')
det=defaultdict(list); tran=defaultdict(list); ext=defaultdict(list);wpa=defaultdict(list); csc=defaultdict(list)
def add(i,kind,path,locator,sha='',basis=''):
 det[i].append(dict(instrument_id=i,channel=kind,path=path,locator=locator,source_reported_sha256=sha,basis=basis))
for r in table('jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv'):wpa[r['id']].append(r)
for r in tbl('csc-annual-reports','CITATION_RESULTS.csv'):
 if r['pdf_page']:csc[r['id']].append(r['package_id']+'#pdf_page='+r['pdf_page']+';'+r['confidence'])
for i,r in pq.items():
 path=r['folder']+'/'+r['file']
 if path in files and r['sha256'] and r['in_census']=='yes':add(i,'pinakes_item',path,'order-level file; '+r['pages']+' recorded pages',r['sha256'],'Pinakes chosen file')
# Filenames independently from inventory: anchored number, suffix (preserved), optional copy/page decoration. Includes year to identify conflicting labels.
named=defaultdict(list)
pat=re.compile(r'^(?:(?:PT\d+-)?(\d{4})[-_])?EO[-_ ](\d+)(?:[-_]?([A-Za-z]))?(?:(?:_From_\d+_to_\d+)|(?: \(\d+\)))*\.(?:pdf|djvu|tiff?|png|jpe?g)$',re.I)
for f in sorted(files):
 m=pat.fullmatch(f.rsplit('/',1)[-1])
 if m:
  y,n,s=m.groups();i='EO:'+str(int(n))+(s or '').upper()
  if i in idc and (not y or idc[i]['date_effective'][:4]==y):
   named[i].append(f);add(i,'exact_filename',f,'filename only','','year (if present), number and suffix match')
book='jobs/hathi-gpo-orders/output/books/'
for r in hin:
 p=book+r['volume']
 if p in files:add(r['instrument_id'],'gpo_number_hit',p,r['candidate_scan_pages'],'','Number occurrence only; possible reference, not caption')
for r in tbl('hathi-gpo-orders','SOURCES.jsonl'):
 for i in r['instrument_ids']:
  rt=r['route'];p=book+(r['url'].rsplit('/',1)[-1] if rt=='govinfo_fr' else r['volume'])
  if rt in ('commons_gpo_ocr','govinfo_fr','wikisource_scan_pages') and p in files:
   add(i,'gpo_held_pages',p,r['page_or_item'],r['sha256'] if rt!='wikisource_scan_pages' else '',rt)
  else:ext[i].append(r['page_url'] if r.get('page_url') else r['url'])
for r in tbl('cotton-capture-custody','SOURCES.jsonl'):
 p='jobs/cotton-capture-custody/output/'+r['cache_path']
 if p not in files:continue
 url=urlsplit(r['url'])
 if url.hostname=='commons.wikimedia.org':
  b=git('show',PIN+':'+p)
  # File signatures only, no page image examination. Never infer media from URL or .bin.
  if b.startswith(b'AT&TFORM') and b[12:16] in (b'DJVM',b'DJVU'):
   assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
   inputs[p]=r['sha256']
   for i in r['instrument_ids']:add(i,'cotton_djvu_record',p,'volume attached to ID; no new page verification',r['sha256'],'Cotton source row + file signature')
   volume=book+url.path.rsplit(':',1)[-1]
   if volume in files and hashlib.sha256(git('show',PIN+':'+volume)).hexdigest()==r['sha256']:
    inputs[volume]=r['sha256']
    for i,rows in det.items():
     for v in list(rows):
      if v['path']==volume:
       add(i,'cotton_same_volume_existing_locator',p,v['locator'],r['sha256'],'byte-identical to '+volume+'; same locator/evidence, not independent')
 else:
  for i in r['instrument_ids']:tran[i].append('cotton:'+r['url'])
for r in tbl('fr-pages','SOURCES.jsonl'):
 i=r.get('printed_instrument_id');p='jobs/fr-pages/output/'+r.get('cache_path','')
 if p in files:add(i,'fr_printed_identity',p,r['page_or_item'],r['sha256'],'printed_instrument_id only; wanted IDs excluded')
hist=[]
for i in H:
 r=reg[i];g=gaps.get(i,{});v=[]
 num=re.fullmatch(r'EO:(\d+)[A-Za-z]?',i)
 for vol in volumes:
  lm=re.fullmatch(r'(\d+)-(\d+)',vol['order_range'])
  if num and lm and int(lm[1])<=int(num[1])<=int(lm[2]):v.append(vol['volume'])
 refs=joined(z['citations_joined'] for z in wpa[i]);h=joined(z['channel'] for z in det[i])
 collection=g.get('candidate_public_source','');state='outside_survey' if not g else ('survey_no_named_public_compilation' if collection=='none' else 'survey_named_public_compilation')
 text=r['transcription_sources']; official=r['official_sources'];loc=joined(ext[i]);ct=joined(tran[i]);c_loc=joined(csc[i]);wparef=bool(wpa[i])
 tier='held_item_or_page_candidate' if h else ('representation_or_index_or_citation_without_identified_held_scan' if text or ct or official or refs or wparef or loc or c_loc else 'no_specific_witness_matched')
 hist.append(dict(instrument_id=i,census_date=idc[i]['date_effective'],partition=tier,held_channels=h,exact_filename_count=len(named[i]),pinakes_file=pq.get(i,{}).get('file',''),pinakes_filename_census_year_conflict=int(bool(pq.get(i,{}).get('year')) and pq[i]['year']!=idc[i]['date_effective'][:4]),register_best_held=r['best_held'],official_job_without_implied_page=official,register_transcriptions=text,cotton_web_capture=ct,wpa_rows=len(wpa[i]),wpa_citations=refs,csc_page_candidate=c_loc,external_scan_locator=loc,range_only_possible_volumes=joined(v),collection_survey=state,survey_collection_value=collection,survey_wpa_route=g.get('wpa_route',''),lewis_status=r['lewis_status'],lewis_route=r['lewis_route'],**overlay(i)))
dump('historical.csv',hist);dump('historical_held_candidates.csv',[v for i in H for v in sorted(det[i],key=lambda r:tuple(r.values()))])
cat=keyed(tbl('later-events','CATALOG_INDEX.csv'),'id')
nam=keyed(tbl('namier','SEARCH_COVERAGE.csv')); own={}; kitactors={};law={};kitpresent=set()
for r in tbl('claim-kit','STATUS_LEADS.jsonl'):
 i=r['instrument_id'];kitpresent.add(i);own[i]=joined(o['kind'] for o in r['own_terms']);kitactors[i]=joined(r['lead_actor_ids']);law[i]=len(r['current_law_leads'])
# Strict chronological candidates only: actual catalog actor signing date and target signing date; if unavailable use full census day, never a year-only comparison or source-as-of.
def signed(i):
 s=cat.get(i,{}).get('signing_date') or idc.get(i,{}).get('date_effective','')
 return s if re.fullmatch(r'\d{4}-\d{2}-\d{2}',s or '') else ''
endtypes={'revocation','supersession','rescission','supersession_or_revocation'}
strong=defaultdict(list); other=defaultdict(list); cross=defaultdict(list);ungated=defaultdict(list);strict15=defaultdict(list);edgeout=[]
LS=set(L)
for r in tbl('later-events','EDGES.csv'):
 t,a=r['target_id'],r['acting_id']
 if t not in LS:continue
 m=r['mechanism'];d=signed(a);td=signed(t)
 if not a or a==t or not d or not td or not td<d<=CUT:ungated[t].append(r['edge_id']);continue
 if m=='cross_reference':cross[t].append(r['edge_id']);continue
 obvious=m in endtypes and not r['qualifier'] and not r['date_flags']
 if obvious:strong[t].append(r['edge_id'])
 else:other[t].append(r['edge_id'])
 edgeout.append({k:r[k] for k in ('target_id','acting_id','edge_id','mechanism','qualifier','date_flags','evidence_type','source_id','source_url','source_sha256','page_or_item')}|dict(target_signing=td,actor_signing=d,priority='unqualified_end_word' if obvious else 'other_or_qualified_relation'))
for r in table('research/stage15/AUDIT/STAGE15_CHRONOLOGY_GATED_CANDIDATE_RELATIONS.csv'):
 t,a=r['candidate_predecessor'],r['actor']
 if t in LS and signed(t) and signed(a) and signed(t)<signed(a)<=CUT:strict15[t].append(r['edge_id'])
# Predefined title metadata only. A personnel/name search or board-creation title does not establish occurrence or terminal effect.
board=re.compile(r'\b(?:creat(?:ing|ion of)|establish(?:ing|ment of)|appoint(?:ing|ment of))\s+(?:an?\s+)?(?:emergency|board of inquiry|board to investigate|board of investigation)',re.I)
closing=re.compile(r'\b(?:clos(?:ing|ure) of|closing)\b.*\b(?:government|federal|executive departments|departments and agencies)\b',re.I)
modern=[]
for i in L:
 n=i in nam;b=bool(board.search(reg[i]['title']));c=bool(closing.search(reg[i]['title'])); shot=joined([('namier_personnel_subject' if n else ''),('board_creation_title' if b else ''),('closing_title' if c else '')]);term=own.get(i,'')
 order=('unqualified_end_word_relation' if strong[i] else 'other_or_qualified_later_relation' if other[i] else 'one_action_subject_candidate' if shot else 'own_term_lead' if term else 'other_indexed_lead' if strict15[i] or cross[i] or ungated[i] or kitactors.get(i,'') or law.get(i,0) else 'no_lead_in_joined_fields')
 modern.append(dict(instrument_id=i,census_date=idc[i]['date_effective'],priority_partition=order,unqualified_end_word_edges=joined(strong[i]),other_or_qualified_relation_edges=joined(other[i]),crossreference_edges=joined(cross[i]),unresolved_or_nonstrict_chronology_edges=joined(ungated[i]),stage15_chronological_edges=joined(strict15[i]),one_action_subjects=shot,namier_name_search_covered=nam.get(i,{}).get('covered',''),own_term_kinds=term,claimkit_actor_ids_unadjudicated=kitactors.get(i,''),claimkit_current_law_lead_count=law.get(i,0),claimkit_record_present=int(i in kitpresent),**overlay(i)))
dump('modern.csv',modern);dump('modern_chronological_edges.csv',edgeout)
stats={'pin':PIN,'scientific_cutoff':CUT,'inputs':inputs,'historical':{'population':len(hist),'partition':cnt(hist,'partition'),'register_classes':cnt(hist,'register_best_held'),'collection_survey':cnt(hist,'collection_survey'),'held_channel_membership':{k:sum(any(v['channel']==k for v in det[i]) for i in H) for k in sorted({v['channel'] for i in H for v in det[i]})},'independent_flags':{k:tot(hist,k) for k in ['exact_filename_count','pinakes_filename_census_year_conflict','cotton_web_capture','wpa_rows','wpa_citations','range_only_possible_volumes','csc_page_candidate','external_scan_locator','official_job_without_implied_page','register_transcriptions']},'held_vs_survey':dict(sorted(Counter(x['partition']+' :: '+x['collection_survey'] for x in hist).items()))},'modern':{'population':len(modern),'priority_partition':cnt(modern,'priority_partition'),'independent_flags':{k:tot(modern,k) for k in modern[0] if k not in ['instrument_id','census_date','priority_partition','namier_name_search_covered','tracker_claim_present']},'one_action_sources':cnt(modern,'one_action_subjects'),'edge_rows':len(edgeout)}}
for label,rows in [('historical',hist),('modern',modern)]:
 stats[label]['dispatch_overlays']={'kit_locks':tot(rows,'kit_lock_agent'),'tracker_claim_present_yes':sum(x['tracker_claim_present']=='yes' for x in rows),'frozen_older_proposal':tot(rows,'frozen_20261018_proposal'),'prior_decision_named_path':tot(rows,'prior_named_decision_paths')}
status=defaultdict(set)
for r in edgeout:
 if r['priority']=='unqualified_end_word':
  t=r['evidence_type'];status[r['target_id']].add('official_text_feed' if t in {'order_text_fr_originals','order_text_govinfo_pdf','order_text_opus_official_copy'} else 'other_text_feed' if t.startswith('order_text') else 'editorial_feed')
stats['modern']['unqualified_end_word_source_combinations']=dict(sorted(Counter(joined(v) for v in status.values()).items()))
stats['historical']['nonheld_register_and_wpa_flags']={'register_transcription':sum(bool(x['register_transcriptions']) for x in hist if not x['held_channels']), 'wpa_row_no_register_transcription':sum(bool(x['wpa_rows']) and not x['register_transcriptions'] for x in hist if not x['held_channels'])}
(out/'summary.json').write_text(json.dumps(stats,sort_keys=True,indent=2)+'\n')

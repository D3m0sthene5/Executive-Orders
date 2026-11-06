"""Read-only original-source crosswalk. python fr_raw.py REPO OUTPUT (with prior modern.csv)."""
import csv,json,io,re,hashlib,subprocess,sys
from pathlib import Path
from collections import defaultdict,Counter
P='51914da4b58fb425b710e070ef10c20da6f119a4'
repo,out=sys.argv[1],Path(sys.argv[2]); inp={}
def git(*a):return subprocess.check_output(['git','-C',repo,*a])
def read(p):
 b=git('show',P+':'+p); inp[p]=hashlib.sha256(b).hexdigest(); return b
def js(p):return [json.loads(x) for x in read(p).splitlines() if x.strip()]
def table(p):return list(csv.DictReader(io.StringIO(read(p).decode('utf-8-sig'))))
def write(n,a):
 with (out/n).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(a[0]),lineterminator='\n');w.writeheader();w.writerows(a)
def joined(a):return '|'.join(sorted(set(a)))
census={x['id']:x['date_effective'] for x in table('research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv') if x['included_in_bibliography']=='1'}
I={x['instrument_id'] for x in table('jobs/readiness-tracker/output/READINESS_BY_ORDER.csv') if x['ready_for_human_review']=='no' and not x['provisional_status'] and x['text_evidence_tier']=='original_supported' and re.match(r'^\d{4}',census[x['instrument_id']]) and '1937'<=census[x['instrument_id']][:4] and census[x['instrument_id']]<='2026-10-14'}
assert len(I)==3908
selected={}; shas={}
for r in js('jobs/fr-originals/output/SOURCES.jsonl'):
 for i in set(r['instrument_ids'])&I:
  assert i not in selected; selected[i]=r
assert set(selected)==I and len({r['url'] for r in selected.values()})==len({r['sha256'] for r in selected.values()})==3179
tree={}
for line in git('ls-tree','-rz',P).split(b'\0'):
 if not line:continue
 fields,name=line.decode().split('\t');tree[name]=fields.split()[2]
native='jobs/astra-source-retention/output/'
catalog=defaultdict(list)
for r in js(native+'SOURCES.jsonl'):
 if r.get('cache_path'):catalog[r['sha256']].append(native+r['cache_path'])
bysha=defaultdict(list)
for path,obj in tree.items():
 mt=re.search(r'/([0-9a-f]{64})(?:\.(?:pdf|bin))?$',path)
 if mt:bysha[mt[1]].append(path)
que={(q.get('instrument_id'),u) for q in js('research/readiness/FETCH_QUEUE.jsonl') for u in q.get('urls',[]) if isinstance(u,str)}
reqp='jobs/astra-source-retention/REQUESTS.json';requests={(i,r['url']) for r in json.loads(read(reqp)) for i in r['instrument_ids']}
rows=[];results=defaultdict(list)
for i,r in sorted(selected.items()):
 h,u=r['sha256'],r['url'];shas[h]=u
 nativepath=native+'pdf/'+h+'.pdf'
 other=sorted(p for p in bysha[h] if p!=nativepath)
 pages=re.fullmatch(r'(.+), PDF pages (\d+)-(\d+)',r['page_or_item']);assert pages and int(pages[2])<=int(pages[3])
 b=dict(instrument_id=i,source_id=r['source_id'],url=u,requested_url=r['requested_url'],sha256=h,source_bytes=r['bytes'],citation=pages[1],pdf_first_page=pages[2],pdf_last_page=pages[3],page_or_item=r['page_or_item'],source_locator_confidence=r['location_confidence'],source_route=r['route'],source_capture_date=r['retrieved_utc'],fr_job_text_path=r['text_path'],fr_job_cache_path=r.get('cache_path') or '',fr_job_cache_path_tracked=int('jobs/fr-originals/output/'+str(r.get('cache_path') or '') in tree),native_retention_pdf_path=nativepath if nativepath in tree else '',native_pdf_git_blob_id=tree.get(nativepath,''),native_retention_catalog_same_hash=int(nativepath in catalog[h]),other_sha_named_paths=joined(other),other_sha_named_git_blobs=joined(tree[p] for p in other),queued_exact_resolved_url=int((i,u) in que),queued_requested_url=int((i,r['requested_url']) in que),native_active_manifest_resolved_url=int((i,u) in requests),raw_state='native_pdf_filename_present' if nativepath in tree else 'other_sha_named_file_only' if other else 'no_matched_sha_named_file')
 rows.append(b);results[h].append(b)
write('fr_original_raw.csv',rows)
expected={}
for h,rr in results.items():
 assert len({x['url'] for x in rr})==1
 expected[h]=dict(sha256=h,url=rr[0]['url'],instrument_count=len(rr),instrument_ids=joined(x['instrument_id'] for x in rr),pdf_page_intervals=joined(x['pdf_first_page']+'-'+x['pdf_last_page'] for x in rr),raw_state=rr[0]['raw_state'],native_pdf_path=rr[0]['native_retention_pdf_path'],other_sha_named_paths=rr[0]['other_sha_named_paths'])
write('fr_original_raw_by_pdf.csv',list(expected.values()))
summary=dict(pin=P,cutoff='2026-10-14',inputs=inp,pinned_tree=git('rev-parse',P+'^{tree}').decode().strip(),orders=len(rows),exact_selected_fr_source_rows=len(selected),unique_pdf_sources=len(expected),raw_state_orders=dict(Counter(r['raw_state'] for r in rows)),raw_state_pdf_sources=dict(Counter(r['raw_state'] for r in expected.values())),native_records_with_raw_path=sum(bool(r['native_retention_pdf_path']) and r['native_retention_catalog_same_hash'] for r in rows),fr_job_reported_cache_paths_tracked=sum(r['fr_job_cache_path_tracked'] for r in rows),same_hash_other_raw_paths_including_native_overlap=sum(bool(r['other_sha_named_paths']) for r in rows),locator_confidence=dict(Counter(r['source_locator_confidence'] for r in rows)),resolved_url_in_native_fetch_queue=sum(r['queued_exact_resolved_url'] for r in rows),requested_url_in_native_fetch_queue=sum(r['queued_requested_url'] for r in rows),resolved_url_in_active_native_manifest=sum(r['native_active_manifest_resolved_url'] for r in rows),without_native_path_but_in_exact_resolved_queue=sum(not r['native_retention_pdf_path'] and r['queued_exact_resolved_url'] for r in rows),scope='Measured path identity in pinned Git tree; source hash to filename match, Git blob ID, and native catalog corroboration. No new PDF download, byte-by-byte SHA audit or page examination. Other names, archives, caches, network availability and alternate versions not tested.')
(out/'fr_raw_summary.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ('inputs','scope')}))

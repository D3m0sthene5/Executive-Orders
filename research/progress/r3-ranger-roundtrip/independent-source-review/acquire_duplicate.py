import sys,json,re,hashlib,datetime,time
from pathlib import Path
ROOT=Path.cwd();OUT=ROOT/'research/progress/r3-ranger-roundtrip/independent-source-review';sys.path.insert(0,str(ROOT/'jobs/_lib'));from fetch_pool import FetchPool
text=(ROOT/'jobs/early-ranger-workbench/output/EARLY_SOURCE_REVIEW_WORKBENCH.html').read_text();db=json.loads(re.search(r'<script id="payload" type="application/json">(.*?)</script>',text,re.S).group(1));c=next(c for c in db['cases'] if c['id']=='mjm022917')
urls=[x['url'] for x in c['loc_source_resource_candidates'] if '/master/' in x['url'] and x['url'].endswith('.jpg')];assert len(urls)==8
pool=FetchPool(OUT/'cache',workers=4,per_host=3,max_bytes=5_000_000,timeout=25)
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
def one(url):
 n=urls.index(url)+1;row={'url':url,'page':n,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  r=pool.fetch(url);raw=r.pop('body');assert raw.startswith(b'\xff\xd8\xff') and raw.rstrip().endswith(b'\xff\xd9');p=OUT/'mjm022917'/f'page_{n:02}.jpg';p.parent.mkdir(exist_ok=True);p.write_bytes(raw);row.update(r,path=str(p.relative_to(ROOT)),state='acquired')
 except Exception as e:row.update(state='failed',error=type(e).__name__+': '+str(e))
 return row
rows=pool.map(one,urls);(OUT/'DUPLICATE_ACQUISITION.json').write_text(json.dumps({'started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_workbench_sha256':hashlib.sha256(text.encode()).hexdigest(),'rows':rows,'stats':pool.cache_stats()},indent=2)+'\n');print(json.dumps(rows,indent=2))

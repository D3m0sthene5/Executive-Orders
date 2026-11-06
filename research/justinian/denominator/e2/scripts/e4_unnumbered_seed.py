import csv, re, sys, collections
R='/home/user/Executive-Orders/'
OUT=sys.argv[1]
w=list(csv.DictReader(open(R+'jobs/x1-class-engine/data/WPA_UNNUMBERED_ENTRIES.csv',encoding='utf-8')))
cl=list(csv.DictReader(open(R+'jobs/census-completeness/output/CLUSTERS.csv',encoding='utf-8')))
by_member={}
for c in cl:
    for m in c['members'].split('|'): by_member[m]=c
census=list(csv.DictReader(open(R+'research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv',encoding='utf-8')))
un_ids=[r['id'] for r in census if r['id'].startswith('EO:UN')]
nara={r['instrument_id']:r['reference_date'] for r in csv.DictReader(open(R+'research/stage13/CENSUS/NARA_UNNUMBERED_EDITORIAL_DATES_18.csv',encoding='utf-8'))}
bydate=collections.defaultdict(list)
for k,v in nara.items(): bydate[v].append(k)
M={'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12}
def iso(y,d):
    m=re.match(r'\s*([A-Za-z]{3})[a-z]*\.?\s*(\d{1,2})?',d or '')
    if not m or not y: return y or ''
    mo=M.get(m.group(1).lower())
    if not mo: return y
    return '%s-%02d-%02d'%(y,mo,int(m.group(2))) if m.group(2) else '%s-%02d'%(y,mo)
rows=[];stats=collections.Counter()
for r in w:
    mid='LORD:U:%04d'%int(r['seq'])
    c=by_member.get(mid)
    cid=c['cluster_id'] if c else 'not found (no pre-1900 cluster; year %s)'%r['year']
    nums=[m for m in c['members'].split('|') if m.startswith('EO:')] if c else []
    d=iso(r['year'],r['date'])
    leads=bydate.get(d,[])
    linked=[]
    if nums: linked+=nums
    stats['cluster']+= bool(c); stats['numbered_link']+=bool(nums); stats['date_lead']+=bool(leads)
    rows.append({'seed_id':'CU:%s'%r['seq'],'date':d,'page':r['page'],'text':' '.join(r['summary'].split())[:300],
      'census_ids_linked':'|'.join(linked),'census_date_only_leads':'|'.join(leads),
      'completeness_cluster_id':cid,'cluster_n_sources':c['n_sources'] if c else '','cluster_sources':c['sources'] if c else '',
      'lord_mention_id':mid if c else '','source_row':'jobs/x1-class-engine/data/WPA_UNNUMBERED_ENTRIES.csv seq=%s'%r['seq']})
with open(OUT+'/UNNUMBERED_SEED.csv','w',newline='',encoding='utf-8') as f:
    wr=csv.DictWriter(f,fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
print(len(rows),dict(stats),len(un_ids),len(set(c['cluster_id'] for c in cl)))
# census LORD1944 id
print([r['id'] for r in census if 'LORD1944' in r['id']])

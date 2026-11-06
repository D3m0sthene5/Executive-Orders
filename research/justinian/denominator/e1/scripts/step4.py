import csv,json,collections,re
R='/home/user/Executive-Orders/'
m=json.load(open('scripts/_missing.json')); wm,cm=set(m['wm']),set(m['cm'])
rec={r['number']:r for r in csv.DictReader(open('RECOVERED_IDENTITIES.csv'))}
per=list(csv.DictReader(open('WPA_CENSUS_PER_INTEGER.csv')))
c=collections.Counter((int(r['in_wpa_parse']),int(r['in_census_base'])) for r in per)
ng=list(csv.DictReader(open(R+'jobs/clark-discovery/output/NUMBER_GAPS.csv',encoding='utf-8')))
ngn={int(r['instrument_id'][3:]) for r in ng if re.fullmatch(r'EO:\d+',r['instrument_id'])}
w=csv.writer(open('WPA_CENSUS_CROSSTAB.csv','w',newline=''))
w.writerow(['section','in_wpa_parse','in_census_base','count','numbers_or_note'])
lab={(1,1):'both',(1,0):'wpa_only',(0,1):'census_only',(0,0):'neither'}
for k in [(1,1),(1,0),(0,1),(0,0)]:
    nums=[int(r['number']) for r in per if (int(r['in_wpa_parse']),int(r['in_census_base']))==k]
    w.writerow(['summary_1_to_8030_%s'%lab[k],k[0],k[1],c[k],'' if k==(1,1) else ' '.join(map(str,nums))])
w.writerow(['check_vs_clark_NUMBER_GAPS.csv','','',len(ngn),'census-absent integers=%d; in clark NUMBER_GAPS=%d; census-absent not in clark: %s'%(len(cm),len(ngn&cm),sorted(cm-ngn))])
for r in per:
    a,b=int(r['in_wpa_parse']),int(r['in_census_base'])
    if (a,b)!=(1,1):
        n=r['number']; x=rec.get(n)
        w.writerow(['detail_'+lab[(a,b)],a,b,1,'%s: %s'%(n,(x['notes'].split(';')[0] if x else 'wpa_row_present'))])

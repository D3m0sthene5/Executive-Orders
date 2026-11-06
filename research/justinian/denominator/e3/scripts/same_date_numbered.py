import sys,csv,json
sys.path.insert(0,'/home/user/Executive-Orders/jobs/_lib')
import eo_identity as e
d=e.load_dates('/home/user/Executive-Orders')
r=list(csv.DictReader(open('/home/user/Executive-Orders/jobs/ofr-codification-1989/output/UNNUMBERED_ROWS.csv')))
res={}
for x in r:
    res[x['date']]=sorted(k+'|'+v['title'][:70]+'|'+v['date_source'] for k,v in d.items() if v['date']==x['date'] and not k.startswith('EO:UN'))
json.dump(res,open(sys.argv[1],'w'),indent=1)
for k,v in res.items(): print(k,len(v),v[:4])

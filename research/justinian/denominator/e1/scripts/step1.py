import csv,re,json,sys
R='/home/user/Executive-Orders/'
wpa=list(csv.DictReader(open(R+'jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv',encoding='utf-8')))
cen=list(csv.DictReader(open(R+'research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv',encoding='utf-8')))
W=sorted({int(r['number']) for r in wpa})
C=set()
for r in cen:
    m=re.fullmatch(r'EO:(\d+)[A-Z½]?(-\d+)?',r['id'])
    if m: C.add(int(m.group(1)))
mx=max(W); print('wpa rows',len(wpa),'distinct',len(W),'max',mx,'census bases',len(C),'max',max(C))
Ws=set(W)
wm=[n for n in range(1,mx+1) if n not in Ws]
cm=[n for n in range(1,mx+1) if n not in C]
print('wpa missing',len(wm),wm); print('census missing <=mx',len(cm))
print('wpa present census absent',sorted(Ws-C))
print('census present wpa absent',sorted((C&set(range(1,mx+1)))-Ws))
print('census >mx',sorted(n for n in C if n>mx)[:20])
rows=[]
for n in range(1,mx+1):
    rows.append((n,int(n in Ws),int(n in C)))
with open(sys.argv[1],'w',newline='') as f:
    w=csv.writer(f);w.writerow(['number','in_wpa_parse','in_census_base']);w.writerows(rows)
json.dump({'wm':wm,'cm':cm},open(sys.argv[2],'w'))
import collections
print(collections.Counter((a,b) for _,a,b in rows))

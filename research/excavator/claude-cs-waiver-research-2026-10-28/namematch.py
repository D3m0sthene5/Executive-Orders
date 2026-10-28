import csv, re, sys, collections
rows=list(csv.DictReader(open(sys.argv[1])))
W=[r for r in rows if r['type']=='cs_waiver_individual']
def name_of(s):
    s=re.sub(r'\s+',' ',s)
    m=re.match(r"\s*((?:Mrs?\.|Miss|Dr\.)?\s*[A-Z][a-zA-Z'\.]+(?: [A-Z][a-zA-Z'\.]*){1,3})(?:,| made| permitted| may| eligible| authorized| allowed| reinstated| appointed| exempted| to be| retained)", s)
    return m.group(1).strip() if m else None
def surname(n): return n.split()[-1]
idx=collections.defaultdict(list)
for r in rows:
    txt=(r['wpa_summary']+' '+r['app_title'])
    for tok in set(re.findall(r"[A-Z][a-z]{3,}",txt)): idx[tok].append(r)
out=[]
for w in W:
    n=name_of(w['wpa_summary']) or name_of(w['app_title'].replace('Authorizing the Appointment of ','').replace('Executive Order ',''))
    if not n: continue
    parts=[p for p in re.sub(r'(Mrs?\.|Miss|Dr\.)','',n).split() if len(p)>1]
    if len(parts)<2: continue
    sur=parts[-1]; first=parts[0]
    for r in idx.get(sur,[]):
        if r['instrument_id']==w['instrument_id']: continue
        txt=re.sub(r'\s+',' ',r['wpa_summary']+' '+r['app_title'])
        if first in txt and sur in txt:
            try:
                if r['year'] and w['year'] and int(r['year'])<int(w['year']): rel='earlier'
                else: rel='later_or_same'
            except: rel='?'
            out.append((w['instrument_id'],w['year'],n,r['instrument_id'],r['year'],r['type'],rel,txt[:160]))
wr=csv.writer(sys.stdout); wr.writerow(['waiver','wyear','name','other','oyear','otype','rel','other_text'])
for o in out: wr.writerow(o)
print('waivers with parsed name:',sum(1 for w in W if name_of(w['wpa_summary'])),file=sys.stderr)
print('waivers with any match:',len(set(o[0] for o in out)),file=sys.stderr)

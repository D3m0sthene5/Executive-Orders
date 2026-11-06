import sys,os,re,csv,json
csv.field_size_limit(10**9)
root='/home/user/Executive-Orders'
nums={'8969':('1941-12-11'),'10276':('1951-07-31')}
files=[l.strip() for l in sys.stdin if l.strip()]
dre=re.compile(r'\b(1[89]\d\d)(?:-\d\d-\d\d)?\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, 19\d\d')
out=[]
for f in files:
    p=os.path.join(root,f)
    try:
        if f.endswith('.csv'):
            with open(p,newline='',encoding='utf-8',errors='replace') as fh:
                r=csv.reader(fh); hdr=next(r,[])
                for i,row in enumerate(r,2):
                    for n in nums:
                        if any(c in (n,'EO:'+n,'EO-'+n) or re.fullmatch(r'(EO[:-])?0*'+n,c) for c in row) :
                            ds=[(hdr[j] if j<len(hdr) else str(j),c) for j,c in enumerate(row) if len(c)<40 and re.search(r'(19\d\d)',c) and re.search(r'date|year|^y$|sign|effective|published',(hdr[j] if j<len(hdr) else ''),re.I)]
                            out.append((f,i,n,ds))
        else:
            with open(p,encoding='utf-8',errors='replace') as fh:
                for i,l in enumerate(fh,1):
                    for n in nums:
                        if re.search(r'(EO[:\- _]|"(?:eo_number|number|order_number|id|instrument_id)": ?"?)0*'+n+r'\b',l):
                            try: d=json.loads(l)
                            except Exception: d={}
                            ds=[(k,str(v)) for k,v in d.items() if re.search(r'date|year|^y$',k,re.I) and re.search(r'19\d\d',str(v)) and len(str(v))<40] if isinstance(d,dict) else []
                            out.append((f,i,n,ds))
    except Exception as e: out.append((f,0,'ERR',str(e)))
for o in out: print(json.dumps(o))

import csv,json,re,sys,os
csv.field_size_limit(10**9)
root='/home/user/Executive-Orders'
WRONG={'EO:8969':('1946-12-11','1941-12-11'),'EO:10276':('1961-07-31','1951-07-31')}
IDK=('id','instrument_id','actor_id','acting_id','target_id','census_id')
files=[l.strip() for l in open(sys.argv[1]) if l.strip()]
rows=[]
def walk(o,path,f,line):
    if isinstance(o,dict):
        iid=next((o[k] for k in IDK if isinstance(o.get(k),str) and o[k] in WRONG),None)
        if iid:
            for k,v in o.items():
                if isinstance(v,str) and v.startswith(WRONG[iid][0]) and re.search('date',k):
                    rows.append((iid,f,f'line {line}',f'{path}{k}',v))
        for k,v in o.items(): walk(v,path+k+'.',f,line)
    elif isinstance(o,list):
        for i,v in enumerate(o): walk(v,path+f'[{i}].',f,line)
for f in files:
    p=os.path.join(root,f)
    try:
        if f.endswith('.csv'):
            with open(p,newline='',encoding='utf-8',errors='replace') as fh:
                r=csv.reader(fh); hdr=next(r,[])
                for row in r:
                    ln=r.line_num
                    d=dict(zip(hdr,row))
                    iid=next((d[k] for k in ('id','instrument_id','acting_id') if d.get(k) in WRONG),None)
                    if iid:
                        for k,v in d.items():
                            if re.search('date',k) and v.startswith(WRONG[iid][0]): rows.append((iid,f,f'line {ln}',k,v))
        else:
            with open(p,encoding='utf-8',errors='replace') as fh:
                for ln,l in enumerate(fh,1):
                    if '1946-12-11' in l or '1961-07-31' in l:
                        try: walk(json.loads(l),'',f,ln)
                        except Exception: pass
    except Exception as e: print('ERR',f,e,file=sys.stderr)
OFF={'EO:8969':('jobs/app-executive-orders/output/texts/executive-order-8969-exemption-joshua-g-hefty-from-compulsory-retirement-for-age.txt','file lines 3-5 (signature block)','"FRANKLIN D ROOSEVELT / The White House, / December 11, 1941." (APP transcription: mirror, not an official printing; no held FR/OFR printing exists - OFR index marks order not received for publication, jobs/fr-originals/output/NOT_FOUND.csv line 312). Corroborated by jobs/app-executive-orders/output/INDEX.csv line 5493 date 1941-12-11'),
 'EO:10276':('jobs/fr-originals/data/full_run/texts/EO_10276.txt','lines 530-533 (PDF page 3 of extract; 16 FR 7535, Federal Register Vol 16 No 149, Aug 2 1951)','"The White House, July 31, 1951, 7:01 p. m., e. d. t. [F. R. Doc. 51-8977; Filed, Aug. 1, 1951; 10:08 a. m.]" (held official FR printing, machine OCR text layer; also issue date "Thursday, August 2, 1951" line 5-ish; jobs/app-executive-orders/output/INDEX.csv line 4164 date 1951-07-31)')}
seen=set()
with open(sys.argv[2],'w',newline='') as fh:
    w=csv.writer(fh); w.writerow('instrument_id,path,locator,current_value,correct_value,official_source_path,official_locator,official_quote'.split(','))
    for iid,f,loc,field,v in rows:
        k=(iid,f,loc,field)
        if k in seen: continue
        seen.add(k)
        o=OFF[iid]; w.writerow([iid,f,loc,f'{field}={v}',WRONG[iid][1],o[0],o[1],o[2]])
print(len(seen))

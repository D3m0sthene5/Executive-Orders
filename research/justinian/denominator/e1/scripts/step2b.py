"""Re-scan the OCR page text (the exact pages wpa.py consumed) for entry heads that wpa.N_ENTRY cannot read:
multi-number heads ('36, 37:'), ranges ('40-42:'), and starred heads ('21 * :'). Lists, for each integer missing from the
WPA parse, the head line that covers it."""
import json,re,sys,csv
P='/home/user/Executive-Orders/research/progress/branch-recovery-2026-10-29/legacy/wpa-lists/jobs/wpa-lists/data/numbered_pages.jsonl'
miss=json.load(open(sys.argv[1]))['wm']
pages=[json.loads(l) for l in open(P,encoding='utf-8')]
HEAD=re.compile(r'^\s*(\d{1,4}(?:\s*[-–]\s*(?:\d{1,4}|[A-Z]))?(?:\s*,\s*\d{1,4}(?:\s*[-–]\s*(?:\d{1,4}|[A-Z]))?)*)\s*(\*?)\s*[:;]\s*(.*)$')
def expand(prefix):
    out=set(); 
    for part in prefix.split(','):
        part=part.strip()
        m=re.fullmatch(r'(\d+)\s*[-–]\s*(\d+)',part)
        if m:
            a,b=int(m.group(1)),int(m.group(2))
            if 0<b-a<=60: out.update(range(a,b+1))
            else: out.add(a)
            continue
        m=re.match(r'(\d+)',part)
        if m: out.add(int(m.group(1)))
    return out
found={}
heads=[]
year=None
for pg in pages:
    if pg['page']<18: continue
    L=pg['text'].splitlines()
    for i,l in enumerate(L):
        if re.fullmatch(r'\s*1[89]\d\d\s*',l): year=int(l)
        m=HEAD.match(l)
        if m:
            nums=expand(m.group(1))
            for n in nums:
                if n in miss: found.setdefault(n,[]).append((pg['page'],i,l,year,L[i:i+3]))
json.dump({str(k):v for k,v in found.items()},open(sys.argv[2],'w'),indent=1)
print(len(found),'of',len(miss),'missing integers have a candidate head')
for n in miss:
    c=found.get(n)
    print(n,[(x[0],x[2][:60]) for x in c] if c else 'NONE')

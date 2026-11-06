import json,re,sys,csv
P='/home/user/Executive-Orders/research/progress/branch-recovery-2026-10-29/legacy/wpa-lists/jobs/wpa-lists/data/numbered_pages.jsonl'
pages=[json.loads(l) for l in open(P,encoding='utf-8')]
rows=list(csv.DictReader(open('/home/user/Executive-Orders/jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv',encoding='utf-8')))
have=sorted({int(r['number']) for r in rows})
def lines():
    for pg in pages:
        if pg['page']<18: continue
        for i,l in enumerate(pg['text'].splitlines()): yield pg['page'],i,l
LL=list(lines())
for n in map(int,sys.argv[1:]):
    p=max(x for x in have if x<n); q=min(x for x in have if x>n)
    pr=[r for r in rows if int(r['number'])==p][-1]; nr=[r for r in rows if int(r['number'])==q][0]
    print('#### missing',n,'prev',pr['id'],'p',pr['page'],'next',nr['id'],'p',nr['page'])
    hp=re.compile(r'^\s*%d\s*(?:-\s*[A-Z\d]+)?\s*[*]?\s*[:;]'%p); hq=re.compile(r'^\s*%d\s*(?:-\s*[A-Z\d]+)?\s*[*]?\s*[:;]'%q)
    st=[k for k,(pg,i,l) in enumerate(LL) if pg==int(pr['page']) and hp.match(l)]
    en=[k for k,(pg,i,l) in enumerate(LL) if pg==int(nr['page']) and hq.match(l)]
    if st and en:
        for pg,i,l in LL[st[-1]:en[0]+1]: print('  p%d L%d: %s'%(pg,i,l))
    else: print('  heads not located',st,en)

import json,re,sys
P='/home/user/Executive-Orders/research/progress/branch-recovery-2026-10-29/legacy/wpa-lists/jobs/wpa-lists/data/numbered_pages.jsonl'
pages=[json.loads(l) for l in open(P,encoding='utf-8')]
for n in map(int,sys.argv[1:]):
    pat=re.compile(r'(?<![\d,.])%d(?!\d)'%n)
    for pg in pages:
        if pg['page']<18: continue
        L=pg['text'].splitlines()
        for i,l in enumerate(L):
            if pat.search(l) and re.search(r'^\s*\d+\s*[-–.]?\s*[A-Z]?\s*[:;.,]',l):
                print(n,'p',pg['page'],'L',i,repr(l[:160]))

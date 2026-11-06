import json,re,sys,csv,hashlib
sys.path.insert(0,'/home/user/Executive-Orders/research/progress/branch-recovery-2026-10-29/legacy/wpa-lists/jobs/wpa-lists')
sys.dont_write_bytecode=True
import wpa
P='/home/user/Executive-Orders/research/progress/branch-recovery-2026-10-29/legacy/wpa-lists/jobs/wpa-lists/data/numbered_pages.jsonl'
pages=[json.loads(l) for l in open(P,encoding='utf-8')]
ents=wpa.parse_numbered(pages)
cur=list(csv.DictReader(open('/home/user/Executive-Orders/jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv',encoding='utf-8')))
print(len(ents),len(cur),[e['id'] for e in ents]==[r['id'] for r in cur], all(e['text']==r['text'] for e,r in zip(ents,cur)))

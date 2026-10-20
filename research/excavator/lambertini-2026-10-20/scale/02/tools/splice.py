import json
D='/home/user/Executive-Orders/research/excavator/lambertini-2026-10-20/scale/02/'
S='/tmp/claude-0/-home-user-Executive-Orders/dc388148-b92d-5956-9825-90ce34a3dac7/scratchpad/lambertini2/b2/'
mach={}
for l in open('/home/user/Executive-Orders/jobs/readiness-tracker/output/MACHINE_LATER_SEARCH.jsonl'):
    r=json.loads(l); mach[r['instrument_id']]=r['later_source_search']
out=[]
for l in open(D+'claims_assembled.jsonl'):
    c=json.loads(l); n=c['instrument_id'].split(':')[1]
    ms=mach[c['instrument_id']]; assert len(ms)==3
    own={"checked_on":"2026-10-20","query_or_scope":f"by-number scan (hyphenation and whitespace normalised) for 'Executive Order {n}', 'EO {n}' and the bare number near 'order' in all 6,652 held Federal Register order texts, to find any amendment, extension, suspension, revocation or reinstatement of EO {n} other than EO 13990; hits read in context","repository":"jobs/fr-originals/data/full_run/texts (official Federal Register text layers, EO 1 through EO 14435)"}
    c['later_source_search']=ms+[own]
    out.append(c)
with open(S+'claims_spliced.jsonl','w') as f:
    for c in out: f.write(json.dumps(c,sort_keys=True,ensure_ascii=False)+'\n')
print('spliced',len(out))

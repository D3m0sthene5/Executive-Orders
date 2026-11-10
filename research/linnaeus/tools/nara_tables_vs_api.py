"""Measure NARA disposition tables (held HTML, dir argv[1]) against later-events FR-API notes for the no-lead set.
Usage: python -I nara_tables_vs_api.py <html_dir> <repo_root> <dir holding out/NO_LEAD_TYPES.csv>. Measurement aid, not a job."""
import re,html,glob,os,csv,collections,json,sys
D=sys.argv[1]; R=sys.argv[2]; S=sys.argv[3]
ent={}
pages=0
for f in sorted(glob.glob(D+'/*.html')):
    t=open(f,encoding='utf-8',errors='replace').read()
    if 'Page Not Found' in t[:5000] or os.path.getsize(f)<2000: continue
    pages+=1
    txt=html.unescape(re.sub(r'<[^>]+>','\n',t))
    txt=re.sub(r'[ \t\xa0]+',' ',txt)
    # entry headers can run on inside the previous text node; notes cite 'EO N' or 'Executive Order of <date>'
    txt=re.sub(r'(Executive Order No\.\s*\d{4,5})',r'\n\1',txt)
    lines=[l.strip() for l in txt.split('\n') if l.strip()]
    cur=None
    for i,l in enumerate(lines):
        # An entry starts at 'Executive Order' + a number line, or at a line that begins 'Executive Order (No.) N'
        # (1938-style pages print the number and the title on one line). Review finding 12, 2026-11-10.
        m1=re.match(r'Executive Order(?: No\.?)?\s*(\d{4,5}(?:-?[A-Z])?)\b',l)
        if m1 or (re.fullmatch(r'Executive Order(?: No\.?)?',l) and i+1<len(lines)
                  and re.fullmatch(r'\d{4,5}(-?[A-Z])?',lines[i+1])):
            cur='EO:'+(m1.group(1) if m1 else lines[i+1]).replace('-','')
            ent[cur]={'page':os.path.basename(f),'lines':[]}
            continue
        if cur and l!=cur[3:]:
            ent[cur]['lines'].append(l)
print('pages',pages,'entries',len(ent))
NOTE=re.compile(r'^(Revoked by|Superseded by|Amended by|Amends|Revokes|Supersedes|See|Note|Continued by|Terminated by|Modified by|Partially revoked by|Suspended by|Reinstated by)\b',re.I)
def notes(e):
    out=[];cur=None
    for l in e['lines']:
        m=NOTE.match(l)
        if m: cur=[l]; out.append(cur)
        elif cur is not None and not l.startswith(('Signed','Federal Register')): cur.append(l)
    return [' '.join(x) for x in out]
rows=list(csv.DictReader(open(S+'/out/NO_LEAD_TYPES.csv',encoding='utf-8')))
le=collections.defaultdict(list)
for x in csv.DictReader(open(R+'/jobs/later-events/output/EDGES.csv',encoding='utf-8')):
    le[x['target_id']].append(x)
c=collections.Counter(); ex=[]
post=[r for r in rows if r['number'] and int(r['number'])>=7532]
for r in post:
    i=r['instrument_id']; c['post1937_nolead']+=1
    e=ent.get(i)
    if not e: c['no_nara_entry']+=1; continue
    c['nara_entry']+=1
    ns=notes(e)
    later=[n for n in ns if re.match(r'(Revoked|Superseded|Amended by|Continued|Terminated|Modified|Partially|Suspended|Reinstated|See)',n,re.I)]
    ending=[n for n in ns if re.match(r'(Revoked|Superseded|Terminated|Partially revoked)',n,re.I)]
    if later: c['nara_later_note']+=1
    if ending:
        c['nara_ending_note']+=1
        api=[x for x in le.get(i,[]) if x['evidence_type'].startswith('ofr_note')]
        if not api: c['nara_ending_not_in_api']+=1; ex.append((i,ending[:2],e['page']))
print(dict(c))
for x in ex[:25]: print(x)
json.dump({k:{'page':v['page'],'notes':notes(v)} for k,v in ent.items()},open(S+'/nara_entries.json','w'),indent=0)

"""Mechanical screen of NIRA code-approval order candidates. Usage: python3 -I screen.py TREE OUTDIR"""
import json,csv,re,glob,os,sys,time,collections
T0=time.time()
R,OUT=sys.argv[1],sys.argv[2]
os.chdir(R)
CO='research/excavator/claude-nira-sweep-2026-10-29/'
rows=list(csv.DictReader(open('jobs/x1-class-engine/output/TYPES.csv')))
TT={r['instrument_id']:r['app_title'] for r in rows}
idx={x['instrument_id']:x for x in json.load(open('jobs/claim-kit/output/INDEX.json'))}
def dossier(i): return json.load(open('jobs/claim-kit/output/dossiers/%s.json'%i.replace(':','_')))
def title_of(d,iid):
    o=d.get('original_source_id'); p=''
    if o and o in d['evidence']: p=d['evidence'][o]['source']['page_or_item']
    elif d['clauses']: p=d['clauses'][0]['source']['page_or_item']
    if not p: p=TT.get(iid,'')
    return p.split('—',1)[-1].split(';')[0].strip()
counts={}
typed=[r['instrument_id'] for r in rows if r['type']=='nra_code_approval']
counts['x1_typed_nra_code_approval']=len(typed)
no=[i for i in typed if idx.get(i,{}).get('status')=='no']
counts['x1_typed_and_provisional_no']=len(no)
dos={i:dossier(i) for i in no}
title={i:title_of(dos[i],i) for i in no}
# pool title rule: code approval/amendment/exemption; empty titles kept (batches contain them, screen decides)
tpat=re.compile(r'code|amend|exempt|industry',re.I)
admin=re.compile(r'Executive Order No|Approving Agreement|Administration of|Delegat|Creating|Government Contracts|Authorizing the Administrator',re.I)
pool=[i for i in no if (not title[i] or tpat.search(title[i])) and not (title[i] and admin.search(title[i]))]
counts['dropped_by_title_rule']=len(no)-len(pool)
coh=json.load(open(CO+'COHORTS.json'))
trial={'EO:6811','EO:6308','EO:6248'}  # try1 packet members (3 trial orders)
pp=re.compile(r'poultry|petroleum',re.I)
out_trial=[i for i in pool if i in trial]
out_pp=[i for i in pool if i not in trial and pp.search(title[i])]
pool=[i for i in pool if i not in set(out_trial)|set(out_pp)]
counts['trial_orders_removed']=len(out_trial); counts['poultry_petroleum_outliers_removed_by_title']=len(out_pp)
counts['pool_size']=len(pool)
batches={k:v for k,v in coh.items() if isinstance(v,list)}
bset=set().union(*batches.values())
counts['batch_lists']={k:len(v) for k,v in batches.items()}
claimed=set()
for f in glob.glob('research/readiness/claims/*.jsonl'):
    for l in open(f):
        if l.strip():
            try: claimed.add(json.loads(l)['instrument_id'])
            except Exception: pass
lock=set(json.load(open('research/readiness/CLAIM_KIT_LOCK.json'))['orders'])
holds=set()
for l in open('research/readiness/SOURCE_AUDIT_HOLDS.jsonl'):
    if l.strip(): holds.add(json.loads(l)['instrument_id'])
rem=list(pool); excl={}
for name,s in [('cohort_batches',bset),('existing_claims',claimed),('claim_kit_lock',lock),('source_audit_holds',holds)]:
    hit=[i for i in rem if i in s]; counts['removed_by_'+name]=len(hit); rem=[i for i in rem if i not in s]
counts['after_exclusions']=len(rem)
# structural screens
KW=['committee','stay','stayed','pending','condition','report','until','provided','exempt','exemption','appoint','period of','days after','effective date']
BOILER=re.compile(r'report[,]? (and )?recommendation|report of the administrator|administrator.s report|his report|report containing|the report',re.I)
def kwhits(text):
    low=text.lower(); raw=[k for k in KW if k in low]
    low2=BOILER.sub(' ',low); adj=[k for k in KW if k in low2]
    return raw,adj
fails=collections.defaultdict(list); cands=[]
for i in rem:
    d=dos[i]; why=[]
    if d['whole_order_status']!='no': why.append('whole_order_status')
    if len(d['clauses'])!=1: why.append('clause_count=%d'%len(d['clauses']))
    o=d.get('original_source_id'); tp=None
    if not o or o not in d['evidence']: why.append('no_original_source_id')
    else:
        tp=d['evidence'][o]['source'].get('text_path')
        if not tp or not os.path.exists(tp): why.append('text_path_missing'); 
    kinds=[d['evidence'][t].get('kind') for t in d['own_terms'] if t in d['evidence']]
    bad=[k for k in kinds if k in ('condition','report_deadline')]
    if bad: why.append('own_terms:'+','.join(sorted(set(bad))))
    if d['actor_provisions']: why.append('actor_provisions')
    if d['chain']['events']: why.append('chain_events')
    if why:
        fails[i]=why; continue
    text=open(tp,encoding='utf-8',errors='replace').read()
    raw,adj=kwhits(text)
    cands.append(dict(instrument_id=i,title=title[i],clause_count=1,text_path=tp,text_chars=len(text),
        keyword_hits=raw,keyword_hits_excluding_report_boilerplate=adj,
        other_own_terms_kinds=sorted(set(k for k in kinds if k)),
        _text=text))
counts['failed_structural_screens']=len(fails)
fc=collections.Counter(w.split('=')[0].split(':')[0] for v in fails.values() for w in v); counts['structural_fail_reasons']=dict(fc)
counts['candidates_passing_structural']=len(cands)
# corpus
paths=sorted(glob.glob('jobs/*/output/texts/**/*.txt',recursive=True))
corpus=[]
for p in paths:
    try: corpus.append((p,re.sub(rb'\s+',b' ',open(p,'rb').read().lower())))
    except Exception: pass
counts['held_texts_searched']=len(corpus)
corpus_len={p:len(b) for p,b in corpus}
def codename(t):
    m=re.search(r'Codes? of Fair Competition\s+(?:for|of)\s+(?:the\s+)?(.+)$',t,re.I)
    if not m: return None
    n=re.sub(r',?\s*etc\.?$','',m.group(1).strip(),flags=re.I).strip(' .,;')
    return n
def hitnum(p):
    b=os.path.basename(p)
    m=re.search(r'executive-order-(\d+)(?:-([a-z])-)?',b) or re.search(r'EO_(\d+)([A-Z]?)',b) or re.search(r'cd-job-[a-z-]+?-(\d+)([A-Z]?)-',b)
    return (int(m.group(1)),(m.group(2) or '').upper()) if m else None
def hitnum(p):
    b=os.path.basename(p)
    m=re.search(r'executive-order-(\d+)(?:-([a-z])-)?',b) or re.search(r'EO_(\d+)([A-Z]?)',b) or re.search(r'cd-job-[a-z-]+?-(\d+)([A-Z]?)-',b)
    return (int(m.group(1)),(m.group(2) or '').upper()) if m else None
def ownish(p,iid):
    b=os.path.basename(p).lower(); n=iid.split(':')[1].lower()
    m=re.match(r'(\d+)([a-z]?)$',n)
    num,suf=m.groups()
    pat=r'(?<!\d)%s(?:-?%s)?(?![\da-z])'%(num,suf) if suf else r'(?<!\d)%s(?![\d])'%num
    return bool(re.search(pat,b))
for c in cands:
    iid=c['instrument_id']; name=codename(c['title']); c['code_name_searched']=name
    n=iid.split(':')[1]; num=re.match(r'\d+',n).group(); suf=re.sub(r'^\d+','',n).lower()
    numre=re.compile((r'order[^\d\n]{0,14}%s%s(?![\d])(?!-[a-z]\b)'%(num,('[- ]?'+suf) if suf else '')).encode()) 
    hits=[]; own=c['text_path']; dups=0
    ot=re.sub(r'\s+',' ',c['_text'].lower()); k=ot.find('now, therefore'); k=k if k>=0 else max(0,len(ot)//3)
    sl=ot[k:k+90].encode()
    nm=name.lower().encode() if name and len(name)>=8 else None
    nm2=re.sub(rb'\s+',b' ',nm) if nm else None
    for p,b in corpus:
        if p==own or ownish(p,iid): continue
        hit=None
        if len(sl)>=40 and sl in b: dups+=1; continue
        if nm2 and nm2 in b: hit='code_name'
        elif num.encode() in b and numre.search(b): hit='order_number'
        if hit: hits.append((p,hit))
    mynum=(int(num),suf.upper())
    keep=[]; seen=set()
    for p,h in hits:
        hn=hitnum(p)
        rel='unknown' if hn is None else ('earlier' if hn<mynum else ('same_number' if hn==mynum else 'later'))
        if rel=='same_number': continue
        key=hn if hn else p
        if key in seen: continue
        seen.add(key); keep.append((p,h,rel))
    keep.sort(key=lambda t:({'later':0,'unknown':1,'earlier':2}[t[2]],corpus_len[t[0]]))
    c['duplicate_copies_of_own_text_excluded']=dups
    c['hit_relation_counts']=dict(collections.Counter(r for _,_,r in keep))
    c['earlier_numbered_hits_not_counted']=[p for p,h,r in keep if r=='earlier'][:3]
    kl=[(p,h,r) for p,h,r in keep if r!='earlier']
    c['later_text_hit_count']=len(kl)
    c['later_text_hits']=[p for p,_,_ in kl[:5]]
    c['later_text_hit_basis']=[h for _,h,_ in kl[:5]]
    c['later_text_hit_relation']=[r for _,_,r in kl[:5]]
    c['later_hits_by_basis']=dict(collections.Counter(h for _,h,_ in kl))
    del c['_text']
    c['strict_plain_no_keyword_at_all']=not c['keyword_hits'] and not c['other_own_terms_kinds']
    plain = not c['keyword_hits_excluding_report_boilerplate'] and not c['other_own_terms_kinds']
    c['screen']='plain' if plain else 'flagged'
    c['later_text_hits_out']=c['later_text_hits']
for c in cands:
    c['later_text_hits']=c.pop('later_text_hits_out')
cands.sort(key=lambda c:(c['screen']!='plain',c['later_text_hit_count']>0,c['later_text_hit_count'],len(c['keyword_hits']),c['instrument_id']))
counts['plain']=sum(c['screen']=='plain' for c in cands); counts['flagged']=len(cands)-counts['plain']
counts['strict_plain_no_keyword_at_all']=sum(c['strict_plain_no_keyword_at_all'] for c in cands)

counts['elapsed_seconds']=round(time.time()-T0,1)
json.dump(dict(counts=counts,candidates=cands,structural_fails={k:v for k,v in fails.items()}),open(os.path.join(OUT,'CANDIDATES.json'),'w'),indent=1)
print(json.dumps(counts,indent=1))

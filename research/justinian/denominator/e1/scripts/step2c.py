"""Recover entries absent from the WPA parse by re-reading the OCR page text the parser consumed.
usage: python3 -I step2c.py MISSING.json OUT_CSV   (repo paths hard-coded below)"""
import json,re,sys,csv,glob,collections
R='/home/user/Executive-Orders/'
OCR_REL='research/progress/branch-recovery-2026-10-29/legacy/wpa-lists/jobs/wpa-lists/data/numbered_pages.jsonl'
pages=[json.loads(l) for l in open(R+OCR_REL,encoding='utf-8')]
byp={p['page']:p['text'].splitlines() for p in pages}
miss=json.load(open(sys.argv[1]))['wm']
rows=list(csv.DictReader(open(R+'jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv',encoding='utf-8')))
have=sorted({int(r['number']) for r in rows})
cen={r['id'] for r in csv.DictReader(open(R+'research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv',encoding='utf-8'))}
MON=r'(?:Jan|Feb|Mar|Apr|May|June?|July?|Aug|Sept?|Oct|Nov|Dec)\.?'
# ---- held-official index
OFFG={'machine_read_government_printed_copy','government_printed_copy'}
idx=collections.defaultdict(list)
for p in sorted(glob.glob(R+'jobs/*/output/SOURCES.jsonl')):
    rel=p[len(R):]
    for l in open(p,encoding='utf-8'):
        try:d=json.loads(l)
        except Exception: continue
        ids=d.get('instrument_ids') or []
        if not ids: continue
        off=(d.get('grade') in OFFG) or str(d.get('route','')).startswith('official/')
        kind='official' if off else ('mirror' if 'mirror' in str(d.get('grade','')) or 'transcription' in str(d.get('grade','')) else 'other')
        for i in ids: idx[i].append((kind,rel,d.get('page_or_item',''),d.get('grade') or d.get('route','')))
LL=[(pg,i,l) for pg in sorted(byp) if pg>=18 for i,l in enumerate(byp[pg])]
def region(n):
    p=max(x for x in have if x<n); q=min(x for x in have if x>n)
    def loc(num,last):
        hp=re.compile(r'^\s*%d\s*(?:-\s*[A-Z\d]+)?\s*\*?\s*[:;]'%num)
        ks=[k for k,(pg,i,l) in enumerate(LL) if hp.match(l)]
        ks=[k for k in ks if abs(LL[k][0]-[int(r['page']) for r in rows if int(r['number'])==num][0])<=1]
        return (ks[-1] if last else ks[0]) if ks else None
    a,b=loc(p,True),loc(q,False)
    if a is None or b is None: return None
    return LL[a:b+1]
HEAD=re.compile(r'^\s*(\d{1,4}(?:\s*[-–]\s*(?:\d{1,4}|[A-Z])){0,2}(?:\s*,\s*\d{1,4}(?:\s*[-–]\s*(?:\d{1,4}|[A-Z]))?)*)\s*(\*?)\s*[:;]\s*(\*?\s*(?:\(no date\).*|'+MON+r'.*|\[.*))$')
def expand(prefix):
    out=set()
    for part in prefix.split(','):
        part=part.strip()
        m=re.fullmatch(r'(\d+)\s*[-–]\s*(\d+)',part)
        if m:
            a,b=int(m.group(1)),int(m.group(2))
            if b>a and b-a<=60: out.update(range(a,b+1))
            continue   # b<=a: a suffixed id like 106-1, not the bare number
        m=re.match(r'(\d+)',part)
        if m: out.add(int(m.group(1)))
    return out
def datein(s):
    m=re.search(r'('+MON+r')\s*(\d{1,2})',s); return (m.group(1)+' '+m.group(2)) if m else ('(no date)' if 'no date' in s else '')
def norm(s): return s.translate(str.maketrans({'l':'1','I':'1','O':'0','o':'0'}))
out=[]; cat=collections.Counter(); used=set()
def boundary(pg,i):
    n=len(byp[pg]); return 'on_page_boundary(line %d of %d)'%(i,n) if i<=2 or i>=n-4 else 'mid_page'
for n in miss:
    found=None
    # s1 head covering n
    for pg,i,l in LL:
        m=HEAD.match(l)
        odd=re.fullmatch(r'\s*(\d+)\s*[-–]\s*\1\s*[-–]\s*\d+\s*',m.group(1)) if m else None
        if m and (n in expand(m.group(1)) or (odd and int(odd.group(1))==n)):
            pre=m.group(1)
            if re.search(r'\d\s*,\s*\d|\d-\d+-\d|\d{1,4}\s*[-–]\s*\d{2,4}\s*$',pre.strip()) or ',' in pre:
                c='multi_number_or_range_head'
            elif m.group(2): c='starred_head_unreadable_by_parser'
            else: c='plain_head_swallowed_by_parser_sequence_guard'
            if re.fullmatch(r'\s*\d+\s*[-–]\s*\d+\s*[-–]\s*\d+\s*',pre): c='odd_range_head_92-92-3 (ambiguous)'
            found=(c,pg,i,l,datein(m.group(3)),'' ); break
    if not found:
        pat=re.compile(r'(?<![\d,])%s\s*[:;]\s*(%s\s*\d{1,2})'%(re.escape(str(n)).replace('1','[1Il]',1) if str(n)[0]=='1' else re.escape(str(n)),MON))
        for pg,i,l in LL:
            m=pat.search(l)
            if m and m.start()>0 and not re.match(r'^\s*$',l[:m.start()]):
                found=('two_entries_merged_on_one_ocr_line',pg,i,l,datein(m.group(1)),''); break
    if not found:
        pat=re.compile(r'^\s*%d\s+(%s\s*\d{1,2})'%(n,MON))
        for pg,i,l in LL:
            m=pat.match(l)
            if m: found=('head_missing_colon',pg,i,l,datein(m.group(1)),''); break
    if not found:
        reg=region(n)
        if reg:
            for pg,i,l in reg:
                m=re.match(r'^\s*([0-9lIO]{2,4})\s*(?:[-–*]\s*[A-Z\d]+)?\s*[:;]?\s*('+MON+r'\s*\d{1,2})',l)
                if m:
                    h=norm(m.group(1)); s=str(n)
                    if len(h)==len(s) and sum(a!=b for a,b in zip(h,s))==1 and int(h) not in (min(x for x in have if x>n),max(x for x in have if x<n)) and (pg,i) not in used:
                        used.add((pg,i))
                        found=('ocr_digit_error_in_head(inferred_by_sequence)',pg,i,l,datein(m.group(2)),"printed head read by OCR as '%s'; number inferred from sequence and date, NOT printed in the OCR"%m.group(1)); break
    if not found:
        c='not_in_ocr_text'; out.append((n,'', '', '', '', OCR_REL,'not found','' )); 
        cat[c]+=1; out[-1]=(n,'','','not found','not found',c); continue
    c,pg,i,l,dt,extra=found; cat[c]+=1
    out.append((n,pg,i,l,dt,c,extra,boundary(pg,i)))
json.dump({'rows':out,'cat':cat},open(sys.argv[2],'w'),indent=1,default=str)
print(cat)
# write CSV
w=csv.writer(open(sys.argv[3],'w',newline='',encoding='utf-8'));
w.writerow(['number','suffix','wpa_page','date_printed','ocr_snippet','ocr_source_path','in_census','held_official_path','held_official_page','notes'])
for o in out:
    n=o[0]; eid='EO:%d'%n; inc='yes' if eid in cen else 'no'
    offs=[x for x in idx.get(eid,[]) if x[0]=='official']; mir=[x for x in idx.get(eid,[]) if x[0]=='mirror']
    hp=' | '.join(sorted({x[1] for x in offs})); hg=' | '.join(x[2] for x in offs)
    if not offs: hp='none found in jobs/*/output/SOURCES.jsonl'; hg=''
    note_extra=('; non-official mirror rows: '+' | '.join(sorted({x[1] for x in mir}))) if mir else ''
    if len(o)==6:
        w.writerow([n,'','','','not found: entry not in OCR text (see REPORT: scan lacks printed pp. 486-487)' if 5853<=n<=5879 else 'not found',OCR_REL,inc,hp,hg,o[5]+note_extra]); continue
    _,pg,i,l,dt,c,extra,bd=o
    snip=' / '.join(x.strip() for x in byp[pg][i:i+3])[:300]
    w.writerow([n,'',pg,dt,snip,OCR_REL+' (page %d, line %d)'%(pg,i),inc,hp,hg,'%s; %s%s%s'%(c,bd,('; '+extra) if extra else '',note_extra)])

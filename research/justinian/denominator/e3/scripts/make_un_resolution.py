import csv,re,json,sys
csv.field_size_limit(10**9)
R='/home/user/Executive-Orders/'
out=sys.argv[1]
cen=[l.rstrip('\n') for l in open(R+'research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv')]
cenline={l.split(',')[0]:i+1 for i,l in enumerate(cen) if l.startswith('EO:UN:')}
nf=open(R+'research/stage13/CENSUS/NARA_UNNUMBERED_EDITORIAL_DATES_18.csv',newline=''); nrd=csv.DictReader(nf)
nara={}
for r in nrd: nara[r['instrument_id']]=(nrd.line_num,r)
uf=open(R+'jobs/ofr-codification-1989/output/UNNUMBERED_ROWS.csv',newline=''); urd=csv.DictReader(uf)
un={}
for r in urd: un[r['table_row']]=(urd.line_num,r)
by_tr={}
for tr,(ln,r) in un.items():
    cid=r['census_id'] or None
    by_tr[tr]=(ln,r)
# census id -> UNNUMBERED_ROWS row: via census_id, else via NARA date match (rows 12/71 ambiguous same date)
cid2un={}
for tr,(ln,r) in un.items():
    if r['census_id']: cid2un[r['census_id']]=(ln,r)
pf=open(R+'jobs/shepard-citations/output/PLO_TABLE.csv',newline=''); prd=csv.DictReader(pf)
plo=[]
for p in prd: p['_line']=prd.line_num; plo.append(p)
MON={'01':'Jan','02':'Feb','03':'Mar','04':'Apr','05':'May','06':'June','07':'July','08':'Aug','09':'Sept','10':'Oct','11':'Nov','12':'Dec'}
sd=json.load(open(sys.argv[2]))
def cites(date):
    y,m,d=date.split('-'); rx=re.compile(f"{MON[m]}[a-z]*\\.? ?{int(d)}, ?{y}")
    return [p for p in plo if rx.search(' '.join([p['subject'],p['eo_dates_unresolved']]))]
fieldnames='census_id,source_table,source_row_text,matched_table,matched_row,date,eo_number,evidence,confidence'.split(',')
rows=[]
for cid in sorted(cenline,key=lambda c:(c.split(':')[2],int(c.split(':')[-1]))):
    nl,nr=nara[cid]
    ul,ur=cid2un.get(cid,(None,None))
    date=nr['reference_date']
    if ur is None:
        cand=[(tr,l,r) for tr,(l,r) in un.items() if r['date']==date and not r['census_id']]
        ur=cand[0][2] if cand else None; ul=cand[0][1] if cand else None
        note_amb=' [UNNUMBERED_ROWS pairing for this id is flagged ambiguous_same_date: two NARA rows share this date; disposition text shown is from the first same-date row and cannot be assigned to this id with certainty]'
    else: note_amb=''
    srctab=f"research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv line {cenline[cid]} (year_group 'Unknown date'); research/stage13/CENSUS/NARA_UNNUMBERED_EDITORIAL_DATES_18.csv line {nl} (raw_label '{nr['raw_label']}', reference_date {date}, category {nr['editorial_category']}); jobs/ofr-codification-1989/output/UNNUMBERED_ROWS.csv line {ul}"
    txt=f"NARA 1989 codification table row: date '{nr['raw_label']}'; disposition '{ur['disposition'] if ur else ''}'; amendments '{ur['amendments'] if ur else ''}'"+(f" (PDF page {ur['pdf_page']}, printed p. {ur['printed_page']})" if ur else '')+note_amb
    hits=cites(date)
    same=[p for p in plo if p['signature_date']==date]
    held_cites=[]
    ev=[];mt=[];mr=[];conf='none'
    ev.append(f"Date {date} is already held from the NARA 1989 codification row itself (not from PLO_TABLE); census year 'Unknown date' is a stale stage15 projection (jobs/early-ranger-year-reconcile/output/STAGE15_TO_STAGE17_YEAR_CHANGES.csv already carries a stage17 year for this id where listed). No EO number is given by any held table for this row.")
    ids=sd.get(date,[])
    if ids: ev.append(f"Numbered/other census orders with the same date (leads only, NOT matches): {'; '.join(i.split('|')[0] for i in ids)}")
    if hits:
        for p in hits:
            mt.append('jobs/shepard-citations/output/PLO_TABLE.csv'); mr.append(f"line {p['_line']} {p['plo_id']} signed {p['signature_date']}")
            ev.append(f"{p['plo_id']} (line {p['_line']}) subject: \"{p['subject'][:150]}\"; eo_dates_unresolved='{p['eo_dates_unresolved'][:100]}'; eo_ids='{p['eo_ids']}'")
        if cid=='EO:UN:executive-orders-01:row:4': conf='strong'; ev.append('PLO_TABLE eo_ids already links PLO:1359 and PLO:5585 to this census id (jobs/shepard-citations/output/EDGES.csv lines 7611-7612); the cited date July 21, 1871 equals the NARA row date and no other census order has that date. Strength is for the date/identity of the cited order only; no EO number.')
        else:
            conf='weak'; ev.append('PLO cites an executive order by date only; identity with this census row rests on date equality, and the PLO text does not name or number the order. Corroborates the date, adds no date or number.')
            if len(ids)>0 or cid.endswith(('row:12','row:71')): ev.append('Date shared with other candidate orders, so the citation cannot be assigned to this id.')
    elif same:
        for p in same:
            mt.append('jobs/shepard-citations/output/PLO_TABLE.csv'); mr.append(f"line {p['_line']} {p['plo_id']} signed {p['signature_date']}")
        ev.append(f"REJECTED: only a same-day coincidence: {'; '.join(p['plo_id']+' signed '+p['signature_date']+' ('+p['subject'][:80]+')' for p in same)} is a Public Land Order (a different instrument) signed that day; its text does not cite this order. Not a match.")
        conf='none'
    else:
        ev.append('No PLO_TABLE row signed on this date and none cites this date; the PLO series begins 1942-06-20 (PLO:1) so a pre-1942 order cannot be a PLO.' if date<'1942-06-20' else 'No PLO_TABLE row cites this order.')
    # held official FR text citing the date
    if cid.endswith('row:205'):
        mt.append('jobs/shepard-citations/output/UNRESOLVED.csv'); mr.append("lines 552/554/1720: EO:8507 held text jobs/fr-originals/data/full_run/texts/EO_8507.txt quotes 'Executive Order of November 9, 1923'")
        ev.append("Held FR text of EO 8507 quotes 'Executive Order of November 9, 1923' (shepard UNRESOLVED.csv line 552); EO 3924 (pinakes ProQuest ingest, Alaska agricultural experiment lands) shares the date, so the citation is not resolved to a single instrument.")
        conf='weak'
    rows.append([cid,srctab,txt,' | '.join(mt) or 'not found',' | '.join(mr) or 'not found',date,'not found',' ## '.join(ev),conf])
with open(out,'w',newline='') as fh:
    w=csv.writer(fh); w.writerow(fieldnames); w.writerows(rows)
import collections; print(len(rows),collections.Counter(r[-1] for r in rows))

import csv,re
csv.field_size_limit(10**9)
root='/home/user/Executive-Orders/'
r=list(csv.DictReader(open(root+'jobs/ofr-codification-1989/output/UNNUMBERED_ROWS.csv')))
f=open(root+'jobs/shepard-citations/output/PLO_TABLE.csv',newline='')
rd=csv.DictReader(f); plo=[]
for p in rd: p['_line']=rd.line_num; plo.append(p)
MON={'01':'Jan','02':'Feb','03':'Mar','04':'Apr','05':'May','06':'June','07':'July','08':'Aug','09':'Sept','10':'Oct','11':'Nov','12':'Dec'}
for x in r:
    y,m,d=x['date'].split('-'); lab=f"{MON[m]}. {int(d)}, {y}"
    pats=[f"{MON[m]}[a-z]*\\.? ?{int(d)}, ?{y}"]
    rx=re.compile(pats[0])
    hits=[p for p in plo if rx.search(' '.join([p['subject'],p['eo_dates_unresolved'],p['eo_refs'],p['reserve_refs'],p['plo_refs']]))]
    print(x['table_row'],x['date'],len(hits))
    for p in hits[:6]: print('   ',p['_line'],p['plo_id'],p['signature_date'],'|',p['subject'][:140],'|',p['eo_dates_unresolved'][:80],'|',p['eo_ids'])

import csv,json,glob
R='/home/user/Executive-Orders/'
T={'EO:2103','EO:2703','EO:3493','EO:3733'}
hits={t:[] for t in T}
for p in glob.glob(R+'jobs/*/output/SOURCES.jsonl'):
    for l in open(p,encoding='utf-8'):
        try:d=json.loads(l)
        except Exception: continue
        for i in d.get('instrument_ids') or []:
            if i in T: hits[i].append(p[len(R):]+' :: '+str(d.get('grade') or d.get('route')))
w=csv.writer(open('WPA_ONLY_CENSUS_ABSENT.csv','w',newline='',encoding='utf-8'))
w.writerow(['id','wpa_csv_line','wpa_page','year','month_day','wpa_text_start','merged_with_neighbour','sources_rows_naming_id','clark_NUMBER_GAPS_row'])
ng={r['instrument_id']:r for r in csv.DictReader(open(R+'jobs/clark-discovery/output/NUMBER_GAPS.csv',encoding='utf-8'))}
for i,r in enumerate(csv.DictReader(open(R+'jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv',encoding='utf-8')),2):
    if r['id'] in T:
        w.writerow([r['id'],'jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv:%d'%i,r['page'],r['year'],r['month_day'],r['text'][:120],'yes (next head 2104/3494 inside text)' if r['id'] in('EO:2103','EO:3493') else 'no',' | '.join(hits[r['id']]) or 'none','jobs/clark-discovery/output/NUMBER_GAPS.csv (class %s)'%ng[r['id']]['class'] if r['id'] in ng and 'class' in ng[r['id']] else ('jobs/clark-discovery/output/NUMBER_GAPS.csv' if r['id'] in ng else 'none')])

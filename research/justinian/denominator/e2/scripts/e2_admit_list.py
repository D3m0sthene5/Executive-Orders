import csv, os, sys, re
R='/home/user/Executive-Orders/'
OUT=sys.argv[1]
def rd(p): return list(csv.DictReader(open(R+p,encoding='utf-8')))
census_rows=rd('research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv')
CEN={r['id']:i+2 for i,r in enumerate(census_rows)}   # file line number
CENF='research/stage15/CENSUS/IDENTITY_LAYER_PROJECTION_14972.csv'
q=rd('research/niebuhr/ADMISSION_QUEUE.csv')
hoover={r['instrument_id']:r for r in rd('jobs/ofr-compilations/output/HOOVER_V2_ORDERS.csv')}
gaps={r['instrument_id']:(i+2,r) for i,r in enumerate(rd('jobs/clark-discovery/output/NUMBER_GAPS.csv'))}
app={r['instrument_id']:(i+2,r) for i,r in enumerate(rd('jobs/app-executive-orders/output/INDEX.csv'))}
OFRPDF='releases/source_books/OFR_1974_Hoover_Proclamations_and_Executive_Orders_v2_uc1.c025504761.pdf'
cols='candidate_id,group,number,suffix,date,title_or_subject,held_official_path,held_official_page_or_locator,held_text_path,evidence_summary,already_in_census(yes/no),notes'.split(',')
rows=[]
def split(i):
    m=re.match(r'EO:(\d+)([A-Za-z]*)$',i); return m.group(1),m.group(2)
def cen(i): return ('yes' if i in CEN else 'no')
def cenref(i): return ('census row %s line %d'%(CENF,CEN[i])) if i in CEN else 'absent from %s (14972 ids)'%CENF
# (a)
for n,r in enumerate(q,1):
    i=r['instrument_id']; num,suf=split(i)
    held=bool(r['official_pdf'])
    h=hoover.get(i)
    loc=('OFR 1974 Hoover vol. II PDF pp. %s (printed pp. %s)'%(r['pdf_pages'],r['printed_pages'])) if held else 'none held'
    if held and h and (h['pdf_pages']!=r['pdf_pages']): loc+=' [HOOVER_V2_ORDERS.csv says PDF pp. %s]'%h['pdf_pages']
    ev=('Official heading "%s"; official date %s; APP date %s; dates_agree=%s'%(r['official_heading'],r['date_official'],r['date_app'],r['dates_agree'])) if held else 'No official printing held (queue: "%s"); APP date %s only (index/catalogue, not an official printing)'%(r['dates_agree'],r['date_app'])
    notes=['queue row %d of research/niebuhr/ADMISSION_QUEUE.csv; %s'%(n+1,r['decision_needed'] or 'decision_needed blank'),'APP page: '+r['app_url'],'APP text: '+r['app_text_path'],cenref(i)]
    if i in ('EO:5855A','EO:5605A','EO:5638A','EO:6005A'):
        pass
    if not held:
        if i=='EO:5151A': notes.append('listed only in OFR Hoover vol. II Table 2, PDF p. 699 (jobs/ofr-compilations/output/CENSUS_LEADS.csv); the order itself is in vol. I, not held')
        if i=='EO:6585': notes.append('named with date 1934-02-06 in OFR 1989 Codification PDF p. 692 (jobs/ofr-codification-1989/output/CENSUS_LEADS.csv): a reference, not the order')
    if re.match(r'EO:58(5[3-9]|6\d|7\d)$',i): notes.append('also row b-%s (same instrument; count once)'%num)
    if held and num in ('5874',) : notes.append('official span is 44 PDF pages; confirm the span is one order')
    rows.append(dict(zip(cols,['ADM-a-%02d'%n,'a_niebuhr_queue',num,suf,r['date_official'] or r['date_app'],r['title_app'],r['official_pdf'] if held else 'none held',loc,r['official_text_path'] or 'none held',ev,cen(i),'; '.join(notes)])))
# (b)
for n in range(5853,5880):
    i='EO:%d'%n; h=hoover[i]; gl,g=gaps.get(i,(None,None)); al,a=app.get(i,(None,None))
    names=['OFR 1974 Hoover v2 (official compilation) via jobs/ofr-compilations/output/HOOVER_V2_ORDERS.csv']
    if a: names.append('APP INDEX.csv line %d (catalogue)'%al)
    if g: names.append('clark-discovery NUMBER_GAPS.csv line %d strength=%s'%(gl,g['strength']))
    citing=g['cited_plausibly_by'] if g else ''
    ev='OFR printed heading in %s first line; official date %s; OFR PDF pp. %s; APP title "%s"'%(h['text_path'],h['date'],h['pdf_pages'],(a['title'].split('—',1)[-1] if a else 'not found'))
    ev+='; HOOVER_V2_ORDERS census flag=%s'%h['census']
    notes=['named by: '+' | '.join(names)]
    if citing: notes.append('later orders citing it (NUMBER_GAPS): '+citing)
    notes.append(cenref(i))
    if i in CEN: notes.append('already a census id with blank date_effective: a date fill, not an admission')
    else: notes.append('owner A-20261021-1/D-20261104-delegated-answers: admit as working identity flagged compiled-source-only, queued for Lewis; no authentication')
    if i=='EO:5874': notes.append('official span is 44 PDF pages; confirm the span is one order')
    qrow=[x for x in q if x['instrument_id']==i]
    notes.append(('queue row ADM-a-%02d'%(q.index(qrow[0])+1)) if qrow else 'not in ADMISSION_QUEUE.csv')
    rows.append(dict(zip(cols,['ADM-b-%d'%n,'b_june1932_run',str(n),'',h['date'],(a['title'].split('—',1)[-1] if a else 'not found'),OFRPDF,'OFR 1974 Hoover vol. II PDF pp. %s (printed pp. %s)'%(h['pdf_pages'],h['printed_pages']),'jobs/ofr-compilations/output/'+h['text_path'],ev,cen(i),'; '.join(notes)])))
# (c)
P='jobs/pinakes-proquest-ingest/output/'
L=[
('27A','27','A','1890-09-04','Board on Geographic Names (per Niebuhr secondary lookup; label "27-A" used by later orders)',
 'research/pre-1937-sources/ProQuest Pre-1937 Orders/PT1-1890-EO-28.pdf (held scan of EO 28; candidate same instrument, NOT shown to be labelled 27-A)',
 'PDF pp. 1-4 of PT1-1890-EO-28.pdf: check whether the page is numbered 28 or 27-A. Separately, OFR 1974 Hoover vol. II PDF pp. 176-177 (printed 947-948) = EO 5658, which cites "No. 27-A of September 4, 1890"',
 P+'texts/EO_28.txt',
 'Cited as "Executive Order 27-A, September 4, 1890" by EO 399 (wikisource-texts), EO 5658 (OFR text jobs/ofr-compilations/output/texts/EO_5658.txt line 21), EO 6247, 6680, 7298 (jobs/clark-discovery/output/CITED_BUT_UNKNOWN.csv). Niebuhr b04.jsonl/CORROBORATION.csv resolve it "probably" to EO:28 (medium confidence; Wikisource secondary). Census has EO:28 dated 1890-09-04 (%s line %d).'%(CENF,CEN['EO:28']),
 'no (EO:27A); EO:28 is yes',
 'Decision: alias of EO:28 (add alias, no new identity) vs separate order. Census EO:27 is a different order (Oct 24, 1887, WPA numbered p.21). The held OCR text EO_28.txt is too garbled to read (first lines are noise), so the scan itself must be read by a person. Not found: any held page headed 27-A.'),
('130A','130','A','1900-06-22','Franchise granted by the Republic of Hawaii to the First American Bank of Hawaii approved (WPA index wording)',
 'none held',
 'none held. Index only: WPA 1944 numbered list printed p.31, entry "130-A * (no date)" inside the EO:130 row (jobs/x1-class-engine/data/WPA_NUMBERED_ENTRIES.csv id=EO:130 page 31; excerpt in research/niebuhr/WPA_JOIN.json)',
 'none held',
 'Named in WPA index (undated); EO 130-D Wikisource text says "Executive Order 130-A, June 22, 1900" (secondary; jobs/clark-discovery/output/CITED_BUT_UNKNOWN.csv); Niebuhr list rows (Wikisource list, Wikipedia) give 1900-06-22 and the title; text of 130-A not seen. Census holds EO:130, 130B (1900-06-22), 130C, 130D but not 130A.',
 'no',
 'Date 1900-06-22 comes from secondary lists, not a held official printing. Sibling EO:130C has a ProQuest scan (jobs/pinakes-proquest-ingest/output/texts/EO_130C.txt) that a person may check for a 130-A mention. Route: ProQuest phrase search (jobs/lewis-originals/output/ROUTES.csv).'),
('967A','967','A','1914-06-23','Alaska Townsite and Railroad Withdrawal No. 2 (EO:1967A; subject from census/WPA row)',
 'research/pre-1937-sources/ProQuest Pre-1937 Orders/PT1-1914-EO-1967-A.pdf (listed in %sINVENTORY.csv; the PDF is NOT on this checkout, only its extracted text)'%P,
 'PDF p. 1 (1 page) of PT1-1914-EO-1967-A.pdf: check the printed number (1967-A) and date June 23, 1914; held OCR text first lines "ORDER OF WITHDRAWAL. Alaska Townsite and Railroad Withdrawal No. 2"',
 P+'texts/EO_1967A.txt',
 'EO 3366 ProQuest text (%stexts/EO_3366.txt line 3) says "Executive Order Number 967-A, dated June 23, 1914"; WPA numbered list p.184 has EO:1967A, June 23 (and later entries cite "1967-A of June 23, 1914": EO:2773 p.250, EO:3545 p.316, EO:4741, 4878, 4974, 7325). Niebuhr b04 resolves 967A to 1967A as an OCR drop of a leading 1 (medium confidence). Census has EO:1967A (%s line %d).'%(P,CENF,CEN['EO:1967A']),
 'no (EO:967A); EO:1967A is yes',
 'Probably NOT a new admission: an OCR/typo form of existing EO:1967A. Recommend recording as alias only after a person checks EO 3366 PDF and the 1967-A page. EO:967 is a separate census order.'),
('2687A','2687','A','1917-08-21','Establishing an Exports Administrative Board and an Exports Council (Wikisource/Wikipedia list; secondary)',
 'none held',
 'none held (order text only on Wikisource mirror, not in repo; cited-by pages: Wikisource EO 2645/2687/2729-A/2770 texts, jobs/wikisource-texts/output/texts/EO_2687.txt, EO_2645.txt, EO_2729A.txt)',
 'none held',
 'Cited as "Executive Order 2687-A, August 21, 1917" by EO 2645, 2729-A, 2770 and tagged by EO 2687 (jobs/clark-discovery/output/CITED_BUT_UNKNOWN.csv, 4 rows); Niebuhr b04.jsonl: identified_with_text from Wikisource mirror, confidence high; not found in WPA numbered text as "2687-A". Census has EO:2687 but not 2687A.',
 'no',
 'Date and title are from secondary web lists. Niebuhr note: 2686-A (coal prices, same date) may also be missing from the census. Route: ProQuest phrase search "Executive Order No. 2687A" (jobs/lewis-originals/output/ROUTES.csv).'),
]
for k,(lid,num,suf,date,title,path,loc,txt,ev,inc,notes) in enumerate(L,1):
    rows.append(dict(zip(cols,['ADM-c-%s'%lid,'c_lettered_id',num,suf,date,title,path,loc,txt,ev,inc,notes])))
with open(OUT+'/ADMIT_LIST.csv','w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(cols)
    for r in rows: w.writerow([r[c] for c in cols])
print(len(rows))
import collections; print(collections.Counter((r['group'],r['already_in_census(yes/no)'][:3]) for r in rows))

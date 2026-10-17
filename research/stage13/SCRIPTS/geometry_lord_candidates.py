"""Extract audit-only candidate date markers from existing PDF text positions.
No OCR, no inferred EO IDs, no source promotion. Date lines can be false positives.
Usage: python geometry_lord_candidates.py PDF OUTPUT_DIR
"""
import fitz, re, json, sys, pathlib, hashlib, collections, statistics, difflib
pdf,out=sys.argv[1:3]; out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
PAGES=range(22,248) # PDF zero-based, 23-248 inclusive
mon_map={'jan':1,'jane':1,'jany':1,'janr':1,'janv':1,'feb':2,'febe':2,'febs':2,'febr':2,'mar':3,'mare':3,'mars':3,'march':3,'apr':4,'apre':4,'apr3':4,'aprs':4,'april':4,'may':5,'fay':5,'maye':5,'jun':6,'june':6,'june':6,'july':7,'jul':7,'julv':7,'auge':8,'aug':8,'augs':8,'augu':8,'sepe':9,'sept':9,'septe':9,'sep':9,'oct':10,'octe':10,'octs':10,'nov':11,'nove':11,'novs':11,'dec':12,'dece':12,'decs':12}
# Some old OCR misses alphabetic characters; no fuzzy matching on arbitrary tokens to avoid body false positives.
def month_match(w):
 z=re.sub(r'[^a-z0-9]','',w.lower())
 if z in mon_map:return mon_map[z],z
 return None,None
f=fitz.open(pdf);sha=hashlib.sha256(pathlib.Path(pdf).read_bytes()).hexdigest()
previous_year=None; recs=[]; register=[]; outside=[]; yearheadings=[]
for i in PAGES:
 p=f[i];words=p.get_text('words');entries=[]
 for x0,y0,x1,y1,w,*_ in words:
  m,code=month_match(w)
  if m:
   entries.append(dict(x=x0,y=y0,m=m,raw=w,code=code))
 # infer modal date-column x from lowest-x 60% month entries, clustered on x intervals of 30. In rare pages no months.
 if entries:
  xs=sorted(e['x'] for e in entries)
  low=xs[:max(1,int(len(xs)*0.65))]
  med=statistics.median(low)
  likely=[e for e in entries if abs(e['x']-med)<105]
  # If dates shifted along x and narrow cluster, keep whichever cluster has more distinct ys.
  clusters=collections.defaultdict(list)
  for e in entries:clusters[round(e['x']/70)*70].append(e)
  dominant=max(clusters.items(),key=lambda kv:(len(kv[1]),-kv[0]))[0]
  if len(likely)<len(clusters[dominant]):likely=[e for e in entries if abs(e['x']-dominant)<65]
 else:
  med=None;likely=[]
 # year heading scan within left zone and matching plausible years
 years=[]
 for w in words:
  t=re.sub('[^0-9]','',w[4])
  if len(t)==4 and 1789<=int(t)<=1941 and (med is None or w[0] <= med+10):
   years.append(dict(year=int(t),y=w[1],x=w[0]))
 # use preceding year heading if exists on this page, else inherit only if strong previous anchor
 years.sort(key=lambda x:x['y']);yearheadings.extend([dict(pdf_page=i+1,**y) for y in years]);
 candidates=[]
 for e in likely:
  # date/day same y within +-19 pts; positioned 0..135 after month. Exclude year heading etc
  possible=[]
  for w in words:
   if w[0]>e['x']+12 and w[0]<e['x']+155 and abs(w[1]-e['y'])<18:
    txt=w[4].strip('.,/;:!()[]*')
    if re.fullmatch(r'\d{1,2}',txt) and 1<=int(txt)<=31:possible.append((abs(w[1]-e['y'])+abs(w[0]-e['x']-55)/50,w))
  day=(int(min(possible,key=lambda x:x[0])[1][4].strip('.,/;:!()[]*')) if possible else None)
  yr=[y for y in years if y['y']<e['y'] and y['year']>=1789]
  source_year=yr[-1]['year'] if yr else previous_year
  year_type='on_page' if yr else ('carried_from_prior_page' if source_year else 'undetermined')
  candidates.append(dict(source='Lord 1943 Unnumbered series',pdf_page=i+1,pdf_word_x=round(e['x'],1),pdf_word_y=round(e['y'],1),month=e['m'],day=day,year_candidate=None,year_assignment="UNDETERMINED_NEEDS_VISUAL_CHECK",year_token_heuristic_unverified=source_year,year_heuristic_basis=year_type,raw_month=e['raw'],identification_status='DATE_MARKER_NOT_VERIFIED_ORDER',source_pdf_sha256=sha))
 if years:previous_year=years[-1]['year']
 if entries:outside.extend([dict(page=i+1,word=e['raw'],x=round(e['x']),y=round(e['y'])) for e in entries if e not in likely])
 recs.extend(candidates)
 register.append(dict(pdf_page=i+1,all_recognized_month_tokens=len(entries),date_column_candidates=len(candidates),resolved_day=sum(z['day'] is not None for z in candidates),years_detected=[x['year'] for x in years],date_column_x_estimate=round(med,1) if med is not None else None))
with (out/'LORD_GEOMETRY_DATE_LEADS.jsonl').open('w') as f1:
 for r in recs:f1.write(json.dumps(r)+'\n')
with (out/'LORD_GEOMETRY_PAGE_QA.jsonl').open('w') as f1:
 for r in register:f1.write(json.dumps(r)+'\n')
with (out/'LORD_REJECTED_MONTH_TOKENS.jsonl').open('w') as f1:
 for r in outside:f1.write(json.dumps(r)+'\n')
print(json.dumps(dict(pages=len(register),candidate_date_markers=len(recs),with_day=sum(r['day'] is not None for r in recs),with_authoritative_year=sum(r['year_candidate'] is not None for r in recs),heuristic_year_tokens=sum(r['year_token_heuristic_unverified'] is not None for r in recs),year_headings=len(yearheadings),months_outside_date_column=len(outside),pages_without_any_marker=sum(not r['date_column_candidates'] for r in register),pdf_sha256=sha),indent=2))

#!/usr/bin/env python3
"""Reusable review workspace for Lord's unnumbered-series chronology.
Never promotes OCR lines to EO identities. Uses word coordinates already embedded
in scanned PDF; page images remain the authoritative source. 1023 date leads
may merge or omit multiple same-date orders. Caller supplies PDF and existing
Stage13 geom leads. Creates CSV+JSONL+static HTML for manual adjudication.
"""
import collections,csv,hashlib,html,json,pathlib,statistics,sys
import fitz
p=pathlib.Path(sys.argv[1]); data=pathlib.Path(sys.argv[2]);out=pathlib.Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True)
f=fitz.open(p);sha=hashlib.sha256(p.read_bytes()).hexdigest()
leads=[json.loads(line) for line in data.open() if line.strip()]
assert len(leads)>1000 and all(r['source_pdf_sha256']==sha for r in leads)
perpage=collections.defaultdict(list)
for r in leads:perpage[r['pdf_page']].append(r)
record=[]
for page,rr in sorted(perpage.items()):
 rr.sort(key=lambda r:r['pdf_word_y']);words=f[page-1].get_text('words')
 for i,r in enumerate(rr):
  y=r['pdf_word_y'];next_y=rr[i+1]['pdf_word_y'] if i+1<len(rr) else f[page-1].rect.height-50
  # Capping at 300 points intentionally avoids dumping unrelated entire pages.
  end=min(y+295,next_y-15);begin=max(0,y-13); min_x=r['pdf_word_x']+95
  token=[w for w in words if begin <= w[1]<=end and w[0]>=min_x]
  token.sort(key=lambda w:(round(w[1]/14),w[0]));context=' '.join(w[4] for w in token)
  if len(context)>1900:context=context[:1900]+' [TRUNCATED: SEE SOURCE PAGE]'
  id='LORD:PDF:'+str(page)+':'+str(int(y))
  record.append(dict(candidate_id=id,pdf_page=page,loc_page_url=f'https://www.loc.gov/resource/gdc.43013029/?sp={page}',pdf_word_y=r['pdf_word_y'],month=r['month'],day=r['day'],raw_month=r['raw_month'],year_hint_UNVERIFIED=r['year_token_heuristic_unverified'],date_status='NOT_AUTHENTICATED',source_excerpt_UNVERIFIED=context,flags='DAY_UNREADABLE' if r['day'] is None else 'SOURCE_ROW_MAY_INCLUDE_MULTIPLE_ORDERS',identity_class='UNRESOLVED_BIBLIOGRAPHIC_APPEARANCE',source_pdf_sha256=sha))
assert len(record)==len(leads)
with open(out/'LORD_CHRONOLOGICAL_REVIEW_LEADS.csv','w',newline='',encoding='utf8') as q:
 w=csv.DictWriter(q,fieldnames=list(record[0]));w.writeheader();w.writerows(record)
with open(out/'LORD_CHRONOLOGICAL_REVIEW_LEADS.jsonl','w',encoding='utf8') as q:
 for r in record:q.write(json.dumps(r,ensure_ascii=False)+'\n')
summary=[]
for page in range(23,249):
 x=perpage[page];summary.append({'pdf_page':page,'date_line_leads':len(x),'no_day_leads':sum(r['day'] is None for r in x),'pdf_source':'https://www.loc.gov/resource/gdc.43013029/?sp='+str(page),'manual_review_required':True})
with open(out/'PAGE_REVIEW_PRIORITIES.csv','w',newline='',encoding='utf8') as q:
 w=csv.DictWriter(q,fieldnames=list(summary[0]));w.writeheader();w.writerows(sorted(summary,key=lambda v:(v['date_line_leads'], -v['no_day_leads'])))
# Preserve no client persistence by default; user exports explicit adjudication JSON.
rows=[{'id':r['candidate_id'],'page':r['pdf_page'],'url':r['loc_page_url'],'month':r['month'],'day':r['day'],'y':r['year_hint_UNVERIFIED'],'excerpt':r['source_excerpt_UNVERIFIED'][:1100]} for r in record]
payload=json.dumps(rows,ensure_ascii=False).replace('</','<\\/')
h='''<!DOCTYPE html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Lord 1943 unnumbered EO source review</title><style>body{font:15px/1.45 system-ui,sans-serif;margin:0;background:#f5f6f7;color:#111}header{background:#172638;color:white;padding:22px 6vw}header h1{font-size:23px;margin:0 0 5px}main{max-width:1200px;margin:0 auto;padding:15px}input,select,button{padding:9px;border:1px solid #aeb7c2;border-radius:6px;background:white}input{width:260px}.tools{display:flex;gap:9px;flex-wrap:wrap;align-items:center;margin-bottom:12px}.notice{padding:12px;border:1px solid #c1cbd5;background:white;border-radius:8px}.item{background:white;border:1px solid #dce2e8;border-radius:8px;margin:8px 0;padding:13px}.row{display:flex;gap:10px;justify-content:space-between;flex-wrap:wrap}.excerpt{white-space:pre-wrap;max-height:150px;overflow:auto;font-family:ui-monospace,monospace;font-size:12px;background:#f5f5f5;padding:8px;border-radius:4px}.muted{color:#556}.pill{display:inline-block;padding:3px 8px;background:#eaf1fa;border-radius:4px;font-size:12px}button{cursor:pointer}a{color:#14518a}</style>
<header><h1>Lord 1943 — Unnumbered EO Source-Review Workbench</h1><div>Historical source leads only. No entry has been authenticated as a presidential executive order.</div></header><main><div class="notice">The source volume reports over 1,500 historical entries. These '''+str(len(rows))+''' machine-extracted date-line leads are incomplete and can merge multiple same-date instruments. Validate the scanned page and original underlying document. Dates, year hints, and excerpt text are provisional.</div><p class="tools"><input id="find" placeholder="Search date lead or excerpt" oninput="render()"><select id="status"><option value="ALL">All review states</option><option value="TODO">Unreviewed</option><option value="KEEP">Candidate document identified</option><option value="SPLIT">More than one document</option><option value="MERGE">Likely duplicate</option><option value="REJECT">Not an executive order</option><option value="HOLD">Cannot determine</option></select><button onclick="exportReviews()">Export decisions JSON</button><span id="count"></span></p><section id="result"></section></main><script>const DATA='''+payload+''';const decisions={};const $=id=>document.getElementById(id);const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));function render(){const q=$('find').value.toLowerCase(),f=$('status').value;let filtered=DATA.filter(r=>((r.excerpt||'')+' '+r.id+' '+r.y+' '+r.page).toLowerCase().includes(q) && (f==='ALL'||(decisions[r.id]?.decision||'TODO')===f));$('count').innerText=filtered.length+' / '+DATA.length+' leads';$('result').innerHTML=filtered.slice(0,100).map(r=>`<article class="item"><div class="row"><b>${escape(r.id)}</b><span>Month ${r.month}, day ${r.day??'?'} • Year hint ${escape(r.y||'unknown')} (unverified) • <a target="_blank" rel="noopener" href="${r.url}">Scan page ${r.page}</a></span></div><div class="excerpt">${escape(r.excerpt)}</div><div class="row"><select onchange="recordDecision('${r.id}',this.value)">${['TODO','KEEP','SPLIT','MERGE','REJECT','HOLD'].map(v=>`<option ${decisions[r.id]?.decision===v?'selected':''}>${v}</option>`).join('')}</select><label>Document/source identifier <input value="${escape(decisions[r.id]?.document_id||'')}" onchange="recordID('${r.id}',this.value)" placeholder="Leave blank if unverified"></label></div></article>`).join('')}function recordDecision(id,v){decisions[id]={...(decisions[id]||{}),decision:v}}function recordID(id,v){decisions[id]={...(decisions[id]||{}),document_id:v}}function exportReviews(){const s=JSON.stringify({source:'Lord1943',kind:'UNVERIFIED_REVIEW_PROPOSALS',records:Object.entries(decisions).map(([id,v])=>({id,...v}))},null,2);let blob=new Blob([s],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='lord1943_review_proposals.json';a.click();URL.revokeObjectURL(url)}$('status').addEventListener('change',render);render();</script></html>'''
(out/'LORD_SOURCE_REVIEW.html').write_text(h,encoding='utf8')
print(json.dumps({'chronological_pdf_pages':226,'date_line_review_leads':len(record),'leads_with_uncertain_day':sum(r['day'] is None for r in record),'no_dates_promoted':True,'html':'LORD_SOURCE_REVIEW.html'},indent=2))

"""Acquire a bounded batch of official Statutes at Large scans named by Opus.

Source: Stage20 shared-source citation queue. Every citation is unverified text.
Does not infer that the linked statute changes, ends or supports any order.

Run: python research/stage20/code/acquire_shared_statutes.py
     python research/stage20/code/acquire_shared_statutes.py --offline-check
"""
import argparse
import csv
import hashlib
import io
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'research/stage20'
QUEUE=BASE/'output/SHARED_SOURCE_REFERENCE_QUEUE.csv'
OUT=BASE/'output'
SOURCES=BASE/'sources/statutes_at_large'
STAT=re.compile(r'^(\d{1,3}) Stat\. (\d{1,5})$')
MAX_BYTES=18_000_000
RESPONSE_TIMEOUT=25

def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()

def cited_statutes(queue=QUEUE):
    with queue.open(newline='',encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    result=[]
    for x in rows:
        if x['reference_type']!='STAT':continue
        m=STAT.fullmatch(x['reference_as_mentioned'])
        if not m:raise ValueError('Unsupported Statutes at Large citation: '+x['reference_as_mentioned'])
        volume,page=map(int,m.groups())
        if not (1<=volume<=140 and page>0):raise ValueError('Invalid historical source reference')
        if int(x['affected_candidate_count'])!=len(x['case_ids'].split(' | ')):
            raise ValueError('Case count mismatch for '+x['reference_as_mentioned'])
        target=f'STATUTE-{volume}-Pg{page}.pdf'
        result.append({'citation':x['reference_as_mentioned'],'volume':volume,'start_page_hint':page,
            'source_url':f'https://www.govinfo.gov/content/pkg/STATUTE-{volume}/pdf/{target}',
            'case_ids_mentioned':x['case_ids'],'case_lead_count':x['affected_candidate_count'],
            'local_relpath':'research/stage20/sources/statutes_at_large/'+target})
    if len(result)!=10:raise ValueError('Expected ten cited statutes at this frozen checkpoint')
    return result

def download_source(url):
    request=urllib.request.Request(url,headers={'User-Agent':'EO-Lifecycle-Research/1.0 (source authenticity research)','Accept':'application/pdf'})
    with urllib.request.urlopen(request,timeout=RESPONSE_TIMEOUT) as response:
        if response.status!=200:raise OSError('HTTP '+str(response.status))
        if response.geturl()!=url:raise OSError('Unexpected redirect: '+response.geturl())
        content=response.read(MAX_BYTES+1)
        if len(content)>MAX_BYTES:raise ValueError('PDF above hard source-size limit')
        if not content.startswith(b'%PDF-') or b'%%EOF' not in content[-2048:]:
            raise ValueError('HTTP response lacks PDF header or final EOF marker')
        return content

def gather(fetch=download_source):
    records=[];SOURCES.mkdir(parents=True,exist_ok=True)
    for c in cited_statutes():
        p=ROOT/c['local_relpath']
        r=dict(c)
        r.update({'download_state':'not_attempted','bytes':'','sha256':'','error':'',
                  'primary_source_authority_checked_by_human':'no',
                  'cited_order_scope_and_effect_verified':'no'})
        try:
            if p.is_file():
                data=p.read_bytes()
                if not data.startswith(b'%PDF-') or len(data)>MAX_BYTES:
                    raise ValueError('Existing source file failed basic PDF validation')
                r['download_state']='already_archived_pdf'
            else:
                data=fetch(c['source_url'])
                p.write_bytes(data)
                r['download_state']='downloaded_govinfo_candidate_pdf'
            r['bytes']=str(len(data));r['sha256']=sha_bytes(data)
        except Exception as e:
            r['download_state']='unavailable_or_invalid_response'
            r['error']=type(e).__name__+': '+str(e)[:160]
        records.append(r)
    return records

def summarize(rows):
    success=[r for r in rows if r['sha256']]
    return {'schema':'eo-shared-statute-acquisition/v1',
      'planned_statute_citation_searches':len(rows),
      'govinfo_pdf_bytes_archived':len(success),
      'failed_or_unavailable_requests':len(rows)-len(success),
      'total_candidate_eo_mention_edges_from_fetched_statutes':sum(int(r['case_lead_count']) for r in success),
      'original_source_authority_or_legal_effect_human_verified':0,
      'retrieval_qualification':('A govinfo.gov PDF contains the raw source response; a citation may be a statute page inside a larger act. '
       'Humans must inspect printed pagination, statutory operative text, effective date and savings. '
       'An Opus co-mention does not establish applicability to a particular executive order.')}

def main():
    a=argparse.ArgumentParser();a.add_argument('--offline-check',action='store_true');args=a.parse_args()
    if args.offline_check:
        report=json.loads((OUT/'STATUTE_FETCH_SUMMARY.json').read_text(encoding='utf-8'))
        with (OUT/'STATUTE_FETCH_INDEX.csv').open(newline='',encoding='utf-8') as f:
            index=list(csv.DictReader(f))
        for r in index:
            if r['sha256']:
                b=(ROOT/r['local_relpath']).read_bytes()
                if len(b)!=int(r['bytes']) or sha_bytes(b)!=r['sha256']:
                    raise ValueError('Archived GovInfo PDF changed: '+r['citation'])
        if summarize(index)!=report:
            raise ValueError('Acquisition report inconsistent with index')
        print('GovInfo shared statute outputs passed offline integrity check')
        return
    rows=gather()
    OUT.mkdir(parents=True,exist_ok=True)
    output=io.StringIO(newline='')
    writer=csv.DictWriter(output,fieldnames=list(rows[0]),lineterminator='\n')
    writer.writeheader();writer.writerows(rows)
    (OUT/'STATUTE_FETCH_INDEX.csv').write_text(output.getvalue(),encoding='utf-8')
    report=summarize(rows)
    (OUT/'STATUTE_FETCH_SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()

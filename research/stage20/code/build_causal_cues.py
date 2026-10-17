"""Convert 844 recovered Opus narratives into *research cues*, never legal findings.

Run: python research/stage20/code/build_causal_cues.py [--check]
Directory-matched original images are shared-batch hints only.
"""
import argparse
import csv
import io
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'research/stage20/output'
ISO_DATE=re.compile(r'\b(?:17|18|19|20)\d{2}-\d{2}-\d{2}\b')
EVENT=re.compile(r'\b(effective|ended|terminated|revoked|repealed|expired|sunset|lapsed|ceased|abolished|transferred|amended)\b',re.I)
SEARCH=re.compile(r'\b(retrieved|checked|searched|search|re-fetched|cache|as of|through cutoff|reviewer|full-text)\b',re.I)

def load_notes(path):
    with path.open(encoding='utf-8') as f:
        rows=[json.loads(s) for s in f if s.strip()]
    if len(rows)!=844 or len({r['instrument_id'] for r in rows})!=844:
        raise ValueError('Exactly 844 unique completed-Opus research records required')
    if any(r['independent_human_certification'] for r in rows):
        raise ValueError('Unexpected certification status in unverified Opus record')
    return rows

def load_media(path):
    with path.open(newline='',encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=496 or len({r['manifest_path'] for r in rows})!=496:
        raise ValueError('Expected 496 unique Opus media members')
    if any(x['source_bytes_verified']!='yes' for x in rows):
        raise ValueError('Unverified media bytes cannot enter queue')
    return rows

def role(context):
    if SEARCH.search(context):return 'possibly_research_check_date_not_legal_event'
    if EVENT.search(context):return 'possibly_effective_event_date_unverified'
    return 'date_role_unknown'

def date_contexts(record):
    text='\n'.join(str(record.get(k) or '') for k in ('review_problems_verbatim','what_remains_inferential_verbatim'))
    rows=[]
    for m in ISO_DATE.finditer(text):
        snippet=text[max(0,m.start()-110):min(len(text),m.end()+110)].replace('\n',' ')
        rows.append({'literal_date_mention':m.group(0),'date_role_guess':role(snippet),
                     'verbatim_context':snippet,
                     'start_character_offset_in_concatenated_notes':m.start(),
                     'legal_effect_and_source_unverified':True})
    return rows

def prefix(value):
    return value.replace('\\','/').lstrip('./').rstrip('/')+'/' if isinstance(value,str) and value else None

def classify_media(record,media):
    p=media['manifest_path']
    ev=prefix(record.get('evidence_dir_in_archive'))
    rv=prefix(record.get('review_dir_in_archive'))
    if ev and p.startswith(ev):return 'shared_evidence_shard_path_only'
    if rv and p.startswith(rv):return 'shared_reviewer_batch_path_only'
    return None

def build(notes,media):
    case_images=defaultdict(list)
    image_rows=[]
    for doc in media:
        matches=[(n['instrument_id'],kind) for n in notes if (kind:=classify_media(n,doc))]
        for identity,kind in matches:
            case_images[identity].append((doc['manifest_path'],kind,len(matches)))
        image_rows.append({'manifest_path':doc['manifest_path'],'sha256':doc['sha256'],
                           'bytes':doc['bytes'],'accepted_case_batch_matches':len(matches),
                           'batch_match_types':' | '.join(sorted({kind for _,kind in matches})),
                           'example_case_ids':' | '.join(sorted(i for i,_ in matches)[:12]),
                           'association_grade':'no_case_specific_evidence',
                           'source_bytes_verified':'yes','case_specific_legal_source_verified':'no'})
    packets,work=[],[]
    role_counts=Counter()
    for n in notes:
        identity=n['instrument_id']
        spans=date_contexts(n)
        role_counts.update(x['date_role_guess'] for x in spans)
        refs=n.get('explicit_references_not_verified',[])
        images=case_images[identity]
        effective_candidates=sum(x['date_role_guess']=='possibly_effective_event_date_unverified' for x in spans)
        p={'schema':'eo-causal-lead-packet/v1','instrument_id':identity,
           'provisional_status':n['verdict'],'opus_lane':n.get('opus_lane'),
           'opus_footprint_complete_unverified':n.get('opus_footprint_complete_claim'),
           'original_opus_notes_file':'research/stage20/output/OPUS_NOTE_LEADS.jsonl',
           'date_mentions_with_verbatim_context':spans,
           'explicit_citations_as_unverified_leads':refs,
           'source_media_candidate_count_by_batch_path_only':len(images),
           'sample_shared_batch_media_candidates':[{'manifest_path':f,'association':k,
                'other_candidate_orders_may_share_image':count>1} for f,k,count in images[:8]],
           'full_media_list':'research/stage20/output/MEDIA_BATCH_ASSOCIATION_AUDIT.csv',
           'required_human_review_gates':['original_identity_and_page_authentication',
             'complete_original_operative_clauses','dated_successor_source_history',
             'first_effective_end_or_current_predicate','earlier_cessation_and_revival_tests',
             'savings_accrued_rights_residuals','independent_human_review'],
           'historical_first_cessation_verified':False,'human_certified':False}
        packets.append(p)
        score=(12 if str(n.get('opus_footprint_complete_claim')).lower()=='true' else 0)
        score+=(10 if n['verdict']=='yes' else 0)+min(3,effective_candidates)*4+min(4,len(refs))*3
        score+=(3 if images else 0)
        work.append({'instrument_id':identity,'provisional_status':n['verdict'],
                     'footprint_assertion_not_verified':n.get('opus_footprint_complete_claim'),
                     'date_mentions':len(spans),
                     'possible_event_date_mentions_NOT_FINDINGS':effective_candidates,
                     'distinct_explicit_reference_leads':len(refs),
                     'media_candidates_in_shared_batches_NOT_CASE_EVIDENCE':len(images),
                     'triage_score_NOT_CONFIDENCE':score,
                     'next_action':('Verify cutoff-date operative predicate and later interventions, then audit remaining clause footprint.'
                        if n['verdict']=='yes' else
                        'Test earliest clause-specific effective cessation, later savings, nonrevival and counterevidence.'),
                     'human_certified':'no'})
    work.sort(key=lambda r:(-r['triage_score_NOT_CONFIDENCE'],r['instrument_id']))
    image_rows.sort(key=lambda r:r['manifest_path'])
    summary={'schema':'eo-stage20-causal-cue-excavation/v1',
      'case_records':len(notes),'verified_image_members':len(media),
      'image_members_with_any_accepted_case_batch_path':sum(x['accepted_case_batch_matches']>0 for x in image_rows),
      'image_members_with_many_accepted_case_batch_paths':sum(x['accepted_case_batch_matches']>1 for x in image_rows),
      'image_members_with_exactly_one_accepted_case_batch_path':sum(x['accepted_case_batch_matches']==1 for x in image_rows),
      'image_members_with_no_accepted_case_batch_path':sum(x['accepted_case_batch_matches']==0 for x in image_rows),
      'cases_with_any_weak_media_path_hint':len(case_images),
      'cases_with_any_ISO_date_context':sum(bool(p['date_mentions_with_verbatim_context']) for p in packets),
      'literal_date_mentions_by_machine_context_guess':dict(sorted(role_counts.items())),
      'unverified_case_specific_image_assertions':0,'human_certified_whole_lifecycle_dossiers':0,
      'qualification':('A shard or reviewer directory match is not evidence an image proves a particular case. '
         'A nearby causal verb does not make a date an established legal event.')}
    return packets,work,image_rows,summary

def outputs(notes,media):
    packets,work,image_rows,summary=build(notes,media)
    def format_csv(rows):
        b=io.StringIO(newline='')
        writer=csv.DictWriter(b,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)
        return b.getvalue()
    return {
      'CAUSAL_LEAD_PACKETS_844.jsonl':''.join(json.dumps(x,sort_keys=True,ensure_ascii=False)+'\n' for x in packets),
      'CAUSAL_LEAD_PRIORITIES_844.csv':format_csv(work),
      'MEDIA_BATCH_ASSOCIATION_AUDIT.csv':format_csv(image_rows),
      'CAUSAL_CUE_SUMMARY.json':json.dumps(summary,indent=2)+'\n'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--notes',type=Path,default=DATA/'OPUS_NOTE_LEADS.jsonl')
    p.add_argument('--media',type=Path,default=DATA/'OPUS_ORIGINAL_MEDIA_MEMBER_MAP.csv')
    p.add_argument('--out',type=Path,default=DATA)
    p.add_argument('--check',action='store_true')
    args=p.parse_args()
    data=outputs(load_notes(args.notes),load_media(args.media))
    if args.check:
        for name,content in data.items():
            if (args.out/name).read_text(encoding='utf-8')!=content:
                raise ValueError('Stale causal cue result: '+name)
        print('Causal source-cue outputs reproduce byte for byte')
    else:
        args.out.mkdir(parents=True,exist_ok=True)
        for name,content in data.items():
            (args.out/name).write_text(content,encoding='utf-8')
        print(data['CAUSAL_CUE_SUMMARY.json'])
if __name__=='__main__':
    main()
